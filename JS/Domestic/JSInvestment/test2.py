"""
test2.py – 미국 시가총액 Top 20 기업 모멘텀 대시보드
데이터: yfinance (Yahoo Finance)  |  벤치마크: SPY
지표:   Price / Trend / RS / Volume  (각 0-2점, 총 0-8점)

  Price  : 52주 신고가 근접(90%) + MA 정배열(20>60>120)
  Trend  : 골든크로스(10일내) + MACD > Signal
  RS     : SPY 대비 초과수익(20일) + 그룹 내 상위 30%
  Volume : 거래량 급증(>20일평균×1.5) + OBV 20일 상승
"""
import os, warnings, platform
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch, Patch

warnings.filterwarnings("ignore")

if platform.system() == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
elif platform.system() == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# ── 종목 정의 (2024년 기준 시가총액 Top 20) ──────────────────────
STOCKS = [
    {"ticker": "AAPL",  "name": "Apple",        "sector": "Technology"},
    {"ticker": "MSFT",  "name": "Microsoft",     "sector": "Technology"},
    {"ticker": "NVDA",  "name": "NVIDIA",        "sector": "Technology"},
    {"ticker": "AVGO",  "name": "Broadcom",      "sector": "Technology"},
    {"ticker": "META",  "name": "Meta",          "sector": "Technology"},
    {"ticker": "ORCL",  "name": "Oracle",        "sector": "Technology"},
    {"ticker": "GOOGL", "name": "Alphabet",      "sector": "Communication"},
    {"ticker": "AMZN",  "name": "Amazon",        "sector": "Cons. Discret."},
    {"ticker": "TSLA",  "name": "Tesla",         "sector": "Cons. Discret."},
    {"ticker": "HD",    "name": "Home Depot",    "sector": "Cons. Discret."},
    {"ticker": "JPM",   "name": "JPMorgan",      "sector": "Financials"},
    {"ticker": "V",     "name": "Visa",          "sector": "Financials"},
    {"ticker": "MA",    "name": "Mastercard",    "sector": "Financials"},
    {"ticker": "BRK-B", "name": "Berkshire",     "sector": "Financials"},
    {"ticker": "LLY",   "name": "Eli Lilly",     "sector": "Healthcare"},
    {"ticker": "UNH",   "name": "UnitedHealth",  "sector": "Healthcare"},
    {"ticker": "JNJ",   "name": "J&J",           "sector": "Healthcare"},
    {"ticker": "WMT",   "name": "Walmart",       "sector": "Cons. Staples"},
    {"ticker": "PG",    "name": "P&G",           "sector": "Cons. Staples"},
    {"ticker": "XOM",   "name": "ExxonMobil",    "sector": "Energy"},
]

SECTOR_COLORS = {
    "Technology":    "#4C72B0",
    "Communication": "#55A868",
    "Cons. Discret.":"#C44E52",
    "Financials":    "#8172B2",
    "Healthcare":    "#CCB974",
    "Cons. Staples": "#64B5CD",
    "Energy":        "#DD8452",
}

INDICATORS = ["Price", "Trend", "RS", "Volume"]
IND_LABELS = {
    "Price":  "Price\n(신고가+정배열)",
    "Trend":  "Trend\n(GC+MACD)",
    "RS":     "RS\n(SPY초과+순위)",
    "Volume": "Volume\n(급증+OBV)",
}
IND_COLORS = {"Price": "#4E79A7", "Trend": "#F28E2B", "RS": "#E15759", "Volume": "#59A14F"}

MARKET_TICKER = "SPY"
TODAY  = pd.Timestamp.today()
START  = (TODAY - pd.DateOffset(years=1, months=1)).strftime("%Y-%m-%d")
END    = TODAY.strftime("%Y-%m-%d")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── 데이터 수집 ───────────────────────────────────────────────────

def fetch_all():
    tickers = [s["ticker"] for s in STOCKS] + [MARKET_TICKER]
    print(f"  {len(tickers)}개 종목 다운로드 중... ({START} ~ {END})")
    raw = yf.download(tickers, start=START, end=END, auto_adjust=True, progress=False)
    return raw


