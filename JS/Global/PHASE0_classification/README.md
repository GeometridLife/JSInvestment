# PHASE0: Global Stock Classification (섹터 분류)

## 목표
글로벌 주요 시장(미국, 유럽, 일본, 중국 등) 상장 종목을 섹터별로 분류하고 스크리닝 유니버스를 확정한다.

## 워크플로우
```
리서치 → 플래닝 → 수정 → 구현 → 수정
```

## 산출물
- `YYYYMMDD_research.md` — 리서치 (데이터 소스, 분류 체계, 필터 기준)
- `YYYYMMDD_planning.md` — 구현 계획
- `YYYYMMDD_classification.py` — 분류 스크립트
- `YYYYMMDD_classification_master.xlsx` — 마스터 테이블 (종목코드, 종목명, 섹터, 시총, 거래소 등)

## 주요 검토 사항
- 분류 체계: GICS / ICB / 자체 분류
- 데이터 소스: Yahoo Finance, Bloomberg, MSCI, 각국 거래소 API
- 필터 기준: 시가총액, 거래량, 유동성 기준
- 대상 거래소: NYSE, NASDAQ, LSE, TSE, HKEX, SSE 등
- 통화 처리: USD 기준 환산 여부

## 참고 (Domestic)
- Domestic PHASE0는 WICS 기반 18개 섹터로 분류
- KOSPI+KOSDAQ에서 시총 ≥1,000억 & 일평균거래대금 ≥10억 필터 → 1,271종목
