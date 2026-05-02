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

## 참고 (Domestic)
- Domestic PHASE3는 미구현 상태
- 향후 국내 뉴스, 증권사 리포트, 커뮤니티 감성 분석 예정
