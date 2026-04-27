"""
PHASE1 Momentum - Step 3: 랭킹 산출
Date: 2026-04-27
Description:
    - 백테스트 결과 로드
    - 지표별 Top 20, 섹터별 Top 3, 복합 모멘텀 산출
    - 최종 랭킹 Excel 출력
"""

import os
import sys
import glob
import datetime
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

warnings.filterwarnings('ignore')
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TODAY_STR = datetime.date.today().strftime('%Y%m%d')

# 백테스트 결과 파일 탐색
BACKTEST_CANDIDATES = sorted(glob.glob(os.path.join(SCRIPT_DIR, '*_momentum_backtest.xlsx')))
if not BACKTEST_CANDIDATES:
    print("[ERROR] 백테스트 결과 파일을 찾을 수 없습니다. Step 2를 먼저 실행하세요.")
    sys.exit(1)
BACKTEST_EXCEL = BACKTEST_CANDIDATES[-1]

# 출력
OUTPUT_RANKING = os.path.join(SCRIPT_DIR, f'{TODAY_STR}_momentum_ranking.xlsx')
CHART_DIR = os.path.join(SCRIPT_DIR, f'{TODAY_STR}_ranking_charts')

# 마스터 테이블 (시총 정보)
PHASE0_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'PHASE0_classification')
MASTER_CANDIDATES = sorted(glob.glob(os.path.join(PHASE0_DIR, '*_classification_master_verified.xlsx')))
MASTER_EXCEL = MASTER_CANDIDATES[-1] if MASTER_CANDIDATES else None

# 랭킹 설정
TOP_N = 20
SECTOR_TOP_N = 3
COMPOSITE_TOP_N = 50

# 시총 구간 (억 단위)
MCAP_TIERS = {
    '대형 (5조+)': 50000,
    '중형 (1조~5조)': 10000,
    '소형 (1000억~1조)': 0,
}


# ============================================================
# 데이터 로드
# ============================================================
def load_mcap_map():
    """마스터 테이블에서 시총 정보 로드 → {ticker: 시총(억)}"""
    if not MASTER_EXCEL:
        print("[WARNING] 마스터 테이블 없음, 시총 구간 랭킹 스킵")
        return {}
    df = pd.read_excel(MASTER_EXCEL, sheet_name='전체종목')
    mcap_map = {}
    for _, row in df.iterrows():
        tk = str(row['ticker']).strip().zfill(6)
        if '시가총액(억)' in df.columns:
            mcap_map[tk] = row['시가총액(억)']
        elif '시가총액' in df.columns:
            mcap_map[tk] = row['시가총액'] / 1e8
    print(f"[로드] 시총 정보: {len(mcap_map)}종목")
    return mcap_map


def assign_mcap_tier(mcap_억):
    """시총(억)에 따라 대형/중형/소형 구간 배정"""
    if mcap_억 >= 50000:
        return '대형 (5조+)'
    elif mcap_억 >= 10000:
        return '중형 (1조~5조)'
    else:
        return '소형 (1000억~1조)'


def load_backtest_results():
    """백테스트 Excel에서 모든 시트 로드"""
    print(f"[로드] {os.path.basename(BACKTEST_EXCEL)}")
    xls = pd.ExcelFile(BACKTEST_EXCEL)
    sheets = {}
    for name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=name)
        sheets[name] = df
        print(f"  {name}: {len(df)}종목")
    return sheets


