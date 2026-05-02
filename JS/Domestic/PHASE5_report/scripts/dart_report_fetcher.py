"""
PHASE5 Report - Step 1: DART 사업/분기보고서 XML 전문 수집
Date: 2026-05-01
Description:
    - PHASE2 시총 상위 500종목 대상
    - OpenDartReader를 통해 사업보고서/분기보고서 XML 전문 수집
    - 종목별 캐시 저장 (cache/{ticker}_{year}_{quarter}.pkl)
    - PHASE0 섹터 매핑 포함

Usage:
    C:/Python311/python.exe scripts/dart_report_fetcher.py
    C:/Python311/python.exe scripts/dart_report_fetcher.py --year 2025 --quarter 4Q
    C:/Python311/python.exe scripts/dart_report_fetcher.py --ticker 005930
    C:/Python311/python.exe scripts/dart_report_fetcher.py --sector 반도체
"""

import os
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env')
load_dotenv(_env_path)

import sys
import time
import datetime
import pickle
import json
import argparse
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import re

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
DOMESTIC_DIR = os.path.dirname(BASE_DIR)
PHASE0_DIR = os.path.join(DOMESTIC_DIR, 'PHASE0_classification')
PHASE2_DIR = os.path.join(DOMESTIC_DIR, 'PHASE2_fundamental')

CACHE_DIR = os.path.join(BASE_DIR, 'cache')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# DART 보고서 코드
REPRT_CODE_MAP = {
    '1Q': '11013',   # 1분기보고서
    '2Q': '11012',   # 반기보고서
    '3Q': '11014',   # 3분기보고서
    '4Q': '11011',   # 사업보고서(감사보고서 포함)
}

QUARTER_LABEL = {
    '11013': '1Q',
    '11012': '2Q',
    '11014': '3Q',
    '11011': '4Q',
}

MAX_STOCKS = 500
DART_SLEEP = 1.0   # API 호출 간격 (초)

# ============================================================
# 섹터 매핑 로드
# ============================================================
def load_sector_map():
    """PHASE0 섹터 분류 CSV에서 ticker → tier1 매핑 로드"""
    csv_path = os.path.join(PHASE0_DIR, 'kospi_kosdaq_sector_classification.csv')
    if not os.path.exists(csv_path):
        print(f"[WARN] 섹터 분류 파일 없음: {csv_path}")
        return {}
    df = pd.read_csv(csv_path)
    df['ticker'] = df['ticker'].astype(str).str.strip().str.zfill(6)
    return dict(zip(df['ticker'], df['tier1']))


# ============================================================
# 시총 상위 종목 로드 (PHASE2 캐시)
# ============================================================
def load_top_stocks(max_n=MAX_STOCKS):
    """PHASE2 fundamental_cache.pkl에서 시총 상위 종목 추출"""
    cache_path = os.path.join(PHASE2_DIR, 'cache', 'fundamental_cache.pkl')
    if not os.path.exists(cache_path):
        print(f"[ERROR] PHASE2 캐시 없음: {cache_path}")
        print("  → PHASE2 data_collector.py를 먼저 실행하세요.")
        sys.exit(1)

    with open(cache_path, 'rb') as f:
        cache = pickle.load(f)

    master = cache['master']

    # 시총 컬럼 찾기
    mcap_col = None
    for c in ['시가총액', '시가총액_y', '시가총액_x', '시가총액(억)']:
        if c in master.columns:
            mcap_col = c
            break

    if mcap_col:
        top = master.dropna(subset=[mcap_col]).nlargest(max_n, mcap_col)
    else:
        top = master.head(max_n)

    return top[['ticker', 'name']].copy()


# ============================================================
# XML 전문에서 텍스트 추출 (HTML 태그 제거)
# ============================================================
def extract_text_from_xml(xml_text):
    """DART XML/HTML에서 순수 텍스트 추출"""
    if not xml_text:
        return ""

    # BeautifulSoup으로 HTML 태그 제거
    soup = BeautifulSoup(xml_text, 'html.parser')

    # 테이블 처리: 셀 간 구분자 추가
    for table in soup.find_all('table'):
        for row in table.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            cell_texts = [c.get_text(strip=True) for c in cells]
            row.replace_with(' | '.join(cell_texts) + '\n')

    text = soup.get_text()

    # 연속 공백/줄바꿈 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = text.strip()

    return text


