"""
PHASE1 Global Momentum - Step 2: 백테스트
- 4개 모멘텀 지표: DD, MACD, RSI, 52주 신고가
- 4개 기간: 1Y, 3Y, 5Y, 10Y
- 2개 프레임: Daily, Weekly
- 비용 모델: c=0.02% (편도), 왕복 0.04%

실행: python 20260501_momentum_backtest.py
입력: cache/{날짜}_daily_cache.pkl, cache/{날짜}_weekly_cache.pkl
출력: results/{날짜}_momentum_backtest.xlsx
      results/{날짜}_dd_forward_distribution.xlsx
"""

import os
import sys
import pickle
import numpy as np
import pandas as pd
from datetime import datetime

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATE_STR = datetime.now().strftime('%Y%m%d')

# 입출력
CACHE_DIR = os.path.join(SCRIPT_DIR, 'cache')
RESULTS_DIR = os.path.join(SCRIPT_DIR, 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

MASTER_XLSX = os.path.join(SCRIPT_DIR, '..', 'PHASE0_classification', '20260501_classification_master.xlsx')
BACKTEST_XLSX = os.path.join(RESULTS_DIR, f'{DATE_STR}_momentum_backtest.xlsx')
DD_DIST_XLSX = os.path.join(RESULTS_DIR, f'{DATE_STR}_dd_forward_distribution.xlsx')

# 비용 모델
c = 0.0002  # 편도 0.02%
COST_ROUNDTRIP = 2 * c  # 왕복 0.04%

# 기간
PERIOD_MAP = {
    '1Y': 252,
    '3Y': 756,
    '5Y': 1260,
    '10Y': 2520,
}

# DD Forward MDD 윈도우
FORWARD_WINDOW = 20
DD_BINS = [(0, 0.05), (0.05, 0.10), (0.10, 0.20), (0.20, 1.0)]
DD_BIN_LABELS = ['0-5%', '5-10%', '10-20%', '20%+']


# ============================================================
# 캐시 로드
# ============================================================
def load_caches():
    """pickle 캐시 로드 (고정 파일명)"""
    daily_path = os.path.join(CACHE_DIR, 'daily_cache.pkl')
    weekly_path = os.path.join(CACHE_DIR, 'weekly_cache.pkl')

    if not os.path.exists(daily_path) or not os.path.exists(weekly_path):
        print("ERROR: 캐시 파일 없음. 먼저 data_collector.py를 실행하세요.")
        sys.exit(1)

    print(f"일간 캐시: daily_cache.pkl")
    print(f"주간 캐시: weekly_cache.pkl")

    with open(daily_path, 'rb') as f:
        daily_cache = pickle.load(f)
    with open(weekly_path, 'rb') as f:
        weekly_cache = pickle.load(f)

    print(f"일간: {len(daily_cache)}종목, 주간: {len(weekly_cache)}종목")

    return daily_cache, weekly_cache


def load_master():
    """마스터 테이블에서 섹터 정보 로드"""
    df = pd.read_excel(MASTER_XLSX, sheet_name='전체종목')
    sector_map = dict(zip(df['Symbol'], df['GICS_Sector']))
    name_map = dict(zip(df['Symbol'], df['Name']))
    return sector_map, name_map


# ============================================================
# DD 지표
# ============================================================
def calc_dd_metrics(prices):
    """DD 5개 서브 지표 계산"""
    if len(prices) < FORWARD_WINDOW + 10:
        return None

    prices = prices.values if hasattr(prices, 'values') else prices

    # 1. Forward MDD (무조건부)
    forward_mdd_list = []
    for t in range(len(prices) - FORWARD_WINDOW):
        window = prices[t:t + FORWARD_WINDOW]
        peak = np.maximum.accumulate(window)
        dd = (peak - window) / np.where(peak > 0, peak, 1)
        forward_mdd_list.append(dd.max())

    fmdd = np.array(forward_mdd_list)
    fmdd_median = np.median(fmdd)
    fmdd_75th = np.percentile(fmdd, 75)
    fmdd_95th = np.percentile(fmdd, 95)

    # 2. Forward MDD (조건부)
    running_peak = np.maximum.accumulate(prices)
    current_dd = (running_peak - prices) / np.where(running_peak > 0, running_peak, 1)

    conditional_fmdd = {}
    for (lo, hi), label in zip(DD_BINS, DD_BIN_LABELS):
        mask = (current_dd[:-FORWARD_WINDOW] >= lo) & (current_dd[:-FORWARD_WINDOW] < hi)
        if mask.sum() > 0:
            conditional_fmdd[label] = {
                'median': np.median(fmdd[mask]),
                '75th': np.percentile(fmdd[mask], 75),
                '95th': np.percentile(fmdd[mask], 95),
                'count': int(mask.sum()),
            }
        else:
            conditional_fmdd[label] = {'median': np.nan, '75th': np.nan, '95th': np.nan, 'count': 0}

    # 3. Recovery Time
    recovery_times = []
    in_dd = False
    dd_start = 0
    peak_val = prices[0]

    for t in range(1, len(prices)):
        if prices[t] > peak_val:
            if in_dd:
                recovery_times.append(t - dd_start)
                in_dd = False
            peak_val = prices[t]
        elif prices[t] < peak_val and not in_dd:
            in_dd = True
            dd_start = t

    recovery_median = np.median(recovery_times) if recovery_times else np.nan

    # 4. Calmar Ratio
    n_years = len(prices) / 252
    if n_years > 0 and prices[0] > 0:
        total_return = prices[-1] / prices[0]
        ann_return = total_return ** (1 / n_years) - 1
        mdd = current_dd.max()
        calmar = ann_return / mdd if mdd > 0 else np.nan
    else:
        ann_return = np.nan
        calmar = np.nan

    # 5. DD Velocity
    velocities = []
    in_dd = False
    dd_start_idx = 0
    peak_val = prices[0]

    for t in range(1, len(prices)):
        if prices[t] >= peak_val:
            peak_val = prices[t]
            in_dd = False
        else:
            if not in_dd:
                in_dd = True
                dd_start_idx = t
                dd_peak = peak_val
            current_dd_size = (dd_peak - prices[t]) / dd_peak
            duration = t - dd_start_idx + 1
            if duration > 0:
                velocities.append(current_dd_size / duration)

    dd_velocity_avg = np.mean(velocities) if velocities else np.nan

    return {
        'fmdd_median': fmdd_median,
        'fmdd_75th': fmdd_75th,
        'fmdd_95th': fmdd_95th,
        'recovery_time_median': recovery_median,
        'calmar_ratio': calmar,
        'ann_return': ann_return,
        'mdd': current_dd.max(),
        'dd_velocity_avg': dd_velocity_avg,
        'conditional_fmdd': conditional_fmdd,
    }


# ============================================================
# MACD 지표
# ============================================================
def calc_macd_strategy(prices):
    """MACD 골든/데드크로스 전략"""
    if len(prices) < 35:  # EMA(26) + 약간의 마진
        return None

    close = prices.values if hasattr(prices, 'values') else prices
    idx = prices.index if hasattr(prices, 'index') else range(len(prices))

    # pandas Series로 EMA 계산
    ps = pd.Series(close, index=idx)
    ema12 = ps.ewm(span=12, adjust=False).mean()
    ema26 = ps.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    hist = macd_line - signal

    hist_vals = hist.values
    trades = []
    in_position = False
    entry_price = 0

    for t in range(1, len(hist_vals)):
        if not in_position and hist_vals[t - 1] <= 0 and hist_vals[t] > 0:
            entry_price = close[t]
            in_position = True
        elif in_position and hist_vals[t - 1] >= 0 and hist_vals[t] < 0:
            exit_price = close[t]
            if entry_price > 0:
                log_ret = np.log(exit_price / entry_price) - COST_ROUNDTRIP
                trades.append(log_ret)
            in_position = False

    # 미청산 포지션
    if in_position and entry_price > 0:
        log_ret = np.log(close[-1] / entry_price) - COST_ROUNDTRIP
        trades.append(log_ret)

    if not trades:
        return {'cum_return': 0, 'win_rate': 0, 'avg_return': 0, 'n_trades': 0}

    return {
        'cum_return': sum(trades),
        'win_rate': sum(1 for t in trades if t > 0) / len(trades),
        'avg_return': np.mean(trades),
        'n_trades': len(trades),
    }


# ============================================================
# RSI 지표
# ============================================================
def calc_rsi_strategy(prices, period=14):
    """RSI 과매도 반등 전략"""
    if len(prices) < period + 10:
        return None

    close = prices.values if hasattr(prices, 'values') else prices
    ps = pd.Series(close)

    delta = ps.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    rsi_vals = rsi.values
    trades = []
    in_position = False
    entry_price = 0
    was_below_30 = False

    for t in range(period, len(rsi_vals)):
        if rsi_vals[t] < 30:
            was_below_30 = True

        if not in_position:
            # 진입: RSI가 30 하회 후 30 상향 돌파
            if was_below_30 and rsi_vals[t] >= 30 and rsi_vals[t - 1] < 30:
                entry_price = close[t]
                in_position = True
                was_below_30 = False
        else:
            # 청산: RSI가 70 상회 후 70 하향 돌파
            if rsi_vals[t] <= 70 and rsi_vals[t - 1] > 70:
                exit_price = close[t]
                if entry_price > 0:
                    log_ret = np.log(exit_price / entry_price) - COST_ROUNDTRIP
                    trades.append(log_ret)
                in_position = False

    # 미청산 포지션
    if in_position and entry_price > 0:
        log_ret = np.log(close[-1] / entry_price) - COST_ROUNDTRIP
        trades.append(log_ret)

    if not trades:
        return {'cum_return': 0, 'win_rate': 0, 'avg_return': 0, 'n_trades': 0}

    return {
        'cum_return': sum(trades),
        'win_rate': sum(1 for t in trades if t > 0) / len(trades),
        'avg_return': np.mean(trades),
        'n_trades': len(trades),
    }


# ============================================================
# 52주 신고가 지표
# ============================================================
def calc_high52_strategy(prices, trailing_stop=0.05, min_gap=5):
    """52주 신고가 브레이크아웃 전략"""
    if len(prices) < 260:  # 250 + 약간의 마진
        return None

    close = prices.values if hasattr(prices, 'values') else prices

    # 250일 롤링 최고가
    high_250 = pd.Series(close).rolling(250, min_periods=250).max().values

    trades = []
    in_position = False
    entry_price = 0
    peak_since_entry = 0
    last_entry_idx = -min_gap

    for t in range(250, len(close)):
        if not in_position:
            if close[t] >= high_250[t] and (t - last_entry_idx) >= min_gap:
                entry_price = close[t]
                peak_since_entry = entry_price
                in_position = True
                last_entry_idx = t
        else:
            peak_since_entry = max(peak_since_entry, close[t])
            if close[t] < peak_since_entry * (1 - trailing_stop):
                exit_price = close[t]
                if entry_price > 0:
                    log_ret = np.log(exit_price / entry_price) - COST_ROUNDTRIP
                    trades.append(log_ret)
                in_position = False

    # 미청산 포지션
    if in_position and entry_price > 0:
        log_ret = np.log(close[-1] / entry_price) - COST_ROUNDTRIP
        trades.append(log_ret)

    if not trades:
        return {'cum_return': 0, 'win_rate': 0, 'avg_return': 0, 'n_trades': 0}

    return {
        'cum_return': sum(trades),
        'win_rate': sum(1 for t in trades if t > 0) / len(trades),
        'avg_return': np.mean(trades),
        'n_trades': len(trades),
    }


# ============================================================
# 백테스트 실행
# ============================================================
def run_backtest(cache, frame_name, sector_map, name_map):
    """전체 백테스트 실행"""
    results = {}  # key: (indicator, frame, period), value: list of dicts

    tickers = list(cache.keys())
    total = len(tickers)

    for period_name, n_days in PERIOD_MAP.items():
        print(f"\n  [{frame_name}] {period_name} ({n_days}일)")

        dd_results = []
        macd_results = []
        rsi_results = []
        high52_results = []

        for i, ticker in enumerate(tickers):
            if (i + 1) % 500 == 0 or i == 0:
                print(f"    진행: {i+1}/{total}")

            df = cache[ticker]
            if 'Close' not in df.columns:
                continue

            prices = df['Close'].dropna()
            sliced = prices.tail(n_days)

            if len(sliced) < n_days * 0.8:
                data_flag = 'insufficient'
            else:
                data_flag = 'ok'

            if len(sliced) < 30:
                continue

            sector = sector_map.get(ticker, 'Unknown')
            name = name_map.get(ticker, '')
            base_info = {
                'Symbol': ticker,
                'Name': name,
                'GICS_Sector': sector,
                'data_days': len(sliced),
                'data_flag': data_flag,
            }

            # DD
            dd = calc_dd_metrics(sliced)
            if dd is not None:
                row = {**base_info}
                row['fmdd_median'] = dd['fmdd_median']
                row['fmdd_75th'] = dd['fmdd_75th']
                row['fmdd_95th'] = dd['fmdd_95th']
                row['recovery_time_median'] = dd['recovery_time_median']
                row['calmar_ratio'] = dd['calmar_ratio']
                row['ann_return'] = dd['ann_return']
                row['mdd'] = dd['mdd']
                row['dd_velocity_avg'] = dd['dd_velocity_avg']
                dd_results.append(row)

            # MACD
            macd = calc_macd_strategy(sliced)
            if macd is not None:
                macd_results.append({**base_info, **macd})

            # RSI
            rsi = calc_rsi_strategy(sliced)
            if rsi is not None:
                rsi_results.append({**base_info, **rsi})

            # 52주 신고가
            high52 = calc_high52_strategy(sliced)
            if high52 is not None:
                high52_results.append({**base_info, **high52})

        # DataFrame 변환 및 정렬
        key_prefix = f'{frame_name}_{period_name}'

        if dd_results:
            dd_df = pd.DataFrame(dd_results).sort_values('calmar_ratio', ascending=False)
            results[f'DD_{key_prefix}'] = dd_df
            print(f"    DD: {len(dd_df)}종목")

        if macd_results:
            macd_df = pd.DataFrame(macd_results).sort_values('cum_return', ascending=False)
            results[f'MACD_{key_prefix}'] = macd_df
            print(f"    MACD: {len(macd_df)}종목")

        if rsi_results:
            rsi_df = pd.DataFrame(rsi_results).sort_values('cum_return', ascending=False)
            results[f'RSI_{key_prefix}'] = rsi_df
            print(f"    RSI: {len(rsi_df)}종목")

        if high52_results:
            h52_df = pd.DataFrame(high52_results).sort_values('cum_return', ascending=False)
            results[f'HIGH52_{key_prefix}'] = h52_df
            print(f"    HIGH52: {len(h52_df)}종목")

    return results


# ============================================================
# Excel 출력
# ============================================================
def export_results(all_results):
    """백테스트 결과 Excel 저장"""
    print("\n" + "=" * 60)
    print("결과 저장")
    print("=" * 60)

    with pd.ExcelWriter(BACKTEST_XLSX, engine='openpyxl') as writer:
        for sheet_name, df in sorted(all_results.items()):
            # Excel 시트명 31자 제한
            safe_name = sheet_name[:31]
            df.to_excel(writer, sheet_name=safe_name, index=False)

    print(f"백테스트 결과: {BACKTEST_XLSX}")
    print(f"총 시트 수: {len(all_results)}")


# ============================================================
# Main
# ============================================================
def main():
    print(f"PHASE1 Global Momentum - Backtest")
    print(f"Date: {DATE_STR}")
    print(f"비용 모델: c={c*100:.2f}% (편도), 왕복 {COST_ROUNDTRIP*100:.2f}%")
    print()

    # 캐시 로드
    daily_cache, weekly_cache = load_caches()
    sector_map, name_map = load_master()

    all_results = {}

    # Daily 백테스트
    print("\n" + "=" * 60)
    print("Daily 백테스트")
    print("=" * 60)
    daily_results = run_backtest(daily_cache, 'Daily', sector_map, name_map)
    all_results.update(daily_results)

    # Weekly 백테스트
    print("\n" + "=" * 60)
    print("Weekly 백테스트")
    print("=" * 60)
    weekly_results = run_backtest(weekly_cache, 'Weekly', sector_map, name_map)
    all_results.update(weekly_results)

    # Excel 저장
    export_results(all_results)

    # 요약
    print("\n" + "=" * 60)
    print("요약")
    print("=" * 60)
    print(f"총 시트: {len(all_results)}")
    for key in sorted(all_results.keys()):
        df = all_results[key]
        if 'cum_return' in df.columns:
            top = df.head(3)
            print(f"\n  [{key}] Top 3:")
            for _, row in top.iterrows():
                sector = str(row.get('GICS_Sector', 'Unknown'))[:15] if pd.notna(row.get('GICS_Sector')) else 'Unknown'
                print(f"    {row['Symbol']:6s} ({sector:15s}): "
                      f"누적={row['cum_return']:.3f}, 승률={row['win_rate']:.1%}, "
                      f"거래={row['n_trades']:.0f}회")
        elif 'calmar_ratio' in df.columns:
            top = df.head(3)
            print(f"\n  [{key}] Top 3:")
            for _, row in top.iterrows():
                sector = str(row.get('GICS_Sector', 'Unknown'))[:15] if pd.notna(row.get('GICS_Sector')) else 'Unknown'
                print(f"    {row['Symbol']:6s} ({sector:15s}): "
                      f"Calmar={row['calmar_ratio']:.2f}, MDD={row['mdd']:.1%}")

    print(f"\n완료!")


if __name__ == '__main__':
    main()
