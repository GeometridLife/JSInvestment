"""
PHASE2 Fundamental - Step 1: 데이터 수집기 (1단계: 기본 밸류에이션)
Date: 2026-04-28
Description:
    - KRX 직접 API로 전종목 PER, PBR, EPS, BPS, DIV, 시가총액 수집
    - pykrx 로그인 불필요 (requests로 직접 호출)
    - PHASE0 마스터에서 종목 리스트 + 섹터 정보 로드
    - 기업 분류: Type A(일반), Type B(지주사), Type C(금융)
    - ROE 근사값 계산 (EPS/BPS)
    - 캐시 저장 (cache/fundamental_cache.pkl)

Usage:
    C:/Python311/python.exe scripts/data_collector.py
"""

import os
from dotenv import load_dotenv

# .env 파일에서 KRX 인증정보 로드
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env')
load_dotenv(_env_path)

import sys
import time
import glob
import datetime
import pickle
import requests
import io
import pandas as pd
import numpy as np

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)  # PHASE2_fundamental/
DOMESTIC_DIR = os.path.dirname(BASE_DIR)  # Domestic/
PHASE0_DIR = os.path.join(DOMESTIC_DIR, 'PHASE0_classification')

TODAY_STR = datetime.date.today().strftime('%Y%m%d')
TODAY_DATE = datetime.date.today()

# 입력: PHASE0 마스터 테이블
MASTER_CANDIDATES = sorted(glob.glob(os.path.join(PHASE0_DIR, '*_classification_master_verified.xlsx')))
if not MASTER_CANDIDATES:
    print("[ERROR] PHASE0 마스터 파일을 찾을 수 없습니다.")
    sys.exit(1)
MASTER_EXCEL = MASTER_CANDIDATES[-1]

# 지주사 데이터
HOLDCO_LIST = os.path.join(BASE_DIR, 'data', 'holdco_list.csv')
HOLDCO_SUBS = os.path.join(BASE_DIR, 'data', 'holdco_subsidiaries.csv')

# 캐시
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
FUNDAMENTAL_CACHE = os.path.join(CACHE_DIR, 'fundamental_cache.pkl')

# 로그
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
UPDATE_HISTORY = os.path.join(LOG_DIR, 'update_history.csv')

# 금융업 섹터 (PHASE0 마스터의 tier1 기준)
FINANCIAL_SECTORS = ['금융/보험', '금융', '보험', '은행', '증권', '기타금융']


# ============================================================
# Step 1: 종목 리스트 + 섹터 정보 로드
# ============================================================
def load_master():
    """PHASE0 마스터에서 종목 리스트 + 섹터 정보 로드"""
    df = pd.read_excel(MASTER_EXCEL, sheet_name='전체종목')
    df['ticker'] = df['ticker'].astype(str).str.strip().str.zfill(6)
    print(f"[Step 1] 마스터 로드: {len(df)}종목 ({os.path.basename(MASTER_EXCEL)})")
    return df


# ============================================================
# Step 2: 기업 분류 (Type A/B/C)
# ============================================================
def classify_companies(master_df):
    """
    Type A: 일반기업
    Type B: 지주사 (NAV 조정 대상)
    Type C: 금융업 (별도 처리)
    """
    # 금융업 판별 (섹터 기반)
    sector_col = None
    for col in ['tier1', 'wics_tier1', 'sector', 'WICS_tier1', 'wics_sector']:
        if col in master_df.columns:
            sector_col = col
            break

    if sector_col:
        is_financial = master_df[sector_col].str.contains(
            '|'.join(FINANCIAL_SECTORS), na=False, case=False
        )
    else:
        is_financial = pd.Series(False, index=master_df.index)
        print("  [WARN] 섹터 컬럼을 찾을 수 없어 금융업 분류 스킵")

    # 지주사 판별
    holdco_tickers = set()
    if os.path.exists(HOLDCO_LIST):
        holdco_df = pd.read_csv(HOLDCO_LIST)
        holdco_df['ticker'] = holdco_df['ticker'].astype(str).str.zfill(6)
        holdco_tickers = set(holdco_df['ticker'].tolist())
        print(f"  지주사 목록 로드: {len(holdco_tickers)}종목")

    # 종목명 패턴으로 추가 지주사 탐지
    name_patterns = ['지주', '홀딩스', 'Holdings', '금융지주']
    if 'name' in master_df.columns:
        name_match = master_df['name'].str.contains(
            '|'.join(name_patterns), na=False, case=False
        )
        extra_holdcos = set(master_df.loc[name_match, 'ticker'].tolist())
        holdco_tickers = holdco_tickers | extra_holdcos

    is_holdco = master_df['ticker'].isin(holdco_tickers)

    # 분류 부여 (금융지주는 Type C 우선)
    master_df['company_type'] = 'A'  # 기본: 일반
    master_df.loc[is_holdco, 'company_type'] = 'B'  # 지주사
    master_df.loc[is_financial, 'company_type'] = 'C'  # 금융업
    # 금융지주는 C (금융 우선)
    master_df.loc[is_holdco & is_financial, 'company_type'] = 'C'

    counts = master_df['company_type'].value_counts()
    print(f"  기업 분류: Type A(일반)={counts.get('A', 0)}, "
          f"Type B(지주사)={counts.get('B', 0)}, "
          f"Type C(금융)={counts.get('C', 0)}")

    return master_df


