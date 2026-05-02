"""
PHASE1 Momentum - Step 2: 백테스트 엔진
Date: 2026-04-27
Description:
    - 캐시 데이터 로드
    - DD(5개 서브지표), MACD, RSI, 52주 신고가 백테스트
    - 기간별(1Y/3Y/5Y/10Y) × 프레임별(일간/주간) 결과 산출
    - Excel + 차트 출력
"""

import os
import sys
import glob
import pickle
import datetime
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

warnings.filterwarnings('ignore')
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)  # PHASE1_momentum/
PHASE0_DIR = os.path.join(os.path.dirname(BASE_DIR), 'PHASE0_classification')
TODAY = datetime.date.today()
TODAY_STR = TODAY.strftime('%Y%m%d')
YEAR_STR = TODAY.strftime('%Y')
MONTH_STR = TODAY.strftime('%m')

# 결과물: results/연/월/ 폴더
RESULTS_DIR = os.path.join(BASE_DIR, 'results', YEAR_STR, MONTH_STR)
os.makedirs(RESULTS_DIR, exist_ok=True)

# 캐시: cache/ 폴더
CACHE_DIR = os.path.join(BASE_DIR, 'cache')

def find_latest_file(pattern, search_dir=CACHE_DIR):
    candidates = sorted(glob.glob(os.path.join(search_dir, pattern)))
    if not candidates:
        print(f"[ERROR] 파일 없음: {pattern} in {search_dir}")
        sys.exit(1)
    return candidates[-1]

DAILY_CACHE = os.path.join(CACHE_DIR, 'daily_cache.pkl')
WEEKLY_CACHE = os.path.join(CACHE_DIR, 'weekly_cache.pkl')
if not os.path.exists(DAILY_CACHE):
    DAILY_CACHE = find_latest_file('*_daily_cache.pkl')
if not os.path.exists(WEEKLY_CACHE):
    WEEKLY_CACHE = find_latest_file('*_weekly_cache.pkl')

# 마스터 테이블
MASTER_CANDIDATES = sorted(glob.glob(os.path.join(PHASE0_DIR, '*_classification_master_verified.xlsx')))
MASTER_EXCEL = MASTER_CANDIDATES[-1] if MASTER_CANDIDATES else None

# 출력 (results/연/월 폴더에 저장)
OUTPUT_BACKTEST = os.path.join(RESULTS_DIR, f'{TODAY_STR}_momentum_backtest.xlsx')
OUTPUT_DD_DIST = os.path.join(RESULTS_DIR, f'{TODAY_STR}_dd_forward_distribution.xlsx')
CHART_DIR = os.path.join(RESULTS_DIR, f'{TODAY_STR}_charts')

# 비용
COMMISSION_ONE_WAY = 0.001   # 0.1%
COMMISSION_ROUND = 2 * COMMISSION_ONE_WAY  # 0.2%

# 기간
PERIOD_MAP = {
    '1Y': 250,
    '3Y': 750,
    '5Y': 1250,
    '10Y': 2500,
}
MIN_DATA_RATIO = 0.8  # 최소 데이터 비율

# Forward MDD 윈도우 (영업일)
FORWARD_WINDOW = 20  # 일간 기준 약 1개월
FORWARD_WINDOW_WEEKLY = 4  # 주간 기준 약 1개월

# DD 조건부 구간
DD_BINS = [(0, 0.05), (0.05, 0.10), (0.10, 0.20), (0.20, 1.0)]
DD_BIN_LABELS = ['0~5%', '5~10%', '10~20%', '20%+']


# ============================================================
# 데이터 로드
# ============================================================
def load_data():
    print(f"[로드] Daily: {os.path.basename(DAILY_CACHE)}")
    with open(DAILY_CACHE, 'rb') as f:
        daily = pickle.load(f)
    print(f"  → {len(daily)}종목")

    print(f"[로드] Weekly: {os.path.basename(WEEKLY_CACHE)}")
    with open(WEEKLY_CACHE, 'rb') as f:
        weekly = pickle.load(f)
    print(f"  → {len(weekly)}종목")

    # 마스터 테이블 (섹터 정보)
    sector_map = {}
    if MASTER_EXCEL:
        df_master = pd.read_excel(MASTER_EXCEL, sheet_name='전체종목')
        for _, row in df_master.iterrows():
            tk = str(row['ticker']).strip().zfill(6)
            sector_map[tk] = {
                'name': row['name'],
                'tier1': row['tier1'],
                'tier2': row.get('tier2', ''),
                'market': row.get('market', ''),
            }
        print(f"[로드] 마스터 테이블: {len(sector_map)}종목 섹터 정보")

    return daily, weekly, sector_map


def slice_period(df, n_days):
    """시계열에서 최근 n_days만 슬라이스"""
    if len(df) <= n_days:
        return df, len(df) >= n_days * MIN_DATA_RATIO
    return df.tail(n_days), True


