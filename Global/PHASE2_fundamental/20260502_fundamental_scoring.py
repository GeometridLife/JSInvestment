"""
PHASE2 Fundamental — Scoring (1,841 US 종목)
================================================================

역할:
  EDGAR 캐시 + yfinance 캐시 + PHASE0 마스터를 통합해서:
    1) 재무건전성 필터 (다중 시그널 + 섹터별 임계값 + NaN-safe)
    2) 카테고리 점수: 밸류에이션 / 성장성 / 주주환원
    3) 메인 = cat_valuation × cat_growth × penalty (Forward fallback 0.50)
    4) 그룹별(Large/Mid/Small) 랭킹 + 섹터 랭킹 + 주주환원 랭킹
    5) Excel 7시트 + 차트 4장 + EDGAR vs yfinance 검증 csv

입력:
    cache/edgar_cache.pkl              # 메인 (Trailing 재무)
    cache/yf_info_cache.pkl            # Forward 컨센서스 + 시총·시세
    cache/yf_cashflow_cache.pkl        # 검증용
    ../PHASE0_classification/20260501_classification_master.xlsx

산출:
    results/{날짜}_fundamental_ranking.xlsx   # 7시트
    charts/{날짜}_top30_large.png
    charts/{날짜}_top30_mid.png
    charts/{날짜}_top30_small.png
    charts/{날짜}_valuation_vs_growth_scatter.png
    logs/edgar_yf_diff.csv             # EDGAR vs yfinance 5%+ 차이

실행:
    cd C:\\Users\\limit\\Desktop\\JS\\Global\\PHASE2_fundamental
    python 20260502_fundamental_scoring.py

옵션:
    --skip-charts  : 차트 생성 스킵
    --skip-xverify : EDGAR-yfinance cross-check 스킵
"""
from __future__ import annotations
import os
import sys
import pickle
import argparse
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

# 한글 폰트 (Windows: Malgun Gothic)
try:
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False
except Exception:
    pass

# ================================================================
# 설정
# ================================================================
SCRIPT_DIR  = Path(__file__).parent
MASTER_PATH = SCRIPT_DIR.parent / 'PHASE0_classification' / '20260501_classification_master.xlsx'
CACHE_DIR   = SCRIPT_DIR / 'cache'
LOGS_DIR    = SCRIPT_DIR / 'logs'
RESULTS_DIR = SCRIPT_DIR / 'results'
CHARTS_DIR  = SCRIPT_DIR / 'charts'
RESULTS_DIR.mkdir(exist_ok=True)
CHARTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

EDGAR_CACHE_PATH = CACHE_DIR / 'edgar_cache.pkl'
YF_INFO_PATH     = CACHE_DIR / 'yf_info_cache.pkl'
YF_CF_PATH       = CACHE_DIR / 'yf_cashflow_cache.pkl'

TODAY_STR = datetime.now().strftime('%Y%m%d')

# 시총 그룹 임계값 (USD)
SIZE_LARGE = 10_000_000_000
SIZE_MID   =  2_000_000_000

# 섹터별 D/E 임계값 (재무건전성 필터)
DE_THRESHOLD = {
    'Financials':  None,
    'Real Estate': 8.0,
    'Utilities':   5.0,
}
DE_DEFAULT = 4.0
TIE_EXEMPT_SECTORS = {'Financials'}

# Forward fallback 페널티
FWD_FALLBACK_PENALTY = 0.50

# Cross-check 임계값
XVERIFY_DIFF_THRESHOLD = 0.05  # 5% 이상 차이 시 로그

# 출력 파일 prefix
OUT_PREFIX = TODAY_STR


# ================================================================
# Phase 0: 캐시 로드 + 통합 DataFrame 구축
# ================================================================
def load_pickle(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, 'rb') as f:
        return pickle.load(f)


