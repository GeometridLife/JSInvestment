"""
PHASE2 Fundamental — 미니 파이프라인 통합 테스트 (30종목)
================================================================

목적:
  본구현(1,841 US 종목, 첫 수집 4.5시간) 들어가기 전에 30종목으로
  end-to-end 파이프라인 검증.

  검증 대상:
    1) EDGAR 매핑 — 8핵심 필드 30종목 95%+ 커버리지 (sector-aware)
    2) yfinance — Forward 필드 30종목 90%+ 커버리지
    3) 재무건전성 필터 4종 정상 작동
    4) 카테고리 점수 (cat_valuation, cat_growth, cat_shareholder) 0~1 범위
    5) 곱셈 스코어 + Forward fallback 페널티 0.50 적용
    6) 그룹별(Large/Mid/Small) 랭킹 정합성

샘플: 30종목 (GICS 11섹터 균등 + 금융주 + 무배당 + 소형주)

실행:
    cd C:\\Users\\limit\\Desktop\\JS\\Global\\PHASE2_fundamental\\scripts
    pip install edgartools yfinance==1.3.0 pandas numpy openpyxl
    python test_mini_pipeline.py

산출물:
  - test_mini_pipeline_result.xlsx     : 30종목 통합 데이터 + 카테고리 점수 + 랭킹
  - test_mini_pipeline_metrics.csv     : 검증 메트릭 (커버리지, 필터, 스코어 분포)
  - test_mini_pipeline_log.txt         : 종목별 상세 로그

소요 예상: 8~12분 (EDGAR 첫 호출 ~6분 + yf ~3분 + 스코어링 즉시)
"""

import os
import sys
import time
import json
import warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# ----------------------------------------------------------------
# 설정
# ----------------------------------------------------------------
EDGAR_IDENTITY = os.environ.get('EDGAR_IDENTITY', 'JS Investment limited8090@gmail.com')

import yfinance as yf
from edgar import set_identity, Company
set_identity(EDGAR_IDENTITY)

# ----------------------------------------------------------------
# 30종목 샘플 (GICS 11섹터 균등 + 다양성 확보)
# ----------------------------------------------------------------
SAMPLES = [
    # IT (3) — 대형/중형/소형
    ('AAPL',  'Information Technology'),
    ('MSFT',  'Information Technology'),
    ('UPST',  'Information Technology'),  # 소형
    # Financials (3) — 금융주 매핑 검증
    ('JPM',   'Financials'),
    ('BAC',   'Financials'),
    ('GS',    'Financials'),
    # Healthcare (3)
    ('UNH',   'Health Care'),
    ('JNJ',   'Health Care'),
    ('LLY',   'Health Care'),
    # Cons Discretionary (3) — 무배당 포함
    ('AMZN',  'Consumer Discretionary'),
    ('TSLA',  'Consumer Discretionary'),
    ('NKE',   'Consumer Discretionary'),
    # Cons Staples (2)
    ('PG',    'Consumer Staples'),
    ('KO',    'Consumer Staples'),
    # Energy (2)
    ('XOM',   'Energy'),
    ('CVX',   'Energy'),
    # Industrials (3)
    ('CAT',   'Industrials'),
    ('UNP',   'Industrials'),
    ('GE',    'Industrials'),
    # Materials (2)
    ('LIN',   'Materials'),
    ('SHW',   'Materials'),
    # Utilities (2)
    ('NEE',   'Utilities'),
    ('SO',    'Utilities'),
    # Real Estate (2)
    ('PLD',   'Real Estate'),
    ('AMT',   'Real Estate'),
    # Comm Services (3) — 무배당 GOOGL/META 포함
    ('GOOGL', 'Communication Services'),
    ('META',  'Communication Services'),
    ('NFLX',  'Communication Services'),
    # Mid/Small Cap 검증
    ('CROX',  'Consumer Discretionary'),
    ('ANET',  'Information Technology'),
]

