#!/usr/bin/env python3
"""
Narrative x company analyzer.

기사에서 실제로 연결된 ticker를 중심으로 narrative별 기업 노출도를 계산하고,
사전에 정의한 beneficiary map 후보는 보조 watchlist 신호로만 붙인다.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE3_1_DIR = SCRIPT_DIR.parent
RESULTS_DIR = PHASE3_1_DIR / "results"
CONFIG_DIR = PHASE3_1_DIR / "config"
CACHE_DIR = PHASE3_1_DIR / "cache"
TODAY_STR = dt.datetime.now().strftime("%Y%m%d")

BUCKET_WEIGHT = {
    "pure_play": 100.0,
    "enabler": 80.0,
    "adopter": 55.0,
    "sympathetic": 35.0,
    "news_linked": 65.0,
}


def normalize_ticker(value: Any) -> str:
    return str(value or "").strip().upper().replace("/", "-").replace(".", "-")


def percentile(series: pd.Series, fill: float = 50.0) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    ranked = numeric.rank(pct=True, method="average") * 100.0
    return ranked.fillna(fill)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def flatten_beneficiary_map(mapping: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for theme, buckets in mapping.items():
        for bucket, tickers in buckets.items():
            if bucket == "keywords":
                continue
            for ticker in tickers:
                rows.append(
                    {
                        "theme": theme,
                        "ticker": normalize_ticker(ticker),
                        "bucket_type": bucket,
                        "bucket_weight": BUCKET_WEIGHT.get(bucket, 25.0),
                    }
                )
    return pd.DataFrame(rows).drop_duplicates(["theme", "ticker"], keep="first")


def price_confirmation(row: pd.Series) -> float:
    state = row.get("price_state")
    ret_1m = row.get("price_return_1m")
    rel_1m = row.get("relative_return_1m_spy")
    score = 50.0
    if pd.notna(rel_1m):
        score += max(min(float(rel_1m), 30.0), -30.0) * 0.8
    if pd.notna(ret_1m):
        score += max(min(float(ret_1m), 40.0), -20.0) * 0.3
    if state == "confirming":
        score += 10.0
    elif state == "lagging":
        score -= 15.0
    elif state == "extended":
        score -= 10.0
    elif state == "overheated":
        score -= 25.0
    return max(min(score, 100.0), 0.0)


def classify_role(row: pd.Series) -> str:
    bucket = row.get("bucket_type")
    article_count = row.get("article_count_7d", 0)
    narrative_type = row.get("theme_narrative_type", "")
    if article_count > 0 and narrative_type == "derivative_mention" and bucket in {"enabler", "adopter", "news_linked"}:
        return "derivative_news_linked"
    if article_count > 0 and bucket == "pure_play":
        return "direct_pure_play"
    if article_count > 0 and bucket in {"enabler", "adopter", "sympathetic"}:
        return f"news_linked_{bucket}"
    if article_count > 0:
        return "news_linked_unmapped"
    if bucket == "pure_play":
        return "mapped_pure_play_watch"
    return "mapped_watch"


def confidence_to_score(confidence: Any) -> float:
    return {
        "very_high": 100.0,
        "high": 82.0,
        "medium": 62.0,
        "low": 35.0,
    }.get(str(confidence or "").strip(), 50.0)


def build_theme_summary(matrix: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for theme, grp in matrix.groupby("theme", sort=False):
        first = grp.iloc[0]
        linked = grp[grp["article_count_7d"] > 0]
        mapped_pure = grp[(grp["article_count_7d"] == 0) & (grp["bucket_type"] == "pure_play")]
        linked_top = linked.sort_values("company_narrative_score", ascending=False).head(5)
        pure_top = mapped_pure.sort_values("company_narrative_score", ascending=False).head(5)
        direct_linked_count = int(len(linked))
        pure_linked_count = int(len(linked[linked["bucket_type"].eq("pure_play")]))
        company_support_score = min(
            100.0,
            direct_linked_count * 8.0
            + min(float(linked["source_breadth_7d"].sum()), 10.0) * 4.0
            + min(float(linked["article_count_7d"].sum()), 30.0) * 1.2
            + pure_linked_count * 8.0,
        )
        confidence_score = confidence_to_score(first.get("theme_adjusted_confidence"))
        type_penalty = {
            "sustained_narrative": 0.0,
            "emerging_watch": 5.0,
            "derivative_mention": 18.0,
            "single_event": 22.0,
            "noise_possible": 28.0,
        }.get(str(first.get("theme_narrative_type")), 10.0)
        investability_score = (
            0.40 * float(first.get("attention_score", 0.0))
            + 0.35 * company_support_score
            + 0.25 * confidence_score
            - type_penalty
        )
        if investability_score >= 75:
            verdict = "Core Candidate"
        elif investability_score >= 62:
            verdict = "Active Watch"
        elif investability_score >= 48:
            verdict = "Watch / Validate"
        else:
            verdict = "Low Priority"
        rows.append(
            {
                "rank": first.get("rank"),
                "theme": theme,
                "attention_score": first.get("attention_score"),
                "theme_adjusted_confidence": first.get("theme_adjusted_confidence"),
                "theme_narrative_type": first.get("theme_narrative_type"),
                "company_support_score": company_support_score,
                "investability_score": investability_score,
                "verdict": verdict,
                "news_linked_companies": ", ".join(linked_top["ticker"].astype(str).tolist()) if not linked_top.empty else "",
                "mapped_pure_play_watch": ", ".join(pure_top["ticker"].astype(str).tolist()) if not pure_top.empty else "",
            }
        )
    return pd.DataFrame(rows).sort_values("investability_score", ascending=False).reset_index(drop=True)


def build_matrix(ranking: pd.DataFrame, debug: pd.DataFrame, beneficiary: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    debug = debug.copy()
    debug["ticker"] = debug["ticker"].map(normalize_ticker)
    debug["published_at_ts"] = pd.to_datetime(debug["published_at"], utc=True, errors="coerce")
    latest_ts = debug["published_at_ts"].max()
    last7 = debug[debug["published_at_ts"] >= latest_ts - pd.Timedelta(days=6)].copy()

    article_linked = (
        last7.groupby(["theme", "ticker"], as_index=False)
        .agg(
            article_count_7d=("article_id", "nunique"),
            source_breadth_7d=("source", "nunique"),
            matched_item_count=("items", lambda s: sum(len([x for x in str(v).split(";") if x and x != "nan"]) for v in s)),
            sample_headlines=("title", lambda s: " | ".join(pd.Series(s).dropna().drop_duplicates().head(3).astype(str))),
        )
    )
    article_linked["bucket_type"] = "news_linked"
    article_linked["bucket_weight"] = BUCKET_WEIGHT["news_linked"]

    merged = pd.concat(
        [
            article_linked,
            mapping.assign(article_count_7d=0, source_breadth_7d=0, matched_item_count=0, sample_headlines=""),
        ],
        ignore_index=True,
    )
    merged = merged.sort_values(["theme", "ticker", "article_count_7d"], ascending=[True, True, False])
    merged = merged.drop_duplicates(["theme", "ticker"], keep="first")

    theme_cols = [
        "theme",
        "rank",
        "attention_score",
        "adjusted_confidence",
        "narrative_type",
        "article_count_7d",
        "unique_ticker_count_7d",
        "top_ticker_share_7d",
        "pure_play_ratio_7d",
    ]
    theme_info = ranking[[c for c in theme_cols if c in ranking.columns]].rename(
        columns={
            "article_count_7d": "theme_article_count_7d",
            "adjusted_confidence": "theme_adjusted_confidence",
            "narrative_type": "theme_narrative_type",
        }
    )
    merged = merged.merge(theme_info, on="theme", how="left")

    price_cols = [
        "theme",
        "ticker",
        "company_name",
        "sector",
        "industry",
        "price_return_5d",
        "price_return_1m",
        "price_return_3m",
        "relative_return_1m_spy",
        "price_state",
    ]
    if not beneficiary.empty:
        price = beneficiary[[c for c in price_cols if c in beneficiary.columns]].drop_duplicates(["theme", "ticker"], keep="first")
        merged = merged.merge(price, on=["theme", "ticker"], how="left")
        ticker_price_cols = [
            "ticker",
            "company_name",
            "sector",
            "industry",
            "price_return_5d",
            "price_return_1m",
            "price_return_3m",
            "relative_return_1m_spy",
            "price_state",
        ]
        ticker_price = (
            beneficiary[[c for c in ticker_price_cols if c in beneficiary.columns]]
            .dropna(subset=["ticker"])
            .drop_duplicates(["ticker"], keep="first")
        )
        merged = merged.merge(ticker_price, on="ticker", how="left", suffixes=("", "_ticker"))
        for col in ticker_price_cols:
            if col == "ticker":
                continue
            ticker_col = f"{col}_ticker"
            if ticker_col in merged.columns:
                if col in merged.columns:
                    merged[col] = merged[col].combine_first(merged[ticker_col])
                else:
                    merged[col] = merged[ticker_col]
                merged = merged.drop(columns=[ticker_col])

    merged["bucket_weight"] = merged["bucket_weight"].fillna(BUCKET_WEIGHT["news_linked"])
    merged["article_exposure_pct"] = merged.groupby("theme")["article_count_7d"].transform(percentile)
    merged["source_breadth_pct"] = merged.groupby("theme")["source_breadth_7d"].transform(percentile)
    merged["context_relevance_pct"] = merged.groupby("theme")["matched_item_count"].transform(percentile)
    merged["pure_play_fit"] = merged["bucket_weight"]
    merged["price_confirmation"] = merged.apply(price_confirmation, axis=1)

    derivative_penalty = (
        (merged["theme_narrative_type"].eq("derivative_mention") & (merged["article_count_7d"].eq(0))).astype(float) * 20.0
        + (merged["theme_narrative_type"].eq("single_event")).astype(float) * 15.0
    )
    mapped_only_penalty = merged["article_count_7d"].eq(0).astype(float) * 12.0
    merged["company_narrative_score"] = (
        0.35 * merged["article_exposure_pct"]
        + 0.20 * merged["context_relevance_pct"]
        + 0.20 * merged["pure_play_fit"]
        + 0.15 * merged["price_confirmation"]
        + 0.10 * merged["source_breadth_pct"]
        - 0.15 * derivative_penalty
        - 0.15 * mapped_only_penalty
    )
    merged["company_narrative_role"] = merged.apply(classify_role, axis=1)
    merged["interpretation_flag"] = "normal"
    merged.loc[merged["article_count_7d"].eq(0), "interpretation_flag"] = "mapped_only_needs_news_confirmation"
    merged.loc[
        merged["theme_narrative_type"].eq("derivative_mention") & merged["article_count_7d"].gt(0),
        "interpretation_flag",
    ] = "news_linked_but_derivative_theme"
    merged.loc[merged["price_state"].isin(["overheated", "extended"]), "interpretation_flag"] += ";price_risk"

    return merged.sort_values(["rank", "theme", "company_narrative_score"], ascending=[True, True, False]).reset_index(drop=True)


def write_report(path: Path, matrix: pd.DataFrame, top_themes: int) -> None:
    summary = build_theme_summary(matrix)
    lines = [
        "# Integrated Narrative x Company Analysis",
        "",
        f"- 생성 시각: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"- 분석 행 수: {len(matrix):,}",
        "- 해석 원칙: theme attention score로 내러티브 열기를 보고, company support score로 실제 기업 연결 품질을 검증한다.",
        "- beneficiary map 후보는 뉴스 직접 연결이 없으면 watchlist로만 본다.",
        "",
    ]
    summary_cols = [
        "theme",
        "attention_score",
        "theme_adjusted_confidence",
        "theme_narrative_type",
        "company_support_score",
        "investability_score",
        "verdict",
        "news_linked_companies",
        "mapped_pure_play_watch",
    ]
    lines.append("## 통합 우선순위")
    lines.append("")
    lines.append("| " + " | ".join(summary_cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(summary_cols)) + " |")
    for _, row in summary.head(top_themes)[summary_cols].iterrows():
        values = []
        for col in summary_cols:
            val = row[col]
            if isinstance(val, float):
                val = f"{val:.2f}"
            values.append(str(val).replace("|", "/"))
        lines.append("| " + " | ".join(values) + " |")
    lines.append("")

    cols = [
        "ticker",
        "company_narrative_role",
        "company_narrative_score",
        "article_count_7d",
        "source_breadth_7d",
        "bucket_type",
        "price_return_1m",
        "relative_return_1m_spy",
        "price_state",
        "interpretation_flag",
    ]
    themes = summary.head(top_themes)
    for _, theme_row in themes.iterrows():
        theme = theme_row["theme"]
        lines.append(f"## {theme}")
        lines.append(
            f"- attention: {theme_row['attention_score']:.2f}, company_support: {theme_row['company_support_score']:.2f}, investability: {theme_row['investability_score']:.2f}, verdict: {theme_row['verdict']}"
        )
        lines.append(f"- confidence: {theme_row['theme_adjusted_confidence']}, type: {theme_row['theme_narrative_type']}")
        lines.append("")
        grp = matrix[matrix["theme"] == theme].sort_values("company_narrative_score", ascending=False).head(12)
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for _, row in grp[cols].iterrows():
            values = []
            for col in cols:
                val = row[col]
                if isinstance(val, float):
                    val = f"{val:.2f}"
                values.append(str(val).replace("|", "/"))
            lines.append("| " + " | ".join(values) + " |")
        lines.append("")
        linked = grp[grp["article_count_7d"] > 0]["ticker"].head(5).tolist()
        mapped = grp[grp["article_count_7d"] == 0]["ticker"].head(5).tolist()
        lines.append(f"- 뉴스가 실제 연결한 기업: {', '.join(linked) if linked else '없음'}")
        lines.append(f"- 뉴스 확인이 더 필요한 테마 후보: {', '.join(mapped) if mapped else '없음'}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranking", type=Path, default=RESULTS_DIR / "20260503_live_finnhub_37d_top25_v3_latest_theme_ranking.csv")
    parser.add_argument("--debug", type=Path, default=RESULTS_DIR / "20260503_live_finnhub_37d_top25_v3_theme_match_debug.csv")
    parser.add_argument("--beneficiary", type=Path, default=RESULTS_DIR / "20260503_live_finnhub_37d_top25_beneficiary_candidates.csv")
    parser.add_argument("--beneficiary-map", type=Path, default=CONFIG_DIR / "theme_beneficiary_map.json")
    parser.add_argument("--top-themes", type=int, default=10)
    parser.add_argument("--output-prefix", default=f"{TODAY_STR}_narrative_company_matrix")
    args = parser.parse_args()

    ranking = pd.read_csv(args.ranking)
    debug = pd.read_csv(args.debug)
    beneficiary = pd.read_csv(args.beneficiary) if args.beneficiary.exists() else pd.DataFrame()
    mapping = flatten_beneficiary_map(load_json(args.beneficiary_map))
    matrix = build_matrix(ranking, debug, beneficiary, mapping)

    csv_path = RESULTS_DIR / f"{args.output_prefix}.csv"
    report_path = RESULTS_DIR / f"{args.output_prefix}.md"
    matrix.to_csv(csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
    write_report(report_path, matrix, args.top_themes)

    print(f"matrix_csv {csv_path}")
    print(f"report_md {report_path}")
    print(f"rows {len(matrix)}")
    print(
        matrix[
            [
                "rank",
                "theme",
                "ticker",
                "company_narrative_role",
                "company_narrative_score",
                "article_count_7d",
                "price_return_1m",
                "price_state",
                "interpretation_flag",
            ]
        ]
        .head(40)
        .to_string(index=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
