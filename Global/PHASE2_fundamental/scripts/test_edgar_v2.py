"""
PHASE2 Fundamental — edgartools 5.30.2 v2 테스트 (실제 API 기반)
================================================================

배경:
  v1 스크립트는 facts.query() API를 잘못 가정해서 추출 0% 실패.
  edgartools 5.30.2 실제 API 확인 후 재작성:
    - Company.income_statement(periods, period, as_dataframe=True) → DataFrame
    - Company.balance_sheet(...)
    - Company.cashflow_statement(...)  # cash_flow()는 deprecated
    - Company.list_concepts(search=..., statement=...)

목적:
  1) 7종목에서 우리가 원하는 핵심 재무 항목이 잡히는지 확인
  2) periods=10으로 깊이(10년치) 가능한지 검증 — yfinance는 4년뿐이라 EDGAR 메리트
  3) 각 종목 처리 시간 측정 (rate limit + 풀스캔 가능성 평가)
  4) 실패 항목은 list_concepts()로 어떤 라벨이 실제 존재하는지 출력해 매핑 보강 자료 확보

샘플: 7개 (test_edgar v1과 동일)
  AAPL, JPM, UNH, XOM, CAT, NEE, PG

실행:
    cd C:\\Users\\limit\\Desktop\\JS\\Global\\PHASE2_fundamental\\scripts
    # PowerShell이면: $env:EDGAR_IDENTITY = "Sang Il limited8090@gmail.com"
    # cmd.exe이면:    set EDGAR_IDENTITY=Sang Il limited8090@gmail.com
    python test_edgar_v2.py

산출물 (같은 폴더):
  - test_edgar_v2_result.json    : 종목별 원시 추출값 + 시간
  - test_edgar_v2_summary.csv    : 항목별 추출 성공률
  - test_edgar_v2_concepts.txt   : 잡힌 라벨 vs 우리 매핑 — 실패 매핑 디버깅용

소요 예상: 1~3분 (7종목, 첫 호출 시 SEC 응답 캐시됨)
"""

import os
import json
import time
from pathlib import Path
import pandas as pd

# ----------------------------------------------------------------
# SEC EDGAR User-Agent (이름 + 이메일 의무)
# ----------------------------------------------------------------
EDGAR_IDENTITY = os.environ.get('EDGAR_IDENTITY', 'JS Investment limited8090@gmail.com')

from edgar import set_identity, Company
import edgar
set_identity(EDGAR_IDENTITY)

# ================================================================
# 1. 샘플
# ================================================================
SAMPLES = [
    ('AAPL',  'IT'),
    ('JPM',   'Financial'),
    ('UNH',   'Healthcare'),
    ('XOM',   'Energy'),
    ('CAT',   'Industrial'),
    ('NEE',   'Utility'),
    ('PG',    'Cons Staples'),
]

# 깊이 테스트 — 10년치 잡히는지
PERIODS = 10

# ================================================================
# 2. 항목 매핑 — edgartools가 statement DataFrame에서 보여주는 라벨 후보
#    (실제 라벨은 회사마다 다를 수 있음. 첫 매칭 우선)
#    edgartools 5.x DataFrame 인덱스는 사람이 읽기 쉬운 label 형식
#    (e.g. 'Total Revenue', 'Net Income', 'Stockholders Equity')
#    하지만 GAAP concept 이름 (e.g. 'Revenues', 'NetIncomeLoss') 도 시도
# ================================================================
INCOME_FIELDS = {
    'Revenue':           ['Revenues', 'Total Revenue', 'Revenue', 'Sales Revenue Net',
                          'Revenue From Contract With Customer Excluding Assessed Tax'],
    'OperatingIncome':   ['Operating Income Loss', 'Operating Income', 'Income From Operations'],
    'NetIncome':         ['Net Income Loss', 'Net Income', 'Net Income Common Stockholders'],
    'InterestExpense':   ['Interest Expense'],
    'EPS_Basic':         ['Earnings Per Share Basic', 'Basic EPS'],
    'EPS_Diluted':       ['Earnings Per Share Diluted', 'Diluted EPS'],
}

BALANCE_FIELDS = {
    'TotalAssets':         ['Assets', 'Total Assets'],
    'TotalLiabilities':    ['Liabilities', 'Total Liabilities'],
    'StockholdersEquity':  ['Stockholders Equity',
                             'Stockholders Equity Including Portion Attributable To Noncontrolling Interest'],
    'LongTermDebt':        ['Long Term Debt', 'Long Term Debt Noncurrent'],
    'CurrentAssets':       ['Assets Current', 'Current Assets'],
    'CurrentLiabilities':  ['Liabilities Current', 'Current Liabilities'],
}