# ================================================================
# EDGAR 라벨 매핑 (sector-aware) — 본구현의 edgar_field_map.py 미니 버전
# ================================================================
GENERAL_FIELDS = {
    'income': {
        'Revenue':         ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax',
                            'SalesRevenueNet', 'RevenueFromContractWithCustomerIncludingAssessedTax'],
        'OperatingIncome': ['OperatingIncomeLoss', 'OperatingIncome'],
        'NetIncome':       ['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic'],
        'InterestExpense': ['InterestExpense', 'InterestExpenseDebt', 'InterestExpenseNonoperating',
                            'InterestExpenseOperating', 'InterestIncomeExpenseNet'],
    },
    'balance': {
        'StockholdersEquity': ['StockholdersEquity'],
        'LongTermDebt':       ['LongTermDebt', 'LongTermDebtNoncurrent'],
    },
    'cashflow': {
        'DividendsPaid':     ['PaymentsOfDividends', 'PaymentsOfDividendsCommonStock'],
        'StockRepurchase':   ['PaymentsForRepurchaseOfCommonStock', 'PaymentsForRepurchaseOfEquity'],
        'OperatingCashFlow': ['NetCashProvidedByUsedInOperatingActivities'],
    },
}

# 금융주 오버라이드 — JPM/BAC/GS 등
FINANCIAL_OVERRIDES = {
    'income': {
        # OperatingIncome 라벨 자체가 없음 → 세전이익 사용
        'OperatingIncome': ['IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest'],
        'InterestExpense': ['InterestExpenseOperating', 'InterestExpense', 'InterestIncomeExpenseNet'],
    },
}


def _to_float(v):
    """안전한 float 변환: NaN, 빈값, 문자열(콤마/$/괄호), Decimal 등 모두 흡수"""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, (int, float)):
        return float(v) if not (isinstance(v, float) and np.isnan(v)) else None
    s = str(v).strip()
    if s in ('', '—', '-', 'N/A', 'NA', 'nan', 'None'):
        return None
    # 회계 음수 표현 (1,234) → -1234
    neg = False
    if s.startswith('(') and s.endswith(')'):
        neg = True
        s = s[1:-1]
    # $, 콤마, 공백 제거
    s = s.replace('$', '').replace(',', '').replace(' ', '')
    # 단위 접미사 처리 (concise_format=True 대비)
    mult = 1
    if s.endswith('B'):   mult, s = 1e9,  s[:-1]
    elif s.endswith('M'): mult, s = 1e6,  s[:-1]
    elif s.endswith('K'): mult, s = 1e3,  s[:-1]
    try:
        val = float(s) * mult
        return -val if neg else val
    except (ValueError, TypeError):
        return None


# edgartools enhanced_statement.to_dataframe()이 추가하는 메타 컬럼.
# 이걸 제외해야 실제 회계 기간 컬럼만 남는다.
EDGAR_META_COLS = {'label', 'depth', 'is_abstract', 'is_total', 'section', 'confidence'}


def _period_columns(df: pd.DataFrame) -> list:
    """메타 컬럼 제외하고 회계기간 컬럼만, 최신→과거 순으로 반환."""
    period_cols = [c for c in df.columns if c not in EDGAR_META_COLS]
    # 'FY 2024' > 'FY 2023' string sort로 desc (대부분 케이스 정상 동작)
    # datetime 객체면 자연 정렬됨
    try:
        return sorted(period_cols, reverse=True)
    except TypeError:
        return period_cols


def find_field(df: pd.DataFrame, candidates: list, debug: bool = False):
    """첫 매칭 라벨의 가장 최근 값 반환. 못 찾으면 (None, None).
    DataFrame.loc[label]이 Series/DataFrame 어느 쪽이든 안전 처리.
    메타 컬럼(label/depth/is_abstract/...) 제외 후 period 컬럼만 사용."""
    if df is None or len(df) == 0:
        return None, None
    period_cols = _period_columns(df)
    if not period_cols:
        if debug:
            print(f"    [debug] period 컬럼 없음. df.columns={list(df.columns)[:10]}")
        return None, None
    for label in candidates:
        if label not in df.index:
            continue
        try:
            row = df.loc[label]
            # 라벨 중복 → DataFrame: 첫 row 사용
            if isinstance(row, pd.DataFrame):
                if len(row) == 0:
                    continue
                row = row.iloc[0]
            if not isinstance(row, pd.Series):
                continue
            # period 컬럼만 추출, 최신→과거 순으로
            for col in period_cols:
                if col not in row.index:
                    continue
                fv = _to_float(row[col])
                if fv is not None:
                    return label, fv
            if debug:
                print(f"    [debug] '{label}' 매칭됐으나 period 값 모두 변환 실패. "
                      f"period_cols={period_cols[:3]}, sample={[row.get(c) for c in period_cols[:3]]}")
        except Exception as e:
            if debug:
                print(f"    [debug] '{label}' 접근 실패: {type(e).__name__}: {e}")
            continue
    return None, None


