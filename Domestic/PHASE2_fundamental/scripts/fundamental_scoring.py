"""
PHASE2 Fundamental - Step 4: 펀더멘탈 스코어링 (v2.1)
Date: 2026-04-30
Description:
    - 재무건전성 필터 (부실기업 사전 제거)
    - 메인 스코어 = 밸류에이션 매력도 × 성장성 (곱셈 방식)
      A. Forward 밸류에이션: Forward PER, PEG (지주사: NAV 디스카운트)
      B. Forward 성장성: 매출/영업이익/EPS 성장률, EPS Revision
    - 부가지표: 주주환원 (총주주환원수익률, 주주환원/영업이익, 배당성향, 자사주매입비율)
    - Forward 없으면 Trailing fallback (가중치 50% 감소)

Usage:
    C:/Python311/python.exe scripts/fundamental_scoring.py
"""

import os
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env')
load_dotenv(_env_path)

import sys
import datetime
import pickle
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

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

TODAY_STR = datetime.date.today().strftime('%Y%m%d')
YEAR_STR = datetime.date.today().strftime('%Y')
MONTH_STR = datetime.date.today().strftime('%m')

RESULTS_DIR = os.path.join(BASE_DIR, 'results', YEAR_STR, MONTH_STR)
os.makedirs(RESULTS_DIR, exist_ok=True)
CHART_DIR = os.path.join(RESULTS_DIR, f'{TODAY_STR}_fundamental_charts')
os.makedirs(CHART_DIR, exist_ok=True)

# Forward fallback 감소율 (곱셈 스코어에 적용)
FWD_FALLBACK_PENALTY = 0.50

# 시총 기준 그룹 (억 원)
SIZE_LARGE_THRESHOLD = 1_0000_0000_0000    # 1조 이상 = 대형
SIZE_MID_THRESHOLD = 3000_0000_0000        # 3000억 이상 = 중형, 미만 = 소형


# ============================================================
# 데이터 로드
# ============================================================
def load_all_caches():
    caches = {}

    # pykrx + 마스터
    fund_path = os.path.join(CACHE_DIR, 'fundamental_cache.pkl')
    if os.path.exists(fund_path):
        with open(fund_path, 'rb') as f:
            caches['fundamental'] = pickle.load(f)
        print(f"[로드] fundamental: {len(caches['fundamental']['master'])}종목")

    # DART
    dart_path = os.path.join(CACHE_DIR, 'dart_cache.pkl')
    if os.path.exists(dart_path):
        with open(dart_path, 'rb') as f:
            caches['dart'] = pickle.load(f)
        print(f"[로드] DART: {len(caches['dart'])}종목")

    # 컨센서스
    cons_path = os.path.join(CACHE_DIR, 'consensus_cache.pkl')
    if os.path.exists(cons_path):
        with open(cons_path, 'rb') as f:
            caches['consensus'] = pickle.load(f)
        n = len([k for k in caches['consensus'] if not k.startswith('_')])
        print(f"[로드] 컨센서스: {n}종목")

    # NAV
    nav_path = os.path.join(CACHE_DIR, 'nav_cache.pkl')
    if os.path.exists(nav_path):
        with open(nav_path, 'rb') as f:
            caches['nav'] = pickle.load(f)
        print(f"[로드] NAV: {len(caches['nav'])}종목")

    return caches


