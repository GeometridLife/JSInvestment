# PHASE3_1: Sector Attention Tracker — Research

작성일: 2026-05-03

---

## 1. 목적

PHASE3 (기업별 narrative 수집)의 보완 모듈. 방향이 정반대다.

```
PHASE3   : tickers → news       (기업별 narrative)
PHASE3_1 : news → themes/tickers (시장 전체 attention 분포)
```

핵심 질문:
> "지금 시장에서 어떤 narrative가 뜨거워지고 있는가, 그리고 어떤 narrative가 식어가는가?"

활용 시나리오:
- 내 watchlist 테마의 attention 변화율 모니터링
- attention이 낮으면서 펀더멘털 좋은 영역 발굴 (역상관 알파)
- 새로 떠오르는 narrative 조기 포착 (emerging theme)

---

## 2. 확정된 설계 결정

| 항목 | 결정 | 비고 |
|---|---|---|
| Attention 지표 | 절대 빈도 + 상대 변화율 | **변화율이 메인 시그널** |
| 분류 단위 | 테마 기반 (narrative unit) | GICS 아님 |
| 코드 구조 | `PHASE3_1_narrative_attention/` 분리 | PHASE3와 독립 |
| 1차 구현 범위 | Static theme dictionary + daily aggregate | LLM clustering은 후순위 |
| 핵심 산출물 | theme/sector/item attention ranking | ticker 분석은 보조 |

---

## 3. Attention 지표 정의

### 3.1 절대 빈도 (baseline)
- 일별 / 주별 테마 t의 mention count
- 단순 count: `freq_t(d) = Σ articles mentioning theme t on day d`
- 가중 count: 매체 신뢰도, 기사 prominence (제목 vs 본문) 가중치
- source별 count는 분리 저장: `gdelt_count`, `finnhub_count`, `reddit_count`
- ticker별 count는 보조 feature로만 사용하고, 최종 메인 ranking은 theme/item 기준

### 3.2 변화율 (메인 시그널)

여러 방법이 있고 각각 장단점이 다르다:

**(a) Simple ratio**
```
change_ratio_t(d) =
  avg_daily_freq_t(last_7d) / avg_daily_freq_t(prev_30d_ex_recent)
```
- 장점: 직관적, 계산 간단
- 단점: 분모 0 또는 매우 작을 때 폭발 (cold start, 신생 테마)

**(b) Z-score (표준화)**
```
z_t(d) =
  (avg_daily_freq_t(last_7d) - μ_t(prev_90d_ex_recent)) / σ_t(prev_90d_ex_recent)
```
- 장점: 통계적으로 anomaly 정의 가능 (z>2면 유의미한 spike)
- 단점: 분포가 정규가 아닐 수 있음 (뉴스는 long-tail), σ가 0인 경우

**(c) Log ratio (추천)**
```
log_change_t(d) =
  log((avg_daily_freq_t(last_7d) + ε) / (avg_daily_freq_t(prev_30d_ex_recent) + ε))
```
- 장점: cold start 처리 (ε 스무딩), 대칭성 (상승/하락 동일 스케일), outlier 견고
- 단점: 해석이 살짝 추상적

**결정**: (c) Log ratio를 메인으로, (b) Z-score를 보조로 산출. (a)는 시각화 용도로만.

### 3.3 Window 정의

변화율 계산에서 baseline에 최근 데이터를 섞으면 spike가 희석된다. 그래서 baseline은 현재 window를 제외한다.

| Window | 정의 | 용도 |
|---|---|---|
| `last_1d` | 기준일 하루 | 당일 급등 알림 |
| `last_7d` | 기준일 포함 최근 7일 | 메인 attention |
| `prev_30d_ex_recent` | `last_7d` 직전 30일 | 단기 baseline |
| `prev_90d_ex_recent` | `last_7d` 직전 90일 | z-score / 안정성 |

초기 구현에서는 최소 37일치 데이터가 있어야 `7d vs 30d`를 계산한다. 97일치가 있으면 z-score까지 계산한다.

### 3.4 정규화 — 매우 중요

