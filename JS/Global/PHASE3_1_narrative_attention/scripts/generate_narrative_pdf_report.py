#!/usr/bin/env python3
"""
Generate a PDF report for narrative attention and linked-company analysis.

Pillow만 사용해 차트/표를 이미지 페이지로 그린 뒤 PDF로 저장한다.
"""
from __future__ import annotations

import argparse
import datetime as dt
import textwrap
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE3_1_DIR = SCRIPT_DIR.parent
RESULTS_DIR = PHASE3_1_DIR / "results"
CACHE_DIR = PHASE3_1_DIR / "cache"
TODAY_STR = dt.datetime.now().strftime("%Y%m%d")

PAGE_W, PAGE_H = 1600, 1130
MARGIN = 70
FONT_PATH = Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf")

COLORS = {
    "bg": (255, 255, 255),
    "text": (15, 23, 42),
    "muted": (100, 116, 139),
    "grid": (226, 232, 240),
    "blue": (37, 99, 235),
    "green": (5, 150, 105),
    "orange": (217, 119, 6),
    "red": (220, 38, 38),
    "gray": (100, 116, 139),
    "light": (241, 245, 249),
}


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if FONT_PATH.exists():
        return ImageFont.truetype(str(FONT_PATH), size)
    return ImageFont.load_default()


F = {
    "title": font(44),
    "h1": font(30),
    "h2": font(24),
    "body": font(18),
    "small": font(15),
    "tiny": font(13),
    "table": font(12),
}


def new_page() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (PAGE_W, PAGE_H), COLORS["bg"])
    return img, ImageDraw.Draw(img)


def fmt(value: Any, digits: int = 2, suffix: str = "") -> str:
    try:
        if pd.isna(value):
            return "-"
    except Exception:
        pass
    if isinstance(value, (float, int)):
        return f"{value:.{digits}f}{suffix}"
    return str(value)


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, fnt: ImageFont.ImageFont, fill=COLORS["text"]) -> None:
    draw.text(xy, value, font=fnt, fill=fill)


def wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, fnt: ImageFont.ImageFont, width: int, line_gap: int = 8, fill=COLORS["text"]) -> int:
    x, y = xy
    for para in str(value).split("\n"):
        lines = textwrap.wrap(para, width=width) or [""]
        for line in lines:
            draw.text((x, y), line, font=fnt, fill=fill)
            y += fnt.size + line_gap
    return y


def pill(draw: ImageDraw.ImageDraw, xy: tuple[int, int], label: str, fill: tuple[int, int, int]) -> int:
    x, y = xy
    bbox = draw.textbbox((0, 0), label, font=F["tiny"])
    w = bbox[2] - bbox[0] + 22
    h = 28
    draw.rounded_rectangle((x, y, x + w, y + h), radius=12, fill=fill)
    draw.text((x + 11, y + 6), label, font=F["tiny"], fill=(255, 255, 255))
    return x + w + 8


def source_coverage(raw_finnhub: Path, raw_gdelt: Path | None) -> list[str]:
    lines = []
    if raw_finnhub.exists():
        df = pd.read_csv(raw_finnhub, encoding="utf-8-sig", on_bad_lines="skip")
        dates = pd.to_datetime(df["published_at"], utc=True, errors="coerce")
        lines.append(
            f"Finnhub company-news: {len(df):,} rows, {df['ticker'].nunique():,} tickers, "
            f"{dates.min().date()} ~ {dates.max().date()}"
        )
    if raw_gdelt and raw_gdelt.exists():
        df = pd.read_csv(raw_gdelt, encoding="utf-8-sig", on_bad_lines="skip")
        dates = pd.to_datetime(df["published_at"], utc=True, errors="coerce")
        lines.append(f"GDELT sample: {len(df):,} rows, {dates.min().date()} ~ {dates.max().date()} (보조 샘플)")
    else:
        lines.append("GDELT: 현재 통합 점수에는 미반영")
    reddit_files = list((CACHE_DIR / "raw").glob("*reddit*raw.csv"))
    if reddit_files:
        rows = sum(len(pd.read_csv(p, on_bad_lines="skip")) for p in reddit_files)
        lines.append(f"Reddit: local cache {len(reddit_files)} files, {rows:,} rows")
    else:
        lines.append("Reddit: 현재 로컬 raw cache 없음. retail attention은 미반영")
    return lines


