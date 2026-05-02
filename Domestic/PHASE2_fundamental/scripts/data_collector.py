"""
PHASE2 Fundamental - Step 1: 데이터 수집기 (v2)
Date: 2026-04-30
Description:
    - pykrx: 전종목 PER, PBR, EPS, BPS, DIV, DPS, 시가총액
    - DART: 재무제표(IS/BS) + 현금흐름표(CF) → 주주환원, 재무건전성
    - 기업 분류: Type A(일반), Type B(지주사), Type C(금융)
    - 캐시: fundamental_cache.pkl, dart_cache.pkl

Usage:
    C:/Python311/python.exe scripts/data_collector.py
    C:/Python311/python.exe scripts/data_collector.py --skip-dart
"""

import os
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env')
load_dotenv(_env_path)

import sys
import time
import glob
import datetime
import pickle
import pandas as pd
import numpy as np

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
DOMESTIC_DIR = os.path.dirname(BASE_DIR)
PHASE0_DIR = os.path.join(DOMESTIC_DIR, 'PHASE0_classification')

TODAY_STR = datetime.date.today().strftime('%Y%m%d')
TODAY_DATE = datetime.date.today()

MASTER_CANDIDATES = sorted(glob.glob(os.path.join(PHASE0_DIR, '*_classification_master_verified.xlsx')))
if not MASTER_CANDIDATES:
    print("[ERROR] PHASE0 마스터 파일을 찾을 수 없습니다.")
    sys.exit(1)
MASTER_EXCEL = MASTER_CANDIDATES[-1]

HOLDCO_LIST = os.path.join(BASE_DIR, 'data', 'holdco_list.csv')
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
FUNDAMENTAL_CACHE = os.path.join(CACHE_DIR, 'fundamental_cache.pkl')
DART_CACHE = os.path.join(CACHE_DIR, 'dart_cache.pkl')

LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
UPDATE_HISTORY = os.path.join(LOG_DIR, 'update_history.csv')

FINANCIAL_SECTORS = ['금융/보험', '금융', '보험', '은행', '증권', '기타금융']

# DART 수집 대상 연도 (최신 사업보고서)
DART_YEAR = TODAY_DATE.year - 1  # 2025년 실행 시 2024년 사업보고서
DART_SLEEP = 0.5  # API 호출 간격 (초)


# ============================================================
# Step 1: 마스터 + 기업 분류
# ============================================================
def load_master():
    df = pd.read_excel(MASTER_EXCEL, sheet_name='전체종목')
    df['ticker'] = df['ticker'].astype(str).str.strip().str.zfill(6)
    print(f"[Step 1] 마스터 로드: {len(df)}종목")
    return df


def classify_companies(master_df):
    sector_col = None
    for col in ['tier1', 'wics_tier1', 'sector']:
        if col in master_df.columns:
            sector_col = col
            break

    if sector_col:
        is_financial = master_df[sector_col].str.contains(
            '|'.join(FINANCIAL_SECTORS), na=False, case=False)
    else:
        is_financial = pd.Series(False, index=master_df.index)

    holdco_tickers = set()
    if os.path.exists(HOLDCO_LIST):
        hdf = pd.read_csv(HOLDCO_LIST)
        hdf['ticker'] = hdf['ticker'].astype(str).str.zfill(6)
        holdco_tickers = set(hdf['ticker'].tolist())

    if 'name' in master_df.columns:
        name_match = master_df['name'].str.contains(
            '지주|홀딩스|Holdings|금융지주', na=False, case=False)
        holdco_tickers = holdco_tickers | set(master_df.loc[name_match, 'ticker'].tolist())

    is_holdco = master_df['ticker'].isin(holdco_tickers)

    master_df['company_type'] = 'A'
    master_df.loc[is_holdco, 'company_type'] = 'B'
    master_df.loc[is_financial, 'company_type'] = 'C'
    master_df.loc[is_holdco & is_financial, 'company_type'] = 'C'

    counts = master_df['company_type'].value_counts()
    print(f"  분류: A={counts.get('A', 0)}, B={counts.get('B', 0)}, C={counts.get('C', 0)}")
    return master_df


