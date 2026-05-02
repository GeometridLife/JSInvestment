# Apple(AAPL) 90일 내러티브 정성 분석 리포트

> 기준일: 2026-05-02  
> 분석 범위: Finnhub 90일 뉴스 + Reddit 90일 검색 결과 + GDELT 최근 보조 샘플  
> 데이터 소스: Finnhub, GDELT, Reddit  
> 입력 파일: `20260502_AAPL_90d_narrative_debug.csv`  
> 목적: 정량 스코어링 전, Apple을 둘러싼 시장의 핵심 narrative를 정성적으로 해석

---

## 1. Executive Summary

Apple의 최근 90일 내러티브는 **긍정적이지만 구조적 의심이 남아 있는 상태**로 판단된다.

최근 7~30일만 보면 Apple은 분명히 긍정 이벤트가 강하다. Q2 실적 호조, iPhone 매출 회복, 서비스 매출, 자사주매입 및 배당, 중국/인도 수요 회복이 반복적으로 언급된다. 특히 최근 뉴스 플로우는 Apple을 다시 **실적 확인형 메가캡**으로 재평가하는 방향이다.

하지만 90일 전체로 보면 이야기는 더 복잡하다. Apple은 여전히 AI/Siri 경쟁력, 리더십 전환 가능성, 관세와 공급망 비용, App Store 규제, 밸류에이션 부담이라는 overhang을 안고 있다. 즉, 시장은 Apple을 버리고 있지는 않지만, 과거처럼 무조건적인 프리미엄을 주기에는 몇 가지 질문을 계속 던지고 있다.

최종 정성 판정:

| 항목 | 판단 |
|---|---|
| Narrative Grade | `Positive With Overhang` |
| Screening Label | `earnings_buyback_recovery_with_ai_leadership_overhang` |
| 핵심 긍정 요인 | Q2 실적, iPhone/services, buyback, China/India |
| 핵심 부정 요인 | AI 지연, 리더십 불확실성, 관세/공급망, 규제, 밸류에이션 |
| 투자자 관심도 | 높음 |
| 데이터 신뢰도 | 중간 |

---

## 2. 데이터 커버리지

수집된 원천 문서는 총 3,443건이며, relevance filter를 통과한 문서는 1,300건이다. 단, source별 실제 커버리지는 다르다. Finnhub는 90일 커버리지로 해석 가능하지만, GDELT는 최신순 `maxrecords=100` 제한 때문에 최근 9일 보조 샘플로만 사용한다. Reddit은 90일 범위 검색 결과지만 Reddit search API 특성상 완전한 전수 데이터로 보지는 않는다.

| Source Type | Raw Count | Relevant Count |
|---|---:|---:|
| Finnhub news | 3,078 | 1,209 |
| GDELT news | 100 | 48 |
| Reddit post | 265 | 43 |
| Total | 3,443 | 1,300 |

실제 날짜 커버리지:

| Source Type | Date Range | Unique Days | Coverage 판단 |
|---|---|---:|---|
| Finnhub news | 2026-02-03 ~ 2026-05-02 | 73 | 90일 주 분석 소스 |
| Reddit post | 2026-02-02 ~ 2026-05-02 | 84 | 90일 retail 검색 샘플 |
| GDELT news | 2026-04-24 ~ 2026-05-02 | 9 | 최근 뉴스 보조 샘플 |

주요 지표:

| Metric | Value |
|---|---:|
| Relevance ratio | 37.8% |
| Relevant news source diversity | 44 |
| 90D positive docs | 388 |
| 90D neutral docs | 720 |
| 90D negative docs | 192 |
| 90D Reddit relevant posts | 43 |
| 90D Reddit raw engagement | 22,135 |

해석:

- 데이터 양은 Apple 단일 종목 분석에는 충분하다.
- 다만 raw 문서 중 실제 관련 문서는 37.8% 수준이므로, 단순 mention count를 그대로 쓰면 과대평가 위험이 있다.
- Finnhub/Yahoo 계열 뉴스 비중이 높고, GDELT는 90일 전체가 아니라 최근 뉴스 보조 샘플 성격이다.
- Reddit은 게시글 수는 많지 않지만 engagement가 커서 retail narrative 포착에는 유용하다. 다만 검색 API 샘플로 해석한다.

---

## 3. 핵심 내러티브 구조

