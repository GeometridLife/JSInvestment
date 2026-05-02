# PHASE5 Report — 감사/사업보고서 심층 분석 시스템

## 개요
DART에 공시된 사업보고서·분기보고서를 수집하고, Claude API를 활용한 4단계 심층 분석을 수행한 뒤,
전문 수준의 .docx 분석 리포트를 자동 생성하는 파이프라인.

## 파이프라인 구조

```
[Step 1] dart_report_fetcher.py
  - PHASE2 시총 상위 500종목 대상
  - OpenDartReader.list() → rcpt_no 확보
  - OpenDartReader.document_all(rcpt_no) → XML 전문 수집
  - 종목별 캐시: cache/{ticker}_{year}_{quarter}.pkl

[Step 2] report_analyzer.py
  - Claude API (anthropic SDK)로 4단계 분석 수행
    1) 파일 리서치 (전체 통독)
    2) 중요 내용 1차 정리
    3) 놓친 부분 체크 (재검토)
    4) 중요 내용 최종 정리
  - 분석 결과 JSON 저장: cache/{ticker}_{year}_{quarter}_analysis.json

[Step 3] report_generator.js
  - docx-js(Node.js)로 마이크로인피니티 예시 형식의 .docx 생성
  - 출력: result/{tier1섹터}/{year}/{quarter}/{회사명}_분석보고서.docx

[Orchestrator] run_pipeline.py
  - Step1→2→3 순차 실행
  - 진행률 표시, 에러 로깅
  - 특정 종목/섹터/분기만 선택 실행 가능
```

## 폴더 구조

```
PHASE5_report/
├── scripts/
│   ├── dart_report_fetcher.py   # Step 1
│   ├── report_analyzer.py       # Step 2
│   ├── report_generator.js      # Step 3
│   └── run_pipeline.py          # Orchestrator
├── docs/
│   └── architecture.md          # 본 문서
├── cache/                       # 중간 결과물 캐시
├── logs/                        # 실행 로그
└── result/                      # 최종 리포트 출력
    ├── 반도체/
    │   └── 2025/
    │       └── 4Q/
    │           └── 삼성전자_분석보고서.docx
    ├── 바이오∕제약∕헬스케어/
    └── ...
```

## DART 보고서 코드 매핑

| reprt_code | 보고서 유형 | 분기 표기 |
|-----------|-----------|----------|
| 11013     | 1분기보고서 | 1Q       |
| 11012     | 반기보고서  | 2Q       |
| 11014     | 3분기보고서 | 3Q       |
| 11011     | 사업보고서  | 4Q       |

## 환경 변수 (.env)

```
DART_API_KEY=...         # 기존
ANTHROPIC_API_KEY=...    # 추가 필요
```

## 의존성

- Python: OpenDartReader, anthropic, python-dotenv, pandas, beautifulsoup4
- Node.js: docx (npm install -g docx)
