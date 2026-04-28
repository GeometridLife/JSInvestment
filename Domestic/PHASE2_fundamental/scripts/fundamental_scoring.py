"""
PHASE2 Fundamental - Step 2: 펀더멘탈 스코어링 (1단계: pykrx 기본)
Date: 2026-04-28
Description:
    - cache/fundamental_cache.pkl 로드
    - 카테고리별 Rank Percentile 스코어링
    - 기업 분류(Type A/B/C)에 따른 차별 스코어링
    - 결과: Excel + 차트 (results/YYYY/MM/)

1단계(pykrx만) 사용 가능 지표:
    밸류에이션: PER, PBR, 배당수익률(DIV)
    수익성: ROE (근사값 = EPS/BPS)
    → 나머지 카테고리는 2단계(DART) 이후 추가

Usage:
    C:/Python311/python.exe scripts/fundamental_scoring.py
"""

import os
import sys
import datetime
import pickle
import pandas as pd
import numpy as np

# matplotlib 한글 설정
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정
for font_name in ['Malgun Gothic', 'NanumGothic', 'AppleGothic']:
    try:
        fm.findfont(font_name, fallback_to_default=False)
        plt.rcParams['font.family'] = font_name
        break
    except:
        continue
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
FUNDAMENTAL_CACHE = os.path.join(CACHE_DIR, 'fundamental_cache.pkl')

TODAY_STR = datetime.date.today().strftime('%Y%m%d')
YEAR_STR = datetime.date.today().strftime('%Y')
MONTH_STR = datetime.date.today().strftime('%m')

RESULTS_DIR = os.path.join(BASE_DIR, 'results', YEAR_STR, MONTH_STR)
os.makedirs(RESULTS_DIR, exist_ok=True)

# 차트 폴더
CHART_DIR = os.path.join(RESULTS_DIR, f'{TODAY_STR}_fundamental_charts')
os.makedirs(CHART_DIR, exist_ok=True)

# ============================================================
# 1단계 카테고리 설계 (pykrx만)
# ============================================================
# 2단계(DART) 추가 시 확장 예정
STAGE_2A_INDICATORS = {
    '밸류에이션': {
        'indicators': ['PER_rank', 'PBR_rank', 'DIV_rank'],
        'weight': 0.50,  # 1단계에서는 밸류에이션 비중 높음 (지표가 적으므로)
    },
    '수익성': {
        'indicators': ['ROE_rank'],
        'weight': 0.50,  # 1단계에서는 수익성 비중도 높게
    },
}

# 2단계(DART) 이후 최종 가중치
STAGE_2B_INDICATORS = {
    '밸류에이션': {
        'indicators': ['PER_rank', 'PBR_rank', 'DIV_rank', 'EV_EBITDA_rank'],
        'weight': 0.30,
    },
    '수익성': {
        'indicators': ['ROE_rank', 'OPM_rank', 'NPM_rank'],
        'weight': 0.20,
    },
    '성장성': {
        'indicators': ['REV_GROWTH_rank', 'OP_GROWTH_rank'],
        'weight': 0.25,
    },
    '재무건전성': {
        'indicators': ['DEBT_RATIO_rank', 'CURRENT_RATIO_rank', 'ICR_rank'],
        'weight': 0.15,
    },
    '현금흐름': {
        'indicators': ['FCF_YIELD_rank', 'ACCRUAL_rank'],
        'weight': 0.10,
    },
}


# ============================================================
# 데이터 로드
# ============================================================
def load_cache():
    if not os.path.exists(FUNDAMENTAL_CACHE):
        print("[ERROR] fundamental_cache.pkl이 없습니다. data_collector.py를 먼저 실행하세요.")
        sys.exit(1)

    with open(FUNDAMENTAL_CACHE, 'rb') as f:
        cache = pickle.load(f)

    print(f"[로드] 캐시 스테이지: {cache.get('stage', '?')}")
    print(f"[로드] 기준일: {cache.get('target_date', '?')}")
    print(f"[로드] 수집일시: {cache.get('collected_at', '?')}")
    return cache


