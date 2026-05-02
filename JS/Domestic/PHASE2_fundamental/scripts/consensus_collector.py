"""
PHASE2 Fundamental - Step 2: Naver Finance(WISEfn) Forward 컨센서스 수집
Date: 2026-05-01
Description:
    - navercomp.wisereport.co.kr 에서 Forward 컨센서스 스크래핑
    - table[5]: 주요지표 (PER, PBR, EPS, 매출액, 영업이익, ROE 등) Trailing(A) + Forward(E)
    - table[11]: 투자의견 컨센서스 (투자의견, 목표주가, Forward EPS, Forward PER, 추정기관수)
    - 시총 상위 ~500종목 대상
    - 캐시: consensus_cache.pkl

Usage:
    C:/Python311/python.exe scripts/consensus_collector.py
"""

import os
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env')
load_dotenv(_env_path)

import sys
import time
import datetime
import pickle
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
FUNDAMENTAL_CACHE = os.path.join(CACHE_DIR, 'fundamental_cache.pkl')
CONSENSUS_CACHE = os.path.join(CACHE_DIR, 'consensus_cache.pkl')

TODAY_STR = datetime.date.today().strftime('%Y%m%d')
MAX_STOCKS = 500       # 시총 상위 N종목만
SLEEP_SEC = 0.8        # 호출 간격 (네이버 차단 방지)
REQUEST_TIMEOUT = 15

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}


# ============================================================
# 숫자 파싱
# ============================================================
def _parse_number(text):
    """숫자 파싱 (콤마, 공백, N/A 처리)"""
    if not text or text.strip() in ['', '-', 'N/A', 'nan', 'NaN', '\xa0']:
        return np.nan
    try:
        return float(text.strip().replace(',', '').replace('\xa0', ''))
    except (ValueError, TypeError):
        return np.nan


# ============================================================
# Naver Finance (WISEfn/navercomp) 스크래핑
# ============================================================
def _find_table_by_header(tables, header_keywords):
    """
    테이블 리스트에서 헤더 행에 특정 키워드가 포함된 테이블을 찾음.
    테이블 인덱스가 변할 수 있으므로 키워드 기반 탐색.
    """
    for ti, table in enumerate(tables):
        rows = table.find_all('tr')
        if not rows:
            continue
        header_text = rows[0].get_text()
        if all(kw in header_text for kw in header_keywords):
            return ti, table
    return None, None