def load_master() -> pd.DataFrame:
    df = pd.read_excel(MASTER_PATH, sheet_name='전체종목')
    us_mask = df['Country'] == 'United States'
    not_adr = ~df['Is_ADR'].fillna(False).astype(bool)
    df = df[us_mask & not_adr].copy()
    df = df[['Symbol', 'Name', 'GICS_Sector', 'GICS_Industry_Group',
             'Market_Cap', 'Country']].copy()
    df.rename(columns={'Symbol': 'ticker',
                        'Name': 'name',
                        'GICS_Sector': 'sector',
                        'GICS_Industry_Group': 'industry_group',
                        'Market_Cap': 'mc_master'}, inplace=True)
    return df


def build_dataframe() -> pd.DataFrame:
    """PHASE0 마스터 + EDGAR + yfinance를 ticker 단위로 통합."""
    print("[Phase 0] 캐시 로드 + 통합 DataFrame 구축...")
    master = load_master()
    print(f"  PHASE0 master      : {len(master)}종목")

    edgar_cache = load_pickle(EDGAR_CACHE_PATH)
    yf_info     = load_pickle(YF_INFO_PATH)
    yf_cf       = load_pickle(YF_CF_PATH)
    print(f"  EDGAR cache        : {len(edgar_cache)}종목")
    print(f"  yfinance info      : {len(yf_info)}종목")
    print(f"  yfinance cashflow  : {len(yf_cf)}종목")

    rows = []
    for _, m in master.iterrows():
        tk = m['ticker']
        row = m.to_dict()

        # EDGAR
        e = edgar_cache.get(tk, {})
        if e.get('_status') == 'ok':
            for k, v in e.items():
                if k.startswith('edgar_') or k in ('data_completeness',):
                    row[k] = v
        row['edgar_status'] = e.get('_status', 'missing')

        # yfinance info
        yi = yf_info.get(tk, {})
        if yi.get('_status') == 'ok':
            for k, v in yi.items():
                if k.startswith('yf_'):
                    row[k] = v
        row['yf_info_status'] = yi.get('_status', 'missing')

        # yfinance cashflow (검증용 — 최근값 기준)
        yc = yf_cf.get(tk, {})
        if yc.get('_status') == 'ok':
            for fname in ['CashDividendsPaid', 'RepurchaseOfStock', 'OperatingCashFlow']:
                rec = yc.get(f'yf_{fname}', {})
                vals = rec.get('values') or []
                row[f'yfcf_{fname}'] = vals[0] if vals else None

        rows.append(row)

    df = pd.DataFrame(rows)
    print(f"  통합 DataFrame     : {len(df)}행 × {len(df.columns)}열")
    return df


