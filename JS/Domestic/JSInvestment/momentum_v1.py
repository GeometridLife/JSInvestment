"""
momentum_v1.py  –  JSInvestment 종목마스터 모멘텀 분석 대시보드
지표: Price / Trend / RS / Volume  (각 0-2점, 총 0-8점)

  Price  : 52주 신고가 근접(90%) + MA 정배열(20>60>120)
  Trend  : 골든크로스(10일내) + MACD > Signal
  RS     : 시장 초과수익(20일) + 섹터 내 상위30%
  Volume : 거래량 급증(>20일평균×1.5) + OBV 20일 상승
"""
import os, time, warnings, platform, pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
from pykrx import stock as krx

warnings.filterwarnings("ignore")

# ── 한글 폰트 ────────────────────────────────────────────────────
if platform.system() == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
elif platform.system() == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# ── 설정 ─────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CSV_PATH   = os.path.join(BASE_DIR, "종목마스터.csv")
CACHE_PATH = os.path.join(BASE_DIR, ".momentum_cache.pkl")

TODAY      = pd.Timestamp.today()
END_DATE   = TODAY.strftime("%Y%m%d")
START_DATE = (TODAY - pd.DateOffset(years=1, months=1)).strftime("%Y%m%d")

INDICATORS = ["Price", "Trend", "RS", "Volume"]
IND_LABELS = {
    "Price":  "Price\n(신고가+정배열)",
    "Trend":  "Trend\n(GC+MACD)",
    "RS":     "RS\n(시장초과+순위)",
    "Volume": "Volume\n(급증+OBV)",
}
MAX_SCORE    = 8
TIER1_COLORS = {"반도체": "#4C72B0", "전력인프라": "#DD8452"}
IND_COLORS   = {"Price": "#4E79A7", "Trend": "#F28E2B", "RS": "#E15759", "Volume": "#59A14F"}

# ── 데이터 ───────────────────────────────────────────────────────

def load_master():
    df = pd.read_csv(CSV_PATH, dtype={"코드": str})
    df["코드"] = df["코드"].str.zfill(6)
    return df.dropna(subset=["종목명"]).reset_index(drop=True)


def _fetch_market():
    # KODEX 200 ETF(069500)를 KOSPI 대리 지수로 사용 (pykrx 지수 API 버그 우회)
    try:
        df = krx.get_market_ohlcv(START_DATE, END_DATE, "069500")
        return df["종가"]
    except Exception as e:
        print(f"\n  [경고] 시장 지수 수집 실패: {e}")
        return None


def _fetch_stock(ticker):
    try:
        df = krx.get_market_ohlcv(START_DATE, END_DATE, ticker)
        if df is None or df.empty:
            return None
        df = df.rename(columns={
            "시가": "open", "고가": "high", "저가": "low",
            "종가": "close", "거래량": "volume",
        })
        return df[["open", "high", "low", "close", "volume"]]
    except Exception:
        return None


def load_all_data(master):
    """당일 캐시가 있으면 재사용, 없으면 pykrx에서 수집 후 저장"""
    cache_key = TODAY.strftime("%Y%m%d")
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "rb") as f:
                cached = pickle.load(f)
            if cached.get("date") == cache_key:
                print("  당일 캐시 데이터 사용")
                return cached["market"], cached["stocks"]
        except Exception:
            pass

    print("  KOSPI 지수 수집 중...")
    market = _fetch_market()

    stocks, n = {}, len(master)
    for i, row in master.iterrows():
        tk = row["코드"]
        print(f"  [{i+1:>3}/{n}] {row['종목명']:<14} ({tk})", end="\r")
        stocks[tk] = _fetch_stock(tk)
        time.sleep(0.35)  # API 호출 간격
    ok = sum(v is not None for v in stocks.values())
    print(f"\n  {ok}/{n}개 종목 수집 완료")

    try:
        with open(CACHE_PATH, "wb") as f:
            pickle.dump({"date": cache_key, "market": market, "stocks": stocks}, f)
    except Exception:
        pass
    return market, stocks


# ── 보조 지표 (pandas-ta 대체 순수 구현) ────────────────────────

def _ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def _macd(close, fast=12, slow=26, signal=9):
    macd_line = _ema(close, fast) - _ema(close, slow)
    sig_line  = _ema(macd_line, signal)
    return macd_line, sig_line

def _obv(close, volume):
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()


# ── 지표 계산 (종목별) ───────────────────────────────────────────

