# PHASE3: Global Narrative Indicators (내러티브 지표)

## 목표
뉴스, 애널리스트 리포트, SNS 등 정성적 데이터를 정량화하여 내러티브 기반 스크리닝 지표를 산출한다.

## 워크플로우
```
리서치 → 플래닝 → 수정 → 구현 → 수정
```

## 폴더 구조
```
PHASE3_narrative/
├── docs/          # 리서치 & 플래닝 문서
│   ├── YYYYMMDD_research.md
│   └── YYYYMMDD_planning.md
├── scripts/       # 실행 스크립트
├── cache/         # 중간 결과물 캐시
├── logs/          # 실행 로그
└── results/       # 최종 결과
```

## 주요 검토 사항
- 데이터 소스: 글로벌 뉴스 API (NewsAPI, GDELT), SEC 공시, 트위터/X, Reddit (r/wallstreetbets 등)
- NLP/감성분석: Claude API, FinBERT, 자체 파이프라인
- 지표 후보: 뉴스 감성 스코어, 애널리스트 목표가 변경률, 내부자 거래, 기관 보유 변화
- 언어 처리: 영어 중심 (일본어/중국어는 추후)
- 업데이트 주기: 일간 or 주간

---

## 데이터 수집 설계 보완

### 1. 1차 구현 범위
초기 PHASE3는 감성분석보다 먼저 **기업별 관련 문서를 정확히 모으는 raw collector**를 구축한다.

- 입력: PHASE0 마스터 테이블의 종목 리스트
- 기간: 최근 7일 기본값
- 소스: Finnhub 회사 뉴스 + GDELT 뉴스 + Reddit 게시글
- 출력: 원천별 raw CSV + 통합 CSV
- 이후 단계: 중복 제거, relevance 필터, 감성분석, narrative keyword scoring

### 2. 데이터 소스 우선순위

| 우선순위 | 소스 | 용도 | 장점 | 주의점 |
|---|---|---|---|---|
| 1 | Finnhub Company News | 티커 기준 회사 뉴스 | ticker 기반이라 GDELT보다 기업 매칭이 정확함 | API key 필요, 플랜별 rate limit 확인 필요 |
| 2 | GDELT DOC 2.0 | 글로벌 뉴스 raw 수집 | API key 불필요, 글로벌 커버리지, tone/metadata 활용 가능 | 금융 특화가 아니므로 기업명 오탐 관리 필요 |
| 3 | NewsAPI | 보조 뉴스 수집 | source/domain/date 필터 편리 | API key 필요, 무료/개발 플랜 제한, full text 한계 |
| 4 | Reddit | 개인투자자 narrative | meme/retail sentiment 포착 | 공식 API/약관/rate limit 준수 필요, ticker 오탐 큼 |
| 5 | SEC/공시 | event verification | 신뢰도 높음 | narrative보다는 이벤트 확인용 |

### 3. 기업 매칭 규칙
단순 ticker 검색은 오탐이 크므로 기본 검색은 **기업명 중심**으로 한다.

- 뉴스 기본 쿼리: 정제된 회사명 exact phrase
- ticker는 `A`, `ON`, `NOW`, `CAT`, `META`처럼 일반 단어와 겹치므로 단독 검색 금지
- Reddit은 ticker 앞에 `$`가 붙은 cashtag를 보조로 사용할 수 있으나, 회사명 매칭과 함께 검증 필요
- 뉴스 검색은 `Common Stock`, `Class A` 등 상장 표기만 제거하고 `Inc.`, `Corporation` 같은 법인 suffix는 보존한다. Reddit은 짧은 회사명 alias와 `$TICKER`를 보조로 함께 사용한다.

### 4. Raw 데이터 표준 스키마

| 컬럼 | 설명 |
|---|---|
| `ticker` | 종목 코드 |
| `company_name` | PHASE0 회사명 |
| `source_type` | `finnhub_news`, `gdelt_news`, `reddit_post` |
| `source` | 뉴스 domain 또는 subreddit |
| `title` | 제목 |
| `text` | description/selftext/snippet |
| `url` | 원문 URL |
| `published_at` | 발행/작성 시각 |
| `query` | 실제 검색 쿼리 |
| `matched_terms` | 매칭에 사용한 회사명/alias/ticker |
| `engagement` | Reddit score + comments 등 참여도 |
| `raw_json` | 원본 JSON 문자열 |
| `collected_at` | 수집 시각 |

### 5. 수집 안정성 체크리스트

- API 호출마다 timeout, retry, sleep 적용
- source별 실패 로그 저장
- URL 기준 중복 제거
- 동일 ticker 내 title 유사 중복은 후속 처리에서 제거
- 전체 1,800개 이상 종목 수집 전 `--limit`으로 샘플 검증
- Reddit은 인증/약관 변경 가능성이 높으므로 실패해도 뉴스 수집은 계속 진행

### 6. 초기 스크리닝 지표 후보

Raw 수집 후 바로 계산 가능한 1차 지표:

