# Amazon(AMZN) 90일 내러티브 정성 분석 리포트

> 기준일: 2026-05-02  
> 분석 대상: Amazon.com Inc. (`AMZN`)  
> 분석 범위: Finnhub 90일 뉴스 + Reddit 90일 검색 결과 + GDELT 최근 보조 샘플  
> 데이터 소스: Finnhub, GDELT, Reddit  
> 입력 파일: `20260502_AMZN_90d_narrative_debug.csv`  
> 목적: 정량 스코어링 전, Amazon을 둘러싼 시장의 핵심 narrative를 정성적으로 해석

---

## 1. Executive Summary

Amazon의 최근 90일 내러티브는 **AWS/AI 성장 기대와 CAPEX·마진 부담이 충돌하는 상태**로 판단된다.

최근 30일 뉴스 흐름에서는 AWS, Anthropic, Bedrock, agentic AI, Trainium, AI infrastructure 관련 이야기가 강하게 부상했다. 시장은 Amazon을 단순 전자상거래 기업이 아니라 **AWS와 AI 인프라를 가진 hyperscaler**로 다시 보고 있다.

하지만 Reddit과 일부 뉴스에서는 CAPEX 부담, earnings miss, 고평가 논쟁, 클라우드 투자 회수 가능성에 대한 우려가 크다. 특히 retail에서는 "Amazon이 AI를 위해 너무 많이 쓰는 것 아닌가"라는 질문이 반복된다.

최종 정성 판정:

| 항목 | 판단 |
|---|---|
| Narrative Grade | `Positive With Capex/Margin Overhang` |
| Screening Label | `aws_ai_infrastructure_momentum_with_capex_margin_overhang` |
| 핵심 긍정 요인 | AWS, AI/Anthropic, Trainium, advertising, retail scale |
| 핵심 부정 요인 | CAPEX 부담, margin pressure, earnings miss 기억, 밸류에이션 |
| 투자자 관심도 | 높음 |
| 데이터 신뢰도 | 중간 |

---

## 2. 데이터 커버리지

수집된 원천 문서는 총 3,490건이며, relevance filter를 통과한 문서는 1,275건이다. Finnhub와 Reddit은 90일 범위에서 수집됐고, GDELT는 최신순 `maxrecords=100` 제한 때문에 최근 보조 샘플로만 사용한다.

| Source Type | Raw Count | Relevant Count |
|---|---:|---:|
| Finnhub news | 3,183 | 1,168 |
| GDELT news | 100 | 43 |
| Reddit post | 207 | 64 |
| Total | 3,490 | 1,275 |

실제 날짜 커버리지:

| Source Type | Date Range | Coverage 판단 |
|---|---|---|
| Finnhub news | 2026-02-06 ~ 2026-05-02 | 90일 주 분석 소스 |
| Reddit post | 2026-02-03 ~ 2026-05-02 | 90일 retail 검색 샘플 |
| GDELT news | 2026-04-24 ~ 2026-05-02 | 최근 뉴스 보조 샘플 |

주요 지표:

| Metric | Value |
|---|---:|
| Relevance ratio | 36.5% |
| Relevant news source diversity | 26 |
| 90D positive docs | 311 |
| 90D neutral docs | 766 |
| 90D negative docs | 198 |
| 90D Reddit relevant posts | 64 |
| 90D Reddit raw engagement | 38,895 |

해석:

- 데이터 양은 충분하다.
- relevance ratio는 Apple과 비슷한 수준이다. Amazon은 시장 전체/Big Tech/AI 기사에 자주 섞이므로 필터가 필수다.
- Reddit engagement는 높지만, 몇 개 대형 게시글이 전체를 크게 좌우한다.
- GDELT는 최근 9일 보조 샘플로만 해석한다.

---

## 3. 핵심 내러티브 구조

Amazon의 현재 내러티브는 다음 질문으로 요약할 수 있다.

> **Amazon은 AWS와 AI 인프라를 통해 다시 고성장 hyperscaler로 재평가될 수 있는가, 아니면 AI CAPEX와 마진 부담이 그 재평가를 제한할 것인가?**

Amazon은 더 이상 단순 retail/e-commerce 이야기로만 움직이지 않는다. 최근 narrative의 중심은 AWS, AI, Anthropic, Trainium, Bedrock, agentic AI, cloud infrastructure다. 다만 이 긍정 narrative는 CAPEX와 margin에 대한 의심을 동시에 낳는다.

---

## 4. Bull Case: 긍정 내러티브

### 4.1 AWS와 AI 인프라 재평가

가장 강한 topic은 `AI/Anthropic`과 `AWS/Cloud`다. 90일 관련 문서에서 AI/Anthropic topic은 517건, AWS/Cloud topic은 335건이다.