def _price(df):
    """52주 신고가 90% + MA 정배열(20>60>120)"""
    if df is None or len(df) < 120:
        return 0, np.nan, False
    c     = df["close"]
    ma20  = c.rolling(20).mean()
    ma60  = c.rolling(60).mean()
    ma120 = c.rolling(120).mean()
    hi52  = df["high"].rolling(252, min_periods=200).max().iloc[-1]
    pct52 = round(float(c.iloc[-1] / hi52 * 100), 1) if pd.notna(hi52) else np.nan
    near  = bool(pd.notna(hi52) and c.iloc[-1] >= hi52 * 0.90)
    align = bool(ma20.iloc[-1] > ma60.iloc[-1] > ma120.iloc[-1])
    return int(near) + int(align), pct52, align


def _trend(df):
    """골든크로스(최근 10일) + MACD > Signal"""
    if df is None or len(df) < 60:
        return 0, False, False
    c    = df["close"]
    ma20 = c.rolling(20).mean()
    ma60 = c.rolling(60).mean()
    cross = bool(((ma20 > ma60) & (ma20.shift(1) <= ma60.shift(1))).iloc[-10:].any())
    macd_line, sig_line = _macd(c)
    mv, ms = macd_line.iloc[-1], sig_line.iloc[-1]
    macd_bull = bool(pd.notna(mv) and pd.notna(ms) and mv > ms)
    return int(cross) + int(macd_bull), cross, macd_bull


def _rs_raw(df, market):
    """시장(KOSPI) 대비 20일 초과수익률 (raw 수치, 점수화는 나중에)"""
    if df is None or market is None or len(df) < 20:
        return np.nan
    c   = df["close"]
    idx = c.index.intersection(market.index)
    if len(idx) < 20:
        return np.nan
    c_s = c.loc[idx]
    m_s = market.loc[idx]
    sr  = (c_s.iloc[-1] / c_s.iloc[-20] - 1) * 100
    mr  = (m_s.iloc[-1] / m_s.iloc[-20] - 1) * 100
    return round(float(sr - mr), 2)


def _volume(df):
    """거래량 급증(>평균×1.5) + OBV 20일 상승"""
    if df is None or len(df) < 20:
        return 0, False, False
    c, v  = df["close"], df["volume"]
    avg20 = v.rolling(20).mean().iloc[-1]
    surge = bool(avg20 > 0 and v.iloc[-1] > avg20 * 1.5)
    obv    = _obv(c, v)
    obv_up = bool(len(obv) >= 20 and obv.iloc[-1] > obv.iloc[-20])
    return int(surge) + int(obv_up), surge, obv_up


# ── 전체 모멘텀 계산 ─────────────────────────────────────────────

def compute_all(master, market, stocks):
    rows = []
    for _, r in master.iterrows():
        tk = r["코드"]
        df = stocks.get(tk)

        p_s, pct52, align  = _price(df)
        t_s, cross, macd_b = _trend(df)
        rs_raw             = _rs_raw(df, market)
        v_s, surge, obv_up = _volume(df)

        rows.append(dict(
            종목명=r["종목명"], 코드=tk, 시장=r["시장"],
            Tier1=r["Tier1(상위섹터)"],
            Tier2=r["Tier2(중위섹터)"],
            Tier3=r["Tier3(하위섹터)"],
            Price=p_s, Trend=t_s, Volume=v_s, RS_raw=rs_raw,
            pct_52w=pct52, 정배열=align,
            골든크로스=cross, MACD강세=macd_b,
            거래량급증=surge, OBV상승=obv_up,
        ))

    res = pd.DataFrame(rows)

    # RS 점수화: RS_raw>0 → +1점 / 섹터내 상위30% → 추가 +1점 (최대 2점)
    res["RS"] = 0
    for tier1 in res["Tier1"].unique():
        mask     = res["Tier1"] == tier1
        rs_col   = res.loc[mask, "RS_raw"]
        valid_rs = rs_col.dropna()
        if valid_rs.empty:
            continue
        above_mkt = mask & (res["RS_raw"] > 0)
        res.loc[above_mkt, "RS"] += 1
        thr   = valid_rs.quantile(0.70)
        top30 = mask & (res["RS_raw"] >= thr)
        res.loc[top30, "RS"] = (res.loc[top30, "RS"] + 1).clip(upper=2)

    res["Total"] = res[INDICATORS].sum(axis=1)
    return res


# ── 시각화 ───────────────────────────────────────────────────────