CASHFLOW_FIELDS = {
    'OperatingCashFlow':   ['Net Cash Provided By Used In Operating Activities',
                             'Operating Cash Flow', 'Cash Flow From Operating Activities'],
    'DividendsPaid':       ['Payments Of Dividends', 'Payments Of Dividends Common Stock',
                             'Cash Dividends Paid'],
    'StockRepurchase':     ['Payments For Repurchase Of Common Stock',
                             'Payments For Repurchase Of Equity', 'Repurchase Of Common Stock'],
    'CapitalExpenditure':  ['Payments To Acquire Property Plant And Equipment',
                             'Capital Expenditure', 'Capital Expenditures'],
}

ALL_GROUPS = {
    'IncomeStatement': INCOME_FIELDS,
    'BalanceSheet':    BALANCE_FIELDS,
    'CashFlowStatement': CASHFLOW_FIELDS,
}


# ================================================================
# 3. DataFrame에서 라벨 매칭 — 정확/대소문자 무시/공백 무시 단계적 시도
# ================================================================
def _norm(s: str) -> str:
    return ''.join(str(s).lower().split())

def find_row(df: pd.DataFrame, candidates: list):
    """반환: (matched_label, Series(period→value)) or (None, None)"""
    if df is None or df.empty:
        return None, None
    # 인덱스가 단일 라벨일 수도, 'label' 컬럼이 있을 수도 있음
    # edgartools 5.x: 보통 인덱스가 라벨, 컬럼이 회계기간
    idx_norm_map = {_norm(i): i for i in df.index}
    for label in candidates:
        if label in df.index:
            return label, df.loc[label]
        ln = _norm(label)
        if ln in idx_norm_map:
            real = idx_norm_map[ln]
            return real, df.loc[real]
    # partial contains fallback (양방향)
    for label in candidates:
        ln = _norm(label)
        for k_norm, k_real in idx_norm_map.items():
            if ln in k_norm or k_norm in ln:
                return k_real, df.loc[k_real]
    return None, None


def series_to_record(s: pd.Series) -> dict:
    if s is None:
        return {'matched_label': None, 'periods': [], 'values': []}
    s2 = s.dropna() if hasattr(s, 'dropna') else s
    periods = [str(c) for c in s2.index]
    values = []
    for v in s2.values:
        try:
            values.append(float(v))
        except (TypeError, ValueError):
            values.append(None)
    return {'periods': periods, 'values': values}


# ================================================================
# 4. 종목별 추출
# ================================================================
def extract_company(ticker: str) -> dict:
    out = {'_steps': []}
    t0 = time.time()

    try:
        c = Company(ticker)
    except Exception as e:
        out['_error'] = f"Company({ticker}) 실패: {type(e).__name__}: {e}"
        return out
    out['_steps'].append(f"Company() ok ({time.time()-t0:.1f}s)")

    # 3 statement DataFrame 받기
    statements = {}
    for stmt_name, method in [('IncomeStatement', 'income_statement'),
                               ('BalanceSheet', 'balance_sheet'),
                               ('CashFlowStatement', 'cashflow_statement')]:
        ts = time.time()
        try:
            df = getattr(c, method)(periods=PERIODS, period='annual', as_dataframe=True)
            statements[stmt_name] = df
            n_rows = len(df) if df is not None else 0
            n_cols = len(df.columns) if df is not None and hasattr(df, 'columns') else 0
            out['_steps'].append(f"{stmt_name}: {n_rows}행 × {n_cols}기간 ({time.time()-ts:.1f}s)")
        except Exception as e:
            statements[stmt_name] = None
            out['_steps'].append(f"{stmt_name}: ERROR {type(e).__name__}: {str(e)[:80]}")

    # 항목 추출
    extracted = {}
    available_labels = {}
    for stmt_name, fields in ALL_GROUPS.items():
        df = statements.get(stmt_name)
        extracted[stmt_name] = {}
        if df is None or df.empty:
            available_labels[stmt_name] = []
            continue
        available_labels[stmt_name] = list(df.index)[:50]  # 디버깅용
        for field, candidates in fields.items():
            label, series = find_row(df, candidates)
            if label is None:
                extracted[stmt_name][field] = {'matched_label': None}
            else:
                rec = series_to_record(series)
                rec['matched_label'] = label
                extracted[stmt_name][field] = rec

    out['extracted'] = extracted
    out['available_labels'] = available_labels  # 디버깅용
    out['total_elapsed_sec'] = round(time.time() - t0, 1)
    return out


