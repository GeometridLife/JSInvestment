# Narrative

> 주간 단위 narrative 흐름 분석 시스템. 새로 부상하거나 쇠퇴하는 시장 narrative를 정량적으로 추적하여 포트폴리오 액션(신규 진입 / 비중 확대 / 비중 축소)에 매핑한다.

## 0. 이 문서의 위치

- **CLAUDE.md** — 작업 행동 규범. 모든 코드 작성 작업에서 참조.
- **README.md** (이 문서) — 프로젝트 명세 및 진행 상황. 매 세션 시작 시 참조.

이 두 문서는 함께 읽혀야 한다. CLAUDE.md는 "어떻게 작업할 것인가", README.md는 "무엇을 만들 것인가"를 정의한다.

---

## 1. 프로젝트 목표

### 1.1 분석하고자 하는 3가지 narrative 패턴

| 패턴 | 의미 | 매핑되는 포트폴리오 액션 |
|---|---|---|
| **단기 급등** | 미약했던 narrative가 단기적으로 크게 상승 | 신규 진입 검토 |
| **지배적 상승** | 시장의 지배적 narrative가 꾸준히 상승 | 비중 확대 |
| **기존 강세 하락** | 기존에 크게 자리잡은 narrative가 최근 하락 | 비중 축소 |

### 1.2 각 narrative에 대해 산출하고자 하는 정보

1. 현재 attention 정량값
2. **신뢰도** — 통계적으로 유의한 추세인지, 일시적 노이즈인지

### 1.3 이 프로젝트 범위에서 명시적으로 제외하는 것

LLM은 아래 항목을 **임의로 추가하지 않는다**. 필요하다고 판단되면 사용자에게 먼저 제안한다.

- ❌ **재무 추세 분석** (매출, EPS 등) — 이 프로젝트 범위 제외
- ❌ **기술 추세 분석** (주가 모멘텀, RSI 등) — 이 프로젝트 범위 제외
- ❌ **Finnhub `/company-news`** — ticker 단위 호출 구조라 '시장 전체 narrative' 정의에 부적합 (Phase 0 검토 후 제외 결정)
- ⏸ **Narrative-주가 lead-lag 분석** — 차기 Phase로 보류 (Phase 0~3 완료 후 별도 진행)
- ⏸ **인플루언서 사전 / 귀속 분석** — 보류

### 1.4 분석 주기

**주 1회**. 매주 데이터를 갱신하고 위 산출물을 생성한다.

---

## 2. 확정된 결정사항

이 섹션은 **단정적**이다. 변경이 필요하면 사용자와 논의 후 이 섹션을 업데이트한다. LLM이 임의로 다른 선택을 하지 않는다.

| # | 항목 | 결정 |
|---|---|---|
| 1 | Narrative 정의 방식 | **사전 정의된 테마 리스트** (옵션 A) |
| 2 | 주 데이터 소스 | **GDELT DOC 2.0 ArtList** (37일 historical) — 현재 throttle 안정화 대기 중 (§3.2 ⚠️). 보조: **Finnhub `/news?category=general`** (latest snapshot baseline) |
| 3 | 보조 데이터 소스 | Reddit (수집은 하되 **분석에서는 제외**) |
| 4 | 캐시 전략 | UTC 일 단위 저장 + 응답 `id` 기준 dedup. GDELT는 빈 날짜만 신규 fetch (rate limit 절약), Finnhub `/news` general은 latest 100건이라 매번 fetch 후 누적 merge |
| 5 | 분석 주기 | 주 1회 |
| 6 | 신뢰도 산출 | **z-score + 지속성 + 다중 소스 confirmation의 가중합** |
| 7 | 인플루언서 사전 / 귀속 분석 | **보류** |
| 8 | Narrative ↔ 종목 매핑 | 사전 정의된 CSV 기반, narrative당 핵심 종목 5~10개 |
| 9 | Narrative-주가 lead-lag | **차기 Phase로 보류** (Phase 0~3 완료 후 별도 진행) |
| 10 | 재무/기술 추세 분석 | **이 프로젝트 범위에서 제외** |
| 11 | 데이터 윈도우 | 단기 분석은 37일, 장기 baseline은 `<TBD: Phase 0에서 결정>` |