# ============================================================
# 지표별 Top N
# ============================================================
def rank_by_indicator(sheets):
    """각 지표별 Top 20 산출"""
    rankings = {}

    for sheet_name, df in sheets.items():
        if len(df) == 0:
            continue

        indicator = sheet_name.split('_')[0]

        if indicator == 'DD':
            # DD: Calmar Ratio 기준 (높을수록 좋음)
            if 'calmar_ratio' not in df.columns:
                continue
            df_valid = df.dropna(subset=['calmar_ratio'])
            df_valid = df_valid[df_valid['calmar_ratio'] > 0]  # 양수만
            top = df_valid.nlargest(TOP_N, 'calmar_ratio')
            rank_col = 'calmar_ratio'

            # 추가: Forward MDD가 낮은 Top 20 (하방 리스크 낮은 종목)
            if 'forward_mdd_median' in df.columns:
                df_fmdd = df.dropna(subset=['forward_mdd_median'])
                top_low_risk = df_fmdd.nsmallest(TOP_N, 'forward_mdd_median')
                rankings[f'{sheet_name}_LowRisk'] = top_low_risk

        elif indicator in ('MACD', 'RSI', 'HIGH52'):
            # 누적수익률 기준
            if 'cum_return_pct' not in df.columns:
                continue
            df_valid = df.dropna(subset=['cum_return_pct'])
            top = df_valid.nlargest(TOP_N, 'cum_return_pct')
            rank_col = 'cum_return_pct'
        else:
            continue

        top = top.copy()
        top.insert(0, 'rank', range(1, len(top) + 1))
        rankings[sheet_name] = top

    print(f"\n[랭킹] 지표별 Top {TOP_N}: {len(rankings)}개 시트 생성")
    return rankings


# ============================================================
# 섹터별 Top N
# ============================================================
def rank_by_sector(sheets):
    """18개 섹터 × 지표별 Top 3"""
    sector_rankings = []

    for sheet_name, df in sheets.items():
        if len(df) == 0:
            continue

        indicator = sheet_name.split('_')[0]

        if indicator == 'DD':
            rank_col = 'calmar_ratio'
            ascending = False
        elif indicator in ('MACD', 'RSI', 'HIGH52'):
            rank_col = 'cum_return_pct'
            ascending = False
        else:
            continue

        if rank_col not in df.columns or 'tier1' not in df.columns:
            continue

        df_valid = df.dropna(subset=[rank_col])
        if indicator == 'DD':
            df_valid = df_valid[df_valid[rank_col] > 0]

        for sector in df_valid['tier1'].unique():
            if sector == '미분류':
                continue
            sector_df = df_valid[df_valid['tier1'] == sector]
            top = sector_df.nlargest(SECTOR_TOP_N, rank_col)

            for rank_num, (_, row) in enumerate(top.iterrows(), 1):
                sector_rankings.append({
                    'sheet': sheet_name,
                    'indicator': indicator,
                    'sector': sector,
                    'rank': rank_num,
                    'ticker': row['ticker'],
                    'name': row['name'],
                    rank_col: row[rank_col],
                })

    df_sector = pd.DataFrame(sector_rankings)
    print(f"[랭킹] 섹터별 Top {SECTOR_TOP_N}: {len(df_sector)}건")
    return df_sector


# ============================================================
# 시총 구간별 Top N
# ============================================================
def rank_by_mcap_tier(sheets, mcap_map):
    """대형/중형/소형 구간별 × 지표별 Top 10"""
    if not mcap_map:
        return pd.DataFrame()

    # Daily_3Y 기준
    target_suffix = 'Daily_3Y'
    tier_rankings = []

    for sheet_name, df in sheets.items():
        if not sheet_name.endswith(target_suffix) or len(df) == 0:
            continue

        indicator = sheet_name.split('_')[0]

        if indicator == 'DD':
            rank_col = 'calmar_ratio'
        elif indicator in ('MACD', 'RSI', 'HIGH52'):
            rank_col = 'cum_return_pct'
        else:
            continue

        if rank_col not in df.columns:
            continue

        df_valid = df.dropna(subset=[rank_col]).copy()
        if indicator == 'DD':
            df_valid = df_valid[df_valid[rank_col] > 0]

        # sufficient 필터
        if 'sufficient' in df_valid.columns:
            df_valid = df_valid[df_valid['sufficient'] == True]

        # 시총 구간 배정
        df_valid['ticker_clean'] = df_valid['ticker'].astype(str).str.strip().str.zfill(6)
        df_valid['시총_억'] = df_valid['ticker_clean'].map(mcap_map).fillna(0)
        df_valid['mcap_tier'] = df_valid['시총_억'].apply(assign_mcap_tier)

        for tier_name in MCAP_TIERS.keys():
            tier_df = df_valid[df_valid['mcap_tier'] == tier_name]
            top = tier_df.nlargest(10, rank_col)

            for rank_num, (_, row) in enumerate(top.iterrows(), 1):
                tier_rankings.append({
                    'indicator': indicator,
                    'mcap_tier': tier_name,
                    'rank': rank_num,
                    'ticker': row['ticker'],
                    'name': row['name'],
                    'tier1': row.get('tier1', ''),
                    '시총_억': int(row['시총_억']),
                    rank_col: row[rank_col],
                })

    df_mcap = pd.DataFrame(tier_rankings)
    if len(df_mcap) > 0:
        print(f"[랭킹] 시총 구간별 Top 10 (Daily_3Y): {len(df_mcap)}건")
        for tier in MCAP_TIERS.keys():
            count = len(df_mcap[df_mcap['mcap_tier'] == tier])
            print(f"  {tier}: {count}건")
    return df_mcap