def get_year_series(df: pd.DataFrame, candidates: list, n=3):
    """최근 n개년 시계열 반환 (3년 연속적자 필터용). period 컬럼만 사용."""
    if df is None or len(df) == 0:
        return []
    period_cols = _period_columns(df)
    if not period_cols:
        return []
    for label in candidates:
        if label not in df.index:
            continue
        try:
            row = df.loc[label]
            if isinstance(row, pd.DataFrame):
                if len(row) == 0:
                    continue
                row = row.iloc[0]
            if not isinstance(row, pd.Series):
                continue
            vals = []
            for col in period_cols[:n]:
                if col not in row.index:
                    continue
                fv = _to_float(row[col])
                if fv is not None:
                    vals.append(fv)
                if len(vals) >= n:
                    break
            return vals
        except Exception:
            continue
    return []


_DEBUG_DUMPED = False  # 첫 1종목만 DataFrame 구조 출력

def collect_edgar(ticker: str, sector: str, debug: bool = False) -> dict:
    """EDGAR에서 핵심 8필드 + 3년치 OperatingIncome 추출"""
    global _DEBUG_DUMPED
    is_financial = (sector == 'Financials')
    field_map = {k: dict(v) for k, v in GENERAL_FIELDS.items()}
    if is_financial:
        for stmt, ov in FINANCIAL_OVERRIDES.items():
            field_map[stmt].update(ov)

    out = {'ticker': ticker, 'sector': sector, 'is_financial': is_financial}
    try:
        c = Company(ticker)
        income_df  = c.income_statement(periods=10, period='annual', as_dataframe=True)
        balance_df = c.balance_sheet(periods=10, period='annual', as_dataframe=True)
        cf_df      = c.cashflow_statement(periods=10, period='annual', as_dataframe=True)

        # 첫 종목에서 DataFrame 구조 진단 (이후 진단 누락 시 즉시 보정)
        if debug and not _DEBUG_DUMPED:
            _DEBUG_DUMPED = True
            print(f"\n  [debug] {ticker} income_statement DataFrame 구조:")
            print(f"    shape={income_df.shape}, columns={list(income_df.columns)[:6]}")
            print(f"    index sample(8): {list(income_df.index)[:8]}")
            if len(income_df) > 0:
                first_row = income_df.iloc[0]
                print(f"    first row dtype={first_row.dtype}, values type={type(first_row.values[0]).__name__}, "
                      f"values sample={first_row.values[:3]}")

        for fname, candidates in field_map['income'].items():
            label, value = find_field(income_df, candidates, debug=debug)
            out[f'edgar_{fname}'] = value
            out[f'edgar_{fname}_label'] = label
        for fname, candidates in field_map['balance'].items():
            label, value = find_field(balance_df, candidates, debug=debug)
            out[f'edgar_{fname}'] = value
            out[f'edgar_{fname}_label'] = label
        for fname, candidates in field_map['cashflow'].items():
            label, value = find_field(cf_df, candidates, debug=debug)
            out[f'edgar_{fname}'] = value
            out[f'edgar_{fname}_label'] = label

        # 3년 연속적자 필터용
        out['edgar_OperatingIncome_3y'] = get_year_series(income_df, field_map['income']['OperatingIncome'], n=3)
        # 3년 영업CF 음수 필터용 (신규)
        out['edgar_OperatingCashFlow_3y'] = get_year_series(cf_df, field_map['cashflow']['OperatingCashFlow'], n=3)
        out['edgar_status'] = 'ok'
    except Exception as e:
        import traceback
        out['edgar_status'] = f'ERROR: {type(e).__name__}: {str(e)[:200]}'
        if debug:
            print(f"    [debug] {ticker} traceback:\n{traceback.format_exc()[:600]}")
    return out