---

## 3. 데이터 소스 명세

### 3.1 Finnhub `/news?category=general`

- **역할**: latest snapshot baseline (보조). historical 본 데이터원 아님
- **엔드포인트**: `https://finnhub.io/api/v1/news?category=general`
- **인증**: API key (`.env`의 `FINNHUB_API_KEY`, gitignore됨)
- **응답 특성** (실험 확정, 2026-05-09):
  - 한 번 호출 = 최신 100건 (~3-4일치 spanning)
  - 항목 schema: `id, datetime (unix), headline, summary, source, url, image, category, related`
- **historical 페이징 한계**: `minId` 파라미터는 **"이 ID보다 새로운 것" 필터** (polling 용). 작은 값을 줘도 동일한 latest 100을 반환. 큰 값을 주면 0건. → **과거 페이징 불가**
- **사용하지 않는 엔드포인트**: `company-news` (§1.3 참조), `stock/candle`, `stock/financials-reported` 등
- **캐시**: `data/cache/finnhub/news_general/<YYYY-MM-DD>.json` — UTC date로 분류, `id` 기준 dedup, 매 호출 시 누적 merge
- **구현**: [src/fetch/finnhub.py](src/fetch/finnhub.py) — `fetch_general_news()`, `save_general_news(items)`

### 3.2 GDELT DOC 2.0 ArtList

- **역할**: 본 데이터원 (37일 historical, narrative-keyword 검색)
- **엔드포인트**: `https://api.gdeltproject.org/api/v2/doc/doc?mode=ArtList&format=json`
- **인증**: 불필요 (공개 API)
- **지원 파라미터** (확정):
  - `query` 필수 — narrative별 키워드/테마
  - `startdatetime` / `enddatetime` (UTC, `YYYYMMDDHHMMSS`) — date range 지원
  - `maxrecords` 최대 250
  - `sort=DateDesc`
- **응답 항목**: `url, url_mobile, title, seendate (YYYYMMDDTHHMMSSZ), socialimage, domain, language, sourcecountry`
- **하루 단위 호출이 옳은 이유**: `sort=DateDesc`라 넓은 윈도우로 호출하면 250건이 최근 며칠에만 쏠리고 과거는 누락. **하루 단위로 끊어 호출** + 캐시.
- **캐시**: `data/cache/gdelt/<query_id>/<YYYY-MM-DD>.json` (예정 — query 단위 분리 필요)
- **구현**: [src/fetch/gdelt.py](src/fetch/gdelt.py) — `fetch_doc_articles(query, day, max_records=250)` (1일 단위 1회 호출, 검증 보류 상태)

#### ⚠️ 접근성 이슈 — 2026-05-09 시점 미해결

- **rate limit**: 문서 정책 1 req / 5초. 위반 시 cooldown이 시간~일 단위로 확장됨 (관측됨)
- **현 상태**: 6시간 이상 throttle 풀리지 않음. 모바일 핫스팟 (다른 IP)에서도 429 동일 응답 → 단일 IP 문제만은 아닌 것으로 추정 (CGNAT 풀 공유 또는 GDELT의 광범위 backoff)
- **에러 본문**: `Please limit requests to one every 5 seconds or contact kalev.leetaru5@gmail.com for larger queries.`
- **해결 시도 중**: 운영자(`kalev.leetaru5@gmail.com`)에게 안정 접근 권한 요청 메일 발송 → 응답 대기 (24~48h)
- **응답 후 갈림길**:
  - 권한 받음 → 5초 spacing for-loop orchestrator 작성 + 검증
  - 거절/무응답 → fallback (GDELT raw CDN files `data.gdeltproject.org/gdeltv2/` 직접 다운로드 + 파싱) 또는 유료 API (MarketAux ~$19/월, Tiingo ~$30/월) 결정
