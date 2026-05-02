"""
PHASE1 Global Momentum - 일일 실행 러너
Description:
    매일 실행하면 Step 1→2→3를 순차 실행합니다.
    - Step 1: 데이터 증분 업데이트 (신규 데이터만 추가, ~1분)
    - Step 2: 백테스트 재실행 (~수분)
    - Step 3: 랭킹 재산출 (~1분)

Usage:
    python run_daily.py
    python run_daily.py --skip-collect
    python run_daily.py --only-collect
"""

import os
import sys
import time
import datetime
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable

STEPS = [
    ('Step 1: 데이터 수집 (증분)', '20260501_data_collector.py'),
    ('Step 2: 백테스트', '20260501_momentum_backtest.py'),
    ('Step 3: 랭킹', '20260501_momentum_ranking.py'),
]


def run_step(name, script_file):
    """개별 스텝 실행"""
    script_path = os.path.join(SCRIPT_DIR, script_file)
    if not os.path.exists(script_path):
        print(f"  [ERROR] 스크립트 없음: {script_file}")
        return False

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"  시작: {datetime.datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")

    start = time.time()
    result = subprocess.run(
        [PYTHON, script_path],
        cwd=SCRIPT_DIR,
    )
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
    print(f"PHASE1 Global Momentum - 일일 실행")
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

    # 최종 요약
    print("\n" + "=" * 60)
    print(f"일일 실행 완료 (총 {total_elapsed:.0f}초)")
    print("=" * 60)
    for name, status in results.items():
        icon = '✓' if status == 'success' else ('→' if status == 'skipped' else '✗')
        print(f"  {icon} {name}: {status}")
    print("=" * 60)


if __name__ == '__main__':
    main()