def collect_yf(ticker: str) -> dict:
    """yfinance Ticker.info에서 Forward + 시총·시세"""
    out = {}
    try:
        info = yf.Ticker(ticker).info or {}
        for f in ['forwardPE', 'forwardEps', 'pegRatio',
                  'trailingPE', 'trailingEps',
                  'earningsGrowth', 'revenueGrowth',
                  'dividendYield', 'payoutRatio',
                  'debtToEquity', 'currentRatio',
                  'marketCap', 'currentPrice', 'enterpriseValue',
                  'sector', 'industry']:
            out[f'yf_{f}'] = info.get(f)
        out['yf_status'] = 'ok'
    except Exception as e:
        out['yf_status'] = f'ERROR: {type(e).__name__}: {str(e)[:100]}'
    return out


# ================================================================
# 필터 / 카테고리 / 스코어
# ================================================================
# 섹터별 D/E 임계값 (None = 면제)
DE_THRESHOLD = {
    'Financials':  None,
    'Real Estate': 8.0,
    'Utilities':   5.0,
}
DE_DEFAULT = 4.0
TIE_EXEMPT_SECTORS = {'Financials'}


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """다중 시그널 + 섹터별 임계값 + NaN-safe.
    자본잠식/시총누락 = 단독 제외 / 나머지 4개 = 2+ 위반 시 제외."""
    solo_filters = []
    violations_list = []

    for _, r in df.iterrows():
        sector = r.get('sector')
        de_cap = DE_THRESHOLD.get(sector, DE_DEFAULT)

        # === 단독 제외 ===
        eq = r.get('edgar_StockholdersEquity')
        if pd.notna(eq) and eq <= 0:
            solo_filters.append('자본잠식')
            violations_list.append([])
            continue
        mc = r.get('yf_marketCap')
        if pd.isna(mc) or (mc or 0) == 0:
            solo_filters.append('시총누락')
            violations_list.append([])
            continue

        # === 다중 시그널 (NaN-safe) ===
        v = []

        # 2. 고부채
        if de_cap is not None:
            ltd = r.get('edgar_LongTermDebt')
            if pd.notna(ltd) and pd.notna(eq) and eq > 0:
                de = ltd / eq
                if de > de_cap:
                    v.append(f'고부채(D/E={de:.1f}>{de_cap})')

        # 3. 이자보상미달
        if sector not in TIE_EXEMPT_SECTORS:
            op = r.get('edgar_OperatingIncome')
            ie = r.get('edgar_InterestExpense')
            if pd.notna(op) and pd.notna(ie) and abs(ie) > 0:
                tie = op / abs(ie)
                if tie < 1:
                    v.append(f'이자보상미달(TIE={tie:.2f})')

        # 4. 3년 연속 영업적자
        op_3y = r.get('edgar_OperatingIncome_3y') or []
        if len(op_3y) >= 3 and all(pd.notna(o) and o < 0 for o in op_3y[:3]):
            v.append('3년영업적자')

        # 5. 3년 연속 영업CF 음수 (신규)
        ocf_3y = r.get('edgar_OperatingCashFlow_3y') or []
        if len(ocf_3y) >= 3 and all(pd.notna(o) and o < 0 for o in ocf_3y[:3]):
            v.append('3년OCF음수')

        solo_filters.append(None)
        violations_list.append(v)

    df['solo_filter'] = solo_filters
    df['violations'] = violations_list
    df['n_violations'] = df['violations'].apply(len)
    df['passed_filter'] = df['solo_filter'].isna() & (df['n_violations'] < 2)
    df['filter_reason'] = df.apply(
        lambda r: r['solo_filter'] if r['solo_filter']
        else (','.join(r['violations']) if not r['passed_filter'] else ''),
        axis=1)
    # 데이터 완전성 (필터 5개 NaN 개수 추적)
    completeness_cols = ['edgar_StockholdersEquity', 'edgar_LongTermDebt',
                          'edgar_OperatingIncome', 'edgar_InterestExpense']
    df['data_completeness'] = df[completeness_cols].notna().sum(axis=1)
    return df