# ============================================================
# Rank Percentile 계산
# ============================================================
def compute_rank_percentile(series, ascending=True):
    """
    Rank Percentile (0~1). ascending=True면 값이 작을수록 높은 rank_pct
    PER, PBR: ascending=True (낮을수록 저평가 → 높은 점수)
    ROE, DIV: ascending=False (높을수록 우수 → 높은 점수)
    """
    valid = series.dropna()
    if len(valid) == 0:
        return pd.Series(np.nan, index=series.index)

    ranked = valid.rank(ascending=ascending, method='average')
    pct = (ranked - 1) / (len(valid) - 1) if len(valid) > 1 else pd.Series(0.5, index=valid.index)
    return pct.reindex(series.index)


def compute_fundamental_scores(df, stage='2A'):
    """카테고리 가중 Rank Percentile 스코어링"""
    print("\n[스코어링] 시작")

    # --- Rank Percentile 계산 ---
    # 원칙: 의미 없는 값(0, 적자, 극단)은 NaN 처리하여 랭킹에서 제외

    # PER: 양수만 유효 (0 = 적자/데이터없음, 음수 = 적자)
    per_valid = df['PER'].copy()
    per_valid[per_valid <= 0] = np.nan       # 적자기업 제외
    per_valid[per_valid > 200] = np.nan      # 극단 고PER 제외
    df['PER_rank'] = compute_rank_percentile(per_valid, ascending=True)  # 낮을수록 좋음

    # PBR: 양수만 유효
    pbr_valid = df['PBR'].copy()
    pbr_valid[pbr_valid <= 0] = np.nan       # 자본잠식 등 제외
    pbr_valid[pbr_valid > 30] = np.nan       # 극단 고PBR 제외
    df['PBR_rank'] = compute_rank_percentile(pbr_valid, ascending=True)  # 낮을수록 좋음

    # DIV (배당수익률): 0 초과만 유효 (무배당 = 0은 제외)
    div_valid = df['DIV'].copy()
    div_valid[div_valid <= 0] = np.nan       # 무배당 종목 제외
    df['DIV_rank'] = compute_rank_percentile(div_valid, ascending=False)  # 높을수록 좋음

    # ROE 근사값: 양수만 유효 (0 이하 = 적자/무의미)
    roe_valid = df['ROE_approx'].copy() if 'ROE_approx' in df.columns else pd.Series(np.nan, index=df.index)
    roe_valid[roe_valid <= 0] = np.nan       # 적자기업 제외
    roe_valid[roe_valid > 100] = np.nan      # 극단값 제외
    df['ROE_rank'] = compute_rank_percentile(roe_valid, ascending=False)  # 높을수록 좋음

    # 유효 지표 수 체크 (최소 2개 이상 유효해야 스코어링 참여)
    rank_cols_check = ['PER_rank', 'PBR_rank', 'DIV_rank', 'ROE_rank']
    df['n_valid_ranks'] = df[rank_cols_check].notna().sum(axis=1)

    # 디버그 출력
    for col in rank_cols_check:
        valid_n = df[col].notna().sum()
        print(f"  {col}: 유효 {valid_n}종목")

    # --- 카테고리 점수 계산 ---
    categories = STAGE_2A_INDICATORS if stage == '2A' else STAGE_2B_INDICATORS

    cat_scores = {}
    for cat_name, cat_info in categories.items():
        indicators = cat_info['indicators']
        # 해당 카테고리 내 유효 지표의 평균
        ind_cols = [c for c in indicators if c in df.columns]
        if ind_cols:
            cat_scores[cat_name] = df[ind_cols].mean(axis=1)
        else:
            cat_scores[cat_name] = pd.Series(np.nan, index=df.index)
        df[f'cat_{cat_name}'] = cat_scores[cat_name]

    # --- 최종 점수: 가중 합산 ---
    df['fundamental_score'] = 0.0
    total_weight = 0.0

    for cat_name, cat_info in categories.items():
        weight = cat_info['weight']
        score_col = f'cat_{cat_name}'
        if score_col in df.columns:
            valid_mask = df[score_col].notna()
            df.loc[valid_mask, 'fundamental_score'] += df.loc[valid_mask, score_col] * weight
            # 가중치 재정규화를 위한 유효 카테고리 추적
            if f'has_{cat_name}' not in df.columns:
                df[f'has_{cat_name}'] = valid_mask.astype(int)
            total_weight += weight

    # 유효 카테고리 수
    has_cols = [c for c in df.columns if c.startswith('has_')]
    df['n_valid_categories'] = df[has_cols].sum(axis=1)

    # 가중치 재정규화 (일부 카테고리 데이터 없는 경우)
    effective_weight = pd.Series(0.0, index=df.index)
    for cat_name, cat_info in categories.items():
        weight = cat_info['weight']
        effective_weight += df.get(f'has_{cat_name}', 0) * weight

    df['fundamental_score'] = np.where(
        effective_weight > 0,
        df['fundamental_score'] / effective_weight,
        np.nan
    )

    # 유효 지표 최소 기준: 4개 중 최소 2개 이상 유효해야 점수 부여
    min_indicators = 2
    df.loc[df['n_valid_ranks'] < min_indicators, 'fundamental_score'] = np.nan

    # 최종 순위
    df['fundamental_rank'] = df['fundamental_score'].rank(ascending=False, method='min')

    # 지표 유효 개수
    rank_cols = [c for c in df.columns if c.endswith('_rank') and not c.startswith('fundamental') and not c.startswith('n_')]
    df['n_indicators'] = df[rank_cols].notna().sum(axis=1)

    # 통계 출력
    valid = df['fundamental_score'].notna()
    print(f"  유효 종목: {valid.sum()} / {len(df)}")
    print(f"  점수 범위: {df.loc[valid, 'fundamental_score'].min():.4f} ~ "
          f"{df.loc[valid, 'fundamental_score'].max():.4f}")
    print(f"  평균: {df.loc[valid, 'fundamental_score'].mean():.4f}")

    return df


