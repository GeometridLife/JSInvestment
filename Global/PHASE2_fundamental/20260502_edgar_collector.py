"""
PHASE2 Fundamental — EDGAR 재무제표 수집 (1,841 US 종목 × 10년)
================================================================

역할:
  PHASE0 마스터에서 Country='United States' AND Is_ADR=False인 1,841 종목을
  대상으로, edgartools를 통해 SEC EDGAR XBRL 공시에서 핵심 재무 데이터를 추출.

  - 손익: Revenue, OperatingIncome, NetIncome, InterestExpense, EPS, GrossProfit
  - 재무상태: TotalAssets/Liabilities, StockholdersEquity, LongTermDebt(±Current),
              CurrentAssets/Liabilities, CashAndEquivalents
  - 현금흐름: OperatingCashFlow, DividendsPaid, StockRepurchase, CapEx, ...
  - 시계열: OperatingIncome_3y, OperatingCashFlow_3y (필터용)

특징:
  - 100종목마다 중간 캐시 저장 (중단 시 재개 가능)
  - 증분 수집 (오늘 fetch된 종목 자동 스킵 — `--rebuild` 옵션으로 강제 재수집)
  - 첫 1종목 디버그 모드 (DataFrame 구조 출력)
  - SEC rate limit 0.1초 sleep, 429 시 30초 대기 + 3회 재시도
  - sector-aware 매핑 (Financials는 별도 후보)

실행:
    cd C:\\Users\\limit\\Desktop\\JS\\Global\\PHASE2_fundamental
    pip install edgartools openpyxl pandas
    # 환경변수 (선택):
    # PowerShell:  $env:EDGAR_IDENTITY = "Sang Il limited8090@gmail.com"
    # cmd.exe:     set EDGAR_IDENTITY=Sang Il limited8090@gmail.com
    python 20260502_edgar_collector.py

옵션:
    --limit N         : 첫 N 종목만 수집 (테스트용)
    --rebuild         : 캐시 무시하고 전체 재수집
    --start FROM      : 특정 ticker부터 시작 (디버그)

산출물:
    cache/edgar_cache.pkl                : {ticker: {edgar_*: value, ...}}
    logs/edgar_collection_log.csv        : 수집 이력
    logs/edgar_errors.csv                : 에러 종목

소요:
    첫 실행: ~4시간 (1,841 × 평균 8초)
    이후 재실행 (캐시 있음): ~30분 (첫 호출 응답 캐시 활용)
    증분: 분기 보고 발표 시점 30~50종목만 → ~10분
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

# edgartools
EDGAR_IDENTITY = os.environ.get('EDGAR_IDENTITY', 'JS Investment limited8090@gmail.com')
from edgar import set_identity, Company
import edgar
set_identity(EDGAR_IDENTITY)

# 우리 매핑 모듈
sys.path.insert(0, str(Path(__file__).parent))
from edgar_field_map import extract_company_fields


# ================================================================
# 설정
# ================================================================
SCRIPT_DIR = Path(__file__).parent
MASTER_PATH = SCRIPT_DIR.parent / 'PHASE0_classification' / '20260501_classification_master.xlsx'
CACHE_DIR = SCRIPT_DIR / 'cache'
LOGS_DIR = SCRIPT_DIR / 'logs'
CACHE_PATH = CACHE_DIR / 'edgar_cache.pkl'
LOG_PATH = LOGS_DIR / 'edgar_collection_log.csv'
ERROR_PATH = LOGS_DIR / 'edgar_errors.csv'

CACHE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

PERIODS = 10        # 10년치
SLEEP_SEC = 0.1     # SEC 10 req/sec 한도
SAVE_EVERY = 100    # 100종목마다 중간 저장
MAX_RETRY = 3
RETRY_WAIT_SEC = 30
TODAY_STR = datetime.now().strftime('%Y-%m-%d')


# ================================================================
# 1. PHASE0 마스터 로드 (US AND not ADR)
# ================================================================
def load_universe() -> pd.DataFrame:
    """1,841 US 종목 (Country='United States', Is_ADR=False) 로드."""
    df = pd.read_excel(MASTER_PATH, sheet_name='전체종목')
    print(f"  PHASE0 전체: {len(df)}종목")
    us_mask = df['Country'] == 'United States'
    not_adr = ~df['Is_ADR'].fillna(False).astype(bool)
    target = df[us_mask & not_adr].copy()
    print(f"  US AND not ADR: {len(target)}종목")
    target = target[['Symbol', 'Name', 'GICS_Sector', 'GICS_Industry_Group', 'Market_Cap']].copy()
    target.rename(columns={'Symbol': 'ticker', 'GICS_Sector': 'sector'}, inplace=True)
    return target


# ================================================================
# 2. 캐시 관리
# ================================================================
def load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, 'rb') as f:
            return pickle.load(f)
    return {}


def save_cache(cache: dict):
    tmp = CACHE_PATH.with_suffix('.tmp')
    with open(tmp, 'wb') as f:
        pickle.dump(cache, f)
    tmp.replace(CACHE_PATH)


def append_log(rows: list, path: Path, header: list):
    """CSV append (없으면 헤더 포함 새로 생성)."""
    df = pd.DataFrame(rows, columns=header)
    if path.exists():
        df.to_csv(path, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        df.to_csv(path, mode='w', header=True, index=False, encoding='utf-8-sig')


# ================================================================
# 3. 한 종목 수집 (재시도 포함)
# ================================================================
def fetch_one(ticker: str, sector: str, debug: bool = False) -> dict:
    """edgartools 호출 + 매핑 적용. 실패 시 재시도."""
    last_err = None
    for attempt in range(1, MAX_RETRY + 1):
        try:
            c = Company(ticker)
            income_df = c.income_statement(periods=PERIODS, period='annual', as_dataframe=True)
            balance_df = c.balance_sheet(periods=PERIODS, period='annual', as_dataframe=True)
            cf_df = c.cashflow_statement(periods=PERIODS, period='annual', as_dataframe=True)

            if debug:
                print(f"\n  [debug] {ticker} DataFrame 구조:")
                for n, dfx in [('income', income_df), ('balance', balance_df), ('cashflow', cf_df)]:
                    if dfx is None:
                        print(f"    {n}: None")
                    else:
                        print(f"    {n}: shape={dfx.shape}, cols sample={list(dfx.columns)[:8]}")

            row = extract_company_fields(ticker, sector, income_df, balance_df, cf_df)
            row['_fetched_at'] = TODAY_STR
            row['_attempt'] = attempt
            row['_status'] = 'ok'
            return row
        except Exception as e:
            last_err = e
            err_str = f"{type(e).__name__}: {str(e)[:120]}"
            # 429 / network 에러는 대기 후 재시도
            if attempt < MAX_RETRY and any(k in err_str.lower()
                                            for k in ['429', 'rate', 'timeout', 'connection', 'network']):
                time.sleep(RETRY_WAIT_SEC)
                continue
            return {
                'ticker': ticker,
                '_sector': sector,
                '_fetched_at': TODAY_STR,
                '_status': 'error',
                '_error': err_str,
                '_attempt': attempt,
            }
    return {
        'ticker': ticker,
        '_sector': sector,
        '_fetched_at': TODAY_STR,
        '_status': 'error',
        '_error': str(last_err)[:200],
        '_attempt': MAX_RETRY,
    }


# ================================================================
# 4. 메인
# ================================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None,
                        help='첫 N 종목만 수집 (테스트용)')
    parser.add_argument('--rebuild', action='store_true',
                        help='캐시 무시하고 전체 재수집')
    parser.add_argument('--start', type=str, default=None,
                        help='특정 ticker부터 시작')
    args = parser.parse_args()

    print("=" * 72)
    print("PHASE2 EDGAR 재무제표 수집")
    print(f"edgartools version  : {edgar.__version__ if hasattr(edgar, '__version__') else 'unknown'}")
    print(f"EDGAR_IDENTITY      : {EDGAR_IDENTITY}")
    print(f"Periods             : {PERIODS}년")
    print(f"Cache               : {CACHE_PATH}")
    print(f"Today               : {TODAY_STR}")
    print(f"Mode                : {'REBUILD (전체 재수집)' if args.rebuild else 'INCREMENTAL (오늘 수집된 종목 스킵)'}")
    print("=" * 72)

    # 1) 유니버스 로드
    print("\n[Step 1/3] 유니버스 로드...")
    universe = load_universe()
    if args.start:
        idx = universe.index[universe['ticker'] == args.start]
        if len(idx) > 0:
            universe = universe.loc[idx[0]:].reset_index(drop=True)
            print(f"  --start {args.start} 적용 → {len(universe)}종목 남음")
    if args.limit:
        universe = universe.head(args.limit)
        print(f"  --limit {args.limit} 적용")

    # 2) 캐시 로드
    print("\n[Step 2/3] 캐시 로드...")
    cache = {} if args.rebuild else load_cache()
    print(f"  기존 캐시: {len(cache)}종목")

    # 3) 수집
    print(f"\n[Step 3/3] EDGAR 수집 시작 ({len(universe)}종목)...")
    print("=" * 72)

    log_rows = []
    error_rows = []
    n_fetched = 0
    n_skipped = 0
    n_error = 0
    start_time = time.time()

    for i, row in universe.iterrows():
        ticker = row['ticker']
        sector = row['sector']
        i1 = i + 1

        # 증분 스킵: 오늘 이미 수집된 종목
        if not args.rebuild and ticker in cache:
            cached_at = cache[ticker].get('_fetched_at', '')
            if cached_at == TODAY_STR and cache[ticker].get('_status') == 'ok':
                n_skipped += 1
                if i1 % 100 == 0:
                    elapsed = time.time() - start_time
                    print(f"  [{i1:5d}/{len(universe)}] 진행 중... "
                          f"수집 {n_fetched}, 스킵 {n_skipped}, 에러 {n_error} "
                          f"(elapsed {elapsed:.0f}s)")
                continue

        ts = time.time()
        result = fetch_one(ticker, sector, debug=(n_fetched == 0))
        elapsed = time.time() - ts
        cache[ticker] = result

        if result.get('_status') == 'ok':
            n_fetched += 1
            rev = result.get('edgar_Revenue')
            rev_str = f"{rev/1e9:6.1f}B" if rev else "  N/A"
            sector_str = str(sector) if (sector is not None and pd.notna(sector)) else '?'
            print(f"  [{i1:5d}/{len(universe)}] {ticker:6s} ({sector_str[:18]:<18s}) "
                  f"Rev={rev_str} ({elapsed:4.1f}s)")
            log_rows.append({
                'ticker': ticker, 'sector': sector,
                'status': 'ok', 'elapsed_sec': round(elapsed, 1),
                'revenue': rev,
                'data_completeness': result.get('data_completeness', 0),
                'fetched_at': TODAY_STR,
            })
        else:
            n_error += 1
            err = result.get('_error', '?')[:100]
            print(f"  [{i1:5d}/{len(universe)}] {ticker:6s} ERROR: {err}")
            error_rows.append({
                'ticker': ticker, 'sector': sector,
                'error': err, 'attempt': result.get('_attempt', 1),
                'fetched_at': TODAY_STR,
            })
            log_rows.append({
                'ticker': ticker, 'sector': sector,
                'status': 'error', 'elapsed_sec': round(elapsed, 1),
                'revenue': None, 'data_completeness': 0,
                'fetched_at': TODAY_STR,
            })

        # 100종목마다 중간 저장
        if (n_fetched + n_skipped) % SAVE_EVERY == 0 and (n_fetched + n_skipped) > 0:
            save_cache(cache)
            if log_rows:
                append_log(log_rows, LOG_PATH,
                           ['ticker', 'sector', 'status', 'elapsed_sec',
                            'revenue', 'data_completeness', 'fetched_at'])
                log_rows = []
            if error_rows:
                append_log(error_rows, ERROR_PATH,
                           ['ticker', 'sector', 'error', 'attempt', 'fetched_at'])
                error_rows = []
            elapsed_total = time.time() - start_time
            avg = elapsed_total / (n_fetched + n_skipped) if (n_fetched + n_skipped) > 0 else 0
            remaining = avg * (len(universe) - i1)
            print(f"  >>> 중간 저장 ({i1}/{len(universe)}). "
                  f"평균 {avg:.1f}s/종목, ETA ~{remaining/60:.0f}분")

        time.sleep(SLEEP_SEC)

    # 최종 저장
    save_cache(cache)
    if log_rows:
        append_log(log_rows, LOG_PATH,
                   ['ticker', 'sector', 'status', 'elapsed_sec',
                    'revenue', 'data_completeness', 'fetched_at'])
    if error_rows:
        append_log(error_rows, ERROR_PATH,
                   ['ticker', 'sector', 'error', 'attempt', 'fetched_at'])

    total_elapsed = time.time() - start_time

    # 요약
    print("\n" + "=" * 72)
    print("수집 완료")
    print("=" * 72)
    print(f"  총 시도         : {len(universe)}종목")
    print(f"  수집 성공       : {n_fetched}")
    print(f"  스킵 (이미 수집): {n_skipped}")
    print(f"  에러            : {n_error}")
    print(f"  소요            : {total_elapsed/60:.1f}분")
    print(f"  캐시 위치       : {CACHE_PATH}")
    print(f"  로그            : {LOG_PATH}")
    if n_error > 0:
        print(f"  에러 상세       : {ERROR_PATH}")

    # 필드 커버리지 요약 (마지막 수집된 캐시 기준)
    ok_rows = [v for v in cache.values() if v.get('_status') == 'ok']
    if ok_rows:
        print("\n  핵심 필드 커버리지:")
        key_fields = ['edgar_Revenue', 'edgar_OperatingIncome', 'edgar_NetIncome',
                      'edgar_InterestExpense', 'edgar_StockholdersEquity',
                      'edgar_LongTermDebt', 'edgar_DividendsPaid',
                      'edgar_StockRepurchase', 'edgar_OperatingCashFlow']
        for f in key_fields:
            cnt = sum(1 for r in ok_rows if r.get(f) is not None)
            pct = cnt / len(ok_rows) * 100
            marker = '✓' if pct >= 95 else ('△' if pct >= 80 else '✗')
            print(f"    {marker} {f:35s} {pct:5.1f}% ({cnt}/{len(ok_rows)})")


if __name__ == '__main__':
    main()