전체 뉴스 볼륨이 날마다 다르다 (주말 적음, 큰 사건 있는 날 많음). 정규화 안 하면 "전체 뉴스가 많은 날 = 모든 테마 attention 증가"로 잘못 보임.

**share metric**:
```
share_t(d) = freq_t(d) / total_articles(d)
```

→ 변화율은 share 기준으로 계산:
```
log_change_t(d) = log((share_t(7d) + ε) / (share_t(30d) + ε))
```

이러면 "전체 뉴스 대비 이 테마의 비중이 얼마나 늘었나"가 측정됨.

단, `total_articles(d)`는 source별로 따로 계산한다. GDELT 전체 기사 수와 Reddit thread comment 수를 같은 분모로 섞으면 안 된다.

```
source_share_t(d, source) = freq_t(d, source) / total_articles(d, source)
```

최종 score는 source별 share 변화율을 계산한 뒤 합친다.

### 3.5 최종 Attention Score 초안

초기에는 설명 가능한 linear score로 시작한다.

```
news_attention =
  0.80 * finnhub_company_log_share_change_pct
+ 0.20 * gdelt_log_share_change_pct

retail_attention =
  0.60 * reddit_log_share_change_pct
+ 0.40 * reddit_engagement_change_pct

breadth_score =
  percentile(unique_source_count_7d)

attention_score =
  0.65 * news_attention
+ 0.15 * retail_attention
+ 0.15 * breadth_score
+ 0.10 * z_score_pct
```

현재 `scripts/prototype_attention_from_cache.py`의 실제 구현도 이 산식을 따른다. 참고용 통합 변화율 `log_share_change_7d_30d`도 출력하지만, 최종 `attention_score`에는 source별 score가 사용된다.

출력되는 주요 중간 컬럼:

| 컬럼 | 의미 |
|---|---|
| `finnhub_company_log_change_7d_30d` | Finnhub company-news 기준 최근 7일 share / 직전 30일 share의 log 변화율 |
| `gdelt_log_change_7d_30d` | GDELT 기준 최근 7일 share / 직전 30일 share의 log 변화율 |
| `reddit_log_change_7d_30d` | Reddit 기준 최근 7일 share / 직전 30일 share의 log 변화율 |
| `news_attention` | `0.80 * Finnhub percentile + 0.20 * GDELT percentile` |
| `retail_attention` | `0.60 * Reddit 변화율 percentile + 0.40 * Reddit engagement percentile` |
| `attention_score` | 최종 랭킹 점수 |

### 3.6 신뢰도 레이어

`attention_score`가 높아도 기사 수가 적거나 단일 이벤트에 몰리면 실제 narrative shift가 아닐 수 있다. 그래서 점수와 별도로 신뢰도 레이어를 둔다.

| 컬럼 | 의미 |
|---|---|
| `adjusted_confidence` | `very_high`, `high`, `medium`, `low` |
| `narrative_type` | `sustained_narrative`, `emerging_watch`, `derivative_mention`, `single_event`, `noise_possible` |
| `daily_active_days_7d` | 최근 7일 중 기사가 나온 날짜 수 |
| `unique_ticker_count_7d` | 최근 7일 매칭 기사에 포함된 고유 ticker 수 |
| `top_ticker_share_7d` | 특정 ticker 하나에 쏠린 비율 |
| `top_headline_cluster_share_7d` | 유사 headline cluster 하나에 쏠린 비율 |
| `pure_play_ratio_7d` | 해당 theme pure-play ticker가 차지하는 비율 |
| `event_concentration_score` | ticker/headline 쏠림 중 큰 값 |

해석 원칙:
- `attention_score`는 관심 증가 강도다.
- `adjusted_confidence`는 그 증가를 믿을 수 있는 정도다.
- `narrative_type`은 sustained narrative인지, 단일 이벤트인지, 상위 narrative의 파생 mention인지 구분한다.

결과 해석은 `attention_score` 하나만 보지 않고 아래 필드를 같이 본다.