def build_theme_summary(ranking: pd.DataFrame, matrix: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in ranking.iterrows():
        theme = row["theme"]
        linked = matrix[(matrix["theme"] == theme) & (matrix["article_count_7d"] > 0)]
        linked = linked.sort_values("company_narrative_score", ascending=False)
        support = min(
            100.0,
            len(linked) * 8.0
            + min(float(linked["source_breadth_7d"].sum()), 10.0) * 4.0
            + min(float(linked["article_count_7d"].sum()), 30.0) * 1.2,
        )
        rows.append(
            {
                "theme": theme,
                "attention_score": row.get("attention_score", 0),
                "adjusted_confidence": row.get("adjusted_confidence", ""),
                "narrative_type": row.get("narrative_type", ""),
                "article_count_7d": row.get("article_count_7d", 0),
                "baseline_article_count_30d": row.get("baseline_article_count_30d", 0),
                "pure_play_ratio_7d": row.get("pure_play_ratio_7d", 0),
                "company_support_score": support,
                "news_linked_companies": ", ".join(linked["ticker"].head(5).astype(str).tolist()),
            }
        )
    return pd.DataFrame(rows)


def reason_text(row: pd.Series, companies: str) -> str:
    msg = (
        f"{row['theme']}는 최근 7일 기사 {int(row.get('article_count_7d', 0))}건, "
        f"30일 baseline {fmt(row.get('baseline_article_count_30d'))}건 대비 "
        f"log change {fmt(row.get('log_share_change_7d_30d'))}로 상위권에 올랐다. "
        f"활성일수 {fmt(row.get('daily_active_days_7d'), 0)}일, 소스 {fmt(row.get('unique_source_count_7d'), 0)}개, "
        f"pure-play ratio {fmt(float(row.get('pure_play_ratio_7d', 0))*100, 1, '%')}이다. "
    )
    ntype = str(row.get("narrative_type", ""))
    if ntype == "sustained_narrative":
        msg += "기사 수와 기업 breadth가 함께 받쳐주는 지속형 내러티브다. "
    elif ntype == "emerging_watch":
        msg += "상승은 확인되지만 이벤트성인지 지속성인지 추가 관찰이 필요하다. "
    elif ntype == "derivative_mention":
        msg += "독립 테마라기보다 대형주/인접 테마 문맥에 흡수된 성격이 강하다. "
    elif ntype == "noise_possible":
        msg += "샘플 수와 집중도 측면에서 noise 가능성이 높다. "
    if companies:
        msg += f"뉴스가 실제 연결한 주요 종목은 {companies}이다."
    return msg


def draw_bar_chart(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], labels: list[str], values: list[float], title: str, color=COLORS["blue"]) -> None:
    x0, y0, x1, y1 = box
    draw.text((x0, y0 - 34), title, font=F["h2"], fill=COLORS["text"])
    max_v = max(values) if values else 1
    row_h = max(26, int((y1 - y0) / max(len(labels), 1)))
    label_w = 310
    for i, (label, value) in enumerate(zip(labels, values)):
        y = y0 + i * row_h
        draw.text((x0, y + 4), label[:30], font=F["small"], fill=COLORS["text"])
        bx0 = x0 + label_w
        bw = int((x1 - bx0 - 70) * (value / max_v)) if max_v else 0
        draw.rectangle((bx0, y + 4, bx0 + bw, y + row_h - 6), fill=color)
        draw.text((bx0 + bw + 8, y + 4), fmt(value, 1), font=F["small"], fill=COLORS["muted"])


def draw_scatter(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], df: pd.DataFrame) -> None:
    x0, y0, x1, y1 = box
    draw.text((x0, y0 - 34), "Attention vs Company Support", font=F["h2"], fill=COLORS["text"])
    draw.rectangle(box, outline=COLORS["grid"], width=2)
    for i in range(1, 5):
        gx = x0 + int((x1 - x0) * i / 5)
        gy = y0 + int((y1 - y0) * i / 5)
        draw.line((gx, y0, gx, y1), fill=COLORS["grid"])
        draw.line((x0, gy, x1, gy), fill=COLORS["grid"])
    for _, row in df.head(12).iterrows():
        x = x0 + int((x1 - x0) * float(row["attention_score"]) / 100)
        y = y1 - int((y1 - y0) * float(row["company_support_score"]) / 100)
        color = {
            "sustained_narrative": COLORS["green"],
            "emerging_watch": COLORS["orange"],
            "derivative_mention": COLORS["blue"],
            "noise_possible": COLORS["gray"],
        }.get(row["narrative_type"], COLORS["red"])
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=color)
        draw.text((x + 10, y - 8), str(row["theme"])[:16], font=F["tiny"], fill=COLORS["text"])