# ============================================================
# Step 2: pykrx 수집
# ============================================================
def collect_pykrx(tickers):
    from pykrx import stock

    target_date = TODAY_STR
    for _ in range(10):
        try:
            fund_df = stock.get_market_fundamental_by_ticker(target_date, market='ALL')
            if fund_df is not None and len(fund_df) > 0:
                cols_to_check = [c for c in ['BPS', 'PER', 'PBR', 'EPS', 'DIV', 'DPS'] if c in fund_df.columns]
                if cols_to_check and not (fund_df[cols_to_check] == 0).all(axis=None):
                    break
        except Exception:
            pass
        dt = datetime.datetime.strptime(target_date, '%Y%m%d') - datetime.timedelta(days=1)
        target_date = dt.strftime('%Y%m%d')

    print(f"[Step 2] pykrx 수집 (기준일: {target_date})")
    fund_df = stock.get_market_fundamental_by_ticker(target_date, market='ALL')
    mcap_df = stock.get_market_cap_by_ticker(target_date, market='ALL')

    merged = fund_df.join(mcap_df, how='outer')
    merged.index.name = 'ticker'
    merged = merged.reset_index()
    merged['ticker'] = merged['ticker'].astype(str).str.zfill(6)
    merged = merged[merged['ticker'].isin(tickers)]

    merged['ROE_approx'] = np.where(merged['BPS'] > 0, merged['EPS'] / merged['BPS'] * 100, np.nan)
    print(f"  매칭: {len(merged)}종목, PER유효: {(merged['PER'] > 0).sum()}")
    return merged, target_date


# ============================================================
# Step 3: DART 재무제표 수집
# ============================================================
def _parse_dart_amount(val):
    """DART 금액 파싱 (콤마 문자열 또는 숫자)"""
    if pd.isna(val) or val == '' or val == '-':
        return np.nan
    try:
        return float(str(val).replace(',', ''))
    except (ValueError, TypeError):
        return np.nan


def _extract_item(df, sj_div, account_keywords, amount_col='thstrm_amount'):
    """재무제표에서 특정 항목 추출 (키워드 매칭)"""
    subset = df[df['sj_div'] == sj_div]
    for kw in account_keywords:
        match = subset[subset['account_nm'].str.contains(kw, na=False)]
        if len(match) > 0:
            return _parse_dart_amount(match.iloc[0][amount_col])
    return np.nan


def collect_dart(tickers, ticker_name_map, company_types):
    """DART API로 전종목 재무제표 + 현금흐름표 수집"""
    dart_api_key = os.environ.get('DART_API_KEY', '')
    if not dart_api_key:
        print("[Step 3] DART API 키 없음 → 스킵")
        return {}

    try:
        import OpenDartReader
        dart = OpenDartReader(dart_api_key)
    except Exception as e:
        print(f"[Step 3] OpenDartReader 초기화 실패: {e}")
        return {}

    print(f"[Step 3] DART 수집 시작 ({len(tickers)}종목, {DART_YEAR}년)")

    # 기존 캐시 로드 (증분 업데이트)
    existing = {}
    if os.path.exists(DART_CACHE):
        with open(DART_CACHE, 'rb') as f:
            existing = pickle.load(f)
        print(f"  기존 캐시: {len(existing)}종목")

    results = dict(existing)
    errors = []
    skipped = 0
    collected = 0

    for i, tk in enumerate(tickers):
        # 이미 수집된 종목 스킵 (같은 연도)
        if tk in results and results[tk].get('year') == DART_YEAR:
            skipped += 1
            continue

        name = ticker_name_map.get(tk, '?')
        try:
            # finstate_all: IS + BS + CF 모두 한 번에
            fs = dart.finstate_all(tk, DART_YEAR, reprt_code='11011', fs_div='CFS')
            if fs is None or len(fs) == 0:
                # 연결 없으면 별도 시도
                fs = dart.finstate_all(tk, DART_YEAR, reprt_code='11011', fs_div='OFS')

            if fs is None or len(fs) == 0:
                errors.append(tk)
                continue

            data = {'year': DART_YEAR, 'ticker': tk, 'name': name}

            # === 손익계산서 (IS) ===
            data['매출액'] = _extract_item(fs, 'IS', ['매출액', '영업수익', '매출'])
            data['영업이익'] = _extract_item(fs, 'IS', ['영업이익'])
            data['당기순이익'] = _extract_item(fs, 'IS', ['당기순이익', '당기순이익(손실)'])

            # 전기 (성장률 계산용)
            data['매출액_전기'] = _extract_item(fs, 'IS', ['매출액', '영업수익', '매출'], 'frmtrm_amount')
            data['영업이익_전기'] = _extract_item(fs, 'IS', ['영업이익'], 'frmtrm_amount')
            data['당기순이익_전기'] = _extract_item(fs, 'IS', ['당기순이익', '당기순이익(손실)'], 'frmtrm_amount')

            # === 재무상태표 (BS) ===
            data['자산총계'] = _extract_item(fs, 'BS', ['자산총계'])
            data['부채총계'] = _extract_item(fs, 'BS', ['부채총계'])
            data['자본총계'] = _extract_item(fs, 'BS', ['자본총계'])
            data['유동자산'] = _extract_item(fs, 'BS', ['유동자산'])
            data['유동부채'] = _extract_item(fs, 'BS', ['유동부채'])

            # === 현금흐름표 (CF) — 주주환원 핵심 ===
            data['배당금지급'] = _extract_item(fs, 'CF', ['배당금의지급', '배당금지급'])
            data['자사주취득'] = _extract_item(fs, 'CF', ['자기주식의 취득', '자기주식취득', '자사주취득'])
            data['자사주처분'] = _extract_item(fs, 'CF', ['자기주식의 처분', '자기주식처분', '자사주처분'])
            data['영업활동CF'] = _extract_item(fs, 'CF', ['영업활동현금흐름', '영업활동으로'])
            data['이자지급'] = _extract_item(fs, 'CF', ['이자의 지급', '이자지급'])

            results[tk] = data
            collected += 1

        except Exception as e:
            err_msg = str(e)[:80]
            errors.append(tk)
            if 'EXCEEDED' in err_msg.upper() or '한도' in err_msg:
                print(f"\n  [WARN] API 한도 초과! {collected}종목 수집 후 중단")
                break

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(tickers)}] 수집: {collected}, 스킵: {skipped}, 에러: {len(errors)}")

        time.sleep(DART_SLEEP)

    print(f"\n  DART 수집 완료: {collected}신규, {skipped}스킵, {len(errors)}에러")
    print(f"  캐시 총: {len(results)}종목")

    # 캐시 저장
    with open(DART_CACHE, 'wb') as f:
        pickle.dump(results, f, protocol=pickle.HIGHEST_PROTOCOL)
    size_mb = os.path.getsize(DART_CACHE) / (1024 * 1024)
    print(f"  저장: {size_mb:.1f}MB → {os.path.basename(DART_CACHE)}")

    return results