- `direction`: `rising`, `falling`, `stable`, `new`
- `source_mix`: `news_led`, `retail_led`, `broad_based`
- `confidence`: `high`, `medium`, `low`
- `risk_tone`: `positive`, `negative`, `mixed`, `unknown`

---

## 4. 테마 정의 — 가장 어려운 문제

### 4.1 Static theme dictionary (Stage A)

초기 테마 리스트 (현재 시장 narrative 기준, ~15-20개):

| Theme | Keywords (예시) | GDELT GKG themes | 대표 tickers |
|---|---|---|---|
| AI Infrastructure | "AI chip", "GPU", "accelerator", "datacenter AI" | TECH_AI, TECH_DATA_CENTER | NVDA, AMD, AVGO |
| Power Infrastructure | "data center power", "grid", "transformer" | ENV_NUCLEARPOWER, INFRA_ELECTRIC | VST, GEV, ETN |
| Defense | "defense spending", "NATO", "Ukraine aid" | MIL_WEAPONS, MIL_DEFENSE | LMT, RTX, GD |
| GLP-1 / Obesity drugs | "Wegovy", "Ozempic", "obesity drug" | HEALTH_PHARMA | LLY, NVO |
| Stablecoin / Crypto policy | "stablecoin", "crypto regulation" | ECON_CRYPTOCURRENCY | COIN, MSTR |
| Quantum computing | "quantum computer", "qubit" | TECH_QUANTUM | IBM, IONQ, RGTI |
| Nuclear renaissance | "nuclear power", "SMR", "uranium" | ENV_NUCLEARPOWER | CCJ, BWXT |
| Reshoring / Industrial | "reshoring", "CHIPS Act", "manufacturing" | MFG_MANUFACTURING | CAT, ETN |
| Robotics / Automation | "humanoid robot", "automation" | TECH_ROBOTICS | ABB, ISRG |
| ... | ... | ... | ... |

**관리 방식**: `config/themes.yaml`로 외부화. 사용자가 직접 편집 가능.

### 4.2 매칭 로직

각 기사에 대해 multiple theme tagging 가능:

```
article_themes(article) = {
  t : (keyword_score(t, article) >= threshold)
       OR (any GKG theme in t.gkg_themes is in article.gkg_themes)
}
```

- 키워드는 단순 OR보다 점수제로 시작: title match > description/body match
- GDELT 사용 시 GKG theme 태그 매칭이 keyword 매칭보다 견고
- Finnhub/Reddit은 GKG 없으므로 keyword + ticker 매칭
- 너무 범용적인 단어는 단독 매칭 금지: `AI`, `power`, `chip`, `grid`, `drug` 등
- 테마별 `exclude_keywords`를 둔다. 예: `power` 테마에서 `political power`, `chip` 테마에서 `potato chip`

초기 점수 예시:

| 매칭 항목 | 점수 |
|---|---:|
| title keyword exact phrase | +3 |
| title ticker/company basket match | +2 |
| description/body keyword exact phrase | +1 |
| GDELT GKG theme match | +2 |
| exclude keyword hit | -3 |

초기 기준:
- `theme_match_score >= 2`: matched
- `theme_match_score < 2`: unmatched 또는 low-confidence

### 4.3 Theme / Sector / Item 계층

`theme`만 있으면 너무 넓고, `ticker`만 있으면 PHASE3와 겹친다. 그래서 3단 구조로 저장한다.

| 계층 | 예시 | 목적 |
|---|---|---|
| `sector_group` | Semiconductors, Defense, Healthcare | 큰 흐름 파악 |
| `theme` | AI Infrastructure, Nuclear Renaissance | narrative ranking |
| `item` | HBM, SMR, GLP-1, stablecoin | 구체적 관심 대상 |

한 기사는 여러 theme/item에 매칭될 수 있다. 다만 score 계산에서는 기사 1건의 총 가중치가 과도하게 중복되지 않도록 `1 / matched_theme_count` 방식의 fractional count도 같이 저장한다.

### 4.4 Emerging theme discovery (Stage B, 다음 단계)

