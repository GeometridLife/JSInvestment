# Narrative Beneficiary Stock 설계

작성일: 2026-05-03

## 1. 목적

`PHASE3_1_narrative_attention`이 뽑은 뜨는 narrative를 실제 투자 후보군으로 연결한다.

핵심 질문:

> "이 narrative가 계속된다면 어떤 종목이 가장 직접적으로 수혜를 받을 가능성이 높은가?"

주의: 이 모듈은 매수 추천기가 아니다. narrative 수혜 가능성이 있는 종목을 **리서치 후보군**으로 좁히는 screening layer다.

---

## 2. 전체 흐름

```
theme attention ranking
→ theme confidence filter
→ theme → exposure universe 생성
→ ticker별 exposure score
→ price/fundamental/news confirmation
→ beneficiary score
→ tiered candidate list
→ 검증 리포트
```

수혜주 추출은 `attention_score`만으로 하지 않는다. 최소한 아래 4개 축을 같이 본다.

| 축 | 질문 |
|---|---|
| `exposure` | 이 회사가 해당 narrative에 실제로 노출되어 있는가? |
| `purity` | 회사 전체 사업에서 이 narrative 비중이 큰가? |
| `confirmation` | 가격/뉴스/실적 데이터가 narrative를 확인해주는가? |
| `risk` | 이미 과열됐거나 부정 이벤트가 큰가? |

---

## 3. 입력 데이터

### 3.1 필수 입력

| 입력 | 경로/출처 | 용도 |
|---|---|---|
| Theme ranking | `results/*_latest_theme_ranking.csv` | 뜨는 narrative 선택 |
| Theme match debug | `results/*_theme_match_debug.csv` | ticker별 기사 연결 |
| PHASE0 universe | `PHASE0_classification/nasdaq_screener.csv` 또는 master xlsx | 기본 종목 universe |
| Theme dictionary | `config/themes.json` | keyword / item / pure-play seed |

### 3.2 선택 입력

| 입력 | 용도 |
|---|---|
| PHASE1 momentum score | price confirmation |
| PHASE2 fundamental score | quality / valuation filter |
| Finnhub company profile | industry, market cap, peers |
| SEC/10-K item text | revenue exposure / segment verification |
| GDELT/Reddit pulse | broad-based attention 확인 |

---

## 4. Candidate Universe 생성

각 theme마다 후보군을 4개 bucket으로 만든다.

### 4.1 Pure-play bucket

해당 narrative에 사업 노출이 직접적인 종목.

예:

| Theme | Pure-play 예시 |
|---|---|
| Quantum Computing | IONQ, RGTI, QBTS, QUBT |
| Data Center Capex | VRT, ETN, GEV, SMCI, DELL, ANET |
| Grid And Power Equipment | ETN, GEV, VRT, BE, FLNC |
| GLP-1 | LLY, NVO, VKTX |

장점: narrative 민감도 높음.  
단점: 실적 품질/밸류에이션 리스크 큼.

### 4.2 Enabler bucket

테마가 성장할 때 핵심 인프라/부품/플랫폼을 제공하는 종목.

예:

| Theme | Enabler 예시 |
|---|---|
| Quantum Computing | NVDA, IBM, HON |
| Data Center Capex | NVDA, AMD, AVGO, TSM, ASML, MU |
| Robotics | NVDA, ISRG, TER, ROK, ABB |

장점: 사업 안정성 높음.  
단점: theme purity는 낮을 수 있음.

### 4.3 Customer / Adopter bucket

그 narrative를 사용해 비용 절감/성장 가속을 얻는 종목.

예:

| Theme | Adopter 예시 |
|---|---|
| AI Infrastructure | META, MSFT, GOOGL, AMZN |
| Robotics | AMZN, TSLA, META |
| Stablecoin | V, MA, PYPL, HOOD |

장점: 대형주 중심으로 안정적.  
단점: 수혜가 indirect라 alpha가 약할 수 있음.

