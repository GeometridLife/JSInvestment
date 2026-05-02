"""
PHASE0: 한국 주식 섹터 분류 마스터 테이블 구축
Date: 2026-04-27
Description:
    - FinanceDataReader로 KOSPI/KOSDAQ 전종목 수집
    - 시총 1,000억↑ & 일평균 거래대금 10억↑ (20일 OR 60일) 필터링
    - WICS 섹터 분류 조인 (tier1 18개, 특수목적법인 제외)
    - Excel 마스터 테이블 + 섹터 요약 + 차트 출력
"""

import os
import re
import time
import datetime
import warnings
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import FinanceDataReader as fdr

warnings.filterwarnings('ignore')
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TODAY_STR = datetime.date.today().strftime('%Y%m%d')
WICS_CSV = os.path.join(SCRIPT_DIR, 'kospi_kosdaq_sector_classification.csv')
OUTPUT_EXCEL = os.path.join(SCRIPT_DIR, f'{TODAY_STR}_classification_master.xlsx')
OUTPUT_CHART = os.path.join(SCRIPT_DIR, f'{TODAY_STR}_sector_distribution.png')

MARKETCAP_THRESHOLD = 1000_0000_0000       # 1,000억 원
TRADING_VALUE_THRESHOLD = 10_0000_0000     # 10억 원
TRADING_DAYS_SHORT = 20
TRADING_DAYS_LONG = 60


# ============================================================
# Step 1: 전종목 수집 + 시총 필터링
# ============================================================
def collect_and_filter_by_marketcap():
    """
    FDR StockListing으로 KOSPI/KOSDAQ 전종목 수집 + 시총 필터
    StockListing 결과에 시가총액(Marcap)이 포함되어 있음
    """
    records = []
    for market in ['KOSPI', 'KOSDAQ']:
        df = fdr.StockListing(market)
        print(f"[Step 1] {market}: {len(df)}종목 수집, 컬럼: {list(df.columns)}")
        df['market'] = market
        records.append(df)
        time.sleep(1)

    df_all = pd.concat(records, ignore_index=True)

    # FDR 컬럼명 정규화 (버전에 따라 다를 수 있음)
    # 일반적: Code, Name, Market, Marcap, ...
    # 또는: Symbol, Name, Market, MarketCap, ...
    col_map = {}
    for col in df_all.columns:
        cl = col.lower().strip()
        if cl in ('code', 'symbol', 'ticker', 'isu_srt_cd'):
            col_map[col] = 'ticker'
        elif cl in ('name', 'isu_abbrv', 'stockname'):
            col_map[col] = 'name'
        elif cl in ('marcap', 'marketcap', 'market_cap', '시가총액'):
            col_map[col] = '시가총액'
        elif cl in ('volume', '거래량'):
            col_map[col] = '거래량'
        elif cl in ('amount', '거래대금'):
            col_map[col] = '거래대금'

    df_all = df_all.rename(columns=col_map)

    # market 컬럼이 위에서 덮어씌워질 수 있으니 확인
    if 'market' not in df_all.columns:
        # records에서 다시 합치기
        pass

    print(f"[Step 1] 전체 종목: {len(df_all)}")
    print(f"  사용 가능 컬럼: {list(df_all.columns)}")

    # 시총 필터
    if '시가총액' in df_all.columns:
        before = len(df_all)
        df_all['시가총액'] = pd.to_numeric(df_all['시가총액'], errors='coerce').fillna(0)
        df_filtered = df_all[df_all['시가총액'] >= MARKETCAP_THRESHOLD].copy()
        print(f"[Step 2-1] 시총 필터: {before} → {len(df_filtered)}종목 (≥ {MARKETCAP_THRESHOLD/1e8:.0f}억)")
    else:
        print("[WARNING] 시가총액 컬럼을 찾을 수 없습니다. 필터 없이 진행합니다.")
        df_filtered = df_all.copy()

    return df_filtered