이번 단계에서는 미구현. 향후 작업:
- 전체 뉴스에서 entity (organization, person, product) 추출
- 7일 빈도 / 90일 빈도 비율로 "새로 떠오르는 entity" 발굴
- entity co-occurrence로 narrative 클러스터링
- static dictionary에 없는 recurring phrase를 후보로 저장: `candidate_emerging_items.csv`

---

## 5. 데이터 소스

### 5.1 우선순위

| 순위 | 소스 | 용도 | 비고 |
|---|---|---|---|
| 1 | Finnhub `company-news` | 30~90일 baseline / investable universe attention | symbol + date range 가능, chunk 수집 가능 |
| 2 | Finnhub `general` news | 시장 뉴스 최신 스트림 | baseline보다는 daily append |
| 3 | GDELT 2.0 DOC API | 글로벌 pulse / breadth 보조 | maxrecords/429 때문에 1~3일 보조 지표 |
| 4 | Reddit (r/investing, r/stocks, r/wallstreetbets) | retail attention | retail spike 보조 |

### 5.2 Finnhub — 이번 모듈의 핵심

**왜 Finnhub가 메인인가:**
- `company-news`는 `symbol`, `from`, `to`가 있어 30~90일 baseline 수집에 적합하다.
- 기존 PHASE0 universe와 연결하면 "투자 가능한 종목군에서 어떤 theme attention이 늘었나"를 볼 수 있다.
- GDELT보다 ticker/company 매칭 품질이 높다.
- 원문 전체를 장기 보관하지 않고 daily aggregate만 누적하면 메모리 부담이 작다.

**API endpoints:**
- `https://finnhub.io/api/v1/company-news?symbol=AAPL&from=YYYY-MM-DD&to=YYYY-MM-DD`
- `https://finnhub.io/api/v1/news?category=general`

**운영 원칙:**
- `company-news`를 baseline의 주 소스로 둔다.
- 전체 universe를 한 번에 90일 backfill하지 말고, ticker batch와 date chunk로 나눈다.
- `general news`는 최신 시장 뉴스 보강용이며, 긴 baseline의 핵심으로 쓰지 않는다.
- API key/rate limit 때문에 `--limit`, `--tickers`, `--sleep`, `--finnhub-window-days`를 반드시 둔다.

### 5.3 GDELT — 보조 pulse

**왜 GDELT를 버리지 않는가:**
- API key 불필요, 무제한 쿼리
- 전세계 뉴스 (영어 + 65개 언어 번역)
- **GKG theme 태그가 이미 붙어있음** → keyword 매칭보다 정확
- `tone` 필드로 sentiment 가중 attention 산출 가능

**API endpoints:**
- `https://api.gdeltproject.org/api/v2/doc/doc?query=...&mode=ArtList&format=json`
- `theme:TECH_AI` 같은 query syntax 지원
- 최대 250 results / query → 페이지네이션 또는 시간 분할 필요

**제약:**
- Daily volume이 매우 큼 (수만~수십만 기사/일) → 샘플링 또는 집계만 저장
- 기업명 매칭은 약함 → ticker로 변환은 후처리 필요
- `maxrecords` 제한 때문에 장기 window는 하루 단위 또는 더 작은 시간 단위로 분할 수집
- 동일 기사가 여러 쿼리에서 반복 수집될 수 있어 URL/canonical URL 기준 dedupe 필요
- 429가 발생할 수 있으므로 GDELT는 1~3일 pulse/breadth 용도로 제한한다.

### 5.4 Reddit — Retail attention

PHASE3에서 만든 PRAW 클라이언트 재사용:
- r/investing, r/stocks, r/wallstreetbets `daily discussion` 스레드
- 댓글에서 ticker 빈도 ($AAPL 같은 cashtag) 추출
- 이건 retail attention의 진짜 신호 (institutional view와 다른 차원)

---

## 6. 데이터 흐름