# ============================================================
# 복합 모멘텀
# ============================================================
def composite_momentum(sheets):
    """4개 지표 중 2개 이상에서 Top 50에 드는 종목"""
    # Daily_3Y 기준으로 복합 랭킹 (가장 대표적인 기간)
    target_suffix = 'Daily_3Y'

    ticker_scores = {}  # {ticker: {name, tier1, indicators: set}}

    for sheet_name, df in sheets.items():
        if not sheet_name.endswith(target_suffix):
            continue
        if len(df) == 0:
            continue

        indicator = sheet_name.split('_')[0]

        if indicator == 'DD':
            rank_col = 'calmar_ratio'
            df_valid = df.dropna(subset=[rank_col])
            df_valid = df_valid[df_valid[rank_col] > 0]
            top50 = df_valid.nlargest(COMPOSITE_TOP_N, rank_col)
        elif indicator in ('MACD', 'RSI', 'HIGH52'):
            rank_col = 'cum_return_pct'
            df_valid = df.dropna(subset=[rank_col])
            top50 = df_valid.nlargest(COMPOSITE_TOP_N, rank_col)
        else:
            continue

        for _, row in top50.iterrows():
            tk = row['ticker']
            if tk not in ticker_scores:
                ticker_scores[tk] = {
                    'ticker': tk,
                    'name': row['name'],
                    'tier1': row.get('tier1', ''),
                    'market': row.get('market', ''),
                    'indicators': set(),
                    'details': {},
                }
            ticker_scores[tk]['indicators'].add(indicator)
            ticker_scores[tk]['details'][f'{indicator}_score'] = row[rank_col]

    # 2개 이상 지표에서 Top 50에 든 종목
    composite = []
    for tk, info in ticker_scores.items():
        if len(info['indicators']) >= 2:
            row = {
                'ticker': info['ticker'],
                'name': info['name'],
                'tier1': info['tier1'],
                'market': info['market'],
                'n_indicators': len(info['indicators']),
                'indicators': ', '.join(sorted(info['indicators'])),
            }
            row.update(info['details'])
            composite.append(row)

    df_composite = pd.DataFrame(composite)
    if len(df_composite) > 0:
        df_composite = df_composite.sort_values('n_indicators', ascending=False)
        df_composite.insert(0, 'rank', range(1, len(df_composite) + 1))

    print(f"[랭킹] 복합 모멘텀 (≥2 지표, {target_suffix}): {len(df_composite)}종목")
    return df_composite


