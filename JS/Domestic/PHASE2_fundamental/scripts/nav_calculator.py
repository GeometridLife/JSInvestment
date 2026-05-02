"""
PHASE2 Fundamental - Step 3: 지주사 NAV 계산
Date: 2026-05-01
Description:
    - holdco_list.csv + holdco_subsidiaries.csv 기반
    - NAV = 상장자회사 시총×지분율 + 비상장 장부가 + 자체사업 - 순차입금
    - 자체사업 = 별도(OFS) 영업이익 × 멀티플 (연결 아님!)
    - NAV 디스카운트율 산출
    - 캐시: nav_cache.pkl

Usage:
    C:/Python311/python.exe scripts/nav_calculator.py
"""

import os
import time
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env')
load_dotenv(_env_path)

import sys
import datetime
import pickle
import pandas as pd
import numpy as np

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
DATA_DIR = os.path.join(BASE_DIR, 'data')

FUNDAMENTAL_CACHE = os.path.join(CACHE_DIR, 'fundamental_cache.pkl')
DART_CACHE = os.path.join(CACHE_DIR, 'dart_cache.pkl')
NAV_CACHE = os.path.join(CACHE_DIR, 'nav_cache.pkl')

HOLDCO_LIST = os.path.join(DATA_DIR, 'holdco_list.csv')
HOLDCO_SUBS = os.path.join(DATA_DIR, 'holdco_subsidiaries.csv')

OWN_BIZ_MULTIPLE = 8  # 자체사업 가치 = 별도 영업이익 × 멀티플
DART_YEAR = datetime.date.today().year - 1
DART_SLEEP = 0.5


def _parse_dart_amount(val):
    if pd.isna(val) or val == '' or val == '-':
        return np.nan
    try:
        return float(str(val).replace(',', ''))
    except (ValueError, TypeError):
        return np.nan


def _extract_item(df, sj_div, account_keywords, amount_col='thstrm_amount'):
    subset = df[df['sj_div'] == sj_div]
    for kw in account_keywords:
        match = subset[subset['account_nm'].str.contains(kw, na=False)]
        if len(match) > 0:
            return _parse_dart_amount(match.iloc[0][amount_col])
    return np.nan


def fetch_holdco_ofs(holdco_tickers):
    """지주사 별도(OFS) 재무제표 수집 — 자체사업 가치 + 순차입금 산출용"""
    dart_api_key = os.environ.get('DART_API_KEY', '')
    if not dart_api_key:
        print("  [WARN] DART API 키 없음 → 별도 재무제표 수집 스킵")
        return {}

    try:
        import OpenDartReader
        dart = OpenDartReader(dart_api_key)
    except Exception as e:
        print(f"  [WARN] OpenDartReader 실패: {e}")
        return {}

    ofs_data = {}
    for tk in holdco_tickers:
        try:
            fs = dart.finstate_all(tk, DART_YEAR, reprt_code='11011', fs_div='OFS')
            if fs is None or len(fs) == 0:
                continue

            data = {}
            data['영업이익'] = _extract_item(fs, 'IS', ['영업이익'])
            data['부채총계'] = _extract_item(fs, 'BS', ['부채총계'])
            data['유동자산'] = _extract_item(fs, 'BS', ['유동자산'])
            ofs_data[tk] = data

        except Exception as e:
            pass

        time.sleep(DART_SLEEP)

    print(f"  별도(OFS) 수집: {len(ofs_data)}/{len(holdco_tickers)}개 지주사")
    return ofs_data