- **호출 시 필수 규칙**: 호출 사이 `time.sleep(5)` 이상. for-loop orchestrator 작성 시 반드시 반영

### 3.3 Reddit (분석 제외, 수집만)

- 향후 인플루언서 귀속 분석에서 사용 예정
- 현 단계에서는 산출물에 영향 없음

---

## 4. Narrative ↔ 종목 매핑

- **위치**: `config/narratives.csv`
- **스키마**: `narrative_id, narrative_name, ticker, weight, role`
  - `role`: `pure-play` | `peripheral` (귀속 분석 보류 상태이므로 현재는 메타데이터로만 사용)
- **규모**: narrative 30~50개, narrative당 핵심 종목 5~10개
- **현재 상태**: `<TBD: Phase 0에서 작성>`

---

## 5. 디렉토리 구조

```
PHASE3_2_narrative_2/
├── README.md                          # 이 문서
├── CLAUDE.md                          # 행동 규범
├── .env                               # FINNHUB_API_KEY (gitignore됨)
├── setup_js_env.sh                    # Python 환경 설정 (예정)
├── config/                            # (Phase 0 산출물)
│   └── narratives.csv                 # narrative ↔ 종목 매핑
├── data/
│   ├── cache/
│   │   ├── finnhub/
│   │   │   └── news_general/          # <YYYY-MM-DD>.json (생성됨)
│   │   └── gdelt/                     # <query_id>/<YYYY-MM-DD>.json (예정)
│   └── outputs/                       # 주간 분석 결과
├── src/
│   ├── fetch/
│   │   ├── finnhub.py                 # fetch_general_news, save_general_news
│   │   └── gdelt.py                   # fetch_doc_articles (검증 보류)
│   ├── score/                         # attention / 신뢰도 산출 (Phase 1~2)
│   └── classify/                      # 3-카테고리 분류 (Phase 3)
└── tests/                             # critical 로직 단위 테스트
```

**규칙**:
- 새 모듈 추가 시 위 구조를 따른다. 다른 위치에 만들지 않는다.
- 디렉토리 변경이 필요하면 사용자에게 먼저 제안한다.

---

## 6. 환경

- Python 3.12 (`setup_js_env.sh` 참조)
- 핵심 패키지: pandas 2.2.3, numpy 1.26.4, matplotlib 3.9.2, seaborn 0.13.2
- 추가 패키지가 필요하면 사용자에게 먼저 제안하고 `setup_js_env.sh`에 명시적으로 추가한다.

---

## 7. Phase별 작업 분할

각 Phase는 **독립적으로 검증 가능한 산출물**을 가진다. 다음 Phase로 넘어가기 전 검증 기준을 충족해야 한다.

### Phase 0 — 데이터 인벤토리 & narrative 정의

**작업**:
- ~~기존 fetch 코드 데이터 스키마 확인~~ ✅ (PHASE3_1 캐시 CSV 참조 — finnhub_news 응답 schema 확정)
- ~~Finnhub `/news` general 동작/한계 검증~~ ✅ (latest 100, ~4일치, historical 페이징 불가)
- ~~GDELT DOC 2.0 ArtList 동작 검증~~ ✅ (250 records / day, date range 지원)
- ~~Finnhub fetcher + cache 구현~~ ✅ ([src/fetch/finnhub.py](src/fetch/finnhub.py))
- ~~GDELT fetcher 함수 작성~~ ✅ ([src/fetch/gdelt.py](src/fetch/gdelt.py)) — 검증은 throttle로 보류
- `config/narratives.csv` 작성 (사용자와 함께)
- baseline 윈도우 길이 확정
- ⚠️ **현 블로커**: GDELT 안정 접근 (메일 응답 대기, §3.2 ⚠️ 참조)

