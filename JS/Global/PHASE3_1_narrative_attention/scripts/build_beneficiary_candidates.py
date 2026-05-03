#!/usr/bin/env python3
"""
Narrative beneficiary candidate builder.

Attention ranking에서 신뢰 가능한 theme를 고르고, theme_beneficiary_map.json의
bucket 후보군에 최근 주가/거래량 변화를 붙여 수혜주 리서치 후보 리스트를 만든다.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE3_1_DIR = SCRIPT_DIR.parent
CONFIG_DIR = PHASE3_1_DIR / "config"
RESULTS_DIR = PHASE3_1_DIR / "results"
CACHE_DIR = PHASE3_1_DIR / "cache"
PRICE_CACHE_DIR = CACHE_DIR / "price"

for path in (RESULTS_DIR, PRICE_CACHE_DIR):
    path.mkdir(parents=True, exist_ok=True)

TODAY_STR = dt.datetime.now().strftime("%Y%m%d")

BUCKET_WEIGHT = {
    "pure_play": 1.00,
    "enabler": 0.80,
    "adopter": 0.55,
    "sympathetic": 0.35,
}


def normalize_ticker(value: Any) -> str:
    return str(value or "").strip().upper().replace("/", "-").replace(".", "-")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def latest_file(pattern: str) -> Path:
    matches = sorted(Path().glob(pattern))
    if not matches:
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {pattern}")
    return matches[-1]


def pct_change_from_prices(close: pd.Series, periods: int) -> float:
    close = close.dropna()
    if len(close) <= periods:
        return float("nan")
    start = close.iloc[-periods - 1]
    end = close.iloc[-1]
    if not start:
        return float("nan")
    return (end / start - 1.0) * 100.0


def fetch_price_metrics(tickers: list[str], cache_prefix: str) -> pd.DataFrame:
    import yfinance as yf

    yf_tickers = sorted(set(tickers + ["SPY"]))
    cache_path = PRICE_CACHE_DIR / f"{cache_prefix}_price_metrics.csv"
    print(f"[가격] yfinance 다운로드: {len(yf_tickers)}개")
    data = yf.download(
        tickers=yf_tickers,
        period="1y",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        threads=True,
        progress=False,
    )

    rows = []
    spy_close = extract_close(data, "SPY", len(yf_tickers))
    spy_1m = pct_change_from_prices(spy_close, 21) if spy_close is not None else float("nan")

    for ticker in yf_tickers:
        close = extract_close(data, ticker, len(yf_tickers))
        volume = extract_volume(data, ticker, len(yf_tickers))
        if close is None or close.dropna().empty:
            rows.append({"ticker": ticker, "price_data_ok": False})
            continue
        close = close.dropna()
        last_price = float(close.iloc[-1])
        high_52w = float(close.max())
        distance_from_52w_high = (last_price / high_52w - 1.0) * 100.0 if high_52w else float("nan")
        ret_5d = pct_change_from_prices(close, 5)
        ret_1m = pct_change_from_prices(close, 21)
        ret_3m = pct_change_from_prices(close, 63)
        rel_1m = ret_1m - spy_1m if pd.notna(ret_1m) and pd.notna(spy_1m) else float("nan")

        volume_change = float("nan")
        if volume is not None:
            volume = volume.dropna()
            if len(volume) >= 40:
                recent = volume.tail(5).mean()
                base = volume.tail(25).head(20).mean()
                volume_change = (recent / base - 1.0) * 100.0 if base else float("nan")

        rows.append(
            {
                "ticker": ticker,
                "price_data_ok": True,
                "last_price": last_price,
                "price_return_5d": ret_5d,
                "price_return_1m": ret_1m,
                "price_return_3m": ret_3m,
                "relative_return_1m_spy": rel_1m,
                "volume_change_20d": volume_change,
                "distance_from_52w_high": distance_from_52w_high,
            }
        )

    out = pd.DataFrame(rows)
    out.to_csv(cache_path, index=False)
    return out


def extract_close(data: pd.DataFrame, ticker: str, ticker_count: int) -> pd.Series | None:
    try:
        if isinstance(data.columns, pd.MultiIndex):
            return data[ticker]["Close"].copy()
        if ticker_count == 1 or ticker == "SPY":
            return data["Close"].copy()
    except Exception:
        return None
    return None


def extract_volume(data: pd.DataFrame, ticker: str, ticker_count: int) -> pd.Series | None:
    try:
        if isinstance(data.columns, pd.MultiIndex):
            return data[ticker]["Volume"].copy()
        if ticker_count == 1 or ticker == "SPY":
            return data["Volume"].copy()
    except Exception:
        return None
    return None


def percentile(series: pd.Series, fill: float = 50.0) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    ranked = numeric.rank(pct=True, method="average") * 100.0
    return ranked.fillna(fill)


def inverse_percentile(series: pd.Series, fill: float = 50.0) -> pd.Series:
    return 100.0 - percentile(series, fill=fill)


def price_state(row: pd.Series) -> str:
    ret_1m = row.get("price_return_1m")
    rel_1m = row.get("relative_return_1m_spy")
    dist_high = row.get("distance_from_52w_high")
    if pd.notna(ret_1m) and ret_1m >= 35:
        return "overheated"
    if pd.notna(dist_high) and dist_high >= -5 and pd.notna(ret_1m) and ret_1m >= 15:
        return "extended"
    if pd.notna(rel_1m) and rel_1m >= 5:
        return "confirming"
    if pd.notna(rel_1m) and rel_1m <= -10:
        return "lagging"
    return "neutral"


def load_company_map() -> dict[str, dict[str, Any]]:
    path = Path("JSInvestment/JS/Global/PHASE0_classification/nasdaq_screener.csv")
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    df["ticker"] = df["Symbol"].map(normalize_ticker)
    df = df.drop_duplicates(subset=["ticker"], keep="first")
    return df.set_index("ticker").to_dict("index")


def selected_themes(ranking: pd.DataFrame, requested: str, include_top_attention: int) -> list[str]:
    if requested:
        return [x.strip() for x in requested.split(",") if x.strip()]
    eligible = ranking[
        ranking["narrative_type"].isin(["sustained_narrative", "emerging_watch"])
        & ranking["adjusted_confidence"].isin(["very_high", "high", "medium"])
    ].copy()
    top_attention = ranking.sort_values("attention_score", ascending=False).head(include_top_attention)
    themes = list(dict.fromkeys(eligible["theme"].tolist() + top_attention["theme"].tolist()))
    return themes


def build_candidates(
    ranking: pd.DataFrame,
    debug: pd.DataFrame,
    raw: pd.DataFrame,
    beneficiary_map: dict[str, Any],
    themes: list[str],
) -> pd.DataFrame:
    company_map = load_company_map()
    raw["ticker_norm"] = raw.get("ticker", "").map(normalize_ticker)
    debug["ticker_norm"] = debug.get("ticker", "").map(normalize_ticker)

    latest_ts = pd.to_datetime(raw["published_at"], utc=True, errors="coerce").max()
    last7_start = latest_ts - pd.Timedelta(days=6)
    raw["published_at_ts"] = pd.to_datetime(raw["published_at"], utc=True, errors="coerce")
    debug["published_at_ts"] = pd.to_datetime(debug["published_at"], utc=True, errors="coerce")

    raw_7d = raw[raw["published_at_ts"] >= last7_start].copy()
    debug_7d = debug[debug["published_at_ts"] >= last7_start].copy()
    total_news_by_ticker = raw_7d.groupby("ticker_norm")["url"].nunique().to_dict()

    rows = []
    for theme in themes:
        if theme not in beneficiary_map:
            continue
        theme_rank = ranking[ranking["theme"] == theme]
        if theme_rank.empty:
            continue
        rank_row = theme_rank.iloc[0].to_dict()
        theme_debug = debug_7d[debug_7d["theme"] == theme].copy()
        theme_counts = theme_debug.groupby("ticker_norm")["article_id"].nunique().to_dict() if not theme_debug.empty else {}
        source_breadth = theme_debug.groupby("ticker_norm")["source"].nunique().to_dict() if not theme_debug.empty else {}
        item_counts = (
            theme_debug.assign(item_count=theme_debug["items"].fillna("").astype(str).map(lambda x: len([i for i in x.split(";") if i])))
            .groupby("ticker_norm")["item_count"]
            .sum()
            .to_dict()
            if not theme_debug.empty
            else {}
        )

        for bucket, tickers in beneficiary_map[theme].items():
            if bucket == "keywords":
                continue
            for ticker in tickers:
                ticker_norm = normalize_ticker(ticker)
                company = company_map.get(ticker_norm, {})
                theme_news_count = int(theme_counts.get(ticker_norm, 0))
                total_news_count = int(total_news_by_ticker.get(ticker_norm, 0))
                theme_news_share = theme_news_count / total_news_count if total_news_count else 0.0
                rows.append(
                    {
                        "theme": theme,
                        "ticker": ticker_norm,
                        "company_name": company.get("Name", ""),
                        "sector": company.get("Sector", ""),
                        "industry": company.get("Industry", ""),
                        "bucket_type": bucket,
                        "bucket_weight": BUCKET_WEIGHT.get(bucket, 0.25),
                        "theme_attention_score": rank_row.get("attention_score"),
                        "theme_adjusted_confidence": rank_row.get("adjusted_confidence"),
                        "theme_narrative_type": rank_row.get("narrative_type"),
                        "theme_log_change_7d_30d": rank_row.get("log_share_change_7d_30d"),
                        "theme_news_count_7d": theme_news_count,
                        "ticker_total_news_7d": total_news_count,
                        "theme_news_share_7d": theme_news_share,
                        "matched_item_count": int(item_counts.get(ticker_norm, 0)),
                        "source_breadth_7d": int(source_breadth.get(ticker_norm, 0)),
                    }
                )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.drop_duplicates(subset=["theme", "ticker"], keep="first").reset_index(drop=True)
    return out


def score_candidates(candidates: pd.DataFrame, price: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return candidates
    out = candidates.merge(price, on="ticker", how="left")
    out["price_state"] = out.apply(price_state, axis=1)

    out["theme_news_share_pct"] = out.groupby("theme")["theme_news_share_7d"].transform(percentile)
    out["theme_news_count_pct"] = out.groupby("theme")["theme_news_count_7d"].transform(percentile)
    out["matched_item_count_pct"] = out.groupby("theme")["matched_item_count"].transform(percentile)
    out["bucket_weight_pct"] = out.groupby("theme")["bucket_weight"].transform(percentile)
    out["source_breadth_pct"] = out.groupby("theme")["source_breadth_7d"].transform(percentile)

    out["momentum_1m_pct"] = out.groupby("theme")["price_return_1m"].transform(percentile)
    out["relative_strength_pct"] = out.groupby("theme")["relative_return_1m_spy"].transform(percentile)
    out["volume_spike_pct"] = out.groupby("theme")["volume_change_20d"].transform(percentile)

    out["overextension_pct"] = out.groupby("theme")["price_return_1m"].transform(percentile)
    out["near_high_risk_pct"] = out.groupby("theme")["distance_from_52w_high"].transform(percentile)

    out["exposure_score"] = (
        0.35 * out["theme_news_share_pct"]
        + 0.25 * out["theme_news_count_pct"]
        + 0.20 * out["matched_item_count_pct"]
        + 0.20 * out["bucket_weight_pct"]
    )
    out["purity_score"] = (
        0.80 * out["bucket_weight_pct"]
        + 0.20 * out["matched_item_count_pct"]
    )
    out["confirmation_score"] = (
        0.35 * out["momentum_1m_pct"]
        + 0.25 * out["relative_strength_pct"]
        + 0.20 * out["volume_spike_pct"]
        + 0.20 * out["source_breadth_pct"]
    )
    out["risk_penalty"] = (
        0.45 * out["overextension_pct"]
        + 0.25 * out["near_high_risk_pct"]
        + 0.30 * (out["price_state"].isin(["overheated", "extended"]).astype(float) * 100.0)
    )
    out["beneficiary_score"] = (
        0.40 * out["exposure_score"]
        + 0.25 * out["purity_score"]
        + 0.25 * out["confirmation_score"]
        - 0.20 * out["risk_penalty"]
    )

    out["beneficiary_tier"] = "Watch Only"
    out.loc[(out["beneficiary_score"] >= 65) & (out["bucket_type"] == "pure_play"), "beneficiary_tier"] = "Tier 1: Direct Beneficiary"
    out.loc[(out["beneficiary_score"] >= 60) & (out["bucket_type"].isin(["enabler", "adopter"])), "beneficiary_tier"] = "Tier 2: Enabler / Quality"
    out.loc[(out["beneficiary_score"] >= 50) & (out["bucket_type"] == "sympathetic"), "beneficiary_tier"] = "Tier 3: Optionality"
    out.loc[out["price_state"].eq("overheated"), "beneficiary_tier"] = "Watch Only: Price Extended"

    return out.sort_values(["theme", "beneficiary_score"], ascending=[True, False]).reset_index(drop=True)


def write_report(path: Path, scored: pd.DataFrame) -> None:
    lines = [
        "# Narrative Beneficiary Candidate Report",
        "",
        f"- 생성 시각: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"- 후보 수: {len(scored):,}",
        "",
    ]
    if scored.empty:
        lines.append("후보가 없습니다.")
        path.write_text("\n".join(lines), encoding="utf-8")
        return

    for theme, grp in scored.groupby("theme", sort=False):
        lines.append(f"## {theme}")
        lines.append("")
        cols = [
            "ticker",
            "bucket_type",
            "beneficiary_score",
            "beneficiary_tier",
            "price_return_5d",
            "price_return_1m",
            "price_return_3m",
            "relative_return_1m_spy",
            "price_state",
            "theme_news_count_7d",
        ]
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for _, row in grp.head(12)[cols].iterrows():
            values = []
            for col in cols:
                val = row[col]
                if isinstance(val, float):
                    val = f"{val:.2f}"
                values.append(str(val).replace("|", "/"))
            lines.append("| " + " | ".join(values) + " |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranking", type=Path, default=RESULTS_DIR / "20260503_live_finnhub_37d_top25_v3_latest_theme_ranking.csv")
    parser.add_argument("--debug", type=Path, default=RESULTS_DIR / "20260503_live_finnhub_37d_top25_v3_theme_match_debug.csv")
    parser.add_argument("--raw", type=Path, default=PHASE3_1_DIR / "cache" / "raw" / "20260503_live_finnhub_37d_top25_attention_raw.csv")
    parser.add_argument("--beneficiary-map", type=Path, default=CONFIG_DIR / "theme_beneficiary_map.json")
    parser.add_argument("--themes", default="", help="Comma-separated theme override. Empty means eligible themes from ranking.")
    parser.add_argument(
        "--include-top-attention",
        type=int,
        default=5,
        help="Also include top-N themes by attention score, even when confidence layer marks them as derivative/noise watch.",
    )
    parser.add_argument("--output-prefix", default=f"{TODAY_STR}_beneficiary_candidates")
    args = parser.parse_args()

    ranking = pd.read_csv(args.ranking)
    debug = pd.read_csv(args.debug)
    raw = pd.read_csv(args.raw, encoding="utf-8-sig", on_bad_lines="skip")
    beneficiary_map = load_json(args.beneficiary_map)
    themes = selected_themes(ranking, args.themes, args.include_top_attention)
    candidates = build_candidates(ranking, debug, raw, beneficiary_map, themes)
    price = fetch_price_metrics(candidates["ticker"].dropna().astype(str).tolist(), args.output_prefix) if not candidates.empty else pd.DataFrame()
    scored = score_candidates(candidates, price)

    csv_path = RESULTS_DIR / f"{args.output_prefix}.csv"
    report_path = RESULTS_DIR / f"{args.output_prefix}.md"
    scored.to_csv(csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
    write_report(report_path, scored)

    print(f"후보_파일 {csv_path}")
    print(f"리포트_파일 {report_path}")
    print(f"후보_수 {len(scored)}")
    if not scored.empty:
        print(scored[["theme", "ticker", "bucket_type", "beneficiary_score", "price_return_1m", "price_state", "beneficiary_tier"]].head(20).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
