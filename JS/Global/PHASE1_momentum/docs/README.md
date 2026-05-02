# PHASE1: Global Momentum Indicators (모멘텀 지표)

## 목표
글로벌 종목 대상 모멘텀 기반 스크리닝 지표를 산출한다.

## 워크플로우
```
리서치 → 플래닝 → 수정 → 구현 → 수정
```

## 폴더 구조
```
PHASE1_momentum/
├── docs/          # 리서치 & 플래닝 문서
│   ├── YYYYMMDD_research.md
│   └── YYYYMMDD_planning.md
├── scripts/       # 실행 스크립트
│   ├── data_collector.py
│   ├── momentum_ranking.py
│   ├── momentum_backtest.py
│   └── run_daily.py
├── cache/         # 중간 결과물 캐시
├── logs/          # 실행 로그
└── results/       # 최종 결과 (xlsx, 차트)
```

## 주요 검토 사항
- 모멘텀 전략: Dual Momentum, MACD, RSI, 52주 신고가, 볼린저밴드 등
- 백테스트: 기간별(1Y/3Y/5Y/10Y), 주기별(일봉/주봉)
- 데이터 소스: yfinance, Alpha Vantage, Polygon.io 등
- 시간대 처리: 각 거래소 시간대 차이 고려
- 벤치마크: S&P 500, MSCI World 등

## 참고 (Domestic)
- Domestic은 DD(5개 보조지표), MACD, RSI, 52주 신고가 4개 전략 사용
- pykrx 기반 데이터 수집, 1Y/3Y/5Y/10Y × 일봉/주봉 백테스트 수행