Apple의 현재 내러티브는 Finnhub 90일 뉴스와 Reddit 90일 검색 결과를 주축으로, GDELT 최근 보조 샘플을 더해 다음 질문으로 요약할 수 있다.

> **Apple은 AI 불확실성과 규제 부담을 안고도, iPhone 수요, 서비스 매출, 자사주매입, 신흥시장 회복을 통해 다시 성장주 프리미엄을 정당화할 수 있는가?**

Apple은 현재 순수한 AI 성장주로 평가받고 있지는 않다. 오히려 시장은 Apple을 **성숙한 고품질 메가캡이 다시 성장성을 증명하려는 국면**으로 보고 있다.

최근 긍정 이벤트가 강하게 들어오면서 단기 narrative는 좋아졌지만, 장기 narrative는 여전히 "좋은 회사지만 다음 성장 동력은 무엇인가"라는 질문 위에 서 있다.

---

## 4. Bull Case: 긍정 내러티브

### 4.1 Q2 실적 호조

가장 강한 최근 catalyst는 Q2 실적이다. 수집된 뉴스에서는 record revenue, earnings beat, iPhone sales, upbeat outlook 같은 표현이 반복된다.

시장의 해석은 명확하다.

- Apple의 수요 둔화 우려가 일부 완화됐다.
- iPhone과 services가 여전히 실적을 견인할 수 있다.
- 단기적으로는 AI보다 실적이 주가 narrative를 다시 끌어올렸다.

이 점은 중요하다. Apple에 대한 최근 회의론은 "성장이 끝났다"는 쪽에 가까웠는데, Q2 실적은 적어도 그 우려를 단기적으로 반박하는 역할을 했다.

### 4.2 자사주매입과 배당

Apple의 buyback/dividend 관련 문서는 전체 topic 중 가장 크지는 않지만, 최근 긍정 이벤트에서는 중요한 역할을 한다.

성숙한 메가캡에서 자사주매입은 narrative 안정 장치다. 높은 성장률을 보여주지 못하더라도, 막대한 현금흐름과 주주환원은 투자자에게 downside cushion으로 인식된다.

해석:

- Apple은 여전히 현금 창출력이 강한 기업으로 인식된다.
- 성장주와 quality compounder 사이의 중간 narrative를 유지할 수 있다.
- 실적 호조와 buyback이 결합되면 단기 주가 반응이 커질 수 있다.

### 4.3 중국/인도 수요 회복

China/India 관련 문서는 Apple의 지역 성장 narrative를 보강한다.

중국은 기존 우려를 완화하는 역할을 한다. 최근 데이터에서는 China rebound, China tailwind 같은 프레임이 등장한다. 인도는 장기 성장 optionality다. 당장 전체 실적의 중심축은 아니지만, Apple이 앞으로 성장할 수 있는 지역적 여지를 제공한다.

해석:

- 중국 회복은 단기 sentiment 개선에 중요하다.
- 인도는 장기 성장 narrative를 지탱한다.
- 두 지역이 동시에 긍정적으로 언급되면 Apple의 "ex-growth" 프레임이 약해진다.

### 4.4 제품 생태계의 지속성

Finnhub 90일 뉴스와 Reddit 90일 검색 결과 기준으로 가장 큰 축은 iPhone/Product다. iPhone, iPad, Mac, Vision Pro, foldable, satellite connectivity, iOS 관련 뉴스와 게시글이 반복된다.

이는 Apple이 여전히 product cycle을 중심으로 논의되는 기업이라는 뜻이다. AI가 약하다는 비판이 있더라도, 시장은 Apple의 제품 생태계 자체를 버리지는 않고 있다.

해석:

- Apple의 기본 수요 기반은 여전히 강하다.
- 제품 cycle 기대가 완전히 사라지지 않았다.
- ecosystem durability는 Apple의 구조적 강점으로 남아 있다.

---

## 5. Bear Case: 부정 내러티브

Apple의 bearish narrative는 "Apple이 망가졌다"가 아니다. 더 정확히는 다음에 가깝다.

> **Apple은 여전히 좋은 회사지만, 다음 성장 구간은 더 느리고, 더 비싸고, 더 불확실할 수 있다.**

### 5.1 AI/Siri 경쟁력 의문

AI/Siri는 90일 topic 중 큰 비중을 차지한다. 이는 Apple의 AI narrative가 중요하다는 뜻이지만, 동시에 아직 명확한 확신을 주지 못하고 있다는 뜻이기도 하다.

