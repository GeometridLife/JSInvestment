#!/usr/bin/env python3
"""
Build per-document narrative debug rows from raw narrative CSV files.

This script is intentionally lightweight. It applies ticker-specific keyword
profiles before the later qualitative phase so the debug CSV is readable and
auditable without an LLM in the loop.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import math
import re
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE3_DIR = SCRIPT_DIR.parent
CACHE_DIR = PHASE3_DIR / "cache"
RESULTS_DIR = PHASE3_DIR / "results"
TODAY_STR = dt.datetime.now().strftime("%Y%m%d")


POSITIVE_TERMS = [
    "beat",
    "beats",
    "strong",
    "growth",
    "growing",
    "raised",
    "raise",
    "upgrade",
    "outperform",
    "buy",
    "bullish",
    "surge",
    "rally",
    "record",
    "expansion",
    "adoption",
    "accelerate",
    "momentum",
    "higher",
    "profit",
    "profitable",
]

NEGATIVE_TERMS = [
    "miss",
    "misses",
    "weak",
    "downgrade",
    "underperform",
    "sell",
    "bearish",
    "fall",
    "falls",
    "drop",
    "drops",
    "decline",
    "risk",
    "concern",
    "concerns",
    "expensive",
    "overvalued",
    "lawsuit",
    "recall",
    "pressure",
    "slowdown",
    "competition",
]


PROFILES = {
    "JPM": {
        "min_relevance_score": 5,
        "company_terms": [
            "JPMorgan Chase",
            "JPMorgan",
            "JP Morgan",
            "JPM",
            "$JPM",
            "Jamie Dimon",
            "Dimon",
        ],
        "relevance_terms": [
            "net interest income",
            "NII",
            "net interest margin",
            "NIM",
            "investment banking",
            "trading revenue",
            "loan loss",
            "credit loss",
            "provision",
            "deposits",
            "capital return",
            "stress test",
            "Basel",
            "credit card",
        ],
        "reddit_title_terms": [
            "JPM",
            "JPMorgan",
            "JP Morgan",
            "Jamie Dimon",
            "Dimon",
            "bank",
            "banks",
        ],
        "news_title_terms": [
            "JPM",
            "JPMorgan",
            "JPMorganChase",
            "JP Morgan",
            "Jamie Dimon",
            "Dimon",
        ],
        "exclude_title_patterns": [
            r"^(?:JP Morgan|JPMorgan) (?:retains|maintains|cuts|raises|boosts|lifts|trims|downgrades|upgrades|initiates)\b",
            r"^JPMorgan and .*\b(?:boost|boosts|bullish|raise|raises|cut|cuts)\b",
            r"^JPMorgan, Pimco\b",
            r"^Wall Street Lifts\b",
            r"^How The .* Story Is Shifting\b",
            r"^How The .* Investment Narrative Is Shifting\b",
        ],
        "categories": {
            "earnings_profitability": [
                "earnings",
                "profit",
                "profits",
                "revenue",
                "eps",
                "beat",
                "guidance",
                "quarter",
                "q1",
                "q2",
                "results",
                "return on equity",
                "roe",
            ],
            "nii_margin_rates": [
                "net interest income",
                "nii",
                "net interest margin",
                "nim",
                "interest income",
                "rates",
                "interest rates",
                "deposit beta",
                "funding cost",
            ],
            "credit_risk_provisions": [
                "credit",
                "credit risk",
                "credit cycle",
                "loan loss",
                "credit loss",
                "provision",
                "charge-off",
                "charge offs",
                "delinquency",
                "default",
                "recession",
            ],
            "investment_banking_markets": [
                "investment banking",
                "m&a",
                "ipo",
                "advisory",
                "underwriting",
                "deal",
                "deals",
                "capital markets",
                "trading revenue",
                "markets revenue",
            ],
            "consumer_cards_deposits": [
                "consumer",
                "credit card",
                "cards",
                "deposits",
                "checking",
                "mortgage",
                "auto loan",
                "consumer banking",
            ],
            "dimond_ceo_governance": [
                "jamie dimon",
                "dimon",
                "ceo",
                "succession",
                "leadership",
                "shareholder letter",
                "annual letter",
            ],
            "regulation_capital": [
                "regulation",
                "regulatory",
                "basel",
                "basel iii",
                "capital requirement",
                "capital rules",
                "stress test",
                "ccar",
                "fed",
                "federal reserve",
            ],
            "capital_return_buyback": [
                "buyback",
                "repurchase",
                "dividend",
                "capital return",
                "payout",
                "shareholder return",
            ],
            "ai_technology_fintech": [
                "ai",
                "artificial intelligence",
                "technology",
                "fintech",
                "digital",
                "payments",
                "blockchain",
                "crypto",
                "automation",
            ],
            "valuation_defensive_bank": [
                "valuation",
                "price target",
                "target price",
                "multiple",
                "premium",
                "discount",
                "defensive",
                "quality",
                "safe haven",
                "fortress balance sheet",
            ],
            "macro_geopolitical": [
                "tariff",
                "inflation",
                "recession",
                "economy",
                "geopolitical",
                "war",
                "oil",
                "hormuz",
                "market volatility",
            ],
        },
    },
    "BRK-B": {
        "min_relevance_score": 5,
        "company_terms": [
            "Berkshire Hathaway",
            "Berkshire Hathaway Inc",
            "BRK-B",
            "BRK.B",
            "BRK/A",
            "BRK/B",
        ],
        "relevance_terms": [
            "Warren Buffett",
            "Greg Abel",
            "shareholder meeting",
            "annual meeting",
            "operating earnings",
            "insurance float",
            "GEICO",
            "BNSF",
            "Berkshire Hathaway Energy",
        ],
        "reddit_title_terms": [
            "Berkshire",
            "BRK-B",
            "BRK.B",
            "BRK/A",
            "BRK/B",
            "Buffett",
            "Greg Abel",
        ],
        "categories": {
            "succession_governance": [
                "warren buffett",
                "greg abel",
                "succession",
                "successor",
                "ceo",
                "chairman",
                "munger",
                "annual meeting",
                "shareholder meeting",
                "omaha",
            ],
            "operating_earnings": [
                "operating earnings",
                "earnings",
                "profit",
                "profits",
                "net income",
                "cash flow",
                "quarter",
                "q1",
                "q2",
                "results",
            ],
            "cash_treasury_float": [
                "cash",
                "cash pile",
                "treasury",
                "treasury bills",
                "t-bills",
                "float",
                "insurance float",
                "liquidity",
                "dry powder",
            ],
            "insurance_geico": [
                "insurance",
                "geico",
                "underwriting",
                "premiums",
                "catastrophe",
                "reinsurance",
                "float",
                "claims",
            ],
            "buybacks_capital_allocation": [
                "buyback",
                "buybacks",
                "repurchase",
                "repurchases",
                "share repurchase",
                "capital allocation",
                "acquisition",
                "deal",
                "dividend",
            ],
            "apple_portfolio": [
                "apple",
                "aapl",
                "american express",
                "bank of america",
                "occidental",
                "chevron",
                "coca-cola",
                "equity portfolio",
                "stock portfolio",
                "holdings",
                "stake",
            ],
            "railroad_energy_industrial": [
                "bnsf",
                "railroad",
                "railway",
                "berkshire hathaway energy",
                "energy",
                "utilities",
                "pacificorp",
                "manufacturing",
                "industrial",
            ],
            "valuation_defensive": [
                "valuation",
                "book value",
                "intrinsic value",
                "premium",
                "discount",
                "defensive",
                "safe haven",
                "ballast",
                "compounder",
            ],
            "market_macro_rates": [
                "interest rates",
                "rates",
                "inflation",
                "recession",
                "market",
                "s&p 500",
                "treasuries",
                "fed",
                "tariff",
            ],
            "tax_accounting_noise": [
                "unrealized",
                "accounting",
                "gaap",
                "tax",
                "taxes",
                "investment gains",
                "investment losses",
            ],
        },
    },
    "ISRG": {
        "company_terms": [
            "Intuitive Surgical",
            "Intuitive Surgical Inc",
            "ISRG",
            "$ISRG",
            "da Vinci",
            "da Vinci 5",
        ],
        "relevance_terms": [
            "robotic surgery",
            "surgical robot",
            "surgical robotics",
            "minimally invasive",
            "procedure volume",
            "system placements",
            "installed base",
            "Ion",
        ],
        "categories": {
            "robotic_surgery_platform": [
                "robotic surgery",
                "surgical robot",
                "surgical robotics",
                "minimally invasive",
                "da vinci",
                "procedure volume",
            ],
            "da_vinci_5_adoption": [
                "da vinci 5",
                "dv5",
                "new system",
                "launch",
                "adoption",
                "placement",
                "placements",
                "installed base",
            ],
            "earnings_growth": [
                "earnings",
                "revenue",
                "sales",
                "profit",
                "eps",
                "beat",
                "guidance",
                "quarter",
                "q1",
                "q2",
                "growth",
            ],
            "procedure_volume_utilization": [
                "procedure",
                "procedures",
                "procedure volume",
                "utilization",
                "surgeries",
                "surgery",
                "elective",
                "demand",
            ],
            "installed_base_systems": [
                "installed base",
                "systems",
                "system placements",
                "placed",
                "capital equipment",
                "robot",
                "robots",
            ],
            "margin_cashflow": [
                "margin",
                "gross margin",
                "operating margin",
                "free cash flow",
                "cash flow",
                "fcf",
                "profitability",
            ],
            "valuation": [
                "valuation",
                "price target",
                "target price",
                "multiple",
                "premium",
                "expensive",
                "overvalued",
                "upgrade",
                "downgrade",
                "analyst",
            ],
            "competition": [
                "medtronic",
                "johnson & johnson",
                "j&j",
                "cmr surgical",
                "stryker",
                "hugo",
                "ottava",
                "competitor",
                "competition",
            ],
            "regulatory_safety": [
                "fda",
                "approval",
                "clearance",
                "regulatory",
                "recall",
                "litigation",
                "lawsuit",
                "safety",
            ],
            "hospital_capex_macro": [
                "hospital",
                "hospitals",
                "capex",
                "capital spending",
                "budget",
                "reimbursement",
                "procedure backlog",
                "utilization",
            ],
            "international_china": [
                "china",
                "europe",
                "japan",
                "international",
                "outside the u.s.",
                "ex-us",
                "tariff",
                "currency",
            ],
            "innovation_pipeline": [
                "ion",
                "lung biopsy",
                "single port",
                "sp",
                "instruments",
                "accessories",
                "digital",
                "imaging",
                "ai",
            ],
        },
    }
}


def term_hits(text: str, terms: list[str]) -> int:
    count = 0
    low = text.lower()
    for term in terms:
        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        if re.search(pattern, low):
            count += 1
    return count


def classify_tone(pos_hits: int, neg_hits: int) -> str:
    if pos_hits > neg_hits and pos_hits >= 1:
        return "positive"
    if neg_hits > pos_hits and neg_hits >= 1:
        return "negative"
    return "neutral"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build ticker narrative debug CSV.")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--raw", action="append", default=[], help="Raw CSV path. Can be passed multiple times.")
    parser.add_argument("--output", default=None)
    parser.add_argument("--days", type=int, default=90)
    return parser.parse_args()


def parse_published_at(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    missing = parsed.isna()
    if missing.any():
        reparsed = pd.to_datetime(
            series[missing],
            format="%Y%m%dT%H%M%SZ",
            errors="coerce",
            utc=True,
        )
        parsed.loc[missing] = reparsed
    return parsed


def default_raw_paths(ticker: str) -> list[str]:
    patterns = [
        str(CACHE_DIR / f"*_{ticker}_narrative_raw.csv"),
        str(CACHE_DIR / f"*_{ticker}_gdelt_news_raw.csv"),
    ]
    paths: list[str] = []
    for pattern in patterns:
        paths.extend(glob.glob(pattern))
    return sorted(set(paths))


def main() -> int:
    args = parse_args()
    ticker = args.ticker.upper()
    profile = PROFILES.get(ticker)
    if not profile:
        raise SystemExit(f"No keyword profile is configured for {ticker}")

    paths = args.raw or default_raw_paths(ticker)
    if not paths:
        raise SystemExit(f"No raw files found for {ticker}")

    frames = [pd.read_csv(path) for path in paths]
    raw = pd.concat(frames, ignore_index=True)
    raw = raw.drop_duplicates(subset=["ticker", "source_type", "url", "title"], keep="first")
    raw["published_at"] = parse_published_at(raw["published_at"])

    company_terms = profile["company_terms"]
    relevance_terms = profile["relevance_terms"]
    categories: dict[str, list[str]] = profile["categories"]
    min_relevance_score = int(profile.get("min_relevance_score", 3))
    reddit_title_terms = profile.get("reddit_title_terms", [])
    news_title_terms = profile.get("news_title_terms", [])
    exclude_title_patterns = profile.get("exclude_title_patterns", [])
    category_names = list(categories)

    rows: list[dict] = []
    for rec in raw.to_dict("records"):
        title = str(rec.get("title") or "")
        text = f"{rec.get('title') or ''} {rec.get('text') or ''}"
        if any(re.search(pattern, title, flags=re.IGNORECASE) for pattern in exclude_title_patterns):
            continue
        if str(rec.get("source_type")).endswith("_news") and news_title_terms:
            if term_hits(title, news_title_terms) == 0:
                continue
        if str(rec.get("source_type")) == "reddit_post" and reddit_title_terms:
            if term_hits(title, reddit_title_terms) == 0:
                continue
        company_hits = term_hits(text, company_terms)
        narrative_hits = term_hits(text, relevance_terms)
        category_scores = {name: term_hits(text, terms) for name, terms in categories.items()}
        category_hit_total = sum(1 for score in category_scores.values() if score > 0)

        relevance_score = company_hits * 3 + narrative_hits * 2 + min(category_hit_total, 5)
        if str(rec.get("source_type")) == "reddit_post" and company_hits:
            relevance_score += 1

        if relevance_score < min_relevance_score:
            continue

        pos_hits = term_hits(text, POSITIVE_TERMS)
        neg_hits = term_hits(text, NEGATIVE_TERMS)
        row = {
            "ticker": ticker,
            "source_type": rec.get("source_type"),
            "source": rec.get("source"),
            "title": rec.get("title"),
            "url": rec.get("url"),
            "published_at": rec.get("published_at"),
            "engagement": rec.get("engagement"),
            "relevance_score": relevance_score,
            "tone": classify_tone(pos_hits, neg_hits),
            "positive_hits": pos_hits,
            "negative_hits": neg_hits,
        }
        row.update(category_scores)
        rows.append(row)

    out = pd.DataFrame(rows)
    out_path = Path(args.output) if args.output else RESULTS_DIR / f"{TODAY_STR}_{ticker}_{args.days}d_narrative_debug.csv"
    if out.empty:
        out = pd.DataFrame(
            columns=[
                "ticker",
                "source_type",
                "source",
                "title",
                "url",
                "published_at",
                "engagement",
                "relevance_score",
                "tone",
                "positive_hits",
                "negative_hits",
                *category_names,
            ]
        )
    else:
        out = out.sort_values(["published_at", "relevance_score"], ascending=[False, False])
    out.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"RAW_TOTAL {len(raw)}")
    if not raw.empty:
        print(raw.groupby("source_type").size().to_string())
        print("RAW_DATE_RANGE")
        print(raw.groupby("source_type")["published_at"].agg(["min", "max"]).to_string())
    print(f"RELEVANT_TOTAL {len(out)}")
    if not out.empty:
        print(out.groupby("source_type").size().to_string())
        print("TONE")
        print(out["tone"].value_counts().to_string())
        print("CATEGORY_COUNTS")
        print((out[category_names] > 0).sum().sort_values(ascending=False).to_string())
        now = pd.Timestamp.now(tz="UTC")
        for window in (7, 30, 90):
            recent = out[out["published_at"] >= now - pd.Timedelta(days=window)]
            print(f"WINDOW_{window}D {len(recent)}")
            if not recent.empty:
                print(recent.groupby("source_type").size().to_string())
                print((recent[category_names] > 0).sum().sort_values(ascending=False).head(12).to_string())
        reddit = out[out["source_type"] == "reddit_post"].copy()
        if not reddit.empty:
            reddit["engagement"] = pd.to_numeric(reddit["engagement"], errors="coerce").fillna(0)
            print("TOP_REDDIT")
            for _, row in reddit.sort_values("engagement", ascending=False).head(10).iterrows():
                print(f"- {int(row['engagement'])} | {row['tone']} | {row['title']}")
        print("TOP_SOURCES")
        news = out[out["source_type"].astype(str).str.contains("news", na=False)]
        if not news.empty:
            print(news["source"].value_counts().head(15).to_string())
        print("RECENT_TITLES")
        for _, row in out.head(25).iterrows():
            engagement = row.get("engagement")
            if isinstance(engagement, float) and math.isnan(engagement):
                engagement = ""
            print(f"- {row['published_at']} | {row['source_type']} | {row['tone']} | {row['title']}")
    print(f"SAVED {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
