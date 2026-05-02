# Global Stock Screening System - 세션 요약
> Date: 2026-05-01
> 범위: PHASE0 완료 → PHASE1 Momentum 완료
> 목적: 내일 새 채팅에서 PHASE2 Fundamental 시작 시 컨텍스트 제공

---

## 1. 프로젝트 개요

**글로벌(미국시장) 주식 스크리닝 시스템** — Domestic(한국시장) 시스템을 미러링.
6-Phase 프레임워크, 각 Phase마다 `리서치→수정→플래닝→수정→구현→수정` 워크플로우.

| Phase | 이름 | 상태 |
|-------|------|------|
| PHASE0 | Classification (섹터 분류) | **완료** |
| PHASE1 | Momentum (모멘텀 백테스트) | **완료** |
| PHASE2 | Fundamental (펀더멘탈 스코어링) | 미구현 |
| PHASE3 | Narrative (내러티브/감성분석) | 미구현 |
| PHASE4 | Macro (매크로 환경) | 미구현 |
| PHASE5 | Report (사업보고서 심층분석) | 일부 완료 (Manual) |

---

## 2. PHASE0 Classification (완료)

- **유니버스**: 2,280종목 (US 1,841 + ADR 439)
- **분류**: GICS 11개 섹터
- **데이터소스**: NASDAQ Screener CSV + yfinance
- **산출물**: `PHASE0_classification/20260501_classification_master.xlsx`
  - 시트 `전체종목`: Symbol, Name, Market Cap, Country, IPO Year, Industry, Sector, GICS_Sector 등

---

## 3. PHASE1 Momentum (완료)

### 3.1 아키텍처
3-step 파이프라인 + 일일 러너:
```
data_collector.py → momentum_backtest.py → momentum_ranking.py
                  ↑ run_daily.py (순차 실행)
```

### 3.2 핵심 파일
| 파일 | 역할 |
|------|------|
| `20260501_data_collector.py` | yfinance 증분 수집, Daily/Weekly 캐시 |
| `20260501_momentum_backtest.py` | 4지표 × 32조합 백테스트 |
| `20260501_momentum_ranking.py` | Top20 + Sector Top3 + Composite = 9차트 |
| `run_daily.py` | 일일 실행 러너 (--skip-collect, --only-collect) |
| `test_verify.py` | 80항목 검증 (완료 후 삭제 가능) |

### 3.3 지표
- **DD** (Drawdown): Calmar Ratio, Forward MDD, Recovery Time 등 5개 서브지표
- **MACD**: Golden/Dead Cross 매매, 비용 차감
- **RSI**: 과매도 반등 매매, 비용 차감
- **HIGH52**: 52주 신고가 돌파 + 트레일링 스탑

### 3.4 백테스트 매트릭스
4 지표 × 4 기간(1Y/3Y/5Y/10Y) × 2 프레임(Daily/Weekly) = 32조합
→ 실제 30시트 (HIGH52_Daily_1Y, HIGH52_Weekly_1Y는 250일 윈도우 부족으로 제외)

### 3.5 랭킹 기준
- **종목 Top 20**: Daily_1Y 기준 (HIGH52만 Daily_3Y)
- **섹터 Top 3**: GICS 섹터별 상위 3종목
- **복합 모멘텀**: 4지표 중 2개+ Top50 교집합
- **비용모델**: c=0.02% (one-way), 0.04% roundtrip

### 3.6 캐시 구조
```
cache/
├── daily_cache.pkl     # 일간 OHLCV (고정 파일명, 매일 덮어쓰기)
└── weekly_cache.pkl    # 주간 리샘플링
```

### 3.7 산출물
```
results/
├── 20260501_momentum_backtest.xlsx   # 30시트
└── 20260501_momentum_ranking.xlsx    # Top20×4 + SectorTop3×4 + Composite
charts/
├── 20260501_top20_dd.png
├── 20260501_top20_macd.png
├── 20260501_top20_rsi.png
├── 20260501_top20_high52.png
├── 20260501_sector_top3_dd.png
├── 20260501_sector_top3_macd.png
├── 20260501_sector_top3_rsi.png
├── 20260501_sector_top3_high52.png
└── 20260501_composite_momentum.png
```

### 3.8 검증 결과
80/80 통과 (2026-05-01 최종)

---

## 4. 핵심 기술 노트 (Global 공통)

### yfinance 1.3.0 필수
- 0.2.x는 Yahoo API 변경으로 완전 실패 (JSONDecodeError)
- `yf.download(tickers, group_by='ticker')` → MultiIndex 컬럼 `(ticker, metric)`
- 종목 추출: `data[ticker].copy()` (`.xs()` 아님)
- 배치 크기 80, 배치 간 2초 sleep, 최대 3회 재시도
- `auto_adjust=True`로 수정주가 사용

### 데이터 수집 패턴 (Domestic과 동일)
- 최초 실행: 전체 수집 (10년치)
- 이후 실행: 증분 업데이트 (마지막 날짜 이후만 추가)
- 고정 파일명 캐시 (날짜 없음, 매일 덮어쓰기)
- `logs/update_history.csv`로 누적 이력 관리

### run_daily.py 패턴
- 데이터 수집 → 분석 → 결과 산출 순차 실행
- subprocess로 각 스크립트 호출
- 실패 시 이후 단계 중단
- `--skip-collect`, `--only-collect` 옵션

---

