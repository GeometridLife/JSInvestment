"""
PHASE5 Report - Step 2: Claude API 기반 4단계 감사/사업보고서 분석
Date: 2026-05-01
Description:
    - Step 1에서 수집한 보고서 텍스트를 Claude API로 분석
    - 4단계 프로세스: 파일 리서치 → 1차 정리 → 놓친 부분 체크 → 최종 정리
    - 분석 결과를 JSON으로 저장 (cache/{ticker}_{year}_{quarter}_analysis.json)

Usage:
    C:/Python311/python.exe scripts/report_analyzer.py
    C:/Python311/python.exe scripts/report_analyzer.py --year 2025 --quarter 4Q
    C:/Python311/python.exe scripts/report_analyzer.py --ticker 005930
    C:/Python311/python.exe scripts/report_analyzer.py --sector 반도체
"""

import os
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env')
load_dotenv(_env_path)

import sys
import time
import datetime
import pickle
import json
import argparse
import glob
import pandas as pd

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
DOMESTIC_DIR = os.path.dirname(BASE_DIR)
PHASE0_DIR = os.path.join(DOMESTIC_DIR, 'PHASE0_classification')
PHASE2_DIR = os.path.join(DOMESTIC_DIR, 'PHASE2_fundamental')

CACHE_DIR = os.path.join(BASE_DIR, 'cache')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Claude API 설정
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # 비용/성능 밸런스
MAX_INPUT_CHARS = 180_000     # 보고서 텍스트 최대 길이 (토큰 제한 고려)
MAX_TOKENS_STEP1 = 4096       # 파일 리서치 응답
MAX_TOKENS_STEP2 = 8192       # 1차 정리 응답
MAX_TOKENS_STEP3 = 4096       # 놓친 부분 체크 응답
MAX_TOKENS_STEP4 = 12000      # 최종 정리 응답 (가장 긴 출력)

SLEEP_BETWEEN_CALLS = 2.0     # API 호출 간 대기 (rate limit)

# ============================================================
# 프롬프트 정의 — 4단계 분석 프로세스
# ============================================================

SYSTEM_PROMPT = """당신은 한국 상장기업의 감사보고서/사업보고서를 심층 분석하는 전문 재무분석가입니다.

분석 철학:
1. 숫자보다 맥락: 절대값이 아닌 변화율과 구조 비율에 집중
2. 재무제표 4종 + 주석의 균형: 손익·재무상태·자본변동·현금흐름 + 주석을 모두 교차 검증
3. 경영진이 강조하지 않는 것에 주목: 충당금 신설, 평가손실, 우발채무
4. 이익의 질(Quality of Earnings) 점검: 회계 이익과 현금 이익의 갭이 핵심
5. 2회차 검토 필수: 1차 정리 후 반드시 놓친 부분 체크 → 수정

분석 시 피해야 할 함정:
- 매출 증가 = 무조건 긍정 (매출총이익률 하락, 매출채권·재고 동반 증가 확인)
- 회계 이익 흑자 = 사업 정상 (영업현금흐름 흑자 여부가 더 중요)
- 부채 증가 = 무조건 부정 (선수금 증가는 긍정, 차입금 증가는 주의)
- 우선주는 자본 (RCPS는 경제적 실질은 부채에 가까움)
- 감사 적정의견 = 회사 안정 (회계기준 준수 여부일 뿐)

응답은 반드시 한국어로 작성하세요."""