def draw_table(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], headers: list[str], rows: list[list[str]], title: str | None = None) -> None:
    x0, y0, x1, y1 = box
    if title:
        draw.text((x0, y0 - 32), title, font=F["h2"], fill=COLORS["text"])
    col_w = (x1 - x0) // len(headers)
    row_h = 34
    draw.rectangle((x0, y0, x1, y0 + row_h), fill=COLORS["light"])
    for i, h in enumerate(headers):
        draw.text((x0 + i * col_w + 6, y0 + 9), h, font=F["table"], fill=COLORS["text"])
    for r, row in enumerate(rows):
        y = y0 + row_h * (r + 1)
        if y + row_h > y1:
            break
        fill = (255, 255, 255) if r % 2 == 0 else (248, 250, 252)
        draw.rectangle((x0, y, x1, y + row_h), fill=fill)
        for i, val in enumerate(row):
            draw.text((x0 + i * col_w + 6, y + 9), str(val)[:22], font=F["table"], fill=COLORS["text"])
    draw.rectangle((x0, y0, x1, min(y1, y0 + row_h * (len(rows) + 1))), outline=COLORS["grid"])


def cover_page(ranking: pd.DataFrame, coverage: list[str]) -> Image.Image:
    img, draw = new_page()
    text(draw, (MARGIN, 90), "Narrative Attention Report", F["title"])
    text(draw, (MARGIN, 155), "최근 37일 Finnhub 중심 + GDELT/Reddit 보조 소스 상태 점검", F["h2"], COLORS["muted"])
    text(draw, (MARGIN, 205), f"생성 시각: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}", F["body"], COLORS["muted"])

    y = 300
    text(draw, (MARGIN, y), "데이터 커버리지", F["h1"])
    y += 50
    for line in coverage:
        y = wrapped(draw, (MARGIN + 20, y), f"- {line}", F["body"], 110, fill=COLORS["text"]) + 4

    y += 30
    text(draw, (MARGIN, y), "Top Attention Themes", F["h1"])
    y += 55
    for i, (_, row) in enumerate(ranking.sort_values("attention_score", ascending=False).head(6).iterrows(), start=1):
        text(draw, (MARGIN + 20, y), f"{i}. {row['theme']}", F["body"])
        x = MARGIN + 520
        x = pill(draw, (x, y - 3), f"score {row['attention_score']:.1f}", COLORS["blue"])
        x = pill(draw, (x, y - 3), str(row["adjusted_confidence"]), COLORS["green"])
        pill(draw, (x, y - 3), str(row["narrative_type"]), COLORS["orange"])
        y += 48

    wrapped(
        draw,
        (MARGIN, PAGE_H - 120),
        "주의: 본 PDF는 뉴스 attention과 가격 확인을 결합한 리서치 보조 자료이며 투자 조언이 아닙니다.",
        F["small"],
        130,
        fill=COLORS["muted"],
    )
    return img


def overview_page(ranking: pd.DataFrame, summary: pd.DataFrame) -> Image.Image:
    img, draw = new_page()
    text(draw, (MARGIN, 60), "전체 내러티브 개요", F["h1"])
    top = ranking.sort_values("attention_score", ascending=False).head(10).iloc[::-1]
    draw_bar_chart(draw, (MARGIN, 150, 760, 620), top["theme"].tolist(), top["attention_score"].tolist(), "Attention Score Top 10")
    draw_scatter(draw, (860, 150, 1510, 620), summary.sort_values("attention_score", ascending=False))

    rows = []
    merged = summary.sort_values(["attention_score", "company_support_score"], ascending=False).head(10)
    for _, row in merged.iterrows():
        rows.append(
            [
                row["theme"],
                fmt(row["attention_score"], 1),
                row["adjusted_confidence"],
                row["narrative_type"],
                fmt(row["company_support_score"], 1),
                row["news_linked_companies"],
            ]
        )
    draw_table(
        draw,
        (MARGIN, 720, PAGE_W - MARGIN, 1090),
        ["theme", "attn", "conf", "type", "support", "linked companies"],
        rows,
        "통합 요약",
    )
    return img