# ============================================================
# Step 4: 저장
# ============================================================
def save_fundamental_cache(master_df, pykrx_df, target_date, dart_count):
    cache = {
        'master': master_df,
        'pykrx': pykrx_df,
        'target_date': target_date,
        'collected_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'stage': '2B' if dart_count > 0 else '2A',
    }
    with open(FUNDAMENTAL_CACHE, 'wb') as f:
        pickle.dump(cache, f, protocol=pickle.HIGHEST_PROTOCOL)
    size_mb = os.path.getsize(FUNDAMENTAL_CACHE) / (1024 * 1024)
    print(f"[Step 4] 캐시 저장: {size_mb:.2f}MB")

    # 이력
    row = {
        'date': TODAY_STR,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'target_date': target_date,
        'total_tickers': len(pykrx_df),
        'dart_tickers': dart_count,
        'stage': cache['stage'],
    }
    if os.path.exists(UPDATE_HISTORY):
        hist = pd.read_csv(UPDATE_HISTORY)
        hist = pd.concat([hist, pd.DataFrame([row])], ignore_index=True)
    else:
        hist = pd.DataFrame([row])
    hist.to_csv(UPDATE_HISTORY, index=False, encoding='utf-8-sig')


# ============================================================
# Main
# ============================================================
def main():
    args = sys.argv[1:]
    skip_dart = '--skip-dart' in args

    start_time = time.time()
    print("=" * 60)
    print("PHASE2 Fundamental - Step 1: 데이터 수집 (v2)")
    print(f"실행: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if skip_dart:
        print("  → DART 수집 스킵")
    print("=" * 60)

    # 마스터 + 분류
    master_df = load_master()
    master_df = classify_companies(master_df)

    # pykrx
    tickers = master_df['ticker'].tolist()
    pykrx_df, target_date = collect_pykrx(tickers)
    master_df = master_df.merge(pykrx_df, on='ticker', how='left')

    # DART
    dart_count = 0
    if not skip_dart:
        ticker_name_map = dict(zip(master_df['ticker'], master_df.get('name', master_df['ticker'])))
        company_types = dict(zip(master_df['ticker'], master_df['company_type']))
        dart_results = collect_dart(tickers, ticker_name_map, company_types)
        dart_count = len(dart_results)

    # 저장
    save_fundamental_cache(master_df, pykrx_df, target_date, dart_count)

    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"수집 완료 ({elapsed:.0f}초)")
    print(f"  pykrx: {len(pykrx_df)}종목 / DART: {dart_count}종목")
    print("=" * 60)


if __name__ == '__main__':
    main()