def get_step1_prompt(report_text, company_name):
    """Step 1: 파일 리서치 (전체 통독)"""
    return f"""## 분석 대상
회사명: {company_name}

## 보고서 전문
{report_text}

## 지시사항: Step 1 — 파일 리서치 (전체 통독)

보고서 전체 구조와 회사의 전반적 윤곽을 파악하세요. 이 단계에서는 깊은 분석 없이 정보를 흡수합니다.

다음 항목을 점검하고 정리하세요:

### 1.1 감사보고서 메타정보
- 회사명, 결산기, 보고기간
- 감사인, 감사의견 (적정/한정/부적정/의견거절)
- 회계기준 (K-IFRS / K-GAAP / 중소기업회계처리 특례)

### 1.2 회사 기본 프로필
- 설립일·본사 위치
- 주요 사업 (정관상 사업목적)
- 대표이사·주요 주주
- 자본금 및 발행주식수

### 1.3 재무제표 4종 요약
- 재무상태표: 자산·부채·자본의 절대 규모
- 손익계산서: 매출~당기순이익까지 흐름
- 자본변동표: 자본 항목 변동 내역
- 현금흐름표: 영업·투자·재무 3대 흐름

### 1.4 주석 주요 사항
- 회계정책 (감가상각, 재고평가 등)
- 특수관계자 거래
- 우발채무·약정사항
- 자본 관련 사항 (RCPS, CB 등)

JSON 형식으로 응답하세요:
```json
{{
  "meta": {{
    "company_name": "",
    "fiscal_period": "",
    "auditor": "",
    "audit_opinion": "",
    "accounting_standard": ""
  }},
  "profile": {{
    "established": "",
    "headquarters": "",
    "main_business": "",
    "ceo": "",
    "major_shareholders": "",
    "capital_stock": "",
    "shares_outstanding": ""
  }},
  "financial_summary": {{
    "total_assets": "",
    "total_liabilities": "",
    "total_equity": "",
    "revenue": "",
    "operating_income": "",
    "net_income": "",
    "operating_cashflow": "",
    "investing_cashflow": "",
    "financing_cashflow": ""
  }},
  "notable_items": [
    "주석에서 발견한 주요 사항 1",
    "주석에서 발견한 주요 사항 2"
  ]
}}
```"""


def get_step2_prompt(step1_result, report_text, company_name):
    """Step 2: 중요 내용 1차 정리"""
    return f"""## 분석 대상
회사명: {company_name}

## Step 1 리서치 결과
{step1_result}

## 보고서 전문 (참조용)
{report_text}

## 지시사항: Step 2 — 중요 내용 1차 정리

Step 1에서 파악한 정보를 바탕으로 의사결정에 영향을 줄 수 있는 신호를 추출하세요.

### 분석 프레임워크

#### 2.1 손익 분석 — 변곡점 식별
- 매출 성장률 계산 (50% 초과 시 변곡점 가능성)
- 매출총이익률 변화 (±5%p 이상이면 사업 구조 변화)
- 영업이익 흑자/적자 전환 여부

#### 2.2 재무상태 분석 — 구조 비율
- 부채비율 (부채/자본)
- 유동비율 (유동자산/유동부채)
- 선수금/매출 비율 (매출 가시성)
- 재고/매출 비율 (운전자본 회전)
- 결손금/자본금 비율 (자본 잠식 정도)

#### 2.3 현금흐름 분석 — 이익의 질
- 현금전환비율 = 영업현금흐름 / 당기순이익
  (1.0이상: 양호, 0~0.5: 운전자본 압박, 음수: 주의)

#### 2.4 특수관계자 거래 — 의존도
- 주거래처 매출/전체 매출 = 단일 거래처 의존도

#### 2.5 자본 구조 분석
- RCPS·CB 발행 이력, 결손금 vs 자본잉여금

#### 2.6 우발채무·보증
- 대표이사 개인보증 / 자본총계

JSON 형식으로 응답:
```json
{{
  "income_analysis": {{
    "revenue_current": "",
    "revenue_previous": "",
    "revenue_growth_rate": "",
    "gross_margin_current": "",
    "gross_margin_previous": "",
    "operating_income_current": "",
    "operating_income_previous": "",
    "profit_turnaround": "",
    "key_message": ""
  }},
  "balance_sheet_analysis": {{
    "debt_ratio": "",
    "current_ratio": "",
    "advance_received_ratio": "",
    "inventory_ratio": "",
    "deficit_ratio": "",
    "key_message": ""
  }},
  "cashflow_analysis": {{
    "cash_conversion_ratio": "",
    "operating_cf": "",
    "net_income": "",
    "working_capital_change": "",
    "key_message": ""
  }},
  "related_party": {{
    "major_customer": "",
    "dependency_ratio": "",
    "key_message": ""
  }},
  "capital_structure": {{
    "rcps_cb_history": "",
    "key_message": ""
  }},
  "contingent_liabilities": {{
    "ceo_guarantee": "",
    "guarantee_to_equity_ratio": "",
    "key_message": ""
  }},
  "key_risks": [
    "리스크 1",
    "리스크 2",
    "리스크 3"
  ]
}}
```"""


