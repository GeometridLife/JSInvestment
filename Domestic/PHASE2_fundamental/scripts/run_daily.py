"""
PHASE2 Fundamental - 일일 실행 러너
Description:
    Step 1: pykrx 데이터 수집 (기본 밸류에이션)
    Step 2: 펀더멘탈 스코어링 + 차트

Usage:
    C:/Python311/python.exe scripts/run_daily.py
    C:/Python311/python.exe scripts/run_daily.py --skip-collect
    C:/Python311/python.exe scripts/run_daily.py --only-collect
"""

import os
import sys
import time
import datetime
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable

STEPS = [
    ('Step 1: 데이터 수집 (pykrx)', 'data_collector.py'),
    ('Step 2: 펀더멘탈 스코어링', 'fundamental_scoring.py'),
]


def run_step(name, script_file):
    script_path = os.path.join(SCRIPT_DIR, script_file)
    if not os.path.exists(script_path):
        print(f"  [ERROR] 스크립트 없음: {script_file}")
        return False

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"  시작: {datetime.datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")

    start = time.time()
    result = subprocess.run([PYTHON, script_path], cwd=SCRIPT_DIR)
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"\n  ✓ {name} 완료 ({elapsed:.0f}초)")
        return True
    else:
        print(f"\n  ✗ {name} 실패 (exit code: {result.returncode})")
        return False


def main():
    args = sys.argv[1:]
    skip_collect = '--skip-collect' in args
    only_collect = '--only-collect' in args

    print("=" * 60)
    print(f"PHASE2 Fundamental - 일일 실행")
    print(f"날짜: {datetime.date.today().strftime('%Y-%m-%d')}")
    print(f"시작: {datetime.datetime.now().strftime('%H:%M:%S')}")
    if skip_collect:
        print("  → 데이터 수집 스킵")
    if only_collect:
        print("  → 데이터 수집만 실행")
    print("=" * 60)

    total_start = time.time()
    results = {}

    for name, script in STEPS:
        if skip_collect and 'data_collector' in script:
            print(f"\n  [SKIP] {name}")
            results[name] = 'skipped'
            continue
        if only_collect and 'data_collector' not in script:
            results[name] = 'skipped'
            continue

        ok = run_step(name, script)
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