# ============================================================
# 통합 DataFrame 구축
# ============================================================
def build_merged_df(caches):
    """모든 캐시를 하나의 DataFrame으로 통합"""
    master = caches['fundamental']['master'].copy()
    target_date = caches['fundamental'].get('target_date', '')

    dart = caches.get('dart', {})
    consensus = caches.get('consensus', {})
    nav = caches.get('nav', {})

    # DART 데이터 병합
    dart_rows = []
    for tk, d in dart.items():
        if isinstance(d, dict) and 'ticker' in d:
            dart_rows.append(d)
    if dart_rows:
        dart_df = pd.DataFrame(dart_rows)
        dart_df['ticker'] = dart_df['ticker'].astype(str).str.zfill(6)
        # 중복 컬럼 방지
        overlap = [c for c in dart_df.columns if c in master.columns and c != 'ticker']
        dart_df = dart_df.drop(columns=[c for c in overlap if c != 'name'], errors='ignore')
        master = master.merge(dart_df, on='ticker', how='left', suffixes=('', '_dart'))

    # 컨센서스 데이터 병합
    cons_rows = []
    for tk, d in consensus.items():
        if isinstance(d, dict) and not tk.startswith('_'):
            row = {'ticker': tk}
            row.update(d)
            cons_rows.append(row)
    if cons_rows:
        cons_df = pd.DataFrame(cons_rows)
        cons_df['ticker'] = cons_df['ticker'].astype(str).str.zfill(6)
        overlap = [c for c in cons_df.columns if c in master.columns and c != 'ticker']
        cons_df = cons_df.drop(columns=overlap, errors='ignore')
        master = master.merge(cons_df, on='ticker', how='left')

    # NAV 데이터 병합
    for tk, d in nav.items():
        if isinstance(d, dict):
            idx = master.index[master['ticker'] == tk]
            if len(idx) > 0:
                master.loc[idx[0], 'nav_discount'] = d.get('nav_discount', np.nan)
                master.loc[idx[0], 'nav_value'] = d.get('nav', np.nan)

    # 시가총액 컬럼 정리 (merge로 _x/_y 분리된 경우)
    if '시가총액' not in master.columns:
        for candidate in ['시가총액_y', '시가총액_x']:
            if candidate in master.columns:
                master['시가총액'] = master[candidate]
                break
    # _x, _y 정리
    for drop_col in ['시가총액_x', '시가총액_y']:
        if drop_col in master.columns and '시가총액' in master.columns:
            master.drop(columns=[drop_col], inplace=True, errors='ignore')

    master['has_forward'] = master.get('fwd_eps', pd.Series(dtype=float)).notna()

    print(f"\n  통합 완료: {len(master)}종목")
    print(f"  Forward 데이터: {master['has_forward'].sum()}종목")
    print(f"  DART 데이터: {master.get('매출액', pd.Series(dtype=float)).notna().sum()}종목")

    return master, target_date


# ============================================================
# Phase 1: 재무건전성 필터
# ============================================================
def apply_financial_filter(df):
    """부실기업 사전 제거"""
    print("\n[필터] 재무건전성 필터 적용")
    n_before = len(df)
    filter_reasons = {}
    df['filter_out'] = ''  # 초기화

    # (1) 자본잠식: 자본총계 ≤ 0
    if '자본총계' in df.columns:
        mask = df['자본총계'].notna() & (df['자본총계'] <= 0)
        filter_reasons['자본잠식'] = mask.sum()
        df.loc[mask, 'filter_out'] = df.loc[mask, 'filter_out'] + '자본잠식|'

    # (2) 부채비율 > 400% (금융업 제외)
    if '부채총계' in df.columns and '자본총계' in df.columns:
        debt_ratio = df['부채총계'] / df['자본총계'].replace(0, np.nan) * 100
        mask = (debt_ratio > 400) & (df['company_type'] != 'C')
        filter_reasons['고부채'] = mask.sum()
        df.loc[mask, 'filter_out'] = df.loc[mask, 'filter_out'] + '고부채|'

    # (3) 이자보상배율 < 1
    if '영업이익' in df.columns and '이자지급' in df.columns:
        icr = df['영업이익'] / df['이자지급'].replace(0, np.nan).abs()
        mask = icr.notna() & (icr < 1) & (df['영업이익'].notna())
        filter_reasons['이자보상배율미달'] = mask.sum()
        df.loc[mask, 'filter_out'] = df.loc[mask, 'filter_out'] + '이자보상|'

    # 필터 결과
    filtered_out = df['filter_out'].str.len() > 0
    df['passed_filter'] = ~filtered_out

    for reason, count in filter_reasons.items():
        print(f"  {reason}: {count}종목 제외")
    print(f"  필터 통과: {df['passed_filter'].sum()} / {n_before}")

    return df


# ============================================================
# Phase 2: 지표 산출
# ============================================================
def compute_rank_pct(series, ascending=True):
    """Rank Percentile: 0~1 범위, 1 = 가장 좋음, 0 = 가장 나쁨"""
    valid = series.dropna()
    if len(valid) <= 1:
        return pd.Series(np.nan, index=series.index)
    ranked = valid.rank(ascending=ascending, method='average')
    pct = 1.0 - (ranked - 1) / (len(valid) - 1)
    return pct.reindex(series.index)