CMAP_SCORE = LinearSegmentedColormap.from_list(
    "momentum", ["#F7F7F7", "#FEE08B", "#A6D96A", "#1A9641"], N=256
)


def _sector_heatmap(ax, tier1, valid):
    """Tier2 × 4지표 평균 히트맵"""
    sub   = valid[valid["Tier1"] == tier1]
    pivot = sub.groupby("Tier2")[INDICATORS].mean()
    im    = ax.imshow(pivot.values, cmap=CMAP_SCORE, vmin=0, vmax=2, aspect="auto")
    ax.set_xticks(range(len(INDICATORS)))
    ax.set_xticklabels([IND_LABELS[i] for i in INDICATORS], fontsize=9.5, fontweight="bold")
    ax.set_yticks(range(len(pivot)))
    ax.set_yticklabels(pivot.index, fontsize=9.5)
    ax.set_title(f"{tier1} – Tier2 평균 모멘텀",
                 fontsize=12, fontweight="bold", color=TIER1_COLORS[tier1], pad=7)
    for i in range(len(pivot)):
        for j, ind in enumerate(INDICATORS):
            val = pivot.values[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=9, fontweight="bold",
                    color="white" if val >= 1.5 else "#222")
    plt.colorbar(im, ax=ax, fraction=0.045, pad=0.02)