def rank_pct(s: pd.Series, ascending: bool) -> pd.Series:
    return s.rank(ascending=ascending, pct=True)


def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    # 누락된 EDGAR/yfinance 컬럼 NaN으로 채워서 KeyError 방지
    expected_cols = [
        'edgar_Revenue', 'edgar_OperatingIncome', 'edgar_NetIncome', 'edgar_InterestExpense',
        'edgar_StockholdersEquity', 'edgar_LongTermDebt',
        'edgar_DividendsPaid', 'edgar_StockRepurchase',
        'yf_forwardPE', 'yf_forwardEps', 'yf_pegRatio',
        'yf_trailingPE', 'yf_trailingEps',
        'yf_earningsGrowth', 'yf_revenueGrowth',
        'yf_dividendYield', 'yf_payoutRatio',
        'yf_marketCap',
    ]
    for c in expected_cols:
        if c not in df.columns:
            df[c] = np.nan

    scored = df[df['passed_filter']].copy()

    # === A. 밸류에이션 ===
    scored['fwd_per_rank'] = rank_pct(scored['yf_forwardPE'], ascending=True)
    scored['peg_rank']     = rank_pct(scored['yf_pegRatio'].clip(0, 10), ascending=True)
    scored['trailing_per_rank'] = rank_pct(scored['yf_trailingPE'], ascending=True)

    def _val(row):
        if pd.notna(row['fwd_per_rank']):
            scores = [row['fwd_per_rank'], row.get('peg_rank')]
            scores = [s for s in scores if pd.notna(s)]
            return np.mean(scores) if scores else np.nan
        return row['trailing_per_rank']

    scored['cat_valuation']  = scored.apply(_val, axis=1)
    scored['val_is_forward'] = scored['fwd_per_rank'].notna()

    # === B. 성장성 ===
    # Forward (yfinance): earningsGrowth, revenueGrowth
    scored['fwd_eg_rank']  = rank_pct(scored['yf_earningsGrowth'], ascending=False)
    scored['fwd_rg_rank']  = rank_pct(scored['yf_revenueGrowth'], ascending=False)

    # Trailing (EDGAR): 매출/영업이익 YoY는 미니에서 단순화 (Revenue 1년 데이터만)
    # 본구현에서는 Trailing series로 정확 계산. 여기선 fwd가 없을 때만 단순 fallback.

    def _growth(row):
        fwd = [row.get('fwd_eg_rank'), row.get('fwd_rg_rank')]
        fwd = [s for s in fwd if pd.notna(s)]
        return np.mean(fwd) if fwd else np.nan

    scored['cat_growth']        = scored.apply(_growth, axis=1)
    scored['growth_is_forward'] = scored[['fwd_eg_rank', 'fwd_rg_rank']].notna().any(axis=1)

    # === C. 주주환원 (부가) ===
    div = scored['edgar_DividendsPaid'].abs()
    buy = scored['edgar_StockRepurchase'].abs()
    mc  = scored['yf_marketCap']
    op  = scored['edgar_OperatingIncome'].abs()

    scored['shareholder_yield'] = (div.fillna(0) + buy.fillna(0)) / mc
    scored['return_to_op']      = (div.fillna(0) + buy.fillna(0)) / op
    scored['payout_ratio']      = div / scored['edgar_NetIncome']
    scored['buyback_yield']     = buy / mc

    sh_ranks = pd.concat([
        rank_pct(scored['shareholder_yield'].clip(0, 0.3), ascending=False),
        rank_pct(scored['return_to_op'].clip(0, 1.5), ascending=False),
        rank_pct(scored['payout_ratio'].clip(0, 1.0), ascending=False),
        rank_pct(scored['buyback_yield'].clip(0, 0.3), ascending=False),
    ], axis=1)
    scored['cat_shareholder'] = sh_ranks.mean(axis=1)

    # === 메인 = 밸류 × 성장 × 페널티 ===
    PENALTY = 0.50

    def _main(row):
        v = row['cat_valuation']; g = row['cat_growth']
        if pd.isna(v) or pd.isna(g):
            return np.nan
        raw = v * g
        p = 1.0
        if not row['val_is_forward']:    p *= PENALTY
        if not row['growth_is_forward']: p *= PENALTY
        return raw * p

    scored['fundamental_score'] = scored.apply(_main, axis=1)

    # === 그룹 분류 (미국시장 기준) ===
    SIZE_LARGE = 10_000_000_000
    SIZE_MID   =  2_000_000_000

    def _classify(mc):
        if pd.isna(mc) or mc <= 0: return 'Small'
        if mc >= SIZE_LARGE: return 'Large'
        if mc >= SIZE_MID:   return 'Mid'
        return 'Small'

    scored['size_group'] = scored['yf_marketCap'].apply(_classify)
    scored['size_rank']  = scored.groupby('size_group')['fundamental_score'].rank(ascending=False, method='min')
    scored['shareholder_rank'] = scored.groupby('size_group')['cat_shareholder'].rank(ascending=False, method='min')

    # 원본 df에 머지
    keep = ['ticker', 'cat_valuation', 'cat_growth', 'cat_shareholder',
            'val_is_forward', 'growth_is_forward',
            'fundamental_score', 'size_group', 'size_rank', 'shareholder_rank',
            'shareholder_yield', 'return_to_op', 'payout_ratio', 'buyback_yield']
    return df.merge(scored[keep], on='ticker', how='left')