```
[수집 단계]
  Finnhub company-news ──→ baseline raw/daily aggregate
  Finnhub market-news  ──→ latest market stream
  GDELT DOC API        ──→ 1~3d pulse/breadth
  Reddit threads       ──→ retail pulse

[처리 단계]
  raw articles ──→ dedupe ──→ theme tagging ──→ daily aggregates
                              (keyword + GKG)    (theme × date × source)

[분석 단계]
  daily aggregates ──→ rolling windows (7d, 30d)
                  ──→ change metrics (log ratio, z-score, share)
                  ──→ ranked theme attention

[출력]
  - daily_theme_attention.parquet (시계열, 백테스트용)
  - latest_theme_ranking.csv (오늘의 attention top/bottom)
  - emerging_alerts.csv (z > 2.0인 테마)
```

### 6.1 Raw Article 표준 스키마

| 컬럼 | 설명 |
|---|---|
| `article_id` | source + canonical url hash |
| `source_type` | `finnhub_news`, `finnhub_market_news`, `gdelt_news`, `reddit_post`, `reddit_comment` |
| `source` | domain/subreddit/provider |
| `title` | 제목 |
| `text` | description/snippet/selftext/comment body |
| `url` | 원문 URL |
| `canonical_url` | dedupe용 정규화 URL |
| `published_at` | UTC 기준 발행 시각 |
| `language` | 언어 |
| `country` | 가능하면 source country |
| `query` | 수집 query |
| `raw_json` | 원본 JSON |
| `collected_at` | UTC 기준 수집 시각 |

### 6.2 Theme Match Debug 스키마

| 컬럼 | 설명 |
|---|---|
| `article_id` | raw article 연결 키 |
| `theme` | 매칭된 테마 |
| `sector_group` | 상위 섹터 그룹 |
| `items` | 매칭된 세부 item 목록 |
| `theme_match_score` | rule 기반 매칭 점수 |
| `matched_terms` | 실제 매칭된 keyword/GKG/ticker |
| `excluded_terms` | 제외 키워드 hit |
| `is_low_confidence` | 낮은 신뢰도 여부 |
| `fractional_weight` | multi-tag 보정 가중치 |

### 6.3 Daily Aggregate 스키마

| 컬럼 | 설명 |
|---|---|
| `date` | UTC 기준 날짜 |
| `source_type` | source 구분 |
| `sector_group` | 상위 섹터 그룹 |
| `theme` | 테마 |
| `item` | 세부 item, 없으면 null |
| `article_count` | 단순 기사 수 |
| `weighted_article_count` | source/title/fractional 가중 기사 수 |
| `unique_source_count` | 고유 domain/subreddit 수 |
| `total_source_articles` | 해당 source_type의 전체 기사 수 |
| `share` | `weighted_article_count / total_source_articles` |
| `positive_event_count` | 긍정 이벤트 키워드 수 |
| `negative_event_count` | 부정 이벤트 키워드 수 |

---

## 7. 폴더 구조 제안

```
PHASE3_1_narrative_attention/
├── docs/
│   ├── 20260503_research.md   ← 이 문서
│   └── 20260503_planning.md   ← 다음 단계
├── config/
│   ├── themes.yaml            # 테마 정의 (keywords, GKG themes, tickers)
│   └── sources.yaml           # 소스별 endpoint, rate limit
├── scripts/
│   ├── ingestion/
│   │   ├── gdelt_collector.py
│   │   ├── finnhub_market_news.py
│   │   └── reddit_daily_discussion.py
│   ├── tagging/
│   │   └── theme_tagger.py    # 기사 → 테마 매칭
│   ├── aggregation/
│   │   └── daily_aggregator.py
│   └── analysis/
│       └── attention_metrics.py  # log ratio, z-score 계산
├── cache/
│   ├── raw/                   # 원본 기사 (90일 보존)
│   └── daily/                 # 일별 집계 (영구 보존)
├── results/
│   ├── daily_theme_attention.parquet
│   ├── latest_theme_ranking.csv
│   └── emerging_alerts.csv
└── logs/
```

---

## 8. Ranking 출력 포맷

`latest_theme_ranking.csv`는 사람이 바로 읽고 다음 리서치로 넘길 수 있어야 한다.