def fetch_naver_consensus(ticker):
    """
    Naver Finance(WISEfn) 기업개요 페이지에서 Forward 컨센서스 데이터 추출.

    데이터 소스:
    - table[5] (주요지표): PER, PBR, EPS, BPS, 매출액, 영업이익, 당기순이익, ROE 등
      컬럼: [주요지표, YYYY/MM(A), YYYY/MM(E)]  (A=실적, E=추정)
    - table[11] (투자의견 컨센서스): 투자의견, 목표주가, EPS, PER, 추정기관수

    Returns: dict or None
    """
    url = f'https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={ticker}'

    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return None

        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        tables = soup.find_all('table')
        result = {}

        # =====================================================
        # 1. 주요지표 테이블 (Forward/Trailing 밸류에이션+재무)
        # =====================================================
        # 키워드 기반 탐색: '주요지표' 헤더 + '(A)' or '(E)' 컬럼
        indicators_table = None
        indicators_idx = None

        for ti, table in enumerate(tables):
            rows = table.find_all('tr')
            if len(rows) < 5:  # 최소 5행 이상
                continue
            header_text = rows[0].get_text()
            if '주요지표' in header_text and ('(A)' in header_text or '(E)' in header_text):
                indicators_table = table
                indicators_idx = ti
                break

        # 못 찾으면 인덱스 5로 폴백
        if indicators_table is None and len(tables) > 5:
            rows = tables[5].find_all('tr')
            if len(rows) >= 5:
                header_text = rows[0].get_text()
                if '(A)' in header_text or '(E)' in header_text:
                    indicators_table = tables[5]
                    indicators_idx = 5

        if indicators_table:
            rows = indicators_table.find_all('tr')

            # 헤더에서 Trailing(A)과 Forward(E) 컬럼 인덱스 파악
            header_cells = rows[0].find_all(['th', 'td'])
            trailing_col = None
            forward_col = None

            for ci, cell in enumerate(header_cells):
                cell_text = cell.get_text(strip=True)
                if '(A)' in cell_text:
                    trailing_col = ci
                if '(E)' in cell_text:
                    forward_col = ci

            if forward_col is not None:
                # 각 지표 행 파싱
                for row in rows[1:]:
                    cells = row.find_all(['th', 'td'])
                    if len(cells) <= forward_col:
                        continue

                    label = cells[0].get_text(strip=True)
                    fwd_val = _parse_number(cells[forward_col].get_text(strip=True))
                    trail_val = np.nan
                    if trailing_col is not None and len(cells) > trailing_col:
                        trail_val = _parse_number(cells[trailing_col].get_text(strip=True))

                    # EPS
                    if label == 'EPS' or label.startswith('EPS('):
                        result['fwd_eps_from_table5'] = fwd_val
                        if not np.isnan(trail_val):
                            result['trailing_eps_fn'] = trail_val

                    # PER
                    elif label == 'PER' or label.startswith('PER('):
                        result['fwd_per_table5'] = fwd_val
                        if not np.isnan(trail_val):
                            result['trailing_per'] = trail_val

                    # PBR
                    elif label == 'PBR' or label.startswith('PBR('):
                        result['fwd_pbr'] = fwd_val
                        if not np.isnan(trail_val):
                            result['trailing_pbr'] = trail_val

                    # 매출액
                    elif '매출액' in label or '매출' == label:
                        result['fwd_revenue'] = fwd_val
                        if not np.isnan(trail_val):
                            result['trailing_revenue'] = trail_val

                    # 영업이익 (영업이익률/영업이익성장 제외)
                    elif '영업이익' in label and '률' not in label and '성장' not in label and '증가' not in label:
                        result['fwd_op'] = fwd_val
                        if not np.isnan(trail_val):
                            result['trailing_op'] = trail_val

                    # 당기순이익
                    elif '당기순이익' in label or '순이익' in label:
                        result['fwd_net_income'] = fwd_val
                        if not np.isnan(trail_val):
                            result['trailing_net_income'] = trail_val

                    # ROE
                    elif label == 'ROE' or label.startswith('ROE('):
                        result['fwd_roe'] = fwd_val

                    # BPS
                    elif label == 'BPS' or label.startswith('BPS('):
                        result['fwd_bps'] = fwd_val

        # =====================================================
        # 2. 투자의견 컨센서스 테이블
        # =====================================================
        # 키워드 기반 탐색: '투자의견', '목표주가', 'EPS'
        consensus_table = None

        for ti, table in enumerate(tables):
            rows = table.find_all('tr')
            if len(rows) != 2:  # 정확히 2행 (헤더+데이터)
                continue
            header_text = rows[0].get_text()
            if '투자의견' in header_text and '목표주가' in header_text:
                consensus_table = table
                break

        # 못 찾으면 인덱스 11로 폴백
        if consensus_table is None and len(tables) > 11:
            rows = tables[11].find_all('tr')
            if len(rows) == 2:
                header_text = rows[0].get_text()
                if '투자의견' in header_text or 'EPS' in header_text:
                    consensus_table = tables[11]

        if consensus_table:
            rows = consensus_table.find_all('tr')
            if len(rows) >= 2:
                header_cells = rows[0].find_all(['th', 'td'])
                data_cells = rows[1].find_all(['th', 'td'])

                # table[11] 구조 (확인됨):
                #   header: ['4.00', '투자의견', '목표주가(원)', 'EPS(원)', 'PER(배)', '추정기관수']  (6셀)
                #   data:   ['4.00', '298,750',  '38,055',      '5.79',    '24']                    (5셀)
                #
                # 헤더 첫 셀은 rating 값, '투자의견'은 그 레이블이므로
                # 데이터와 1칸 오프셋 발생. 데이터 기준으로 직접 파싱:
                #   data[0] = rating, data[1] = target, data[2] = EPS, data[3] = PER, data[4] = analysts

                if len(data_cells) >= 5:
                    result['consensus_rating'] = _parse_number(data_cells[0].get_text(strip=True))
                    result['target_price'] = _parse_number(data_cells[1].get_text(strip=True))
                    result['fwd_eps'] = _parse_number(data_cells[2].get_text(strip=True))
                    result['fwd_per'] = _parse_number(data_cells[3].get_text(strip=True))
                    result['analyst_count'] = _parse_number(data_cells[4].get_text(strip=True))
                elif len(data_cells) >= 3:
                    # 추정기관수 적은 종목은 컬럼이 줄 수 있음
                    result['consensus_rating'] = _parse_number(data_cells[0].get_text(strip=True))
                    result['fwd_eps'] = _parse_number(data_cells[1].get_text(strip=True)) if len(data_cells) > 1 else np.nan
                    result['target_price'] = _parse_number(data_cells[1].get_text(strip=True)) if len(data_cells) > 1 else np.nan

        # =====================================================
        # 3. table[5]의 EPS를 fwd_eps 폴백으로 사용
        # =====================================================
        if 'fwd_eps' not in result and 'fwd_eps_from_table5' in result:
            result['fwd_eps'] = result['fwd_eps_from_table5']

        # =====================================================
        # 4. 데이터 검증: 최소 Forward EPS 또는 매출 있어야 유효
        # =====================================================
        if result and ('fwd_eps' in result or 'fwd_revenue' in result):
            return result
        return None

    except Exception as e:
        return None