def compute_indicators(df):
    """모든 지표 산출"""
    print("\n[지표] 산출 중...")

    # === A. 밸류에이션 ===

    # Forward PER = 현재가 / Forward EPS
    if 'fwd_eps' in df.columns:
        # 현재가 = EPS × PER (pykrx) 또는 시총/주식수
        # 간소화: pykrx의 PER 데이터 활용
        # Forward PER = (Trailing PER × Trailing EPS) / Forward EPS
        trailing_eps = df['EPS'].replace(0, np.nan)
        trailing_per = df['PER'].replace(0, np.nan)
        current_price = trailing_eps * trailing_per  # 근사 현재가

        fwd_eps = df['fwd_eps'].replace(0, np.nan)
        df['fwd_per'] = current_price / fwd_eps
        df.loc[df['fwd_per'] <= 0, 'fwd_per'] = np.nan
        df.loc[df['fwd_per'] > 200, 'fwd_per'] = np.nan

        # PEG = Forward PER / Forward EPS 성장률(%)
        fwd_eps_growth = (fwd_eps / trailing_eps - 1) * 100  # %
        df['peg'] = df['fwd_per'] / fwd_eps_growth.replace(0, np.nan)
        df.loc[df['peg'] <= 0, 'peg'] = np.nan
        df.loc[df['peg'] > 10, 'peg'] = np.nan

    # Trailing PER (fallback)
    df['trailing_per'] = df['PER'].copy()
    df.loc[df['trailing_per'] <= 0, 'trailing_per'] = np.nan
    df.loc[df['trailing_per'] > 200, 'trailing_per'] = np.nan

    # === B. 성장성 ===

    # Forward 성장률 (극단값 캡: -200% ~ +1000%)
    # 분모: 컨센서스 trailing 데이터 우선, 없으면 DART 실적
    if 'fwd_revenue' in df.columns:
        trailing_rev = df.get('trailing_revenue', pd.Series(np.nan, index=df.index)).replace(0, np.nan)
        if '매출액' in df.columns:
            trailing_rev = trailing_rev.fillna(df['매출액'].replace(0, np.nan))
        df['fwd_rev_growth'] = (df['fwd_revenue'] / trailing_rev - 1).clip(-2, 10)

    if 'fwd_op' in df.columns:
        trailing_op = df.get('trailing_op', pd.Series(np.nan, index=df.index)).replace(0, np.nan)
        if '영업이익' in df.columns:
            trailing_op = trailing_op.fillna(df['영업이익'].replace(0, np.nan))
        df['fwd_op_growth'] = (df['fwd_op'] / trailing_op - 1).clip(-2, 10)

    if 'fwd_eps' in df.columns:
        # EPS 분모: 컨센서스 trailing_eps_fn 우선, 없으면 pykrx EPS
        trailing_eps = df.get('trailing_eps_fn', pd.Series(np.nan, index=df.index)).replace(0, np.nan)
        trailing_eps = trailing_eps.fillna(df['EPS'].replace(0, np.nan))
        df['fwd_eps_growth'] = (df['fwd_eps'] / trailing_eps - 1).clip(-2, 10)

    # Trailing 성장률 (fallback)
    if '매출액' in df.columns and '매출액_전기' in df.columns:
        prev_rev = df['매출액_전기'].replace(0, np.nan)
        df['trailing_rev_growth'] = (df['매출액'] / prev_rev - 1).clip(-2, 10)

    if '영업이익' in df.columns and '영업이익_전기' in df.columns:
        prev_op = df['영업이익_전기'].replace(0, np.nan)
        df['trailing_op_growth'] = (df['영업이익'] / prev_op - 1)
        # 극단값 캡 (-200% ~ +1000%)
        df['trailing_op_growth'] = df['trailing_op_growth'].clip(-2, 10)

    if '당기순이익' in df.columns and '당기순이익_전기' in df.columns:
        prev_ni = df['당기순이익_전기'].replace(0, np.nan)
        df['trailing_eps_growth'] = (df['당기순이익'] / prev_ni - 1)
        df['trailing_eps_growth'] = df['trailing_eps_growth'].clip(-2, 10)

    # === C. 주주환원 ===
    mcap = df.get('시가총액', pd.Series(np.nan, index=df.index)).replace(0, np.nan)

    if '배당금지급' in df.columns:
        div_paid = df['배당금지급'].fillna(0).abs()
        buyback = df.get('자사주취득', pd.Series(0, index=df.index)).fillna(0).abs()
        buyback_disposal = df.get('자사주처분', pd.Series(0, index=df.index)).fillna(0).abs()

        net_buyback = buyback - buyback_disposal
        net_buyback = net_buyback.clip(lower=0)  # 순매입만 (처분 > 취득이면 0)

        total_return = div_paid + net_buyback

        # 총 주주환원수익률
        df['shareholder_yield'] = total_return / mcap
        df.loc[df['shareholder_yield'] > 0.3, 'shareholder_yield'] = np.nan  # 30% 초과 이상치

        # 주주환원/영업이익
        op = df.get('영업이익', pd.Series(np.nan, index=df.index)).replace(0, np.nan)
        df['return_to_op'] = total_return / op.abs()
        df.loc[df['return_to_op'] > 1.5, 'return_to_op'] = np.nan  # 150% 초과 캡

        # 자사주매입비율
        df['buyback_yield'] = net_buyback / mcap
        df.loc[df['buyback_yield'] > 0.2, 'buyback_yield'] = np.nan

    # 배당성향 = DPS / EPS
    eps_valid = df['EPS'].replace(0, np.nan)
    dps_valid = df.get('DPS', pd.Series(0, index=df.index))
    df['payout_ratio'] = dps_valid / eps_valid
    df.loc[df['payout_ratio'] < 0, 'payout_ratio'] = np.nan      # 적자 제외
    df.loc[df['payout_ratio'] > 1.0, 'payout_ratio'] = np.nan    # 100% 초과 비정상

    return df