def get_step3_prompt(step2_result, report_text, company_name):
    """Step 3: 놓친 부분 체크 (재검토)"""
    return f"""## 분석 대상
회사명: {company_name}

## Step 2 (1차 정리) 결과
{step2_result}

## 보고서 전문 (재검토용)
{report_text}

## 지시사항: Step 3 — 놓친 부분 체크 (재검토)

1차 정리에서 간과한 항목을 구조적으로 점검하세요. 보통 1차에서 30~40%의 정보를 놓칩니다.

### 재검토 체크리스트

#### 3.1 현금흐름표 디테일
- 영업현금흐름과 당기순이익의 차이 → 이익의 질
- 운전자본 변동 항목별 금액
- 투자활동의 CAPEX 종류별 분해
- 재무활동 0인지 여부
- 비현금 거래

#### 3.2 주석 깊이 점검
- 충당부채 신설 또는 급증
- 재고자산 평가충당금 변동
- 금융부채 만기 분석
- 외화자산 종류 변화
- 보험가입 종류 변화
- 연구개발비 자본화 vs 비용화

#### 3.3 인력·운영 신호
- 총 인건비 증가율
- R&D 인건비 증가율
- 임차료 증가율
- 퇴직급여 증가율

#### 3.4 자본 구조 디테일
- RCPS 차수별 발행가·발행시기
- CB 만기 도래 시점
- 전환가 조정조건(refixing) 유무

#### 3.5 산업 맥락 매칭
- 업종 특수성 반영 여부
- 정부 R&D 보조금 의존도
- 특허·무형자산

#### 3.6 누락하기 쉬운 항목
- 임차보증금 변동 (사업장 확장)
- 사용 제한된 예금
- 대표이사·임원 보증 제공 내역

JSON 형식으로 응답:
```json
{{
  "missed_items": [
    {{
      "category": "카테고리 (예: 현금흐름, 주석, 인력, 자본 등)",
      "finding": "발견 내용",
      "significance": "중요도 (high/medium/low)",
      "signal": "bull/watch/risk"
    }}
  ],
  "corrections_to_step2": [
    "Step 2 수정/보완 사항 1",
    "Step 2 수정/보완 사항 2"
  ],
  "additional_risks": [
    "추가 리스크 1"
  ],
  "additional_positives": [
    "추가 긍정 요소 1"
  ]
}}
```"""