# ============================================================
# DD 지표 (5개 서브)
# ============================================================
def calc_dd_metrics(prices, forward_window=FORWARD_WINDOW):
    """
    DD 5개 서브 지표 산출
    prices: Close 가격 Series (DatetimeIndex)
    Returns: dict of metrics
    """
    if len(prices) < forward_window + 10:
        return None

    prices = prices.values.astype(float)
    n = len(prices)

    # --- 1. Forward MDD (무조건부) ---
    forward_mdds = []
    for t in range(n - forward_window):
        window = prices[t:t + forward_window]
        peak = np.maximum.accumulate(window)
        dd = np.where(peak > 0, (peak - window) / peak, 0)
        forward_mdds.append(dd.max())

    forward_mdds = np.array(forward_mdds)
    fmdd_median = np.median(forward_mdds)
    fmdd_75 = np.percentile(forward_mdds, 75)
    fmdd_95 = np.percentile(forward_mdds, 95)

    # --- 2. Forward MDD (조건부) ---
    # 각 시점의 현재 DD 수준
    running_peak = np.maximum.accumulate(prices)
    current_dd = np.where(running_peak > 0, (running_peak - prices) / running_peak, 0)

    conditional_fmdd = {}
    for (lo, hi), label in zip(DD_BINS, DD_BIN_LABELS):
        mask = (current_dd[:n - forward_window] >= lo) & (current_dd[:n - forward_window] < hi)
        if mask.sum() > 5:  # 최소 표본
            conditional_fmdd[label] = {
                'median': np.median(forward_mdds[mask]),
                'p75': np.percentile(forward_mdds[mask], 75),
                'p95': np.percentile(forward_mdds[mask], 95),
                'count': int(mask.sum()),
            }
        else:
            conditional_fmdd[label] = {'median': np.nan, 'p75': np.nan, 'p95': np.nan, 'count': int(mask.sum())}

    # 현재 시점의 DD 구간 (마지막 시점)
    current_dd_level = current_dd[-1]
    current_bin = '20%+'
    for (lo, hi), label in zip(DD_BINS, DD_BIN_LABELS):
        if lo <= current_dd_level < hi:
            current_bin = label
            break

    # --- 3. Recovery Time ---
    recovery_times = []
    in_dd = False
    dd_start = 0
    peak_val = prices[0]

    for t in range(1, n):
        if prices[t] > peak_val:
            if in_dd:
                recovery_times.append(t - dd_start)
                in_dd = False
            peak_val = prices[t]
        elif prices[t] < peak_val and not in_dd:
            in_dd = True
            dd_start = t

    recovery_median = np.median(recovery_times) if recovery_times else np.nan

    # --- 4. Calmar Ratio ---
    total_return = prices[-1] / prices[0] - 1
    n_years = n / 252
    annualized_return = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0
    max_dd = np.max(current_dd)
    calmar = annualized_return / max_dd if max_dd > 0 else np.nan

    # --- 5. DD Velocity ---
    velocities = []
    in_dd = False
    dd_start_idx = 0
    dd_peak = prices[0]

    for t in range(1, n):
        if prices[t] >= dd_peak:
            if in_dd:
                dd_depth = (dd_peak - np.min(prices[dd_start_idx:t])) / dd_peak
                dd_duration = t - dd_start_idx
                if dd_duration > 0 and dd_depth > 0.03:  # 3% 이상 DD만
                    velocities.append(dd_depth / dd_duration)
                in_dd = False
            dd_peak = prices[t]
        elif not in_dd and prices[t] < dd_peak * 0.97:  # 3% 이상 하락 시작
            in_dd = True
            dd_start_idx = t

    dd_velocity_avg = np.mean(velocities) if velocities else np.nan

    return {
        'forward_mdd_median': round(fmdd_median * 100, 2),
        'forward_mdd_p75': round(fmdd_75 * 100, 2),
        'forward_mdd_p95': round(fmdd_95 * 100, 2),
        'current_dd_pct': round(current_dd_level * 100, 2),
        'current_dd_bin': current_bin,
        'cond_fmdd': conditional_fmdd,
        'recovery_time_median': round(recovery_median, 1) if not np.isnan(recovery_median) else np.nan,
        'calmar_ratio': round(calmar, 3) if not np.isnan(calmar) else np.nan,
        'dd_velocity_avg': round(dd_velocity_avg * 100, 4) if not np.isnan(dd_velocity_avg) else np.nan,
        'max_dd_pct': round(max_dd * 100, 2),
        'annualized_return_pct': round(annualized_return * 100, 2),
    }


# ============================================================
# MACD 백테스트
# ============================================================
def backtest_macd(prices):
    """MACD 교차점 기반 백테스트"""
    if len(prices) < 35:
        return None

    prices_s = pd.Series(prices.values.astype(float), index=prices.index)
    ema12 = prices_s.ewm(span=12, adjust=False).mean()
    ema26 = prices_s.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    hist = macd_line - signal

    hist_vals = hist.values
    price_vals = prices_s.values

    # 교차점 탐지
    trades = []
    in_position = False
    entry_price = 0
    entry_idx = 0

    for t in range(1, len(hist_vals)):
        if not in_position:
            # 골든크로스: 음→양
            if hist_vals[t - 1] <= 0 and hist_vals[t] > 0:
                entry_price = price_vals[t]
                entry_idx = t
                in_position = True
        else:
            # 데드크로스: 양→음
            if hist_vals[t - 1] >= 0 and hist_vals[t] < 0:
                exit_price = price_vals[t]
                log_return = np.log(exit_price / entry_price) - COMMISSION_ROUND
                trades.append({
                    'entry_idx': entry_idx,
                    'exit_idx': t,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'log_return': log_return,
                    'holding_days': t - entry_idx,
                })
                in_position = False

    if not trades:
        return None

    returns = np.array([t['log_return'] for t in trades])
    cum_return = returns.sum()
    win_rate = np.mean(returns > 0)
    avg_win = np.mean(returns[returns > 0]) if (returns > 0).any() else 0
    avg_loss = np.mean(returns[returns <= 0]) if (returns <= 0).any() else 0
    rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else np.nan

    return {
        'cum_log_return': round(cum_return, 4),
        'cum_return_pct': round((np.exp(cum_return) - 1) * 100, 2),
        'win_rate': round(win_rate * 100, 2),
        'n_trades': len(trades),
        'avg_win_pct': round((np.exp(avg_win) - 1) * 100, 2) if avg_win != 0 else 0,
        'avg_loss_pct': round((np.exp(avg_loss) - 1) * 100, 2) if avg_loss != 0 else 0,
        'risk_reward': round(rr_ratio, 2) if not np.isnan(rr_ratio) else np.nan,
        'avg_holding_days': round(np.mean([t['holding_days'] for t in trades]), 1),
    }