# ============================================================
# Step 3: KRX 직접 API로 데이터 수집
# ============================================================
def _find_recent_trading_date():
    """최근 거래일 찾기 (오늘부터 역순 탐색)"""
    dt = TODAY_DATE
    for _ in range(10):
        date_str = dt.strftime('%Y%m%d')
        try:
            # KRX 시세 API로 거래일 여부 확인
            result = _fetch_krx_fundamental(date_str)
            if result is not None and len(result) > 10:
                return date_str
        except Exception:
            pass
        dt -= datetime.timedelta(days=1)
    return None


def _fetch_krx_fundamental(date_str):
    """
    KRX data.krx.co.kr에서 전종목 PER/PBR/배당수익률 조회
    PER/PBR/배당수익률 페이지: MDCSTAT03501
    """
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"

    payload = {
        'bld': 'dbms/MDC/STAT/standard/MDCSTAT03501',
        'locale': 'ko_KR',
        'searchType': '1',
        'mktId': 'ALL',
        'trdDd': date_str,
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020203',
    }

    resp = requests.post(url, data=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        return None

    data = resp.json()
    items = data.get('OutBlock_1', data.get('output', []))
    if not items:
        return None

    df = pd.DataFrame(items)
    return df


def _fetch_krx_marcap(date_str):
    """
    KRX data.krx.co.kr에서 전종목 시가총액 조회
    시가총액 페이지: MDCSTAT01501
    """
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"

    payload = {
        'bld': 'dbms/MDC/STAT/standard/MDCSTAT01501',
        'locale': 'ko_KR',
        'mktId': 'ALL',
        'trdDd': date_str,
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101',
    }

    resp = requests.post(url, data=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        return None

    data = resp.json()
    items = data.get('OutBlock_1', data.get('output', []))
    if not items:
        return None

    df = pd.DataFrame(items)
    return df


def _parse_krx_number(val):
    """KRX 숫자 문자열 파싱 (콤마 제거, 빈 값 → NaN)"""
    if pd.isna(val) or val == '' or val == '-':
        return np.nan
    try:
        return float(str(val).replace(',', ''))
    except (ValueError, TypeError):
        return np.nan


def collect_krx_data(tickers):
    """KRX 직접 API로 전종목 PER, PBR, EPS, BPS, DIV, 시가총액 수집"""
    print("[Step 3] KRX 직접 API 데이터 수집 시작...")

    # 최근 거래일 찾기
    target_date = _find_recent_trading_date()
    if target_date is None:
        print("  [ERROR] 최근 거래일을 찾을 수 없습니다.")
        sys.exit(1)
    print(f"  기준일: {target_date}")

    # --- PER/PBR/배당수익률 ---
    fund_raw = _fetch_krx_fundamental(target_date)
    if fund_raw is None or len(fund_raw) == 0:
        print("  [ERROR] PER/PBR 데이터를 가져올 수 없습니다.")
        sys.exit(1)

    print(f"  PER/PBR 원본: {len(fund_raw)}종목")
    print(f"  컬럼: {fund_raw.columns.tolist()}")

    # 컬럼명 매핑 (KRX JSON 키 → 표준 컬럼명)
    # KRX 컬럼명은 한글 또는 영문 약어일 수 있음
    fund_df = pd.DataFrame()
    # 종목코드 컬럼 찾기
    for code_col in ['ISU_SRT_CD', 'ISU_CD', 'isu_srt_cd', 'isu_cd', 'TRD_DD']:
        if code_col in fund_raw.columns:
            fund_df['ticker'] = fund_raw[code_col].astype(str).str.strip()
            break
    else:
        # 첫 번째 컬럼이 종목코드일 가능성
        fund_df['ticker'] = fund_raw.iloc[:, 0].astype(str).str.strip()

    # 종목명
    for name_col in ['ISU_ABBRV', 'isu_abbrv', 'ISU_NM']:
        if name_col in fund_raw.columns:
            fund_df['krx_name'] = fund_raw[name_col]
            break

    # PER, PBR, EPS, BPS, DIV, DPS 매핑
    col_mapping = {
        'PER': ['PER', 'per'],
        'PBR': ['PBR', 'pbr'],
        'EPS': ['EPS', 'eps'],
        'BPS': ['BPS', 'bps'],
        'DIV': ['DVD_YLD', 'dvd_yld', 'DIV_YLD', 'DY'],
        'DPS': ['DPS', 'dps', 'DVD', 'dvd'],
    }

    for target, candidates in col_mapping.items():
        for src in candidates:
            if src in fund_raw.columns:
                fund_df[target] = fund_raw[src].apply(_parse_krx_number)
                break
        if target not in fund_df.columns:
            fund_df[target] = np.nan

    # --- 시가총액 ---
    mcap_raw = _fetch_krx_marcap(target_date)
    if mcap_raw is not None and len(mcap_raw) > 0:
        print(f"  시가총액 원본: {len(mcap_raw)}종목")

        mcap_df = pd.DataFrame()
        for code_col in ['ISU_SRT_CD', 'ISU_CD', 'isu_srt_cd', 'isu_cd']:
            if code_col in mcap_raw.columns:
                mcap_df['ticker'] = mcap_raw[code_col].astype(str).str.strip()
                break
        else:
            mcap_df['ticker'] = mcap_raw.iloc[:, 0].astype(str).str.strip()

        for mcap_col in ['MKTCAP', 'mktcap', 'LIST_SHRS']:
            if mcap_col in mcap_raw.columns:
                mcap_df['시가총액'] = mcap_raw[mcap_col].apply(_parse_krx_number)
                break

        for vol_col in ['ACC_TRDVOL', 'acc_trdvol']:
            if vol_col in mcap_raw.columns:
                mcap_df['거래량'] = mcap_raw[vol_col].apply(_parse_krx_number)
                break

        for amt_col in ['ACC_TRDVAL', 'acc_trdval']:
            if amt_col in mcap_raw.columns:
                mcap_df['거래대금'] = mcap_raw[amt_col].apply(_parse_krx_number)
                break

        # 병합
        fund_df = fund_df.merge(mcap_df, on='ticker', how='left')
    else:
        print("  [WARN] 시가총액 데이터를 가져올 수 없습니다.")

    # ticker 정리 (6자리 제로패딩)
    fund_df['ticker'] = fund_df['ticker'].str.zfill(6)

    # 대상 종목만 필터
    fund_df = fund_df[fund_df['ticker'].isin(tickers)].copy()
    print(f"  마스터 매칭: {len(fund_df)}종목")

    # ROE 근사값 계산
    fund_df['ROE_approx'] = np.where(
        fund_df['BPS'] > 0,
        fund_df['EPS'] / fund_df['BPS'] * 100,
        np.nan
    )

    # 요약
    for col in ['PER', 'PBR', 'EPS', 'BPS', 'DIV', 'ROE_approx']:
        if col in fund_df.columns:
            valid = fund_df[col].notna() & (fund_df[col] != 0)
            print(f"  {col} 유효: {valid.sum()}")

    return fund_df, target_date


# ============================================================
# Step 3-alt: pykrx fallback
# ============================================================
def collect_pykrx_data(tickers):
    """pykrx fallback (KRX 직접 API 실패 시)"""
    try:
        from pykrx import stock
    except ImportError:
        print("[ERROR] pykrx도 사용할 수 없습니다.")
        sys.exit(1)

    target_date = TODAY_STR
    max_retries = 10
    for attempt in range(max_retries):
        try:
            fund_df = stock.get_market_fundamental_by_ticker(target_date, market='ALL')
            if fund_df is not None and len(fund_df) > 0:
                if (fund_df[['BPS', 'PER', 'PBR', 'EPS', 'DIV', 'DPS']] == 0).all(axis=None):
                    dt = datetime.datetime.strptime(target_date, '%Y%m%d')
                    dt -= datetime.timedelta(days=1)
                    target_date = dt.strftime('%Y%m%d')
                    continue
                break
        except Exception:
            dt = datetime.datetime.strptime(target_date, '%Y%m%d')
            dt -= datetime.timedelta(days=1)
            target_date = dt.strftime('%Y%m%d')

    print(f"[Step 3] pykrx 데이터 수집 (기준일: {target_date})")

    fund_df = stock.get_market_fundamental_by_ticker(target_date, market='ALL')
    mcap_df = stock.get_market_cap_by_ticker(target_date, market='ALL')

    merged = fund_df.join(mcap_df, how='outer')
    merged.index.name = 'ticker'
    merged = merged.reset_index()
    merged['ticker'] = merged['ticker'].astype(str).str.zfill(6)
    merged = merged[merged['ticker'].isin(tickers)]

    merged['ROE_approx'] = np.where(
        merged['BPS'] > 0,
        merged['EPS'] / merged['BPS'] * 100,
        np.nan
    )

    return merged, target_date


# ============================================================
# Step 4: 저장
# ============================================================
def save_cache(master_df, fund_df, target_date):
    """캐시 저장"""
    cache = {
        'master': master_df,
        'pykrx': fund_df,  # 호환성 유지 (키 이름)
        'target_date': target_date,
        'collected_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'stage': '2A',
    }

    with open(FUNDAMENTAL_CACHE, 'wb') as f:
        pickle.dump(cache, f, protocol=pickle.HIGHEST_PROTOCOL)

    size_mb = os.path.getsize(FUNDAMENTAL_CACHE) / (1024 * 1024)
    print(f"[Step 4] 캐시 저장: {size_mb:.2f}MB → {os.path.basename(FUNDAMENTAL_CACHE)}")

    # 업데이트 이력
    history_row = {
        'date': TODAY_STR,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'target_date': target_date,
        'total_tickers': len(fund_df),
        'type_a': len(master_df[master_df['company_type'] == 'A']),
        'type_b': len(master_df[master_df['company_type'] == 'B']),
        'type_c': len(master_df[master_df['company_type'] == 'C']),
        'stage': '2A',
    }
    if os.path.exists(UPDATE_HISTORY):
        df_hist = pd.read_csv(UPDATE_HISTORY)
        df_hist = pd.concat([df_hist, pd.DataFrame([history_row])], ignore_index=True)
    else:
        df_hist = pd.DataFrame([history_row])
    df_hist.to_csv(UPDATE_HISTORY, index=False, encoding='utf-8-sig')
    print(f"[Step 4] 이력 저장: {os.path.basename(UPDATE_HISTORY)}")


# ============================================================
# Main
# ============================================================
def main():
    start_time = time.time()
    print("=" * 60)
    print("PHASE2 Fundamental - Step 1: 데이터 수집")
    print(f"실행 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 마스터 로드
    master_df = load_master()

    # 기업 분류
    master_df = classify_companies(master_df)

    # 데이터 수집 (pykrx 우선, 실패 시 KRX 직접 API fallback)
    tickers = master_df['ticker'].tolist()
    try:
        print("\n[방법 1] pykrx 시도...")
        fund_df, target_date = collect_pykrx_data(tickers)
        print(f"  → pykrx 성공")
    except Exception as e:
        print(f"  → pykrx 실패: {e}")
        print("\n[방법 2] KRX 직접 API fallback 시도...")
        try:
            fund_df, target_date = collect_krx_data(tickers)
            if len(fund_df) < 100:
                raise ValueError(f"KRX 데이터 부족: {len(fund_df)}종목")
            print(f"  → KRX 직접 API 성공")
        except Exception as e2:
            print(f"  → KRX 직접 API도 실패: {e2}")
            print("\n[ERROR] 데이터를 수집할 수 없습니다.")
            print("  해결 방법:")
            print("  1) 인터넷 연결 확인")
            print("  2) pip install --upgrade pykrx")
            print("  3) KRX 사이트 접속 가능 여부 확인: http://data.krx.co.kr")
            sys.exit(1)

    # 마스터에 펀더멘탈 데이터 병합
    master_df = master_df.merge(fund_df, on='ticker', how='left')

    # 저장
    save_cache(master_df, fund_df, target_date)

    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"수집 완료 ({elapsed:.0f}초)")
    print(f"  전체 종목: {len(master_df)}")
    print(f"  펀더멘탈 매칭: {len(fund_df)}종목")
    for col in ['PER', 'PBR', 'DIV', 'ROE_approx']:
        if col in master_df.columns:
            print(f"  {col} 유효: {master_df[col].notna().sum()}")
    print("=" * 60)


if __name__ == '__main__':
    main()
