import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import font_manager
import platform
import os

# 한글 폰트 설정
if platform.system() == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
elif platform.system() == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
else:
    plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

csv_path = os.path.join(os.path.dirname(__file__), "종목마스터.csv")
df = pd.read_csv(csv_path, dtype={"코드": str})
df["수주모듈"] = df["수주모듈"].fillna("-")

COLORS = {
    "반도체": "#4C72B0",
    "전력인프라": "#DD8452",
}
TIER1_LIST = ["반도체", "전력인프라"]

fig = plt.figure(figsize=(22, 26))
fig.patch.set_facecolor("#F8F9FA")
gs = gridspec.GridSpec(
    3, 2,
    figure=fig,
    height_ratios=[1.2, 1.2, 3.5],
    hspace=0.45,
    wspace=0.35,
)

# ── 1. Tier1 파이차트 ──────────────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
tier1_counts = df["Tier1(상위섹터)"].value_counts()
ax1.pie(
    tier1_counts,
    labels=tier1_counts.index,
    autopct="%1.1f%%",
    colors=[COLORS[k] for k in tier1_counts.index],
    startangle=90,
    wedgeprops={"edgecolor": "white", "linewidth": 2},
    textprops={"fontsize": 12},
)
ax1.set_title("섹터 비중 (Tier1)", fontsize=14, fontweight="bold", pad=12)

# ── 2. 시장 파이차트 ──────────────────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
market_counts = df["시장"].value_counts()
ax2.pie(
    market_counts,
    labels=market_counts.index,
    autopct="%1.1f%%",
    colors=["#55A868", "#C44E52"],
    startangle=90,
    wedgeprops={"edgecolor": "white", "linewidth": 2},
    textprops={"fontsize": 12},
)
ax2.set_title("시장 비중 (KOSPI / KOSDAQ)", fontsize=14, fontweight="bold", pad=12)

# ── 3. 반도체 Tier2 막대차트 ──────────────────────────────────────
ax3 = fig.add_subplot(gs[1, 0])
semi = df[df["Tier1(상위섹터)"] == "반도체"]
semi_t2 = semi["Tier2(중위섹터)"].value_counts().sort_values()
bars3 = ax3.barh(semi_t2.index, semi_t2.values, color=COLORS["반도체"], edgecolor="white")
for bar, val in zip(bars3, semi_t2.values):
    ax3.text(val + 0.1, bar.get_y() + bar.get_height() / 2, str(val),
             va="center", fontsize=9)
ax3.set_title("반도체 Tier2 분포", fontsize=14, fontweight="bold")
ax3.set_xlabel("종목 수")
ax3.tick_params(axis="y", labelsize=10)
ax3.set_facecolor("#FFFFFF")
ax3.spines[["top", "right"]].set_visible(False)

# ── 4. 전력인프라 Tier2 막대차트 ──────────────────────────────────
ax4 = fig.add_subplot(gs[1, 1])
power = df[df["Tier1(상위섹터)"] == "전력인프라"]
power_t2 = power["Tier2(중위섹터)"].value_counts().sort_values()
bars4 = ax4.barh(power_t2.index, power_t2.values, color=COLORS["전력인프라"], edgecolor="white")
for bar, val in zip(bars4, power_t2.values):
    ax4.text(val + 0.1, bar.get_y() + bar.get_height() / 2, str(val),
             va="center", fontsize=9)
ax4.set_title("전력인프라 Tier2 분포", fontsize=14, fontweight="bold")
ax4.set_xlabel("종목 수")
ax4.tick_params(axis="y", labelsize=10)
ax4.set_facecolor("#FFFFFF")
ax4.spines[["top", "right"]].set_visible(False)

# ── 5. 종목 테이블 ────────────────────────────────────────────────
ax5 = fig.add_subplot(gs[2, :])
ax5.axis("off")

display_df = df[["No", "종목명", "코드", "시장", "Tier1(상위섹터)", "Tier2(중위섹터)", "Tier3(하위섹터)", "수주모듈"]].copy()
display_df["No"] = display_df["No"].astype(str)

col_widths = [0.04, 0.13, 0.07, 0.07, 0.10, 0.13, 0.15, 0.07]
table = ax5.table(
    cellText=display_df.values,
    colLabels=display_df.columns,
    loc="center",
    cellLoc="center",
)
table.auto_set_font_size(False)
table.set_fontsize(8.5)
table.scale(1, 1.18)

# 헤더 스타일
for j in range(len(display_df.columns)):
    cell = table[0, j]
    cell.set_facecolor("#2C3E50")
    cell.set_text_props(color="white", fontweight="bold")

# 행 색상
for i in range(1, len(display_df) + 1):
    tier1 = display_df.iloc[i - 1]["Tier1(상위섹터)"]
    base_color = "#EBF2FA" if tier1 == "반도체" else "#FEF3E8"
    alt_color = "#D6E8F5" if tier1 == "반도체" else "#FDE3C8"
    row_color = base_color if i % 2 == 0 else alt_color
    for j in range(len(display_df.columns)):
        cell = table[i, j]
        cell.set_facecolor(row_color)
        if j == 7 and display_df.iloc[i - 1]["수주모듈"] == "O":
            cell.set_text_props(color="#C0392B", fontweight="bold")

for j, w in enumerate(col_widths):
    for i in range(len(display_df) + 1):
        table[i, j].set_width(w)

ax5.set_title(
    f"종목마스터 전체 목록  (총 {len(display_df)}개 종목)",
    fontsize=14, fontweight="bold", pad=16,
)

fig.suptitle("JSInvestment 종목마스터 대시보드", fontsize=18, fontweight="bold", y=0.995)

plt.savefig(os.path.join(os.path.dirname(__file__), "종목마스터_대시보드.png"),
            dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.show()