# ============================================================
# Step 2: 거래대금 필터링
# ============================================================
def filter_by_trading_value(df_filtered):
    """
    일평균 거래대금 필터링 (20일 OR 60일 중 하나라도 10억↑이면 통과)
    FDR DataReader로 개별 종목 OHLCV에서 거래대금(Volume*Close 근사) 수집
    """
    today = datetime.date.today()
    end_str = today.strftime('%Y-%m-%d')
    start_60 = (today - datetime.timedelta(days=120)).strftime('%Y-%m-%d')  # 넉넉하게

    tickers = df_filtered['ticker'].tolist()
    total = len(tickers)
    avg_20_list = []
    avg_60_list = []

    print(f"[Step 2-2] {total}종목 거래대금 수집 시작...")

    for i, t in enumerate(tickers):
        try:
            df_price = fdr.DataReader(t, start_60, end_str)

            if df_price is None or len(df_price) == 0:
                avg_20_list.append(0)
                avg_60_list.append(0)
                continue

            # 거래대금 산출: FDR에 'Amount' 컬럼이 있으면 사용, 없으면 Close * Volume 근사
            if 'Amount' in df_price.columns:
                trading_val = df_price['Amount']
            elif 'Close' in df_price.columns and 'Volume' in df_price.columns:
                trading_val = df_price['Close'] * df_price['Volume']
            else:
                avg_20_list.append(0)
                avg_60_list.append(0)
                continue

            # 최근 20일, 60일 평균
            avg_60 = trading_val.tail(TRADING_DAYS_LONG).mean()
            avg_20 = trading_val.tail(TRADING_DAYS_SHORT).mean()

            avg_20_list.append(avg_20 if pd.notna(avg_20) else 0)
            avg_60_list.append(avg_60 if pd.notna(avg_60) else 0)

        except Exception as e:
            avg_20_list.append(0)
            avg_60_list.append(0)

        # 진행률 표시
        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{total}] 처리 중...")
            time.sleep(0.5)  # API rate limit 방지

    df_filtered = df_filtered.copy()
    df_filtered['일평균거래대금_20d'] = avg_20_list
    df_filtered['일평균거래대금_60d'] = avg_60_list

    before = len(df_filtered)
    mask = (
        (df_filtered['일평균거래대금_20d'] >= TRADING_VALUE_THRESHOLD) |
        (df_filtered['일평균거래대금_60d'] >= TRADING_VALUE_THRESHOLD)
    )
    df_result = df_filtered[mask].copy()
    print(f"[Step 2-2] 거래대금 필터: {before} → {len(df_result)}종목 (≥ {TRADING_VALUE_THRESHOLD/1e8:.0f}억, 20d OR 60d)")

    return df_result


# ============================================================
# Step 3: WICS 섹터 조인
# ============================================================
def load_wics(csv_path):
    """WICS CSV 로드, 특수목적법인 제외, 이름 정규화"""
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    df = df[df['tier1'] != '특수목적법인'].copy()
    df['name_clean'] = df['name'].astype(str).str.strip().str.replace(r'\s+', '', regex=True)
    print(f"[Step 3] WICS 로드: {len(df)}종목 (특수목적법인 제외)")
    return df


def normalize_name(name):
    """종목명 정규화: 공백 제거"""
    if pd.isna(name):
        return ''
    return re.sub(r'\s+', '', str(name).strip())


def extract_common_name(name):
    """우선주명에서 보통주명 추출: '삼성전자우' → '삼성전자'"""
    clean = normalize_name(name)
    return re.sub(r'[0-9]*우[A-Z]?$', '', clean)