# ============================================================
# 출력
# ============================================================
def save_rankings(indicator_rankings, sector_ranking, composite_ranking, mcap_ranking):
    """Excel 저장"""
    os.makedirs(CHART_DIR, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_RANKING, engine='openpyxl') as writer:
        # 지표별 Top 20
        for sheet_name, df in sorted(indicator_rankings.items()):
            short = sheet_name[:31]
            df.to_excel(writer, sheet_name=short, index=False)

        # 섹터별
        if len(sector_ranking) > 0:
            sector_ranking.to_excel(writer, sheet_name='Sector_Top3', index=False)

        # 시총 구간별
        if len(mcap_ranking) > 0:
            mcap_ranking.to_excel(writer, sheet_name='MCap_Tier_Top10', index=False)

        # 복합
        if len(composite_ranking) > 0:
            composite_ranking.to_excel(writer, sheet_name='Composite_Momentum', index=False)

    print(f"\n[출력] 랭킹 결과: {os.path.basename(OUTPUT_RANKING)}")

    # 복합 모멘텀 차트
    if len(composite_ranking) > 0 and len(composite_ranking) >= 5:
        fig, ax = plt.subplots(figsize=(14, max(8, len(composite_ranking) * 0.4)))

        y_pos = range(len(composite_ranking))
        colors = {2: '#3498db', 3: '#2ecc71', 4: '#e74c3c'}
        bar_colors = [colors.get(n, '#95a5a6') for n in composite_ranking['n_indicators'].values]

        ax.barh(y_pos, composite_ranking['n_indicators'].values, color=bar_colors)
        ax.set_yticks(y_pos)
        ax.set_yticklabels([
            f"{r['name']} ({r['ticker']}) [{r['tier1']}]"
            for _, r in composite_ranking.iterrows()
        ], fontsize=8)
        ax.set_xlabel('지표 수')
        ax.set_title(f'복합 모멘텀: 2개 이상 지표에서 Top {COMPOSITE_TOP_N}에 진입한 종목\n(Daily 3Y 기준)',
                     fontsize=13, fontweight='bold')
        ax.invert_yaxis()

        # 범례
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#e74c3c', label='4개 지표'),
            Patch(facecolor='#2ecc71', label='3개 지표'),
            Patch(facecolor='#3498db', label='2개 지표'),
        ]
        ax.legend(handles=legend_elements, loc='lower right')

        plt.tight_layout()
        plt.savefig(os.path.join(CHART_DIR, f'{TODAY_STR}_composite_momentum.png'), dpi=150)
        plt.close()
        print(f"[출력] 복합 모멘텀 차트 저장")


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 60)
    print("PHASE1 Momentum - Step 3: 랭킹")
    print(f"실행 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    sheets = load_backtest_results()
    mcap_map = load_mcap_map()

    # 지표별 Top 20
    indicator_rankings = rank_by_indicator(sheets)

    # 섹터별 Top 3
    sector_ranking = rank_by_sector(sheets)

    # 시총 구간별 Top 10
    mcap_ranking = rank_by_mcap_tier(sheets, mcap_map)

    # 복합 모멘텀
    composite_ranking = composite_momentum(sheets)

    # 저장
    save_rankings(indicator_rankings, sector_ranking, composite_ranking, mcap_ranking)

    # 요약
    print("\n" + "=" * 60)
    print("랭킹 요약")
    print("=" * 60)

    # 시총 구간별 요약
    if len(mcap_ranking) > 0:
        print("\n[시총 구간별 Top 종목 (Daily_3Y)]")
        for tier in MCAP_TIERS.keys():
            tier_df = mcap_ranking[mcap_ranking['mcap_tier'] == tier]
            if len(tier_df) == 0:
                continue
            print(f"\n  === {tier} ===")
            for indicator in tier_df['indicator'].unique():
                ind_df = tier_df[tier_df['indicator'] == indicator].head(3)
                names = ', '.join([f"{r['name']}({r['시총_억']:,}억)" for _, r in ind_df.iterrows()])
                print(f"    {indicator}: {names}")

    # 복합 모멘텀 요약
    if len(composite_ranking) > 0:
        print("\n[복합 모멘텀]")
        for n_ind in sorted(composite_ranking['n_indicators'].unique(), reverse=True):
            subset = composite_ranking[composite_ranking['n_indicators'] == n_ind]
            print(f"\n  [{n_ind}개 지표 충족] {len(subset)}종목:")
            for _, row in subset.iterrows():
                print(f"    {row['name']} ({row['ticker']}) - {row['tier1']} - {row['indicators']}")
    print("=" * 60)


if __name__ == '__main__':
    main()