# ============================================================
# RSI 백테스트
# ============================================================
def calc_rsi(prices, period=14):
    """Wilder RSI 계산"""
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def backtest_rsi(prices):
    """RSI 과매도 반등 전략 백테스트"""
    if len(prices) < 20:
        return None

    prices_s = pd.Series(prices.values.astype(float), index=prices.index)
    rsi = calc_rsi(prices_s)
    rsi_vals = rsi.values
    price_vals = prices_s.values

    trades = []
    in_position = False
    was_below_30 = False
    entry_price = 0
    entry_idx = 0

    for t in range(1, len(rsi_vals)):
        if np.isnan(rsi_vals[t]):
            continue

        if not in_position:
            if rsi_vals[t] < 30:
                was_below_30 = True
            elif was_below_30 and rsi_vals[t] >= 30:
                # RSI가 30 하회 후 상향 돌파 → 진입
                entry_price = price_vals[t]
                entry_idx = t
                in_position = True
                was_below_30 = False
        else:
            if rsi_vals[t] > 70:
                was_above_70 = True
            if in_position and rsi_vals[t - 1] >= 70 and rsi_vals[t] < 70:
                # RSI가 70 상회 후 하향 돌파 → 청산
                exit_price = price_vals[t]
                log_return = np.log(exit_price / entry_price) - COMMISSION_ROUND
                trades.append({
                    'entry_idx': entry_idx,
                    'exit_idx': t,
                    'log_return': log_return,
                    'holding_days': t - entry_idx,
                })
                in_position = False

    if not trades or len(trades) < 3:  # 최소 3회 이상 거래해야 통계적 유의
        return None

    returns = np.array([t['log_return'] for t in trades])
    cum_return = returns.sum()
    win_rate = np.mean(returns > 0)
    avg_win = np.mean(returns[returns > 0]) if (returns > 0).any() else 0
    avg_loss = np.mean(returns[returns <= 0]) if (returns <= 0).any() else 0
    rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else np.nan

    return {
        'cum_log_return': round(cum_return, 4),
        'cum_return_pct': round((np.exp(cum_return) - 1) * 100, 2),
        'win_rate': round(win_rate * 100, 2),
        'n_trades': len(trades),
        'avg_win_pct': round((np.exp(avg_win) - 1) * 100, 2) if avg_win != 0 else 0,
        'avg_loss_pct': round((np.exp(avg_loss) - 1) * 100, 2) if avg_loss != 0 else 0,
        'risk_reward': round(rr_ratio, 2) if not np.isnan(rr_ratio) else np.nan,
        'avg_holding_days': round(np.mean([t['holding_days'] for t in trades]), 1),
    }


# ============================================================
# 골든크로스 (MA50/MA200) 백테스트
# ============================================================
def backtest_golden_cross(prices, short_window=50, long_window=200):
    """MA50이 MA200을 상향 돌파하면 진입, 하향 돌파하면 청산"""
    if len(prices) < long_window + 10:
        return None

    prices_s = pd.Series(prices.values.astype(float), index=prices.index)
    ma_short = prices_s.rolling(window=short_window).mean()
    ma_long = prices_s.rolling(window=long_window).mean()

    short_vals = ma_short.values
    long_vals = ma_long.values
    price_vals = prices_s.values

    trades = []
    in_position = False
    entry_price = 0
    entry_idx = 0

    for t in range(long_window, len(price_vals)):
        if np.isnan(short_vals[t]) or np.isnan(long_vals[t]):
            continue

        if not in_position:
            # 골든크로스: MA50이 MA200 위로
            if short_vals[t - 1] <= long_vals[t - 1] and short_vals[t] > long_vals[t]:
                entry_price = price_vals[t]
                entry_idx = t
                in_position = True
        else:
            # 데드크로스: MA50이 MA200 아래로
            if short_vals[t - 1] >= long_vals[t - 1] and short_vals[t] < long_vals[t]:
                exit_price = price_vals[t]
                log_return = np.log(exit_price / entry_price) - COMMISSION_ROUND
                trades.append({
                    'entry_idx': entry_idx,
                    'exit_idx': t,
                    'log_return': log_return,
                    'holding_days': t - entry_idx,
                })
                in_position = False

    if not trades or len(trades) < 2:  # 장기 시그널이라 최소 2회
        return None

    returns = np.array([t['log_return'] for t in trades])
    cum_return = returns.sum()
    win_rate = np.mean(returns > 0)
    avg_win = np.mean(returns[returns > 0]) if (returns > 0).any() else 0
    avg_loss = np.mean(returns[returns <= 0]) if (returns <= 0).any() else 0
    rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else np.nan

    return {
        'cum_log_return': round(cum_return, 4),
        'cum_return_pct': round((np.exp(cum_return) - 1) * 100, 2),
        'win_rate': round(win_rate * 100, 2),
        'n_trades': len(trades),
        'avg_win_pct': round((np.exp(avg_win) - 1) * 100, 2) if avg_win != 0 else 0,
        'avg_loss_pct': round((np.exp(avg_loss) - 1) * 100, 2) if avg_loss != 0 else 0,
        'risk_reward': round(rr_ratio, 2) if not np.isnan(rr_ratio) else np.nan,
        'avg_holding_days': round(np.mean([t['holding_days'] for t in trades]), 1),
    }