# ── 보조 지표 ─────────────────────────────────────────────────────

def _ema(s, span):
    return s.ewm(span=span, adjust=False).mean()

def _macd(close):
    line = _ema(close, 12) - _ema(close, 26)
    return line, _ema(line, 9)

def _obv(close, volume):
    return (np.sign(close.diff()).fillna(0) * volume).cumsum()


# ── 지표 계산 (종목별) ───────────────────────────────────────────

def calc_price(c, h):
    if len(c) < 120:
        return 0, np.nan, False
    ma20, ma60, ma120 = c.rolling(20).mean(), c.rolling(60).mean(), c.rolling(120).mean()
    hi52 = h.rolling(252, min_periods=200).max().iloc[-1]
    pct52 = round(float(c.iloc[-1] / hi52 * 100), 1) if pd.notna(hi52) else np.nan
    near  = bool(pd.notna(hi52) and c.iloc[-1] >= hi52 * 0.90)
    align = bool(ma20.iloc[-1] > ma60.iloc[-1] > ma120.iloc[-1])
    return int(near) + int(align), pct52, align

def calc_trend(c):
    if len(c) < 60:
        return 0, False, False
    ma20, ma60 = c.rolling(20).mean(), c.rolling(60).mean()
    cross = bool(((ma20 > ma60) & (ma20.shift(1) <= ma60.shift(1))).iloc[-10:].any())
    ml, ms = _macd(c)
    macd_bull = bool(pd.notna(ml.iloc[-1]) and pd.notna(ms.iloc[-1]) and ml.iloc[-1] > ms.iloc[-1])
    return int(cross) + int(macd_bull), cross, macd_bull

def calc_rs_raw(c, market):
    if len(c) < 20 or market is None:
        return np.nan
    idx = c.index.intersection(market.index)
    if len(idx) < 20:
        return np.nan
    sr = (c.loc[idx].iloc[-1] / c.loc[idx].iloc[-20] - 1) * 100
    mr = (market.loc[idx].iloc[-1] / market.loc[idx].iloc[-20] - 1) * 100
    return round(float(sr - mr), 2)

def calc_volume(c, v):
    if len(c) < 20:
        return 0, False, False
    avg20 = v.rolling(20).mean().iloc[-1]
    surge = bool(avg20 > 0 and v.iloc[-1] > avg20 * 1.5)
    obv   = _obv(c, v)
    obv_up = bool(len(obv) >= 20 and obv.iloc[-1] > obv.iloc[-20])
    return int(surge) + int(obv_up), surge, obv_up


# ── 전체 계산 ─────────────────────────────────────────────────────

def compute(raw):
    close_df  = raw["Close"]
    high_df   = raw["High"]
    volume_df = raw["Volume"]
    market    = close_df[MARKET_TICKER].dropna() if MARKET_TICKER in close_df.columns else None

    rows = []
    for s in STOCKS:
        tk = s["ticker"]
        if tk not in close_df.columns:
            print(f"  [경고] {tk} 데이터 없음")
            continue

        c = close_df[tk].dropna()
        h = high_df[tk].dropna()
        v = volume_df[tk].dropna()
        common = c.index.intersection(h.index).intersection(v.index)
        c, h, v = c.loc[common], h.loc[common], v.loc[common]

        p_s, pct52, align    = calc_price(c, h)
        t_s, cross, macd_b   = calc_trend(c)
        rs_raw               = calc_rs_raw(c, market)
        vol_s, surge, obv_up = calc_volume(c, v)

        rows.append(dict(
            ticker=tk, name=s["name"], sector=s["sector"],
            Price=p_s, Trend=t_s, Volume=vol_s, RS_raw=rs_raw,
            pct_52w=pct52, 정배열=align,
            골든크로스=cross, MACD강세=macd_b,
            거래량급증=surge, OBV상승=obv_up,
        ))

    df = pd.DataFrame(rows)

    # RS 점수화: SPY 초과(+1) + 그룹 상위 30%(+1)
    df["RS"] = 0
    rs_col   = df["RS_raw"]
    df.loc[rs_col > 0, "RS"] += 1
    valid_rs = rs_col.dropna()
    if len(valid_rs) >= 3:
        thr = valid_rs.quantile(0.70)
        df.loc[rs_col >= thr, "RS"] = (df.loc[rs_col >= thr, "RS"] + 1).clip(upper=2)

    df["Total"] = df[INDICATORS].sum(axis=1)
    return df


