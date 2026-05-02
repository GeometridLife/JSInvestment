"""
PHASE1 Global Momentum - Step 3: 랭킹 및 차트
- 종목 선별: 지표별 Top 20 (4장)
- 섹터 선별: 섹터별 Top 3 (4장)
- 복합 모멘텀: 2개+ 지표 Top 50 교집합 (1장)
- 총 9장 차트

실행: python 20260501_momentum_ranking.py
입력: results/{날짜}_momentum_backtest.xlsx
출력: results/{날짜}_momentum_ranking.xlsx
      charts/{날짜}_*.png (9장)
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATE_STR = datetime.now().strftime('%Y%m%d')

RESULTS_DIR = os.path.join(SCRIPT_DIR, 'results')
CHARTS_DIR = os.path.join(SCRIPT_DIR, 'charts')
os.makedirs(CHARTS_DIR, exist_ok=True)

# 기본 기간/프레임 (랭킹 기준)
DEFAULT_PERIOD = '1Y'
DEFAULT_FRAME = 'Daily'
HIGH52_PERIOD = '3Y'  # HIGH52는 250일 윈도우 필요 → 1Y 부족, 3Y 사용

# 랭킹 설정
TOP_N_STOCKS = 20      # 종목 선별
TOP_N_SECTOR = 3       # 섹터 선별
TOP_N_COMPOSITE = 50   # 복합 모멘텀 기준


# ============================================================
# 백테스트 결과 로드
# ============================================================
def load_backtest():
    """최신 백테스트 결과 로드"""
    xlsx_files = sorted([f for f in os.listdir(RESULTS_DIR) if f.endswith('_momentum_backtest.xlsx')])
    if not xlsx_files:
        print("ERROR: 백테스트 결과 없음. momentum_backtest.py를 먼저 실행하세요.")
        sys.exit(1)

    xlsx_path = os.path.join(RESULTS_DIR, xlsx_files[-1])
    print(f"백테스트 결과: {xlsx_files[-1]}")

    xls = pd.ExcelFile(xlsx_path)
    sheets = {}
    for name in xls.sheet_names:
        sheets[name] = pd.read_excel(xls, sheet_name=name)

    print(f"시트 수: {len(sheets)}")
    return sheets


# ============================================================
# 지표별 Top 20 (종목 선별)
# ============================================================
def rank_top_stocks(sheets):
    """지표별 전체 랭킹 Top 20"""
    print("\n" + "=" * 60)
    print("종목 선별: 지표별 Top 20")
    print("=" * 60)

    indicators = {
        'DD': f'DD_{DEFAULT_FRAME}_{DEFAULT_PERIOD}',
        'MACD': f'MACD_{DEFAULT_FRAME}_{DEFAULT_PERIOD}',
        'RSI': f'RSI_{DEFAULT_FRAME}_{DEFAULT_PERIOD}',
        'HIGH52': f'HIGH52_{DEFAULT_FRAME}_{HIGH52_PERIOD}',
    }

    top_stocks = {}
    for ind_name, sheet_name in indicators.items():
        if sheet_name not in sheets:
            print(f"  ⚠️ {sheet_name} 시트 없음, 스킵")
            continue

        df = sheets[sheet_name].copy()

        if ind_name == 'DD':
            sort_col = 'calmar_ratio'
        else:
            sort_col = 'cum_return'

        if sort_col not in df.columns:
            print(f"  ⚠️ {sheet_name}에 {sort_col} 컬럼 없음")
            continue

        df = df.dropna(subset=[sort_col])
        df = df.sort_values(sort_col, ascending=False).head(TOP_N_STOCKS)
        df = df.reset_index(drop=True)
        df.index += 1
        df.index.name = 'Rank'

        top_stocks[ind_name] = df
        print(f"  {ind_name}: {len(df)}종목")

    return top_stocks


# ============================================================
# 섹터별 Top 3 (섹터 선별)
# ============================================================
def rank_sector_top(sheets):
    """GICS 섹터별 Top 3"""
    print("\n" + "=" * 60)
    print("섹터 선별: 섹터별 Top 3")
    print("=" * 60)

    indicators = {
        'DD': f'DD_{DEFAULT_FRAME}_{DEFAULT_PERIOD}',
        'MACD': f'MACD_{DEFAULT_FRAME}_{DEFAULT_PERIOD}',
        'RSI': f'RSI_{DEFAULT_FRAME}_{DEFAULT_PERIOD}',
        'HIGH52': f'HIGH52_{DEFAULT_FRAME}_{HIGH52_PERIOD}',
    }

    sector_tops = {}
    for ind_name, sheet_name in indicators.items():
        if sheet_name not in sheets:
            continue

        df = sheets[sheet_name].copy()

        if ind_name == 'DD':
            sort_col = 'calmar_ratio'
        else:
            sort_col = 'cum_return'

        if sort_col not in df.columns or 'GICS_Sector' not in df.columns:
            continue

        df = df.dropna(subset=[sort_col, 'GICS_Sector'])

        # 섹터별 Top 3
        result_rows = []
        for sector in sorted(df['GICS_Sector'].unique()):
            sector_df = df[df['GICS_Sector'] == sector].sort_values(sort_col, ascending=False).head(TOP_N_SECTOR)
            result_rows.append(sector_df)

        if result_rows:
            result = pd.concat(result_rows, ignore_index=True)
            sector_tops[ind_name] = result
            n_sectors = df['GICS_Sector'].nunique()
            print(f"  {ind_name}: {len(result)}종목 ({n_sectors}섹터)")

    return sector_tops


# ============================================================
# 복합 모멘텀
# ============================================================
def rank_composite(sheets):
    """4개 지표 중 2개 이상에서 Top 50에 드는 종목"""
    print("\n" + "=" * 60)
    print("복합 모멘텀: 2개+ 지표 Top 50 교집합")
    print("=" * 60)

    indicators = {
        'DD': f'DD_{DEFAULT_FRAME}_{DEFAULT_PERIOD}',
        'MACD': f'MACD_{DEFAULT_FRAME}_{DEFAULT_PERIOD}',
        'RSI': f'RSI_{DEFAULT_FRAME}_{DEFAULT_PERIOD}',
        'HIGH52': f'HIGH52_{DEFAULT_FRAME}_{HIGH52_PERIOD}',
    }

    # 각 지표별 Top 50 종목 수집
    top50_sets = {}
    top50_scores = {}

    for ind_name, sheet_name in indicators.items():
        if sheet_name not in sheets:
            continue

        df = sheets[sheet_name].copy()

        if ind_name == 'DD':
            sort_col = 'calmar_ratio'
        else:
            sort_col = 'cum_return'

        if sort_col not in df.columns:
            continue

        df = df.dropna(subset=[sort_col])
        top50 = df.sort_values(sort_col, ascending=False).head(TOP_N_COMPOSITE)
        top50_sets[ind_name] = set(top50['Symbol'].tolist())

        for _, row in top50.iterrows():
            sym = row['Symbol']
            if sym not in top50_scores:
                top50_scores[sym] = {
                    'Symbol': sym,
                    'Name': row.get('Name', ''),
                    'GICS_Sector': row.get('GICS_Sector', ''),
                    'indicators': [],
                    'count': 0,
                }
            top50_scores[sym]['indicators'].append(ind_name)
            top50_scores[sym]['count'] += 1
            top50_scores[sym][f'{ind_name}_{sort_col}'] = row[sort_col]

    # 2개 이상 지표에서 Top 50
    composite = [v for v in top50_scores.values() if v['count'] >= 2]
    composite.sort(key=lambda x: x['count'], reverse=True)

    if composite:
        comp_df = pd.DataFrame(composite)
        comp_df['indicators'] = comp_df['indicators'].apply(lambda x: ', '.join(x))
        comp_df = comp_df.sort_values('count', ascending=False).reset_index(drop=True)
        comp_df.index += 1
        comp_df.index.name = 'Rank'
        print(f"  복합 모멘텀 종목: {len(comp_df)}")
        print(f"  4지표 Top 50: {sum(1 for v in composite if v['count'] == 4)}")
        print(f"  3지표 Top 50: {sum(1 for v in composite if v['count'] == 3)}")
        print(f"  2지표 Top 50: {sum(1 for v in composite if v['count'] == 2)}")
    else:
        comp_df = pd.DataFrame()
        print(f"  복합 모멘텀 종목: 0")

    return comp_df


# ============================================================
# 차트 생성
# ============================================================
def create_charts(top_stocks, sector_tops, composite_df):
    """총 9장 차트 생성"""
    print("\n" + "=" * 60)
    print("차트 생성 (총 9장)")
    print("=" * 60)

    plt.rcParams['figure.dpi'] = 150

    # --- 1~4: 종목 Top 20 차트 (4장) ---
    for ind_name, df in top_stocks.items():
        fig, ax = plt.subplots(figsize=(14, 8))

        if ind_name == 'DD':
            sort_col = 'calmar_ratio'
            title_metric = 'Calmar Ratio'
        else:
            sort_col = 'cum_return'
            title_metric = 'Cumulative Return'

        plot_df = df.head(TOP_N_STOCKS).sort_values(sort_col, ascending=True)
        labels = [f"{row['Symbol']} ({row['GICS_Sector'][:12]})" for _, row in plot_df.iterrows()]
        values = plot_df[sort_col].values

        colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(values)))
        bars = ax.barh(range(len(labels)), values, color=colors)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel(title_metric, fontsize=10)
        ax.set_title(f'Top {TOP_N_STOCKS} Stocks by {ind_name} ({DEFAULT_FRAME} {DEFAULT_PERIOD})',
                      fontsize=13, fontweight='bold')

        for i, v in enumerate(values):
            fmt = f'{v:.2f}' if ind_name == 'DD' else f'{v:.3f}'
            ax.text(v + abs(v) * 0.02, i, fmt, va='center', fontsize=7)

        plt.tight_layout()
        chart_path = os.path.join(CHARTS_DIR, f'{DATE_STR}_top{TOP_N_STOCKS}_{ind_name.lower()}.png')
        plt.savefig(chart_path, bbox_inches='tight')
        plt.close()
        print(f"  ✅ {os.path.basename(chart_path)}")

    # --- 5~8: 섹터 Top 3 차트 (4장) ---
    for ind_name, df in sector_tops.items():
        if ind_name == 'DD':
            sort_col = 'calmar_ratio'
            title_metric = 'Calmar Ratio'
        else:
            sort_col = 'cum_return'
            title_metric = 'Cumulative Return'

        sectors = sorted(df['GICS_Sector'].unique())
        n_sectors = len(sectors)

        fig, ax = plt.subplots(figsize=(16, max(8, n_sectors * 1.2)))

        y_pos = 0
        y_ticks = []
        y_labels = []
        all_values = []
        all_colors = []
        sector_boundaries = []

        color_map = plt.cm.tab10(np.linspace(0, 1, n_sectors))

        for s_idx, sector in enumerate(sectors):
            sector_df = df[df['GICS_Sector'] == sector].sort_values(sort_col, ascending=False)
            sector_boundaries.append(y_pos)

            for _, row in sector_df.iterrows():
                y_ticks.append(y_pos)
                y_labels.append(f"{row['Symbol']} ({sector[:10]})")
                all_values.append(row[sort_col])
                all_colors.append(color_map[s_idx])
                y_pos += 1
            y_pos += 0.5  # 섹터 간 간격

        ax.barh(y_ticks, all_values, color=all_colors)
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels, fontsize=7)
        ax.set_xlabel(title_metric, fontsize=10)
        ax.set_title(f'Sector Top {TOP_N_SECTOR} by {ind_name} ({DEFAULT_FRAME} {DEFAULT_PERIOD})',
                      fontsize=13, fontweight='bold')

        for i, v in enumerate(all_values):
            fmt = f'{v:.2f}' if ind_name == 'DD' else f'{v:.3f}'
            ax.text(v + abs(v) * 0.02 if v >= 0 else v - abs(v) * 0.15,
                    y_ticks[i], fmt, va='center', fontsize=6)

        plt.tight_layout()
        chart_path = os.path.join(CHARTS_DIR, f'{DATE_STR}_sector_top{TOP_N_SECTOR}_{ind_name.lower()}.png')
        plt.savefig(chart_path, bbox_inches='tight')
        plt.close()
        print(f"  ✅ {os.path.basename(chart_path)}")

    # --- 9: 복합 모멘텀 차트 (1장) ---
    if len(composite_df) > 0:
        fig, ax = plt.subplots(figsize=(14, max(8, len(composite_df) * 0.4)))

        plot_df = composite_df.sort_values('count', ascending=True)
        labels = [f"{row['Symbol']} ({row['GICS_Sector'][:12]})" for _, row in plot_df.iterrows()]
        counts = plot_df['count'].values

        color_map_comp = {4: '#2ca02c', 3: '#1f77b4', 2: '#ff7f0e'}
        colors = [color_map_comp.get(c, '#999999') for c in counts]

        bars = ax.barh(range(len(labels)), counts, color=colors)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel('Number of Indicators in Top 50', fontsize=10)
        ax.set_title(f'Composite Momentum (2+ Indicators in Top {TOP_N_COMPOSITE})',
                      fontsize=13, fontweight='bold')
        ax.set_xticks([2, 3, 4])

        # 범례
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#2ca02c', label='4 indicators'),
            Patch(facecolor='#1f77b4', label='3 indicators'),
            Patch(facecolor='#ff7f0e', label='2 indicators'),
        ]
        ax.legend(handles=legend_elements, loc='lower right')

        # 지표 이름 표시
        for i, (_, row) in enumerate(plot_df.iterrows()):
            ax.text(counts[len(counts)-1-i] if i < len(counts) else 0 + 0.05,
                    i, row.get('indicators', ''), va='center', fontsize=6, style='italic')

        # 재계산
        for idx_pos, (_, row) in enumerate(plot_df.iterrows()):
            ax.text(row['count'] + 0.05, idx_pos,
                    str(row.get('indicators', '')),
                    va='center', fontsize=6, style='italic')

        plt.tight_layout()
        chart_path = os.path.join(CHARTS_DIR, f'{DATE_STR}_composite_momentum.png')
        plt.savefig(chart_path, bbox_inches='tight')
        plt.close()
        print(f"  ✅ {os.path.basename(chart_path)}")
    else:
        print(f"  ⚠️ 복합 모멘텀 종목 없음, 차트 스킵")


# ============================================================
# Excel 저장
# ============================================================
def export_ranking(top_stocks, sector_tops, composite_df):
    """랭킹 결과 Excel 저장"""
    print("\n" + "=" * 60)
    print("랭킹 Excel 저장")
    print("=" * 60)

    ranking_xlsx = os.path.join(RESULTS_DIR, f'{DATE_STR}_momentum_ranking.xlsx')

    with pd.ExcelWriter(ranking_xlsx, engine='openpyxl') as writer:
        # 종목 Top 20
        for ind_name, df in top_stocks.items():
            df.to_excel(writer, sheet_name=f'Top{TOP_N_STOCKS}_{ind_name}')

        # 섹터 Top 3
        for ind_name, df in sector_tops.items():
            df.to_excel(writer, sheet_name=f'Sector_Top{TOP_N_SECTOR}_{ind_name}', index=False)

        # 복합 모멘텀
        if len(composite_df) > 0:
            composite_df.to_excel(writer, sheet_name='Composite_Momentum')

    print(f"랭킹 저장: {ranking_xlsx}")


# ============================================================
# Main
# ============================================================
def main():
    print(f"PHASE1 Global Momentum - Ranking")
    print(f"Date: {DATE_STR}")
    print(f"기준: {DEFAULT_FRAME} {DEFAULT_PERIOD}")
    print()

    # 백테스트 결과 로드
    sheets = load_backtest()

    # 종목 선별: Top 20
    top_stocks = rank_top_stocks(sheets)

    # 섹터 선별: Top 3
    sector_tops = rank_sector_top(sheets)

    # 복합 모멘텀
    composite_df = rank_composite(sheets)

    # Excel 저장
    export_ranking(top_stocks, sector_tops, composite_df)

    # 차트 생성
    create_charts(top_stocks, sector_tops, composite_df)

    # 최종 요약
    print("\n" + "=" * 60)
    print("최종 요약")
    print("=" * 60)

    if 'DD' in top_stocks:
        print(f"\n[DD Top 5]")
        for _, row in top_stocks['DD'].head(5).iterrows():
            print(f"  {row['Symbol']:6s} {row['Name'][:25]:25s} Calmar={row['calmar_ratio']:.2f}")

    if 'MACD' in top_stocks:
        print(f"\n[MACD Top 5]")
        for _, row in top_stocks['MACD'].head(5).iterrows():
            print(f"  {row['Symbol']:6s} {row['Name'][:25]:25s} CR={row['cum_return']:.3f} "
                  f"WR={row['win_rate']:.0%} ({row['n_trades']:.0f})")

    if 'RSI' in top_stocks:
        print(f"\n[RSI Top 5]")
        for _, row in top_stocks['RSI'].head(5).iterrows():
            print(f"  {row['Symbol']:6s} {row['Name'][:25]:25s} CR={row['cum_return']:.3f} "
                  f"WR={row['win_rate']:.0%} ({row['n_trades']:.0f})")

    if 'HIGH52' in top_stocks:
        print(f"\n[52W High Top 5]")
        for _, row in top_stocks['HIGH52'].head(5).iterrows():
            print(f"  {row['Symbol']:6s} {row['Name'][:25]:25s} CR={row['cum_return']:.3f} "
                  f"WR={row['win_rate']:.0%} ({row['n_trades']:.0f})")

    if len(composite_df) > 0:
        top_comp = composite_df[composite_df['count'] >= 3]
        if len(top_comp) > 0:
            print(f"\n[복합 모멘텀 - 3개+ 지표]")
            for _, row in top_comp.iterrows():
                print(f"  {row['Symbol']:6s} {row['Name'][:25]:25s} "
                      f"({row['count']}지표: {row['indicators']})")

    print(f"\n완료!")


if __name__ == '__main__':
    main()