# ============================================================
# 볼린저 밴드 백테스트
# ============================================================
def backtest_bollinger(prices, window=20, num_std=2):
    """하단 밴드 터치 후 중심선 회복 시 진입, 상단 밴드 터치 시 청산"""
    if len(prices) < window + 10:
        return None

    prices_s = pd.Series(prices.values.astype(float), index=prices.index)
    ma = prices_s.rolling(window=window).mean()
    std = prices_s.rolling(window=window).std()
    upper = ma + num_std * std
    lower = ma - num_std * std

    price_vals = prices_s.values
    ma_vals = ma.values
    upper_vals = upper.values
    lower_vals = lower.values

    trades = []
    in_position = False
    touched_lower = False
    entry_price = 0
    entry_idx = 0

    for t in range(window, len(price_vals)):
        if np.isnan(ma_vals[t]):
            continue

        if not in_position:
            # 하단 밴드 터치 감지
            if price_vals[t] <= lower_vals[t]:
                touched_lower = True
            # 하단 터치 후 중심선(MA) 회복 → 진입
            elif touched_lower and price_vals[t] >= ma_vals[t]:
                entry_price = price_vals[t]
                entry_idx = t
                in_position = True
                touched_lower = False
        else:
            # 상단 밴드 터치 → 청산
            if price_vals[t] >= upper_vals[t]:
                exit_price = price_vals[t]
                log_return = np.log(exit_price / entry_price) - COMMISSION_ROUND
                trades.append({
                    'entry_idx': entry_idx,
                    'exit_idx': t,
                    'log_return': log_return,
                    'holding_days': t - entry_idx,
                })
                in_position = False

    if not trades or len(trades) < 3:  # 최소 3회
        return None

    returns = np.array([t['log_return'] for t in trades])
    cum_return = returns.sum()
    win_rate = np.mean(returns > 0)
    avg_win = np.mean(returns[returns > 0]) if (returns > 0).any() else 0
    avg_loss = np.mean(returns[returns <= 0]) if (returns <= 0).any() else 0
    rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else np.nan

    return {
        'cum_log_return': round(cum_return, 4),
        'cum_return_pct': round((np.exp(cum_return) - 1) * 100, 2),
        'win_rate': round(win_rate * 100, 2),
        'n_trades': len(trades),
        'avg_win_pct': round((np.exp(avg_win) - 1) * 100, 2) if avg_win != 0 else 0,
        'avg_loss_pct': round((np.exp(avg_loss) - 1) * 100, 2) if avg_loss != 0 else 0,
        'risk_reward': round(rr_ratio, 2) if not np.isnan(rr_ratio) else np.nan,
        'avg_holding_days': round(np.mean([t['holding_days'] for t in trades]), 1),
    }


# ============================================================
# 52주 신고가 백테스트
# ============================================================
def backtest_52w_high(prices, lookback=250):
    """52주 신고가 브레이크아웃 + 트레일링 스톱 백테스트"""
    if len(prices) < lookback + 10:
        return None

    price_vals = prices.values.astype(float)
    n = len(price_vals)

    trades = []
    in_position = False
    entry_price = 0
    trailing_high = 0
    entry_idx = 0
    last_entry_idx = -10  # 연속 진입 방지

    for t in range(lookback, n):
        high_lookback = np.max(price_vals[t - lookback:t])

        if not in_position:
            # 52주 신고가 갱신 + 최소 5일 간격
            if price_vals[t] >= high_lookback and (t - last_entry_idx) >= 5:
                entry_price = price_vals[t]
                trailing_high = price_vals[t]
                entry_idx = t
                in_position = True
        else:
            # 트레일링 스톱 업데이트
            if price_vals[t] > trailing_high:
                trailing_high = price_vals[t]

            # 청산: 트레일링 고점 대비 -5%
            if price_vals[t] < trailing_high * 0.95:
                exit_price = price_vals[t]
                log_return = np.log(exit_price / entry_price) - COMMISSION_ROUND
                trades.append({
                    'entry_idx': entry_idx,
                    'exit_idx': t,
                    'log_return': log_return,
                    'holding_days': t - entry_idx,
                })
                in_position = False
                last_entry_idx = t

    if not trades:
        return None

    returns = np.array([t['log_return'] for t in trades])
    cum_return = returns.sum()
    win_rate = np.mean(returns > 0)
    avg_win = np.mean(returns[returns > 0]) if (returns > 0).any() else 0
    avg_loss = np.mean(returns[returns <= 0]) if (returns <= 0).any() else 0
    rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else np.nan

    return {
        'cum_log_return': round(cum_return, 4),
        'cum_return_pct': round((np.exp(cum_return) - 1) * 100, 2),
        'win_rate': round(win_rate * 100, 2),
        'n_trades': len(trades),
        'avg_win_pct': round((np.exp(avg_win) - 1) * 100, 2) if avg_win != 0 else 0,
        'avg_loss_pct': round((np.exp(avg_loss) - 1) * 100, 2) if avg_loss != 0 else 0,
        'risk_reward': round(rr_ratio, 2) if not np.isnan(rr_ratio) else np.nan,
        'avg_holding_days': round(np.mean([t['holding_days'] for t in trades]), 1),
    }


