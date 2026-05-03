# AAPL 90D Narrative Analysis

> 기준일: 2026-05-02  
> 입력 소스: Finnhub 90D chunk 수집, GDELT 90D 보조 수집, Reddit 90D 검색  
> 분석 방식: README의 `dedupe -> relevance filter -> source별 metric -> event/tone 분류` 순서 적용

## Input Coverage

| Source Type | Raw Count | Relevant Count |
|---|---:|---:|
| Finnhub news | 3,078 | 1,209 |
| GDELT news | 100 | 48 |
| Reddit post | 265 | 43 |
| Total | 3,443 | 1,300 |

- `relevance_ratio`: 37.8%
- Relevant news source diversity: 44
- GDELT는 `maxrecords=100` 보조 샘플이라 최근 구간에 편중되어 있다.
- Finnhub는 7일 window로 쪼개 수집해 2026-02-03부터 2026-05-02까지 커버했다.

## Window Metrics

| Window | Relevant Docs | Finnhub | GDELT | Reddit |
|---|---:|---:|---:|---:|
| 7D | 199 | 144 | 41 | 14 |
| 30D | 525 | 450 | 48 | 27 |
| 90D | 1,300 | 1,209 | 48 | 43 |

Reddit relevant engagement:

| Window | Relevant Posts | Raw Engagement | Log Engagement |
|---|---:|---:|---:|
| 7D | 14 | 2,453 | 63.13 |
| 30D | 27 | 17,231 | 132.02 |
| 90D | 43 | 22,135 | 191.12 |

## Tone

| Tone | 90D Count | 30D Count |
|---|---:|---:|
| Positive | 388 | 198 |
| Neutral | 720 | 260 |
| Negative | 192 | 67 |

최근 30일은 90일 전체보다 긍정 비중이 높다. 이는 5월 초 Q2 실적, iPhone sales, buyback/dividend, China/India demand 관련 뉴스가 긍정 이벤트로 잡혔기 때문이다.

## Topic Counts

| Topic | 90D Relevant Docs | 30D Relevant Docs |
|---|---:|---:|
| iPhone/Product | 470 | 185 |
| Earnings/Growth | 347 | 199 |
| AI/Siri | 274 | 74 |
| Valuation/Analyst | 240 | 87 |
| Leadership | 208 | 147 |
| Regulatory/Legal | 181 | 51 |
| Tariff/Supply Chain | 159 | 43 |
| China/India | 110 | 40 |
| Shareholder Return | 48 | 26 |

## Narrative Phases

### 1. 90D Base Narrative: Product + AI + Valuation

90일 전체에서는 Apple의 내러티브가 `iPhone/product`, `AI/Siri`, `valuation/analyst` 중심으로 넓게 분산된다. Apple Intelligence, Siri, AI 경쟁력, iPhone 17/Ultra/foldable 등 제품 기대가 반복되지만, 동시에 "AI에서 뒤처졌는가"라는 의심도 계속 나온다.

해석:

- 제품 생태계와 iPhone 관련 관심은 매우 높다.
- AI는 기대와 불안이 같이 존재한다.
- valuation 관련 글이 많아 "좋은 회사지만 비싼가"라는 프레임이 유지된다.

### 2. Recent 30D Narrative: Earnings + Leadership + Product

최근 30일에는 `earnings/growth`, `leadership`, `product`가 강해졌다. 특히 Reddit engagement 상위권은 Tim Cook/John Ternus 리더십 전환 관련 게시글에 집중되어 있다.

해석:

- 단순 실적 뉴스만이 아니라 leadership narrative가 retail attention을 크게 끌었다.
- Reddit에서는 Tim Cook 관련 게시글이 대형 engagement를 만들었다.
- 이 이슈는 사실 여부 검증이 필요한 event narrative로 별도 플래그 처리해야 한다.

### 3. Recent 7D Narrative: Q2 Beat + Buyback + China/India Recovery

최근 7일은 가장 명확하다. 핵심은 Q2 실적 호조다.

반복되는 긍정 이벤트:

- Apple shares soar after record quarterly revenue
- Q2 earnings/revenue beat
- iPhone sales and services strength
- share buyback/dividend raise
- China rebound
- India growth

반복되는 리스크:

- AI momentum 부족
- memory shortage / supply constraints
- tariff/trade pressure
- growth quality가 가격 인상 또는 일시적 수요인지에 대한 의문

## Retail Narrative

Reddit relevant post는 90일 기준 43건이고 engagement는 22,135로 높다. 하지만 대부분의 engagement가 몇 개 대형 게시글에 집중된다.

상위 retail themes:

- Tim Cook stepping down / John Ternus succession
- Apple Q2 earnings and revenue beat
- AAPL no AI / no Tim Cook concern
- iPhone 17 / satellite connectivity
- China/Taiwan geopolitical concern
- Big Tech 비교: AAPL vs MSFT/NVDA/META/GOOGL/AMZN

Retail tone은 mixed positive다. 실적과 브랜드/제품은 인정하지만, AI와 leadership, valuation에 대한 질문이 계속 남아 있다.

## Preliminary Scores

단일 종목 분석이라 universe percentile은 계산하지 않고 정성 등급으로만 표시한다.

| Category | Signal | Reason |
|---|---|---|
| `attention_score` | High | 90D relevant 1,300건, news source diversity 44 |
| `retail_score` | High | 90D relevant Reddit engagement 22,135, 30D 집중도 높음 |
| `event_score` | High Positive | Q2 beat, record revenue, buyback, services/iPhone strength |
| `risk_signal` | Medium | AI/Siri lag, tariff/supply chain, valuation, leadership uncertainty |
| `data_quality` | Medium | raw 중 relevant 37.8%, Finnhub/Yahoo 편중, GDELT cap |

## Final Narrative Label

`earnings_buyback_recovery_with_ai_leadership_overhang`

Apple의 90일 내러티브는 **제품/AI/밸류에이션 논쟁을 배경으로 깔고, 최근 30일에는 리더십 이슈와 실적 이벤트가 강하게 부상했으며, 최근 7일에는 Q2 실적 호조와 자사주매입/수요 회복이 긍정 모멘텀을 주도**하는 형태다.

스크리닝 관점에서는 Apple을 "강한 이벤트 모멘텀 + 높은 retail attention + 중간 수준의 구조적 의심" 종목으로 분류한다.

## Implementation Notes

- 90일 Finnhub 수집은 반드시 `--finnhub-window-days 7`처럼 chunk 수집을 사용한다.
- `max_records`에 닿으면 최신/과거 구간이 누락될 수 있으므로 Apple급 대형주는 `--max-records 10000` 이상을 권장한다.
- 정식 스코어링에서는 Tim Cook succession 같은 고 engagement 이벤트를 SEC/공식 뉴스로 검증하는 `event_verification` 플래그가 필요하다.
