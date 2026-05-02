#!/usr/bin/env python3
"""
PHASE3 Global Narrative - Raw data collector

Collects recent company-level narrative data from:
  - GDELT DOC 2.0 news API
  - Finnhub company-news API
  - Reddit public search JSON endpoint

Default window is the last 7 days. The collector is intentionally conservative:
company names are used as the primary search key because many tickers are
ordinary English words.

Examples:
  python3 scripts/collect_narrative_raw.py --days 7 --limit 5
  python3 scripts/collect_narrative_raw.py --days 7 --tickers AAPL,MSFT,NVDA
  python3 scripts/collect_narrative_raw.py --days 7 --source gdelt --limit 20
  FINNHUB_API_KEY=... python3 scripts/collect_narrative_raw.py --days 7 --source finnhub --tickers AAPL
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pandas as pd
import requests


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE3_DIR = SCRIPT_DIR.parent
GLOBAL_DIR = PHASE3_DIR.parent
PHASE0_DIR = GLOBAL_DIR / "PHASE0_classification"

CACHE_DIR = PHASE3_DIR / "cache"
LOG_DIR = PHASE3_DIR / "logs"
RESULTS_DIR = PHASE3_DIR / "results"
for path in (CACHE_DIR, LOG_DIR, RESULTS_DIR):
    path.mkdir(exist_ok=True)

TODAY = dt.datetime.now(dt.timezone.utc)
TODAY_STR = dt.datetime.now().strftime("%Y%m%d")
RUN_TS = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

GDELT_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"
FINNHUB_ENDPOINT = "https://finnhub.io/api/v1/company-news"
REDDIT_SUBREDDITS = ["stocks", "investing", "wallstreetbets", "options", "ValueInvesting"]
FINNHUB_SYMBOL_ALIASES = {
    "BRK-A": "BRK.A",
    "BRK-B": "BRK.B",
}

HEADERS = {
    "User-Agent": (
        "JSInvestmentNarrativeCollector/0.1 "
        "(personal research; contact: limited8090@gmail.com)"
    )
}

NASDAQ_TO_GICS = {
    "Technology": "Information Technology",
    "Finance": "Financials",
    "Health Care": "Health Care",
    "Consumer Discretionary": "Consumer Discretionary",
    "Consumer Staples": "Consumer Staples",
    "Industrials": "Industrials",
    "Energy": "Energy",
    "Real Estate": "Real Estate",
    "Utilities": "Utilities",
    "Basic Materials": "Materials",
    "Telecommunications": "Communication Services",
}


def clean_company_name(name: str) -> str:
    """Remove listing boilerplate while preserving the legal company name."""
    out = str(name or "").strip()
    replacements = [
        r"\bCommon Stock\b",
        r"\bOrdinary Shares?\b",
        r"\bAmerican Depositary Shares?\b",
        r"\bAmerican Depositary Receipts?\b",
        r"\bDepositary Shares?\b",
        r"\bClass [A-Z]\b",
        r"\bSeries [A-Z0-9]+\b",
    ]
    for pattern in replacements:
        out = re.sub(pattern, " ", out, flags=re.IGNORECASE)
    out = re.sub(r"\s+", " ", out).strip(" -,.")
    return out or str(name or "").strip()


def short_company_name(name: str) -> str:
    """Remove common legal suffixes for secondary matching."""
    out = clean_company_name(name)
    replacements = [
        r"\bInc\.\b",
        r"\bInc\b",
        r"\bCorporation\b",
        r"\bCorp\.\b",
        r"\bCorp\b",
        r"\bCompany\b",
        r"\bCo\.\b",
        r"\bLimited\b",
        r"\bLtd\.\b",
        r"\bLtd\b",
        r"\bPLC\b",
        r"\bN\.V\.\b",
        r"\bS\.A\.\b",
    ]
    for pattern in replacements:
        out = re.sub(pattern, " ", out, flags=re.IGNORECASE)
    out = re.sub(r"\s+", " ", out).strip(" -,.")
    return out or str(name or "").strip()


def build_aliases(company_name: str) -> list[str]:
    cleaned = clean_company_name(company_name)
    aliases = [cleaned]

    # A shorter alias often performs better for names like "Microsoft Corporation".
    short = re.sub(
        r"\b(holdings?|group|technologies|technology|systems|international)\b",
        " ",
        short_company_name(company_name),
        flags=re.IGNORECASE,
    )
    short = re.sub(r"\s+", " ", short).strip(" -,.")
    if short and short.lower() != cleaned.lower():
        aliases.append(short)

    # Keep only useful distinct aliases.
    deduped: list[str] = []
    seen = set()
    for alias in aliases:
        key = alias.lower()
        if len(alias) >= 3 and key not in seen:
            deduped.append(alias)
            seen.add(key)
    return deduped[:2]


def gdelt_query(aliases: list[str]) -> str:
    # For news, prefer exact company names. Add a short alias only when it is
    # specific enough; otherwise names such as "Apple" become noisy quickly.
    selected = aliases[:1]
    if len(aliases) > 1 and len(aliases[1].split()) >= 2:
        selected.append(aliases[1])
    exact = [f'"{alias}"' for alias in selected if alias]
    return f"({' OR '.join(exact)})" if len(exact) > 1 else exact[0]


def reddit_query(ticker: str, aliases: list[str]) -> str:
    terms = [f'"{alias}"' for alias in aliases if alias]
    if len(ticker) >= 2:
        terms.append(f"${ticker}")
    return " OR ".join(terms)


def load_universe() -> pd.DataFrame:
    """Load PHASE0 universe. Prefer xlsx; fall back to nasdaq_screener.csv."""
    xlsx_candidates = sorted(glob.glob(str(PHASE0_DIR / "*_classification_master.xlsx")))
    if xlsx_candidates:
        try:
            df = pd.read_excel(xlsx_candidates[-1], sheet_name="전체종목")
            cols = {
                "Symbol": "ticker",
                "Name": "company_name",
                "Country": "country",
                "Is_ADR": "is_adr",
                "GICS_Sector": "sector",
                "Market_Cap": "market_cap",
            }
            df = df.rename(columns=cols)
            return df[list(cols.values())].copy()
        except Exception as exc:
            print(f"[WARN] master xlsx 로드 실패, CSV fallback 사용: {type(exc).__name__}: {exc}")

    csv_path = PHASE0_DIR / "nasdaq_screener.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"PHASE0 universe not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df["Symbol"] = df["Symbol"].astype(str).str.replace("/", "-", regex=False)
    df["price"] = pd.to_numeric(df["Last Sale"].astype(str).str.replace("$", "", regex=False), errors="coerce")
    df["avg_daily_value"] = pd.to_numeric(df["Volume"], errors="coerce") * df["price"]
    df["market_cap"] = pd.to_numeric(df["Market Cap"], errors="coerce")
    df["is_adr"] = df["Country"] != "United States"
    df["sector"] = df["Sector"].map(NASDAQ_TO_GICS)

    mask = (
        (df["market_cap"] >= 1_000_000_000)
        & (df["avg_daily_value"] >= 10_000_000)
        & ~df["Name"].str.contains(r"\b(?:Warrants?|Rights?|Units?)\b", case=False, na=False)
        & (df["Industry"] != "Blank Checks")
    )
    out = df.loc[mask, ["Symbol", "Name", "Country", "is_adr", "sector", "market_cap"]].copy()
    out = out.rename(
        columns={
            "Symbol": "ticker",
            "Name": "company_name",
            "Country": "country",
        }
    )
    return out


def request_json(
    session: requests.Session,
    url: str,
    params: dict[str, Any],
    retries: int = 3,
    headers: dict[str, str] | None = None,
) -> Any:
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, params=params, headers=headers, timeout=20)
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(5 * attempt)
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(5 * attempt)
    raise last_exc or RuntimeError("unknown request failure")


def collect_gdelt(session: requests.Session, row: pd.Series, days: int, max_records: int) -> tuple[list[dict], list[dict]]:
    ticker = row["ticker"]
    company = row["company_name"]
    aliases = build_aliases(company)
    query = gdelt_query(aliases)
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "timespan": f"{days}d",
        "maxrecords": max_records,
        "sort": "datedesc",
    }
    records: list[dict] = []
    errors: list[dict] = []
    try:
        data = request_json(session, GDELT_ENDPOINT, params=params)
    except Exception as exc:
        errors.append(error_row(ticker, company, "gdelt_news", query, exc))
        return records, errors

    for item in data.get("articles", []):
        url = item.get("url") or ""
        domain = item.get("domain") or urlparse(url).netloc
        records.append(
            {
                "ticker": ticker,
                "company_name": company,
                "source_type": "gdelt_news",
                "source": domain,
                "title": item.get("title"),
                "text": item.get("snippet") or "",
                "url": url,
                "published_at": item.get("seendate"),
                "query": query,
                "matched_terms": "|".join(aliases),
                "engagement": None,
                "raw_json": json.dumps(item, ensure_ascii=False),
                "collected_at": TODAY.isoformat(),
            }
        )
    return records, errors


def collect_finnhub(
    session: requests.Session,
    row: pd.Series,
    days: int,
    max_records: int,
    token: str,
    window_days: int = 7,
) -> tuple[list[dict], list[dict]]:
    ticker = row["ticker"]
    company = row["company_name"]
    query = FINNHUB_SYMBOL_ALIASES.get(str(ticker).upper(), ticker)
    records: list[dict] = []
    errors: list[dict] = []

    end_date = TODAY.date()
    start_date = end_date - dt.timedelta(days=days)
    cur = start_date
    window_days = max(1, window_days)
    windows: list[tuple[dt.date, dt.date]] = []

    while cur <= end_date:
        chunk_to = min(cur + dt.timedelta(days=window_days - 1), end_date)
        windows.append((cur, chunk_to))
        cur = chunk_to + dt.timedelta(days=1)

    # Newest-first keeps the freshest narrative when max_records is capped.
    for cur, chunk_to in reversed(windows):
        if len(records) >= max_records:
            break
        params = {
            "symbol": ticker,
            "from": cur.isoformat(),
            "to": chunk_to.isoformat(),
        }
        try:
            data = request_json(
                session,
                FINNHUB_ENDPOINT,
                params=params,
                headers={"X-Finnhub-Token": token},
            )
        except Exception as exc:
            errors.append(error_row(ticker, company, "finnhub_news", f"{query}:{cur}:{chunk_to}", exc))
            continue

        if isinstance(data, dict) and data.get("error"):
            errors.append(error_row(ticker, company, "finnhub_news", f"{query}:{cur}:{chunk_to}", RuntimeError(data["error"])))
            continue
        if not isinstance(data, list):
            errors.append(error_row(ticker, company, "finnhub_news", f"{query}:{cur}:{chunk_to}", RuntimeError(f"unexpected response: {data}")))
            continue

        for item in data:
            if len(records) >= max_records:
                break
            published_at = ""
            published_date = None
            if item.get("datetime"):
                published_dt = dt.datetime.fromtimestamp(
                    int(item["datetime"]),
                    tz=dt.timezone.utc,
                )
                published_at = published_dt.isoformat()
                published_date = published_dt.date()
            if published_date and not (start_date <= published_date <= end_date):
                continue
            records.append(
                {
                    "ticker": ticker,
                    "company_name": company,
                    "source_type": "finnhub_news",
                    "source": item.get("source") or "Finnhub",
                    "title": item.get("headline"),
                    "text": item.get("summary") or "",
                    "url": item.get("url") or "",
                    "published_at": published_at,
                    "query": f"{query}:{cur}:{chunk_to}",
                    "matched_terms": ticker,
                    "engagement": None,
                    "raw_json": json.dumps(item, ensure_ascii=False),
                    "collected_at": TODAY.isoformat(),
                }
            )

    return records, errors


def collect_reddit(session: requests.Session, row: pd.Series, days: int, max_records: int) -> tuple[list[dict], list[dict]]:
    ticker = row["ticker"]
    company = row["company_name"]
    aliases = build_aliases(company)
    query = reddit_query(ticker, aliases)
    after_ts = TODAY.timestamp() - days * 86400
    records: list[dict] = []
    errors: list[dict] = []
    reddit_window = "week" if days <= 7 else "month" if days <= 31 else "year"

    for subreddit in REDDIT_SUBREDDITS:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            "q": query,
            "restrict_sr": "on",
            "sort": "new",
            "t": reddit_window,
            "limit": min(max_records, 100),
        }
        try:
            data = request_json(session, url, params=params)
        except Exception as exc:
            errors.append(error_row(ticker, company, f"reddit:{subreddit}", query, exc))
            continue

        children = data.get("data", {}).get("children", [])
        for child in children:
            item = child.get("data", {})
            created_utc = float(item.get("created_utc") or 0)
            if created_utc < after_ts:
                continue
            permalink = item.get("permalink") or ""
            full_url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else permalink
            engagement = int(item.get("score") or 0) + int(item.get("num_comments") or 0)
            records.append(
                {
                    "ticker": ticker,
                    "company_name": company,
                    "source_type": "reddit_post",
                    "source": subreddit,
                    "title": item.get("title"),
                    "text": item.get("selftext") or "",
                    "url": full_url,
                    "published_at": dt.datetime.fromtimestamp(created_utc, tz=dt.timezone.utc).isoformat(),
                    "query": query,
                    "matched_terms": "|".join(aliases + [f"${ticker}"]),
                    "engagement": engagement,
                    "raw_json": json.dumps(item, ensure_ascii=False),
                    "collected_at": TODAY.isoformat(),
                }
            )
    return records, errors


def error_row(ticker: str, company: str, source_type: str, query: str, exc: Exception) -> dict:
    err = re.sub(r"token=[^&\\s]+", "token=***", str(exc)[:300])
    return {
        "ticker": ticker,
        "company_name": company,
        "source_type": source_type,
        "query": query,
        "error_type": type(exc).__name__,
        "error": err,
        "collected_at": TODAY.isoformat(),
    }


def dedupe(records: list[dict]) -> list[dict]:
    out: list[dict] = []
    seen = set()
    for rec in records:
        key = (rec.get("ticker"), rec.get("source_type"), rec.get("url") or rec.get("title"))
        if key in seen:
            continue
        seen.add(key)
        out.append(rec)
    return out


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def ticker_slug(args: argparse.Namespace, universe: pd.DataFrame) -> str:
    if args.tickers:
        tickers = [ticker.strip().upper() for ticker in args.tickers.split(",") if ticker.strip()]
        joined = "_".join(tickers[:6])
        if len(tickers) > 6:
            joined += f"_plus{len(tickers) - 6}"
        return joined
    if args.limit:
        return f"limit{args.limit}"
    return f"universe{len(universe)}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect recent narrative raw data.")
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of tickers.")
    parser.add_argument("--tickers", default=None, help="Comma-separated ticker list.")
    parser.add_argument("--source", choices=["all", "gdelt", "finnhub", "reddit"], default="all")
    parser.add_argument("--max-records", type=int, default=50, help="Max records per ticker/source query.")
    parser.add_argument("--sleep", type=float, default=0.5, help="Sleep seconds between tickers.")
    parser.add_argument("--gdelt-sleep", type=float, default=5.0, help="Extra sleep after each GDELT query.")
    parser.add_argument(
        "--finnhub-token",
        default=None,
        help="Finnhub API token. Defaults to FINNHUB_API_KEY or FINNHUB_TOKEN env var.",
    )
    parser.add_argument("--finnhub-window-days", type=int, default=7, help="Finnhub date-window size for chunked collection.")
    parser.add_argument("--include-adr", action="store_true", help="Include ADR/non-US listings from PHASE0.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    universe = load_universe()
    universe["ticker"] = universe["ticker"].astype(str)

    if not args.include_adr and "is_adr" in universe.columns:
        universe = universe[~universe["is_adr"].fillna(False).astype(bool)].copy()

    if args.tickers:
        wanted = {ticker.strip().upper() for ticker in args.tickers.split(",") if ticker.strip()}
        universe = universe[universe["ticker"].str.upper().isin(wanted)].copy()
        missing = sorted(wanted - set(universe["ticker"].str.upper()))
        if missing:
            print(f"[WARN] universe에서 찾지 못한 ticker: {', '.join(missing)}")

    if args.limit:
        universe = universe.head(args.limit).copy()

    if universe.empty:
        print("[ERROR] 수집 대상 종목이 없습니다.")
        return 1

    finnhub_token = args.finnhub_token or os.getenv("FINNHUB_API_KEY") or os.getenv("FINNHUB_TOKEN")
    if args.source == "finnhub" and not finnhub_token:
        print("[ERROR] Finnhub 수집에는 FINNHUB_API_KEY 또는 FINNHUB_TOKEN 환경변수가 필요합니다.")
        return 1
    if args.source == "all" and not finnhub_token:
        print("[WARN] FINNHUB_API_KEY/FINNHUB_TOKEN 없음: all 실행에서 Finnhub는 스킵합니다.")

    print("=" * 72)
    print("PHASE3 Narrative Raw Collector")
    print(f"  tickers: {len(universe)}")
    print(f"  window : last {args.days} days")
    print(f"  source : {args.source}")
    print("=" * 72)

    session = requests.Session()
    session.headers.update(HEADERS)

    records: list[dict] = []
    errors: list[dict] = []

    for idx, row in enumerate(universe.itertuples(index=False), start=1):
        s = pd.Series(row._asdict())
        ticker = s["ticker"]
        name = s["company_name"]
        print(f"[{idx}/{len(universe)}] {ticker} - {clean_company_name(name)}")

        if args.source in ("all", "gdelt"):
            gdelt_records, gdelt_errors = collect_gdelt(session, s, args.days, args.max_records)
            records.extend(gdelt_records)
            errors.extend(gdelt_errors)
            print(f"  GDELT: {len(gdelt_records)}")
            time.sleep(args.gdelt_sleep)

        if args.source in ("all", "finnhub") and finnhub_token:
            finnhub_records, finnhub_errors = collect_finnhub(
                session,
                s,
                args.days,
                args.max_records,
                finnhub_token,
                args.finnhub_window_days,
            )
            records.extend(finnhub_records)
            errors.extend(finnhub_errors)
            print(f"  Finnhub: {len(finnhub_records)}")

        if args.source in ("all", "reddit"):
            reddit_records, reddit_errors = collect_reddit(session, s, args.days, args.max_records)
            records.extend(reddit_records)
            errors.extend(reddit_errors)
            print(f"  Reddit: {len(reddit_records)} posts, errors={len(reddit_errors)}")

        time.sleep(args.sleep)

    records = dedupe(records)

    fieldnames = [
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
    error_fields = ["ticker", "company_name", "source_type", "query", "error_type", "error", "collected_at"]

    suffix = f"{RUN_TS}_{args.days}d_{args.source}_{ticker_slug(args, universe)}"

    raw_path = CACHE_DIR / f"{suffix}_narrative_raw.csv"
    err_path = LOG_DIR / f"{suffix}_narrative_errors.csv"

    write_csv(raw_path, records, fieldnames)
    write_csv(err_path, errors, error_fields)

    source_paths: list[Path] = []
    if records:
        for source_type in sorted({row["source_type"] for row in records}):
            source_rows = [row for row in records if row["source_type"] == source_type]
            source_path = CACHE_DIR / f"{suffix}_{source_type}_raw.csv"
            write_csv(source_path, source_rows, fieldnames)
            source_paths.append(source_path)

    by_source = pd.DataFrame(records).groupby("source_type").size().to_dict() if records else {}
    print("\n" + "=" * 72)
    print(f"saved raw   : {raw_path}")
    for source_path in source_paths:
        print(f"saved source: {source_path}")
    print(f"saved errors: {err_path}")
    print(f"records     : {len(records)} {by_source}")
    print(f"errors      : {len(errors)}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