# ================================================================
# Phase 1: 재무건전성 필터 (다중 시그널 + 섹터 임계값 + NaN-safe)
# ================================================================
def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[Phase 1] 재무건전성 필터...")
    solo, viols = [], []

    for _, r in df.iterrows():
        sector = r.get('sector')
        de_cap = DE_THRESHOLD.get(sector, DE_DEFAULT)

        # 단독 제외
        eq = r.get('edgar_StockholdersEquity')
        if pd.notna(eq) and eq <= 0:
            solo.append('자본잠식'); viols.append([]); continue
        mc = r.get('yf_marketCap') or r.get('mc_master')
        if pd.isna(mc) or (mc or 0) == 0:
            solo.append('시총누락'); viols.append([]); continue
        # EDGAR 데이터 자체가 없는 종목
        if r.get('edgar_status') != 'ok':
            solo.append('EDGAR_데이터없음'); viols.append([]); continue

        # 다중 시그널
        v = []
        if de_cap is not None:
            ltd = r.get('edgar_LongTermDebt')
            if pd.notna(ltd) and pd.notna(eq) and eq > 0:
                de = ltd / eq
                if de > de_cap:
                    v.append(f'고부채(D/E={de:.1f}>{de_cap})')
        if sector not in TIE_EXEMPT_SECTORS:
            op = r.get('edgar_OperatingIncome')
            ie = r.get('edgar_InterestExpense')
            if pd.notna(op) and pd.notna(ie) and abs(ie) > 0:
                tie = op / abs(ie)
                if tie < 1:
                    v.append(f'이자보상미달(TIE={tie:.2f})')
        op_3y = r.get('edgar_OperatingIncome_3y') or []
        if len(op_3y) >= 3 and all(pd.notna(o) and o < 0 for o in op_3y[:3]):
            v.append('3년영업적자')
        ocf_3y = r.get('edgar_OperatingCashFlow_3y') or []
        if len(ocf_3y) >= 3 and all(pd.notna(o) and o < 0 for o in ocf_3y[:3]):
            v.append('3년OCF음수')

        solo.append(None); viols.append(v)

    df['solo_filter']    = solo
    df['violations']     = viols
    df['n_violations']   = df['violations'].apply(len)
    df['passed_filter']  = df['solo_filter'].isna() & (df['n_violations'] < 2)
    df['filter_reason']  = df.apply(
        lambda r: r['solo_filter'] if r['solo_filter']
        else (','.join(r['violations']) if not r['passed_filter'] else ''),
        axis=1)

    n_solo = df['solo_filter'].notna().sum()
    n_multi = ((df['n_violations'] >= 2) & df['solo_filter'].isna()).sum()
    n_pass = df['passed_filter'].sum()
    n_warn = ((df['n_violations'] == 1) & df['solo_filter'].isna()).sum()
    print(f"  단독 제외           : {n_solo:5d}")
    print(f"  다중 시그널 제외    : {n_multi:5d}")
    print(f"  1개 위반 (통과)     : {n_warn:5d}")
    print(f"  정상 통과           : {n_pass - n_warn:5d}")
    print(f"  최종 통과 (스코어링): {n_pass:5d} / {len(df)}")
    return df


# ================================================================
# Phase 2: 카테고리 점수 (rank percentile)
# ================================================================
def rank_pct(s: pd.Series, ascending: bool) -> pd.Series:
    return s.rank(ascending=ascending, pct=True)


