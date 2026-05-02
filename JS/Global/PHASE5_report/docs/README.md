# PHASE5: Global Business Report Analysis (사업보고서 심층 분석)

## 목표
글로벌 기업의 Annual Report / 10-K / 사업보고서를 수집·분석하여 전문 수준의 분석 리포트를 자동 생성한다.

## 워크플로우
```
리서치 → 플래닝 → 수정 → 구현 → 수정
```

## 폴더 구조
```
PHASE5_report/
├── docs/          # 아키텍처 & 분석 프로세스 문서
│   ├── architecture.md
│   └── analysis_process.md
├── scripts/       # 파이프라인 스크립트
│   ├── report_fetcher.py      # Step 1: 보고서 수집
│   ├── report_analyzer.py     # Step 2: Claude API 4단계 분석
│   ├── report_generator.js    # Step 3: docx 생성
│   └── run_pipeline.py        # Orchestrator
├── cache/         # 분석 JSON 캐시
├── logs/          # 실행 로그
└── result/        # 최종 리포트 출력
    └── {sector}/{year}/{quarter}/
```

## 파이프라인 (Domestic 기준 — 글로벌 적응 필요)
```
[Step 1] 보고서 수집 (SEC EDGAR 10-K / 각국 공시)
[Step 2] Claude API 4단계 분석
  1) 파일 리서치 (전체 통독)
  2) 중요 내용 1차 정리
  3) 놓친 부분 체크 (재검토)
  4) 중요 내용 최종 정리
[Step 3] docx/PDF 리포트 생성
```

## 주요 검토 사항
- 보고서 수집: SEC EDGAR (미국 10-K/10-Q), Companies House (영국), EDINET (일본), 巨潮资讯 (중국)
- 수동 보고서: Manual_report/ 폴더에 직접 다운로드한 PDF 지원
- 분석 언어: 영문 보고서 → 영문 or 한글 리포트
- 리포트 형식: Domestic과 동일한 docx → PDF 파이프라인
- 토큰 관리: 영문 10-K는 국문 사업보고서보다 길 수 있음 → 청크 분할 검토

## 참고 (Domestic)
- DART OpenDartReader로 XML 전문 수집
- Claude API (claude-sonnet-4-20250514) 4단계 분석
- docx-js(Node.js)로 보고서 생성 → LibreOffice로 PDF 변환
- Noto Sans KR 폰트 사용
