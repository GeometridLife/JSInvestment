"""
PHASE2 Fundamental — 일일 실행 러너
================================================================

3-step 순차 실행:
  Step 1: EDGAR 재무제표 수집      (20260502_edgar_collector.py)
  Step 2: yfinance 데이터 수집     (20260502_yf_collector.py)
  Step 3: 펀더멘탈 스코어링         (20260502_fundamental_scoring.py)

실행:
    cd C:\\Users\\limit\\Desktop\\JS\\Global\\PHASE2_fundamental
    python run_daily.py

옵션:
    --skip-edgar      Step 1 스킵 (캐시 재사용)
    --skip-yf         Step 2 스킵
    --only-edgar      Step 1만
    --only-yf         Step 2만
    --only-scoring    Step 3만
    --skip-collect    Step 1+2 모두 스킵 → Step 3만 (= --only-scoring)
    --rebuild         수집 단계에서 캐시 무시
    --skip-charts     스코어링 차트 스킵
    --skip-xverify    EDGAR-yfinance cross-check 스킵

전형적 사용:
    # 첫 실행 (모든 단계)
    python run_daily.py

    # EDGAR는 이미 수집됨, yfinance + scoring만
    python run_daily.py --skip-edgar

    # 스코어링 로직만 수정한 경우
    python run_daily.py --only-scoring

    # 강제 전체 재수집
    python run_daily.py --rebuild
"""
import sys
import time
import argparse
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

STEPS = [
    ('edgar',   'Step 1: EDGAR 재무제표 수집',   '20260502_edgar_collector.py'),
    ('yf',      'Step 2: yfinance 데이터 수집',  '20260502_yf_collector.py'),
    ('scoring', 'Step 3: 펀더멘탈 스코어링',     '20260502_fundamental_scoring.py'),
]


def run_step(name: str, title: str, script: str, extra_args: list) -> bool:
    """한 단계 실행. 반환: 성공 여부"""
    script_path = SCRIPT_DIR / script
    if not script_path.exists():
        print(f"\n!!! 스크립트 없음: {script_path}")
        return False

    print(f"\n{'=' * 72}")
    print(f"  {title}")
    print(f"  $ python {script} {' '.join(extra_args)}")
    print('=' * 72)

    start = time.time()
    cmd = [sys.executable, str(script_path)] + extra_args
    try:
        result = subprocess.run(cmd, cwd=SCRIPT_DIR)
    except KeyboardInterrupt:
        print(f"\n!!! 사용자 중단 — {title}")
        return False
    except Exception as e:
        print(f"\n!!! 실행 에러: {type(e).__name__}: {e}")
        return False

    elapsed = time.time() - start
    if result.returncode != 0:
        print(f"\n!!! {title} 실패 (return code {result.returncode}, {elapsed/60:.1f}분)")
        return False

    print(f"\n>>> {title} 완료 ({elapsed/60:.1f}분)")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-edgar',   action='store_true')
    parser.add_argument('--skip-yf',      action='store_true')
    parser.add_argument('--only-edgar',   action='store_true')
    parser.add_argument('--only-yf',      action='store_true')
    parser.add_argument('--only-scoring', action='store_true')
    parser.add_argument('--skip-collect', action='store_true',
                        help='Step 1+2 모두 스킵 (= --only-scoring)')
    parser.add_argument('--rebuild',      action='store_true')
    parser.add_argument('--skip-charts',  action='store_true')
    parser.add_argument('--skip-xverify', action='store_true')
    args = parser.parse_args()

    # 어떤 단계 실행할지 결정
    skip = {'edgar': False, 'yf': False, 'scoring': False}
    if args.only_edgar:    skip = {'edgar': False, 'yf': True,  'scoring': True}
    elif args.only_yf:     skip = {'edgar': True,  'yf': False, 'scoring': True}
    elif args.only_scoring or args.skip_collect:
        skip = {'edgar': True, 'yf': True, 'scoring': False}
    else:
        skip['edgar'] = args.skip_edgar
        skip['yf']    = args.skip_yf

    # 단계별 추가 인자
    extra_args = {'edgar': [], 'yf': [], 'scoring': []}
    if args.rebuild:
        extra_args['edgar'].append('--rebuild')
        extra_args['yf'].append('--rebuild')
    if args.skip_charts:
        extra_args['scoring'].append('--skip-charts')
    if args.skip_xverify:
        extra_args['scoring'].append('--skip-xverify')

    print("=" * 72)
    print("PHASE2 Global Fundamental — Daily Runner")
    print("=" * 72)
    print("실행할 단계:")
    for name, title, _ in STEPS:
        flag = '스킵' if skip[name] else '실행'
        marker = '○' if skip[name] else '●'
        print(f"  {marker} [{flag}] {title}")
    if extra_args.get('edgar') or extra_args.get('yf') or extra_args.get('scoring'):
        print("추가 인자:")
        for k, v in extra_args.items():
            if v:
                print(f"  - {k}: {' '.join(v)}")

    overall_start = time.time()
    failures = []

    for name, title, script in STEPS:
        if skip[name]:
            print(f"\n>>> [스킵] {title}")
            continue
        ok = run_step(name, title, script, extra_args[name])
        if not ok:
            failures.append(title)
            # EDGAR/yf 실패해도 scoring은 시도 안 함 (데이터 없으니)
            print(f"\n!!! 이후 단계 중단 (의존성 깨짐)")
            break

    total = time.time() - overall_start
    print("\n" + "=" * 72)
    print(f"전체 소요: {total/60:.1f}분")
    if failures:
        print(f"실패한 단계: {failures}")
        sys.exit(1)
    print("모든 단계 완료")
    print("=" * 72)


if __name__ == '__main__':
    main()
