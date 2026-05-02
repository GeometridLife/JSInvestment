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
BASE_DIR = os.path.dirname(SCRIPT_DIR)  # PHASE1_momentum/
TODAY = datetime.date.today()
TODAY_STR = TODAY.strftime('%Y%m%d')
YEAR_STR = TODAY.strftime('%Y')
MONTH_STR = TODAY.strftime('%m')

# 결과물: results/연/월/ 폴더
RESULTS_DIR = os.path.join(BASE_DIR, 'results', YEAR_STR, MONTH_STR)
os.makedirs(RESULTS_DIR, exist_ok=True)

# 백테스트 결과 파일 탐색 (results/연/월 우선 → 루트 폴백)
BACKTEST_CANDIDATES = sorted(glob.glob(os.path.join(RESULTS_DIR, '*_momentum_backtest.xlsx')))
if not BACKTEST_CANDIDATES:
    BACKTEST_CANDIDATES = sorted(glob.glob(os.path.join(BASE_DIR, '*_momentum_backtest.xlsx')))
if not BACKTEST_CANDIDATES:
    print("[ERROR] 백테스트 결과 파일을 찾을 수 없습니다. Step 2를 먼저 실행하세요.")
    sys.exit(1)
BACKTEST_EXCEL = BACKTEST_CANDIDATES[-1]

# 출력 (results/연/월 폴더에 저장)
OUTPUT_RANKING = os.path.join(RESULTS_DIR, f'{TODAY_STR}_momentum_ranking.xlsx')
CHART_DIR = os.path.join(RESULTS_DIR, f'{TODAY_STR}_ranking_charts')

# 마스터 테이블 (시총 정보)
PHASE0_DIR = os.path.join(os.path.dirname(BASE_DIR), 'PHASE0_classification')
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

        elif indicator in ('MACD', 'RSI', 'HIGH52', 'GC', 'BB'):
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
        elif indicator in ('MACD', 'RSI', 'HIGH52', 'GC', 'BB'):
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
        elif indicator in ('MACD', 'RSI', 'HIGH52', 'GC', 'BB'):
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
# 카테고리 가중 Rank Percentile 복합 스코어링
# ============================================================
# 카테고리 정의:
#   추세추종 (1/3): MACD, GC (골든크로스), HIGH52
#   역추세   (1/3): RSI, BB (볼린저)
#   리스크   (1/3): DD (Calmar Ratio)
CATEGORY_MAP = {
    'MACD':   '추세추종',
    'GC':     '추세추종',
    'HIGH52': '추세추종',
    'RSI':    '역추세',
    'BB':     '역추세',
    'DD':     '리스크',
}
CATEGORY_WEIGHT = {
    '추세추종': 1 / 3,
    '역추세':   1 / 3,
    '리스크':   1 / 3,
}