최근 뉴스는 Amazon을 AI 인프라 기업으로 다시 해석한다.

긍정적 해석:

- AWS는 AI workload를 흡수할 수 있는 핵심 인프라다.
- Bedrock과 Anthropic exposure는 Amazon의 AI narrative를 강화한다.
- Trainium과 custom chip 이야기는 Nvidia 의존도를 줄일 수 있는 optionality로 해석된다.
- Amazon은 retail보다 cloud/AI multiple을 받을 수 있는 여지가 있다.

### 4.2 Anthropic / Agentic AI narrative

Anthropic, Claude, agentic AI 관련 뉴스가 강하다. 이는 Amazon의 AI strategy를 더 구체적으로 보이게 만든다.

긍정적 의미:

- Amazon은 AI 모델을 직접 소유하지 않더라도 distribution과 infra layer에서 수익화할 수 있다.
- Anthropic과 AWS의 결합은 enterprise AI 수요를 끌어오는 narrative가 된다.
- AI가 AWS 성장률을 다시 끌어올릴 수 있다는 기대가 생긴다.

### 4.3 Advertising과 retail scale

Advertising topic은 58건으로 AI/AWS보다 작지만, Amazon의 margin narrative에 중요하다. Retail/e-commerce topic은 202건이다.

긍정적 의미:

- Retail은 규모의 경제와 소비자 접점을 제공한다.
- Advertising은 고마진 사업으로 operating margin 개선에 기여할 수 있다.
- Prime, marketplace, logistics는 Amazon ecosystem의 defensibility를 유지한다.

### 4.4 실적 이후 재평가 가능성

최근 뉴스에는 price target raise, AWS growth, Amazon breakout, undervalued AWS growth 같은 프레임이 등장한다.

긍정적 의미:

- 시장은 Amazon의 AWS/AI 가치를 다시 평가하려는 움직임을 보인다.
- CAPEX 우려가 줄어들면 re-rating 여지가 있다.

---

## 5. Bear Case: 부정 내러티브

Amazon의 bearish narrative는 다음에 가깝다.

> **AWS와 AI는 강하지만, 그 성장을 얻기 위해 지출해야 하는 돈이 너무 크고, retail margin과 valuation이 이를 충분히 보상하는지 불확실하다.**

### 5.1 AI CAPEX 부담

CAPEX/Infrastructure topic은 290건이다. 이는 Amazon narrative에서 매우 중요한 양면적 주제다.

리스크:

- AI 인프라 투자가 과도하면 free cash flow가 압박받을 수 있다.
- AWS 성장률이 CAPEX 증가를 정당화하지 못하면 multiple이 눌릴 수 있다.
- Reddit에서는 "AMZN이 AI 때문에 너무 많이 쓴다"는 우려가 강하게 반응했다.

### 5.2 실적 미스와 spending forecast 기억

Reddit 상위 engagement에는 `Amazon stock falls 10% on $200 billion spending forecast, earnings miss`가 포함된다. 이는 최근 90일 retail narrative에서 Amazon의 부정 프레임이 아직 살아 있음을 보여준다.

리스크:

- 실적 beat가 나오더라도 투자자들은 CAPEX guidance를 더 민감하게 볼 수 있다.
- Amazon은 성장보다 투자 비용이 먼저 보이는 구간에서 narrative가 약해질 수 있다.

### 5.3 Margin pressure

Retail, logistics, fulfillment, delivery cost는 Amazon의 구조적 부담이다. AWS와 ads는 고마진 사업이지만, 전체 기업 narrative는 여전히 retail margin과 물류 비용에 영향을 받는다.

리스크:

- 소비 둔화 또는 물류 비용 상승 시 retail margin이 압박받을 수 있다.
- AI CAPEX와 retail 비용이 동시에 커지면 earnings quality가 의심받을 수 있다.

### 5.4 규제와 노동 이슈

Regulatory/Labor topic은 148건이다. Amazon은 antitrust, FTC, 노동/union, privacy, marketplace seller 이슈에 노출되어 있다.

리스크:

- marketplace power와 labor practice에 대한 규제는 장기 overhang이다.
- AWS/AI 이슈와 별개로 retail platform 규제가 sentiment를 훼손할 수 있다.

### 5.5 밸류에이션 논쟁

Valuation topic은 232건이다. 최근 Amazon이 AI/AWS narrative로 재평가받고 있지만, 34x earnings, price target, analyst debate 같은 프레임이 동시에 존재한다.

리스크:

- AI/AWS 기대가 이미 가격에 반영됐는지 논쟁이 있다.
- CAPEX가 커질수록 valuation 정당화 기준이 높아진다.

---

## 6. Retail Narrative

Amazon의 Reddit 관련 게시글은 64건이고, raw engagement 합계는 38,895다.

상위 retail theme:

