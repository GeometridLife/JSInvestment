# PHASE2: Global Fundamental Indicators (펀더멘탈 지표)

## 목표
Forward 컨센서스 기반 펀더멘탈 스크리닝 지표를 글로벌 종목에 적용한다.

## 워크플로우
```
리서치 → 플래닝 → 수정 → 구현 → 수정
```

## 폴더 구조
```
PHASE2_fundamental/
├── docs/          # 리서치 & 플래닝 문서
│   ├── YYYYMMDD_research.md
│   └── YYYYMMDD_planning.md
├── scripts/       # 실행 스크립트
│   ├── data_collector.py
│   ├── consensus_collector.py
│   ├── fundamental_scoring.py
│   └── run_daily.py
├── data/          # 정적 데이터 (지주사 목록 등)
├── cache/         # 중간 결과물 캐시
├── logs/          # 실행 로그
└── results/       # 최종 결과 (xlsx, 차트)
```

## 스코어링 프레임워크 (Domestic 기준 — 글로벌 적응 필요)
```
[필터] 재무건전성 → 부실/위험 종목 제거
[스코어링] 밸류에이션(30%) + 성장성(40%) + 주주환원(30%)
```

## 주요 검토 사항
- Forward 컨센서스 소스: Bloomberg, Refinitiv, Visible Alpha, Koyfin, SimplyWall.St
- 재무제표 소스: SEC EDGAR (미국), 각국 공시시스템
- 주주환원: Buyback + Dividend (미국은 자사주매입 비중 높음)
- 회계 기준 차이: US GAAP vs IFRS
- 통화 환산: 매출/이익 비교 시 USD 기준 통일 여부
- ADR/GDR 중복 상장 처리

## 참고 (Domestic)
- Forward: FnGuide 컨센서스 스크래핑 (~500종목)
- Trailing: DART 재무제표 + pykrx
- 지주사 NAV 조정, 금융업 별도 처리
- Forward 없는 종목은 Trailing fallback (가중치 50% 감소)