# ============================================================
# 메인 백테스트 루프
# ============================================================
def run_all_backtests(data_dict, sector_map, frame_label, forward_window):
    """전종목 × 4지표 × 4기간 백테스트 실행"""
    all_results = {}  # {(indicator, period): [rows]}

    tickers = list(data_dict.keys())
    total = len(tickers)

    for period_name, n_days in PERIOD_MAP.items():
        print(f"\n--- {frame_label} / {period_name} ---")

        dd_rows = []
        macd_rows = []
        rsi_rows = []
        h52_rows = []
        gc_rows = []
        bb_rows = []

        for i, ticker in enumerate(tickers):
            df = data_dict[ticker]
            if 'Close' not in df.columns or len(df) == 0:
                continue

            prices = df['Close'].dropna()
            sliced, sufficient = slice_period(prices, n_days)

            if len(sliced) < 30:
                continue

            info = sector_map.get(ticker, {'name': ticker, 'tier1': '미분류', 'tier2': '', 'market': ''})
            base_row = {
                'ticker': ticker,
                'name': info['name'],
                'market': info.get('market', ''),
                'tier1': info['tier1'],
                'tier2': info.get('tier2', ''),
                'data_days': len(sliced),
                'sufficient': sufficient,
            }

            # DD
            dd_result = calc_dd_metrics(sliced, forward_window)
            if dd_result:
                row = {**base_row}
                row['forward_mdd_median'] = dd_result['forward_mdd_median']
                row['forward_mdd_p75'] = dd_result['forward_mdd_p75']
                row['forward_mdd_p95'] = dd_result['forward_mdd_p95']
                row['current_dd_pct'] = dd_result['current_dd_pct']
                row['current_dd_bin'] = dd_result['current_dd_bin']
                row['recovery_time_median'] = dd_result['recovery_time_median']
                row['calmar_ratio'] = dd_result['calmar_ratio']
                row['dd_velocity_avg'] = dd_result['dd_velocity_avg']
                row['max_dd_pct'] = dd_result['max_dd_pct']
                row['annualized_return_pct'] = dd_result['annualized_return_pct']

                # 조건부 Forward MDD (현재 구간)
                cond = dd_result['cond_fmdd'].get(dd_result['current_dd_bin'], {})
                row['cond_fmdd_median'] = cond.get('median', np.nan)
                if not np.isnan(row.get('cond_fmdd_median', np.nan)):
                    row['cond_fmdd_median'] = round(row['cond_fmdd_median'] * 100, 2)
                row['cond_fmdd_p95'] = cond.get('p95', np.nan)
                if not np.isnan(row.get('cond_fmdd_p95', np.nan)):
                    row['cond_fmdd_p95'] = round(row['cond_fmdd_p95'] * 100, 2)
                row['cond_sample_size'] = cond.get('count', 0)

                dd_rows.append(row)

            # MACD
            macd_result = backtest_macd(sliced)
            if macd_result:
                macd_rows.append({**base_row, **macd_result})

            # RSI
            rsi_result = backtest_rsi(sliced)
            if rsi_result:
                rsi_rows.append({**base_row, **rsi_result})

            # 52주 신고가 (1Y는 lookback=250과 데이터가 겹쳐 시그널 부족 → 제외)
            if period_name != '1Y':
                lb = 250 if frame_label == 'Daily' else 52
                h52_result = backtest_52w_high(sliced, lookback=lb)
                if h52_result:
                    h52_rows.append({**base_row, **h52_result})

            # 골든크로스 (1Y는 MA200 lookback과 겹침 → 제외)
            if period_name != '1Y':
                gc_result = backtest_golden_cross(sliced)
                if gc_result:
                    gc_rows.append({**base_row, **gc_result})

            # 볼린저 밴드
            bb_result = backtest_bollinger(sliced)
            if bb_result:
                bb_rows.append({**base_row, **bb_result})

            if (i + 1) % 200 == 0:
                print(f"  [{i+1}/{total}] 처리 중...")

        key_prefix = f"{frame_label}"
        all_results[f'DD_{key_prefix}_{period_name}'] = pd.DataFrame(dd_rows) if dd_rows else pd.DataFrame()
        all_results[f'MACD_{key_prefix}_{period_name}'] = pd.DataFrame(macd_rows) if macd_rows else pd.DataFrame()
        all_results[f'RSI_{key_prefix}_{period_name}'] = pd.DataFrame(rsi_rows) if rsi_rows else pd.DataFrame()
        all_results[f'HIGH52_{key_prefix}_{period_name}'] = pd.DataFrame(h52_rows) if h52_rows else pd.DataFrame()
        all_results[f'GC_{key_prefix}_{period_name}'] = pd.DataFrame(gc_rows) if gc_rows else pd.DataFrame()
        all_results[f'BB_{key_prefix}_{period_name}'] = pd.DataFrame(bb_rows) if bb_rows else pd.DataFrame()

        print(f"  DD: {len(dd_rows)}, MACD: {len(macd_rows)}, RSI: {len(rsi_rows)}, 52W: {len(h52_rows)}, GC: {len(gc_rows)}, BB: {len(bb_rows)}")

    return all_results