뉴스와 Reddit 모두에서 Apple이 AI에서 뒤처졌는지, Siri/Apple Intelligence가 충분히 강한 성장 동력이 될 수 있는지에 대한 의심이 나타난다.

리스크:

- AI narrative가 약하면 Apple은 mature hardware/services 기업으로만 평가될 수 있다.
- AI 기대감이 높은 시장 환경에서 multiple compression 요인이 될 수 있다.
- "좋은 실적"과 "새로운 성장 프리미엄"은 다른 문제다.

### 5.2 리더십 전환 불확실성

Reddit engagement 상위권에는 Tim Cook, John Ternus, CEO transition 관련 게시글이 크게 잡힌다.

이 부분은 특히 조심해야 한다. 현재 수집 데이터에서 engagement가 크다고 해서 공식 이벤트로 확정할 수는 없다. 하지만 중요한 것은 시장 참여자들이 Apple의 리더십 전환 가능성에 민감하게 반응하고 있다는 점이다.

리스크:

- 리더십 루머는 narrative volatility를 키운다.
- 공식 확인 전까지는 낮은 신뢰도의 고관심 이벤트로 분리해야 한다.
- Apple은 경영진 신뢰도가 valuation에 반영되는 기업이므로, succession narrative는 무시하기 어렵다.

### 5.3 관세, 공급망, 비용 압박

tariff, supply chain, memory shortage, component cost, India/China manufacturing 관련 문서도 반복된다.

최근 실적이 좋아도 비용 압박이 커지면 시장은 margin을 의심할 수 있다. Apple은 하드웨어 매출 비중이 크고 글로벌 공급망이 복잡하기 때문에, 관세/공급망 뉴스가 narrative에 미치는 영향이 크다.

리스크:

- 매출 호조가 margin pressure로 상쇄될 수 있다.
- 관세/무역 정책 뉴스가 단기 sentiment를 흔들 수 있다.
- 공급망 이슈는 제품 출시 및 가격 전략에 영향을 줄 수 있다.

### 5.4 App Store 및 규제 리스크

regulatory/legal topic도 무시하기 어렵다. App Store, antitrust, legal pressure는 Apple의 services narrative에 직접 연결된다.

Apple의 bull case에서 services는 매우 중요하다. 그런데 services는 동시에 규제 리스크에 가장 노출된 영역 중 하나다.

리스크:

- App Store 수수료 구조가 압박받으면 services margin narrative가 약해질 수 있다.
- 고마진 서비스 매출의 질에 대한 의심이 커질 수 있다.

### 5.5 밸류에이션 부담

valuation/analyst topic이 꾸준히 많다. 이는 시장이 Apple을 "좋은 회사인가"보다 "지금 가격에 살 만한가"로 보고 있다는 뜻이다.

리스크:

- 좋은 실적에도 valuation이 높으면 상승 여력이 제한될 수 있다.
- AI narrative가 약하면 프리미엄 multiple을 방어하기 어렵다.

---

## 6. Retail Narrative

Reddit 기준 retail narrative는 높지만 혼재되어 있다.

90일 범위에서 검색된 관련 Reddit 게시글은 43건이고, raw engagement 합계는 22,135다. 다만 Reddit search API 결과이므로 전수 수집이라기보다 retail 관심을 보는 샘플로 해석한다. 특히 몇 개 대형 게시글이 engagement를 크게 끌어올렸다.

상위 retail theme:

- Tim Cook / John Ternus 리더십 전환
- Apple Q2 earnings beat
- iPhone 17 및 product cycle
- "AAPL no AI" 우려
- China/Taiwan geopolitical concern
- Big Tech 비교: Apple vs Microsoft/Nvidia/Meta/Google/Amazon

Retail 해석:

- Apple에 대한 관심은 매우 높다.
- 실적 호조는 인정받고 있다.
- 그러나 AI, 리더십, 밸류에이션에 대한 의심이 계속 남아 있다.
- retail은 강한 bullish consensus라기보다 **engaged but unconvinced**에 가깝다.

---

## 7. News / Institutional Narrative

뉴스 쪽 tone은 Reddit보다 더 건설적이다.

최근 뉴스는 Apple을 다음 프레임으로 다룬다.

- Q2 beat
- record revenue
- iPhone demand
- services strength
- buyback/dividend
- China/India recovery
- analyst constructive commentary