def theme_page(row: pd.Series, debug: pd.DataFrame, matrix: pd.DataFrame, daily: pd.DataFrame) -> Image.Image:
    img, draw = new_page()
    theme = row["theme"]
    theme_matrix = matrix[matrix["theme"] == theme].sort_values("company_narrative_score", ascending=False).head(10)
    companies = ", ".join(theme_matrix[theme_matrix["article_count_7d"] > 0]["ticker"].head(5).astype(str).tolist())

    text(draw, (MARGIN, 50), f"{int(row['rank'])}. {theme}", F["h1"])
    x = MARGIN
    x = pill(draw, (x, 100), f"attention {row['attention_score']:.1f}", COLORS["blue"])
    x = pill(draw, (x, 100), str(row["adjusted_confidence"]), COLORS["green"])
    pill(draw, (x, 100), str(row["narrative_type"]), COLORS["orange"])

    summary = (
        f"주요 단어: {row.get('top_items', '-')}\n"
        f"기사수 7d {fmt(row.get('article_count_7d'), 0)} | baseline 30d {fmt(row.get('baseline_article_count_30d'))} | "
        f"pure-play ratio {fmt(float(row.get('pure_play_ratio_7d', 0))*100, 1, '%')}\n"
        f"{reason_text(row, companies)}"
    )
    wrapped(draw, (MARGIN, 155), summary, F["small"], 150, fill=COLORS["text"])

    d = daily[daily["theme"] == theme].copy()
    if not d.empty:
        d["date"] = pd.to_datetime(d["date"])
        labels = [x.strftime("%m-%d") for x in d["date"]]
        values = d["article_count"].astype(float).tolist()
        draw_bar_chart(draw, (MARGIN, 385, 760, 675), labels[-12:], values[-12:], "Daily Article Count", COLORS["blue"])
    else:
        text(draw, (MARGIN, 430), "Daily data 없음", F["body"], COLORS["muted"])

    linked = theme_matrix.iloc[::-1]
    draw_bar_chart(
        draw,
        (860, 385, PAGE_W - MARGIN, 675),
        linked["ticker"].tolist(),
        linked["article_count_7d"].fillna(0).astype(float).tolist(),
        "Linked Companies: Article Count 7d",
        COLORS["green"],
    )

    rows = []
    spy_5d = 0.939858
    for _, r in theme_matrix.head(9).iterrows():
        rel5 = r.get("price_return_5d") - spy_5d if pd.notna(r.get("price_return_5d")) else float("nan")
        rows.append(
            [
                r["ticker"],
                str(r.get("company_narrative_role", "")).replace("_", " ")[:18],
                fmt(r.get("article_count_7d"), 0),
                fmt(r.get("source_breadth_7d"), 0),
                fmt(r.get("price_return_5d"), 1, "%"),
                fmt(rel5, 1, "%"),
                fmt(r.get("price_return_1m"), 1, "%"),
                str(r.get("price_state", "-")),
            ]
        )
    draw_table(
        draw,
        (MARGIN, 760, PAGE_W - MARGIN, 1090),
        ["ticker", "role", "art7d", "src7d", "5d", "5d-SPY", "1m", "state"],
        rows,
        "관련 종목과 최근 주가 흐름",
    )
    return img


def headlines_page(ranking: pd.DataFrame, debug: pd.DataFrame, top_n: int) -> Image.Image:
    img, draw = new_page()
    text(draw, (MARGIN, 55), "상위 내러티브별 샘플 헤드라인", F["h1"])
    y = 120
    for _, row in ranking.sort_values("attention_score", ascending=False).head(top_n).iterrows():
        theme = row["theme"]
        text(draw, (MARGIN, y), theme, F["body"], COLORS["blue"])
        y += 32
        titles = debug[debug["theme"] == theme]["title"].dropna().drop_duplicates().head(3).tolist()
        for title in titles:
            y = wrapped(draw, (MARGIN + 24, y), f"- {title}", F["tiny"], 150, line_gap=4) + 4
        y += 14
        if y > PAGE_H - 130:
            break
    return img


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranking", type=Path, default=RESULTS_DIR / "20260503_live_finnhub_37d_top25_v3_latest_theme_ranking.csv")
    parser.add_argument("--debug", type=Path, default=RESULTS_DIR / "20260503_live_finnhub_37d_top25_v3_theme_match_debug.csv")
    parser.add_argument("--matrix", type=Path, default=RESULTS_DIR / "20260503_live_finnhub_37d_top25_integrated_narrative_company.csv")
    parser.add_argument("--daily", type=Path, default=CACHE_DIR / "daily" / "20260503_live_finnhub_37d_top25_v3_daily_theme_attention.csv")
    parser.add_argument("--raw-finnhub", type=Path, default=CACHE_DIR / "raw" / "20260503_live_finnhub_37d_top25_attention_raw.csv")
    parser.add_argument("--raw-gdelt", type=Path, default=CACHE_DIR / "raw" / "20260503_live_gdelt_3d_sample_attention_raw.csv")
    parser.add_argument("--top-themes", type=int, default=8)
    parser.add_argument("--output", type=Path, default=RESULTS_DIR / f"{TODAY_STR}_narrative_attention_report.pdf")
    args = parser.parse_args()

    ranking = pd.read_csv(args.ranking).sort_values("attention_score", ascending=False).reset_index(drop=True)
    debug = pd.read_csv(args.debug)
    matrix = pd.read_csv(args.matrix)
    daily = pd.read_csv(args.daily)
    summary = build_theme_summary(ranking, matrix)

    pages = [
        cover_page(ranking, source_coverage(args.raw_finnhub, args.raw_gdelt)),
        overview_page(ranking, summary),
    ]
    for _, row in ranking.head(args.top_themes).iterrows():
        pages.append(theme_page(row, debug, matrix, daily))
    pages.append(headlines_page(ranking, debug, args.top_themes))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(args.output, "PDF", save_all=True, append_images=pages[1:], resolution=150.0)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