def get_step4_prompt(step1_result, step2_result, step3_result, company_name):
    """Step 4: 중요 내용 최종 정리"""
    return f"""## 분석 대상
회사명: {company_name}

## Step 1 리서치 결과
{step1_result}

## Step 2 (1차 정리) 결과
{step2_result}

## Step 3 (재검토) 결과
{step3_result}

## 지시사항: Step 4 — 최종 분석 보고서 작성

Step 1~3의 결과를 통합하여 최종 분석 보고서를 구성하세요.
이 결과물이 docx 리포트의 기초 데이터가 됩니다.

### 보고서 구조 (10개 섹션)

JSON 형식으로 응답:
```json
{{
  "executive_summary": "2~3문장 핵심 결론",

  "section_1_company_overview": {{
    "basic_info_table": [
      {{"항목": "회사명", "내용": ""}},
      {{"항목": "설립일", "내용": ""}},
      {{"항목": "대표이사", "내용": ""}},
      {{"항목": "주요사업", "내용": ""}},
      {{"항목": "감사인/의견", "내용": ""}},
      {{"항목": "회계기준", "내용": ""}},
      {{"항목": "자본금", "내용": ""}},
      {{"항목": "발행주식수", "내용": ""}}
    ],
    "business_identity": "사업 정체성 설명"
  }},

  "section_2_income_analysis": {{
    "key_metrics_table": [
      {{"지표": "매출액", "당기": "", "전기": "", "증감률": ""}},
      {{"지표": "매출총이익", "당기": "", "전기": "", "증감률": ""}},
      {{"지표": "영업이익", "당기": "", "전기": "", "증감률": ""}},
      {{"지표": "당기순이익", "당기": "", "전기": "", "증감률": ""}}
    ],
    "analysis_text": "손익 분석 본문 (변곡점 식별, 이익 구조 변화 등)"
  }},

  "section_3_balance_sheet": {{
    "summary_table": [
      {{"항목": "자산총계", "당기": "", "전기": "", "증감": ""}},
      {{"항목": "부채총계", "당기": "", "전기": "", "증감": ""}},
      {{"항목": "자본총계", "당기": "", "전기": "", "증감": ""}}
    ],
    "key_ratios": [
      {{"비율": "부채비율", "값": "", "평가": ""}},
      {{"비율": "유동비율", "값": "", "평가": ""}}
    ],
    "analysis_text": "재무상태 분석 본문"
  }},

  "section_4_key_risks": {{
    "risks": [
      {{
        "title": "리스크 제목",
        "description": "상세 설명",
        "severity": "high/medium/low"
      }}
    ]
  }},

  "section_5_shareholder": {{
    "cap_table": [
      {{"주주명": "", "지분율": "", "비고": ""}}
    ],
    "ipo_stage": "IPO 단계 진단"
  }},

  "section_6_cashflow": {{
    "summary_table": [
      {{"활동": "영업활동", "금액": "", "전기": ""}},
      {{"활동": "투자활동", "금액": "", "전기": ""}},
      {{"활동": "재무활동", "금액": "", "전기": ""}}
    ],
    "cash_conversion_ratio": "",
    "quality_of_earnings": "이익의 질 진단"
  }},

  "section_7_contingent": {{
    "guarantees": [
      {{"구분": "", "금액": "", "비고": ""}}
    ],
    "upcoming_events": "차기 자금 이벤트",
    "analysis_text": "자금 부담 분석"
  }},

  "section_8_operational_signals": {{
    "signals": [
      {{
        "category": "인력/R&D/임차료/보험/외화/정부보조금",
        "finding": "발견 내용",
        "implication": "시사점"
      }}
    ]
  }},

  "section_9_diagnosis": {{
    "bull_case": [
      "긍정 요소 1",
      "긍정 요소 2"
    ],
    "watch_list": [
      "주의 요소 1"
    ],
    "risk_factors": [
      "위험 요소 1"
    ],
    "one_liner": "한 줄 요약",
    "industry_context": "산업 맥락"
  }},

  "section_10_limitations": [
    "분석 한계 1",
    "추가 검토 권장 항목 1"
  ]
}}
```

모든 금액은 실제 수치를 기재하세요 (억원 단위 권장).
빈 값이 없도록 보고서에서 확인된 정보를 최대한 채워 넣으세요.
확인되지 않는 항목은 "확인 불가" 또는 "해당 없음"으로 표시하세요."""


# ============================================================
# Claude API 호출
# ============================================================
def call_claude(client, messages, max_tokens, step_name):
    """Claude API 호출 (에러 핸들링 포함)"""
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=messages,
        )

        text = response.content[0].text

        # 토큰 사용량 로깅
        usage = response.usage
        print(f"    [{step_name}] input={usage.input_tokens:,} output={usage.output_tokens:,}")

        return text

    except Exception as e:
        print(f"    [{step_name}] API 에러: {e}")
        return None


