"""
PHASE2 Fundamental — yfinance 데이터 수집 (1,841 US 종목)
================================================================

역할:
  EDGAR가 메인 소스인 영역(Trailing 재무) 외의 데이터를 yfinance에서 수집.

  [1차 데이터]
    Ticker.info에서 Forward 컨센서스 + 시총·현재가
    - Forward: forwardPE, forwardEps, pegRatio, earningsGrowth, revenueGrowth
    - Trailing fallback: trailingPE, trailingEps, priceToBook, priceToSales
    - 주주환원 yield: dividendYield, payoutRatio, fiveYearAvgDividendYield
    - 재무건전성 보조: debtToEquity, currentRatio, totalDebt
    - Capital: marketCap, enterpriseValue, sharesOutstanding, currentPrice
    - Meta: sector, industry, currency, exchange

  [검증용 데이터]
    Ticker.cashflow에서 자사주매입·배당지급 (EDGAR vs yfinance cross-check 용)
    - Operating Cash Flow, Cash Dividends Paid, Repurchase Of Capital Stock

특징:
  - 50종목마다 중간 캐시 저장
  - 증분 수집 (오늘 fetch된 종목 스킵 — `--rebuild`로 강제)
  - rate limit 0.5초 sleep, 429 시 30초 대기 + 3회 재시도
  - 캐시 분리: yf_info_cache.pkl (메인) + yf_cashflow_cache.pkl (검증)

실행:
    cd C:\\Users\\limit\\Desktop\\JS\\Global\\PHASE2_fundamental
    python 20260502_yf_collector.py

옵션:
    --limit N       : 첫 N 종목만 수집
    --rebuild       : 캐시 무시 전체 재수집
    --start TICKER  : 특정 ticker부터 시작
    --info-only     : Ticker.info만 (cashflow 스킵)
    --cashflow-only : cashflow만

산출물:
    cache/yf_info_cache.pkl       : Ticker.info 추출
    cache/yf_cashflow_cache.pkl   : Ticker.cashflow 검증용 (4년치)
    logs/yf_collection_log.csv

소요:
    Info     : 1,841 × 0.5초 ≈ 15분
    Cashflow : 1,841 × 0.6초 ≈ 18분
    합계     : ~30~35분
"""
from __future__ import annotations
import os
import sys
import time
import pickle
import argparse
import warnings
from pathlib import Path
from datetime import datetime
import pandas as pd

warnings.filterwarnings('ignore')

import yfinance as yf

# ================================================================
# 설정
# ================================================================
SCRIPT_DIR = Path(__file__).parent
MASTER_PATH = SCRIPT_DIR.parent / 'PHASE0_classification' / '20260501_classification_master.xlsx'
CACHE_DIR = SCRIPT_DIR / 'cache'
LOGS_DIR = SCRIPT_DIR / 'logs'
INFO_CACHE_PATH = CACHE_DIR / 'yf_info_cache.pkl'
CF_CACHE_PATH = CACHE_DIR / 'yf_cashflow_cache.pkl'
LOG_PATH = LOGS_DIR / 'yf_collection_log.csv'
ERROR_PATH = LOGS_DIR / 'yf_errors.csv'

CACHE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

SLEEP_SEC = 0.5      # rate limit safety
SAVE_EVERY = 50
MAX_RETRY = 3
RETRY_WAIT_SEC = 30
TODAY_STR = datetime.now().strftime('%Y-%m-%d')


# ================================================================
# 1. 추출할 Ticker.info 필드 (PHASE2 스코어링·필터에 필요한 것)
# ================================================================
INFO_FIELDS = [
    # Forward Valuation (메인)
    'forwardPE', 'forwardEps', 'pegRatio', 'trailingPegRatio',
    # Trailing fallback
    'trailingPE', 'trailingEps', 'priceToBook', 'priceToSalesTrailing12Months',
    # Forward Growth
    'earningsGrowth', 'revenueGrowth', 'earningsQuarterlyGrowth', 'revenueQuarterlyGrowth',
    # Profitability (참고)
    'profitMargins', 'operatingMargins', 'returnOnEquity', 'returnOnAssets', 'grossMargins',
    # Shareholder return (yield)
    'dividendYield', 'dividendRate', 'payoutRatio',
    'fiveYearAvgDividendYield', 'lastDividendValue', 'lastDividendDate',
    # Financial health (보조)
    'debtToEquity', 'currentRatio', 'quickRatio',
    'totalCash', 'totalDebt', 'totalRevenue', 'ebitda', 'grossProfits',
    # Capital structure
    'sharesOutstanding', 'floatShares', 'sharesShort',
    'marketCap', 'enterpriseValue', 'beta', 'currentPrice',
    # Meta
    'sector', 'industry', 'country', 'currency', 'exchange',
    'longBusinessSummary', 'website',
]

