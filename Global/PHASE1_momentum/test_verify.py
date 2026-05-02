"""
PHASE1 Global Momentum - 결과 검증
- 데이터 캐시 무결성
- 백테스트 로직 스팟체크 (수동 계산과 비교)
- 결과 합리성 (이상치, 분포)
- 랭킹 정합성

실행: python test_verify.py
"""

import os
import sys
import pickle
import numpy as np
import pandas as pd
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SCRIPT_DIR, 'cache')
RESULTS_DIR = os.path.join(SCRIPT_DIR, 'results')
MASTER_XLSX = os.path.join(SCRIPT_DIR, '..', 'PHASE0_classification', '20260501_classification_master.xlsx')

passed = 0
failed = 0
warnings = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  ✅ {name}")
        passed += 1
    else:
        print(f"  ❌ {name} — {detail}")
        failed += 1


def warn(name, detail=""):
    global warnings
    print(f"  ⚠️ {name} — {detail}")
    warnings += 1


# ============================================================
# 1. 캐시 무결성
# ============================================================
print("=" * 60)
print("1. 캐시 무결성")
print("=" * 60)

daily_path = os.path.join(CACHE_DIR, 'daily_cache.pkl')
weekly_path = os.path.join(CACHE_DIR, 'weekly_cache.pkl')

check("daily_cache.pkl 존재", os.path.exists(daily_path))
check("weekly_cache.pkl 존재", os.path.exists(weekly_path))

with open(daily_path, 'rb') as f:
    daily_cache = pickle.load(f)
with open(weekly_path, 'rb') as f:
    weekly_cache = pickle.load(f)

check("Daily 종목 수 >= 2200", len(daily_cache) >= 2200, f"실제: {len(daily_cache)}")
check("Weekly 종목 수 >= 2200", len(weekly_cache) >= 2200, f"실제: {len(weekly_cache)}")
check("Daily == Weekly 종목 수", len(daily_cache) == len(weekly_cache),
      f"daily={len(daily_cache)}, weekly={len(weekly_cache)}")

# 마스터 대비 누락 체크
master_df = pd.read_excel(MASTER_XLSX, sheet_name='전체종목')
master_tickers = set(master_df['Symbol'].tolist())
cache_tickers = set(daily_cache.keys())
missing = master_tickers - cache_tickers
check("마스터 대비 누락 <= 5", len(missing) <= 5, f"누락: {len(missing)}종목 {list(missing)[:10]}")

# 필수 종목 존재
must_have = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'TSM', 'BRK-B', 'JPM']
for ticker in must_have:
    check(f"필수 종목 {ticker} 캐시 존재", ticker in daily_cache)

# 데이터 기간 체크
print("\n  [데이터 기간 분포]")
lengths = {tk: len(df) for tk, df in daily_cache.items()}
print(f"  최소: {min(lengths.values())}일, 최대: {max(lengths.values())}일, "
      f"중앙값: {np.median(list(lengths.values())):.0f}일")

check("AAPL 10년 데이터 >= 2000일", lengths.get('AAPL', 0) >= 2000,
      f"실제: {lengths.get('AAPL', 0)}")

# OHLCV 컬럼 체크
sample_ticker = 'AAPL'
sample_df = daily_cache[sample_ticker]
required_cols = {'Open', 'High', 'Low', 'Close', 'Volume'}
actual_cols = set(sample_df.columns)
check("OHLCV 컬럼 존재", required_cols.issubset(actual_cols),
      f"있는 컬럼: {actual_cols}, 필요: {required_cols - actual_cols}")

# 가격 합리성
aapl_close = daily_cache['AAPL']['Close']
check("AAPL 최근가 > $100", aapl_close.iloc[-1] > 100, f"실제: ${aapl_close.iloc[-1]:.2f}")
check("AAPL 최근가 < $1000", aapl_close.iloc[-1] < 1000, f"실제: ${aapl_close.iloc[-1]:.2f}")

# 주간 리샘플링 체크
aapl_weekly = weekly_cache['AAPL']
daily_weeks = len(daily_cache['AAPL']) / 5
check("Weekly 행 수 합리적", abs(len(aapl_weekly) - daily_weeks) < daily_weeks * 0.1,
      f"weekly={len(aapl_weekly)}, 예상≈{daily_weeks:.0f}")