# ============================================================
# Phase 3: Rank Percentile + 카테고리 스코어링
# ============================================================
def _classify_size(mcap):
    """시가총액 기준 대형/중형/소형 분류"""
    if pd.isna(mcap) or mcap <= 0:
        return '소형'
    if mcap >= SIZE_LARGE_THRESHOLD:
        return '대형'
    elif mcap >= SIZE_MID_THRESHOLD:
        return '중형'
    return '소형'


def compute_scores(df):
    """메인 = 밸류에이션 × 성장성, 그룹별(대형/중형/소형) 랭킹"""
    print("\n[스코어링] 시작")

    scored = df[df['passed_filter'] == True].copy()

    # 시총 그룹 분류
    mcap_col = '시가총액' if '시가총액' in scored.columns else None
    if mcap_col:
        scored['size_group'] = scored[mcap_col].apply(_classify_size)
    else:
        scored['size_group'] = '소형'

    for sg in ['대형', '중형', '소형']:
        cnt = (scored['size_group'] == sg).sum()
        print(f"  {sg}: {cnt}종목")
    print(f"  스코어링 대상: {len(scored)}종목")

    # ==========================================
    # A. 밸류에이션 (30%)
    # ==========================================
    val_indicators = {}

    # Forward PER (낮을수록 좋음)
    if 'fwd_per' in scored.columns:
        fwd_per_valid = scored['fwd_per'].copy()
        val_indicators['fwd_per_rank'] = compute_rank_pct(fwd_per_valid, ascending=True)

    # PEG (낮을수록 좋음)
    if 'peg' in scored.columns:
        peg_valid = scored['peg'].copy()
        val_indicators['peg_rank'] = compute_rank_pct(peg_valid, ascending=True)

    # Trailing PER fallback (낮을수록 좋음)
    trailing_per_rank = compute_rank_pct(scored['trailing_per'], ascending=True)
    val_indicators['trailing_per_rank'] = trailing_per_rank

    # NAV 디스카운트 (지주사, 높을수록 좋음)
    if 'nav_discount' in scored.columns:
        nav_rank = compute_rank_pct(scored['nav_discount'], ascending=False)
        val_indicators['nav_rank'] = nav_rank

    # 밸류에이션 카테고리 점수
    for k, v in val_indicators.items():
        scored[k] = v

    def _val_score(row):
        is_holdco = row.get('company_type') == 'B'
        has_fwd = pd.notna(row.get('fwd_per_rank'))

        if is_holdco and pd.notna(row.get('nav_rank')):
            return row['nav_rank']
        elif has_fwd:
            scores = [row.get('fwd_per_rank'), row.get('peg_rank')]
            scores = [s for s in scores if pd.notna(s)]
            return np.mean(scores) if scores else np.nan
        else:
            # Trailing fallback
            val = row.get('trailing_per_rank')
            return val  # 가중치 감소는 최종 합산에서 처리

    scored['cat_valuation'] = scored.apply(_val_score, axis=1)
    scored['val_is_forward'] = scored.get('fwd_per_rank', pd.Series(dtype=float)).notna()

    # ==========================================
    # B. 성장성 (40%)
    # ==========================================
    growth_indicators = {}

    # Forward 성장률
    for col_name, rank_name in [
        ('fwd_rev_growth', 'fwd_rev_growth_rank'),
        ('fwd_op_growth', 'fwd_op_growth_rank'),
        ('fwd_eps_growth', 'fwd_eps_growth_rank'),
    ]:
        if col_name in scored.columns:
            growth_indicators[rank_name] = compute_rank_pct(scored[col_name], ascending=False)

    # EPS Revision
    if 'eps_revision_3m' in scored.columns:
        growth_indicators['eps_rev_rank'] = compute_rank_pct(scored['eps_revision_3m'], ascending=False)

    # Trailing 성장률 (fallback)
    for col_name, rank_name in [
        ('trailing_rev_growth', 'trailing_rev_growth_rank'),
        ('trailing_op_growth', 'trailing_op_growth_rank'),
        ('trailing_eps_growth', 'trailing_eps_growth_rank'),
    ]:
        if col_name in scored.columns:
            growth_indicators[rank_name] = compute_rank_pct(scored[col_name], ascending=False)

    for k, v in growth_indicators.items():
        scored[k] = v

    def _growth_score(row):
        fwd_scores = [row.get('fwd_rev_growth_rank'), row.get('fwd_op_growth_rank'),
                       row.get('fwd_eps_growth_rank'), row.get('eps_rev_rank')]
        fwd_scores = [s for s in fwd_scores if pd.notna(s)]

        trail_scores = [row.get('trailing_rev_growth_rank'), row.get('trailing_op_growth_rank'),
                        row.get('trailing_eps_growth_rank')]
        trail_scores = [s for s in trail_scores if pd.notna(s)]

        if fwd_scores:
            return np.mean(fwd_scores)
        elif trail_scores:
            return np.mean(trail_scores)  # 가중치 감소는 최종 합산에서 처리
        return np.nan

    scored['cat_growth'] = scored.apply(_growth_score, axis=1)
    has_fwd_growth = False
    for c in ['fwd_rev_growth_rank', 'fwd_op_growth_rank', 'fwd_eps_growth_rank']:
        if c in scored.columns:
            has_fwd_growth = True
            break
    if has_fwd_growth:
        fwd_growth_cols = [c for c in ['fwd_rev_growth_rank', 'fwd_op_growth_rank', 'fwd_eps_growth_rank'] if c in scored.columns]
        scored['growth_is_forward'] = scored[fwd_growth_cols].notna().any(axis=1) if fwd_growth_cols else False
    else:
        scored['growth_is_forward'] = False

    # ==========================================
    # C. 주주환원 (30%)
    # ==========================================
    sh_indicators = {}
    for col_name, rank_name, asc in [
        ('shareholder_yield', 'sh_yield_rank', False),
        ('return_to_op', 'return_to_op_rank', False),
        ('payout_ratio', 'payout_rank', False),
        ('buyback_yield', 'buyback_rank', False),
    ]:
        if col_name in scored.columns:
            valid = scored[col_name].copy()
            valid[valid <= 0] = np.nan  # 주주환원 0 이하 제외
            sh_indicators[rank_name] = compute_rank_pct(valid, ascending=asc)

    for k, v in sh_indicators.items():
        scored[k] = v

    def _sh_score(row):
        scores = [row.get('sh_yield_rank'), row.get('return_to_op_rank'),
                  row.get('payout_rank'), row.get('buyback_rank')]
        scores = [s for s in scores if pd.notna(s)]
        return np.mean(scores) if scores else np.nan

    scored['cat_shareholder'] = scored.apply(_sh_score, axis=1)

    # ==========================================
    # 최종 점수: 밸류에이션 × 성장성 (곱셈)
    # 주주환원은 부가지표 (별도 랭킹, 메인에 미반영)
    # ==========================================
    def _final_score(row):
        val = row.get('cat_valuation')
        growth = row.get('cat_growth')

        # 밸류에이션 × 성장성 둘 다 있어야 스코어링
        if pd.isna(val) or pd.isna(growth):
            return np.nan

        score = val * growth

        # Forward fallback 페널티: trailing만 쓰면 스코어 감소
        penalty = 1.0
        if not row.get('val_is_forward', False) and row.get('company_type') != 'B':
            penalty *= FWD_FALLBACK_PENALTY
        if not row.get('growth_is_forward', False):
            penalty *= FWD_FALLBACK_PENALTY

        return score * penalty

    scored['fundamental_score'] = scored.apply(_final_score, axis=1)

    # 그룹별 랭킹 (대형/중형/소형 각각)
    scored['size_rank'] = scored.groupby('size_group')['fundamental_score'].rank(
        ascending=False, method='min')
    # 전체 랭킹도 유지 (참고용)
    scored['fundamental_rank'] = scored['fundamental_score'].rank(ascending=False, method='min')

    # 주주환원 별도 랭킹 (부가지표, 그룹별)
    scored['shareholder_rank'] = scored.groupby('size_group')['cat_shareholder'].rank(
        ascending=False, method='min')

    # 유효 카테고리 수
    scored['n_categories'] = scored[['cat_valuation', 'cat_growth', 'cat_shareholder']].notna().sum(axis=1)

    valid = scored['fundamental_score'].notna()
    print(f"  스코어 유효: {valid.sum()} / {len(scored)}")
    for sg in ['대형', '중형', '소형']:
        sg_valid = valid & (scored['size_group'] == sg)
        if sg_valid.sum() > 0:
            print(f"    {sg}: {sg_valid.sum()}종목, "
                  f"범위 {scored.loc[sg_valid, 'fundamental_score'].min():.4f} ~ "
                  f"{scored.loc[sg_valid, 'fundamental_score'].max():.4f}")

    # 원본 df에 스코어 병합
    score_cols = ['size_group', 'size_rank',
                  'cat_valuation', 'cat_growth', 'cat_shareholder',
                  'fundamental_score', 'fundamental_rank', 'shareholder_rank',
                  'n_categories', 'has_forward', 'val_is_forward', 'growth_is_forward',
                  'shareholder_yield', 'return_to_op', 'payout_ratio', 'buyback_yield',
                  'fwd_per', 'peg', 'trailing_per',
                  'fwd_rev_growth', 'fwd_op_growth', 'fwd_eps_growth',
                  'trailing_rev_growth', 'trailing_op_growth', 'trailing_eps_growth']
    score_cols = [c for c in score_cols if c in scored.columns]

    result = df.merge(scored[['ticker'] + score_cols], on='ticker', how='left', suffixes=('', '_scored'))

    return result


