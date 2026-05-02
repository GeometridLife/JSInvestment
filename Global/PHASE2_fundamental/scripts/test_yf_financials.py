"""
PHASE2 Fundamental — yfinance financials/cashflow/balance_sheet 보조 테스트
================================================================

목적:
  Ticker.info 외 영역 — 즉 EDGAR가 메인이 될 영역(Trailing 재무제표,
  현금흐름표, 재무상태표) — 에서 yfinance가 얼마나 잡히는지 baseline 확인.
  EDGAR와 비교 검증할 때 reference 용도로도 사용.

샘플 (test_yf_forward와 동일 14종목):
  GICS 11섹터 + 중형/소형 = 14

검사 항목:
  [Income (.financials)]
    Total Revenue, Operating Income, Net Income, Interest Expense,
    EBITDA, Diluted EPS, Diluted Average Shares
  [Balance Sheet (.balance_sheet)]
    Total Assets, Total Liabilities Net Minority Interest,
    Stockholders Equity, Total Debt, Current Assets, Current Liabilities
  [Cash Flow (.cashflow)]
    Operating Cash Flow, Free Cash Flow,
    Cash Dividends Paid, Repurchase Of Capital Stock,
    Common Stock Issuance, Issuance Of Debt, Repayment Of Debt

실행 방법:
    cd C:\\Users\\limit\\Desktop\\JS\\Global\\PHASE2_fundamental\\scripts
    python test_yf_financials.py

산출물:
  - test_yf_financials_summary.csv : 항목별 종목 커버리지 + 연도 깊이
  - test_yf_financials_result.json : 종목별 raw 추출값 (최근 4개년)

소요 시간 예상: 1~2분 (14종목 × 3 statement)
"""

import yfinance as yf
import pandas as pd
import json
import time
from pathlib import Path

# ================================================================
# 1. 샘플 (test_yf_forward와 동일)
# ================================================================
SAMPLES = [
    ('AAPL',  'IT'),
    ('ANET',  'IT'),
    ('JPM',   'Financial'),
    ('UNH',   'Healthcare'),
    ('AMZN',  'Cons Discretionary'),
    ('PG',    'Cons Staples'),
    ('XOM',   'Energy'),
    ('CAT',   'Industrials'),
    ('LIN',   'Materials'),
    ('NEE',   'Utilities'),
    ('PLD',   'Real Estate'),
    ('GOOGL', 'Comm Services'),
    ('CROX',  'Mid Cap'),
    ('UPST',  'Small Cap'),
]

# ================================================================
# 2. 검사할 항목 — yfinance 행 이름 후보 (회사별로 다를 수 있음)
# ================================================================
INCOME_FIELDS = {
    'Revenue':           ['Total Revenue', 'Revenue', 'Operating Revenue'],
    'OperatingIncome':   ['Operating Income', 'Operating Income Loss'],
    'NetIncome':         ['Net Income', 'Net Income Common Stockholders', 'Net Income Continuous Operations'],
    'InterestExpense':   ['Interest Expense', 'Interest Expense Non Operating'],
    'EBITDA':            ['EBITDA', 'Normalized EBITDA'],
    'DilutedEPS':        ['Diluted EPS', 'Basic EPS'],
    'DilutedShares':     ['Diluted Average Shares', 'Basic Average Shares'],
}

BALANCE_FIELDS = {
    'TotalAssets':         ['Total Assets'],
    'TotalLiabilities':    ['Total Liabilities Net Minority Interest', 'Total Liabilities'],
    'StockholdersEquity':  ['Stockholders Equity', 'Common Stock Equity', 'Total Equity Gross Minority Interest'],
    'TotalDebt':           ['Total Debt', 'Long Term Debt And Capital Lease Obligation'],
    'LongTermDebt':        ['Long Term Debt'],
    'CurrentAssets':       ['Current Assets'],
    'CurrentLiabilities':  ['Current Liabilities'],
    'CashAndEquivalents':  ['Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments'],
}

CASHFLOW_FIELDS = {
    'OperatingCashFlow':    ['Operating Cash Flow', 'Cash Flow From Continuing Operating Activities'],
    'FreeCashFlow':         ['Free Cash Flow'],
    'CashDividendsPaid':    ['Cash Dividends Paid', 'Common Stock Dividend Paid'],
    'RepurchaseOfStock':    ['Repurchase Of Capital Stock', 'Common Stock Payments'],
    'IssuanceOfStock':      ['Issuance Of Capital Stock', 'Common Stock Issuance'],
    'IssuanceOfDebt':       ['Issuance Of Debt', 'Long Term Debt Issuance'],
    'RepaymentOfDebt':      ['Repayment Of Debt', 'Long Term Debt Payments'],
    'CapitalExpenditure':   ['Capital Expenditure', 'Capital Expenditures'],
}

ALL_GROUPS = {
    'Income': INCOME_FIELDS,
    'Balance Sheet': BALANCE_FIELDS,
    'Cash Flow': CASHFLOW_FIELDS,
}