- `news_count_7d`: 최근 7일 뉴스 수
- `reddit_post_count_7d`: 최근 7일 Reddit 게시글 수
- `reddit_engagement_7d`: score + comment count 합계
- `source_diversity_7d`: 서로 다른 뉴스 domain 수
- `mention_acceleration`: 최근 언급량 / 과거 평균 언급량
- `negative_event_keyword_count`: lawsuit, downgrade, probe, fraud, recall 등 부정 이벤트 키워드 수
- `positive_event_keyword_count`: partnership, upgrade, guidance, approval, contract 등 긍정 이벤트 키워드 수

---

## 내러티브 스코어링 설계

### 1. 기본 원칙

Raw count를 바로 점수화하지 않는다. 뉴스/Reddit 모두 시장 전체 기사, ETF 기사, daily discussion, 여러 종목을 묶은 글이 섞이므로 **관련성 필터를 먼저 통과한 문서만 지표 계산에 사용**한다.

스코어링 순서:

```
raw load
→ URL/title dedupe
→ relevance filter
→ source별 metric 계산
→ log/percentile normalization
→ sector/size group percentile
→ narrative_score 산출
```

### 2. Relevance Filter

문서별 `relevance_score`를 계산하고, 일정 기준 이상만 지표에 반영한다.

| 항목 | 예시 | 점수 |
|---|---|---:|
| 회사명 exact match | `Apple Inc`, `Microsoft Corporation` | +2 |
| ticker/cashtag match | `AAPL`, `$AAPL` | +2 |
| 핵심 제품/경영진 키워드 | `iPhone`, `Tim Cook`, `Azure`, `CUDA` | +1 |
| 실적/이벤트 키워드 | `earnings`, `guidance`, `buyback`, `approval` | +1 |
| 시장/ETF/매크로 잡음 | `S&P 500`, `ETF`, `daily discussion`, `market today` | -1 |

초기 기준:

- `relevance_score >= 2`: relevant
- `relevance_score < 2`: 제외 또는 low-confidence 보관
- Reddit은 title 기준을 우선하고, selftext는 ticker가 너무 많이 섞이는 경우가 있어 보조로만 사용

### 3. Source별 Metric

| 카테고리 | 지표 | 설명 |
|---|---|---|
| News Attention | `relevant_news_count_7d` | Finnhub + GDELT 관련 뉴스 수 |
| News Breadth | `source_diversity_7d` | 관련 뉴스의 서로 다른 source/domain 수 |
| Retail Attention | `relevant_reddit_count_7d` | 관련 Reddit 게시글 수 |
| Retail Engagement | `reddit_log_engagement_7d` | `sum(log1p(score + comments))` |
| Event Momentum | `positive_event_count_7d` | 긍정 이벤트 키워드 수 |
| Risk Signal | `negative_event_count_7d` | 부정 이벤트 키워드 수 |
| Data Quality | `relevance_ratio` | relevant 문서 / raw 문서 |

### 4. Normalization

대형주는 항상 뉴스가 많기 때문에 절대 count만으로 비교하지 않는다.

- Reddit engagement는 `log1p` 변환
- source별 metric은 0~100 percentile로 변환
- 가능하면 GICS sector 또는 size group 내 percentile 사용
- `max_records`에 걸린 종목은 `is_capped = true`로 표시하고 count 해석에 주의
- 90일 이상 Finnhub 수집은 넓은 기간을 한 번에 요청하지 말고 `--finnhub-window-days 7`로 chunk 수집한다.
- GDELT는 `maxrecords` 제한 때문에 90일 요청이라도 최신 기사 샘플에 편중될 수 있으므로, 장기 분석에서는 Finnhub를 주 분석 소스로 두고 GDELT는 breadth 확인용 보조 소스로 사용한다.

### 5. 최종 점수 초안

```
attention_score =
  0.60 * relevant_news_count_pct
+ 0.40 * source_diversity_pct

retail_score =
  0.50 * relevant_reddit_count_pct
+ 0.50 * reddit_log_engagement_pct

event_score =
  positive_event_pct - negative_event_pct

narrative_score =
  0.35 * attention_score
+ 0.25 * retail_score
+ 0.25 * event_score
+ 0.15 * relevance_ratio_pct
```

### 6. 구현 예정 산출물

- `scripts/score_narrative.py`: raw CSV를 받아 ticker별 내러티브 지표 산출
- `results/YYYYMMDD_narrative_scores.csv`: ticker별 최종 스코어
- `results/YYYYMMDD_narrative_debug.csv`: 문서별 relevance/tone/event 판정 디버그
- `results/YYYYMMDD_narrative_report.md`: 상위 종목 narrative 요약
- `results/YYYYMMDD_TICKER_90d_narrative_analysis.md`: 단일 종목 심층 narrative 분석

---

## Phase B: 정성 Narrative Analysis

Phase B는 정량 스코어를 만들기 전, 수집된 문서에서 **투자자가 실제로 말하고 있는 이야기 구조**를 해석하는 단계다. 목표는 단순 긍정/부정 감성이 아니라 "왜 시장이 이 종목을 다시 보거나 피하는가"를 정리하는 것이다.