# ============================================================
# 결과 저장 (Excel)
# ============================================================
def save_results(df, target_date):
    """결과 Excel 저장"""
    output_path = os.path.join(RESULTS_DIR, f'{TODAY_STR}_fundamental_ranking.xlsx')

    # 섹터 컬럼 확인
    sector_col = None
    for col in ['tier1', 'wics_tier1', 'sector', 'WICS_tier1', 'wics_sector']:
        if col in df.columns:
            sector_col = col
            break

    # 출력용 컬럼 선택
    base_cols = ['ticker', 'name'] if 'name' in df.columns else ['ticker']
    if sector_col:
        base_cols.append(sector_col)
    base_cols.append('company_type')

    score_cols = ['fundamental_score', 'fundamental_rank', 'n_indicators', 'n_valid_categories']
    cat_cols = [c for c in df.columns if c.startswith('cat_')]
    rank_cols = ['PER_rank', 'PBR_rank', 'DIV_rank', 'ROE_rank']
    raw_cols = ['PER', 'PBR', 'EPS', 'BPS', 'DIV', 'DPS', 'ROE_approx']
    mcap_cols = [c for c in ['시가총액', '거래량', '거래대금', '상장주식수'] if c in df.columns]

    all_cols = base_cols + score_cols + cat_cols + rank_cols + raw_cols + mcap_cols
    all_cols = [c for c in all_cols if c in df.columns]

    # 정렬 (점수 높은 순)
    result = df[all_cols].sort_values('fundamental_rank', ascending=True)

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # 전체 랭킹
        result.to_excel(writer, sheet_name='전체랭킹', index=False)

        # Type별 시트
        for comp_type, type_name in [('A', '일반기업'), ('B', '지주사'), ('C', '금융업')]:
            subset = result[result['company_type'] == comp_type]
            if len(subset) > 0:
                subset.to_excel(writer, sheet_name=type_name, index=False)

        # 섹터별 Top 10
        if sector_col:
            sector_top = []
            for sector in df[sector_col].dropna().unique():
                sector_df = result[result[sector_col] == sector].head(10)
                sector_df = sector_df.copy()
                sector_top.append(sector_df)
            if sector_top:
                pd.concat(sector_top).to_excel(writer, sheet_name='섹터별_Top10', index=False)

        # Top 50 상세
        result.head(50).to_excel(writer, sheet_name='Top50', index=False)

    print(f"\n[저장] {os.path.basename(output_path)}")
    print(f"  시트: 전체랭킹, 일반기업, 지주사, 금융업, 섹터별_Top10, Top50")
    return output_path