# ================================================================
# 5. 메인
# ================================================================
def main():
    print("=" * 72)
    print("edgartools v2 재무제표 추출 테스트 (실제 API 기반)")
    try:
        print(f"edgartools version: {edgar.__version__}")
    except Exception:
        pass
    print(f"EDGAR_IDENTITY    : {EDGAR_IDENTITY}")
    print(f"Periods 시도      : {PERIODS} (10년치 깊이 검증)")
    print("=" * 72)

    results = {}
    errors = {}
    start = time.time()

    for ticker, sector in SAMPLES:
        print(f"\n[{sector:14s}] {ticker} ...", end=' ')
        try:
            data = extract_company(ticker)
            results[ticker] = {'sector': sector, **data}
            elapsed = data.get('total_elapsed_sec', 0)
            ext = data.get('extracted', {})
            success_count = sum(1 for stmt in ext.values()
                                  for f in stmt.values()
                                  if f.get('matched_label'))
            total_targets = sum(len(g) for g in ALL_GROUPS.values())
            print(f"{elapsed:.1f}s, 추출 {success_count}/{total_targets}")
            # 핵심 수치 즉시 출력
            try:
                rev = ext['IncomeStatement']['Revenue']
                if rev.get('values'):
                    rec_count = len(rev['values'])
                    latest = rev['values'][0]
                    print(f"   Revenue: {latest/1e9:.1f}B (최근), 깊이 {rec_count}기간")
                div = ext['CashFlowStatement']['DividendsPaid']
                if div.get('values'):
                    print(f"   Dividends: {abs(div['values'][0])/1e9:.2f}B")
                buy = ext['CashFlowStatement']['StockRepurchase']
                if buy.get('values'):
                    print(f"   Buyback : {abs(buy['values'][0])/1e9:.2f}B")
            except Exception:
                pass
        except Exception as e:
            errors[ticker] = f"{type(e).__name__}: {str(e)[:200]}"
            print(f"FATAL ERROR: {errors[ticker]}")
        time.sleep(0.5)  # SEC rate limit (10/sec 한도)

    total = time.time() - start
    print(f"\n전체 소요: {total:.1f}s | 성공 {len(results)}/{len(SAMPLES)}")

    # ================================================================
    # 6. 항목별 커버리지
    # ================================================================
    print("\n" + "=" * 72)
    print("항목별 추출 성공률 + 평균 깊이 (기간 수)")
    print("=" * 72)
    coverage_rows = []
    for stmt_name, fields in ALL_GROUPS.items():
        print(f"\n[{stmt_name}]")
        for field in fields:
            cnt = 0
            depths = []
            for r in results.values():
                f = r.get('extracted', {}).get(stmt_name, {}).get(field, {})
                if f.get('matched_label'):
                    cnt += 1
                    depths.append(len(f.get('values', [])))
            pct = cnt / len(results) * 100 if results else 0
            avg_d = sum(depths) / len(depths) if depths else 0
            marker = '✓' if pct >= 80 else ('△' if pct >= 50 else '✗')
            print(f"  {marker} {field:25s} {pct:5.1f}%  (avg {avg_d:.1f}기간)")
            coverage_rows.append({
                'statement': stmt_name, 'field': field,
                'coverage_pct': round(pct, 1),
                'success_count': cnt, 'total': len(results),
                'avg_depth_periods': round(avg_d, 1),
            })

    pd.DataFrame(coverage_rows).to_csv(
        'test_edgar_v2_summary.csv', index=False, encoding='utf-8-sig')
    print("\n커버리지 CSV: test_edgar_v2_summary.csv")

    # ================================================================
    # 7. 잡힌 라벨 덤프 — 실패 항목 매핑 보강용
    # ================================================================
    concepts_path = Path(__file__).parent / 'test_edgar_v2_concepts.txt'
    with open(concepts_path, 'w', encoding='utf-8') as f:
        for tk, r in results.items():
            f.write(f"\n=== {tk} ({r.get('sector', '')}) ===\n")
            for stmt_name, labels in (r.get('available_labels', {}) or {}).items():
                f.write(f"\n[{stmt_name}] {len(labels)}개 라벨\n")
                for lbl in labels:
                    f.write(f"  - {lbl}\n")
    print(f"라벨 덤프    : {concepts_path}")

    # JSON
    out = {
        'meta': {
            'edgar_identity': EDGAR_IDENTITY,
            'periods_requested': PERIODS,
            'sample_count': len(SAMPLES),
            'success_count': len(results),
            'error_count': len(errors),
            'total_elapsed_sec': round(total, 2),
        },
        'results': results,
        'errors': errors,
    }
    out_path = Path(__file__).parent / 'test_edgar_v2_result.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, default=str, ensure_ascii=False)
    print(f"Raw JSON     : {out_path}")

    print("\n" + "=" * 72)
    print("완료. 채팅에 다음 3개 첨부해 주세요:")
    print("  1) test_edgar_v2_summary.csv")
    print("  2) test_edgar_v2_concepts.txt   ← 매핑 디버깅 핵심")
    print("  3) test_edgar_v2_result.json    (raw 데이터)")
    print("=" * 72)


if __name__ == '__main__':
    main()