그러나 동시에 반복되는 주의점도 있다.

- AI delay
- margin pressure
- tariff/supply chain cost
- App Store legal risk
- CEO succession

해석:

뉴스 narrative는 **positive event-driven**이다. Apple은 실적으로 신뢰를 회복하고 있지만, 아직 AI 기반의 장기 성장 narrative까지 확보한 것은 아니다.

---

## 8. Catalyst / Risk Map

| 항목 | 방향 | 신뢰도 | 해석 |
|---|---|---|---|
| Q2 실적 호조 | 긍정 | 높음 | 가장 강한 최근 catalyst |
| iPhone/services 수요 | 긍정 | 높음 | 실적 narrative의 핵심 |
| 자사주매입/배당 | 긍정 | 높음 | mature compounder narrative 강화 |
| 중국 회복 | 긍정 | 중간 | 기존 우려 완화 |
| 인도 성장 | 긍정 | 중간 | 장기 성장 optionality |
| AI/Siri catch-up | 혼합 | 중간 | 성공 시 re-rating, 실패 시 multiple 부담 |
| 리더십 전환 | 혼합/위험 | 낮음 | 관심은 높지만 공식 검증 필요 |
| 관세/공급망 | 부정 | 중간 | margin 및 sentiment risk |
| App Store/규제 | 부정 | 중간 | services bull case를 훼손할 수 있음 |
| 밸류에이션 | 혼합/부정 | 높음 | 좋은 뉴스가 이미 반영됐는지 논쟁 |

---

## 9. Verification Queue

다음 항목은 narrative score에 바로 반영하기 전에 공식 확인이 필요하다.

| 항목 | 이유 | 확인 소스 |
|---|---|---|
| Tim Cook / John Ternus 리더십 전환 | Reddit engagement가 매우 크며 score 왜곡 가능 | Apple IR, SEC 8-K, Apple Newsroom |
| Q2 revenue / EPS / buyback 규모 | 핵심 긍정 catalyst | Apple earnings release, 10-Q |
| China/India 회복 | bull case의 지역 성장 근거 | earnings call transcript |
| tariff refund / cost pressure | margin risk | management commentary, filing |
| App Store / antitrust 이슈 | services risk | legal docket, regulator release, company filing |

---

## 10. 최종 판단

Apple은 현재 **강한 긍정 이벤트와 구조적 의심이 공존하는 종목**이다. 이 판단은 Finnhub 90일 뉴스와 Reddit 90일 검색 샘플을 중심으로 하며, GDELT는 최근 9일 뉴스 보조 확인용으로만 반영했다.

최근 7~30일 narrative는 분명히 좋아졌다. 실적 호조, iPhone/services, buyback, China/India 회복이 Apple을 다시 긍정적으로 보게 만든다.

하지만 90일 전체로 보면 Apple은 아직 완전히 깨끗한 상승 narrative가 아니다. AI/Siri 신뢰 부족, 리더십 루머, 공급망/관세, 규제, 밸류에이션 부담이 남아 있다.

따라서 스크리닝 관점에서 Apple은 다음처럼 분류한다.

```text
Narrative Grade: Positive With Overhang
Narrative Label: earnings_buyback_recovery_with_ai_leadership_overhang
Attention: High
Event Momentum: High Positive
Retail Interest: High but Mixed
Risk Overhang: Medium
Data Quality: Medium
```

투자 narrative 한 줄 요약:

> Apple은 실적과 자본환원으로 다시 설득력을 얻고 있지만, AI와 리더십, 밸류에이션에 대한 질문이 사라지기 전까지는 "강한 긍정 모멘텀 + 명확한 overhang"을 동시에 가진 종목이다.

---

## 11. Phase C로 넘길 Feature 후보

정량 스코어링에 사용할 후보 feature:

- `relevant_news_count_7d`
- `relevant_news_count_30d`
- `relevant_news_count_90d`
- `source_diversity_30d`
- `relevant_reddit_count_7d`
- `relevant_reddit_count_30d`
- `reddit_log_engagement_7d`
- `reddit_log_engagement_30d`
- `positive_event_count_7d`
- `negative_event_count_7d`
- `earnings_growth_topic_count_30d`
- `ai_siri_topic_count_90d`
- `leadership_topic_count_30d`
- `tariff_supply_chain_topic_count_30d`
- `regulatory_legal_topic_count_90d`
- `relevance_ratio`
- `event_verification_needed`