### 4.4 Sympathetic / ETF-like bucket

같은 narrative에 묶여 움직이지만 실제 사업 노출은 약할 수 있는 종목.

예:
- 같은 Reddit basket
- 같은 ETF 구성 종목
- 같은 headline에 자주 같이 등장하는 종목

이 bucket은 trade 후보로는 볼 수 있지만, fundamental beneficiary로는 낮게 가중한다.

---

## 5. Ticker별 Feature

### 5.1 Exposure Feature

| Feature | 설명 |
|---|---|
| `theme_news_count_7d` | 해당 ticker가 theme 관련 기사에 등장한 수 |
| `theme_news_share_7d` | ticker 전체 뉴스 중 theme 관련 기사 비중 |
| `theme_log_change_7d_30d` | ticker별 theme attention 변화율 |
| `matched_item_count` | HBM, SMR, data center 등 세부 item 매칭 수 |
| `bucket_type` | pure_play / enabler / adopter / sympathetic |
| `bucket_weight` | pure_play 1.0, enabler 0.8, adopter 0.55, sympathetic 0.35 |

### 5.2 Purity Feature

| Feature | 설명 |
|---|---|
| `business_purity_score` | 회사 사업이 theme에 얼마나 직접적인지 |
| `segment_keyword_hits` | 사업 설명/10-K segment에서 theme keyword hit |
| `theme_revenue_proxy` | segment revenue가 있으면 비중, 없으면 unknown |
| `market_cap_bucket` | small/mid/large/mega |

초기에는 manual config 기반으로 시작한다. 나중에 10-K/IR 문서에서 자동 추출한다.

### 5.3 Confirmation Feature

| Feature | 설명 |
|---|---|
| `momentum_1m` | 최근 1개월 price momentum |
| `relative_strength_sector` | sector 대비 상대 강도 |
| `volume_spike` | 거래량 증가 |
| `earnings_revision_proxy` | guidance/estimate 관련 positive keyword |
| `source_breadth` | 여러 source에서 narrative가 확인되는지 |

### 5.4 Risk Feature

| Feature | 설명 |
|---|---|
| `valuation_risk` | PER/PS/EV sales 등 과열 proxy |
| `negative_event_count` | lawsuit, probe, downgrade 등 |
| `single_event_dependency` | narrative가 단일 이벤트에 몰렸는지 |
| `top_ticker_share` | 특정 ticker 쏠림 여부 |
| `low_liquidity_flag` | 거래대금 부족 |

---

## 6. Beneficiary Score

초기 점수는 설명 가능한 linear score로 시작한다.

```
exposure_score =
  0.35 * theme_news_share_pct
+ 0.25 * theme_log_change_pct
+ 0.20 * matched_item_count_pct
+ 0.20 * bucket_weight_pct

purity_score =
  0.50 * business_purity_score
+ 0.30 * segment_keyword_pct
+ 0.20 * theme_revenue_proxy_pct

confirmation_score =
  0.35 * momentum_1m_pct
+ 0.25 * relative_strength_sector_pct
+ 0.20 * volume_spike_pct
+ 0.20 * source_breadth_pct

risk_penalty =
  0.35 * valuation_risk_pct
+ 0.30 * negative_event_pct
+ 0.20 * single_event_dependency_pct
+ 0.15 * low_liquidity_flag

beneficiary_score =
  0.40 * exposure_score
+ 0.25 * purity_score
+ 0.25 * confirmation_score
- 0.20 * risk_penalty
```

`attention_score`는 theme 선택에 사용하고, ticker 점수에는 직접 넣지 않는다. 같은 theme 안에서 후보 종목을 비교할 때는 `beneficiary_score`를 사용한다.

---

## 7. Tier 분류

최종 후보는 단일 ranking보다 tier로 보여주는 것이 좋다.