# ============================================================
# 결과 저장
# ============================================================
def save_results(df, target_date):
    output_path = os.path.join(RESULTS_DIR, f'{TODAY_STR}_fundamental_ranking.xlsx')

    sector_col = None
    for col in ['tier1', 'wics_tier1', 'sector']:
        if col in df.columns:
            sector_col = col
            break

    base_cols = ['ticker']
    if 'name' in df.columns: base_cols.append('name')
    if sector_col: base_cols.append(sector_col)
    base_cols.append('company_type')

    score_cols = ['size_group', 'size_rank', 'fundamental_score', 'fundamental_rank',
                  'cat_valuation', 'cat_growth',
                  'cat_shareholder', 'shareholder_rank']

    detail_cols = ['fwd_per', 'peg', 'trailing_per',
                   'shareholder_yield', 'return_to_op', 'payout_ratio', 'buyback_yield',
                   'fwd_rev_growth', 'fwd_op_growth', 'fwd_eps_growth',
                   'trailing_rev_growth', 'trailing_op_growth']

    raw_cols = ['PER', 'PBR', 'EPS', 'BPS', 'DIV', 'DPS',
                '매출액', '영업이익', '당기순이익', '배당금지급', '자사주취득']

    mcap_cols = [c for c in ['시가총액'] if c in df.columns]

    all_cols = base_cols + score_cols + detail_cols + raw_cols + mcap_cols
    all_cols = [c for c in all_cols if c in df.columns]

    # 점수 있는 종목만, 순위순
    has_score = df['fundamental_score'].notna() if 'fundamental_score' in df.columns else pd.Series(False, index=df.index)
    result = df.loc[has_score, all_cols].sort_values('fundamental_rank')

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        result.to_excel(writer, sheet_name='전체랭킹', index=False)

        # 시총 그룹별 시트 (size_rank 순)
        for sg in ['대형', '중형', '소형']:
            if 'size_group' in result.columns:
                sub = result[result['size_group'] == sg].sort_values('size_rank')
                if len(sub) > 0:
                    sub.to_excel(writer, sheet_name=f'{sg}주', index=False)

        # 기업유형별 시트
        for ctype, name in [('A', '일반기업'), ('B', '지주사'), ('C', '금융업')]:
            sub = result[result['company_type'] == ctype]
            if len(sub) > 0:
                sub.to_excel(writer, sheet_name=name, index=False)

        if sector_col:
            sector_top = []
            for sect in result[sector_col].dropna().unique():
                sector_top.append(result[result[sector_col] == sect].head(10))
            if sector_top:
                pd.concat(sector_top).to_excel(writer, sheet_name='섹터별Top10', index=False)

        result.head(50).to_excel(writer, sheet_name='Top50', index=False)

        # 필터 제외 종목
        if 'filter_out' in df.columns:
            filtered = df[df['filter_out'].str.len() > 0]
            if len(filtered) > 0:
                filter_cols = ['ticker', 'name', 'company_type', 'filter_out'] if 'name' in df.columns else ['ticker', 'company_type', 'filter_out']
                filter_cols = [c for c in filter_cols if c in df.columns]
                filtered[filter_cols].to_excel(writer, sheet_name='필터제외', index=False)

    print(f"\n[저장] {os.path.basename(output_path)}")
    return output_path


