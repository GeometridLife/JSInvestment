"""
PHASE1 Momentum - Step 1: 데이터 수집기 (증분 업데이트 지원)
Date: 2026-04-27
Description:
    - 최초 실행: FDR로 10년치 일간 OHLCV 전체 수집
    - 이후 실행: 기존 캐시 로드 → 마지막 날짜 이후 데이터만 추가 수집
    - 주간 데이터 리샘플링
    - 캐시는 날짜 없이 고정 파일명 (daily_cache.pkl) → 매일 덮어쓰기
"""

import os
import sys
import time
import glob
import datetime
import pickle
import pandas as pd
import FinanceDataReader as fdr

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)  # PHASE1_momentum/
PHASE0_DIR = os.path.join(os.path.dirname(BASE_DIR), 'PHASE0_classification')
TODAY_STR = datetime.date.today().strftime('%Y%m%d')
TODAY_DATE = datetime.date.today()

# 입력: 마스터 테이블 (가장 최근 파일 자동 탐색)
MASTER_CANDIDATES = sorted(glob.glob(os.path.join(PHASE0_DIR, '*_classification_master_verified.xlsx')))
if not MASTER_CANDIDATES:
    print("[ERROR] PHASE0 마스터 파일을 찾을 수 없습니다.")
    sys.exit(1)
MASTER_EXCEL = MASTER_CANDIDATES[-1]

# 캐시: cache/ 폴더
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
DAILY_CACHE = os.path.join(CACHE_DIR, 'daily_cache.pkl')
WEEKLY_CACHE = os.path.join(CACHE_DIR, 'weekly_cache.pkl')

# 로그: logs/ 폴더
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
COLLECTION_LOG = os.path.join(LOG_DIR, f'{TODAY_STR}_collection_log.csv')
UPDATE_HISTORY = os.path.join(LOG_DIR, 'update_history.csv')

# 수집 설정
YEARS_BACK = 10
FULL_START_DATE = (TODAY_DATE - datetime.timedelta(days=365 * YEARS_BACK + 30)).strftime('%Y-%m-%d')
END_DATE = TODAY_DATE.strftime('%Y-%m-%d')


# ============================================================
# Step 1: 종목 리스트 로드
# ============================================================
def load_ticker_list():
    df = pd.read_excel(MASTER_EXCEL, sheet_name='전체종목')
    tickers = df['ticker'].astype(str).str.strip().str.zfill(6).tolist()
    names = df['name'].tolist()
    ticker_name_map = dict(zip(tickers, names))
    print(f"[Step 1] 마스터 테이블: {len(tickers)}종목 ({os.path.basename(MASTER_EXCEL)})")
    return tickers, ticker_name_map


# ============================================================
# Step 2: 기존 캐시 로드 + 증분 업데이트
# ============================================================
def load_existing_cache():
    """기존 캐시가 있으면 로드, 없으면 빈 딕셔너리"""
    if os.path.exists(DAILY_CACHE):
        with open(DAILY_CACHE, 'rb') as f:
            cache = pickle.load(f)
        # 캐시 내 데이터의 마지막 날짜 확인
        last_dates = {}
        for tk, df in cache.items():
            if len(df) > 0:
                last_dates[tk] = df.index.max()
        if last_dates:
            overall_last = max(last_dates.values())
            print(f"[Step 2] 기존 캐시 로드: {len(cache)}종목, 최근 데이터: {overall_last.strftime('%Y-%m-%d')}")
        else:
            print(f"[Step 2] 기존 캐시 로드: {len(cache)}종목 (빈 데이터)")
        return cache, last_dates
    else:
        print("[Step 2] 기존 캐시 없음 → 전체 수집 (최초 실행)")
        return {}, {}