# ============================================================
# 메인 수집 루프
# ============================================================
def collect_consensus():
    print("=" * 60)
    print("PHASE2 Fundamental - Step 2: Naver Finance 컨센서스 수집")
    print(f"실행: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 마스터 캐시 로드 (시총 순 정렬용)
    if not os.path.exists(FUNDAMENTAL_CACHE):
        print("[ERROR] fundamental_cache.pkl 없음. data_collector.py를 먼저 실행하세요.")
        sys.exit(1)

    with open(FUNDAMENTAL_CACHE, 'rb') as f:
        cache = pickle.load(f)

    master = cache['master']

    # 시총 상위 N종목 선별
    mcap_col = None
    for c in ['시가총액', '시가총액_y', '시가총액_x', '시가총액(억)']:
        if c in master.columns:
            mcap_col = c
            break
    if mcap_col:
        top_stocks = master.dropna(subset=[mcap_col]).nlargest(MAX_STOCKS, mcap_col)
    else:
        top_stocks = master.head(MAX_STOCKS)

    tickers = top_stocks['ticker'].tolist()
    names = dict(zip(top_stocks['ticker'], top_stocks.get('name', top_stocks['ticker'])))

    print(f"  대상: {len(tickers)}종목 (시총 상위)")

    # 기존 캐시 로드
    existing = {}
    if os.path.exists(CONSENSUS_CACHE):
        with open(CONSENSUS_CACHE, 'rb') as f:
            existing = pickle.load(f)
        # 오늘 수집분이면 스킵
        if existing.get('_collected_date') == TODAY_STR:
            print(f"  오늘 이미 수집됨 ({len(existing) - 1}종목). 스킵.")
            return existing

    results = {}
    success = 0
    fail = 0
    unique_eps = set()

    for i, tk in enumerate(tickers):
        name = names.get(tk, tk)
        data = fetch_naver_consensus(tk)

        if data:
            data['name'] = name
            results[tk] = data
            success += 1
            # EPS 고유값 추적 (모든 종목이 같은 값인지 진단)
            eps = data.get('fwd_eps')
            if eps is not None and not np.isnan(eps):
                unique_eps.add(eps)
        else:
            fail += 1

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(tickers)}] 성공: {success}, 실패: {fail}, 고유 EPS: {len(unique_eps)}")

        time.sleep(SLEEP_SEC)

    results['_collected_date'] = TODAY_STR
    results['_collected_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 저장
    with open(CONSENSUS_CACHE, 'wb') as f:
        pickle.dump(results, f, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"\n{'=' * 60}")
    print(f"컨센서스 수집 완료")
    print(f"  성공: {success}종목, 실패: {fail}종목")
    print(f"  고유 fwd_eps 값: {len(unique_eps)}개")
    if len(unique_eps) <= 3:
        print(f"  [WARNING] fwd_eps 고유값이 너무 적음! 데이터 확인 필요: {unique_eps}")
    # 샘플 출력 (검증용)
    sample_tks = [tk for tk in list(results.keys())[:5] if not tk.startswith('_')]
    for tk in sample_tks:
        d = results[tk]
        print(f"    {d.get('name','?'):10s}  fwd_eps={d.get('fwd_eps','?'):>10}  "
              f"fwd_rev={d.get('fwd_revenue','?'):>12}  fwd_op={d.get('fwd_op','?'):>10}  "
              f"target={d.get('target_price','?'):>10}  analysts={d.get('analyst_count','?')}")
    print("=" * 60)

    return results


if __name__ == '__main__':
    collect_consensus()
