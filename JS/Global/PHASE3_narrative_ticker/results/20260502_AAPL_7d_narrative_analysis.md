# AAPL 7D Narrative Analysis

> 기준 데이터: 2026-05-02 수집 raw CSV  
> 입력 소스: Finnhub, GDELT, Reddit  
> 주의: 7일 샘플 기반의 1차 정성 분석이며, 정식 스코어링 전 relevance filter 검토용이다.

## Raw Coverage

| Source Type | Raw Count |
|---|---:|
| Finnhub news | 20 |
| GDELT news | 10 |
| Reddit post | 32 |
| Total | 62 |

제목 기준 간이 relevance filter를 적용하면 관련 문서는 약 27건으로 축소된다.

| Source Type | Relevant Count |
|---|---:|
| Finnhub news | 7 |
| GDELT news | 8 |
| Reddit post | 12 |
| Total | 27 |

관련 뉴스 source diversity는 7개, 관련 Reddit engagement 합계는 1,689, `log1p(score + comments)` 합계는 약 51.6이다.

## Main Narrative

Apple의 최근 7일 내러티브는 **Q2 실적 호조와 주주환원 강화**가 중심이다.

핵심 긍정 신호:

- record quarterly revenue
- earnings/revenue beat
- services business strength
- large share buyback
- China/India demand recovery
- Tim Cook leadership commentary

특히 Finnhub/GDELT 모두에서 `record quarter`, `Q2 earnings`, `share buyback`, `China tailwind`, `India growth`가 반복된다. 뉴스 내러티브만 보면 Apple은 단기적으로 **실적 확인 + 자사주매입 + 글로벌 수요 회복** 조합이 강하다.

## Retail Narrative

Reddit에서는 긍정과 회의가 섞인다.

긍정:

- `Apple reports earnings and revenue beat, boosted by services business`
- `AAPL Quarterly Revenue $111.2 billion (up 17% YoY)`
- `AAPL Soars Continuously; an All-Time High Is Within Reach`
- `Can AAPL Sustain Its Rapid Growth?`

회의:

- `AAPL - no AI, no Tim Cook, no problem!`
- revenue guidance가 가격 인상 효과인지에 대한 의문
- valuation 부담과 성장 지속성에 대한 질문

즉 retail 쪽에서는 **실적은 인정하지만 AI 모멘텀과 성장 질에 대한 의심이 남아 있는 상태**로 해석한다.

## Preliminary Signal

| Category | Signal | Comment |
|---|---|---|
| News attention | Strong | 관련 뉴스와 source breadth가 모두 양호 |
| Event momentum | Strong positive | earnings beat, buyback, services, China/India |
| Retail attention | Moderate to strong | engagement는 높지만 discussion noise 포함 |
| Retail tone | Mixed positive | 실적 호조 vs AI/valuation 의심 |
| Data quality | Medium | Finnhub도 시장 전체 기사, GDELT도 간접 기사 섞임 |

## Interpretation

Apple은 현재 샘플 기준으로 **긍정 이벤트 기반 내러티브가 강한 종목**이다. 다만 이 강도는 순수 제품 혁신 또는 AI 기대감보다 **실적 확인, 서비스 매출, 자사주매입, 지역 수요 회복**에 더 많이 기댄다.

스크리닝 관점에서는 다음처럼 분류한다.

- `attention_score`: 높음
- `event_score`: 높음
- `retail_score`: 중상
- `risk_signal`: 중간
- `narrative_label`: `earnings_buyback_recovery`

정식 스코어링에서는 `market-wide`, `ETF`, `daily discussion` 문서를 제거하지 않으면 Apple의 mention count가 과대평가될 수 있다.