def visualize(res):
    valid = res.dropna(subset=["RS_raw"]).copy().reset_index(drop=True)
    n_valid = len(valid)

    fig = plt.figure(figsize=(24, 33))
    fig.patch.set_facecolor("#F0F2F5")

    gs = gridspec.GridSpec(
        4, 3,
        figure=fig,
        height_ratios=[0.04, 1.05, 1.55, 1.7],
        hspace=0.52, wspace=0.32,
    )

    # ── 타이틀 바 ────────────────────────────────────────────────
    ax_t = fig.add_subplot(gs[0, :])
    ax_t.axis("off")
    ax_t.text(
        0.5, 0.5,
        f"JSInvestment 모멘텀 대시보드  ·  기준일 {TODAY.strftime('%Y-%m-%d')}"
        f"  ·  {n_valid}개 종목  ·  평균 {valid['Total'].mean():.1f} / {MAX_SCORE}점",
        ha="center", va="center", fontsize=15, fontweight="bold", color="white",
        transform=ax_t.transAxes,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#2C3E50", alpha=0.92),
    )

    # ── Row 1: 섹터 히트맵 ×2 + Tier2 Total 막대 ─────────────────
    for ci, tier1 in enumerate(["반도체", "전력인프라"]):
        _sector_heatmap(fig.add_subplot(gs[1, ci]), tier1, valid)

    ax_bar = fig.add_subplot(gs[1, 2])
    t2avg  = (valid.groupby(["Tier1", "Tier2"])["Total"]
               .mean().reset_index()
               .sort_values("Total", ascending=True))
    bcolors = [TIER1_COLORS[t] for t in t2avg["Tier1"]]
    bars = ax_bar.barh(t2avg["Tier2"], t2avg["Total"], color=bcolors, edgecolor="white", height=0.7)
    for bar, val in zip(bars, t2avg["Total"]):
        ax_bar.text(val + 0.08, bar.get_y() + bar.get_height() / 2,
                    f"{val:.1f}", va="center", fontsize=9)
    ax_bar.set_xlim(0, MAX_SCORE + 0.6)
    ax_bar.axvline(MAX_SCORE / 2, color="#999", linestyle="--", linewidth=1, alpha=0.6)
    ax_bar.set_title("Tier2 섹터 평균 Total 점수", fontsize=12, fontweight="bold", pad=7)
    ax_bar.set_xlabel("평균 Total 점수 (0–8)")
    ax_bar.tick_params(axis="y", labelsize=9)
    ax_bar.set_facecolor("white")
    ax_bar.spines[["top", "right"]].set_visible(False)
    ax_bar.legend(
        handles=[Patch(facecolor=v, label=k) for k, v in TIER1_COLORS.items()],
        loc="lower right", fontsize=9,
    )

    # ── Row 2: Top 30 종목 Stacked Bar ───────────────────────────
    ax_top = fig.add_subplot(gs[2, :])
    top30  = valid.nlargest(30, "Total").sort_values("Total", ascending=True).reset_index(drop=True)
    ylabels = [f"{r['종목명']}  ({r['코드']})" for _, r in top30.iterrows()]

    left = np.zeros(len(top30))
    for ind in INDICATORS:
        ax_top.barh(ylabels, top30[ind].values, left=left,
                    color=IND_COLORS[ind], label=ind, edgecolor="white", height=0.72)
        left += top30[ind].values

    # 우측 레이블
    for i, (_, row) in enumerate(top30.iterrows()):
        ax_top.text(
            row["Total"] + 0.1, i,
            f"  {int(row['Total'])}pt  │  {row['Tier1']} › {row['Tier2']}",
            va="center", fontsize=8,
        )
    # Tier1 색 표시 바 (좌측)
    for i, (_, row) in enumerate(top30.iterrows()):
        ax_top.barh([ylabels[i]], [0.15], left=[-0.25],
                    color=TIER1_COLORS.get(row["Tier1"], "#aaa"),
                    edgecolor="none", height=0.72)

    ax_top.set_xlim(-0.4, MAX_SCORE + 5.5)
    ax_top.set_title("Top 30 종목 – 모멘텀 스코어 (지표별 세부)", fontsize=13, fontweight="bold", pad=8)
    ax_top.legend(loc="lower right", fontsize=10)
    ax_top.set_xlabel("모멘텀 점수 (0–8)")
    ax_top.tick_params(axis="y", labelsize=8.5)
    ax_top.set_facecolor("white")
    ax_top.spines[["top", "right"]].set_visible(False)

    # ── Row 3: 전체 종목 히트맵 ──────────────────────────────────
    ax_h = fig.add_subplot(gs[3, :])
    sdf  = (valid.sort_values(["Tier1", "Tier2", "Total"],
                              ascending=[True, True, False])
            .reset_index(drop=True))
    heat = sdf[INDICATORS].values.T  # shape: (4, N)

    im2 = ax_h.imshow(heat, cmap=CMAP_SCORE, vmin=0, vmax=2, aspect="auto")
    ax_h.set_yticks(range(len(INDICATORS)))
    ax_h.set_yticklabels([IND_LABELS[i] for i in INDICATORS], fontsize=9.5)
    ax_h.set_xticks(range(len(sdf)))
    xlabels = [f"{r['종목명']}\n{int(r['Total'])}pt" for _, r in sdf.iterrows()]
    ax_h.set_xticklabels(xlabels, rotation=80, ha="right", fontsize=6.5)
    ax_h.set_title(
        "전체 종목 모멘텀 히트맵  (Tier1 → Tier2 → Total 내림차순 정렬)",
        fontsize=12, fontweight="bold", pad=8,
    )
    plt.colorbar(im2, ax=ax_h, orientation="horizontal",
                 fraction=0.018, pad=0.22, label="점수 (0–2)")

    # Tier1 경계선 (흰색 굵은 선)
    t1_arr = sdf["Tier1"].values
    for pos in np.where(t1_arr[:-1] != t1_arr[1:])[0]:
        ax_h.axvline(pos + 0.5, color="white", linewidth=2.5)

    # Tier2 경계선 (회색 얇은 선)
    t2_arr = sdf["Tier2"].values
    for pos in np.where(t2_arr[:-1] != t2_arr[1:])[0]:
        ax_h.axvline(pos + 0.5, color="#BBBBBB", linewidth=0.7, alpha=0.8)

    out_path = os.path.join(BASE_DIR, "momentum_dashboard.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"  저장: {out_path}")
    plt.show()


# ── 메인 ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("▶ 종목마스터 로드...")
    master = load_master()
    print(f"  {len(master)}개 종목")

    print(f"▶ 주가 데이터 수집  ({START_DATE} ~ {END_DATE})")
    market, stocks = load_all_data(master)

    print("▶ 모멘텀 지표 계산...")
    result = compute_all(master, market, stocks)

    out_csv = os.path.join(BASE_DIR, "momentum_result.csv")
    result.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"  결과 CSV: momentum_result.csv")

    # 콘솔 요약
    print("\n── 모멘텀 상위 10 종목 ─────────────────────────────────────")
    cols = ["종목명", "Tier1", "Tier2", "Price", "Trend", "RS", "Volume", "Total"]
    print(result.nlargest(10, "Total")[cols].to_string(index=False))

    print("\n── Tier2 섹터 평균 점수 ────────────────────────────────────")
    t2 = result.groupby(["Tier1", "Tier2"])[INDICATORS + ["Total"]].mean().round(2)
    print(t2.to_string())

    print("\n▶ 시각화 생성...")
    visualize(result)