# ============================================================
# 2. 백테스트 결과 로드 및 구조 체크
# ============================================================
print("\n" + "=" * 60)
print("2. 백테스트 결과 구조")
print("=" * 60)

xlsx_files = sorted([f for f in os.listdir(RESULTS_DIR) if f.endswith('_momentum_backtest.xlsx')])
check("백테스트 Excel 존재", len(xlsx_files) > 0)

bt_path = os.path.join(RESULTS_DIR, xlsx_files[-1])
xls = pd.ExcelFile(bt_path)
sheets = {name: pd.read_excel(xls, sheet_name=name) for name in xls.sheet_names}

# 예상 시트: 4지표 × 4기간 × 2프레임 = 32 (단, HIGH52_Daily_1Y는 없을 수 있음)
check("시트 수 >= 28", len(sheets) >= 28, f"실제: {len(sheets)}")

# 필수 시트 존재
for ind in ['DD', 'MACD', 'RSI']:
    for frame in ['Daily', 'Weekly']:
        for period in ['1Y', '3Y', '5Y', '10Y']:
            key = f'{ind}_{frame}_{period}'
            check(f"시트 {key} 존재", key in sheets, f"없음")

# HIGH52는 1Y에서 없을 수 있음
check("HIGH52_Daily_3Y 존재", 'HIGH52_Daily_3Y' in sheets)

# 각 시트 종목 수 합리성
for key, df in sheets.items():
    if len(df) < 100:
        warn(f"{key} 종목 수 적음", f"{len(df)}종목")

# ============================================================
# 3. 백테스트 로직 스팟체크 (MACD 수동 검증)
# ============================================================
print("\n" + "=" * 60)
print("3. MACD 로직 스팟체크 (AAPL, Daily 1Y)")
print("=" * 60)

c = 0.0002
aapl_prices = daily_cache['AAPL']['Close'].tail(252)

ema12 = aapl_prices.ewm(span=12, adjust=False).mean()
ema26 = aapl_prices.ewm(span=26, adjust=False).mean()
macd_line = ema12 - ema26
signal = macd_line.ewm(span=9, adjust=False).mean()
hist = macd_line - signal

trades = []
in_pos = False
entry_p = 0
for t in range(1, len(hist)):
    if not in_pos and hist.iloc[t-1] <= 0 and hist.iloc[t] > 0:
        entry_p = aapl_prices.iloc[t]
        in_pos = True
    elif in_pos and hist.iloc[t-1] >= 0 and hist.iloc[t] < 0:
        exit_p = aapl_prices.iloc[t]
        trades.append(np.log(exit_p / entry_p) - 2*c)
        in_pos = False
if in_pos:
    trades.append(np.log(aapl_prices.iloc[-1] / entry_p) - 2*c)

manual_cr = sum(trades)
manual_wr = sum(1 for t in trades if t > 0) / len(trades) if trades else 0
manual_n = len(trades)

print(f"  수동 계산: CR={manual_cr:.4f}, WR={manual_wr:.1%}, N={manual_n}")

# 백테스트 결과에서 AAPL 찾기
macd_1y = sheets.get('MACD_Daily_1Y', pd.DataFrame())
aapl_bt = macd_1y[macd_1y['Symbol'] == 'AAPL']
if len(aapl_bt) > 0:
    bt_cr = aapl_bt.iloc[0]['cum_return']
    bt_wr = aapl_bt.iloc[0]['win_rate']
    bt_n = aapl_bt.iloc[0]['n_trades']
    print(f"  백테스트:   CR={bt_cr:.4f}, WR={bt_wr:.1%}, N={int(bt_n)}")

    check("MACD CR 오차 < 1%", abs(manual_cr - bt_cr) < 0.01,
          f"수동={manual_cr:.4f}, 백테스트={bt_cr:.4f}")
    check("MACD 거래 횟수 일치", manual_n == int(bt_n),
          f"수동={manual_n}, 백테스트={int(bt_n)}")
else:
    warn("AAPL MACD 결과 없음")

# ============================================================
# 4. DD 로직 스팟체크 (Calmar Ratio)
# ============================================================
print("\n" + "=" * 60)
print("4. DD 로직 스팟체크 (AAPL, Daily 1Y)")
print("=" * 60)

prices = daily_cache['AAPL']['Close'].tail(252).values
n_years = len(prices) / 252
total_ret = prices[-1] / prices[0]
ann_ret = total_ret ** (1/n_years) - 1
running_peak = np.maximum.accumulate(prices)
dd = (running_peak - prices) / running_peak
mdd = dd.max()
manual_calmar = ann_ret / mdd if mdd > 0 else float('nan')