# Cashflow에서 검증용으로 추출할 항목 (yfinance 행 라벨 후보)
CF_FIELDS = {
    'OperatingCashFlow':    ['Operating Cash Flow', 'Cash Flow From Continuing Operating Activities'],
    'FreeCashFlow':         ['Free Cash Flow'],
    'CashDividendsPaid':    ['Cash Dividends Paid', 'Common Stock Dividend Paid'],
    'RepurchaseOfStock':    ['Repurchase Of Capital Stock', 'Common Stock Payments'],
    'IssuanceOfStock':      ['Issuance Of Capital Stock', 'Common Stock Issuance'],
    'CapitalExpenditure':   ['Capital Expenditure', 'Capital Expenditures'],
}


# ================================================================
# 2. PHASE0 마스터 로드 (US AND not ADR — edgar_collector와 동일 유니버스)
# ================================================================
def load_universe() -> pd.DataFrame:
    df = pd.read_excel(MASTER_PATH, sheet_name='전체종목')
    print(f"  PHASE0 전체: {len(df)}종목")
    us_mask = df['Country'] == 'United States'
    not_adr = ~df['Is_ADR'].fillna(False).astype(bool)
    target = df[us_mask & not_adr].copy()
    print(f"  US AND not ADR: {len(target)}종목")
    target = target[['Symbol', 'Name', 'GICS_Sector', 'Market_Cap']].copy()
    target.rename(columns={'Symbol': 'ticker', 'GICS_Sector': 'sector'}, inplace=True)
    return target


# ================================================================
# 3. 캐시 관리
# ================================================================
def load_pickle(path: Path) -> dict:
    if path.exists():
        with open(path, 'rb') as f:
            return pickle.load(f)
    return {}


def save_pickle(obj: dict, path: Path):
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'wb') as f:
        pickle.dump(obj, f)
    tmp.replace(path)