# ================================================================
# 메인
# ================================================================
def main():
    out_dir = Path(__file__).parent
    log_path = out_dir / 'test_mini_pipeline_log.txt'
    log_lines = []

    def log(msg):
        print(msg)
        log_lines.append(msg)

    log("=" * 72)
    log(f"PHASE2 미니 파이프라인 통합 테스트 — {len(SAMPLES)}종목")
    log(f"EDGAR_IDENTITY: {EDGAR_IDENTITY}")
    log("=" * 72)

    # === Step 1: EDGAR 수집 ===
    log("\n[Step 1/3] EDGAR 재무제표 수집...")
    rows = []
    t0 = time.time()
    for i, (tk, sec) in enumerate(SAMPLES, 1):
        ts = time.time()
        # 첫 1종목 디버그 ON (DataFrame 구조 + 라벨 매칭 진단)
        edgar_data = collect_edgar(tk, sec, debug=(i <= 1))
        elapsed = time.time() - ts
        rev = edgar_data.get('edgar_Revenue')
        rev_str = f"{rev/1e9:.1f}B" if rev else "N/A"
        status_short = edgar_data.get('edgar_status', '?')[:30]
        log(f"  [{i:2d}/{len(SAMPLES)}] {tk:6s} ({sec[:18]:<18s}) Rev={rev_str:>8s} ({elapsed:.1f}s) {status_short}")
        rows.append(edgar_data)
        time.sleep(0.1)
    log(f"  EDGAR 수집 소요: {time.time()-t0:.1f}s")

    # === Step 2: yfinance 수집 ===
    log("\n[Step 2/3] yfinance Ticker.info 수집...")
    t0 = time.time()
    for i, row in enumerate(rows, 1):
        ts = time.time()
        yf_data = collect_yf(row['ticker'])
        row.update(yf_data)
        elapsed = time.time() - ts
        fwdpe = yf_data.get('yf_forwardPE')
        mc = yf_data.get('yf_marketCap')
        mc_str = f"{mc/1e9:.0f}B" if mc else "N/A"
        log(f"  [{i:2d}/{len(SAMPLES)}] {row['ticker']:6s} fwdPE={fwdpe!s:>8s} mc={mc_str:>5s} ({elapsed:.1f}s)")
        time.sleep(0.5)
    log(f"  yfinance 수집 소요: {time.time()-t0:.1f}s")

    # === Step 3: 통합 + 필터 + 스코어 ===
    log("\n[Step 3/3] 통합 + 필터 + 스코어링...")
    df = pd.DataFrame(rows)
    df = apply_filters(df)
    n_passed = df['passed_filter'].sum()
    n_filtered = (~df['passed_filter']).sum()
    log(f"  필터: 통과 {n_passed}/{len(df)}, 제외 {n_filtered}")
    if n_filtered > 0:
        for _, r in df[~df['passed_filter']].iterrows():
            log(f"    제외: {r['ticker']} → {r['filter_reason']}")

    df = compute_scores(df)

    # === 검증 메트릭 ===
    log("\n" + "=" * 72)
    log("검증 메트릭")
    log("=" * 72)

    # 1) EDGAR 필드 커버리지
    log("\n[1] EDGAR 필드 커버리지")
    edgar_fields = ['Revenue', 'OperatingIncome', 'NetIncome', 'InterestExpense',
                    'StockholdersEquity', 'LongTermDebt', 'DividendsPaid', 'StockRepurchase']
    metrics = []
    for f in edgar_fields:
        col = f'edgar_{f}'
        cov = df[col].notna().sum() / len(df) * 100 if col in df.columns else 0
        marker = '✓' if cov >= 95 else ('△' if cov >= 80 else '✗')
        log(f"  {marker} {f:25s} {cov:5.1f}%")
        metrics.append({'category': 'EDGAR', 'field': f, 'coverage_pct': round(cov, 1)})

    # 2) yfinance 핵심 필드
    log("\n[2] yfinance 필드 커버리지")
    yf_fields = ['forwardPE', 'forwardEps', 'earningsGrowth', 'revenueGrowth',
                 'trailingPE', 'marketCap', 'dividendYield']
    for f in yf_fields:
        col = f'yf_{f}'
        cov = df[col].notna().sum() / len(df) * 100 if col in df.columns else 0
        # dividendYield는 무배당 종목 N/A 정상이라 70% 기준 완화
        threshold_ok = 70 if f == 'dividendYield' else 90
        marker = '✓' if cov >= threshold_ok else ('△' if cov >= 50 else '✗')
        log(f"  {marker} {f:25s} {cov:5.1f}%")
        metrics.append({'category': 'yfinance', 'field': f, 'coverage_pct': round(cov, 1)})

    # 3) 필터 작동 (단독 제외 vs 다중 시그널 위반)
    log("\n[3] 필터 적발 — 다중 시그널 + 섹터 임계값")
    n_solo = df['solo_filter'].notna().sum()
    n_multi = ((df['n_violations'] >= 2) & df['solo_filter'].isna()).sum()
    n_passed = df['passed_filter'].sum()
    log(f"  · 단독 제외(자본잠식/시총누락): {n_solo}종목")
    log(f"  · 다중 시그널 제외(2+ 위반)   : {n_multi}종목")
    log(f"  · 1개 위반 (경고만, 통과)     : {((df['n_violations'] == 1) & df['solo_filter'].isna()).sum()}종목")
    log(f"  · 위반 0 (정상)              : {((df['n_violations'] == 0) & df['solo_filter'].isna()).sum()}종목")
    metrics.append({'category': 'Filter', 'field': 'solo_excluded', 'count': int(n_solo)})
    metrics.append({'category': 'Filter', 'field': 'multi_excluded', 'count': int(n_multi)})
    metrics.append({'category': 'Filter', 'field': 'passed', 'count': int(n_passed)})

    # 위반 항목별 카운트 (참고)
    log("\n  위반 항목별 카운트 (단독 제외 안 된 종목 중):")
    violation_types = ['고부채', '이자보상미달', '3년영업적자', '3년OCF음수']
    for vt in violation_types:
        cnt = df['violations'].apply(lambda vs: any(vt in v for v in vs)).sum()
        log(f"    - {vt:12s} {cnt}종목 위반")
        metrics.append({'category': 'Violation', 'field': vt, 'count': int(cnt)})

    # 제외 종목 상세
    excluded_df = df[~df['passed_filter']]
    if len(excluded_df) > 0:
        log(f"\n  제외된 {len(excluded_df)}종목:")
        for _, r in excluded_df.iterrows():
            log(f"    {r['ticker']:6s} ({r['sector'][:20]}) → {r['filter_reason']}")

    # 4) 카테고리 점수 분포
    log("\n[4] 카테고리 점수 분포 (필터 통과 종목)")
    for cat in ['cat_valuation', 'cat_growth', 'cat_shareholder', 'fundamental_score']:
        if cat in df.columns:
            vals = df[cat].dropna()
            if len(vals) > 0:
                log(f"  · {cat:25s} n={len(vals):2d}, min={vals.min():.3f}, "
                    f"max={vals.max():.3f}, mean={vals.mean():.3f}")
                metrics.append({'category': 'Score', 'field': cat,
                                'n': len(vals), 'min': round(vals.min(), 3),
                                'max': round(vals.max(), 3), 'mean': round(vals.mean(), 3)})

    # 5) 그룹 분포
    log("\n[5] 그룹 분포")
    if 'size_group' in df.columns:
        grp = df.dropna(subset=['size_group'])['size_group'].value_counts()
        for g, c in grp.items():
            log(f"  · {g:7s} {c}종목")
            metrics.append({'category': 'Group', 'field': g, 'count': int(c)})

    # 6) Forward 비율
    log("\n[6] Forward / Trailing 비율")
    if 'val_is_forward' in df.columns:
        fwd_v = df['val_is_forward'].sum()
        fwd_g = df['growth_is_forward'].sum()
        log(f"  · 밸류에이션 Forward: {fwd_v}/{len(df.dropna(subset=['cat_valuation']))}")
        log(f"  · 성장성 Forward    : {fwd_g}/{len(df.dropna(subset=['cat_growth']))}")
        metrics.append({'category': 'FwdRatio', 'field': 'valuation', 'count': int(fwd_v)})
        metrics.append({'category': 'FwdRatio', 'field': 'growth', 'count': int(fwd_g)})

    # === 출력 ===
    log("\n" + "=" * 72)
    log("산출 파일")
    log("=" * 72)

    # Excel
    out_xlsx = out_dir / 'test_mini_pipeline_result.xlsx'
    with pd.ExcelWriter(out_xlsx, engine='openpyxl') as w:
        # 메인 결과 — 핵심 컬럼만
        main_cols = ['ticker', 'sector', 'is_financial',
                     'yf_marketCap', 'size_group', 'size_rank',
                     'cat_valuation', 'cat_growth', 'cat_shareholder',
                     'val_is_forward', 'growth_is_forward',
                     'fundamental_score', 'shareholder_rank',
                     'passed_filter', 'filter_reason']
        avail = [c for c in main_cols if c in df.columns]
        df[avail].sort_values(['size_group', 'size_rank'], na_position='last').to_excel(
            w, sheet_name='Main', index=False)
        # 그룹별 시트
        for g in ['Large', 'Mid', 'Small']:
            sub = df[df.get('size_group') == g].sort_values('size_rank') if 'size_group' in df.columns else pd.DataFrame()
            if len(sub) > 0:
                sub[avail].to_excel(w, sheet_name=f'Group_{g}', index=False)
        # 필터 제외
        excl = df[~df['passed_filter']]
        if len(excl) > 0:
            excl[['ticker', 'sector', 'filter_reason']].to_excel(w, sheet_name='Excluded', index=False)
        # 원시
        df.to_excel(w, sheet_name='Raw', index=False)
    log(f"  · {out_xlsx.name}")

    # 메트릭 CSV
    out_csv = out_dir / 'test_mini_pipeline_metrics.csv'
    pd.DataFrame(metrics).to_csv(out_csv, index=False, encoding='utf-8-sig')
    log(f"  · {out_csv.name}")

    # 로그
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log_lines))
    log(f"  · {log_path.name}")

    log("\n" + "=" * 72)
    log("완료. 채팅에 다음 3개 첨부:")
    log("  1) test_mini_pipeline_metrics.csv  (검증 메트릭)")
    log("  2) test_mini_pipeline_result.xlsx  (Main 시트만이라도)")
    log("  3) test_mini_pipeline_log.txt      (전체 콘솔 로그)")
    log("=" * 72)


if __name__ == '__main__':
    main()