| 컬럼 | 설명 |
|---|---|
| `as_of_date` | 기준일 |
| `rank` | attention rank |
| `sector_group` | 상위 섹터 |
| `theme` | 테마 |
| `top_items` | HBM, SMR 등 세부 item |
| `attention_score` | 최종 점수 |
| `log_share_change_7d_30d` | 메인 변화율 |
| `z_score_7d_90d` | 이상치 정도 |
| `article_count_7d` | 최근 기사 수 |
| `baseline_article_count_30d` | baseline 평균 기사 수 |
| `unique_source_count_7d` | breadth |
| `source_mix` | news/retail 주도 여부 |
| `direction` | rising/falling/stable/new |
| `confidence` | high/medium/low |
| `sample_headlines` | 대표 제목 3개 |

`emerging_alerts.csv`는 ranking과 별개로 threshold 기반 알림만 담는다.

초기 alert 조건:
- `z_score_7d_90d >= 2.0`
- `article_count_7d >= 5`
- `unique_source_count_7d >= 3`
- `confidence != low`

---

## 9. 검증 / Sanity Check

처음부터 모델 성능을 정량 검증하기 어렵기 때문에, 운영 전 sanity check를 명시한다.

1. **큰 이벤트 재현**: FOMC, CPI, major earnings, 지정학 이벤트가 해당 날짜에 spike로 잡히는지 확인.
2. **주말 효과 제거**: 토/일 뉴스량 감소 때문에 모든 테마가 falling으로 나오지 않는지 확인.
3. **범용어 오탐**: `AI`, `power`, `chip` 같은 단어가 무관 기사까지 끌고 오지 않는지 sample headline 검토.
4. **source cap 확인**: GDELT `maxrecords`에 걸린 쿼리는 `is_capped=true`로 표시.
5. **중복 기사 확인**: syndicated article이 여러 domain에 퍼져 attention을 과대평가하지 않는지 URL/title similarity dedupe 확인.
6. **테마 중복 확인**: 한 기사가 5개 이상 테마에 매칭되면 dictionary가 너무 넓은 것으로 보고 debug queue에 넣음.

---

## 10. 알려진 위험 / 미해결 이슈

1. **테마 정의의 자의성**: `themes.yaml`로 관리해도, 어떤 keyword를 넣을지 자의적. 초기 1-2주 운영하면서 false positive 많은 키워드 제거하는 튜닝 필요.

2. **테마 간 중복**: "AI Infrastructure"와 "Power Infrastructure" 둘 다 매칭되는 기사 많음. multi-tagging 허용하되, fractional count와 debug output으로 관리.

3. **언어**: GDELT는 다국어 지원하나 키워드는 영어. 다국어 뉴스를 잡으려면 GKG theme 태그(언어 독립)에 의존해야 함.

4. **GDELT 다운타임**: 가끔 발생. 재시도 로직 + 부분 실패 허용 필요.

5. **Cold start (신생 테마)**: 30일 baseline 없는 테마는 변화율 계산 불가. ε 스무딩으로 완화하되, 별도 "new theme" 플래그 필요.

6. **Reddit 노이즈**: $TICKER cashtag 매칭은 false positive 많음 (`$ON`, `$A` 같은 짧은 ticker). 회사명 + cashtag 조합 검증 필요.

7. **전체 시장 이벤트**: 금리, CPI, 전쟁 같은 macro event는 모든 테마의 denominator와 numerator를 동시에 흔든다. `macro_event_flag`를 추후 추가할 수 있다.

8. **관심 증가와 투자 매력 혼동**: attention spike는 long signal이 아니다. negative attention도 강하게 잡힐 수 있으므로 `risk_tone`과 함께 해석해야 한다.

---

## 11. 다음 단계 (planning 문서에서)

- [ ] `themes.yaml` 초기 버전 작성 (15-20개 테마)
- [ ] GDELT collector 프로토타입 (1일치 수집 → tagging → 집계 end-to-end)
- [ ] 변화율 계산 검증 (과거 1개월 데이터로 backfill 후 sanity check)
- [ ] Finnhub / Reddit collector 통합
- [ ] 일간 ranking 출력 포맷 결정
- [ ] `sample_headlines` 포함한 debug report 생성