## 5. Domestic PHASE2 Fundamental 요약 (Global 참고용)

Domestic에서 이미 구현된 펀더멘탈 시스템의 핵심 구조:

### 5.1 설계 철학
- **Forward 중심**: 향후 12개월 컨센서스 기반 (과거 데이터는 보조)
- **3 카테고리만**: 밸류에이션 / 성장성 / 주주환원 → 중복 없는 명확한 구분
- **재무건전성 = 필터**: 부실기업 사전 제거 (스코어링 아님)
- **Trailing fallback**: Forward 없으면 Trailing 사용, 가중치 50% 패널티

### 5.2 스코어링 카테고리
| 카테고리 | 가중치 | 핵심 지표 |
|----------|--------|-----------|
| 밸류에이션 | 30% | Forward PER, PEG, NAV Discount(지주사) |
| 성장성 | 40% | Forward 매출/영업이익/EPS 성장률, EPS Revision |
| 주주환원 | 30% | Total Shareholder Yield, Payout Ratio, Buyback Yield |

### 5.3 재무건전성 필터 (사전 제거)
- 자본잠식 (자기자본 ≤ 0)
- 부채비율 과다 (> 400%, 금융업 제외)
- 이자보상배율 미달 (영업이익/이자비용 < 1)
- 3년 연속 영업적자

### 5.4 Domestic 데이터소스 → Global 변환 필요
| Domestic | 용도 | Global 대안 (검토 필요) |
|----------|------|------------------------|
| pykrx | 시총, PER, EPS, 배당 | yfinance (`Ticker.info`, `Ticker.financials`) |
| DART OpenAPI | 재무제표, 현금흐름, 주주환원 | SEC EDGAR / yfinance financials |
| FnGuide | Forward 컨센서스 | Yahoo Finance estimates / Finviz / 유료API |
| NAV Calculator | 지주사 NAV | 해당 없음 (미국은 지주사 구조 다름) |

### 5.5 Domestic 스크립트 구조
```
scripts/
├── data_collector.py        # pykrx + DART 수집
├── consensus_collector.py   # FnGuide Forward 컨센서스 스크래핑
├── nav_calculator.py        # 지주사 NAV 계산
├── fundamental_scoring.py   # 필터 + 3-카테고리 스코어링 + 차트
└── run_daily.py             # 순차 실행 러너
```

### 5.6 Global PHASE2에서 달라질 점 (예상)
1. **Forward 컨센서스 소스**: FnGuide → yfinance estimates / 기타 (리서치 필요)
2. **재무제표 소스**: DART → yfinance `Ticker.financials` / SEC EDGAR
3. **지주사 NAV**: 미국시장에서는 불필요 (Berkshire 등 극소수)
4. **주주환원 데이터**: DART 현금흐름표 → yfinance `Ticker.cashflow`
5. **종목 수**: Domestic ~1,271 → Global 2,280 (API 호출량 고려)
6. **회계 기준**: K-IFRS → US GAAP
7. **통화**: KRW → USD

---

## 6. 워크플로우 규칙

### 각 Phase 워크플로우
```
리서치 → (사용자 수정) → 플래닝 → (사용자 수정) → 구현 → (사용자 수정/검증)
```

### 파일 네이밍
- 문서: `docs/YYYYMMDD_research.md`, `docs/YYYYMMDD_planning.md`
- 스크립트: `YYYYMMDD_scriptname.py`
- 결과: `results/YYYYMMDD_*.xlsx`, `charts/YYYYMMDD_*.png`
- 러너: `run_daily.py` (날짜 없음)

### 검증 패턴
- `test_verify.py` 작성 → 전 항목 통과 확인 → 삭제
- MACD/DD 등 수동 계산으로 spot-check

### 주의사항
- ADR 종목 포함 (모멘텀/펀더멘탈 모두)
- 비용모델: c=0.02% (one-way)
- 차트: matplotlib, `figure.dpi=150`
- 캐시: pickle (고정 파일명, 매일 덮어쓰기)
- 로그: CSV 형태 (`logs/` 폴더)

---

## 7. 내일 PHASE2 시작 시 참고

### 진행 순서
1. **리서치**: Global에서 사용할 데이터소스 확정 (yfinance estimates? 유료API?)
2. **플래닝**: Domestic 구조 참고하되 Global 특성 반영한 구현 계획
3. **구현**: 스크립트 작성 + 실행
4. **검증**: test_verify.py로 전수 검증

### 핵심 확인 사항
- yfinance `Ticker.info`에서 Forward PER/EPS 얻을 수 있는지 테스트
- yfinance `Ticker.financials` / `Ticker.cashflow`에서 재무제표 품질 확인
- 2,280종목 대상 개별 Ticker 호출 시 rate limit 확인 (download()와 달리 개별 호출은 제한 있음)
- Forward 컨센서스 커버리지 (애널리스트 커버 없는 소형주는 Trailing fallback)

### 관련 파일 경로
```
Global/
├── PHASE0_classification/20260501_classification_master.xlsx  # 유니버스
├── PHASE1_momentum/                                           # 모멘텀 (완료)
├── PHASE2_fundamental/docs/                                   # 여기서 시작
│
Domestic/
├── PHASE2_fundamental/docs/20260430_research.md               # 참고용
├── PHASE2_fundamental/docs/20260430_planning.md               # 참고용
├── PHASE2_fundamental/scripts/                                # 참고용
```