# ============================================================
# 차트 생성
# ============================================================
def generate_charts(df, target_date):
    """펀더멘탈 스코어 차트 생성"""
    print("\n[차트] 생성 중...")

    valid = df[df['fundamental_score'].notna()].copy()
    name_col = 'name' if 'name' in valid.columns else 'ticker'

    # --- 1. Top 30 펀더멘탈 점수 바 차트 ---
    fig, ax = plt.subplots(figsize=(14, 10))
    top30 = valid.nsmallest(30, 'fundamental_rank')

    colors = {'A': '#4285F4', 'B': '#EA4335', 'C': '#FBBC04'}
    bar_colors = [colors.get(t, '#999999') for t in top30['company_type']]

    bars = ax.barh(
        range(len(top30)),
        top30['fundamental_score'],
        color=bar_colors,
        edgecolor='white',
        linewidth=0.5
    )

    labels = [f"{row[name_col]} ({row['ticker']})" for _, row in top30.iterrows()]
    ax.set_yticks(range(len(top30)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel('Fundamental Score', fontsize=11)
    ax.set_title(f'PHASE2 펀더멘탈 Top 30 (기준일: {target_date})', fontsize=13, fontweight='bold')

    # 범례
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#4285F4', label='일반기업 (A)'),
        Patch(facecolor='#EA4335', label='지주사 (B)'),
        Patch(facecolor='#FBBC04', label='금융업 (C)'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

    plt.tight_layout()
    chart1_path = os.path.join(CHART_DIR, f'{TODAY_STR}_top30_fundamental.png')
    fig.savefig(chart1_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  {os.path.basename(chart1_path)}")

    # --- 2. 카테고리별 분포 (밸류에이션 vs 수익성 산점도) ---
    fig, ax = plt.subplots(figsize=(10, 8))

    has_val = valid['cat_밸류에이션'].notna()
    has_prof = valid['cat_수익성'].notna()
    plot_mask = has_val & has_prof

    if plot_mask.sum() > 0:
        plot_df = valid[plot_mask]

        type_colors = plot_df['company_type'].map(colors).fillna('#999999')
        ax.scatter(
            plot_df['cat_밸류에이션'],
            plot_df['cat_수익성'],
            c=type_colors,
            alpha=0.4,
            s=20,
            edgecolors='white',
            linewidth=0.3
        )

        # Top 10 레이블
        top10 = plot_df.nsmallest(10, 'fundamental_rank')
        for _, row in top10.iterrows():
            ax.annotate(
                row[name_col],
                (row['cat_밸류에이션'], row['cat_수익성']),
                fontsize=7,
                alpha=0.8,
                textcoords='offset points',
                xytext=(5, 5)
            )

        ax.set_xlabel('밸류에이션 점수 (높을수록 저평가)', fontsize=10)
        ax.set_ylabel('수익성 점수 (높을수록 우수)', fontsize=10)
        ax.set_title(f'밸류에이션 vs 수익성 (기준일: {target_date})', fontsize=12, fontweight='bold')
        ax.legend(handles=legend_elements, loc='lower right', fontsize=9)
        ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.3)
        ax.axvline(x=0.5, color='gray', linestyle='--', alpha=0.3)

    plt.tight_layout()
    chart2_path = os.path.join(CHART_DIR, f'{TODAY_STR}_valuation_vs_profitability.png')
    fig.savefig(chart2_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  {os.path.basename(chart2_path)}")

    # --- 3. PER vs PBR 산점도 (시총 크기) ---
    fig, ax = plt.subplots(figsize=(10, 8))

    has_per = valid['PER'].notna() & (valid['PER'] > 0) & (valid['PER'] < 100)
    has_pbr = valid['PBR'].notna() & (valid['PBR'] > 0) & (valid['PBR'] < 10)
    plot_mask2 = has_per & has_pbr

    if plot_mask2.sum() > 0:
        plot_df2 = valid[plot_mask2]

        # 시총으로 점 크기
        if '시가총액' in plot_df2.columns:
            sizes = np.sqrt(plot_df2['시가총액'] / 1e8)  # 억 단위
            sizes = sizes.clip(5, 200)
        else:
            sizes = 20

        type_colors2 = plot_df2['company_type'].map(colors).fillna('#999999')
        ax.scatter(
            plot_df2['PER'],
            plot_df2['PBR'],
            c=type_colors2,
            s=sizes,
            alpha=0.4,
            edgecolors='white',
            linewidth=0.3
        )

        # 기준선
        ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.4, label='PBR=1')
        ax.axvline(x=15, color='blue', linestyle='--', alpha=0.4, label='PER=15')

        ax.set_xlabel('PER (배)', fontsize=10)
        ax.set_ylabel('PBR (배)', fontsize=10)
        ax.set_title(f'PER vs PBR (버블 크기=시가총액, 기준일: {target_date})', fontsize=12, fontweight='bold')
        ax.legend(fontsize=9)

    plt.tight_layout()
    chart3_path = os.path.join(CHART_DIR, f'{TODAY_STR}_per_vs_pbr.png')
    fig.savefig(chart3_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  {os.path.basename(chart3_path)}")

    # --- 4. 섹터별 평균 스코어 ---
    sector_col = None
    for col in ['tier1', 'wics_tier1', 'sector', 'WICS_tier1', 'wics_sector']:
        if col in valid.columns:
            sector_col = col
            break

    if sector_col:
        fig, ax = plt.subplots(figsize=(12, 8))
        sector_avg = valid.groupby(sector_col)['fundamental_score'].agg(['mean', 'count'])
        sector_avg = sector_avg[sector_avg['count'] >= 5]  # 5종목 이상 섹터만
        sector_avg = sector_avg.sort_values('mean', ascending=True)

        bars = ax.barh(
            range(len(sector_avg)),
            sector_avg['mean'],
            color='#4285F4',
            edgecolor='white',
            linewidth=0.5
        )

        # 종목 수 표시
        for i, (idx, row) in enumerate(sector_avg.iterrows()):
            ax.text(row['mean'] + 0.005, i, f"({int(row['count'])})", va='center', fontsize=8, color='gray')

        ax.set_yticks(range(len(sector_avg)))
        ax.set_yticklabels([f"{idx}" for idx in sector_avg.index], fontsize=9)
        ax.set_xlabel('평균 펀더멘탈 점수', fontsize=10)
        ax.set_title(f'WICS 섹터별 평균 펀더멘탈 점수 (기준일: {target_date})', fontsize=12, fontweight='bold')
        ax.axvline(x=0.5, color='gray', linestyle='--', alpha=0.3)

        plt.tight_layout()
        chart4_path = os.path.join(CHART_DIR, f'{TODAY_STR}_sector_avg_score.png')
        fig.savefig(chart4_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  {os.path.basename(chart4_path)}")

    print(f"[차트] 저장 완료: {os.path.basename(CHART_DIR)}/")


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 60)
    print("PHASE2 Fundamental - Step 2: 펀더멘탈 스코어링")
    print(f"실행 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 캐시 로드
    cache = load_cache()
    df = cache['master']
    target_date = cache['target_date']
    stage = cache.get('stage', '2A')

    print(f"\n전체 종목: {len(df)}")
    print(f"기업 분류: {df['company_type'].value_counts().to_dict()}")

    # 스코어링
    df = compute_fundamental_scores(df, stage=stage)

    # 결과 저장
    xlsx_path = save_results(df, target_date)

    # 차트
    generate_charts(df, target_date)

    print(f"\n{'=' * 60}")
    print("펀더멘탈 스코어링 완료")
    print(f"  Excel: {os.path.basename(xlsx_path)}")
    print(f"  차트: {os.path.basename(CHART_DIR)}/")
    print("=" * 60)


if __name__ == '__main__':
    main()
