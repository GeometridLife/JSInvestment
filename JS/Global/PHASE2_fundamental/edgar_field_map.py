"""
PHASE2 Fundamental — EDGAR GAAP 라벨 매핑 모듈
================================================================

역할:
  edgartools가 반환하는 statement DataFrame에서 우리가 필요한 핵심 재무 필드를
  추출하기 위한 GAAP concept candidate 매핑.

  - 일반기업과 금융주에서 라벨이 다름 → sector-aware
  - 회사·산업별로 라벨이 다양 → candidate fallback (첫 매칭 우선)
  - DataFrame 첫 6개 컬럼은 메타데이터 (label/depth/is_abstract/...) → period 컬럼만 사용
  - NaN-safe: 못 찾으면 None 반환 (호출자가 NaN-safe 처리)

설계 출처:
  - 2026-05-02 EDGAR v2 테스트 (7종목): 라벨 다양성 식별
  - 2026-05-02 미니 파이프라인 (30종목): 매핑 누락 패턴 식별
  - 메모리: project_global_phase2_edgar_mapping.md
"""
from __future__ import annotations
from typing import Optional, Tuple, List
import pandas as pd
import numpy as np


# ================================================================
# 1. EDGAR DataFrame 메타 컬럼 — period 컬럼만 골라내기 위해 제외
# ================================================================
EDGAR_META_COLS = {'label', 'depth', 'is_abstract', 'is_total', 'section', 'confidence'}


# ================================================================
# 2. 섹터별 임계값 (재무건전성 필터에서 사용)
# ================================================================
DE_THRESHOLD = {
    'Financials':  None,   # 면제 (부채가 영업 자산)
    'Real Estate': 8.0,    # REIT는 자산을 부채로 매입
    'Utilities':   5.0,    # 자본집약적
}
DE_DEFAULT = 4.0
TIE_EXEMPT_SECTORS = {'Financials'}


# ================================================================
# 3. GAAP 필드 매핑 — candidate fallback (첫 매칭 우선)
#    실측 검증 (2026-05-02): 30종목 샘플 + 7종목 v2 결과 종합
# ================================================================

# 일반기업 (대부분 종목)
GENERAL_FIELDS = {
    'income': {
        'Revenue': [
            'Revenues',
            'RevenueFromContractWithCustomerExcludingAssessedTax',
            'RevenueFromContractWithCustomerIncludingAssessedTax',
            'SalesRevenueNet',
            'SalesRevenueGoodsNet',
            'SalesRevenueServicesNet',
        ],
        'OperatingIncome': [
            'OperatingIncomeLoss',
            'OperatingIncome',
        ],
        'NetIncome': [
            'NetIncomeLoss',
            'NetIncomeLossAvailableToCommonStockholdersBasic',
            'ProfitLoss',
        ],
        'InterestExpense': [
            'InterestExpense',
            'InterestExpenseDebt',
            'InterestExpenseNonoperating',
            'InterestExpenseOperating',
            'InterestIncomeExpenseNet',
        ],
        'EPS_Basic': [
            'EarningsPerShareBasic',
            'IncomeLossFromContinuingOperationsPerBasicShare',
        ],
        'EPS_Diluted': [
            'EarningsPerShareDiluted',
            'IncomeLossFromContinuingOperationsPerDilutedShare',
        ],
        'GrossProfit': [
            'GrossProfit',
            'GrossProfit_Calculated',
        ],
    },
    'balance': {
        'TotalAssets': ['Assets'],
        'TotalLiabilities': ['Liabilities'],
        'StockholdersEquity': [
            'StockholdersEquity',
            'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
        ],
        'LongTermDebt': [
            'LongTermDebt',
            'LongTermDebtNoncurrent',
        ],
        'LongTermDebtCurrent': [
            'LongTermDebtCurrent',
        ],
        'CurrentAssets': ['AssetsCurrent'],
        'CurrentLiabilities': ['LiabilitiesCurrent'],
        'CashAndEquivalents': [
            'CashAndCashEquivalentsAtCarryingValue',
            'CashCashEquivalentsAndShortTermInvestments',
        ],
    },
    'cashflow': {
        'OperatingCashFlow': [
            'NetCashProvidedByUsedInOperatingActivities',
        ],
        'InvestingCashFlow': [
            'NetCashProvidedByUsedInInvestingActivities',
        ],
        'FinancingCashFlow': [
            'NetCashProvidedByUsedInFinancingActivities',
        ],
        'DividendsPaid': [
            'PaymentsOfDividends',
            'PaymentsOfDividendsCommonStock',
            'DividendsPaid',
        ],
        'StockRepurchase': [
            'PaymentsForRepurchaseOfCommonStock',
            'PaymentsForRepurchaseOfEquity',
        ],
        'StockIssuance': [
            'ProceedsFromIssuanceOfCommonStock',
            'ProceedsFromIssuanceOfCapitalStock',
        ],
        'CapitalExpenditure': [
            'PaymentsToAcquirePropertyPlantAndEquipment',
        ],
    },
}