def composite_momentum(sheets):
    """카테고리 가중 Rank Percentile 기반 복합 스코어링 (Daily_3Y)"""
    target_suffix = 'Daily_3Y'

    # 1단계: 지표별 rank percentile 산출
    indicator_ranks = {}  # {indicator: DataFrame with ticker, rank_pct}

    for sheet_name, df in sheets.items():
        if not sheet_name.endswith(target_suffix) or len(df) == 0:
            continue

        indicator = sheet_name.split('_')[0]
        if indicator not in CATEGORY_MAP:
            continue

        if indicator == 'DD':
            rank_col = 'calmar_ratio'
            df_valid = df.dropna(subset=[rank_col]).copy()
            df_valid = df_valid[df_valid[rank_col] > 0]
        elif indicator in ('MACD', 'RSI', 'HIGH52', 'GC', 'BB'):
            rank_col = 'cum_return_pct'
            df_valid = df.dropna(subset=[rank_col]).copy()
        else:
            continue

        if len(df_valid) < 5:
            continue

        # rank_pct: 0~100 (100이 최고)
        df_valid['rank_pct'] = df_valid[rank_col].rank(pct=True) * 100
        indicator_ranks[indicator] = df_valid[['ticker', 'name', 'tier1', 'market', rank_col, 'rank_pct']].copy()
        indicator_ranks[indicator] = indicator_ranks[indicator].rename(columns={rank_col: f'{indicator}_raw'})

        print(f"  {indicator}: {len(df_valid)}종목 rank_pct 산출")

    if not indicator_ranks:
        return pd.DataFrame()

    # 2단계: 전 종목 통합 (outer join)
    all_tickers = set()
    ticker_info = {}
    for ind, df_r in indicator_ranks.items():
        for _, row in df_r.iterrows():
            tk = row['ticker']
            all_tickers.add(tk)
            if tk not in ticker_info:
                ticker_info[tk] = {
                    'ticker': tk,
                    'name': row['name'],
                    'tier1': row.get('tier1', ''),
                    'market': row.get('market', ''),
                }

    # 3단계: 종목별 카테고리 가중 점수 계산
    composite_rows = []
    for tk in all_tickers:
        info = ticker_info[tk]
        row = {**info}
        category_scores = {}  # {카테고리: [rank_pct values]}
        indicator_count = 0

        for ind, df_r in indicator_ranks.items():
            match = df_r[df_r['ticker'] == tk]
            if len(match) > 0:
                rp = match.iloc[0]['rank_pct']
                raw = match.iloc[0][f'{ind}_raw']
                row[f'{ind}_rank_pct'] = round(rp, 1)
                row[f'{ind}_raw'] = round(raw, 2)
                cat = CATEGORY_MAP[ind]
                if cat not in category_scores:
                    category_scores[cat] = []
                category_scores[cat].append(rp)
                indicator_count += 1
            else:
                row[f'{ind}_rank_pct'] = np.nan
                row[f'{ind}_raw'] = np.nan

        # 카테고리 내 평균 → 카테고리 가중 합산
        total_score = 0
        active_weight = 0
        for cat, weight in CATEGORY_WEIGHT.items():
            if cat in category_scores:
                cat_avg = np.mean(category_scores[cat])
                row[f'cat_{cat}'] = round(cat_avg, 1)
                total_score += weight * cat_avg
                active_weight += weight
            else:
                row[f'cat_{cat}'] = np.nan

        # 가중치 정규화 (일부 카테고리 없는 종목 대응)
        if active_weight > 0:
            row['composite_score'] = round(total_score / active_weight * (active_weight), 1)
        else:
            row['composite_score'] = 0

        row['n_indicators'] = indicator_count
        row['n_categories'] = len(category_scores)
        composite_rows.append(row)

    df_composite = pd.DataFrame(composite_rows)

    # 최소 2개 카테고리 + 3개 이상 지표에 랭크된 종목만
    df_composite = df_composite[
        (df_composite['n_categories'] >= 2) & (df_composite['n_indicators'] >= 3)
    ].copy()

    if len(df_composite) > 0:
        df_composite = df_composite.sort_values('composite_score', ascending=False)
        df_composite.insert(0, 'rank', range(1, len(df_composite) + 1))

    print(f"\n[랭킹] 복합 스코어 (카테고리 가중 Rank Percentile, {target_suffix}): {len(df_composite)}종목")
    print(f"  카테고리 가중치: {CATEGORY_WEIGHT}")
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

    # 복합 스코어 차트 (상위 40종목)
    if len(composite_ranking) > 0 and len(composite_ranking) >= 5:
        top_display = composite_ranking.head(40)
        fig, axes = plt.subplots(1, 2, figsize=(18, max(10, len(top_display) * 0.4)),
                                  gridspec_kw={'width_ratios': [2, 1]})

        # 왼쪽: Composite Score 바 차트
        ax1 = axes[0]
        y_pos = range(len(top_display))
        scores = top_display['composite_score'].values

        # 색상: 카테고리 수 기반
        colors = {2: '#3498db', 3: '#e67e22'}
        bar_colors = [colors.get(n, '#2ecc71') for n in top_display['n_categories'].values]

        ax1.barh(y_pos, scores, color=bar_colors)
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels([
            f"{r['name']} ({r['ticker']}) [{r['tier1']}]"
            for _, r in top_display.iterrows()
        ], fontsize=7)
        ax1.set_xlabel('Composite Score (카테고리 가중 Rank Percentile)')
        ax1.set_title('복합 모멘텀 스코어 Top 40\n(추세 1/3 + 역추세 1/3 + 리스크 1/3)',
                     fontsize=12, fontweight='bold')
        ax1.invert_yaxis()

        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#2ecc71', label='3개 카테고리'),
            Patch(facecolor='#e67e22', label='3개 카테고리 (일부)'),
            Patch(facecolor='#3498db', label='2개 카테고리'),
        ]
        ax1.legend(handles=legend_elements, loc='lower right', fontsize=8)

        # 오른쪽: 카테고리별 점수 히트맵
        ax2 = axes[1]
        cat_cols = [c for c in ['cat_추세추종', 'cat_역추세', 'cat_리스크'] if c in top_display.columns]
        if cat_cols:
            heatmap_data = top_display[cat_cols].values
            labels_y = [f"{r['name']}" for _, r in top_display.iterrows()]
            labels_x = ['추세추종', '역추세', '리스크']

            im = ax2.imshow(heatmap_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
            ax2.set_xticks(range(len(labels_x)))
            ax2.set_xticklabels(labels_x, fontsize=9)
            ax2.set_yticks(range(len(labels_y)))
            ax2.set_yticklabels(labels_y, fontsize=7)
            ax2.set_title('카테고리별 Rank Percentile', fontsize=11, fontweight='bold')

            # 셀 값 표시
            for i in range(len(labels_y)):
                for j in range(len(labels_x)):
                    val = heatmap_data[i, j]
                    if not np.isnan(val):
                        ax2.text(j, i, f'{val:.0f}', ha='center', va='center', fontsize=7,
                                color='white' if val < 30 or val > 80 else 'black')

            fig.colorbar(im, ax=ax2, shrink=0.5, label='Rank %')

        plt.tight_layout()
        plt.savefig(os.path.join(CHART_DIR, f'{TODAY_STR}_composite_score.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print(f"[출력] 복합 스코어 차트 저장")


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

    # 복합 스코어 요약
    if len(composite_ranking) > 0:
        print("\n[복합 스코어 Top 15] (카테고리 가중 Rank Percentile)")
        print(f"  {'순위':>4}  {'종목명':<12}  {'섹터':<16}  {'점수':>6}  {'지표수':>4}  {'카테고리':>6}")
        print("  " + "-" * 70)
        for _, row in composite_ranking.head(15).iterrows():
            print(f"  {row['rank']:>4}  {row['name']:<12}  {row['tier1']:<16}  "
                  f"{row['composite_score']:>6.1f}  {row['n_indicators']:>4}  {row['n_categories']:>6}")
    print("=" * 60)


if __name__ == '__main__':
    main()