def compute_categories(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[Phase 2] 카테고리 점수 산출 (rank percentile)...")
    scored = df[df['passed_filter']].copy()

    # === A. 밸류에이션 (낮을수록 좋음) ===
    scored['fwd_per_rank']      = rank_pct(scored['yf_forwardPE'], ascending=True)
    scored['peg_rank']          = rank_pct(scored['yf_pegRatio'].clip(0, 10) if 'yf_pegRatio' in scored else pd.Series(dtype=float), ascending=True)
    scored['trailing_per_rank'] = rank_pct(scored['yf_trailingPE'], ascending=True)

    def _val(row):
        if pd.notna(row['fwd_per_rank']):
            scs = [row['fwd_per_rank'], row.get('peg_rank')]
            scs = [s for s in scs if pd.notna(s)]
            return np.mean(scs) if scs else np.nan
        return row['trailing_per_rank']
    scored['cat_valuation']  = scored.apply(_val, axis=1)
    scored['val_is_forward'] = scored['fwd_per_rank'].notna()

    # === B. 성장성 (높을수록 좋음) ===
    # Forward EPS growth = (forwardEps - trailingEps) / |trailingEps|
    fwd_eps = scored['yf_forwardEps']
    tr_eps  = scored['yf_trailingEps']
    fwd_eps_growth = ((fwd_eps - tr_eps) / tr_eps.abs()).clip(-2, 10)
    scored['fwd_eps_growth']      = fwd_eps_growth
    scored['fwd_eps_growth_rank'] = rank_pct(fwd_eps_growth, ascending=False)

    # yfinance earningsGrowth, revenueGrowth (Trailing YoY 분기)
    scored['eg_rank'] = rank_pct(scored['yf_earningsGrowth'], ascending=False)
    scored['rg_rank'] = rank_pct(scored['yf_revenueGrowth'], ascending=False)

    def _growth(row):
        # Forward 우선
        fwd = [row.get('fwd_eps_growth_rank')]
        fwd += [row.get('eg_rank'), row.get('rg_rank')]   # Yahoo definition상 Trailing이지만 보조
        fwd = [s for s in fwd if pd.notna(s)]
        if fwd:
            return np.mean(fwd)
        return np.nan
    scored['cat_growth']        = scored.apply(_growth, axis=1)
    scored['growth_is_forward'] = scored['fwd_eps_growth_rank'].notna()

    # === C. 주주환원 (부가지표, 메인 미반영) ===
    div = scored['edgar_DividendsPaid'].abs()
    buy = scored['edgar_StockRepurchase'].abs()
    mc  = scored['yf_marketCap'].fillna(scored.get('mc_master', pd.Series(dtype=float)))
    op  = scored['edgar_OperatingIncome'].abs()
    ni  = scored['edgar_NetIncome']

    scored['shareholder_yield']  = (div.fillna(0) + buy.fillna(0)) / mc
    scored['return_to_op']       = (div.fillna(0) + buy.fillna(0)) / op
    scored['payout_ratio']       = div / ni
    scored['buyback_yield']      = buy / mc

    sh_ranks = pd.concat([
        rank_pct(scored['shareholder_yield'].clip(0, 0.3), ascending=False),
        rank_pct(scored['return_to_op'].clip(0, 1.5), ascending=False),
        rank_pct(scored['payout_ratio'].clip(0, 1.0), ascending=False),
        rank_pct(scored['buyback_yield'].clip(0, 0.3), ascending=False),
    ], axis=1)
    scored['cat_shareholder'] = sh_ranks.mean(axis=1)

    # 통계 출력
    for cat in ['cat_valuation', 'cat_growth', 'cat_shareholder']:
        v = scored[cat].dropna()
        print(f"  {cat:25s} n={len(v):4d}, min={v.min():.3f}, max={v.max():.3f}, mean={v.mean():.3f}")
    fwd_v_n = scored['val_is_forward'].sum()
    fwd_g_n = scored['growth_is_forward'].sum()
    print(f"  Forward(밸류)      : {fwd_v_n}/{len(scored)} ({fwd_v_n/len(scored)*100:.1f}%)")
    print(f"  Forward(성장)      : {fwd_g_n}/{len(scored)} ({fwd_g_n/len(scored)*100:.1f}%)")

    return scored


# ================================================================
# Phase 3: 메인 곱셈 스코어 + 페널티
# ================================================================
def compute_main_score(scored: pd.DataFrame) -> pd.DataFrame:
    print("\n[Phase 3] 메인 스코어 (밸류 × 성장 × 페널티)...")
    def _main(row):
        v = row['cat_valuation']; g = row['cat_growth']
        if pd.isna(v) or pd.isna(g):
            return np.nan
        raw = v * g
        p = 1.0
        if not row['val_is_forward']:    p *= FWD_FALLBACK_PENALTY
        if not row['growth_is_forward']: p *= FWD_FALLBACK_PENALTY
        return raw * p
    scored['fundamental_score'] = scored.apply(_main, axis=1)

    valid = scored['fundamental_score'].dropna()
    print(f"  유효 스코어        : {len(valid)} / {len(scored)}")
    if len(valid) > 0:
        print(f"  분포               : min={valid.min():.4f}, max={valid.max():.4f}, "
              f"mean={valid.mean():.4f}, median={valid.median():.4f}")
    return scored


# ================================================================
# Phase 4: 그룹 분류 + 랭킹
# ================================================================
def compute_rankings(scored: pd.DataFrame) -> pd.DataFrame:
    print("\n[Phase 4] 그룹 분류 + 랭킹...")

    def _classify(mc):
        if pd.isna(mc) or mc <= 0: return 'Small'
        if mc >= SIZE_LARGE: return 'Large'
        if mc >= SIZE_MID:   return 'Mid'
        return 'Small'

    mc_col = scored['yf_marketCap'].fillna(scored.get('mc_master', pd.Series(dtype=float)))
    scored['marketCap_used'] = mc_col
    scored['size_group']     = mc_col.apply(_classify)

    scored['size_rank']        = scored.groupby('size_group')['fundamental_score'].rank(ascending=False, method='min')
    scored['shareholder_rank'] = scored.groupby('size_group')['cat_shareholder'].rank(ascending=False, method='min')
    scored['sector_rank']      = scored.groupby(['size_group', 'sector'])['fundamental_score'].rank(ascending=False, method='min')
    scored['rank_global']      = scored['fundamental_score'].rank(ascending=False, method='min')

    grp = scored['size_group'].value_counts()
    for g in ['Large', 'Mid', 'Small']:
        n = grp.get(g, 0)
        print(f"  {g:5s}: {n}종목")
    return scored


# ================================================================
# EDGAR vs yfinance Cross-check (DividendsPaid, StockRepurchase)
# ================================================================
def cross_check(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[검증] EDGAR vs yfinance cashflow cross-check...")
    diff_rows = []
    for _, r in df.iterrows():
        for ef, yf in [('edgar_DividendsPaid',   'yfcf_CashDividendsPaid'),
                        ('edgar_StockRepurchase', 'yfcf_RepurchaseOfStock'),
                        ('edgar_OperatingCashFlow', 'yfcf_OperatingCashFlow')]:
            ev = r.get(ef); yv = r.get(yf)
            if pd.isna(ev) or pd.isna(yv) or ev == 0 or yv == 0:
                continue
            ea = abs(ev); ya = abs(yv)
            base = max(ea, ya)
            diff = abs(ea - ya) / base
            if diff >= XVERIFY_DIFF_THRESHOLD:
                diff_rows.append({
                    'ticker': r['ticker'], 'sector': r.get('sector'),
                    'field_pair': f'{ef} vs {yf}',
                    'edgar_value': ev, 'yfinance_value': yv,
                    'diff_pct': round(diff * 100, 2),
                })
    diff_df = pd.DataFrame(diff_rows)
    out_path = LOGS_DIR / 'edgar_yf_diff.csv'
    if len(diff_df) > 0:
        diff_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f"  5%+ 차이: {len(diff_df)}건 → {out_path}")
    else:
        print(f"  5%+ 차이 없음")
    return diff_df


# ================================================================
# Excel 출력 (7시트)
# ================================================================
def save_excel(df_full: pd.DataFrame, scored: pd.DataFrame):
    out_path = RESULTS_DIR / f'{OUT_PREFIX}_fundamental_ranking.xlsx'
    print(f"\n[출력] Excel 저장: {out_path.name}")

    # 메인 시트 컬럼
    main_cols = ['ticker', 'name', 'sector', 'industry_group',
                 'size_group', 'size_rank', 'sector_rank', 'rank_global',
                 'fundamental_score', 'cat_valuation', 'cat_growth', 'cat_shareholder',
                 'val_is_forward', 'growth_is_forward',
                 'yf_forwardPE', 'yf_pegRatio', 'yf_trailingPE',
                 'fwd_eps_growth', 'yf_earningsGrowth', 'yf_revenueGrowth',
                 'shareholder_yield', 'return_to_op', 'payout_ratio', 'buyback_yield',
                 'shareholder_rank',
                 'marketCap_used', 'data_completeness']
    main_cols_avail = [c for c in main_cols if c in scored.columns]

    excluded = df_full[~df_full['passed_filter']].copy()
    excl_cols = ['ticker', 'name', 'sector', 'size_group' if 'size_group' in df_full else 'mc_master',
                 'filter_reason', 'solo_filter', 'n_violations', 'violations',
                 'edgar_status', 'data_completeness']
    excl_cols_avail = [c for c in excl_cols if c in excluded.columns]

    fwd_dist = pd.DataFrame({
        'metric': ['총 통과 종목',
                   '밸류에이션 Forward', '밸류에이션 Trailing',
                   '성장성 Forward', '성장성 Trailing',
                   '둘 다 Forward (페널티 없음)',
                   '한쪽만 Forward (페널티 0.5)',
                   '둘 다 Trailing (페널티 0.25)'],
        'count': [
            len(scored),
            int(scored['val_is_forward'].sum()),
            int((~scored['val_is_forward']).sum()),
            int(scored['growth_is_forward'].sum()),
            int((~scored['growth_is_forward']).sum()),
            int((scored['val_is_forward'] & scored['growth_is_forward']).sum()),
            int((scored['val_is_forward'] ^ scored['growth_is_forward']).sum()),
            int(((~scored['val_is_forward']) & (~scored['growth_is_forward'])).sum()),
        ],
    })

    with pd.ExcelWriter(out_path, engine='openpyxl') as w:
        # 그룹별 메인 (각 시트, fundamental_score 내림차순)
        for g in ['Large', 'Mid', 'Small']:
            sub = scored[scored['size_group'] == g].sort_values('size_rank')
            if len(sub) > 0:
                sub[main_cols_avail].to_excel(w, sheet_name=f'Main_{g}', index=False)

        # Top 50 글로벌
        top50 = scored.nsmallest(50, 'rank_global')[main_cols_avail]
        top50.to_excel(w, sheet_name='Top50_Global', index=False)

        # 섹터별 Top 10 (그룹 무관, 글로벌 랭킹 기준)
        sector_top = (scored
                      .sort_values('rank_global')
                      .groupby('sector')
                      .head(10)
                      .sort_values(['sector', 'rank_global']))
        sector_top[main_cols_avail].to_excel(w, sheet_name='Sector_Top10', index=False)

        # 주주환원 랭킹
        sh_cols = ['ticker', 'name', 'sector', 'size_group', 'shareholder_rank',
                   'cat_shareholder', 'shareholder_yield', 'payout_ratio',
                   'buyback_yield', 'return_to_op', 'marketCap_used']
        sh_cols = [c for c in sh_cols if c in scored.columns]
        sh = scored.dropna(subset=['cat_shareholder']).sort_values(['size_group', 'shareholder_rank'])
        sh[sh_cols].to_excel(w, sheet_name='Shareholder_Ranking', index=False)

        # 필터 제외
        excluded[excl_cols_avail].to_excel(w, sheet_name='Excluded', index=False)

        # Forward/Trailing 분포
        fwd_dist.to_excel(w, sheet_name='Forward_Trailing_Dist', index=False)

        # Raw (디버그용 — 전체 컬럼)
        df_full.to_excel(w, sheet_name='Raw', index=False)

    return out_path


# ================================================================
# 차트 (4장)
# ================================================================
def save_charts(scored: pd.DataFrame):
    print("\n[출력] 차트 4장 생성...")
    sectors = sorted(scored['sector'].dropna().unique())
    cmap = plt.get_cmap('tab20')
    sector_color = {s: cmap(i % 20) for i, s in enumerate(sectors)}

    for g in ['Large', 'Mid', 'Small']:
        sub = scored[scored['size_group'] == g].sort_values('size_rank').head(30)
        if len(sub) == 0:
            continue
        fig, ax = plt.subplots(figsize=(13, 9), dpi=150)
        colors = [sector_color.get(s, 'gray') for s in sub['sector']]
        bars = ax.barh(range(len(sub))[::-1], sub['fundamental_score'], color=colors)
        ax.set_yticks(range(len(sub))[::-1])
        ax.set_yticklabels([f"{r['ticker']:6s}  {str(r['name'])[:30]}" for _, r in sub.iterrows()],
                           fontsize=8)
        ax.set_xlabel('Fundamental Score (cat_valuation × cat_growth × penalty)')
        ax.set_title(f'PHASE2 Global Fundamental — Top 30 ({g} Cap)', fontsize=12)
        # 섹터 범례 (실제로 등장한 섹터만)
        present = sub['sector'].dropna().unique()
        handles = [plt.Rectangle((0, 0), 1, 1, color=sector_color[s]) for s in present]
        ax.legend(handles, present, loc='lower right', fontsize=7, title='GICS Sector')
        ax.grid(axis='x', alpha=0.3)
        fig.tight_layout()
        fig.savefig(CHARTS_DIR / f'{OUT_PREFIX}_top30_{g.lower()}.png')
        plt.close(fig)
        print(f"  · {OUT_PREFIX}_top30_{g.lower()}.png ({len(sub)}종목)")

    # 산점도: Valuation × Growth, color=size_group, size=marketCap
    fig, ax = plt.subplots(figsize=(11, 8), dpi=150)
    grp_color = {'Large': '#1f77b4', 'Mid': '#ff7f0e', 'Small': '#2ca02c'}
    for g, c in grp_color.items():
        sub = scored[scored['size_group'] == g].dropna(
            subset=['cat_valuation', 'cat_growth', 'marketCap_used'])
        if len(sub) == 0:
            continue
        sizes = (np.log10(sub['marketCap_used'].clip(lower=1e7)) - 6) * 10
        ax.scatter(sub['cat_valuation'], sub['cat_growth'],
                   s=sizes, c=c, alpha=0.5, edgecolors='white', linewidth=0.5,
                   label=f'{g} (n={len(sub)})')
    ax.axhline(0.5, color='gray', linestyle='--', alpha=0.4)
    ax.axvline(0.5, color='gray', linestyle='--', alpha=0.4)
    ax.set_xlabel('Valuation Score (rank pct, 높을수록 저평가)')
    ax.set_ylabel('Growth Score (rank pct, 높을수록 고성장)')
    ax.set_title(f'PHASE2 — Valuation vs Growth ({len(scored)}종목)', fontsize=12)
    ax.legend(title='Size Group')
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / f'{OUT_PREFIX}_valuation_vs_growth_scatter.png')
    plt.close(fig)
    print(f"  · {OUT_PREFIX}_valuation_vs_growth_scatter.png")


