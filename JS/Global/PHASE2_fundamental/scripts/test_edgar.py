"""
PHASE2 Fundamental — edgartools 재무제표 추출 테스트
================================================================

목적:
  Global PHASE2에서 SEC EDGAR 직접 파싱으로 재무제표 데이터를 가져올 수
  있는지 실측. 다음 핵심 필드가 추출되는지 확인:
    - 손익: Revenue, OperatingIncome, NetIncome, InterestExpense
    - 재무상태: StockholdersEquity, TotalDebt, CurrentAssets, CurrentLiabilities
    - 현금흐름: PaymentsOfDividends, PaymentsForRepurchaseOfCommonStock
    - 부수: SharesOutstanding

샘플 (7개): GICS 섹터 다양성 + 회계 복잡도 차이
  AAPL(IT), JPM(금융), UNH(헬스), XOM(에너지), CAT(산업), NEE(유틸), PG(생필)

실행 방법:
    pip install edgartools pandas
    # 처음 실행 시 SEC 정책에 따라 User-Agent 필요. 본인 이메일로 교체:
    export EDGAR_IDENTITY="홍길동 hong@example.com"
    python test_edgar.py

산출물 (같은 폴더에 저장):
  - test_edgar_result.json   : 종목별 추출된 재무 필드
  - test_edgar_summary.csv   : 필드별 추출 성공률
  - 콘솔로 핵심 요약 표시

소요 시간 예상: 1~2분 (7종목 × 10-K 1건 다운로드/파싱)
"""

import os
import json
import time
from pathlib import Path

# ----------------------------------------------------------------
# SEC EDGAR 정책: User-Agent로 신원 명시 의무 (이름 + 이메일)
# ----------------------------------------------------------------
EDGAR_IDENTITY = os.environ.get('EDGAR_IDENTITY', 'JS Investment limited8090@gmail.com')

# edgartools API
from edgar import set_identity, Company
set_identity(EDGAR_IDENTITY)

import pandas as pd

# ================================================================
# 1. 샘플 (섹터 다양성)
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

