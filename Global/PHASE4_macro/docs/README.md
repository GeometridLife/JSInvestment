# PHASE4: Global Macro Indicators (매크로 지표)

## 목표
거시경제 지표를 수집·분석하여 시장 전체 및 섹터별 매크로 환경을 평가한다.

## 워크플로우
```
리서치 → 플래닝 → 수정 → 구현 → 수정
```

## 폴더 구조
```
PHASE4_macro/
├── docs/          # 리서치 & 플래닝 문서
│   ├── YYYYMMDD_research.md
│   └── YYYYMMDD_planning.md
├── scripts/       # 실행 스크립트
├── cache/         # 중간 결과물 캐시
├── logs/          # 실행 로그
└── results/       # 최종 결과
```

## 주요 검토 사항
- 데이터 소스: FRED (미국), ECB, BOJ, PBOC, World Bank, IMF
- 핵심 지표: 금리(Fed Funds, 10Y Treasury), 인플레이션(CPI, PCE), 고용(NFP, 실업률)
- 추가 지표: ISM PMI, 소비자신뢰지수, GDP 성장률, 환율, 원자재(유가, 금, 구리)
- 시장 지표: VIX, 신용 스프레드, 수익률 커브(2Y-10Y), 달러인덱스(DXY)
- 글로벌 확장: 미국 중심 → 유럽/아시아 매크로 지표 추가
- 시그널화: 매크로 레짐 분류 (Risk-On / Risk-Off / Transition)

## 참고 (Domestic)
- Domestic PHASE4는 미구현 상태
- 국내 매크로: 한은 기준금리, 원/달러 환율, 수출입 동향 등 예정
