# JS Global Investment — 글로벌 주식 스크리닝 시스템

## 개요
글로벌 주식 시장 대상 멀티팩터 스크리닝 시스템.
Domestic(국내)과 동일한 6-Phase 프레임워크를 적용한다.

## Phase 구조

| Phase | 이름 | 설명 | 상태 |
|-------|------|------|------|
| PHASE0 | Classification | 섹터 분류 & 유니버스 확정 | **완료** (2026-05-01) |
| PHASE1 | Momentum | 모멘텀 지표 산출 | **완료** (2026-05-01) |
| PHASE2 | Fundamental | 펀더멘탈 지표 산출 (Forward 컨센서스 기반) | 미구현 |
| PHASE3 | Narrative | 내러티브 지표 산출 (뉴스/감성분석) | 미구현 |
| PHASE4 | Macro | 매크로 지표 산출 (거시경제 환경) | 미구현 |
| PHASE5 | Report | 사업보고서 심층 분석 리포트 생성 | 미구현 |

## 각 Phase 워크플로우
```
리서치 → 플래닝 → 수정 → 구현 → 수정
```
- 리서치: 데이터 소스, 지표 설계, 선행 연구 정리 → `docs/YYYYMMDD_research.md`
- 플래닝: 구현 계획, 스크립트 설계, 의존성 정리 → `docs/YYYYMMDD_planning.md`
- 구현: Python/Node.js 스크립트 → `scripts/`
- 결과: xlsx, 차트, PDF 리포트 → `results/` or `result/`

## 폴더 구조
```
Global/
├── README.md                    # 본 문서
├── PHASE0_classification/       # 섹터 분류
├── PHASE1_momentum/             # 모멘텀 지표
│   ├── docs/
│   ├── scripts/
│   ├── cache/
│   ├── logs/
│   └── results/
├── PHASE2_fundamental/          # 펀더멘탈 지표
│   ├── docs/
│   ├── scripts/
│   ├── data/
│   ├── cache/
│   ├── logs/
│   └── results/
├── PHASE3_narrative/            # 내러티브 지표
│   ├── docs/
│   ├── scripts/
│   ├── cache/
│   ├── logs/
│   └── results/
├── PHASE4_macro/                # 매크로 지표
│   ├── docs/
│   ├── scripts/
│   ├── cache/
│   ├── logs/
│   └── results/
├── PHASE5_report/               # 사업보고서 분석
│   ├── docs/
│   ├── scripts/
│   ├── cache/
│   ├── logs/
│   └── result/
└── Manual_report/               # 수동 다운로드 보고서
```

## Domestic과의 차이점 (예상)
- 데이터 소스: pykrx/DART/FnGuide → yfinance/SEC EDGAR/Bloomberg 등
- 분류 체계: WICS → GICS
- 통화: KRW → USD (or 현지통화)
- 보고서: 사업보고서 → 10-K/Annual Report
- 회계 기준: K-IFRS → US GAAP / IFRS

## 환경 변수 (.env)
```
ANTHROPIC_API_KEY=...    # Claude API (PHASE5 분석용)
# 추가 API 키는 각 Phase 구현 시 결정
```