# ================================================================
# 메인
# ================================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-charts',  action='store_true')
    parser.add_argument('--skip-xverify', action='store_true')
    args = parser.parse_args()

    print("=" * 72)
    print("PHASE2 Global Fundamental — Scoring Pipeline")
    print(f"Today      : {TODAY_STR}")
    print(f"Output dir : {RESULTS_DIR}")
    print("=" * 72)

    # 0. 통합 DataFrame
    df = build_dataframe()

    # 1. 필터
    df = apply_filters(df)

    # Cross-check (필터 전 전체 종목 대상으로도 가능 — 여기선 통합 df 전체)
    if not args.skip_xverify:
        cross_check(df)

    # 2. 카테고리
    scored = compute_categories(df)

    # 3. 메인 곱셈
    scored = compute_main_score(scored)

    # 4. 랭킹
    scored = compute_rankings(scored)

    # df_full에 scored 결과 머지 (filtered out 종목도 포함하기 위해)
    score_cols = ['fundamental_score', 'rank_global',
                  'cat_valuation', 'cat_growth', 'cat_shareholder',
                  'val_is_forward', 'growth_is_forward',
                  'fwd_eps_growth', 'shareholder_yield', 'return_to_op',
                  'payout_ratio', 'buyback_yield',
                  'size_group', 'size_rank', 'sector_rank', 'shareholder_rank',
                  'marketCap_used']
    score_cols = [c for c in score_cols if c in scored.columns]
    df_full = df.merge(scored[['ticker'] + score_cols], on='ticker', how='left',
                        suffixes=('', '_dup'))

    # 5. Excel
    out_path = save_excel(df_full, scored)

    # 6. 차트
    if not args.skip_charts:
        save_charts(scored)

    # 7. 요약
    print("\n" + "=" * 72)
    print("PHASE2 완료")
    print("=" * 72)
    print(f"  최종 통과       : {len(scored)} / {len(df)}")
    print(f"  Top 1: {scored.nsmallest(1, 'rank_global')[['ticker', 'name', 'sector']].to_dict('records')[0]}")
    print(f"  결과 Excel      : {out_path}")
    print(f"  차트 폴더       : {CHARTS_DIR}")


if __name__ == '__main__':
    main()
