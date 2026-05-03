#!/usr/bin/env python3
"""
PHASE3_1 live attention collector.

테마 사전(config/themes.json)을 기준으로 GDELT/Reddit/Finnhub 최신 뉴스를
짧은 window로 수집해 raw CSV를 만든다. 장기 baseline은 원문 전체가 아니라
daily aggregate를 누적해서 관리하는 전제다.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE3_1_DIR = SCRIPT_DIR.parent
GLOBAL_DIR = PHASE3_1_DIR.parent
PHASE0_DIR = GLOBAL_DIR / "PHASE0_classification"
CONFIG_DIR = PHASE3_1_DIR / "config"
CACHE_RAW_DIR = PHASE3_1_DIR / "cache" / "raw"
LOG_DIR = PHASE3_1_DIR / "logs"

for path in (CACHE_RAW_DIR, LOG_DIR):
    path.mkdir(parents=True, exist_ok=True)

GDELT_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"
FINNHUB_MARKET_NEWS_ENDPOINT = "https://finnhub.io/api/v1/news"
FINNHUB_COMPANY_NEWS_ENDPOINT = "https://finnhub.io/api/v1/company-news"
REDDIT_SUBREDDITS = ["stocks", "investing", "wallstreetbets", "options", "ValueInvesting"]
FINNHUB_SYMBOL_ALIASES = {
    "BRK-A": "BRK.A",
    "BRK-B": "BRK.B",
}
HEADERS = {
    "User-Agent": "JSInvestmentNarrativeAttention/0.1 (personal research)"
}
TODAY_STR = dt.datetime.now().strftime("%Y%m%d")
RUN_TS = dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def load_local_env() -> None:
    for path in (
        Path.cwd() / ".env",
        PHASE3_1_DIR / ".env",
        GLOBAL_DIR / ".env",
    ):
        load_env_file(path)


def normalize_ticker(value: str) -> str:
    return str(value or "").strip().upper().replace("/", "-").replace(".", "-")


def load_themes(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_universe(limit: int = 0, tickers: str = "") -> list[dict[str, Any]]:
    requested = {normalize_ticker(x) for x in tickers.split(",") if x.strip()}
    csv_path = PHASE0_DIR / "nasdaq_screener.csv"
    rows: list[dict[str, Any]] = []
    if not csv_path.exists():
        return rows
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = normalize_ticker(str(row.get("Symbol", "")))
            if not ticker:
                continue
            if requested and ticker not in requested:
                continue
            name = str(row.get("Name", "")).strip()
            if re.search(r"\b(?:Warrants?|Rights?|Units?)\b", name, flags=re.IGNORECASE):
                continue
            try:
                market_cap = float(row.get("Market Cap") or 0)
            except ValueError:
                market_cap = 0.0
            rows.append(
                {
                    "ticker": ticker,
                    "company_name": name,
                    "market_cap": market_cap,
                    "sector": row.get("Sector", ""),
                    "country": row.get("Country", ""),
                }
            )
    rows.sort(key=lambda x: x.get("market_cap", 0), reverse=True)
    if limit and limit > 0 and not requested:
        rows = rows[:limit]
    return rows


def safe_query_term(term: str) -> str:
    term = str(term).strip()
    if not term:
        return ""
    if re.search(r"\s|[-/]", term):
        return f'"{term}"'
    return term


def theme_query(theme: dict[str, Any], max_terms: int) -> str:
    terms = []
    for term in theme.get("keywords", [])[:max_terms]:
        safe = safe_query_term(term)
        if safe:
            terms.append(safe)
    query = " OR ".join(terms)
    return f"({query})" if len(terms) > 1 else query


def iter_windows(days: int, chunk_days: int, end_dt: dt.datetime) -> list[tuple[dt.datetime, dt.datetime]]:
    start_dt = end_dt - dt.timedelta(days=days)
    windows = []
    cur = start_dt
    while cur < end_dt:
        chunk_end = min(cur + dt.timedelta(days=chunk_days), end_dt)
        windows.append((cur, chunk_end))
        cur = chunk_end
    return windows


def gdelt_datetime(value: dt.datetime) -> str:
    return value.strftime("%Y%m%d%H%M%S")


def request_json(session: requests.Session, url: str, params: dict[str, Any], retries: int) -> Any:
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, params=params, headers=HEADERS, timeout=25)
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(3 * attempt)
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(3 * attempt)
    raise last_exc or RuntimeError("request failed")


def collect_gdelt(
    session: requests.Session,
    themes: list[dict[str, Any]],
    days: int,
    chunk_days: int,
    max_records: int,
    max_terms: int,
    sleep_sec: float,
    retries: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records = []
    errors = []
    end_dt = dt.datetime.now(dt.timezone.utc)
    for theme in themes:
        query = theme_query(theme, max_terms)
        if not query:
            continue
        for start, end in iter_windows(days, chunk_days, end_dt):
            print(
                f"[GDELT] {theme.get('theme', '')} {start.date()}~{end.date()}",
                flush=True,
            )
            params = {
                "query": query,
                "mode": "artlist",
                "format": "json",
                "startdatetime": gdelt_datetime(start),
                "enddatetime": gdelt_datetime(end),
                "maxrecords": max_records,
                "sort": "datedesc",
            }
            try:
                data = request_json(session, GDELT_ENDPOINT, params, retries)
            except Exception as exc:
                errors.append(
                    {
                        "source_type": "gdelt_news",
                        "theme": theme.get("theme", ""),
                        "query": query,
                        "window_start": start.isoformat(),
                        "window_end": end.isoformat(),
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                time.sleep(sleep_sec)
                continue
            for article in data.get("articles", []) or []:
                records.append(
                    {
                        "ticker": "",
                        "company_name": "",
                        "source_type": "gdelt_news",
                        "source": article.get("domain") or urlparse(article.get("url", "")).netloc,
                        "title": article.get("title", ""),
                        "text": article.get("seendate", ""),
                        "url": article.get("url", ""),
                        "published_at": article.get("seendate", ""),
                        "query": query,
                        "matched_terms": theme.get("theme", ""),
                        "engagement": "",
                        "raw_json": json.dumps(article, ensure_ascii=False),
                        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    }
                )
            time.sleep(sleep_sec)
    return records, errors


def collect_reddit(
    session: requests.Session,
    themes: list[dict[str, Any]],
    days: int,
    max_records: int,
    max_terms: int,
    sleep_sec: float,
    retries: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records = []
    errors = []
    after_ts = time.time() - days * 86400
    reddit_window = "week" if days <= 7 else "month" if days <= 31 else "year"
    for theme in themes:
        query = theme_query(theme, max_terms).replace(" OR ", " ")
        if not query:
            continue
        for subreddit in REDDIT_SUBREDDITS:
            print(f"[Reddit] {theme.get('theme', '')} r/{subreddit}", flush=True)
            params = {
                "q": query,
                "restrict_sr": 1,
                "sort": "new",
                "t": reddit_window,
                "limit": min(max_records, 100),
            }
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            try:
                data = request_json(session, url, params, retries)
            except Exception as exc:
                errors.append(
                    {
                        "source_type": "reddit_post",
                        "theme": theme.get("theme", ""),
                        "query": query,
                        "window_start": "",
                        "window_end": "",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                time.sleep(sleep_sec)
                continue
            for child in data.get("data", {}).get("children", []) or []:
                post = child.get("data", {})
                created = float(post.get("created_utc", 0) or 0)
                if created < after_ts:
                    continue
                permalink = post.get("permalink", "")
                full_url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else permalink
                engagement = int(post.get("score", 0) or 0) + int(post.get("num_comments", 0) or 0)
                records.append(
                    {
                        "ticker": "",
                        "company_name": "",
                        "source_type": "reddit_post",
                        "source": subreddit,
                        "title": post.get("title", ""),
                        "text": post.get("selftext", ""),
                        "url": full_url,
                        "published_at": dt.datetime.fromtimestamp(created, tz=dt.timezone.utc).isoformat(),
                        "query": query,
                        "matched_terms": theme.get("theme", ""),
                        "engagement": engagement,
                        "raw_json": json.dumps(post, ensure_ascii=False),
                        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    }
                )
            time.sleep(sleep_sec)
    return records, errors


def iter_date_windows(days: int, window_days: int) -> list[tuple[dt.date, dt.date]]:
    end_date = dt.datetime.now(dt.timezone.utc).date()
    start_date = end_date - dt.timedelta(days=days)
    cur = start_date
    windows = []
    window_days = max(1, window_days)
    while cur <= end_date:
        chunk_to = min(cur + dt.timedelta(days=window_days - 1), end_date)
        windows.append((cur, chunk_to))
        cur = chunk_to + dt.timedelta(days=1)
    return windows


def collect_finnhub_market(
    session: requests.Session,
    token: str,
    max_records: int,
    retries: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    params = {"category": "general", "token": token}
    records = []
    errors = []
    try:
        data = request_json(session, FINNHUB_MARKET_NEWS_ENDPOINT, params, retries)
    except Exception as exc:
        errors.append(
            {
                "source_type": "finnhub_market_news",
                "theme": "",
                "query": "category=general",
                "window_start": "",
                "window_end": "",
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        return records, errors
    for article in (data or [])[:max_records]:
        published_at = ""
        if article.get("datetime"):
            published_at = dt.datetime.fromtimestamp(int(article["datetime"]), tz=dt.timezone.utc).isoformat()
        records.append(
            {
                "ticker": "",
                "company_name": "",
                "source_type": "finnhub_market_news",
                "source": article.get("source", "Finnhub"),
                "title": article.get("headline", ""),
                "text": article.get("summary", ""),
                "url": article.get("url", ""),
                "published_at": published_at,
                "query": "category=general",
                "matched_terms": "",
                "engagement": "",
                "raw_json": json.dumps(article, ensure_ascii=False),
                "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            }
        )
    return records, errors


def collect_finnhub_company(
    session: requests.Session,
    token: str,
    universe: list[dict[str, Any]],
    days: int,
    window_days: int,
    max_records_per_ticker: int,
    sleep_sec: float,
    retries: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records = []
    errors = []
    windows = list(reversed(iter_date_windows(days, window_days)))
    start_date = dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=days)
    end_date = dt.datetime.now(dt.timezone.utc).date()

    for idx, item in enumerate(universe, start=1):
        ticker = str(item["ticker"]).upper()
        symbol = FINNHUB_SYMBOL_ALIASES.get(ticker, ticker)
        company = item.get("company_name", "")
        per_ticker_count = 0
        print(f"[Finnhub company] {idx}/{len(universe)} {ticker} {days}d", flush=True)
        for cur, chunk_to in windows:
            if per_ticker_count >= max_records_per_ticker:
                break
            params = {
                "symbol": symbol,
                "from": cur.isoformat(),
                "to": chunk_to.isoformat(),
                "token": token,
            }
            try:
                data = request_json(session, FINNHUB_COMPANY_NEWS_ENDPOINT, params, retries)
            except Exception as exc:
                errors.append(
                    {
                        "source_type": "finnhub_news",
                        "theme": "",
                        "query": f"{symbol}:{cur}:{chunk_to}",
                        "window_start": cur.isoformat(),
                        "window_end": chunk_to.isoformat(),
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                time.sleep(sleep_sec)
                continue
            if isinstance(data, dict) and data.get("error"):
                errors.append(
                    {
                        "source_type": "finnhub_news",
                        "theme": "",
                        "query": f"{symbol}:{cur}:{chunk_to}",
                        "window_start": cur.isoformat(),
                        "window_end": chunk_to.isoformat(),
                        "error": str(data["error"]),
                    }
                )
                time.sleep(sleep_sec)
                continue
            if not isinstance(data, list):
                errors.append(
                    {
                        "source_type": "finnhub_news",
                        "theme": "",
                        "query": f"{symbol}:{cur}:{chunk_to}",
                        "window_start": cur.isoformat(),
                        "window_end": chunk_to.isoformat(),
                        "error": f"unexpected response: {data}",
                    }
                )
                time.sleep(sleep_sec)
                continue
            for article in data:
                if per_ticker_count >= max_records_per_ticker:
                    break
                published_at = ""
                published_date = None
                if article.get("datetime"):
                    published_dt = dt.datetime.fromtimestamp(int(article["datetime"]), tz=dt.timezone.utc)
                    published_at = published_dt.isoformat()
                    published_date = published_dt.date()
                if published_date and not (start_date <= published_date <= end_date):
                    continue
                records.append(
                    {
                        "ticker": ticker,
                        "company_name": company,
                        "source_type": "finnhub_news",
                        "source": article.get("source") or "Finnhub",
                        "title": article.get("headline", ""),
                        "text": article.get("summary", ""),
                        "url": article.get("url", ""),
                        "published_at": published_at,
                        "query": f"{symbol}:{cur}:{chunk_to}",
                        "matched_terms": ticker,
                        "engagement": "",
                        "raw_json": json.dumps(article, ensure_ascii=False),
                        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    }
                )
                per_ticker_count += 1
            time.sleep(sleep_sec)
    return records, errors


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = [
        "ticker",
        "company_name",
        "source_type",
        "source",
        "title",
        "text",
        "url",
        "published_at",
        "query",
        "matched_terms",
        "engagement",
        "raw_json",
        "collected_at",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_errors(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = ["source_type", "theme", "query", "window_start", "window_end", "error"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    load_local_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--themes", type=Path, default=CONFIG_DIR / "themes.json")
    parser.add_argument("--sources", default="finnhub_company", help="Comma-separated: finnhub_company,finnhub_market,gdelt,reddit")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--chunk-days", type=int, default=3)
    parser.add_argument("--finnhub-window-days", type=int, default=7)
    parser.add_argument("--limit", type=int, default=25, help="Ticker universe limit for Finnhub company-news.")
    parser.add_argument("--tickers", default="", help="Comma-separated ticker override for Finnhub company-news.")
    parser.add_argument("--theme-limit", type=int, default=0, help="0 means all themes.")
    parser.add_argument("--max-records", type=int, default=100)
    parser.add_argument("--max-records-per-ticker", type=int, default=200)
    parser.add_argument("--max-terms", type=int, default=5)
    parser.add_argument("--sleep", type=float, default=0.5)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--finnhub-token", default=os.getenv("FINNHUB_API_KEY") or os.getenv("FINNHUB_TOKEN") or "")
    parser.add_argument("--output-prefix", default=f"{RUN_TS}_{TODAY_STR}_live")
    args = parser.parse_args()

    themes = load_themes(args.themes)
    if args.theme_limit and args.theme_limit > 0:
        themes = themes[: args.theme_limit]

    source_set = {x.strip().lower() for x in args.sources.split(",") if x.strip()}
    session = requests.Session()
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    if "gdelt" in source_set:
        gdelt_records, gdelt_errors = collect_gdelt(
            session,
            themes,
            args.days,
            args.chunk_days,
            args.max_records,
            args.max_terms,
            args.sleep,
            args.retries,
        )
        records.extend(gdelt_records)
        errors.extend(gdelt_errors)

    if "reddit" in source_set:
        reddit_records, reddit_errors = collect_reddit(
            session,
            themes,
            args.days,
            args.max_records,
            args.max_terms,
            args.sleep,
            args.retries,
        )
        records.extend(reddit_records)
        errors.extend(reddit_errors)

    if "finnhub" in source_set:
        source_set.add("finnhub_company")

    if "finnhub_company" in source_set:
        if args.finnhub_token:
            universe = load_universe(args.limit, args.tickers)
            if not universe:
                errors.append(
                    {
                        "source_type": "finnhub_news",
                        "theme": "",
                        "query": "company-news",
                        "window_start": "",
                        "window_end": "",
                        "error": "수집 대상 ticker universe 없음",
                    }
                )
            else:
                finnhub_records, finnhub_errors = collect_finnhub_company(
                    session,
                    args.finnhub_token,
                    universe,
                    args.days,
                    args.finnhub_window_days,
                    args.max_records_per_ticker,
                    args.sleep,
                    args.retries,
                )
                records.extend(finnhub_records)
                errors.extend(finnhub_errors)
        else:
            errors.append(
                {
                    "source_type": "finnhub_news",
                    "theme": "",
                    "query": "company-news",
                    "window_start": "",
                    "window_end": "",
                    "error": "FINNHUB_API_KEY 없음",
                }
            )

    if "finnhub_market" in source_set:
        if args.finnhub_token:
            print("[Finnhub] category=general", flush=True)
            finnhub_records, finnhub_errors = collect_finnhub_market(session, args.finnhub_token, args.max_records, args.retries)
            records.extend(finnhub_records)
            errors.extend(finnhub_errors)
        else:
            errors.append(
                {
                    "source_type": "finnhub_market_news",
                    "theme": "",
                    "query": "category=general",
                    "window_start": "",
                    "window_end": "",
                    "error": "FINNHUB_API_KEY 없음",
                }
            )

    raw_path = CACHE_RAW_DIR / f"{args.output_prefix}_attention_raw.csv"
    err_path = LOG_DIR / f"{args.output_prefix}_attention_errors.csv"
    write_csv(raw_path, records)
    write_errors(err_path, errors)

    print(f"수집_원문_파일 {raw_path}")
    print(f"수집_에러_파일 {err_path}")
    print(f"수집_행수 {len(records)}")
    print(f"에러_행수 {len(errors)}")
    print(f"소스 {','.join(sorted(source_set))}")
    print(f"테마수 {len(themes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