- AMZN earnings miss / spending forecast
- AWS vs Microsoft/Google AI CAPEX
- Anthropic funding / AI model competition
- AMZN undervaluation / underperformance
- Big Tech 비교: AMZN, GOOGL, MSFT, META, NVDA
- Buy the dip narrative

Retail 해석:

- Retail은 Amazon을 좋은 회사로 보지만 CAPEX와 실적 변동성에 민감하다.
- AWS/AI narrative는 긍정적이나, "얼마를 써야 하는가"가 핵심 불안이다.
- Amazon은 Apple보다 high beta이고, Google보다 margin/CAPEX 회의가 더 강하다.

---

## 7. News / Institutional Narrative

뉴스 쪽 narrative는 AI/AWS 중심으로 건설적이다.

최근 긍정 프레임:

- AWS growth
- Anthropic / Bedrock / agentic AI
- Trainium chip business
- price target raise
- Pentagon AI deals
- undervalued AWS growth
- Amazon breakout after earnings

반복되는 우려:

- cloud cash burn
- AI CAPEX divergence
- spending forecast
- valuation
- regulatory/labor pressure

해석:

뉴스 narrative는 **AWS/AI 재평가**가 중심이다. 하지만 Amazon은 AI 인프라 성장주와 비용 부담 기업이라는 두 프레임이 동시에 존재한다.

---

## 8. Catalyst / Risk Map

| 항목 | 방향 | 신뢰도 | 해석 |
|---|---|---|---|
| AWS 성장 | 긍정 | 높음 | Amazon re-rating의 핵심 |
| Anthropic / Bedrock | 긍정 | 중~높음 | enterprise AI narrative |
| Trainium/custom chip | 긍정 | 중간 | AI infra optionality |
| Advertising growth | 긍정 | 중간 | margin 개선 축 |
| Retail scale / Prime | 긍정 | 중간 | ecosystem durability |
| AI CAPEX 증가 | 혼합/부정 | 높음 | 성장 투자이자 FCF 부담 |
| Earnings miss 기억 | 부정 | 중간 | retail sentiment overhang |
| Logistics / fulfillment cost | 부정 | 중간 | margin risk |
| Regulatory / labor pressure | 부정 | 중간 | platform overhang |
| Valuation debate | 혼합 | 중간 | AWS/AI 기대 반영 여부가 핵심 |

---

## 9. Verification Queue

다음 항목은 narrative score에 바로 반영하기 전에 공식 확인이 필요하다.

| 항목 | 이유 | 확인 소스 |
|---|---|---|
| AWS revenue / operating income growth | 핵심 긍정 catalyst | Amazon earnings release, 10-Q |
| CAPEX guidance / AI infra spending | 핵심 risk overhang | earnings call, 10-Q |
| Anthropic 관련 투자/협력 | AI narrative 검증 | official release, filings |
| Trainium chip revenue 가능성 | upside optionality | AWS disclosure, management commentary |
| Advertising growth | margin 개선 근거 | earnings release |
| FTC / antitrust / labor 이슈 | platform risk | regulator releases, legal docket |

---

## 10. 최종 판단

Amazon은 현재 **AWS와 AI 인프라로 재평가받을 수 있는 강한 narrative를 가진 종목**이다. 하지만 CAPEX와 margin 부담 때문에 Google보다 더 "비용 검증"이 중요한 상태다.

스크리닝 관점에서 Amazon은 다음처럼 분류한다.

```text
Narrative Grade: Positive With Capex/Margin Overhang
Narrative Label: aws_ai_infrastructure_momentum_with_capex_margin_overhang
Attention: High
Event Momentum: Positive
Retail Interest: High but Mixed
Risk Overhang: Medium to High
Data Quality: Medium
```

투자 narrative 한 줄 요약:

> Amazon은 AWS와 AI 인프라로 다시 성장 프리미엄을 받을 수 있지만, 그 프리미엄이 유지되려면 AI CAPEX가 실제 매출과 margin으로 회수된다는 증거가 필요하다.

---

## 11. Phase C로 넘길 Feature 후보

정량 스코어링에 사용할 후보 feature:

- `relevant_news_count_7d`
- `relevant_news_count_30d`
- `relevant_reddit_count_7d`
- `relevant_reddit_count_30d`
- `reddit_log_engagement_7d`
- `reddit_log_engagement_30d`
- `aws_cloud_topic_count_30d`
- `ai_anthropic_topic_count_30d`
- `capex_infra_topic_count_30d`
- `earnings_growth_topic_count_30d`
- `retail_ecommerce_topic_count_90d`
- `advertising_topic_count_90d`
- `regulatory_labor_topic_count_90d`
- `positive_event_count_30d`
- `negative_event_count_30d`
- `relevance_ratio`
- `event_verification_needed`