# ============================================================
# DART 보고서 수집
# ============================================================
def fetch_report(dart, ticker, name, year, quarter):
    """
    특정 종목의 특정 분기 보고서 XML 전문 수집.

    Returns:
        dict: {
            'ticker': str,
            'name': str,
            'year': int,
            'quarter': str,
            'rcpt_no': str,
            'report_title': str,
            'xml_texts': list[str],    # 원본 XML/HTML
            'plain_text': str,          # 태그 제거된 순수 텍스트
            'fetched_at': str,
        } or None
    """
    reprt_code = REPRT_CODE_MAP.get(quarter)
    if not reprt_code:
        print(f"  [ERROR] 잘못된 분기: {quarter}")
        return None

    try:
        # 1. 보고서 목록 검색
        reports = dart.list(ticker, start=f'{year}-01-01', end=f'{year}-12-31', kind='A')
        if reports is None or len(reports) == 0:
            return None

        # reprt_code에 해당하는 보고서 필터링
        # DART list 결과에서 report_nm으로 필터링
        quarter_keywords = {
            '1Q': '분기보고서',
            '2Q': '반기보고서',
            '3Q': '분기보고서',
            '4Q': '사업보고서',
        }

        keyword = quarter_keywords[quarter]
        matched = reports[reports['report_nm'].str.contains(keyword, na=False)]

        if quarter == '1Q':
            # 1분기와 3분기 구분: '[기재정정]' 제외하고 '1분기' or 첫번째
            matched_1q = matched[matched['report_nm'].str.contains('1분기|제1분기', na=False)]
            if len(matched_1q) > 0:
                matched = matched_1q
        elif quarter == '3Q':
            matched_3q = matched[matched['report_nm'].str.contains('3분기|제3분기', na=False)]
            if len(matched_3q) > 0:
                matched = matched_3q

        if len(matched) == 0:
            return None

        # 최신 보고서 (정정 포함 시 최신 것)
        rcpt_no = matched.iloc[0]['rcept_no']
        report_title = matched.iloc[0]['report_nm']

        # 2. 보고서 XML 전문 수집
        time.sleep(DART_SLEEP)
        xml_texts = dart.document_all(rcpt_no)

        if not xml_texts:
            return None

        # 3. 텍스트 추출 및 병합
        all_plain = []
        for xt in xml_texts:
            plain = extract_text_from_xml(xt)
            if plain:
                all_plain.append(plain)

        combined_text = '\n\n=== 문서 구분 ===\n\n'.join(all_plain)

        result = {
            'ticker': ticker,
            'name': name,
            'year': year,
            'quarter': quarter,
            'rcpt_no': rcpt_no,
            'report_title': report_title,
            'xml_texts': xml_texts,
            'plain_text': combined_text,
            'text_length': len(combined_text),
            'fetched_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        return result

    except Exception as e:
        print(f"  [ERROR] {ticker} {name}: {e}")
        return None


# ============================================================
# 캐시 관리
# ============================================================
def get_cache_path(ticker, year, quarter):
    return os.path.join(CACHE_DIR, f'{ticker}_{year}_{quarter}.pkl')


def is_cached(ticker, year, quarter):
    return os.path.exists(get_cache_path(ticker, year, quarter))


def save_cache(data, ticker, year, quarter):
    path = get_cache_path(ticker, year, quarter)
    with open(path, 'wb') as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_cache(ticker, year, quarter):
    path = get_cache_path(ticker, year, quarter)
    with open(path, 'rb') as f:
        return pickle.load(f)


# ============================================================
# 메인 수집 루프
# ============================================================
def collect_reports(year, quarter, tickers=None, sector=None, force=False):
    """
    보고서 수집 메인 함수.

    Args:
        year: 수집 연도 (int)
        quarter: 분기 ('1Q', '2Q', '3Q', '4Q')
        tickers: 특정 종목만 수집 (list of str, optional)
        sector: 특정 섹터만 수집 (str, optional)
        force: 캐시 무시하고 재수집 (bool)
    """
    print("=" * 60)
    print(f"PHASE5 Report - Step 1: DART 보고서 수집")
    print(f"  대상: {year}년 {quarter}")
    print(f"  실행: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # DART API 초기화
    dart_api_key = os.environ.get('DART_API_KEY', '')
    if not dart_api_key:
        print("[ERROR] DART_API_KEY 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    try:
        import OpenDartReader
        dart = OpenDartReader(dart_api_key)
        print(f"  OpenDartReader 초기화 완료")
    except Exception as e:
        print(f"  [ERROR] OpenDartReader 초기화 실패: {e}")
        sys.exit(1)

    # 종목 리스트 로드
    sector_map = load_sector_map()

    if tickers:
        # 특정 종목 지정
        top_stocks = pd.DataFrame({'ticker': tickers})
        # 이름 매핑 시도
        try:
            all_stocks = load_top_stocks(9999)
            name_map = dict(zip(all_stocks['ticker'], all_stocks['name']))
        except:
            name_map = {}
        top_stocks['name'] = top_stocks['ticker'].map(name_map).fillna('Unknown')
    else:
        top_stocks = load_top_stocks(MAX_STOCKS)

    # 섹터 필터
    if sector:
        top_stocks['tier1'] = top_stocks['ticker'].map(sector_map).fillna('기타')
        top_stocks = top_stocks[top_stocks['tier1'] == sector]
        print(f"  섹터 필터: {sector} ({len(top_stocks)}종목)")

    target_list = list(zip(top_stocks['ticker'], top_stocks['name']))
    print(f"  수집 대상: {len(target_list)}종목\n")

    success = 0
    skip = 0
    fail = 0
    errors = []

    for i, (tk, name) in enumerate(target_list):
        # 캐시 확인
        if not force and is_cached(tk, year, quarter):
            skip += 1
            if (i + 1) % 100 == 0:
                print(f"  [{i+1}/{len(target_list)}] 성공:{success} 스킵:{skip} 실패:{fail}")
            continue

        # 수집
        data = fetch_report(dart, tk, name, year, quarter)

        if data:
            save_cache(data, tk, year, quarter)
            success += 1
            tier1 = sector_map.get(tk, '기타')
            print(f"  [{i+1}] {name}({tk}) - {tier1} - {data['text_length']:,}자")
        else:
            fail += 1
            errors.append(f"{tk} {name}")

        if (i + 1) % 50 == 0:
            print(f"  --- [{i+1}/{len(target_list)}] 성공:{success} 스킵:{skip} 실패:{fail} ---")

        time.sleep(DART_SLEEP)

    # 로그 저장
    log_path = os.path.join(LOG_DIR, f'fetch_{year}_{quarter}_{datetime.date.today().strftime("%Y%m%d")}.log')
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"PHASE5 Report Fetch Log\n")
        f.write(f"Date: {datetime.datetime.now()}\n")
        f.write(f"Target: {year} {quarter}\n")
        f.write(f"Success: {success}, Skip: {skip}, Fail: {fail}\n\n")
        if errors:
            f.write("Failed:\n")
            for e in errors:
                f.write(f"  {e}\n")

    print(f"\n{'=' * 60}")
    print(f"수집 완료: 성공 {success}, 스킵(캐시) {skip}, 실패 {fail}")
    print(f"  로그: {log_path}")
    print("=" * 60)

    return success, skip, fail


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='PHASE5 DART 보고서 수집')
    parser.add_argument('--year', type=int, default=datetime.date.today().year - 1,
                        help='수집 연도 (기본: 전년도)')
    parser.add_argument('--quarter', type=str, default='4Q',
                        help='분기 (1Q/2Q/3Q/4Q, 기본: 4Q)')
    parser.add_argument('--ticker', type=str, default=None,
                        help='특정 종목 코드 (콤마 구분)')
    parser.add_argument('--sector', type=str, default=None,
                        help='특정 섹터만 수집')
    parser.add_argument('--force', action='store_true',
                        help='캐시 무시 재수집')
    args = parser.parse_args()

    tickers = None
    if args.ticker:
        tickers = [t.strip().zfill(6) for t in args.ticker.split(',')]

    collect_reports(
        year=args.year,
        quarter=args.quarter.upper(),
        tickers=tickers,
        sector=args.sector,
        force=args.force,
    )


if __name__ == '__main__':
    main()