# ============================================================
# 출력
# ============================================================
def save_results(all_results):
    """Excel 저장"""
    os.makedirs(CHART_DIR, exist_ok=True)

    # 메인 백테스트 Excel
    with pd.ExcelWriter(OUTPUT_BACKTEST, engine='openpyxl') as writer:
        for sheet_name, df in sorted(all_results.items()):
            if len(df) == 0:
                continue
            # 시트 이름 31자 제한
            short_name = sheet_name[:31]
            df.to_excel(writer, sheet_name=short_name, index=False)

    print(f"\n[출력] 백테스트 결과: {os.path.basename(OUTPUT_BACKTEST)}")
    print(f"  시트 수: {sum(1 for df in all_results.values() if len(df) > 0)}")

    # DD 분포 상세 (별도 파일)
    dd_sheets = {k: v for k, v in all_results.items() if k.startswith('DD_') and len(v) > 0}
    if dd_sheets:
        with pd.ExcelWriter(OUTPUT_DD_DIST, engine='openpyxl') as writer:
            for sheet_name, df in sorted(dd_sheets.items()):
                short_name = sheet_name[:31]
                df.to_excel(writer, sheet_name=short_name, index=False)
        print(f"[출력] DD 분포 상세: {os.path.basename(OUTPUT_DD_DIST)}")


def generate_summary_charts(all_results):
    """종합 차트 생성: DD 대시보드 + MACD/RSI/52W 차트"""
    os.makedirs(CHART_DIR, exist_ok=True)

    for key, df in all_results.items():
        if len(df) == 0:
            continue

        indicator = key.split('_')[0]

        if indicator == 'DD':
            _generate_dd_dashboard(key, df)
        elif indicator in ('MACD', 'RSI', 'HIGH52', 'GC', 'BB') and 'cum_return_pct' in df.columns:
            _generate_trading_chart(key, df)

    print(f"[출력] 차트 저장: {CHART_DIR}/")