# ================================================================
# 2. 추출 시도할 GAAP 컨셉 (US GAAP 표준 태그 후보 다수)
#    edgartools가 제공하는 statement 객체에서 매핑되는 이름들
# ================================================================
TARGET_FIELDS = {
    # Income Statement
    'Revenue':           ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'],
    'OperatingIncome':   ['OperatingIncomeLoss'],
    'NetIncome':         ['NetIncomeLoss'],
    'InterestExpense':   ['InterestExpense'],
    'EPS_Basic':         ['EarningsPerShareBasic'],
    'EPS_Diluted':       ['EarningsPerShareDiluted'],

    # Balance Sheet
    'StockholdersEquity': ['StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],
    'TotalAssets':        ['Assets'],
    'TotalLiabilities':   ['Liabilities'],
    'LongTermDebt':       ['LongTermDebt', 'LongTermDebtNoncurrent'],
    'CurrentAssets':      ['AssetsCurrent'],
    'CurrentLiabilities': ['LiabilitiesCurrent'],

    # Cash Flow (주주환원 핵심)
    'DividendsPaid':       ['PaymentsOfDividends', 'PaymentsOfDividendsCommonStock'],
    'StockRepurchase':     ['PaymentsForRepurchaseOfCommonStock', 'PaymentsForRepurchaseOfEquity'],
    'OperatingCashFlow':   ['NetCashProvidedByUsedInOperatingActivities'],

    # Share count
    'SharesOutstanding':   ['CommonStockSharesOutstanding', 'WeightedAverageNumberOfSharesOutstandingBasic'],
}

# ================================================================
# 3. edgartools에서 재무 필드 추출 (다중 전략)
# ================================================================
def extract_company_facts(ticker: str) -> dict:
    """
    edgartools의 Company.get_facts() (XBRL companyfacts API) 사용.
    반환: {field_name: {'value': ..., 'period': ..., 'unit': ..., 'tag': ..., 'fy': ...}, ...}
    """
    out = {}
    try:
        company = Company(ticker)
    except Exception as e:
        return {'_error': f"Company({ticker}) 생성 실패: {type(e).__name__}: {e}"}

    # 1) get_facts() — 가장 광범위한 데이터 (XBRL Frames)
    try:
        facts = company.get_facts()
        if facts is None:
            return {'_error': 'get_facts() returned None'}

        # facts: XBRL Frames 형태 — 다양한 컨셉을 한 번에 제공
        # edgartools 5.x: facts 객체에는 to_pandas() 또는 list of facts
        # 가장 안전한 접근: 컨셉 직접 조회
        for field, candidates in TARGET_FIELDS.items():
            for tag in candidates:
                try:
                    # company.facts.fact(tag) 또는 facts.query() 시도
                    # edgartools 5.x: facts.query() / facts.to_pandas() / facts.pivot()
                    if hasattr(facts, 'query'):
                        df = facts.query(tag)  # tag 필터
                        if df is not None and len(df) > 0:
                            # 가장 최근 연간 (fp='FY') 값
                            df_fy = df[df.get('fp', '') == 'FY'] if 'fp' in df.columns else df
                            if len(df_fy) > 0:
                                latest = df_fy.sort_values('end').iloc[-1]
                                out[field] = {
                                    'value': float(latest.get('val', latest.get('value', 0))),
                                    'period_end': str(latest.get('end', '')),
                                    'fy': int(latest.get('fy', 0)) if 'fy' in latest else None,
                                    'tag': tag,
                                    'unit': str(latest.get('unit', '')),
                                }
                                break
                except Exception:
                    continue
    except Exception as e:
        out['_facts_error'] = f"{type(e).__name__}: {str(e)[:120]}"

    # 2) Fallback: latest 10-K의 financials 객체 사용
    if not any(k for k in out if not k.startswith('_')):
        try:
            filings = company.get_filings(form='10-K').head(1)
            if len(filings) > 0:
                filing = filings[0]
                fin = filing.obj()  # TenK object
                if hasattr(fin, 'financials') and fin.financials is not None:
                    # fin.financials.income_statement / balance_sheet / cash_flow_statement
                    out['_filing_used'] = str(filing.accession_no)
                    out['_filing_date'] = str(filing.filing_date)
        except Exception as e:
            out['_filing_error'] = f"{type(e).__name__}: {str(e)[:120]}"

    return out


# ================================================================
# 4. 메인
# ================================================================
def main():
    print("=" * 70)
    print("edgartools 재무제표 추출 테스트")
    try:
        import edgar
        print(f"edgartools version: {edgar.__version__ if hasattr(edgar, '__version__') else 'unknown'}")
    except Exception:
        pass
    print(f"EDGAR_IDENTITY: {EDGAR_IDENTITY}")
    print("=" * 70)

    results = {}
    errors = {}
    start = time.time()

    for ticker, sector in SAMPLES:
        print(f"\n[{sector:14s}] {ticker} 추출 중...")
        t_start = time.time()
        try:
            data = extract_company_facts(ticker)
            elapsed = time.time() - t_start
            results[ticker] = {'sector': sector, 'elapsed_sec': round(elapsed, 1), **data}

            # 추출된 필드 요약
            extracted = [k for k in data if not k.startswith('_')]
            failed_keys = [k for k in TARGET_FIELDS if k not in extracted]
            print(f"   ✓ 추출: {len(extracted)}/{len(TARGET_FIELDS)} ({elapsed:.1f}s)")
            if extracted:
                # Revenue 샘플 확인
                if 'Revenue' in data:
                    v = data['Revenue']
                    print(f"   ex) Revenue = {v['value']:,.0f} (FY{v.get('fy')}, tag={v.get('tag')})")
                if 'DividendsPaid' in data:
                    v = data['DividendsPaid']
                    print(f"   ex) DividendsPaid = {v['value']:,.0f} (FY{v.get('fy')})")
            if failed_keys:
                print(f"   ✗ 누락: {', '.join(failed_keys[:6])}{'...' if len(failed_keys) > 6 else ''}")

        except Exception as e:
            errors[ticker] = f"{type(e).__name__}: {str(e)[:200]}"
            print(f"   ERROR: {errors[ticker]}")

        time.sleep(0.5)  # SEC EDGAR rate limit (10 req/sec 한도)

    total = time.time() - start
    print(f"\n총 소요: {total:.1f}s | 성공 {len(results)}/{len(SAMPLES)}, 에러 {len(errors)}")

    # ============================================================
    # 5. 필드별 추출 성공률
    # ============================================================
    coverage = {}
    for field in TARGET_FIELDS:
        cnt = sum(1 for r in results.values() if field in r)
        coverage[field] = {
            'success_count': cnt,
            'total': len(SAMPLES),
            'pct': round(cnt / len(SAMPLES) * 100, 1) if SAMPLES else 0,
        }

    print("\n" + "=" * 70)
    print("필드별 추출 성공률")
    print("=" * 70)
    for field, c in coverage.items():
        marker = '✓' if c['pct'] >= 80 else ('△' if c['pct'] >= 50 else '✗')
        print(f"  {marker} {field:25s} {c['pct']:5.1f}% ({c['success_count']}/{c['total']})")

    # CSV
    cov_df = pd.DataFrame([{'field': k, **v} for k, v in coverage.items()])
    cov_df.to_csv('test_edgar_summary.csv', index=False, encoding='utf-8-sig')
    print(f"\n커버리지 CSV: test_edgar_summary.csv")

    # JSON
    out = {
        'meta': {
            'edgar_identity': EDGAR_IDENTITY,
            'sample_count': len(SAMPLES),
            'success_count': len(results),
            'error_count': len(errors),
            'total_elapsed_sec': round(total, 2),
        },
        'coverage': coverage,
        'results': results,
        'errors': errors,
    }
    out_path = Path(__file__).parent / 'test_edgar_result.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, default=str, ensure_ascii=False)
    print(f"Raw 결과 JSON: {out_path}")

    print("\n" + "=" * 70)
    print("완료. 두 파일을 채팅에 첨부하거나 내용 붙여넣어 주세요:")
    print("  1) test_edgar_summary.csv  (필드별 추출률)")
    print("  2) test_edgar_result.json  (raw 데이터)")
    print("=" * 70)


if __name__ == '__main__':
    main()