def join_wics_sectors(df_filtered, df_wics):
    """
    pykrx 종목 ↔ WICS 섹터 조인
    1차: ticker 기반 매칭 (WICS에 ticker가 있는 경우)
    2차: 이름 완전 일치
    3차: 우선주 → 보통주명으로 재매칭
    """
    df = df_filtered.copy()
    df['name_clean'] = df['name'].apply(normalize_name)

    # ticker 정규화 (6자리 맞추기)
    df['ticker_clean'] = df['ticker'].astype(str).str.strip().str.zfill(6)

    # WICS ticker 정규화
    df_wics = df_wics.copy()
    df_wics['ticker_clean'] = df_wics['ticker'].astype(str).str.strip().str.zfill(6)

    # --- 1차: ticker 기반 매칭 ---
    wics_ticker_dict = {}
    for _, row in df_wics.iterrows():
        tk = row['ticker_clean']
        if tk and tk != '000000' and tk != 'nan':
            wics_ticker_dict[tk] = (row['tier1'], row['tier2'], row['tier3'])

    # --- 2차 준비: 이름 기반 매칭 ---
    wics_name_dict = {}
    for _, row in df_wics.iterrows():
        key = row['name_clean']
        wics_name_dict[key] = (row['tier1'], row['tier2'], row['tier3'])

    matched_t1, matched_t2, matched_t3, match_status = [], [], [], []

    for _, row in df.iterrows():
        tk = row['ticker_clean']
        nm = row['name_clean']

        # 1차: ticker
        if tk in wics_ticker_dict:
            t1, t2, t3 = wics_ticker_dict[tk]
            matched_t1.append(t1); matched_t2.append(t2); matched_t3.append(t3)
            match_status.append('ticker_match')
        # 2차: 이름
        elif nm in wics_name_dict:
            t1, t2, t3 = wics_name_dict[nm]
            matched_t1.append(t1); matched_t2.append(t2); matched_t3.append(t3)
            match_status.append('name_match')
        else:
            matched_t1.append(None); matched_t2.append(None); matched_t3.append(None)
            match_status.append('unmatched')

    df['tier1'] = matched_t1
    df['tier2'] = matched_t2
    df['tier3'] = matched_t3
    df['match_status'] = match_status

    matched_count = (df['match_status'] != 'unmatched').sum()
    unmatched_count = (df['match_status'] == 'unmatched').sum()
    print(f"[Step 3] 1~2차 매칭: {matched_count}건 성공, {unmatched_count}건 미매칭")

    # --- 3차: 우선주 → 보통주 ---
    if unmatched_count > 0:
        rematched = 0
        for idx in df[df['match_status'] == 'unmatched'].index:
            common_name = extract_common_name(df.at[idx, 'name'])
            if common_name != df.at[idx, 'name_clean'] and common_name in wics_name_dict:
                t1, t2, t3 = wics_name_dict[common_name]
                df.at[idx, 'tier1'] = t1
                df.at[idx, 'tier2'] = t2
                df.at[idx, 'tier3'] = t3
                df.at[idx, 'match_status'] = 'preferred_stock'
                rematched += 1

        unmatched_final = (df['match_status'] == 'unmatched').sum()
        print(f"[Step 3] 3차 우선주 매칭: +{rematched}건, 최종 미분류: {unmatched_final}건")

    # 미분류 종목 태그
    df.loc[df['match_status'] == 'unmatched', 'tier1'] = '미분류'
    df.loc[df['match_status'] == 'unmatched', 'tier2'] = '미분류'
    df.loc[df['match_status'] == 'unmatched', 'tier3'] = '미분류'

    # 미분류 종목 상세 출력
    df_unmatched = df[df['tier1'] == '미분류']
    if len(df_unmatched) > 0:
        print(f"\n[미분류 종목 상세]")
        for _, row in df_unmatched.iterrows():
            print(f"  {row['ticker']} {row['name']} ({row['market']})")

    return df