**검증**:
- [x] Finnhub `/news` general 응답 schema 확인 — `id, datetime, headline, summary, source, url, image, category, related`
- [x] GDELT DOC 2.0 ArtList 응답 schema 확인 — `url, title, seendate, domain, language, sourcecountry, ...`
- [x] Finnhub historical 한계 실험 확정 (minId 동작 검증, 2026-05-09)
- [ ] GDELT 안정 접근 확보 (메일 응답)
- [ ] `narratives.csv`에 narrative 30~50개, 각 5~10 종목 매핑 완료
- [ ] baseline 윈도우 결정사항이 README §2 #11에 반영됨
- [ ] 상태 — **진행 중 (GDELT blocker)**

### Phase 1 — Attention Score 산출

**작업**:
- narrative별 일별 attention score 계산
- Finnhub + GDELT 가중 결합

**검증**:
- [ ] 알려진 historical narrative(예: 2023년 GLP-1 폭발, 2023년 AI 붐)의 시계열에서 알려진 시점에 spike가 관찰됨
- [ ] sanity check 시각화 산출물이 `data/outputs/sanity/`에 저장됨
- [ ] 상태 — `<TBD>`

### Phase 2 — 변화 탐지 & 신뢰도

**작업**:
- z-score, 지속성, 다중 소스 confirmation 산출
- 가중합 공식 확정

**가중합 공식**: `<TBD: Phase 2에서 결정 후 이 자리에 명시>`

**검증**:
- [ ] 알려진 "신뢰할 만한 상승" 사례에 대해 시스템이 높은 신뢰도 부여
- [ ] 알려진 "일시적 노이즈" 사례에 대해 시스템이 낮은 신뢰도 부여
- [ ] 상태 — `<TBD>`

### Phase 3 — 3-카테고리 분류 & 액션 매핑

**작업**:
- "단기 급등 / 지배적 상승 / 기존 강세 하락" 분류 룰 구현
- 주간 출력 리포트 생성

**검증**:
- [ ] 출력이 사용자의 직관과 spot-check 단계에서 일치
- [ ] `data/outputs/<YYYY-WW>/report.md` 형태로 주간 리포트 생성
- [ ] 상태 — `<TBD>`

### 차기 Phase (이 프로젝트 완료 후 별도 진행)

- **Lead-lag 분석**: narrative 시계열 vs 주가 시계열 cross-correlation
- **귀속 분석**: firm event vs social buzz 분리, 인플루언서 사전 도입
- **재무/기술 추세 결합**: 별도 파이프라인으로 추가 검토 가능

---

## 8. 작업 진행 규칙 (CLAUDE.md와 연결)

- **한 번에 한 Phase, 한 Phase 안에서도 한 기능씩**. 여러 Phase를 동시에 건드리지 않는다.
- 각 작업 완료 시 CLAUDE.md §4의 보고 형식(Verified / Not verified / Uncertain)을 따른다.
- Phase 검증 기준이 충족되면 README의 해당 체크박스를 업데이트한다.
- 결정사항(§2)에 반하는 구현이 필요해 보이면 **멈추고 사용자에게 확인**한다.
- §1.3에 명시된 **제외 항목**(재무/기술 추세 등)을 LLM이 임의로 추가하지 않는다.
- `<TBD>` 자리는 **임의로 채우지 않는다**. 해당 Phase에서 사용자와 함께 결정한다.

---

## 9. 현재 진행 상황

- [x] Phase 분할 합의 완료
- [x] 결정사항 §2 #1, #3~11 확정 / **#2 (주 데이터 소스)는 GDELT 안정 접근 확보 후 최종 확정**
- [x] Phase 0 시작 — 데이터 소스 검증 진행 중
- [x] Finnhub `/news` general fetcher + UTC date 캐시 구현 완료
- [x] GDELT fetcher 함수 작성 완료 (검증은 throttle로 보류)
- [ ] **현 블로커**: GDELT throttle — `kalev.leetaru5@gmail.com` 응답 대기 (메일 발송 2026-05-09)
- [ ] 응답 후:
  - 권한 받음 → `time.sleep(5)` 포함 37-day for-loop orchestrator 작성 + 검증
  - 거절/무응답 → fallback 결정 (raw CDN files 또는 유료 API)