| Tier | 의미 | 조건 예시 |
|---|---|---|
| Tier 1: Direct Beneficiary | 직접 수혜 가능성이 높고 검증도 강함 | exposure high, purity high, confirmation high |
| Tier 2: Enabler / Quality Compounder | 직접성은 낮지만 안정적 수혜 | exposure medium+, quality high |
| Tier 3: Emerging / Optionality | 작지만 upside beta 큼 | pure-play, attention rising, risk high |
| Tier 4: Watch Only | 아직 근거 부족 | low count, single event, weak confirmation |
| Exclude | 후보 제외 | negative event high, liquidity low, false positive |

---

## 8. 예시: Data Center Capex

### 8.1 Narrative 판정

v3 결과:
- `attention_score`: 77.31
- `adjusted_confidence`: very_high
- `narrative_type`: sustained_narrative
- 최근 7일 기사 수: 58
- active days: 6
- unique ticker count: 15

이 theme는 beneficiary extraction 대상으로 적합하다.

### 8.2 후보군 구조

| Bucket | 후보 예시 | 이유 |
|---|---|---|
| Pure-play infrastructure | VRT, SMCI, DELL, ANET | data center equipment/server/networking |
| Power/cooling enabler | ETN, GEV, CEG, VST, BE | AI data center power demand |
| Semiconductor enabler | NVDA, AMD, AVGO, TSM, ASML, MU | accelerator/foundry/memory |
| Hyperscaler adopter | MSFT, AMZN, GOOGL, META, ORCL | capex spender, platform owner |

### 8.3 해석

- `NVDA/MSFT/AMZN/GOOGL`은 narrative 중심에 있지만 이미 mega-cap consensus라 alpha가 작을 수 있다.
- `VRT/ETN/GEV/BE` 같은 power/cooling/infrastructure 쪽이 "AI capex → physical infrastructure" 전환을 더 민감하게 반영할 수 있다.
- `SMCI/DELL/ANET`은 server/networking capex exposure가 높지만 valuation/cycle risk를 같이 봐야 한다.

---

## 9. 예시: Quantum Computing

v3 결과:
- `attention_score`: 80.63
- `adjusted_confidence`: medium
- `narrative_type`: derivative_mention
- pure-play ratio: 0%

이 경우 바로 beneficiary list를 뽑으면 안 된다.

먼저 확인해야 할 것:
1. IONQ/RGTI/QBTS/QUBT 같은 pure-play 뉴스가 실제로 늘었는가?
2. NVDA/IBM/HON 같은 enabler mention이 전부인가?
3. 정부 정책, 대형 계약, 기술 breakthrough 같은 독립 catalyst가 있는가?

후보군은 `watch only`로 시작한다.

---

## 10. 구현 산출물 제안

```
config/
  theme_beneficiary_map.json

scripts/
  build_beneficiary_candidates.py
  score_beneficiaries.py
  generate_beneficiary_report.py

results/
  YYYYMMDD_THEME_beneficiary_candidates.csv
  YYYYMMDD_THEME_beneficiary_report.md
  YYYYMMDD_all_theme_beneficiary_ranking.csv
```

### `theme_beneficiary_map.json` 구조

```json
{
  "Data Center Capex": {
    "pure_play": ["VRT", "SMCI", "DELL", "ANET"],
    "enabler": ["NVDA", "AMD", "AVGO", "TSM", "ASML", "MU"],
    "adopter": ["MSFT", "AMZN", "GOOGL", "META", "ORCL"],
    "sympathetic": ["CEG", "VST", "BE"],
    "keywords": ["data center", "AI capex", "server rack", "hyperscaler"]
  }
}
```

---

## 11. 운영 원칙

1. `sustained_narrative` + `adjusted_confidence >= high`인 theme만 beneficiary scoring을 우선 실행한다.
2. `derivative_mention`은 pure-play basket을 추가 수집해 검증한 뒤 후보군을 만든다.
3. `noise_possible`은 beneficiary list를 만들지 않고 watch queue에만 둔다.
4. 결과는 종목 추천이 아니라 research queue다.
5. 최종 후보는 반드시 price/fundamental/risk layer와 결합한다.