# ============================================================
# Step 4: 결과물 출력
# ============================================================
def generate_output(df_master):
    """Excel 마스터 테이블 + 섹터 요약 + 차트 생성"""

    output_cols = ['ticker', 'name', 'market', 'tier1', 'tier2', 'tier3',
                   '시가총액', '일평균거래대금_20d', '일평균거래대금_60d', 'match_status']

    # 존재하는 컬럼만 선택
    available_cols = [c for c in output_cols if c in df_master.columns]
    df_out = df_master[available_cols].sort_values(
        ['tier1', '시가총액'] if '시가총액' in df_master.columns else ['tier1'],
        ascending=[True, False] if '시가총액' in df_master.columns else [True]
    )

    # 억 단위 변환
    if '시가총액' in df_out.columns:
        df_out['시가총액(억)'] = (df_out['시가총액'] / 1e8).round(0).astype(int)
    if '일평균거래대금_20d' in df_out.columns:
        df_out['일평균거래대금_20d(억)'] = (df_out['일평균거래대금_20d'] / 1e8).round(1)
    if '일평균거래대금_60d' in df_out.columns:
        df_out['일평균거래대금_60d(억)'] = (df_out['일평균거래대금_60d'] / 1e8).round(1)

    # 섹터 요약
    agg_dict = {'ticker': 'count'}
    if '시가총액(억)' in df_out.columns:
        agg_dict['시가총액(억)'] = ['mean', 'sum']
    if '일평균거래대금_20d(억)' in df_out.columns:
        agg_dict['일평균거래대금_20d(억)'] = 'mean'

    sector_summary = df_out.groupby('tier1').agg(
        종목수=('ticker', 'count'),
        **({'평균시총_억': ('시가총액(억)', 'mean'),
            '총시총_억': ('시가총액(억)', 'sum')} if '시가총액(억)' in df_out.columns else {}),
        **({'평균거래대금_20d_억': ('일평균거래대금_20d(억)', 'mean')} if '일평균거래대금_20d(억)' in df_out.columns else {}),
    ).round(0).sort_values('종목수', ascending=False)

    # 미분류 목록
    df_unmatched = df_out[df_out.get('match_status', pd.Series()) == 'unmatched']
    if 'match_status' in df_out.columns:
        df_unmatched = df_out[df_out['match_status'] == 'unmatched'][
            [c for c in ['ticker', 'name', 'market', '시가총액(억)'] if c in df_out.columns]
        ]

    # Excel 저장
    with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
        df_out.to_excel(writer, sheet_name='전체종목', index=False)
        sector_summary.to_excel(writer, sheet_name='섹터요약')
        if len(df_unmatched) > 0:
            df_unmatched.to_excel(writer, sheet_name='미분류', index=False)

    print(f"\n[Step 4] Excel 저장: {OUTPUT_EXCEL}")
    print(f"  - 전체종목: {len(df_out)}건")
    print(f"  - 섹터: {len(sector_summary)}개")
    print(f"  - 미분류: {len(df_unmatched)}건")

    # 차트: 섹터별 종목 수
    fig, ax = plt.subplots(figsize=(14, 8))
    sector_plot = sector_summary.sort_values('종목수', ascending=True)
    # 미분류는 회색, 나머지는 컬러
    colors = []
    for s in sector_plot.index:
        if s == '미분류':
            colors.append('#CCCCCC')
        else:
            colors.append(plt.cm.Set3(len(colors) % 12))

    bars = ax.barh(sector_plot.index, sector_plot['종목수'], color=colors)

    ax.set_xlabel('종목 수', fontsize=12)
    ax.set_title('PHASE0: WICS tier1 섹터별 종목 분포\n'
                 '(시총 ≥ 1,000억 & 일평균 거래대금 ≥ 10억, 20d OR 60d)',
                 fontsize=14, fontweight='bold')

    for bar, val in zip(bars, sector_plot['종목수']):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                str(int(val)), ha='left', va='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(OUTPUT_CHART, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[Step 4] 차트 저장: {OUTPUT_CHART}")

    return df_out, sector_summary


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 60)
    print("PHASE0: 한국 주식 섹터 분류 마스터 테이블 구축")
    print(f"실행 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1 + 2-1: 전종목 수집 & 시총 필터
    df_filtered = collect_and_filter_by_marketcap()

    # Step 2-2: 거래대금 필터
    df_filtered = filter_by_trading_value(df_filtered)

    # Step 3: WICS 섹터 조인
    df_wics = load_wics(WICS_CSV)
    df_master = join_wics_sectors(df_filtered, df_wics)

    # Step 4: 출력
    df_out, sector_summary = generate_output(df_master)

    # 콘솔 요약
    print("\n" + "=" * 60)
    print("섹터 요약")
    print("=" * 60)
    print(sector_summary.to_string())
    print(f"\n총 {len(df_out)}종목, {len(sector_summary)}섹터")
    print("=" * 60)


if __name__ == '__main__':
    main()