# 금융주 오버라이드 — GICS Financials
# OperatingIncome 라벨이 없고 Revenue 구조도 다름
FINANCIAL_OVERRIDES = {
    'income': {
        # OperatingIncome: 세전이익으로 대체
        'OperatingIncome': [
            'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
            'IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic',
        ],
        'InterestExpense': [
            'InterestExpenseOperating',
            'InterestExpense',
            'InterestIncomeExpenseNet',
        ],
        'Revenue': [
            'Revenues',
            'InterestAndDividendIncomeOperating',
        ],
    },
}


# ================================================================
# 4. DataFrame → 값 추출 헬퍼
# ================================================================
def _to_float(v) -> Optional[float]:
    """안전한 float 변환: NaN/빈값/문자열(콤마/$/괄호)/단위접미사 모두 흡수."""
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
    neg = False
    if s.startswith('(') and s.endswith(')'):
        neg = True
        s = s[1:-1]
    s = s.replace('$', '').replace(',', '').replace(' ', '')
    mult = 1
    if s.endswith('B'):   mult, s = 1e9,  s[:-1]
    elif s.endswith('M'): mult, s = 1e6,  s[:-1]
    elif s.endswith('K'): mult, s = 1e3,  s[:-1]
    try:
        val = float(s) * mult
        return -val if neg else val
    except (ValueError, TypeError):
        return None


def _period_columns(df: pd.DataFrame) -> list:
    """메타 컬럼 제외하고 회계기간 컬럼만, 최신→과거 순으로."""
    period_cols = [c for c in df.columns if c not in EDGAR_META_COLS]
    try:
        return sorted(period_cols, reverse=True)
    except TypeError:
        return period_cols


def find_field(df: Optional[pd.DataFrame], candidates: List[str]) -> Tuple[Optional[str], Optional[float]]:
    """첫 매칭 라벨의 가장 최근 값 반환. 없으면 (None, None)."""
    if df is None or len(df) == 0:
        return None, None
    period_cols = _period_columns(df)
    if not period_cols:
        return None, None
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
            for col in period_cols:
                if col not in row.index:
                    continue
                fv = _to_float(row[col])
                if fv is not None:
                    return label, fv
        except Exception:
            continue
    return None, None


def get_year_series(df: Optional[pd.DataFrame], candidates: List[str], n: int = 3) -> List[float]:
    """최근 n개년 시계열 (연속적자/OCF음수 필터용). period 컬럼만."""
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


# ================================================================
# 5. 메인 추출 인터페이스 — collector가 호출
# ================================================================
def get_field_map(sector: Optional[str]) -> dict:
    """섹터에 맞는 매핑 반환 (FINANCIAL OVERRIDES 적용)."""
    field_map = {k: dict(v) for k, v in GENERAL_FIELDS.items()}
    if sector == 'Financials':
        for stmt, ov in FINANCIAL_OVERRIDES.items():
            field_map[stmt].update(ov)
    return field_map


def extract_company_fields(
    ticker: str,
    sector: Optional[str],
    income_df: Optional[pd.DataFrame],
    balance_df: Optional[pd.DataFrame],
    cf_df: Optional[pd.DataFrame],
) -> dict:
    """
    한 종목의 EDGAR 재무 데이터에서 필요한 모든 필드 추출.

    반환 키:
      - 핵심 필드 (스칼라 최근값): edgar_<FieldName>
      - 매칭된 라벨: edgar_<FieldName>_label
      - 시계열 (필터용): edgar_OperatingIncome_3y, edgar_OperatingCashFlow_3y
      - 메타: _is_financial, _sector
    """
    field_map = get_field_map(sector)
    out = {
        'ticker': ticker,
        '_sector': sector,
        '_is_financial': sector == 'Financials',
    }

    # 핵심 스칼라 필드 (최근값)
    for stmt_name, stmt_df in [('income', income_df),
                                ('balance', balance_df),
                                ('cashflow', cf_df)]:
        for fname, candidates in field_map[stmt_name].items():
            label, value = find_field(stmt_df, candidates)
            out[f'edgar_{fname}'] = value
            out[f'edgar_{fname}_label'] = label

    # 시계열 (필터용)
    out['edgar_OperatingIncome_3y'] = get_year_series(
        income_df, field_map['income']['OperatingIncome'], n=3)
    out['edgar_OperatingCashFlow_3y'] = get_year_series(
        cf_df, field_map['cashflow']['OperatingCashFlow'], n=3)

    # 데이터 완전성 (재무건전성 필터 5개 필드 NaN 개수)
    completeness_fields = ['StockholdersEquity', 'LongTermDebt',
                            'OperatingIncome', 'InterestExpense', 'OperatingCashFlow']
    completed = sum(1 for f in completeness_fields if out.get(f'edgar_{f}') is not None)
    out['data_completeness'] = completed

    return out