def _generate_dd_dashboard(key, df):
    """DD 종합 대시보드: 4개 패널"""
    required = ['calmar_ratio', 'forward_mdd_median', 'recovery_time_median',
                 'current_dd_pct', 'cond_fmdd_median', 'sufficient']
    if not all(c in df.columns for c in required):
        return

    # sufficient 데이터만 사용
    df_s = df[df['sufficient'] == True].copy()
    df_s = df_s.dropna(subset=['calmar_ratio', 'forward_mdd_median'])
    df_s = df_s[df_s['calmar_ratio'] > 0]
    if len(df_s) < 10:
        return

    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle(f'{key}: DD 종합 분석 대시보드', fontsize=16, fontweight='bold', y=0.98)

    # ──────────────────────────────────────────────
    # 패널 1 (좌상): 리스크-리턴 스캐터 (종목 간 비교)
    # X축: Forward MDD 중앙값 (낮을수록 좋음)
    # Y축: Calmar Ratio (높을수록 좋음)
    # 크기: 연환산수익률, 색상: 섹터
    # ──────────────────────────────────────────────
    ax1 = axes[0, 0]
    sectors = df_s['tier1'].unique()
    cmap = plt.cm.get_cmap('tab20', len(sectors))
    sector_colors = {s: cmap(i) for i, s in enumerate(sectors)}

    for sector in sectors:
        mask = df_s['tier1'] == sector
        subset = df_s[mask]
        ax1.scatter(
            subset['forward_mdd_median'],
            subset['calmar_ratio'],
            c=[sector_colors[sector]] * len(subset),
            s=np.clip(subset['annualized_return_pct'].abs() * 3, 20, 300),
            alpha=0.6,
            label=sector if len(subset) >= 3 else None,
        )

    # 상위 10개 종목 라벨
    top10_calmar = df_s.nlargest(10, 'calmar_ratio')
    for _, r in top10_calmar.iterrows():
        ax1.annotate(
            r['name'], (r['forward_mdd_median'], r['calmar_ratio']),
            fontsize=7, alpha=0.8,
            xytext=(5, 5), textcoords='offset points',
        )

    ax1.set_xlabel('Forward MDD 중앙값 (%) — 낮을수록 안전', fontsize=10)
    ax1.set_ylabel('Calmar Ratio — 높을수록 효율적', fontsize=10)
    ax1.set_title('① 리스크-리턴 비교 (버블 크기=연환산수익률)', fontsize=12)
    ax1.axhline(y=df_s['calmar_ratio'].median(), color='gray', linestyle='--', alpha=0.5)
    ax1.axvline(x=df_s['forward_mdd_median'].median(), color='gray', linestyle='--', alpha=0.5)
    # 좌상 영역 = 최적 (낮은 리스크, 높은 칼마)
    ax1.text(0.02, 0.98, '◀ 최적 영역 (낮은 리스크 + 높은 수익 효율)',
             transform=ax1.transAxes, fontsize=8, color='green', va='top')
    ax1.legend(fontsize=6, loc='lower right', ncol=2)

    # ──────────────────────────────────────────────
    # 패널 2 (우상): 진입 매력도 Top 20
    # 조건: current_dd가 깊은데 cond_fmdd_median이 낮은 종목
    # 점수 = current_dd_pct / (cond_fmdd_median + 1) → 높을수록 매력적
    # ──────────────────────────────────────────────
    ax2 = axes[0, 1]
    df_entry = df_s.dropna(subset=['cond_fmdd_median', 'cond_sample_size']).copy()
    df_entry = df_entry[df_entry['cond_sample_size'] >= 20]  # 통계적 유의성

    if len(df_entry) >= 5:
        # 진입 매력도 점수: 이미 많이 빠졌는데(current_dd 높음) 추가 하락 기대값이 낮으면 매력적
        df_entry['entry_score'] = df_entry['current_dd_pct'] / (df_entry['cond_fmdd_median'] + 0.5)
        # calmar가 양수인 것만 (기본적으로 수익 내는 종목)
        df_entry = df_entry[df_entry['calmar_ratio'] > 0]
        top20_entry = df_entry.nlargest(20, 'entry_score')

        y_pos = range(len(top20_entry))
        # 막대 색상: current_dd 구간별
        bin_colors = {'0~5%': '#3498db', '5~10%': '#f39c12', '10~20%': '#e67e22', '20%+': '#e74c3c'}
        bar_colors = [bin_colors.get(b, '#95a5a6') for b in top20_entry['current_dd_bin']]

        bars = ax2.barh(y_pos, top20_entry['entry_score'].values, color=bar_colors, alpha=0.8)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels([
            f"{r['name']} (DD:{r['current_dd_pct']:.0f}%→추가:{r['cond_fmdd_median']:.1f}%)"
            for _, r in top20_entry.iterrows()
        ], fontsize=7)
        ax2.set_xlabel('진입 매력도 점수 (높을수록 좋음)', fontsize=10)
        ax2.set_title('② 진입 타이밍 Top 20\n(이미 빠졌지만 추가 하락 기대값이 낮은 종목)', fontsize=12)
        ax2.invert_yaxis()

        from matplotlib.patches import Patch
        legend_els = [Patch(facecolor=c, label=l) for l, c in bin_colors.items()]
        ax2.legend(handles=legend_els, title='현재 DD 구간', fontsize=7, loc='lower right')
    else:
        ax2.text(0.5, 0.5, '충분한 데이터 없음\n(cond_sample_size ≥ 20 필요)',
                 transform=ax2.transAxes, ha='center', va='center', fontsize=12)
        ax2.set_title('② 진입 타이밍 Top 20', fontsize=12)

    # ──────────────────────────────────────────────
    # 패널 3 (좌하): 회복 속도 vs DD 깊이
    # 빨리 회복하면서 낙폭도 작은 = 방어적 종목
    # ──────────────────────────────────────────────
    ax3 = axes[1, 0]
    df_rec = df_s.dropna(subset=['recovery_time_median', 'max_dd_pct']).copy()
    df_rec = df_rec[df_rec['recovery_time_median'] > 0]

    if len(df_rec) >= 10:
        ax3.scatter(
            df_rec['max_dd_pct'],
            df_rec['recovery_time_median'],
            c=df_rec['calmar_ratio'],
            cmap='RdYlGn',
            s=40, alpha=0.6,
        )
        cbar = plt.colorbar(ax3.collections[0], ax=ax3)
        cbar.set_label('Calmar Ratio', fontsize=9)

        # 좌하 영역(작은 MDD + 빠른 회복) 상위 10개 라벨
        df_rec['defense_score'] = 1 / (df_rec['max_dd_pct'] * df_rec['recovery_time_median'] + 1)
        top10_def = df_rec.nlargest(10, 'defense_score')
        for _, r in top10_def.iterrows():
            ax3.annotate(
                r['name'], (r['max_dd_pct'], r['recovery_time_median']),
                fontsize=7, alpha=0.8,
                xytext=(5, 5), textcoords='offset points',
            )

        ax3.set_xlabel('최대 낙폭 MDD (%) — 작을수록 안전', fontsize=10)
        ax3.set_ylabel('회복 기간 중앙값 (일) — 짧을수록 좋음', fontsize=10)
        ax3.set_title('③ 방어력 분석 (MDD vs 회복 속도)', fontsize=12)
        ax3.text(0.02, 0.02, '◀ 최적 영역 (작은 낙폭 + 빠른 회복)',
                 transform=ax3.transAxes, fontsize=8, color='green')

    # ──────────────────────────────────────────────
    # 패널 4 (우하): 종합 Top 15 테이블
    # Calmar 상위 + sufficient + cond_sample 충분한 종목
    # ──────────────────────────────────────────────
    ax4 = axes[1, 1]
    ax4.axis('off')

    df_table = df_s.dropna(subset=['calmar_ratio', 'forward_mdd_median', 'cond_fmdd_median'])
    df_table = df_table[df_table['cond_sample_size'] >= 10]
    df_table = df_table.nlargest(15, 'calmar_ratio')

    if len(df_table) > 0:
        table_data = []
        for _, r in df_table.iterrows():
            table_data.append([
                r['name'],
                r['tier1'],
                f"{r['calmar_ratio']:.2f}",
                f"{r['forward_mdd_median']:.1f}%",
                f"{r['current_dd_pct']:.1f}%",
                f"{r['cond_fmdd_median']:.1f}%",
                f"{r['recovery_time_median']:.0f}일",
                f"{r['annualized_return_pct']:.1f}%",
            ])

        col_labels = ['종목', '섹터', 'Calmar', 'Fwd MDD\n(중앙값)', '현재 DD',
                       '조건부\nFwd MDD', '회복 기간', '연수익률']

        table = ax4.table(
            cellText=table_data,
            colLabels=col_labels,
            cellLoc='center',
            loc='center',
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1.0, 1.5)

        # 헤더 스타일
        for j in range(len(col_labels)):
            table[0, j].set_facecolor('#2c3e50')
            table[0, j].set_text_props(color='white', fontweight='bold')

        # Calmar 기준 그라데이션
        calmar_vals = [float(row[2]) for row in table_data]
        max_cal = max(calmar_vals) if calmar_vals else 1
        for i in range(len(table_data)):
            intensity = calmar_vals[i] / max_cal
            color = plt.cm.RdYlGn(0.3 + intensity * 0.6)
            for j in range(len(col_labels)):
                if i % 2 == 0:
                    table[i + 1, j].set_facecolor((*color[:3], 0.15))

        ax4.set_title('④ 종합 Top 15 (Calmar 기준, 데이터 충분 종목)', fontsize=12, pad=20)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(os.path.join(CHART_DIR, f'{TODAY_STR}_{key}_dd_dashboard.png'), dpi=150, bbox_inches='tight')
    plt.close()


