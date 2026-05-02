"""
PHASE2 Fundamental — yfinance Ticker.info 필드 커버리지 테스트
================================================================

목적:
  Global PHASE2 펀더멘탈 스크리닝에 필요한 forward·trailing·주주환원·
  재무건전성 필드들이 yfinance에서 얼마나 안정적으로 잡히는지 실측한다.

샘플 종목 (14개):
  GICS 11섹터 대형주 1개씩 + 중형주 2개 + 소형주 1개 = 14
  ADR은 PHASE2에서 제외하기로 했으므로 본 테스트에선 제외

실행 방법:
    pip install yfinance==1.3.0 pandas
    python test_yf_forward.py

산출물 (같은 폴더에 저장):
  - test_yf_forward_result.json   : 종목별 raw 필드값
  - test_yf_forward_summary.csv   : 필드별 커버리지 (% non-null)
  - 콘솔 출력으로도 핵심 요약 표시

소요 시간 예상: ~30초 (14종목 × ~2초)
"""

import yfinance as yf
import pandas as pd
import json
import time
from pathlib import Path

# ================================================================
# 1. 샘플 종목 (GICS 11섹터 + 시총 다양성)
# ================================================================
SAMPLES = {
    # 섹터: [ticker, ...] (대표 1~2개)
    'IT (Large)':            ['AAPL'],
    'IT (Mid)':              ['ANET'],
    'Financial':             ['JPM'],
    'Healthcare':            ['UNH'],
    'Cons Discretionary':    ['AMZN'],
    'Cons Staples':          ['PG'],
    'Energy':                ['XOM'],
    'Industrials':           ['CAT'],
    'Materials':             ['LIN'],
    'Utilities':             ['NEE'],
    'Real Estate':           ['PLD'],
    'Comm Services':         ['GOOGL'],
    'Mid Cap':               ['CROX'],   # 의류 중형주
    'Small Cap':             ['UPST'],   # 핀테크 소형주
}

# ================================================================
# 2. 평가할 필드 (PHASE2 스코어링 카테고리별 매핑)
# ================================================================
FIELD_GROUPS = {
    'Forward Valuation': [
        'forwardPE', 'forwardEps', 'pegRatio', 'trailingPegRatio',
    ],
    'Trailing Valuation (fallback)': [
        'trailingPE', 'trailingEps', 'priceToBook', 'priceToSalesTrailing12Months',
    ],
    'Forward Growth (target)': [
        'earningsGrowth', 'revenueGrowth',
        'earningsQuarterlyGrowth', 'revenueQuarterlyGrowth',
    ],
    'Profitability (참고)': [
        'profitMargins', 'operatingMargins', 'returnOnEquity', 'returnOnAssets',
        'grossMargins',
    ],
    'Shareholder Return': [
        'dividendYield', 'dividendRate', 'payoutRatio',
        'fiveYearAvgDividendYield', 'lastDividendValue',
    ],
    'Financial Health (필터용)': [
        'debtToEquity', 'currentRatio', 'quickRatio',
        'totalCash', 'totalDebt', 'totalRevenue', 'ebitda',
    ],
    'Capital Structure': [
        'sharesOutstanding', 'floatShares', 'sharesShort',
        'marketCap', 'enterpriseValue',
    ],
    'Meta': [
        'sector', 'industry', 'country', 'currency', 'exchange',
    ],
}

ALL_FIELDS = [f for fields in FIELD_GROUPS.values() for f in fields]

# ================================================================
# 3. 테스트 실행
# ================================================================
def main():
    print("=" * 70)
    print("yfinance Ticker.info 필드 커버리지 테스트")
    print(f"yfinance version: {yf.__version__}")
    print("=" * 70)

    all_tickers = []
    for cat, tks in SAMPLES.items():
        all_tickers.extend(tks)
    print(f"\n샘플: {len(all_tickers)} 종목, {len(ALL_FIELDS)} 필드 검사\n")

    results = {}
    errors = {}
    elapsed_per_ticker = {}
    start = time.time()

    for cat, tks in SAMPLES.items():
        for tk in tks:
            t_start = time.time()
            try:
                t = yf.Ticker(tk)
                info = t.info or {}
                row = {f: info.get(f) for f in ALL_FIELDS}
                results[tk] = {'category': cat, **row}
                elapsed_per_ticker[tk] = time.time() - t_start
                # 핵심 필드 4개 즉시 출력
                fpe = info.get('forwardPE')
                feps = info.get('forwardEps')
                eg = info.get('earningsGrowth')
                rg = info.get('revenueGrowth')
                print(f"  [{cat:22s}] {tk:6s} fwdPE={fpe!s:>8s} fwdEps={feps!s:>8s} "
                      f"earnG={eg!s:>8s} revG={rg!s:>8s}  ({elapsed_per_ticker[tk]:.1f}s)")
            except Exception as e:
                errors[tk] = f"{type(e).__name__}: {str(e)[:120]}"
                print(f"  [{cat:22s}] {tk:6s} ERROR: {errors[tk]}")
            time.sleep(0.5)  # rate limit safety

    total_elapsed = time.time() - start
    print(f"\n총 소요: {total_elapsed:.1f}s | 성공 {len(results)}/{len(all_tickers)}, 에러 {len(errors)}")

    # ============================================================
    # 4. 필드별 커버리지 계산
    # ============================================================
    if results:
        df = pd.DataFrame(results).T
        print("\n" + "=" * 70)
        print("필드별 커버리지 (% non-null, 비-제로)")
        print("=" * 70)

        coverage_rows = []
        for group, fields in FIELD_GROUPS.items():
            print(f"\n[{group}]")
            for f in fields:
                if f not in df.columns:
                    continue
                col = df[f]
                non_null = col.notna() & (col != '') & (col != 0)
                pct = non_null.sum() / len(df) * 100
                marker = '✓' if pct >= 80 else ('△' if pct >= 50 else '✗')
                print(f"  {marker} {f:40s} {pct:5.1f}%")
                coverage_rows.append({
                    'group': group, 'field': f,
                    'coverage_pct': round(pct, 1),
                    'non_null_count': int(non_null.sum()),
                    'total': len(df),
                })

        cov_df = pd.DataFrame(coverage_rows)
        cov_df.to_csv('test_yf_forward_summary.csv', index=False, encoding='utf-8-sig')
        print(f"\n커버리지 CSV: test_yf_forward_summary.csv")

    # ============================================================
    # 5. JSON 저장 (raw)
    # ============================================================
    out = {
        'meta': {
            'yfinance_version': yf.__version__,
            'sample_count': len(all_tickers),
            'success_count': len(results),
            'error_count': len(errors),
            'total_elapsed_sec': round(total_elapsed, 2),
            'avg_per_ticker_sec': round(sum(elapsed_per_ticker.values()) / max(len(elapsed_per_ticker), 1), 2),
        },
        'results': results,
        'errors': errors,
    }
    out_path = Path(__file__).parent / 'test_yf_forward_result.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, default=str, ensure_ascii=False)
    print(f"Raw 결과 JSON: {out_path}")

    print("\n" + "=" * 70)
    print("완료. 두 파일을 채팅에 첨부하거나 내용 붙여넣어 주세요:")
    print("  1) test_yf_forward_summary.csv  (필드별 커버리지)")
    print("  2) test_yf_forward_result.json  (raw 데이터)")
    print("=" * 70)


if __name__ == '__main__':
    main()
