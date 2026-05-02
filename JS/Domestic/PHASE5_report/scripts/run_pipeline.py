"""
PHASE5 Report - 파이프라인 오케스트레이터
Date: 2026-05-01
Description:
    - Step 1(DART 수집) → Step 2(Claude 분석) → Step 3(docx 생성) 순차 실행
    - 진행률 표시, 에러 관리
    - 특정 종목/섹터/분기 선택 실행 가능

Usage:
    C:/Python311/python.exe scripts/run_pipeline.py
    C:/Python311/python.exe scripts/run_pipeline.py --year 2025 --quarter 4Q
    C:/Python311/python.exe scripts/run_pipeline.py --ticker 005930
    C:/Python311/python.exe scripts/run_pipeline.py --sector 반도체
    C:/Python311/python.exe scripts/run_pipeline.py --step 2       # Step 2만 실행
    C:/Python311/python.exe scripts/run_pipeline.py --step 3       # Step 3만 실행
"""

import os
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env')
load_dotenv(_env_path)

import sys
import time
import datetime
import argparse
import subprocess

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Python/Node 경로 (Windows)
PYTHON_EXE = r'C:\Python311\python.exe'
NODE_EXE = 'node'  # PATH에 있다고 가정


# ============================================================
# 스텝별 실행
# ============================================================
def run_step1(year, quarter, ticker=None, sector=None, force=False):
    """Step 1: DART 보고서 수집"""
    print("\n" + "=" * 60)
    print("  STEP 1: DART 보고서 수집")
    print("=" * 60)

    cmd = [
        PYTHON_EXE,
        os.path.join(SCRIPT_DIR, 'dart_report_fetcher.py'),
        '--year', str(year),
        '--quarter', quarter,
    ]
    if ticker:
        cmd.extend(['--ticker', ticker])
    if sector:
        cmd.extend(['--sector', sector])
    if force:
        cmd.append('--force')

    result = subprocess.run(cmd, cwd=BASE_DIR)
    return result.returncode == 0


def run_step2(year, quarter, ticker=None, sector=None, force=False):
    """Step 2: Claude API 분석"""
    print("\n" + "=" * 60)
    print("  STEP 2: Claude API 분석")
    print("=" * 60)

    cmd = [
        PYTHON_EXE,
        os.path.join(SCRIPT_DIR, 'report_analyzer.py'),
        '--year', str(year),
        '--quarter', quarter,
    ]
    if ticker:
        cmd.extend(['--ticker', ticker])
    if sector:
        cmd.extend(['--sector', sector])
    if force:
        cmd.append('--force')

    result = subprocess.run(cmd, cwd=BASE_DIR)
    return result.returncode == 0


def run_step3(year, quarter, sector=None):
    """Step 3: docx 리포트 생성"""
    print("\n" + "=" * 60)
    print("  STEP 3: docx 리포트 생성")
    print("=" * 60)

    cmd = [
        NODE_EXE,
        os.path.join(SCRIPT_DIR, 'report_generator.js'),
        '--year', str(year),
        '--quarter', quarter,
    ]
    if sector:
        cmd.extend(['--sector', sector])

    result = subprocess.run(cmd, cwd=BASE_DIR)
    return result.returncode == 0


# ============================================================
# 메인
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='PHASE5 Report Pipeline')
    parser.add_argument('--year', type=int, default=datetime.date.today().year - 1,
                        help='수집 연도 (기본: 전년도)')
    parser.add_argument('--quarter', type=str, default='4Q',
                        help='분기 (1Q/2Q/3Q/4Q, 기본: 4Q)')
    parser.add_argument('--ticker', type=str, default=None,
                        help='특정 종목 코드 (콤마 구분)')
    parser.add_argument('--sector', type=str, default=None,
                        help='특정 섹터만 처리')
    parser.add_argument('--step', type=int, default=None,
                        help='특정 스텝만 실행 (1/2/3)')
    parser.add_argument('--force', action='store_true',
                        help='캐시 무시 재처리')
    args = parser.parse_args()

    quarter = args.quarter.upper()

    print("=" * 60)
    print(f"PHASE5 Report Pipeline")
    print(f"  대상: {args.year}년 {quarter}")
    if args.ticker:
        print(f"  종목: {args.ticker}")
    if args.sector:
        print(f"  섹터: {args.sector}")
    if args.step:
        print(f"  스텝: Step {args.step}만 실행")
    print(f"  실행: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    start_time = time.time()
    results = {}

    # Step 1
    if args.step is None or args.step == 1:
        ok = run_step1(args.year, quarter, args.ticker, args.sector, args.force)
        results['step1'] = 'OK' if ok else 'FAIL'
        if not ok and args.step is None:
            print("\n[WARN] Step 1 실패. Step 2, 3 건너뜀.")
            # 캐시가 있으면 계속 진행 가능
            pass

    # Step 2
    if args.step is None or args.step == 2:
        ok = run_step2(args.year, quarter, args.ticker, args.sector, args.force)
        results['step2'] = 'OK' if ok else 'FAIL'
        if not ok and args.step is None:
            print("\n[WARN] Step 2 실패. Step 3 건너뜀.")

    # Step 3
    if args.step is None or args.step == 3:
        ok = run_step3(args.year, quarter, args.sector)
        results['step3'] = 'OK' if ok else 'FAIL'

    elapsed = time.time() - start_time

    # 결과 요약
    print(f"\n{'=' * 60}")
    print(f"파이프라인 완료 ({elapsed:.0f}초)")
    for step, status in results.items():
        emoji = 'OK' if status == 'OK' else 'FAIL'
        print(f"  {step}: {emoji}")
    print("=" * 60)

    # 결과 폴더 안내
    result_dir = os.path.join(BASE_DIR, 'result')
    if os.path.exists(result_dir):
        import glob
        docx_files = glob.glob(os.path.join(result_dir, '**', '*.docx'), recursive=True)
        if docx_files:
            print(f"\n  생성된 리포트: {len(docx_files)}개")
            for f in docx_files[:5]:
                rel = os.path.relpath(f, result_dir)
                print(f"    result/{rel}")
            if len(docx_files) > 5:
                print(f"    ... 외 {len(docx_files) - 5}개")


if __name__ == '__main__':
    main()