def _generate_trading_chart(key, df):
    """MACD/RSI/52W: 누적수익률 + 승률 + 손익비 종합 차트"""
    df_valid = df.dropna(subset=['cum_return_pct'])
    if len(df_valid) < 5:
        return

    # sufficient 필터
    if 'sufficient' in df_valid.columns:
        df_valid = df_valid[df_valid['sufficient'] == True]

    top20 = df_valid.nlargest(20, 'cum_return_pct')

    fig, axes = plt.subplots(1, 3, figsize=(22, 10))
    fig.suptitle(f'{key}: 트레이딩 성과 Top 20', fontsize=14, fontweight='bold')

    # 패널 1: 누적 수익률
    ax1 = axes[0]
    colors = ['#2ecc71' if v > 0 else '#e74c3c' for v in top20['cum_return_pct'].values]
    ax1.barh(range(len(top20)), top20['cum_return_pct'].values, color=colors)
    ax1.set_yticks(range(len(top20)))
    ax1.set_yticklabels([f"{r['name']}" for _, r in top20.iterrows()], fontsize=8)
    ax1.set_xlabel('누적 수익률 (%)')
    ax1.set_title('누적 수익률')
    ax1.invert_yaxis()

    # 패널 2: 승률 + 거래 횟수
    ax2 = axes[1]
    if 'win_rate' in top20.columns:
        bar_colors = ['#2ecc71' if w >= 50 else '#e67e22' if w >= 40 else '#e74c3c'
                      for w in top20['win_rate'].values]
        bars = ax2.barh(range(len(top20)), top20['win_rate'].values, color=bar_colors)
        ax2.axvline(x=50, color='gray', linestyle='--', alpha=0.5, label='50%')
        ax2.set_yticks(range(len(top20)))
        ax2.set_yticklabels([f"({r['n_trades']}회)" for _, r in top20.iterrows()], fontsize=8)
        ax2.set_xlabel('승률 (%) — 괄호: 거래횟수')
        ax2.set_title('승률 & 거래 횟수')
        ax2.invert_yaxis()
        ax2.legend(fontsize=8)

    # 패널 3: 손익비
    ax3 = axes[2]
    if 'risk_reward' in top20.columns:
        rr = top20['risk_reward'].fillna(0).values
        bar_colors = ['#2ecc71' if r >= 2 else '#f39c12' if r >= 1 else '#e74c3c' for r in rr]
        ax3.barh(range(len(top20)), rr, color=bar_colors)
        ax3.axvline(x=1, color='gray', linestyle='--', alpha=0.5, label='1:1')
        ax3.axvline(x=2, color='green', linestyle='--', alpha=0.5, label='2:1')
        ax3.set_yticks(range(len(top20)))
        ax3.set_yticklabels([
            f"{r['name']} [{r['tier1']}]" if 'tier1' in top20.columns else r['name']
            for _, r in top20.iterrows()
        ], fontsize=7)
        ax3.set_xlabel('손익비 (Avg Win / Avg Loss)')
        ax3.set_title('손익비 (≥2 권장)')
        ax3.invert_yaxis()
        ax3.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(CHART_DIR, f'{TODAY_STR}_{key}_top20.png'), dpi=150, bbox_inches='tight')
    plt.close()


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 60)
    print("PHASE1 Momentum - Step 2: 백테스트")
    print(f"실행 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    daily, weekly, sector_map = load_data()

    all_results = {}

    # 일간 백테스트만 실행 (주간은 데이터 부족으로 제외)
    print("\n" + "=" * 40)
    print("일간(Daily) 백테스트")
    print("=" * 40)
    daily_results = run_all_backtests(daily, sector_map, 'Daily', FORWARD_WINDOW)
    all_results.update(daily_results)

    # 결과 저장
    save_results(all_results)
    generate_summary_charts(all_results)

    # 요약
    print("\n" + "=" * 60)
    print("백테스트 요약")
    print("=" * 60)
    for key, df in sorted(all_results.items()):
        if len(df) > 0:
            print(f"  {key}: {len(df)}종목")
    print("=" * 60)


if __name__ == '__main__':
    main()