def append_log(rows: list, path: Path, header: list):
    df = pd.DataFrame(rows, columns=header)
    if path.exists():
        df.to_csv(path, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        df.to_csv(path, mode='w', header=True, index=False, encoding='utf-8-sig')


# ================================================================
# 4. yfinance 추출 헬퍼
# ================================================================
def extract_info(ticker: str) -> dict:
    """yfinance Ticker.info에서 필요 필드만 추출."""
    out = {'ticker': ticker, '_fetched_at': TODAY_STR}
    info = yf.Ticker(ticker).info or {}
    for f in INFO_FIELDS:
        out[f'yf_{f}'] = info.get(f)
    out['_status'] = 'ok'
    return out


def _extract_cf_row(df: pd.DataFrame, candidates: list, n_periods: int = 4) -> dict:
    """yfinance cashflow DataFrame에서 라벨 매칭 후 최근 n개 시계열 추출.
    yfinance: index=항목명, columns=회계연도(Timestamp), 좌측이 최신."""
    if df is None or df.empty:
        return {'matched_label': None, 'years': [], 'values': []}
    for label in candidates:
        if label in df.index:
            row = df.loc[label]
            if isinstance(row, pd.Series):
                row = row.dropna()
                years = [str(c.date()) if hasattr(c, 'date') else str(c)
                         for c in row.index[:n_periods]]
                values = []
                for v in row.values[:n_periods]:
                    try:
                        values.append(float(v))
                    except (TypeError, ValueError):
                        values.append(None)
                return {'matched_label': label, 'years': years, 'values': values}
    return {'matched_label': None, 'years': [], 'values': []}


def extract_cashflow(ticker: str) -> dict:
    """Ticker.cashflow에서 자사주매입·배당지급·OCF 검증용 시계열 추출."""
    out = {'ticker': ticker, '_fetched_at': TODAY_STR}
    t = yf.Ticker(ticker)
    cf_df = t.cashflow
    out['_periods_available'] = len(cf_df.columns) if cf_df is not None else 0
    for fname, candidates in CF_FIELDS.items():
        out[f'yf_{fname}'] = _extract_cf_row(cf_df, candidates, n_periods=4)
    out['_status'] = 'ok'
    return out


# ================================================================
# 5. 재시도 wrapper
# ================================================================
def fetch_one(ticker: str, kind: str) -> dict:
    """kind='info' or 'cashflow'. 재시도 포함."""
    func = extract_info if kind == 'info' else extract_cashflow
    last_err = None
    for attempt in range(1, MAX_RETRY + 1):
        try:
            row = func(ticker)
            row['_attempt'] = attempt
            return row
        except Exception as e:
            last_err = e
            err_str = f"{type(e).__name__}: {str(e)[:120]}"
            if attempt < MAX_RETRY and any(k in err_str.lower()
                                            for k in ['429', 'rate', 'timeout', 'connection', 'network']):
                time.sleep(RETRY_WAIT_SEC)
                continue
            return {
                'ticker': ticker, '_fetched_at': TODAY_STR,
                '_status': 'error', '_error': err_str, '_attempt': attempt,
            }
    return {
        'ticker': ticker, '_fetched_at': TODAY_STR,
        '_status': 'error', '_error': str(last_err)[:200], '_attempt': MAX_RETRY,
    }


# ================================================================
# 6. 한 단계 (info or cashflow) 수집 루프
# ================================================================
def run_phase(universe: pd.DataFrame, kind: str, cache: dict, args) -> tuple:
    """반환: (n_fetched, n_skipped, n_error, log_rows, error_rows)"""
    print(f"\n  [{kind.upper()}] {len(universe)}종목 수집 시작...")

    n_fetched = n_skipped = n_error = 0
    log_rows, error_rows = [], []
    start_time = time.time()
    cache_path = INFO_CACHE_PATH if kind == 'info' else CF_CACHE_PATH

    for i, row in universe.iterrows():
        ticker = row['ticker']
        sector = row.get('sector')
        i1 = i + 1

        # 증분 스킵
        if not args.rebuild and ticker in cache:
            cached_at = cache[ticker].get('_fetched_at', '')
            if cached_at == TODAY_STR and cache[ticker].get('_status') == 'ok':
                n_skipped += 1
                if i1 % 200 == 0:
                    elapsed = time.time() - start_time
                    print(f"    [{i1:5d}/{len(universe)}] 진행... "
                          f"수집 {n_fetched}, 스킵 {n_skipped}, 에러 {n_error} "
                          f"({elapsed:.0f}s)")
                continue

        ts = time.time()
        result = fetch_one(ticker, kind)
        result['_sector'] = sector
        elapsed = time.time() - ts
        cache[ticker] = result

        if result.get('_status') == 'ok':
            n_fetched += 1
            # 진행 출력 (50종목마다)
            if i1 % 50 == 0 or i1 <= 3:
                if kind == 'info':
                    fpe = result.get('yf_forwardPE')
                    mc = result.get('yf_marketCap')
                    mc_str = f"{mc/1e9:5.0f}B" if mc else "  N/A"
                    print(f"    [{i1:5d}/{len(universe)}] {ticker:6s} "
                          f"fwdPE={fpe!s:>8s} mc={mc_str} ({elapsed:.1f}s)")
                else:
                    div = result.get('yf_CashDividendsPaid', {}).get('values', [None])
                    div_v = div[0] if div else None
                    div_str = f"{abs(div_v)/1e9:.1f}B" if div_v else "N/A"
                    print(f"    [{i1:5d}/{len(universe)}] {ticker:6s} "
                          f"div={div_str:>5s} ({elapsed:.1f}s)")
            log_rows.append({
                'ticker': ticker, 'sector': sector, 'kind': kind,
                'status': 'ok', 'elapsed_sec': round(elapsed, 1),
                'fetched_at': TODAY_STR,
            })
        else:
            n_error += 1
            err = result.get('_error', '?')[:100]
            print(f"    [{i1:5d}/{len(universe)}] {ticker:6s} ERROR: {err}")
            error_rows.append({
                'ticker': ticker, 'sector': sector, 'kind': kind,
                'error': err, 'attempt': result.get('_attempt', 1),
                'fetched_at': TODAY_STR,
            })
            log_rows.append({
                'ticker': ticker, 'sector': sector, 'kind': kind,
                'status': 'error', 'elapsed_sec': round(elapsed, 1),
                'fetched_at': TODAY_STR,
            })

        # 중간 저장
        if (n_fetched + n_skipped) > 0 and (n_fetched + n_skipped) % SAVE_EVERY == 0:
            save_pickle(cache, cache_path)
            if log_rows:
                append_log(log_rows, LOG_PATH,
                           ['ticker', 'sector', 'kind', 'status', 'elapsed_sec', 'fetched_at'])
                log_rows = []
            if error_rows:
                append_log(error_rows, ERROR_PATH,
                           ['ticker', 'sector', 'kind', 'error', 'attempt', 'fetched_at'])
                error_rows = []
            elapsed_total = time.time() - start_time
            avg = elapsed_total / max(n_fetched, 1)
            remaining = avg * (len(universe) - i1)
            print(f"    >>> 중간 저장 ({i1}/{len(universe)}). "
                  f"평균 {avg:.1f}s/종목, ETA ~{remaining/60:.0f}분")

        time.sleep(SLEEP_SEC)

    # 최종 저장
    save_pickle(cache, cache_path)
    if log_rows:
        append_log(log_rows, LOG_PATH,
                   ['ticker', 'sector', 'kind', 'status', 'elapsed_sec', 'fetched_at'])
    if error_rows:
        append_log(error_rows, ERROR_PATH,
                   ['ticker', 'sector', 'kind', 'error', 'attempt', 'fetched_at'])

    return n_fetched, n_skipped, n_error


# ================================================================
# 7. 메인
# ================================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--rebuild', action='store_true')
    parser.add_argument('--start', type=str, default=None)
    parser.add_argument('--info-only', action='store_true', dest='info_only')
    parser.add_argument('--cashflow-only', action='store_true', dest='cf_only')
    args = parser.parse_args()

    print("=" * 72)
    print("PHASE2 yfinance 데이터 수집")
    print(f"yfinance version : {yf.__version__}")
    print(f"Today            : {TODAY_STR}")
    print(f"Mode             : {'REBUILD' if args.rebuild else 'INCREMENTAL'}")
    if args.info_only:
        print("Phases           : info만 (cashflow 스킵)")
    elif args.cf_only:
        print("Phases           : cashflow만 (info 스킵)")
    else:
        print("Phases           : info + cashflow")
    print("=" * 72)

    # 유니버스
    print("\n[1/4] 유니버스 로드...")
    universe = load_universe()
    if args.start:
        idx = universe.index[universe['ticker'] == args.start]
        if len(idx) > 0:
            universe = universe.loc[idx[0]:].reset_index(drop=True)
            print(f"  --start {args.start} 적용 → {len(universe)}종목 남음")
    if args.limit:
        universe = universe.head(args.limit)
        print(f"  --limit {args.limit} 적용")

    # Info 단계
    info_stats = (0, 0, 0)
    if not args.cf_only:
        print("\n[2/4] Ticker.info 수집...")
        info_cache = {} if args.rebuild else load_pickle(INFO_CACHE_PATH)
        print(f"  기존 info 캐시: {len(info_cache)}종목")
        info_stats = run_phase(universe, 'info', info_cache, args)

    # Cashflow 단계
    cf_stats = (0, 0, 0)
    if not args.info_only:
        print("\n[3/4] Ticker.cashflow 수집 (검증용)...")
        cf_cache = {} if args.rebuild else load_pickle(CF_CACHE_PATH)
        print(f"  기존 cashflow 캐시: {len(cf_cache)}종목")
        cf_stats = run_phase(universe, 'cashflow', cf_cache, args)

    # 요약
    print("\n[4/4] 요약")
    print("=" * 72)
    print(f"  Info     : 수집 {info_stats[0]}, 스킵 {info_stats[1]}, 에러 {info_stats[2]}")
    print(f"  Cashflow : 수집 {cf_stats[0]}, 스킵 {cf_stats[1]}, 에러 {cf_stats[2]}")
    print(f"  Info 캐시     : {INFO_CACHE_PATH}")
    print(f"  Cashflow 캐시 : {CF_CACHE_PATH}")
    print(f"  로그          : {LOG_PATH}")

    # 필드 커버리지
    info_cache = load_pickle(INFO_CACHE_PATH)
    ok_rows = [v for v in info_cache.values() if v.get('_status') == 'ok']
    if ok_rows:
        print(f"\n  Ticker.info 필드 커버리지 ({len(ok_rows)}종목 기준):")
        key_fields = ['forwardPE', 'forwardEps', 'pegRatio',
                      'trailingPE', 'earningsGrowth', 'revenueGrowth',
                      'dividendYield', 'payoutRatio',
                      'debtToEquity', 'currentRatio',
                      'marketCap', 'currentPrice', 'sector']
        for f in key_fields:
            cnt = sum(1 for r in ok_rows if r.get(f'yf_{f}') is not None)
            pct = cnt / len(ok_rows) * 100
            marker = '✓' if pct >= 90 else ('△' if pct >= 70 else '✗')
            print(f"    {marker} {f:30s} {pct:5.1f}% ({cnt}/{len(ok_rows)})")


if __name__ == '__main__':
    main()