# ── 시각화 ───────────────────────────────────────────────────────

CMAP_SCORE = LinearSegmentedColormap.from_list(
    "momentum", ["#F7F7F7", "#FEE08B", "#A6D96A", "#1A9641"], N=256
)


def _add_sector_bar(ax, sdf, y_pos=-0.55, height=0.4):
    """히트맵 x축 아래 섹터 색 블록 추가"""
    for j, (_, row) in enumerate(sdf.iterrows()):
        color = SECTOR_COLORS.get(row["sector"], "#999")
        ax.add_patch(FancyBboxPatch(
            (j - 0.48, y_pos), 0.96, height,
            boxstyle="square,pad=0", color=color, alpha=0.85,
            transform=ax.transData, clip_on=False,
        ))


def visualize(df):
    fig = plt.figure(figsize=(22, 28))
    fig.patch.set_facecolor("#F0F2F5")

    gs = gridspec.GridSpec(
        4, 2,
        figure=fig,
        height_ratios=[0.04, 1.15, 1.65, 1.45],
        hspace=0.52, wspace=0.30,
    )

    # ── 타이틀 바 ────────────────────────────────────────────────
    ax_t = fig.add_subplot(gs[0, :])
    ax_t.axis("off")
    ax_t.text(
        0.5, 0.5,
        f"US Top 20  Momentum Dashboard   ·   {TODAY.strftime('%Y-%m-%d')}"
        f"   ·   avg {df['Total'].mean():.1f} / 8 pt   ·   benchmark: SPY",
        ha="center", va="center", fontsize=15, fontweight="bold", color="white",
        transform=ax_t.transAxes,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#1A2C42", alpha=0.95),
    )

    # ── 전체 히트맵 (4 indicators × 20 stocks) ───────────────────
    ax_heat = fig.add_subplot(gs[1, :])
    sdf = df.sort_values(["sector", "Total"], ascending=[True, False]).reset_index(drop=True)
    heat = sdf[INDICATORS].values.T  # (4, 20)

    im = ax_heat.imshow(heat, cmap=CMAP_SCORE, vmin=0, vmax=2, aspect="auto")
    ax_heat.set_yticks(range(len(INDICATORS)))
    ax_heat.set_yticklabels([IND_LABELS[i] for i in INDICATORS], fontsize=10.5)

    # x축 레이블: 이름 + 티커 + 점수 (위쪽)
    ax_heat.xaxis.set_ticks_position("top")
    ax_heat.xaxis.set_label_position("top")
    ax_heat.set_xticks(range(len(sdf)))
    xlabels = [f"{r['name']}\n{r['ticker']}\n{int(r['Total'])}pt" for _, r in sdf.iterrows()]
    ax_heat.set_xticklabels(xlabels, fontsize=9, ha="center")

    # 셀 값 표시
    for i in range(len(INDICATORS)):
        for j in range(len(sdf)):
            val = int(heat[i, j])
            ax_heat.text(j, i, str(val), ha="center", va="center",
                         fontsize=13, fontweight="bold",
                         color="white" if heat[i, j] >= 1.5 else "#222")

    plt.colorbar(im, ax=ax_heat, fraction=0.018, pad=0.01, label="점수 (0–2)")

    # 섹터 경계 수직선
    sec_arr = sdf["sector"].values
    for pos in np.where(sec_arr[:-1] != sec_arr[1:])[0]:
        ax_heat.axvline(pos + 0.5, color="white", linewidth=2.5)

    # 섹터 색 블록 (x축 아래)
    _add_sector_bar(ax_heat, sdf)

    # 섹터 레이블 (블록 위)
    prev_sec, prev_start = None, 0
    for j, (_, row) in enumerate(sdf.iterrows()):
        if row["sector"] != prev_sec:
            if prev_sec is not None:
                mid = (prev_start + j - 1) / 2
                ax_heat.text(mid, -0.78, prev_sec, ha="center", va="top",
                             fontsize=7.5, color="white", fontweight="bold",
                             transform=ax_heat.transData, clip_on=False)
            prev_sec, prev_start = row["sector"], j
    mid = (prev_start + len(sdf) - 1) / 2
    ax_heat.text(mid, -0.78, prev_sec, ha="center", va="top",
                 fontsize=7.5, color="white", fontweight="bold",
                 transform=ax_heat.transData, clip_on=False)

    ax_heat.set_title("모멘텀 히트맵   (섹터 → Total 내림차순)",
                      fontsize=13, fontweight="bold", pad=42)

    # ── Top 20 Stacked Horizontal Bar ────────────────────────────
    ax_bar = fig.add_subplot(gs[2, :])
    bar_df  = df.sort_values("Total", ascending=True).reset_index(drop=True)
    ylabels = [f"{r['name']}  ({r['ticker']})" for _, r in bar_df.iterrows()]

    left = np.zeros(len(bar_df))
    for ind in INDICATORS:
        ax_bar.barh(ylabels, bar_df[ind].values, left=left,
                    color=IND_COLORS[ind], label=ind, edgecolor="white", height=0.72)
        left += bar_df[ind].values

    for i, (_, row) in enumerate(bar_df.iterrows()):
        ax_bar.text(
            row["Total"] + 0.12, i,
            f"{int(row['Total'])}pt   {row['sector']}",
            va="center", fontsize=9,
        )
    # 좌측 섹터 색 바
    for i, (_, row) in enumerate(bar_df.iterrows()):
        ax_bar.barh([ylabels[i]], [0.15], left=[-0.25],
                    color=SECTOR_COLORS.get(row["sector"], "#aaa"),
                    edgecolor="none", height=0.72)

    ax_bar.set_xlim(-0.4, 11)
    ax_bar.axvline(4, color="#aaa", linestyle="--", linewidth=1, alpha=0.5)
    ax_bar.set_title("전체 종목 모멘텀 스코어  (Total 오름차순)",
                     fontsize=13, fontweight="bold", pad=8)
    ax_bar.legend(loc="lower right", fontsize=10)
    ax_bar.set_xlabel("모멘텀 점수 (0–8)")
    ax_bar.tick_params(axis="y", labelsize=9.5)
    ax_bar.set_facecolor("white")
    ax_bar.spines[["top", "right"]].set_visible(False)

    # ── 섹터 평균 막대 ────────────────────────────────────────────
    ax_sec = fig.add_subplot(gs[3, 0])
    sec_avg = df.groupby("sector")[INDICATORS + ["Total"]].mean().sort_values("Total", ascending=True)
    bcolors = [SECTOR_COLORS.get(s, "#aaa") for s in sec_avg.index]
    bars = ax_sec.barh(sec_avg.index, sec_avg["Total"], color=bcolors, edgecolor="white", height=0.65)
    for bar, (_, row) in zip(bars, sec_avg.iterrows()):
        ax_sec.text(row["Total"] + 0.08, bar.get_y() + bar.get_height() / 2,
                    f"{row['Total']:.1f}", va="center", fontsize=10)
    ax_sec.set_xlim(0, 8.8)
    ax_sec.axvline(4, color="#aaa", linestyle="--", linewidth=1, alpha=0.5)
    ax_sec.set_title("섹터별 평균 Total 점수", fontsize=12, fontweight="bold", pad=7)
    ax_sec.set_xlabel("평균 점수 (0–8)")
    ax_sec.tick_params(axis="y", labelsize=10)
    ax_sec.set_facecolor("white")
    ax_sec.spines[["top", "right"]].set_visible(False)

    # ── RS vs Total 산점도 (4분면) ────────────────────────────────
    ax_rs = fig.add_subplot(gs[3, 1])
    for _, row in df.iterrows():
        if pd.isna(row["RS_raw"]):
            continue
        color = SECTOR_COLORS.get(row["sector"], "#aaa")
        ax_rs.scatter(row["RS_raw"], row["Total"],
                      color=color, s=140, zorder=3, edgecolors="white", linewidth=1.2)
        ax_rs.annotate(
            row["ticker"], (row["RS_raw"], row["Total"]),
            fontsize=8, ha="center", va="bottom",
            xytext=(0, 6), textcoords="offset points",
        )

    xlim = ax_rs.get_xlim()
    ylim = ax_rs.get_ylim()
    mid_x, mid_y = 0, 4
    ax_rs.axvline(mid_x, color="#888", linestyle="--", linewidth=1, alpha=0.6)
    ax_rs.axhline(mid_y, color="#888", linestyle="--", linewidth=1, alpha=0.6)

    # 4분면 음영
    ax_rs.fill_betweenx([mid_y, ylim[1]], mid_x, xlim[1], alpha=0.04, color="#1A9641")  # 강세
    ax_rs.fill_betweenx([ylim[0], mid_y], xlim[0], mid_x, alpha=0.04, color="#D73027")  # 약세

    ax_rs.text(xlim[1] - (xlim[1] - xlim[0]) * 0.03, ylim[1] - (ylim[1] - ylim[0]) * 0.04,
               "Strong", fontsize=9, color="#1A9641", ha="right", va="top", fontweight="bold", alpha=0.8)
    ax_rs.text(xlim[0] + (xlim[1] - xlim[0]) * 0.03, ylim[0] + (ylim[1] - ylim[0]) * 0.04,
               "Weak", fontsize=9, color="#D73027", ha="left", va="bottom", fontweight="bold", alpha=0.8)
    ax_rs.text(xlim[1] - (xlim[1] - xlim[0]) * 0.03, ylim[0] + (ylim[1] - ylim[0]) * 0.04,
               "RS↑ Mom↓", fontsize=8, color="#888", ha="right", va="bottom", alpha=0.7)
    ax_rs.text(xlim[0] + (xlim[1] - xlim[0]) * 0.03, ylim[1] - (ylim[1] - ylim[0]) * 0.04,
               "RS↓ Mom↑", fontsize=8, color="#888", ha="left", va="top", alpha=0.7)

    ax_rs.set_xlabel("RS  (SPY 대비 20일 초과수익률, %)", fontsize=10)
    ax_rs.set_ylabel("Total 모멘텀 점수 (0–8)", fontsize=10)
    ax_rs.set_title("RS vs Total Momentum  (4분면 분석)", fontsize=12, fontweight="bold", pad=7)
    ax_rs.set_facecolor("white")
    ax_rs.spines[["top", "right"]].set_visible(False)

    legend_elems = [Patch(facecolor=v, label=k)
                    for k, v in SECTOR_COLORS.items() if k in df["sector"].values]
    ax_rs.legend(handles=legend_elems, loc="upper left", fontsize=8, ncol=1, framealpha=0.8)

    out = os.path.join(BASE_DIR, "us_momentum_dashboard.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"  저장: {out}")
    plt.show()


# ── 메인 ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    raw    = fetch_all()
    print("▶ 모멘텀 지표 계산...")
    result = compute(raw)

    result.to_csv(os.path.join(BASE_DIR, "us_momentum_result.csv"),
                  index=False, encoding="utf-8-sig")

    print("\n── 모멘텀 랭킹 ─────────────────────────────────────────────")
    cols = ["name", "sector", "Price", "Trend", "RS", "Volume", "Total", "RS_raw", "pct_52w"]
    print(result.sort_values("Total", ascending=False)[cols].to_string(index=False))

    print("\n▶ 시각화 생성...")
    visualize(result)
