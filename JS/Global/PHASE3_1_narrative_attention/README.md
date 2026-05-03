# PHASE3_1: Narrative Attention Tracker

작성일: 2026-05-03

## 목적

PHASE3의 기업별 narrative 수집을 보완하는 시장 전체 attention tracker다.

```text
PHASE3   : tickers → news       (기업별 narrative)
PHASE3_1 : news → themes/tickers (시장 전체 attention 분포)
```

핵심 질문:

> 지금 시장에서 어떤 narrative가 뜨거워지고 있고, 어떤 narrative가 식어가는가?

## 현재 구조

```text
PHASE3_1_narrative_attention/
├── README.md
├── docs/
│   ├── attention_tracker_design.md
│   └── beneficiary_stock_design.md
├── config/
│   └── themes.json
├── scripts/
│   ├── live_attention_collector.py
│   └── prototype_attention_from_cache.py
├── cache/
│   ├── raw/
│   └── daily/
├── results/
└── logs/
```

## 문서

| 문서 | 내용 |
|---|---|
| [attention_tracker_design.md](docs/attention_tracker_design.md) | narrative attention 수집, scoring, confidence layer, 데이터 흐름 설계 |
| [beneficiary_stock_design.md](docs/beneficiary_stock_design.md) | 뜨는 narrative를 수혜주 후보군으로 연결하는 exposure/purity/confirmation/risk 설계 |

## 핵심 설계 요약

### Attention Tracker

- Finnhub `company-news`를 30~90일 baseline의 메인 소스로 사용한다.
- GDELT는 1~3일 pulse/breadth 보조 지표로 사용한다.
- Reddit은 retail spike 보조 지표로 사용한다.
- `attention_score`는 관심 증가 강도이고, `adjusted_confidence`와 `narrative_type`은 그 신호를 믿을 수 있는지 판단한다.

현재 scoring:

```text
news_attention =
  0.80 * finnhub_company_log_share_change_pct
+ 0.20 * gdelt_log_share_change_pct

retail_attention =
  0.60 * reddit_log_share_change_pct
+ 0.40 * reddit_engagement_change_pct

attention_score =
  0.65 * news_attention
+ 0.15 * retail_attention
+ 0.15 * breadth_score
+ 0.10 * z_score_pct
```

### Confidence Layer

`attention_score`가 높아도 단일 이벤트나 파생 mention일 수 있으므로 별도 신뢰도 레이어를 둔다.

주요 출력:

- `adjusted_confidence`: `very_high`, `high`, `medium`, `low`
- `narrative_type`: `sustained_narrative`, `emerging_watch`, `derivative_mention`, `single_event`, `noise_possible`
- `daily_active_days_7d`
- `unique_ticker_count_7d`
- `top_ticker_share_7d`
- `top_headline_cluster_share_7d`
- `pure_play_ratio_7d`
- `event_concentration_score`

### Beneficiary Stock

수혜주는 theme attention을 그대로 종목 점수로 쓰지 않고 아래 4개 축을 분리한다.

```text
beneficiary_score =
  0.40 * exposure_score
+ 0.25 * purity_score
+ 0.25 * confirmation_score
- 0.20 * risk_penalty
```

후보군 bucket:

- `pure_play`: 직접 수혜, 민감도 높음
- `enabler`: 핵심 부품/인프라 제공자
- `adopter`: 테마를 활용하는 대형 수요자
- `sympathetic`: 같이 움직이지만 직접성은 낮은 후보

## 실행

### Finnhub 37일 baseline 수집

```bash
FINNHUB_API_KEY=... python3 JSInvestment/JS/Global/PHASE3_1_narrative_attention/scripts/live_attention_collector.py \
  --sources finnhub_company \
  --days 37 \
  --finnhub-window-days 7 \
  --limit 25 \
  --max-records-per-ticker 300 \
  --sleep 1.0 \
  --output-prefix 20260503_live_finnhub_37d_top25
```

### Attention score 계산

```bash
python3 JSInvestment/JS/Global/PHASE3_1_narrative_attention/scripts/prototype_attention_from_cache.py \
  --input JSInvestment/JS/Global/PHASE3_1_narrative_attention/cache/raw/20260503_live_finnhub_37d_top25_attention_raw.csv \
  --output-prefix 20260503_live_finnhub_37d_top25
```

## 최근 산출물

| 산출물 | 설명 |
|---|---|
| `results/20260503_live_finnhub_37d_top25_v3_analysis_ko.md` | v3 confidence layer 적용 후 한국어 분석 |
| `results/20260503_live_finnhub_37d_top25_v3_latest_theme_ranking.csv` | v3 ranking CSV |
| `results/20260503_live_finnhub_37d_top25_v3_attention_report.md` | 자동 생성 attention report |

## 다음 단계

- `sustained_narrative` + `adjusted_confidence >= high` 테마부터 beneficiary scoring 구현
- `derivative_mention` 테마는 pure-play basket 추가 수집으로 검증
- `noise_possible` 테마는 수혜주 후보 생성 대상에서 제외하고 watch queue로 분리