def collect_incremental(tickers, ticker_name_map, existing_cache, last_dates):
    """
    증분 업데이트: 기존 캐시의 마지막 날짜 이후 데이터만 수집
    신규 종목은 전체 기간 수집
    """
    updated_cache = dict(existing_cache)  # 기존 데이터 복사
    log_records = []
    total = len(tickers)

    # 업데이트가 필요한 종목 분류
    new_tickers = []      # 캐시에 없는 종목 → 전체 수집
    update_tickers = []   # 캐시에 있지만 업데이트 필요 → 증분 수집
    skip_tickers = []     # 이미 최신 → 스킵

    for tk in tickers:
        if tk not in existing_cache:
            new_tickers.append(tk)
        elif tk in last_dates:
            last = last_dates[tk]
            # 마지막 데이터가 오늘이면 스킵 (당일 종가 이미 수집됨)
            if last.date() >= TODAY_DATE:
                skip_tickers.append(tk)
            else:
                update_tickers.append(tk)
        else:
            new_tickers.append(tk)

    print(f"\n  신규 수집: {len(new_tickers)}종목")
    print(f"  증분 업데이트: {len(update_tickers)}종목")
    print(f"  스킵 (최신): {len(skip_tickers)}종목")

    # --- 신규 종목: 전체 기간 수집 ---
    if new_tickers:
        print(f"\n[수집] 신규 {len(new_tickers)}종목 전체 수집 ({FULL_START_DATE} ~ {END_DATE})")
        for i, tk in enumerate(new_tickers):
            name = ticker_name_map.get(tk, '?')
            try:
                df = fdr.DataReader(tk, FULL_START_DATE, END_DATE)
                if df is not None and len(df) > 0:
                    df.index = pd.to_datetime(df.index)
                    df = df.sort_index()
                    updated_cache[tk] = df
                    log_records.append({'ticker': tk, 'name': name, 'status': 'new_full', 'rows': len(df)})
                else:
                    log_records.append({'ticker': tk, 'name': name, 'status': 'empty', 'rows': 0})
            except Exception as e:
                log_records.append({'ticker': tk, 'name': name, 'status': f'error: {str(e)[:50]}', 'rows': 0})

            if (i + 1) % 50 == 0:
                print(f"    [{i+1}/{len(new_tickers)}] 신규 수집 중...")
                time.sleep(0.3)

    # --- 기존 종목: 증분 수집 ---
    if update_tickers:
        print(f"\n[수집] 기존 {len(update_tickers)}종목 증분 업데이트")
        for i, tk in enumerate(update_tickers):
            name = ticker_name_map.get(tk, '?')
            last = last_dates[tk]
            # 마지막 날짜 다음 날부터
            start = (last + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

            try:
                df_new = fdr.DataReader(tk, start, END_DATE)
                if df_new is not None and len(df_new) > 0:
                    df_new.index = pd.to_datetime(df_new.index)
                    df_new = df_new.sort_index()

                    # 기존 데이터와 합치기 (중복 제거)
                    df_existing = existing_cache[tk]
                    df_merged = pd.concat([df_existing, df_new])
                    df_merged = df_merged[~df_merged.index.duplicated(keep='last')]
                    df_merged = df_merged.sort_index()
                    updated_cache[tk] = df_merged

                    log_records.append({'ticker': tk, 'name': name, 'status': 'incremental', 'rows': len(df_new)})
                else:
                    log_records.append({'ticker': tk, 'name': name, 'status': 'no_new_data', 'rows': 0})
            except Exception as e:
                log_records.append({'ticker': tk, 'name': name, 'status': f'error: {str(e)[:50]}', 'rows': 0})

            if (i + 1) % 100 == 0:
                print(f"    [{i+1}/{len(update_tickers)}] 증분 업데이트 중...")
                time.sleep(0.3)

    # 스킵 종목 로그
    for tk in skip_tickers:
        name = ticker_name_map.get(tk, '?')
        log_records.append({'ticker': tk, 'name': name, 'status': 'skipped_uptodate', 'rows': 0})

    return updated_cache, log_records


# ============================================================
# Step 3: 주간 데이터 리샘플링
# ============================================================
def resample_to_weekly(daily_data):
    weekly_data = {}
    for ticker, df in daily_data.items():
        try:
            agg_dict = {
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum',
            }
            weekly = df.resample('W-FRI').agg(agg_dict).dropna()
            if 'Amount' in df.columns:
                weekly['Amount'] = df['Amount'].resample('W-FRI').sum()
            weekly_data[ticker] = weekly
        except Exception:
            pass
    print(f"[Step 3] 주간 리샘플링: {len(weekly_data)}종목")
    return weekly_data


# ============================================================
# Step 4: 저장 + 업데이트 이력
# ============================================================
def save_caches(daily_data, weekly_data, log_records):
    # Daily
    with open(DAILY_CACHE, 'wb') as f:
        pickle.dump(daily_data, f, protocol=pickle.HIGHEST_PROTOCOL)
    size_mb = os.path.getsize(DAILY_CACHE) / (1024 * 1024)
    print(f"[Step 4] Daily 캐시 저장: {size_mb:.1f}MB")

    # Weekly
    with open(WEEKLY_CACHE, 'wb') as f:
        pickle.dump(weekly_data, f, protocol=pickle.HIGHEST_PROTOCOL)
    size_mb = os.path.getsize(WEEKLY_CACHE) / (1024 * 1024)
    print(f"[Step 4] Weekly 캐시 저장: {size_mb:.1f}MB")

    # Collection log (당일)
    df_log = pd.DataFrame(log_records)
    df_log.to_csv(COLLECTION_LOG, index=False, encoding='utf-8-sig')

    # 업데이트 이력 (누적)
    history_row = {
        'date': TODAY_STR,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_tickers': len(daily_data),
        'new': sum(1 for r in log_records if r['status'] == 'new_full'),
        'incremental': sum(1 for r in log_records if r['status'] == 'incremental'),
        'skipped': sum(1 for r in log_records if r['status'] == 'skipped_uptodate'),
        'errors': sum(1 for r in log_records if 'error' in str(r['status'])),
    }
    if os.path.exists(UPDATE_HISTORY):
        df_hist = pd.read_csv(UPDATE_HISTORY)
        df_hist = pd.concat([df_hist, pd.DataFrame([history_row])], ignore_index=True)
    else:
        df_hist = pd.DataFrame([history_row])
    df_hist.to_csv(UPDATE_HISTORY, index=False, encoding='utf-8-sig')
    print(f"[Step 4] 업데이트 이력 저장: {os.path.basename(UPDATE_HISTORY)}")


# ============================================================
# Main
# ============================================================
def main():
    start_time = time.time()
    print("=" * 60)
    print("PHASE1 Momentum - Step 1: 데이터 수집 (증분 업데이트)")
    print(f"실행 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 종목 리스트
    tickers, ticker_name_map = load_ticker_list()

    # 기존 캐시 로드
    existing_cache, last_dates = load_existing_cache()

    # 증분 수집
    daily_data, log_records = collect_incremental(tickers, ticker_name_map, existing_cache, last_dates)

    # 주간 리샘플링
    weekly_data = resample_to_weekly(daily_data)

    # 저장
    save_caches(daily_data, weekly_data, log_records)

    elapsed = time.time() - start_time

    # 요약
    print("\n" + "=" * 60)
    print(f"수집 완료 ({elapsed:.0f}초)")
    print("=" * 60)
    df_log = pd.DataFrame(log_records)
    for status in df_log['status'].unique():
        count = len(df_log[df_log['status'] == status])
        print(f"  {status}: {count}건")
    print(f"  캐시 총 종목: {len(daily_data)}")
    print("=" * 60)


if __name__ == '__main__':
    main()