def calculate_nav():
    print("=" * 60)
    print("PHASE2 Fundamental - Step 3: 지주사 NAV 계산")
    print(f"실행: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # --- 데이터 로드 ---
    if not os.path.exists(FUNDAMENTAL_CACHE):
        print("[ERROR] fundamental_cache.pkl 없음")
        sys.exit(1)

    with open(FUNDAMENTAL_CACHE, 'rb') as f:
        fund_cache = pickle.load(f)
    master = fund_cache['master']

    # 시가총액 딕셔너리
    mcap_dict = {}
    mcap_col = '시가총액' if '시가총액' in master.columns else None
    if mcap_col:
        for _, row in master.iterrows():
            if pd.notna(row.get(mcap_col)):
                mcap_dict[row['ticker']] = row[mcap_col]

    # DART 데이터 — 별도(OFS) 재무제표를 직접 수집
    # (dart_cache.pkl은 연결(CFS) 기준이라 자체사업 가치 산출에 부적합)

    # 지주사/자회사 데이터
    if not os.path.exists(HOLDCO_SUBS):
        print("[WARN] holdco_subsidiaries.csv 없음 → NAV 계산 스킵")
        return {}

    subs_df = pd.read_csv(HOLDCO_SUBS)
    subs_df['holdco_ticker'] = subs_df['holdco_ticker'].astype(str).str.zfill(6)
    subs_df['sub_ticker'] = subs_df['sub_ticker'].astype(str).str.zfill(6)

    holdco_tickers = subs_df['holdco_ticker'].unique()
    print(f"  지주사: {len(holdco_tickers)}개")

    # 별도(OFS) 재무제표 수집
    ofs_data = fetch_holdco_ofs(holdco_tickers)

    # --- NAV 계산 ---
    nav_results = {}

    for hc_tk in holdco_tickers:
        hc_subs = subs_df[subs_df['holdco_ticker'] == hc_tk]
        hc_name = hc_subs.iloc[0].get('holdco_name', hc_tk)

        nav_detail = {
            'ticker': hc_tk,
            'name': hc_name,
            'listed_sub_value': 0,
            'unlisted_sub_value': 0,
            'own_biz_value': 0,
            'net_debt': 0,
            'subsidiaries': [],
        }

        # (1) 상장 자회사 지분가치
        for _, sub in hc_subs.iterrows():
            sub_tk = sub['sub_ticker']
            ownership = sub.get('ownership_pct', 0)
            is_listed = str(sub.get('is_listed', 'N')).upper() == 'Y'

            if is_listed and sub_tk in mcap_dict:
                sub_mcap = mcap_dict[sub_tk]
                stake_value = sub_mcap * ownership / 100
                nav_detail['listed_sub_value'] += stake_value
                nav_detail['subsidiaries'].append({
                    'name': sub.get('sub_name', sub_tk),
                    'ticker': sub_tk,
                    'listed': True,
                    'mcap': sub_mcap,
                    'ownership': ownership,
                    'value': stake_value,
                })
            elif not is_listed:
                # 비상장: DART에서 장부가 추출 (향후 구현)
                # 현재는 0으로 처리 (보수적)
                nav_detail['subsidiaries'].append({
                    'name': sub.get('sub_name', sub_tk),
                    'ticker': sub_tk,
                    'listed': False,
                    'ownership': ownership,
                    'value': 0,
                })

        # (2) 자체사업 가치 (별도(OFS) 영업이익 × 멀티플)
        if hc_tk in ofs_data:
            hc_ofs = ofs_data[hc_tk]
            own_op = hc_ofs.get('영업이익', 0)
            if pd.notna(own_op) and own_op > 0:
                nav_detail['own_biz_value'] = own_op * OWN_BIZ_MULTIPLE

        # (3) 순차입금 (별도(OFS) 기준: 부채총계 - 유동자산)
        if hc_tk in ofs_data:
            hc_ofs = ofs_data[hc_tk]
            debt = hc_ofs.get('부채총계', 0)
            current_asset = hc_ofs.get('유동자산', 0)
            if pd.notna(debt) and pd.notna(current_asset):
                nav_detail['net_debt'] = max(0, debt - current_asset)

        # NAV 합산
        nav = (nav_detail['listed_sub_value']
               + nav_detail['unlisted_sub_value']
               + nav_detail['own_biz_value']
               - nav_detail['net_debt'])

        nav_detail['nav'] = nav

        # NAV 디스카운트
        hc_mcap = mcap_dict.get(hc_tk, 0)
        nav_detail['market_cap'] = hc_mcap

        if nav > 0 and hc_mcap > 0:
            nav_detail['nav_discount'] = 1 - (hc_mcap / nav)
        else:
            nav_detail['nav_discount'] = np.nan

        nav_results[hc_tk] = nav_detail

        # 출력
        discount_str = f"{nav_detail['nav_discount']:.1%}" if pd.notna(nav_detail.get('nav_discount')) else 'N/A'
        print(f"  {hc_name}({hc_tk}): NAV={nav/1e8:.0f}억, 시총={hc_mcap/1e8:.0f}억, 디스카운트={discount_str}")

    # 저장
    with open(NAV_CACHE, 'wb') as f:
        pickle.dump(nav_results, f, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"\n  저장: {os.path.basename(NAV_CACHE)} ({len(nav_results)}종목)")
    return nav_results


if __name__ == '__main__':
    calculate_nav()
