#!/usr/bin/env python3
"""
Incremental cache updater for PHASE3_1 narrative attention.

기존 raw cache를 master cache로 병합하고, master의 최신 published_at을 기준으로
필요한 날짜만 live_attention_collector.py로 추가 수집한 뒤 rolling window 파일을 만든다.
"""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE3_1_DIR = SCRIPT_DIR.parent
CACHE_RAW_DIR = PHASE3_1_DIR / "cache" / "raw"
LOG_DIR = PHASE3_1_DIR / "logs"
TODAY_STR = dt.datetime.now().strftime("%Y%m%d")

MASTER_RAW = CACHE_RAW_DIR / "master_attention_raw.csv"
ROLLING_RAW = CACHE_RAW_DIR / f"{TODAY_STR}_rolling37_attention_raw.csv"

RAW_COLUMNS = [
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


def read_raw(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=RAW_COLUMNS)
    return pd.read_csv(path, encoding="utf-8-sig", on_bad_lines="skip")


def normalize_raw(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in RAW_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    out = out[RAW_COLUMNS].copy()
    published = out["published_at"].fillna("").astype(str)
    out["published_at_ts"] = pd.to_datetime(published, utc=True, errors="coerce")
    missing_ts = out["published_at_ts"].isna()
    if missing_ts.any():
        out.loc[missing_ts, "published_at_ts"] = pd.to_datetime(
            published[missing_ts],
            format="%Y%m%dT%H%M%SZ",
            utc=True,
            errors="coerce",
        )
    out["url_key"] = out["url"].fillna("").astype(str).str.strip()
    fallback = (
        out["source_type"].fillna("").astype(str)
        + "|"
        + out["ticker"].fillna("").astype(str)
        + "|"
        + out["title"].fillna("").astype(str)
        + "|"
        + out["published_at"].fillna("").astype(str)
    )
    out["dedup_key"] = out["url_key"].where(out["url_key"].ne(""), fallback)
    return out


def dedupe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=RAW_COLUMNS)
    out = normalize_raw(df)
    out = out.sort_values(["published_at_ts", "collected_at"], ascending=[True, True])
    out = out.drop_duplicates(subset=["dedup_key"], keep="last")
    out = out.sort_values("published_at_ts", ascending=True)
    return out[RAW_COLUMNS].reset_index(drop=True)


def discover_raw_files() -> list[Path]:
    files = []
    for path in CACHE_RAW_DIR.glob("*_attention_raw.csv"):
        if path.name.startswith("master_") or "rolling37" in path.name or "_incremental_" in path.name:
            continue
        files.append(path)
    return sorted(files)


def rebuild_master_from_cache() -> pd.DataFrame:
    frames = [read_raw(path) for path in discover_raw_files()]
    if MASTER_RAW.exists():
        frames.append(read_raw(MASTER_RAW))
    if not frames:
        return pd.DataFrame(columns=RAW_COLUMNS)
    master = dedupe(pd.concat(frames, ignore_index=True))
    MASTER_RAW.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(MASTER_RAW, index=False, encoding="utf-8-sig")
    return master


def latest_published_date(df: pd.DataFrame) -> dt.date | None:
    if df.empty or "published_at" not in df.columns:
        return None
    ts = normalize_raw(df)["published_at_ts"].dropna()
    if ts.empty:
        return None
    return ts.max().date()


def calculate_collect_days(master: pd.DataFrame, lookback_days: int, overlap_days: int) -> int:
    latest_date = latest_published_date(master)
    if latest_date is None:
        return lookback_days
    today = dt.datetime.now(dt.timezone.utc).date()
    missing_days = max(0, (today - latest_date).days)
    return max(1, missing_days + overlap_days)


def run_collector(args: argparse.Namespace, collect_days: int, output_prefix: str) -> Path:
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "live_attention_collector.py"),
        "--sources",
        args.sources,
        "--days",
        str(collect_days),
        "--chunk-days",
        str(args.chunk_days),
        "--finnhub-window-days",
        str(min(args.finnhub_window_days, max(1, collect_days))),
        "--limit",
        str(args.limit),
        "--tickers",
        args.tickers,
        "--theme-limit",
        str(args.theme_limit),
        "--max-records",
        str(args.max_records),
        "--max-records-per-ticker",
        str(args.max_records_per_ticker),
        "--max-terms",
        str(args.max_terms),
        "--sleep",
        str(args.sleep),
        "--retries",
        str(args.retries),
        "--output-prefix",
        output_prefix,
    ]
    if args.finnhub_token:
        cmd.extend(["--finnhub-token", args.finnhub_token])
    subprocess.run(cmd, cwd=PHASE3_1_DIR.parents[3], check=True)
    return CACHE_RAW_DIR / f"{output_prefix}_attention_raw.csv"


def export_rolling_window(master: pd.DataFrame, lookback_days: int, output_path: Path) -> pd.DataFrame:
    out = normalize_raw(master)
    end_ts = out["published_at_ts"].max()
    if pd.isna(end_ts):
        rolling = out
    else:
        start_ts = end_ts - pd.Timedelta(days=lookback_days - 1)
        rolling = out[out["published_at_ts"] >= start_ts].copy()
    rolling = rolling[RAW_COLUMNS].reset_index(drop=True)
    rolling.to_csv(output_path, index=False, encoding="utf-8-sig")
    return rolling


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", default="finnhub_company", help="Comma-separated: finnhub_company,finnhub_market,gdelt,reddit")
    parser.add_argument("--lookback-days", type=int, default=37)
    parser.add_argument("--overlap-days", type=int, default=2)
    parser.add_argument("--chunk-days", type=int, default=3)
    parser.add_argument("--finnhub-window-days", type=int, default=7)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--tickers", default="")
    parser.add_argument("--theme-limit", type=int, default=0)
    parser.add_argument("--max-records", type=int, default=100)
    parser.add_argument("--max-records-per-ticker", type=int, default=300)
    parser.add_argument("--max-terms", type=int, default=5)
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--finnhub-token", default="")
    parser.add_argument("--skip-collect", action="store_true", help="Only rebuild master and rolling window from existing cache.")
    parser.add_argument("--rebuild-master", action="store_true", help="Merge existing raw cache files before deciding incremental window.")
    parser.add_argument("--output-prefix", default=f"{TODAY_STR}_incremental")
    args = parser.parse_args()

    CACHE_RAW_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if args.rebuild_master or not MASTER_RAW.exists():
        master = rebuild_master_from_cache()
    else:
        master = dedupe(read_raw(MASTER_RAW))
        master.to_csv(MASTER_RAW, index=False, encoding="utf-8-sig")

    latest_before = latest_published_date(master)
    collect_days = calculate_collect_days(master, args.lookback_days, args.overlap_days)
    incremental_path = None

    if not args.skip_collect:
        incremental_path = run_collector(args, collect_days, args.output_prefix)
        incremental = read_raw(incremental_path)
        master = dedupe(pd.concat([master, incremental], ignore_index=True))
        master.to_csv(MASTER_RAW, index=False, encoding="utf-8-sig")

    rolling = export_rolling_window(master, args.lookback_days, ROLLING_RAW)
    latest_after = latest_published_date(master)

    print(f"master_raw {MASTER_RAW}")
    print(f"rolling_raw {ROLLING_RAW}")
    if incremental_path:
        print(f"incremental_raw {incremental_path}")
    print(f"latest_before {latest_before}")
    print(f"latest_after {latest_after}")
    print(f"collect_days {collect_days}")
    print(f"master_rows {len(master)}")
    print(f"rolling_rows {len(rolling)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