### 1. 입력

- `cache/*_narrative_raw.csv`
- `results/*_narrative_debug.csv`
- 7D/30D/90D window metric
- source별 top engagement 문서

### 2. 분석 순서

```
relevant docs
→ topic cluster
→ bull narrative
→ bear narrative
→ catalyst/risk timeline
→ event verification queue
→ narrative label
→ screening interpretation
```

### 3. 정성 분석 템플릿

| 섹션 | 질문 |
|---|---|
| Core Narrative | 이 종목을 둘러싼 가장 강한 이야기는 무엇인가? |
| Bull Case | 긍정론자는 어떤 근거로 이 종목을 산다고 말하는가? |
| Bear Case | 회의론자는 무엇을 걱정하는가? |
| Retail Tone | Reddit/커뮤니티에서는 무엇에 열광하거나 불안해하는가? |
| Institutional Tone | 뉴스/애널리스트성 기사에서는 어떤 프레임이 우세한가? |
| Catalysts | 최근 7~30일 내러티브를 바꾼 이벤트는 무엇인가? |
| Risk Overhang | 앞으로 narrative score를 훼손할 수 있는 이슈는 무엇인가? |
| Verification Queue | 사실 여부를 공식 공시/IR로 확인해야 할 이벤트는 무엇인가? |
| Screening Label | 스크리닝용 narrative tag는 무엇인가? |

### 4. 판정 등급

| 등급 | 의미 |
|---|---|
| `Strong Positive` | 긍정 이벤트가 명확하고 retail/news 모두 같은 방향 |
| `Positive With Overhang` | 긍정 모멘텀은 강하지만 구조적 의심이 존재 |
| `Mixed / Transition` | 긍정과 부정이 비슷하거나 leadership/product 전환기 |
| `Negative Watch` | 부정 이벤트가 증가하고 긍정 narrative가 약함 |
| `Noise / Low Confidence` | 관련 문서가 적거나 relevance 품질이 낮음 |

### 5. 산출물

- `results/YYYYMMDD_TICKER_90d_phaseB_qualitative.md`
- 핵심 narrative label
- bull/bear thesis
- catalyst/risk map
- verification queue
- 다음 정량 스코어링에 넘길 feature 후보

### 7. Apple 7일 샘플 검토 메모

현재 수집된 AAPL 7일 raw 샘플은 총 62건이다.

- Finnhub 뉴스: 20건
- GDELT 뉴스: 10건
- Reddit 게시글: 32건

제목 기준 간이 relevance filter를 적용하면 관련 문서는 약 27건으로 줄어든다. 주요 내러티브는 **실적 서프라이즈, 서비스 매출, 대규모 자사주매입, 중국/인도 수요 회복**이다. 반면 Reddit에서는 **AI 모멘텀 부재, 가격 인상성 성장, 밸류에이션 부담**에 대한 의심도 같이 보인다.

따라서 Apple 샘플은 `attention`과 `event`는 강하지만, `retail`에서는 긍정/회의가 섞인 상태로 해석한다. 이 샘플은 relevance filter가 없으면 시장 전체 기사와 daily discussion이 섞여 count가 과대평가될 수 있음을 보여준다.

### 8. 실행 예시

```bash
cd JSInvestment/JS/Global/PHASE3_narrative

# 최근 7일, 처음 5개 종목만 테스트
python3 scripts/collect_narrative_raw.py --days 7 --limit 5

# 특정 종목만 테스트
python3 scripts/collect_narrative_raw.py --days 7 --tickers AAPL,MSFT,NVDA

# GDELT 뉴스만 수집
python3 scripts/collect_narrative_raw.py --days 7 --source gdelt --limit 20

# Finnhub 회사 뉴스만 수집 (API key 필요)
FINNHUB_API_KEY=your_key python3 scripts/collect_narrative_raw.py --days 7 --source finnhub --tickers AAPL,MSFT,NVDA

# 90일 이상은 Finnhub를 7일 단위로 쪼개 수집
FINNHUB_API_KEY=your_key python3 scripts/collect_narrative_raw.py --days 90 --source finnhub --tickers AAPL --max-records 2000 --finnhub-window-days 7
```

### 9. 현재 구현 상태

- `scripts/collect_narrative_raw.py`: 최근 7일 Finnhub + GDELT + Reddit raw collector
- `cache/`: raw 수집 결과 CSV 저장. 파일명은 `YYYYMMDD_HHMMSS_...` 형태라 재실행해도 기존 결과를 덮어쓰지 않는다.
- `cache/*_finnhub_news_raw.csv`, `cache/*_gdelt_news_raw.csv`, `cache/*_reddit_post_raw.csv`: `--source all` 실행 시에도 source별 결과를 별도 저장
- `logs/`: source별 실패/상태 로그 저장
- `results/`: 후속 scoring 결과 저장 예정

## 참고 (Domestic)
- Domestic PHASE3는 미구현 상태
- 향후 국내 뉴스, 증권사 리포트, 커뮤니티 감성 분석 예정
