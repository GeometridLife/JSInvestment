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
| 2 | 주 데이터 소스 | Finnhub `company-news` + GDELT |
| 3 | 보조 데이터 소스 | Reddit (수집은 하되 **분석에서는 제외**) |
| 4 | 캐시 전략 | 일 단위 저장, **빈 날짜만** 신규 fetch |
| 5 | 분석 주기 | 주 1회 |
| 6 | 신뢰도 산출 | **z-score + 지속성 + 다중 소스 confirmation의 가중합** |
| 7 | 인플루언서 사전 / 귀속 분석 | **보류** |
| 8 | Narrative ↔ 종목 매핑 | 사전 정의된 CSV 기반, narrative당 핵심 종목 5~10개 |
| 9 | Narrative-주가 lead-lag | **차기 Phase로 보류** (Phase 0~3 완료 후 별도 진행) |
| 10 | 재무/기술 추세 분석 | **이 프로젝트 범위에서 제외** |
| 11 | 데이터 윈도우 | 단기 분석은 37일, 장기 baseline은 `<TBD: Phase 0에서 결정>` |

---

## 3. 데이터 소스 명세

### 3.1 Finnhub

- **사용 엔드포인트**: `company-news` (티커별 뉴스)
- **사용하지 않는 엔드포인트**: `stock/candle`, `stock/financials-reported` 등 (재무/기술 추세 분석은 범위 외)
- **윈도우**: 단기 37일 + baseline 윈도우 `<TBD>`
- **캐시**: `data/cache/finnhub/<ticker>/<YYYY-MM-DD>.json` (일 단위)
- **fetch 정책**: 빈 날짜에 대해서만 신규 요청. 기존 파일은 건드리지 않음.

### 3.2 GDELT

- **사용 데이터**: `<TBD: Phase 0에서 GDELT 어떤 API/데이터셋을 쓸지 확정>`
- **캐시**: `data/cache/gdelt/<YYYY-MM-DD>.json`

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
Narrative/
├── README.md              # 이 문서
├── CLAUDE.md              # 행동 규범
├── setup_js_env.sh        # Python 환경 설정
├── config/
│   └── narratives.csv     # narrative ↔ 종목 매핑 (Phase 0 산출물)
├── data/
│   ├── cache/             # 일별 raw 데이터 캐시
│   │   ├── finnhub/
│   │   └── gdelt/
│   └── outputs/           # 주간 분석 결과
├── src/
│   ├── fetch/             # 데이터 수집 (Phase 0~1)
│   ├── score/             # attention / 신뢰도 산출 (Phase 1~2)
│   └── classify/          # 3-카테고리 분류 (Phase 3)
└── tests/                 # critical 로직 단위 테스트
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
- 기존 fetch 코드의 정확한 데이터 스키마 확인
- `config/narratives.csv` 작성 (사용자와 함께)
- baseline 윈도우 길이 확정
- GDELT 사용 데이터셋 확정

**검증**:
- [ ] `narratives.csv`에 narrative 30~50개, 각 5~10 종목 매핑 완료
- [ ] Finnhub/GDELT 응답 샘플 1건씩 문서화
- [ ] baseline 윈도우 결정사항이 README §2 #11에 반영됨
- [ ] 상태 — `<TBD>`

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
- [x] 결정사항 §2 #1~10 확정
- [ ] Phase 0 시작 전