# ============================================================
# 차트 생성
# ============================================================
def generate_charts(df, target_date):
    print("\n[차트] 생성 중...")
    valid = df[df['fundamental_score'].notna()].copy()
    name_col = 'name' if 'name' in valid.columns else 'ticker'

    colors = {'A': '#4285F4', 'B': '#EA4335', 'C': '#FBBC04'}
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#4285F4', label='일반기업'),
        Patch(facecolor='#EA4335', label='지주사'),
        Patch(facecolor='#FBBC04', label='금융업'),
    ]

    # 1. 그룹별 Top 15 바 차트
    size_colors = {'대형': '#1A73E8', '중형': '#34A853', '소형': '#EA4335'}
    for sg in ['대형', '중형', '소형']:
        sg_data = valid[valid.get('size_group', '') == sg].copy()
        if len(sg_data) == 0:
            continue
        top_n = sg_data.nsmallest(min(15, len(sg_data)), 'size_rank')
        fig, ax = plt.subplots(figsize=(12, 8))
        bar_colors = [colors.get(t, '#999') for t in top_n['company_type']]
        ax.barh(range(len(top_n)), top_n['fundamental_score'], color=bar_colors, edgecolor='white', linewidth=0.5)
        labels = [f"{row[name_col]} ({row['ticker']})" for _, row in top_n.iterrows()]
        ax.set_yticks(range(len(top_n)))
        ax.set_yticklabels(labels, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel('Fundamental Score (Val×Growth)', fontsize=11)
        ax.set_title(f'{sg}주 Top 15 ({target_date})', fontsize=13, fontweight='bold')
        ax.legend(handles=legend_elements, loc='lower right')
        plt.tight_layout()
        fig.savefig(os.path.join(CHART_DIR, f'{TODAY_STR}_top15_{sg}.png'), dpi=150, bbox_inches='tight')
        plt.close(fig)

    # 2. 성장성 vs 밸류에이션 산점도
    fig, ax = plt.subplots(figsize=(10, 8))
    mask = valid['cat_valuation'].notna() & valid['cat_growth'].notna()
    if mask.sum() > 0:
        plot = valid[mask]
        tc = plot['company_type'].map(colors).fillna('#999')
        ax.scatter(plot['cat_valuation'], plot['cat_growth'], c=tc, alpha=0.4, s=20, edgecolors='white', linewidth=0.3)
        top10 = plot.nsmallest(10, 'fundamental_rank')
        for _, r in top10.iterrows():
            ax.annotate(r[name_col], (r['cat_valuation'], r['cat_growth']), fontsize=7, alpha=0.8)
        ax.set_xlabel('밸류에이션 점수 (높을수록 저평가)', fontsize=10)
        ax.set_ylabel('성장성 점수 (높을수록 고성장)', fontsize=10)
        ax.set_title(f'밸류에이션 vs 성장성 ({target_date})', fontsize=12, fontweight='bold')
        ax.axhline(0.5, color='gray', linestyle='--', alpha=0.3)
        ax.axvline(0.5, color='gray', linestyle='--', alpha=0.3)
        ax.legend(handles=legend_elements, loc='lower right')
    plt.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, f'{TODAY_STR}_val_vs_growth.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)

    # 3. Top 10 밸류×성장 + 주주환원 부가지표
    fig, axes = plt.subplots(2, 5, figsize=(20, 8))
    top10 = valid.nsmallest(10, 'fundamental_rank')
    cats = ['cat_valuation', 'cat_growth', 'cat_shareholder']
    cat_labels = ['밸류에이션', '성장성', '주주환원(부가)']
    cat_colors = ['#4285F4', '#34A853', '#AAAAAA']
    for idx, (_, row) in enumerate(top10.iterrows()):
        ax = axes[idx // 5][idx % 5]
        vals = [row.get(c, 0) or 0 for c in cats]
        bars = ax.bar(cat_labels, vals, color=cat_colors)
        ax.set_ylim(0, 1)
        ax.set_title(f"{row[name_col]}\n(#{int(row['fundamental_rank'])})", fontsize=9)
        ax.tick_params(labelsize=7)
    plt.suptitle(f'Top 10: 밸류×성장 + 주주환원(부가) ({target_date})', fontsize=13, fontweight='bold')
    plt.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, f'{TODAY_STR}_top10_categories.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)

    # 4. 주주환원 분포
    if 'shareholder_yield' in valid.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        sh_valid = valid['shareholder_yield'].dropna()
        if len(sh_valid) > 10:
            ax.hist(sh_valid * 100, bins=50, color='#34A853', edgecolor='white', alpha=0.8)
            ax.set_xlabel('총 주주환원수익률 (%)', fontsize=10)
            ax.set_ylabel('종목 수', fontsize=10)
            ax.set_title(f'주주환원수익률 분포 ({target_date})', fontsize=12, fontweight='bold')
            ax.axvline(sh_valid.median() * 100, color='red', linestyle='--', label=f'중앙값: {sh_valid.median()*100:.1f}%')
            ax.legend()
        plt.tight_layout()
        fig.savefig(os.path.join(CHART_DIR, f'{TODAY_STR}_shareholder_yield_dist.png'), dpi=150, bbox_inches='tight')
        plt.close(fig)

    print(f"[차트] 저장: {os.path.basename(CHART_DIR)}/")


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 60)
    print("PHASE2 Fundamental - Step 4: 스코어링 (v2)")
    print(f"실행: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    caches = load_all_caches()

    if 'fundamental' not in caches:
        print("[ERROR] fundamental_cache.pkl 없음. data_collector.py 먼저 실행.")
        sys.exit(1)

    df, target_date = build_merged_df(caches)
    df = apply_financial_filter(df)
    df = compute_indicators(df)
    df = compute_scores(df)

    xlsx_path = save_results(df, target_date)
    generate_charts(df, target_date)

    print(f"\n{'=' * 60}")
    print(f"스코어링 완료")
    print(f"  Excel: {os.path.basename(xlsx_path)}")
    print("=" * 60)


if __name__ == '__main__':
    main()