# ================================================================
# 3. 추출 헬퍼
# ================================================================
def extract_field(df: pd.DataFrame, candidates: list) -> dict:
    """
    DataFrame에서 candidates 중 첫 번째로 매칭되는 row 추출.
    yfinance: index=항목명, columns=각 회계연도(Timestamp)
    반환: {'matched_label': str|None, 'years': [str], 'values': [float]}
    """
    if df is None or df.empty:
        return {'matched_label': None, 'years': [], 'values': []}

    for label in candidates:
        if label in df.index:
            row = df.loc[label]
            # NaN 제거 후 최근 → 과거 순으로
            if isinstance(row, pd.Series):
                row = row.dropna()
                years = [str(c.date()) if hasattr(c, 'date') else str(c) for c in row.index]
                values = [float(v) for v in row.values]
                return {'matched_label': label, 'years': years, 'values': values}
    return {'matched_label': None, 'years': [], 'values': []}


# ================================================================
# 4. 메인
# ================================================================
def main():
    print("=" * 70)
    print("yfinance financials/balance_sheet/cashflow 보조 테스트")
    print(f"yfinance version: {yf.__version__}")
    print("=" * 70)

    results = {}
    errors = {}
    start = time.time()

    for ticker, sector in SAMPLES:
        t_start = time.time()
        print(f"\n[{sector:22s}] {ticker} 추출 중...", end=' ')
        try:
            t = yf.Ticker(ticker)
            income_df = t.financials
            balance_df = t.balance_sheet
            cashflow_df = t.cashflow

            row = {
                'sector': sector,
                'income_periods': len(income_df.columns) if income_df is not None else 0,
                'balance_periods': len(balance_df.columns) if balance_df is not None else 0,
                'cashflow_periods': len(cashflow_df.columns) if cashflow_df is not None else 0,
                'income': {k: extract_field(income_df, v) for k, v in INCOME_FIELDS.items()},
                'balance': {k: extract_field(balance_df, v) for k, v in BALANCE_FIELDS.items()},
                'cashflow': {k: extract_field(cashflow_df, v) for k, v in CASHFLOW_FIELDS.items()},
            }
            results[ticker] = row

            elapsed = time.time() - t_start
            # 핵심 항목 즉시 출력
            rev = row['income'].get('Revenue', {})
            div = row['cashflow'].get('CashDividendsPaid', {})
            buy = row['cashflow'].get('RepurchaseOfStock', {})
            rev_val = rev['values'][0] if rev.get('values') else None
            div_val = div['values'][0] if div.get('values') else None
            buy_val = buy['values'][0] if buy.get('values') else None
            rev_str = f"{rev_val/1e9:.1f}B" if rev_val else "N/A"
            div_str = f"{div_val/1e9:.2f}B" if div_val else "N/A"
            buy_str = f"{buy_val/1e9:.2f}B" if buy_val else "N/A"
            print(f"({elapsed:.1f}s) Rev={rev_str:>7s} Div={div_str:>7s} Buyback={buy_str:>7s}")
        except Exception as e:
            errors[ticker] = f"{type(e).__name__}: {str(e)[:120]}"
            print(f"ERROR: {errors[ticker]}")
        time.sleep(0.5)  # rate limit safety

    total = time.time() - start
    print(f"\n총 소요: {total:.1f}s | 성공 {len(results)}/{len(SAMPLES)}, 에러 {len(errors)}")

    # ============================================================
    # 5. 항목별 커버리지
    # ============================================================
    print("\n" + "=" * 70)
    print("항목별 커버리지 (matched_label 잡힌 종목 비율)")
    print("=" * 70)

    coverage_rows = []
    for group, fields in ALL_GROUPS.items():
        print(f"\n[{group}]")
        group_key = {'Income': 'income', 'Balance Sheet': 'balance', 'Cash Flow': 'cashflow'}[group]
        for field in fields:
            cnt = 0
            avg_periods = []
            for tk, r in results.items():
                f = r[group_key].get(field, {})
                if f.get('matched_label'):
                    cnt += 1
                    avg_periods.append(len(f.get('values', [])))
            pct = cnt / len(results) * 100 if results else 0
            avg_p = sum(avg_periods) / len(avg_periods) if avg_periods else 0
            marker = '✓' if pct >= 80 else ('△' if pct >= 50 else '✗')
            print(f"  {marker} {field:25s} {pct:5.1f}%  (avg {avg_p:.1f} 연도 데이터)")
            coverage_rows.append({
                'group': group,
                'field': field,
                'coverage_pct': round(pct, 1),
                'success_count': cnt,
                'total': len(results),
                'avg_years_available': round(avg_p, 1),
            })

    # CSV
    cov_df = pd.DataFrame(coverage_rows)
    cov_df.to_csv('test_yf_financials_summary.csv', index=False, encoding='utf-8-sig')
    print(f"\n커버리지 CSV: test_yf_financials_summary.csv")

    # JSON
    out = {
        'meta': {
            'yfinance_version': yf.__version__,
            'sample_count': len(SAMPLES),
            'success_count': len(results),
            'error_count': len(errors),
            'total_elapsed_sec': round(total, 2),
        },
        'results': results,
        'errors': errors,
    }
    out_path = Path(__file__).parent / 'test_yf_financials_result.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, default=str, ensure_ascii=False)
    print(f"Raw 결과 JSON: {out_path}")

    print("\n" + "=" * 70)
    print("완료. 두 파일을 채팅에 첨부해 주세요:")
    print("  1) test_yf_financials_summary.csv")
    print("  2) test_yf_financials_result.json")
    print("=" * 70)


if __name__ == '__main__':
    main()
