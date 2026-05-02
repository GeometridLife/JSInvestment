"""
PHASE0 Global Classification
- NASDAQ Screener CSV + FinanceDatabase 기반 미국 주식 섹터 분류
- 시총 ≥ $1B, 거래대금 ≥ $10M/day, Common Stock + ADR
- GICS Sector(11개) 메인 + Industry Group(25개) 참조

실행: python 20260501_classification.py
입력: nasdaq_screener.csv (같은 폴더)
출력: 20260501_classification_master.xlsx, 20260501_sector_distribution.png
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATE_STR = datetime.now().strftime('%Y%m%d')

# 필터 기준
MIN_MARKET_CAP = 1_000_000_000       # $1B
MIN_AVG_DAILY_VALUE = 10_000_000     # $10M

# 입출력 파일
NASDAQ_CSV = os.path.join(SCRIPT_DIR, 'nasdaq_screener.csv')
OUTPUT_XLSX = os.path.join(SCRIPT_DIR, f'{DATE_STR}_classification_master.xlsx')
OUTPUT_CHART = os.path.join(SCRIPT_DIR, f'{DATE_STR}_sector_distribution.png')

# NASDAQ 섹터 → GICS 섹터 매핑
NASDAQ_TO_GICS = {
    'Technology':           'Information Technology',
    'Finance':              'Financials',
    'Health Care':          'Health Care',
    'Consumer Discretionary': 'Consumer Discretionary',
    'Consumer Staples':     'Consumer Staples',
    'Industrials':          'Industrials',
    'Energy':               'Energy',
    'Real Estate':          'Real Estate',
    'Utilities':            'Utilities',
    'Basic Materials':      'Materials',
    'Telecommunications':   'Communication Services',
    'Miscellaneous':        None,  # 수동 분류 필요
}

# ============================================================
# Step 1: NASDAQ CSV 로드 + 기본 전처리
# ============================================================
def load_nasdaq_csv():
    """NASDAQ Screener CSV 로드 및 전처리"""
    print("=" * 60)
    print("Step 1: NASDAQ CSV 로드")
    print("=" * 60)

    if not os.path.exists(NASDAQ_CSV):
        print(f"ERROR: {NASDAQ_CSV} 파일이 없습니다.")
        print("https://www.nasdaq.com/market-activity/stocks/screener 에서 다운로드하세요.")
        sys.exit(1)

    df = pd.read_csv(NASDAQ_CSV)
    print(f"원본: {len(df)} 종목")

    # Symbol 정규화: BRK/B → BRK-B (NASDAQ CSV는 /를 사용)
    df['Symbol'] = df['Symbol'].str.replace('/', '-', regex=False)

    # 가격 전처리 (Last Sale: "$115.55" → 115.55)
    df['price'] = pd.to_numeric(df['Last Sale'].str.replace('$', ''), errors='coerce')

    # 거래대금 계산
    df['avg_daily_value'] = df['Volume'] * df['price']

    # ADR 플래그
    df['is_adr'] = df['Country'] != 'United States'

    # GICS 섹터 매핑
    df['gics_sector'] = df['Sector'].map(NASDAQ_TO_GICS)

    print(f"가격 파싱 성공: {df['price'].notna().sum()}")
    print(f"Market Cap > 0: {(df['Market Cap'] > 0).sum()}")

    return df


# ============================================================
# Step 2: 필터링
# ============================================================
def apply_filters(df):
    """시총, 거래대금, 종목유형 필터 적용"""
    print("\n" + "=" * 60)
    print("Step 2: 필터링")
    print("=" * 60)

    total = len(df)

    # 2-1: Market Cap 결측/0 제거
    df = df[df['Market Cap'] > 0].copy()
    print(f"  Market Cap > 0: {len(df)} (제거: {total - len(df)})")

    # 2-2: 워런트/라이트/유닛 제거 (Symbol 패턴 + Name 키워드)
    before = len(df)
    # 워런트: Name에 "Warrant" 포함 OR 4글자 이상 심볼 끝이 WS/.WS
    warrant_mask = (
        df['Name'].str.contains('Warrant', na=False, case=False) |
        df['Symbol'].str.match(r'^.{3,}(\.WS|WS)$', na=False)
    )
    # 라이트: Name에 "Right" 포함 OR 4글자 이상 심볼 끝이 R/RT
    rights_mask = (
        df['Name'].str.contains(r'\bRights?\b', na=False, case=False) |
        df['Symbol'].str.match(r'^.{3,}(RT)$', na=False)
    )
    # 유닛: Name에 "Unit" 포함 (끝 단어로)
    unit_mask = df['Name'].str.contains(r'\bUnits?\b', na=False, case=False)
    df = df[~(warrant_mask | rights_mask | unit_mask)]
    print(f"  워런트/라이트/유닛 제거: {len(df)} (제거: {before - len(df)})")

    # 2-3: SPAC/Blank Check 제거
    before = len(df)
    df = df[df['Industry'] != 'Blank Checks']
    print(f"  SPAC/Blank Check 제거: {len(df)} (제거: {before - len(df)})")

    # 2-4: 시총 필터 ($1B)
    before = len(df)
    df = df[df['Market Cap'] >= MIN_MARKET_CAP]
    print(f"  시총 >= ${MIN_MARKET_CAP/1e9:.0f}B: {len(df)} (제거: {before - len(df)})")

    # 2-5: 거래대금 필터 ($10M/day)
    before = len(df)
    df = df[df['avg_daily_value'] >= MIN_AVG_DAILY_VALUE]
    print(f"  거래대금 >= ${MIN_AVG_DAILY_VALUE/1e6:.0f}M/day: {len(df)} (제거: {before - len(df)})")

    print(f"\n  ▶ 필터 통과: {len(df)} 종목 (원본 {total}에서 {total - len(df)} 제거)")

    return df


# ============================================================
# Step 3: FinanceDatabase GICS 매핑 보강
# ============================================================
def enrich_with_financedatabase(df):
    """FinanceDatabase에서 GICS sector, industry_group 매핑"""
    print("\n" + "=" * 60)
    print("Step 3: FinanceDatabase GICS 매핑")
    print("=" * 60)

    try:
        import financedatabase as fd

        equities = fd.Equities()
        all_eq = equities.select()
        print(f"FinanceDatabase 로드: {len(all_eq)} 종목")

        # 필요한 컬럼만 추출
        fd_cols = ['sector', 'industry_group', 'industry']
        fd_data = all_eq[fd_cols].copy()
        fd_data.index.name = 'Symbol'
        fd_data = fd_data.rename(columns={
            'sector': 'fd_sector',
            'industry_group': 'fd_industry_group',
            'industry': 'fd_industry',
        })

        # 조인
        before_cols = set(df.columns)
        df = df.merge(fd_data, left_on='Symbol', right_index=True, how='left')

        matched = df['fd_sector'].notna().sum()
        print(f"FinanceDatabase 매칭: {matched}/{len(df)} ({matched/len(df)*100:.1f}%)")

        # GICS 섹터 우선순위: FinanceDatabase > NASDAQ 매핑
        df['final_sector'] = df['fd_sector'].fillna(df['gics_sector'])
        df['final_industry_group'] = df['fd_industry_group']

        unmatched = df['final_sector'].isna().sum()
        print(f"최종 섹터 미분류: {unmatched}")

    except ImportError:
        print("WARNING: financedatabase 미설치. NASDAQ 섹터 매핑만 사용합니다.")
        print("  더 정확한 GICS 분류를 원하면: pip install financedatabase --user")
        df['fd_sector'] = None
        df['fd_industry_group'] = None
        df['fd_industry'] = None
        df['final_sector'] = df['gics_sector']
        df['final_industry_group'] = None

    except Exception as e:
        print(f"WARNING: FinanceDatabase 오류 ({e}). NASDAQ 섹터 매핑만 사용합니다.")
        df['fd_sector'] = None
        df['fd_industry_group'] = None
        df['fd_industry'] = None
        df['final_sector'] = df['gics_sector']
        df['final_industry_group'] = None

    return df


# ============================================================
# Step 4: 결과 출력
# ============================================================
def export_results(df):
    """Excel + 차트 출력"""
    print("\n" + "=" * 60)
    print("Step 4: 결과 출력")
    print("=" * 60)

    # --- Sheet1: 전체종목 ---
    master = df[[
        'Symbol', 'Name', 'final_sector', 'final_industry_group',
        'fd_industry', 'Market Cap', 'avg_daily_value', 'price',
        'Volume', 'Country', 'is_adr', 'Sector', 'Industry', 'IPO Year'
    ]].copy()

    master = master.rename(columns={
        'final_sector': 'GICS_Sector',
        'final_industry_group': 'GICS_Industry_Group',
        'fd_industry': 'GICS_Industry',
        'Market Cap': 'Market_Cap',
        'avg_daily_value': 'Avg_Daily_Value',
        'price': 'Price',
        'Sector': 'NASDAQ_Sector',
        'Industry': 'NASDAQ_Industry',
        'is_adr': 'Is_ADR',
        'IPO Year': 'IPO_Year',
    })

    # 시총 내림차순 정렬
    master = master.sort_values('Market_Cap', ascending=False).reset_index(drop=True)
    master.index += 1  # 1부터 시작
    master.index.name = 'Rank'

    # --- Sheet2: 섹터요약 ---
    sector_summary = master.groupby('GICS_Sector').agg(
        종목수=('Symbol', 'count'),
        평균시총=('Market_Cap', 'mean'),
        총시총=('Market_Cap', 'sum'),
        ADR수=('Is_ADR', 'sum'),
    ).sort_values('총시총', ascending=False)
    sector_summary['ADR비율'] = (sector_summary['ADR수'] / sector_summary['종목수'] * 100).round(1)
    sector_summary['시총비중'] = (sector_summary['총시총'] / sector_summary['총시총'].sum() * 100).round(1)

    # --- Sheet3: Industry Group 요약 ---
    ig_summary = None
    if master['GICS_Industry_Group'].notna().any():
        ig_summary = master[master['GICS_Industry_Group'].notna()].groupby(
            ['GICS_Sector', 'GICS_Industry_Group']
        ).agg(
            종목수=('Symbol', 'count'),
            평균시총=('Market_Cap', 'mean'),
        ).sort_values(['GICS_Sector', '종목수'], ascending=[True, False])

    # --- Sheet4: 미분류 ---
    unclassified = master[master['GICS_Sector'].isna()]

    # --- Sheet5: ADR ---
    adr_list = master[master['Is_ADR'] == True].copy()

    # --- Excel 출력 ---
    with pd.ExcelWriter(OUTPUT_XLSX, engine='openpyxl') as writer:
        master.to_excel(writer, sheet_name='전체종목')
        sector_summary.to_excel(writer, sheet_name='섹터요약')
        if ig_summary is not None and len(ig_summary) > 0:
            ig_summary.to_excel(writer, sheet_name='Industry_Group요약')
        if len(unclassified) > 0:
            unclassified.to_excel(writer, sheet_name='미분류')
        if len(adr_list) > 0:
            adr_list.to_excel(writer, sheet_name='ADR')

    print(f"Excel 저장: {OUTPUT_XLSX}")

    # --- 차트 ---
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # 차트1: 섹터별 종목 수
    sector_counts = sector_summary['종목수'].sort_values(ascending=True)
    colors = plt.cm.Set3(range(len(sector_counts)))
    sector_counts.plot(kind='barh', ax=axes[0], color=colors)
    axes[0].set_title('GICS Sector - Number of Stocks', fontsize=13, fontweight='bold')
    axes[0].set_xlabel('Count')
    for i, v in enumerate(sector_counts):
        axes[0].text(v + 5, i, str(v), va='center', fontsize=9)

    # 차트2: 섹터별 시총 비중
    sector_mcap = sector_summary['시총비중'].sort_values(ascending=False)
    axes[1].pie(sector_mcap, labels=sector_mcap.index, autopct='%1.1f%%',
                startangle=90, textprops={'fontsize': 8})
    axes[1].set_title('GICS Sector - Market Cap Weight', fontsize=13, fontweight='bold')

    plt.tight_layout()
    plt.savefig(OUTPUT_CHART, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"차트 저장: {OUTPUT_CHART}")

    # --- 콘솔 요약 ---
    print(f"\n{'='*60}")
    print(f"결과 요약")
    print(f"{'='*60}")
    print(f"총 종목 수: {len(master)}")
    print(f"  Common Stock: {(~master['Is_ADR']).sum()}")
    print(f"  ADR: {master['Is_ADR'].sum()}")
    print(f"  섹터 분류: {master['GICS_Sector'].notna().sum()}")
    print(f"  섹터 미분류: {master['GICS_Sector'].isna().sum()}")
    print(f"\n[섹터별 종목 수]")
    print(sector_summary[['종목수', '시총비중']].to_string())
    print(f"\n시총 범위: ${master['Market_Cap'].min()/1e9:.1f}B ~ ${master['Market_Cap'].max()/1e12:.1f}T")
    print(f"Top 10 종목:")
    print(master[['Symbol', 'Name', 'GICS_Sector', 'Market_Cap']].head(10).to_string())

    return master


# ============================================================
# Main
# ============================================================
def main():
    print(f"PHASE0 Global Classification")
    print(f"Date: {DATE_STR}")
    print(f"기준: 시총 >= ${MIN_MARKET_CAP/1e9:.0f}B, 거래대금 >= ${MIN_AVG_DAILY_VALUE/1e6:.0f}M/day")
    print()

    # Step 1: 로드
    df = load_nasdaq_csv()

    # Step 2: 필터링
    df = apply_filters(df)

    # Step 3: GICS 매핑 보강
    df = enrich_with_financedatabase(df)

    # Step 4: 출력
    master = export_results(df)

    print(f"\n완료!")
    return master


if __name__ == '__main__':
    main()
