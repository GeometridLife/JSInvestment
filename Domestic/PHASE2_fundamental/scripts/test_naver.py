"""네이버 금융 API 테스트"""
import requests
import pandas as pd

# 방법 1: 네이버 금융 시가총액 페이지 (PER/ROE 포함)
# KOSPI sosok=0, KOSDAQ sosok=1
url = "https://finance.naver.com/sise/sise_market_sum.naver"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

print("=== 네이버 금융 시가총액 페이지 (KOSPI 1페이지) ===")
params = {'sosok': '0', 'page': '1'}
r = requests.get(url, params=params, headers=headers, timeout=15)
print(f"Status: {r.status_code}, Length: {len(r.text)}")

try:
    tables = pd.read_html(r.text, encoding='euc-kr')
    print(f"테이블 수: {len(tables)}")
    for i, t in enumerate(tables):
        if len(t) > 3 and len(t.columns) > 5:
            print(f"\n테이블 {i}: shape={t.shape}")
            print(f"컬럼: {t.columns.tolist()}")
            print(t.head(5).to_string())
except Exception as e:
    print(f"파싱 에러: {e}")

print("\n\n=== 방법 2: 네이버 금융 개별 종목 (삼성전자) ===")
url2 = "https://finance.naver.com/item/main.naver?code=005930"
r2 = requests.get(url2, headers=headers, timeout=15)
print(f"Status: {r2.status_code}, Length: {len(r2.text)}")

# PER/PBR/배당수익률 추출
import re
text = r2.text

for pattern_name, pattern in [
    ('PER', r'PER.*?<em>([0-9,.]+)</em>'),
    ('PBR', r'PBR.*?<em>([0-9,.]+)</em>'),
    ('배당수익률', r'배당수익률.*?<em>([0-9,.]+)</em>'),
    ('ROE', r'ROE.*?<em>([0-9,.]+)</em>'),
    ('EPS', r'EPS.*?>([0-9,.\-]+)<'),
    ('BPS', r'BPS.*?>([0-9,.\-]+)<'),
]:
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        print(f"  {pattern_name}: {matches[:3]}")
    else:
        print(f"  {pattern_name}: 없음")
