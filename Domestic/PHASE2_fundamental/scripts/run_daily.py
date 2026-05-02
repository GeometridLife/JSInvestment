"""
PHASE2 Fundamental - 일일 실행 러너 (v2)
Date: 2026-04-30
Description:
    Step 1: pykrx + DART 데이터 수집
    Step 2: FnGuide 컨센서스 수집
    Step 3: 지주사 NAV 계산
    Step 4: 펀더멘탈 스코어링 + 차트

Usage:
    C:/Python311/python.exe scripts/run_daily.py
    C:/Python311/python.exe scripts/run_daily.py --skip-dart
    C:/Python311/python.exe scripts/run_daily.py --skip-collect
    C:/Python311/python.exe scripts/run_daily.py --only-collect
    C:/Python311/python.exe scripts/run_daily.py --only-score
"""

import os
import sys
import time
import datetime
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable

# 수집 단계 (Step 1~3)
COLLECT_STEPS = [
    ('Step 1: pykrx + DART 데이터 수집', 'data_collector.py'),
    ('Step 2: FnGuide 컨센서스 수집',    'consensus_collector.py'),
    ('Step 3: 지주사 NAV 계산',           'nav_calculator.py'),
]

# 스코어링 단계 (Step 4)
SCORE_STEPS = [
    ('Step 4: 펀더멘탈 스코어링',         'fundamental_scoring.py'),
]

ALL_STEPS = COLLECT_STEPS + SCORE_STEPS


def run_step(name, script_file, extra_args=None):
    script_path = os.path.join(SCRIPT_DIR, script_file)
    if not os.path.exists(script_path):
        print(f"  [ERROR] 스크립트 없음: {script_file}")
        return False

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"  시작: {datetime.datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")

    cmd = [PYTHON, script_path]
    if extra_args:
        cmd.extend(extra_args)

    start = time.time()
    result = subprocess.run(cmd, cwd=SCRIPT_DIR)
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"\n  ✓ {name} 완료 ({elapsed:.0f}초)")
        return True
    else:
        print(f"\n  ✗ {name} 실패 (exit code: {result.returncode})")
        return False


def main():
    args = sys.argv[1:]
    skip_dart = '--skip-dart' in args
    skip_collect = '--skip-collect' in args
    only_collect = '--only-collect' in args
    only_score = '--only-score' in args

    print("=" * 60)
    print(f"PHASE2 Fundamental - 일일 실행 (v2)")
    print(f"날짜: {datetime.date.today().strftime('%Y-%m-%d')}")
    print(f"시작: {datetime.datetime.now().strftime('%H:%M:%S')}")
    if skip_dart:
        print("  → DART 수집 스킵 (pykrx만)")
    if skip_collect:
        print("  → 데이터 수집 전체 스킵 (스코어링만)")
    if only_collect:
        print("  → 데이터 수집만 실행")
    if only_score:
        print("  → 스코어링만 실행")
    print("=" * 60)

    # 실행할 단계 결정
    if only_score:
        steps_to_run = SCORE_STEPS
    elif only_collect:
        steps_to_run = COLLECT_STEPS
    elif skip_collect:
        steps_to_run = SCORE_STEPS
    else:
        steps_to_run = ALL_STEPS

    total_start = time.time()
    results = {}

    for name, script in steps_to_run:
        # --skip-dart 옵션: data_collector에 전달
        extra_args = None
        if skip_dart and 'data_collector' in script:
            extra_args = ['--skip-dart']

        ok = run_step(name, script, extra_args)
        results[name] = 'success' if ok else 'failed'

        if not ok:
            print(f"\n[ABORT] {name} 실패로 이후 단계 중단")
            break

    total_elapsed = time.time() - total_start

    print(f"\n{'=' * 60}")
    print(f"일일 실행 완료 (총 {total_elapsed:.0f}초)")
    print("=" * 60)
    for name, status in results.items():
        icon = '✓' if status == 'success' else ('→' if status == 'skipped' else '✗')
        print(f"  {icon} {name}: {status}")
    print("=" * 60)


if __name__ == '__main__':
    main()
