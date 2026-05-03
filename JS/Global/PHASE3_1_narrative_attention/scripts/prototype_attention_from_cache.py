#!/usr/bin/env python3
"""
PHASE3_1 narrative attention prototype.

This script intentionally avoids live API calls. It reads existing
PHASE3_narrative_ticker raw CSV files, tags articles with a small static theme
dictionary, compresses them into daily aggregates, and emits a latest ranking.

The output is useful for validating schema and scoring behavior, not for a
complete market-wide attention ranking unless the input raw files are
market-wide.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE3_1_DIR = SCRIPT_DIR.parent
GLOBAL_DIR = PHASE3_1_DIR.parent
TICKER_CACHE_DIR = GLOBAL_DIR / "PHASE3_narrative_ticker" / "cache"
CONFIG_DIR = PHASE3_1_DIR / "config"
CACHE_DAILY_DIR = PHASE3_1_DIR / "cache" / "daily"
RESULTS_DIR = PHASE3_1_DIR / "results"

for path in (CACHE_DAILY_DIR, RESULTS_DIR):
    path.mkdir(parents=True, exist_ok=True)

TODAY_STR = dt.datetime.now().strftime("%Y%m%d")


def normalize_url(url: Any) -> str:
    raw = str(url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not k.lower().startswith("utm_")
        and k.lower() not in {"fbclid", "gclid", "mc_cid", "mc_eid"}
    ]
    normalized = parsed._replace(
        scheme=parsed.scheme.lower() or "https",
        netloc=parsed.netloc.lower(),
        query=urlencode(query, doseq=True),
        fragment="",
    )
    return urlunparse(normalized).rstrip("/")


def article_id(row: pd.Series) -> str:
    canonical = normalize_url(row.get("url"))
    if not canonical:
        canonical = "|".join(
            [
                str(row.get("source_type", "")),
                str(row.get("source", "")),
                str(row.get("title", "")),
                str(row.get("published_at", "")),
            ]
        )
    return hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:16]


def parse_published_at(value: Any) -> pd.Timestamp:
    text = str(value or "").strip()
    if not text:
        return pd.NaT
    if re.fullmatch(r"\d{8}T\d{6}Z", text):
        return pd.to_datetime(text, format="%Y%m%dT%H%M%SZ", utc=True, errors="coerce")
    return pd.to_datetime(text, utc=True, errors="coerce")


def load_themes(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        themes = json.load(f)
    for theme in themes:
        theme["keywords"] = [str(x) for x in theme.get("keywords", [])]
        theme["exclude_keywords"] = [str(x) for x in theme.get("exclude_keywords", [])]
    return themes


def phrase_hits(text: str, phrase: str) -> int:
    phrase = phrase.strip()
    if not phrase:
        return 0
    pattern = r"(?<![A-Za-z0-9])" + re.escape(phrase.lower()) + r"(?![A-Za-z0-9])"
    return len(re.findall(pattern, text.lower()))


def match_theme(row: pd.Series, theme: dict[str, Any]) -> dict[str, Any] | None:
    title = str(row.get("title") or "")
    body = str(row.get("text") or "")
    haystack = f"{title}\n{body}"

    excluded: list[str] = []
    for term in theme.get("exclude_keywords", []):
        if phrase_hits(haystack, term):
            excluded.append(term)

    matched: list[str] = []
    score = 0
    for term in theme.get("keywords", []):
        title_hits = phrase_hits(title, term)
        body_hits = phrase_hits(body, term)
        if title_hits:
            score += 3
            matched.append(term)
        elif body_hits:
            score += 1
            matched.append(term)

    if excluded:
        score -= 3 * len(excluded)

    if score < 2:
        return None

    items = []
    for item in theme.get("items", []):
        if phrase_hits(haystack, item):
            items.append(item)

    return {
        "sector_group": theme["sector_group"],
        "theme": theme["theme"],
        "items": ";".join(sorted(set(items))),
        "theme_match_score": score,
        "matched_terms": ";".join(sorted(set(matched))),
        "excluded_terms": ";".join(sorted(set(excluded))),
    }


def load_raw(paths: list[Path]) -> pd.DataFrame:
    frames = []
    for path in paths:
        try:
            df = pd.read_csv(path, encoding="utf-8-sig", on_bad_lines="skip")
        except UnicodeDecodeError:
            df = pd.read_csv(path, on_bad_lines="skip")
        df["input_file"] = path.name
        frames.append(df)
    if not frames:
        raise FileNotFoundError("No input CSV files found.")
    raw = pd.concat(frames, ignore_index=True)
    for col in ["ticker", "company_name", "source_type", "source", "title", "text", "url", "published_at", "engagement"]:
        if col not in raw.columns:
            raw[col] = ""
    raw["published_at_ts"] = raw["published_at"].apply(parse_published_at)
    raw = raw.dropna(subset=["published_at_ts"]).copy()
    raw["date"] = raw["published_at_ts"].dt.date.astype(str)
    raw["canonical_url"] = raw["url"].apply(normalize_url)
    raw["article_id"] = raw.apply(article_id, axis=1)
    raw = raw.sort_values("published_at_ts", ascending=False)
    raw = raw.drop_duplicates(subset=["article_id"], keep="first").copy()
    raw["source_type"] = raw["source_type"].fillna("unknown").astype(str)
    raw["source"] = raw["source"].fillna("").astype(str)
    raw["title"] = raw["title"].fillna("").astype(str)
    raw["text"] = raw["text"].fillna("").astype(str)
    raw["engagement"] = pd.to_numeric(raw["engagement"], errors="coerce").fillna(0)
    return raw


def build_theme_matches(raw: pd.DataFrame, themes: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for _, row in raw.iterrows():
        matches = []
        for theme in themes:
            match = match_theme(row, theme)
            if match:
                matches.append(match)
        if not matches:
            continue
        fractional = 1.0 / len(matches)
        for match in matches:
            rows.append(
                {
                    "article_id": row["article_id"],
                    "date": row["date"],
                    "source_type": row["source_type"],
                    "source": row["source"],
                    "ticker": row.get("ticker", ""),
                    "title": row["title"],
                    "url": row.get("url", ""),
                    "published_at": row["published_at_ts"].isoformat(),
                    "engagement": row["engagement"],
                    "fractional_weight": fractional,
                    **match,
                }
            )
    return pd.DataFrame(rows)


def aggregate_daily(raw: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    source_totals = (
        raw.groupby(["date", "source_type"], as_index=False)
        .agg(total_source_articles=("article_id", "nunique"))
    )
    if matches.empty:
        return pd.DataFrame()
    daily = (
        matches.groupby(["date", "source_type", "sector_group", "theme"], as_index=False)
        .agg(
            article_count=("article_id", "nunique"),
            weighted_article_count=("fractional_weight", "sum"),
            unique_source_count=("source", "nunique"),
            engagement=("engagement", "sum"),
        )
    )
    daily = daily.merge(source_totals, on=["date", "source_type"], how="left")
    daily["share"] = daily["weighted_article_count"] / daily["total_source_articles"].replace(0, pd.NA)
    return daily


def percentile(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    return series.rank(pct=True, method="average") * 100.0


PURE_PLAY_TICKERS = {
    "AI Infrastructure": {"NVDA", "AMD", "AVGO", "TSM", "MRVL", "MU", "ASML", "ARM"},
    "Memory And HBM": {"MU", "WDC", "STX", "TSM", "ASML"},
    "Data Center Capex": {"NVDA", "AMD", "AVGO", "TSM", "MSFT", "AMZN", "GOOGL", "GOOG", "ORCL", "VRT", "ETN", "GEV", "CEG", "VST"},
    "Grid And Power Equipment": {"VRT", "ETN", "GEV", "BE", "CEG", "VST", "FSLR", "ENPH"},
    "Nuclear Renaissance": {"CCJ", "BWXT", "SMR", "CEG", "VST", "OKLO"},
    "GLP-1 And Obesity Drugs": {"LLY", "NVO", "HIMS", "AMGN", "VKTX"},
    "Stablecoin And Crypto Policy": {"COIN", "MSTR", "RIOT", "MARA", "CLSK", "HOOD", "V", "MA"},
    "Quantum Computing": {"IONQ", "RGTI", "QBTS", "QUBT", "IBM", "HON"},
    "Reshoring And Manufacturing": {"CAT", "ETN", "GEV", "HON", "DE", "EMR", "PH"},
    "Robotics And Automation": {"ISRG", "TER", "ROK", "ABB", "META", "NVDA", "TSLA", "ZBRA"},
    "Ecommerce And Ads": {"AMZN", "META", "GOOGL", "GOOG", "RDDT", "SHOP", "MELI"},
    "Smartphone And Devices": {"AAPL", "QCOM", "TSM", "AVGO", "SWKS"},
    "Tariffs And Supply Chain": set(),
    "Banking And Credit": {"JPM", "BAC", "WFC", "C", "GS", "MS"},
    "Earnings And Buybacks": set(),
    "Regulatory And Legal Risk": set(),
}

TITLE_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "for",
    "from",
    "has",
    "in",
    "is",
    "its",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "after",
    "amid",
    "by",
    "says",
    "stock",
    "stocks",
}


def normalize_ticker(value: Any) -> str:
    return str(value or "").strip().upper().replace("/", "-").replace(".", "-")


def title_tokens(title: Any) -> set[str]:
    text = re.sub(r"[^A-Za-z0-9 ]+", " ", str(title or "").lower())
    tokens = {x for x in text.split() if len(x) >= 3 and x not in TITLE_STOPWORDS}
    return tokens


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def top_headline_cluster_share(titles: list[str], threshold: float = 0.45) -> float:
    token_sets = [title_tokens(title) for title in titles if str(title or "").strip()]
    if not token_sets:
        return 0.0
    clusters: list[list[set[str]]] = []
    for tokens in token_sets:
        placed = False
        for cluster in clusters:
            if any(jaccard(tokens, existing) >= threshold for existing in cluster):
                cluster.append(tokens)
                placed = True
                break
        if not placed:
            clusters.append([tokens])
    return max(len(cluster) for cluster in clusters) / len(token_sets)


def confidence_bucket(score: float) -> str:
    if score >= 80:
        return "very_high"
    if score >= 65:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def classify_narrative(
    article_count: int,
    daily_active_days: int,
    event_concentration: float,
    pure_play_ratio: float,
    has_pure_play_map: bool,
    confidence_score: float,
) -> str:
    if article_count < 5:
        return "noise_possible"
    if event_concentration >= 0.65 and daily_active_days <= 3:
        return "single_event"
    if has_pure_play_map and pure_play_ratio < 0.25 and article_count < 15:
        return "derivative_mention"
    if confidence_score >= 70 and daily_active_days >= 4 and event_concentration < 0.60:
        return "sustained_narrative"
    if confidence_score >= 45:
        return "emerging_watch"
    return "noise_possible"


def confidence_metrics(theme_matches: pd.DataFrame, theme: str, article_count: int, unique_sources: int) -> dict[str, Any]:
    if theme_matches.empty or article_count <= 0:
        return {
            "unique_ticker_count_7d": 0,
            "top_ticker_share_7d": 0.0,
            "daily_active_days_7d": 0,
            "top_headline_cluster_share_7d": 0.0,
            "pure_play_ratio_7d": 0.0,
            "event_concentration_score": 0.0,
            "confidence_score_v2": 0.0,
            "adjusted_confidence": "low",
            "narrative_type": "noise_possible",
        }

    ticker_series = theme_matches["ticker"].dropna().map(normalize_ticker)
    ticker_series = ticker_series[ticker_series.astype(str).str.len() > 0]
    unique_ticker_count = int(ticker_series.nunique())
    top_ticker_share = float(ticker_series.value_counts(normalize=True).iloc[0]) if not ticker_series.empty else 0.0
    daily_active_days = int(theme_matches["date"].nunique())
    headline_cluster_share = top_headline_cluster_share(theme_matches["title"].dropna().astype(str).tolist())

    pure_play_set = PURE_PLAY_TICKERS.get(theme, set())
    has_pure_play_map = bool(pure_play_set)
    if has_pure_play_map and not ticker_series.empty:
        pure_play_ratio = float(ticker_series.isin(pure_play_set).mean())
    elif has_pure_play_map:
        pure_play_ratio = 0.0
    else:
        pure_play_ratio = 0.5

    count_component = 1.0 if article_count >= 50 else 0.8 if article_count >= 20 else 0.6 if article_count >= 10 else 0.35 if article_count >= 5 else 0.15
    persistence_component = min(daily_active_days / 7.0, 1.0)
    breadth_component = min(unique_sources / 10.0, 1.0)
    ticker_diversity_component = min(unique_ticker_count / 5.0, 1.0) * (1.0 - min(top_ticker_share, 1.0))
    pure_play_component = pure_play_ratio if has_pure_play_map else 0.5
    event_concentration = max(top_ticker_share, headline_cluster_share)
    event_penalty = max(0.0, event_concentration - 0.55) * 45.0

    confidence_score = 100.0 * (
        0.30 * count_component
        + 0.25 * persistence_component
        + 0.20 * breadth_component
        + 0.15 * ticker_diversity_component
        + 0.10 * pure_play_component
    ) - event_penalty
    confidence_score = max(0.0, min(100.0, confidence_score))
    narrative_type = classify_narrative(
        article_count,
        daily_active_days,
        event_concentration,
        pure_play_ratio,
        has_pure_play_map,
        confidence_score,
    )

    return {
        "unique_ticker_count_7d": unique_ticker_count,
        "top_ticker_share_7d": top_ticker_share,
        "daily_active_days_7d": daily_active_days,
        "top_headline_cluster_share_7d": headline_cluster_share,
        "pure_play_ratio_7d": pure_play_ratio,
        "event_concentration_score": event_concentration,
        "confidence_score_v2": confidence_score,
        "adjusted_confidence": confidence_bucket(confidence_score),
        "narrative_type": narrative_type,
    }


def source_share_change(last7: pd.DataFrame, prev30: pd.DataFrame, source_types: set[str], eps: float = 1e-4) -> float:
    last = last7[last7["source_type"].isin(source_types)]
    prev = prev30[prev30["source_type"].isin(source_types)]
    last_share = float(last["share"].sum() / 7.0) if not last.empty else 0.0
    prev_share = float(prev["share"].sum() / 30.0) if not prev.empty else 0.0
    return math.log((last_share + eps) / (prev_share + eps))


def score_latest(raw: pd.DataFrame, matches: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    if daily.empty:
        return pd.DataFrame()

    as_of = pd.to_datetime(raw["published_at_ts"].max()).tz_convert(None).normalize()
    dates = pd.to_datetime(daily["date"])
    daily = daily.copy()
    daily["date_ts"] = dates

    last7_start = as_of - pd.Timedelta(days=6)
    prev30_start = last7_start - pd.Timedelta(days=30)
    prev90_start = last7_start - pd.Timedelta(days=90)

    keys = ["sector_group", "theme"]
    rows = []
    for key, grp in daily.groupby(keys):
        last7 = grp[(grp["date_ts"] >= last7_start) & (grp["date_ts"] <= as_of)]
        prev30 = grp[(grp["date_ts"] >= prev30_start) & (grp["date_ts"] < last7_start)]
        prev90 = grp[(grp["date_ts"] >= prev90_start) & (grp["date_ts"] < last7_start)]

        last7_share = float(last7["share"].sum() / 7.0)
        prev30_share = float(prev30["share"].sum() / 30.0) if not prev30.empty else 0.0
        prev90_daily = prev90.groupby("date")["share"].sum()
        prev90_mean = float(prev90_daily.mean()) if not prev90_daily.empty else 0.0
        prev90_std = float(prev90_daily.std(ddof=0)) if len(prev90_daily) > 1 else 0.0

        eps = 1e-4
        log_change = math.log((last7_share + eps) / (prev30_share + eps))
        finnhub_company_log_change = source_share_change(last7, prev30, {"finnhub_news"}, eps)
        gdelt_log_change = source_share_change(last7, prev30, {"gdelt_news"}, eps)
        reddit_log_change = source_share_change(last7, prev30, {"reddit_post", "reddit_comment"}, eps)
        z_score = (last7_share - prev90_mean) / prev90_std if prev90_std > 0 else 0.0
        article_count_7d = int(last7["article_count"].sum())
        weighted_7d = float(last7["weighted_article_count"].sum())
        baseline_article_count_30d = float(prev30["article_count"].sum() / 30.0) if not prev30.empty else 0.0
        unique_sources_7d = int(last7["unique_source_count"].sum())
        reddit_engagement_7d = float(last7[last7["source_type"].isin({"reddit_post", "reddit_comment"})]["engagement"].sum())

        source_counts = last7.groupby("source_type")["weighted_article_count"].sum().to_dict()
        news_count = source_counts.get("gdelt_news", 0.0) + source_counts.get("finnhub_news", 0.0) + source_counts.get("finnhub_market_news", 0.0)
        retail_count = source_counts.get("reddit_post", 0.0) + source_counts.get("reddit_comment", 0.0)
        if retail_count > news_count:
            source_mix = "retail_led"
        elif retail_count > 0 and news_count > 0:
            source_mix = "broad_based"
        else:
            source_mix = "news_led"

        if article_count_7d < 3 or unique_sources_7d < 2:
            confidence = "low"
        elif article_count_7d >= 10 and unique_sources_7d >= 4:
            confidence = "high"
        else:
            confidence = "medium"

        if prev30.empty and article_count_7d > 0:
            direction = "new"
        elif log_change >= 0.5:
            direction = "rising"
        elif log_change <= -0.5:
            direction = "falling"
        else:
            direction = "stable"

        match_published = pd.to_datetime(matches["published_at"], utc=True).dt.tz_convert(None)
        theme_matches = matches[
            (matches["sector_group"] == key[0])
            & (matches["theme"] == key[1])
            & (match_published >= last7_start)
        ].copy()
        quality = confidence_metrics(theme_matches, key[1], article_count_7d, unique_sources_7d)
        sample_headlines = (
            theme_matches.sort_values(["engagement", "published_at"], ascending=False)["title"]
            .dropna()
            .drop_duplicates()
            .head(3)
            .tolist()
        )
        top_items = (
            theme_matches["items"]
            .dropna()
            .astype(str)
            .str.split(";")
            .explode()
            .loc[lambda x: x.astype(str).str.len() > 0]
            .value_counts()
            .head(5)
            .index.tolist()
        )

        rows.append(
            {
                "as_of_date": as_of.date().isoformat(),
                "sector_group": key[0],
                "theme": key[1],
                "top_items": ";".join(top_items),
                "log_share_change_7d_30d": log_change,
                "finnhub_company_log_change_7d_30d": finnhub_company_log_change,
                "gdelt_log_change_7d_30d": gdelt_log_change,
                "reddit_log_change_7d_30d": reddit_log_change,
                "z_score_7d_90d": z_score,
                "article_count_7d": article_count_7d,
                "weighted_article_count_7d": weighted_7d,
                "baseline_article_count_30d": baseline_article_count_30d,
                "unique_source_count_7d": unique_sources_7d,
                "reddit_engagement_7d": reddit_engagement_7d,
                "last7_share": last7_share,
                "prev30_share": prev30_share,
                "source_mix": source_mix,
                "direction": direction,
                "confidence": confidence,
                **quality,
                "sample_headlines": " | ".join(sample_headlines),
            }
        )

    ranking = pd.DataFrame(rows)
    if ranking.empty:
        return ranking
    ranking["log_change_pct"] = percentile(ranking["log_share_change_7d_30d"])
    ranking["finnhub_company_log_change_pct"] = percentile(ranking["finnhub_company_log_change_7d_30d"])
    ranking["gdelt_log_change_pct"] = percentile(ranking["gdelt_log_change_7d_30d"])
    ranking["reddit_log_change_pct"] = percentile(ranking["reddit_log_change_7d_30d"])
    ranking["reddit_engagement_pct"] = percentile(ranking["reddit_engagement_7d"])
    ranking["z_score_pct"] = percentile(ranking["z_score_7d_90d"])
    ranking["breadth_pct"] = percentile(ranking["unique_source_count_7d"])
    ranking["count_pct"] = percentile(ranking["article_count_7d"])
    ranking["news_attention"] = (
        0.80 * ranking["finnhub_company_log_change_pct"]
        + 0.20 * ranking["gdelt_log_change_pct"]
    )
    ranking["retail_attention"] = (
        0.60 * ranking["reddit_log_change_pct"]
        + 0.40 * ranking["reddit_engagement_pct"]
    )
    ranking["attention_score"] = (
        0.65 * ranking["news_attention"]
        + 0.15 * ranking["retail_attention"]
        + 0.15 * ranking["breadth_pct"]
        + 0.10 * ranking["z_score_pct"]
    )
    ranking = ranking.sort_values("attention_score", ascending=False).reset_index(drop=True)
    ranking.insert(1, "rank", range(1, len(ranking) + 1))
    return ranking


def write_report(path: Path, raw: pd.DataFrame, matches: pd.DataFrame, ranking: pd.DataFrame, input_paths: list[Path]) -> None:
    lines = [
        "# 내러티브 관심도 리포트",
        "",
        f"- 생성 시각: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"- 입력 파일 수: {len(input_paths)}",
        f"- URL 중복 제거 후 원문 수: {len(raw):,}",
        f"- 테마 매칭 행 수: {len(matches):,}",
        f"- 테마 매칭 기사 수: {matches['article_id'].nunique() if not matches.empty else 0:,}",
        "",
        "## 해석 주의",
        "",
        "이 리포트는 입력 파일의 범위에 따라 해석해야 한다. ticker-level 캐시를 입력으로 쓰면 시장 전체 랭킹이 아니라 파이프라인 검증 결과이고, live collector 결과를 입력으로 쓰면 수집한 테마/기간 내 관심도 랭킹이다.",
        "",
        "## 상위 테마",
        "",
    ]
    if ranking.empty:
        lines.append("매칭된 테마가 없습니다.")
    else:
        cols = [
            "rank",
            "sector_group",
            "theme",
            "attention_score",
            "direction",
            "adjusted_confidence",
            "narrative_type",
            "article_count_7d",
            "daily_active_days_7d",
            "event_concentration_score",
            "log_share_change_7d_30d",
            "source_mix",
        ]
        preview = ranking.head(12)[cols].copy()
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for _, row in preview.iterrows():
            values = []
            for col in cols:
                value = row[col]
                if isinstance(value, float):
                    value = f"{value:.2f}"
                values.append(str(value).replace("|", "/"))
            lines.append("| " + " | ".join(values) + " |")
        lines.extend(["", "## 대표 헤드라인", ""])
        for _, row in ranking.head(8).iterrows():
            lines.append(f"### {int(row['rank'])}. {row['theme']}")
            headlines = [x.strip() for x in str(row.get("sample_headlines", "")).split("|") if x.strip()]
            if headlines:
                for headline in headlines[:3]:
                    lines.append(f"- {headline}")
            else:
                lines.append("- 대표 헤드라인 없음.")
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def default_input_paths() -> list[Path]:
    paths = sorted(TICKER_CACHE_DIR.glob("*_90d_all_*_narrative_raw.csv"))
    if paths:
        return paths
    return sorted(TICKER_CACHE_DIR.glob("*_narrative_raw.csv"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs="*", type=Path, default=None, help="Raw narrative CSV files. Defaults to cached 90d_all files.")
    parser.add_argument("--themes", type=Path, default=CONFIG_DIR / "themes.json")
    parser.add_argument("--output-prefix", default=TODAY_STR)
    args = parser.parse_args()

    input_paths = args.input or default_input_paths()
    themes = load_themes(args.themes)
    raw = load_raw(input_paths)
    matches = build_theme_matches(raw, themes)
    daily = aggregate_daily(raw, matches)
    ranking = score_latest(raw, matches, daily)

    daily_path = CACHE_DAILY_DIR / f"{args.output_prefix}_daily_theme_attention.csv"
    debug_path = RESULTS_DIR / f"{args.output_prefix}_theme_match_debug.csv"
    ranking_path = RESULTS_DIR / f"{args.output_prefix}_latest_theme_ranking.csv"
    report_path = RESULTS_DIR / f"{args.output_prefix}_attention_report.md"

    daily.to_csv(daily_path, index=False, quoting=csv.QUOTE_MINIMAL)
    matches.to_csv(debug_path, index=False, quoting=csv.QUOTE_MINIMAL)
    ranking.to_csv(ranking_path, index=False, quoting=csv.QUOTE_MINIMAL)
    write_report(report_path, raw, matches, ranking, input_paths)

    print(f"원문_행수 {len(raw)}")
    print(f"테마_매칭_행수 {len(matches)}")
    print(f"테마_매칭_기사수 {matches['article_id'].nunique() if not matches.empty else 0}")
    print(f"일별_집계_파일 {daily_path}")
    print(f"디버그_파일 {debug_path}")
    print(f"랭킹_파일 {ranking_path}")
    print(f"리포트_파일 {report_path}")
    if not ranking.empty:
        print("상위5개_테마")
        print(
            ranking[
                [
                    "rank",
                    "theme",
                    "attention_score",
                    "direction",
                    "adjusted_confidence",
                    "narrative_type",
                    "article_count_7d",
                ]
            ]
            .head(5)
            .to_string(index=False)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