def extract_json_from_response(text):
    """응답에서 JSON 블록 추출"""
    if not text:
        return None

    # ```json ... ``` 블록 추출
    import re
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 전체가 JSON인 경우
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # { ... } 블록 추출 시도
    brace_match = re.search(r'\{.*\}', text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


# ============================================================
# 4단계 분석 실행
# ============================================================
def analyze_report(client, report_data):
    """
    4단계 분석 프로세스 실행.

    Args:
        client: anthropic.Anthropic 클라이언트
        report_data: dart_report_fetcher의 캐시 데이터

    Returns:
        dict: 분석 결과 (step1~step4 + final_report)
    """
    ticker = report_data['ticker']
    name = report_data['name']
    year = report_data['year']
    quarter = report_data['quarter']

    print(f"\n  분석 시작: {name}({ticker}) {year} {quarter}")
    print(f"    보고서 길이: {report_data['text_length']:,}자")

    # 보고서 텍스트 (길이 제한)
    report_text = report_data['plain_text']
    if len(report_text) > MAX_INPUT_CHARS:
        print(f"    [WARN] 텍스트 길이 제한 적용: {len(report_text):,} → {MAX_INPUT_CHARS:,}자")
        report_text = report_text[:MAX_INPUT_CHARS]

    analysis = {
        'ticker': ticker,
        'name': name,
        'year': year,
        'quarter': quarter,
        'model': CLAUDE_MODEL,
        'analyzed_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    # ─── Step 1: 파일 리서치 ───
    print(f"    Step 1/4: 파일 리서치...")
    step1_raw = call_claude(
        client,
        messages=[{"role": "user", "content": get_step1_prompt(report_text, name)}],
        max_tokens=MAX_TOKENS_STEP1,
        step_name="Step1"
    )
    if not step1_raw:
        print(f"    [FAIL] Step 1 실패")
        return None

    analysis['step1_raw'] = step1_raw
    analysis['step1_json'] = extract_json_from_response(step1_raw)
    time.sleep(SLEEP_BETWEEN_CALLS)

    # ─── Step 2: 1차 정리 ───
    print(f"    Step 2/4: 중요 내용 1차 정리...")
    step2_raw = call_claude(
        client,
        messages=[{"role": "user", "content": get_step2_prompt(step1_raw, report_text, name)}],
        max_tokens=MAX_TOKENS_STEP2,
        step_name="Step2"
    )
    if not step2_raw:
        print(f"    [FAIL] Step 2 실패")
        return None

    analysis['step2_raw'] = step2_raw
    analysis['step2_json'] = extract_json_from_response(step2_raw)
    time.sleep(SLEEP_BETWEEN_CALLS)

    # ─── Step 3: 놓친 부분 체크 ───
    print(f"    Step 3/4: 놓친 부분 체크...")
    step3_raw = call_claude(
        client,
        messages=[{"role": "user", "content": get_step3_prompt(step2_raw, report_text, name)}],
        max_tokens=MAX_TOKENS_STEP3,
        step_name="Step3"
    )
    if not step3_raw:
        print(f"    [FAIL] Step 3 실패")
        return None

    analysis['step3_raw'] = step3_raw
    analysis['step3_json'] = extract_json_from_response(step3_raw)
    time.sleep(SLEEP_BETWEEN_CALLS)

    # ─── Step 4: 최종 정리 ───
    print(f"    Step 4/4: 최종 정리...")
    step4_raw = call_claude(
        client,
        messages=[{"role": "user", "content": get_step4_prompt(step1_raw, step2_raw, step3_raw, name)}],
        max_tokens=MAX_TOKENS_STEP4,
        step_name="Step4"
    )
    if not step4_raw:
        print(f"    [FAIL] Step 4 실패")
        return None

    analysis['step4_raw'] = step4_raw
    analysis['step4_json'] = extract_json_from_response(step4_raw)
    analysis['final_report'] = analysis['step4_json']

    print(f"    ✓ 분석 완료: {name}")
    return analysis


# ============================================================
# 캐시 관리
# ============================================================
def get_analysis_path(ticker, year, quarter):
    return os.path.join(CACHE_DIR, f'{ticker}_{year}_{quarter}_analysis.json')


def is_analyzed(ticker, year, quarter):
    return os.path.exists(get_analysis_path(ticker, year, quarter))


def save_analysis(analysis, ticker, year, quarter):
    path = get_analysis_path(ticker, year, quarter)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)


def load_analysis(ticker, year, quarter):
    path = get_analysis_path(ticker, year, quarter)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================
# 메인 분석 루프
# ============================================================
def run_analysis(year, quarter, tickers=None, sector=None, force=False):
    """
    분석 메인 함수.
    """
    print("=" * 60)
    print(f"PHASE5 Report - Step 2: Claude API 분석")
    print(f"  대상: {year}년 {quarter}")
    print(f"  모델: {CLAUDE_MODEL}")
    print(f"  실행: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # API 키 확인
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        print("[ERROR] ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        print("  .env 파일에 ANTHROPIC_API_KEY=sk-ant-... 를 추가하세요.")
        sys.exit(1)

    # Anthropic 클라이언트 초기화
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        print(f"  Anthropic 클라이언트 초기화 완료")
    except ImportError:
        print("[ERROR] anthropic 패키지가 설치되지 않았습니다.")
        print("  pip install anthropic")
        sys.exit(1)

    # 섹터 매핑
    sector_map = {}
    csv_path = os.path.join(PHASE0_DIR, 'kospi_kosdaq_sector_classification.csv')
    if os.path.exists(csv_path):
        df_sec = pd.read_csv(csv_path)
        df_sec['ticker'] = df_sec['ticker'].astype(str).str.strip().str.zfill(6)
        sector_map = dict(zip(df_sec['ticker'], df_sec['tier1']))

    # Step 1 캐시에서 수집 완료된 보고서 찾기
    report_caches = glob.glob(os.path.join(CACHE_DIR, f'*_{year}_{quarter}.pkl'))

    if not report_caches:
        print(f"[ERROR] {year}년 {quarter} 보고서 캐시가 없습니다.")
        print("  → dart_report_fetcher.py를 먼저 실행하세요.")
        sys.exit(1)

    # 대상 필터링
    targets = []
    for cache_path in report_caches:
        fname = os.path.basename(cache_path)
        tk = fname.split('_')[0]

        if tickers and tk not in tickers:
            continue
        if sector and sector_map.get(tk) != sector:
            continue

        targets.append((tk, cache_path))

    print(f"  분석 대상: {len(targets)}종목")
    if sector:
        print(f"  섹터 필터: {sector}")

    success = 0
    skip = 0
    fail = 0
    total_cost_input = 0
    total_cost_output = 0

    for i, (tk, cache_path) in enumerate(targets):
        # 이미 분석 완료?
        if not force and is_analyzed(tk, year, quarter):
            skip += 1
            continue

        # 보고서 로드
        with open(cache_path, 'rb') as f:
            report_data = pickle.load(f)

        # 분석 실행
        analysis = analyze_report(client, report_data)

        if analysis:
            save_analysis(analysis, tk, year, quarter)
            success += 1
        else:
            fail += 1

        if (i + 1) % 10 == 0:
            print(f"\n  --- [{i+1}/{len(targets)}] 성공:{success} 스킵:{skip} 실패:{fail} ---")

    # 로그
    log_path = os.path.join(LOG_DIR, f'analyze_{year}_{quarter}_{datetime.date.today().strftime("%Y%m%d")}.log')
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"PHASE5 Report Analysis Log\n")
        f.write(f"Date: {datetime.datetime.now()}\n")
        f.write(f"Model: {CLAUDE_MODEL}\n")
        f.write(f"Success: {success}, Skip: {skip}, Fail: {fail}\n")

    print(f"\n{'=' * 60}")
    print(f"분석 완료: 성공 {success}, 스킵(기분석) {skip}, 실패 {fail}")
    print("=" * 60)

    return success, skip, fail


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='PHASE5 Claude API 보고서 분석')
    parser.add_argument('--year', type=int, default=datetime.date.today().year - 1)
    parser.add_argument('--quarter', type=str, default='4Q')
    parser.add_argument('--ticker', type=str, default=None,
                        help='특정 종목 (콤마 구분)')
    parser.add_argument('--sector', type=str, default=None)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    tickers = None
    if args.ticker:
        tickers = [t.strip().zfill(6) for t in args.ticker.split(',')]

    run_analysis(
        year=args.year,
        quarter=args.quarter.upper(),
        tickers=tickers,
        sector=args.sector,
        force=args.force,
    )


if __name__ == '__main__':
    main()