---

## 12. 실행 메모

초기 프로토타입은 외부 API를 호출하지 않고, 기존 `PHASE3_narrative_ticker/cache/*_90d_all_*_narrative_raw.csv` 파일을 읽어 schema와 scoring을 검증한다.

```bash
python3 JSInvestment/JS/Global/PHASE3_1_narrative_attention/scripts/prototype_attention_from_cache.py
```

산출물:
- `cache/daily/YYYYMMDD_prototype_daily_theme_attention.csv`
- `results/YYYYMMDD_prototype_latest_theme_ranking.csv`
- `results/YYYYMMDD_prototype_theme_match_debug.csv`
- `results/YYYYMMDD_prototype_attention_report.md`

주의: 이 결과는 ticker-level 캐시를 재활용한 것이므로 시장 전체 attention ranking이 아니다. 실제 운영 ranking은 Finnhub/GDELT/Reddit을 source별 chunk 수집한 뒤 daily aggregate를 누적해서 계산한다.

### Finnhub 중심 baseline 샘플 실행

Finnhub API key가 있을 때 baseline용 수집을 먼저 검증한다.

```bash
FINNHUB_API_KEY=... python3 JSInvestment/JS/Global/PHASE3_1_narrative_attention/scripts/live_attention_collector.py \
  --sources finnhub_company \
  --days 37 \
  --finnhub-window-days 7 \
  --limit 25 \
  --max-records-per-ticker 300 \
  --sleep 1.0 \
  --output-prefix 20260503_live_finnhub_37d_top25

python3 JSInvestment/JS/Global/PHASE3_1_narrative_attention/scripts/prototype_attention_from_cache.py \
  --input JSInvestment/JS/Global/PHASE3_1_narrative_attention/cache/raw/20260503_live_finnhub_37d_top25_attention_raw.csv \
  --output-prefix 20260503_live_finnhub_37d_top25
```

해석:
- `--limit 25`: PHASE0 universe에서 market cap 상위 25개만 샘플 수집
- `--tickers AAPL,MSFT,NVDA`: 특정 종목군만 수집하고 싶을 때 사용
- `--days 37`: `last_7d`와 `prev_30d_ex_recent` 계산을 위한 최소 기간
- `--finnhub-window-days 7`: 긴 기간을 7일 단위로 chunk 수집

### Live GDELT 보조 샘플 실행

GDELT는 메인 baseline이 아니라 보조 pulse 확인용으로 작은 범위만 실행한다. GDELT는 429 rate limit이 쉽게 발생하므로 전체 테마/장기 window를 한 번에 요청하지 않는다.

```bash
python3 JSInvestment/JS/Global/PHASE3_1_narrative_attention/scripts/live_attention_collector.py \
  --sources gdelt \
  --days 3 \
  --chunk-days 3 \
  --theme-limit 6 \
  --max-records 50 \
  --max-terms 4 \
  --sleep 0.1 \
  --retries 1 \
  --output-prefix 20260503_live_gdelt_3d_sample

python3 JSInvestment/JS/Global/PHASE3_1_narrative_attention/scripts/prototype_attention_from_cache.py \
  --input JSInvestment/JS/Global/PHASE3_1_narrative_attention/cache/raw/20260503_live_gdelt_3d_sample_attention_raw.csv \
  --output-prefix 20260503_live_gdelt_3d_sample
```

운영에서는 `--sleep`을 1~3초로 늘리고, 테마를 batch로 나누어 매일 누적하는 방식이 안전하다. 37일 baseline은 raw를 다시 전부 읽는 것이 아니라 `cache/daily/*_daily_theme_attention.csv`를 누적해서 만든다.

---

## 13. 수혜주 추출

뜨는 narrative를 종목 후보군으로 연결하는 설계는 `docs/beneficiary_stock_design.md`에 둔다. 핵심은 theme attention을 직접 종목 점수로 쓰지 않고, `exposure`, `purity`, `confirmation`, `risk`를 분리해 `beneficiary_score`를 산출하는 것이다.