print(f"  수동: ann_ret={ann_ret:.4f}, MDD={mdd:.4f}, Calmar={manual_calmar:.4f}")

dd_1y = sheets.get('DD_Daily_1Y', pd.DataFrame())
aapl_dd = dd_1y[dd_1y['Symbol'] == 'AAPL']
if len(aapl_dd) > 0:
    bt_calmar = aapl_dd.iloc[0]['calmar_ratio']
    bt_mdd = aapl_dd.iloc[0]['mdd']
    print(f"  백테스트: MDD={bt_mdd:.4f}, Calmar={bt_calmar:.4f}")

    check("Calmar 오차 < 5%", abs(manual_calmar - bt_calmar) / max(abs(manual_calmar), 0.001) < 0.05,
          f"수동={manual_calmar:.4f}, 백테스트={bt_calmar:.4f}")
    check("MDD 오차 < 1%", abs(mdd - bt_mdd) < 0.01,
          f"수동={mdd:.4f}, 백테스트={bt_mdd:.4f}")
else:
    warn("AAPL DD 결과 없음")

# ============================================================
# 5. 결과 합리성 (이상치 탐지)
# ============================================================
print("\n" + "=" * 60)
print("5. 결과 합리성")
print("=" * 60)

# Calmar 이상치
dd_daily_1y = sheets.get('DD_Daily_1Y', pd.DataFrame())
if 'calmar_ratio' in dd_daily_1y.columns:
    extreme_calmar = dd_daily_1y[dd_daily_1y['calmar_ratio'].abs() > 500]
    if len(extreme_calmar) > 0:
        warn(f"Calmar > 500인 종목: {len(extreme_calmar)}개",
             f"{extreme_calmar['Symbol'].tolist()[:5]}")
    else:
        check("Calmar 이상치 없음 (|Calmar| <= 500)", True)

# MACD 누적수익률 분포
macd_daily_1y = sheets.get('MACD_Daily_1Y', pd.DataFrame())
if 'cum_return' in macd_daily_1y.columns:
    cr_vals = macd_daily_1y['cum_return']
    print(f"  MACD CR 분포: min={cr_vals.min():.3f}, max={cr_vals.max():.3f}, "
          f"mean={cr_vals.mean():.3f}, median={cr_vals.median():.3f}")

    extreme_macd = macd_daily_1y[macd_daily_1y['cum_return'].abs() > 5]
    if len(extreme_macd) > 0:
        warn(f"MACD CR > 5인 종목: {len(extreme_macd)}개",
             f"{extreme_macd['Symbol'].tolist()[:5]}")
    else:
        check("MACD CR 이상치 없음 (|CR| <= 5)", True)

# 거래 횟수 0인 종목
if 'n_trades' in macd_daily_1y.columns:
    zero_trades = macd_daily_1y[macd_daily_1y['n_trades'] == 0]
    pct_zero = len(zero_trades) / len(macd_daily_1y) * 100 if len(macd_daily_1y) > 0 else 0
    check("MACD 거래 0회 비율 < 30%", pct_zero < 30,
          f"{pct_zero:.1f}% ({len(zero_trades)}/{len(macd_daily_1y)})")

# 승률 분포
if 'win_rate' in macd_daily_1y.columns:
    wr_100 = (macd_daily_1y['win_rate'] == 1.0).sum()
    wr_0 = (macd_daily_1y['win_rate'] == 0.0).sum()
    traded = macd_daily_1y[macd_daily_1y['n_trades'] > 0]
    print(f"  승률 100%: {wr_100}종목, 승률 0%: {wr_0}종목 (거래 있는 종목: {len(traded)})")

# ============================================================
# 6. 기간별 일관성
# ============================================================
print("\n" + "=" * 60)
print("6. 기간별 일관성")
print("=" * 60)

# 같은 지표의 1Y vs 3Y: 종목 수가 비슷해야 함
for ind in ['MACD', 'RSI']:
    key_1y = f'{ind}_Daily_1Y'
    key_3y = f'{ind}_Daily_3Y'
    if key_1y in sheets and key_3y in sheets:
        n1 = len(sheets[key_1y])
        n3 = len(sheets[key_3y])
        check(f"{ind} Daily 1Y≈3Y 종목수", abs(n1 - n3) < 200,
              f"1Y={n1}, 3Y={n3}")

# DD의 기간별 Calmar: 같은 종목이면 기간마다 달라야 함 (같으면 버그)
if 'DD_Daily_1Y' in sheets and 'DD_Daily_3Y' in sheets:
    dd1y = sheets['DD_Daily_1Y'].set_index('Symbol')
    dd3y = sheets['DD_Daily_3Y'].set_index('Symbol')
    common = dd1y.index.intersection(dd3y.index)
    if len(common) > 10:
        same_count = 0
        for sym in common[:100]:
            c1 = dd1y.loc[sym, 'calmar_ratio'] if sym in dd1y.index else None
            c3 = dd3y.loc[sym, 'calmar_ratio'] if sym in dd3y.index else None
            if c1 is not None and c3 is not None and abs(c1 - c3) < 0.001:
                same_count += 1
        pct_same = same_count / min(100, len(common)) * 100
        check("DD Calmar 1Y vs 3Y 차이 존재 (>50%)", pct_same < 50,
              f"{pct_same:.0f}%가 1Y==3Y (기간 슬라이싱 버그 가능)")

# ============================================================
# 7. 랭킹 결과 체크
# ============================================================
print("\n" + "=" * 60)
print("7. 랭킹 결과")
print("=" * 60)

ranking_files = sorted([f for f in os.listdir(RESULTS_DIR) if f.endswith('_momentum_ranking.xlsx')])
check("랭킹 Excel 존재", len(ranking_files) > 0)

if ranking_files:
    rk_path = os.path.join(RESULTS_DIR, ranking_files[-1])
    rk_xls = pd.ExcelFile(rk_path)

    # Top20 시트 존재
    for ind in ['DD', 'MACD', 'RSI', 'HIGH52']:
        sheet_name = f'Top20_{ind}'
        check(f"랭킹 {sheet_name} 존재", sheet_name in rk_xls.sheet_names)

    # 섹터 Top3 시트 존재
    for ind in ['DD', 'MACD', 'RSI', 'HIGH52']:
        sheet_name = f'Sector_Top3_{ind}'
        check(f"랭킹 {sheet_name} 존재", sheet_name in rk_xls.sheet_names)

    # 복합 모멘텀
    check("복합 모멘텀 시트 존재", 'Composite_Momentum' in rk_xls.sheet_names)

    # Top20에 실제 20종목 있는지
    if 'Top20_MACD' in rk_xls.sheet_names:
        top20_macd = pd.read_excel(rk_xls, sheet_name='Top20_MACD')
        check("Top20_MACD 종목 수 == 20", len(top20_macd) == 20,
              f"실제: {len(top20_macd)}")

    # 섹터 Top3에 11개 섹터 있는지
    if 'Sector_Top3_MACD' in rk_xls.sheet_names:
        sec_top3 = pd.read_excel(rk_xls, sheet_name='Sector_Top3_MACD')
        n_sectors = sec_top3['GICS_Sector'].nunique()
        check("섹터 Top3 MACD 섹터 수 >= 10", n_sectors >= 10,
              f"실제: {n_sectors}섹터")

# ============================================================
# 8. 차트 파일 체크
# ============================================================
print("\n" + "=" * 60)
print("8. 차트 파일")
print("=" * 60)

charts_dir = os.path.join(SCRIPT_DIR, 'charts')
if os.path.exists(charts_dir):
    chart_files = [f for f in os.listdir(charts_dir) if f.endswith('.png')]
    check("차트 파일 >= 8장", len(chart_files) >= 8, f"실제: {len(chart_files)}장")

    expected_charts = ['top20_dd', 'top20_macd', 'top20_rsi', 'top20_high52',
                       'sector_top3_dd', 'sector_top3_macd', 'sector_top3_rsi', 'sector_top3_high52',
                       'composite_momentum']
    for chart_name in expected_charts:
        found = any(chart_name in f for f in chart_files)
        check(f"차트 {chart_name}.png 존재", found)
else:
    warn("charts/ 폴더 없음")

# ============================================================
# 최종 요약
# ============================================================
print("\n" + "=" * 60)
print(f"검증 완료: {passed} 통과, {failed} 실패, {warnings} 경고")
print("=" * 60)

if failed > 0:
    print("❌ 실패 항목을 확인하세요.")
else:
    print("✅ 모든 검증 통과!")
