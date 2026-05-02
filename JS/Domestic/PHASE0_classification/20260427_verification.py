"""
PHASE0: 분류 결과 검증 스크립트
Date: 2026-04-27
Description:
    - 정량적 검증: 종목수, 섹터 밸런스, 미분류 비율
    - 스팟체크: 대표 종목 섹터 확인
    - 미분류 종목 원인 분석 및 자동 수정 제안
"""

import os
import datetime
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TODAY_STR = datetime.date.today().strftime('%Y%m%d')
INPUT_EXCEL = os.path.join(SCRIPT_DIR, f'{TODAY_STR}_classification_master.xlsx')
WICS_CSV = os.path.join(SCRIPT_DIR, 'kospi_kosdaq_sector_classification.csv')
OUTPUT_FIXED = os.path.join(SCRIPT_DIR, f'{TODAY_STR}_classification_master_verified.xlsx')

# ============================================================
# 검증 1: 정량적 체크
# ============================================================
def check_quantitative(df):
    print("=" * 60)
    print("[검증 1] 정량적 체크")
    print("=" * 60)

    results = []

    # 1-1. 총 종목수 범위
    total = len(df)
    ok = 400 <= total <= 1500
    results.append(('총 종목수 (400~1500 정상)', total, ok))

    # 1-2. 미분류 비율 5% 이하
    unmatched = len(df[df['tier1'] == '미분류'])
    ratio = unmatched / total * 100
    ok = ratio <= 5.0
    results.append((f'미분류 비율 (≤5%)', f'{unmatched}건 ({ratio:.1f}%)', ok))

    # 1-3. 18개 섹터 전부 존재 (미분류 제외)
    sectors = df[df['tier1'] != '미분류']['tier1'].nunique()
    ok = sectors == 18
    results.append(('섹터 수 (18개)', sectors, ok))

    # 1-4. 빈 섹터 없는지 (최소 3종목)
    sector_counts = df[df['tier1'] != '미분류'].groupby('tier1').size()
    min_sector = sector_counts.min()
    min_sector_name = sector_counts.idxmin()
    ok = min_sector >= 3
    results.append((f'최소 섹터 종목수 (≥3)', f'{min_sector_name}: {min_sector}개', ok))

    # 1-5. 시총 Top 30이 전부 분류됐는지
    if '시가총액' in df.columns:
        top30 = df.nlargest(30, '시가총액')
        top30_unmatched = top30[top30['tier1'] == '미분류']
        ok = len(top30_unmatched) == 0
        detail = f'{len(top30_unmatched)}건 미분류'
        if len(top30_unmatched) > 0:
            detail += ': ' + ', '.join(top30_unmatched['name'].tolist())
        results.append(('시총 Top30 전부 분류', detail, ok))

    # 결과 출력
    all_pass = True
    for name, value, ok in results:
        status = 'PASS' if ok else 'FAIL'
        if not ok:
            all_pass = False
        print(f"  {'✓' if ok else '✗'} [{status}] {name}: {value}")

    print()
    return all_pass


# ============================================================
# 검증 2: 대표 종목 스팟체크
# ============================================================
def check_spot(df):
    print("=" * 60)
    print("[검증 2] 대표 종목 스팟체크")
    print("=" * 60)

    # {종목명(완전일치): 기대 섹터}
    spot_checks = {
        '삼성전자': '반도체',
        'SK하이닉스': '반도체',
        '현대차': '자동차/부품',
        '기아': '자동차/부품',
        'LG에너지솔루션': '2차전지/배터리',
        '삼성SDI': '2차전지/배터리',
        'NAVER': '인터넷/플랫폼',
        '카카오': '인터넷/플랫폼',
        '삼성바이오로직스': '바이오/제약/헬스케어',
        '셀트리온': '바이오/제약/헬스케어',
        'KB금융': '금융/보험',
        '한화에어로스페이스': '방산/항공우주',
        'HD현대중공업': '기계/산업재',
        'SK텔레콤': '통신',
        'LG디스플레이': '디스플레이',
    }

    all_pass = True
    for name_exact, expected_sector in spot_checks.items():
        # 완전 일치 우선, 없으면 부분 일치 (가장 짧은 이름 = 가장 정확한 매칭)
        matched = df[df['name'].str.strip() == name_exact]
        if len(matched) == 0:
            matched = df[df['name'].str.contains(name_exact, na=False)]
            if len(matched) > 0:
                matched = matched.loc[matched['name'].str.len().idxmin():matched['name'].str.len().idxmin()]
        if len(matched) == 0:
            print(f"  ? [SKIP] {name_exact}: 종목 미발견 (필터링으로 제외됐을 수 있음)")
            continue
        row = matched.iloc[0]
        actual = row['tier1']
        ok = actual == expected_sector
        if not ok:
            all_pass = False
        status = 'PASS' if ok else 'FAIL'
        print(f"  {'✓' if ok else '✗'} [{status}] {row['name']}: {actual} (기대: {expected_sector})")

    print()
    return all_pass


# ============================================================
# 검증 3: 미분류 종목 원인 분석 + 자동 수정
# ============================================================
def analyze_and_fix_unmatched(df):
    print("=" * 60)
    print("[검증 3] 미분류 종목 원인 분석 & 자동 수정")
    print("=" * 60)

    df_unmatched = df[df['tier1'] == '미분류'].copy()
    if len(df_unmatched) == 0:
        print("  미분류 종목 없음!")
        return df

    # WICS 원본 로드
    df_wics = pd.read_csv(WICS_CSV, encoding='utf-8-sig')
    df_wics = df_wics[df_wics['tier1'] != '특수목적법인'].copy()
    wics_names = set(df_wics['name'].astype(str).str.strip().str.replace(r'\s+', '', regex=True))
    wics_name_dict = {}
    for _, row in df_wics.iterrows():
        key = str(row['name']).strip().replace(' ', '')
        wics_name_dict[key] = (row['tier1'], row['tier2'], row['tier3'])

    fixed_count = 0
    df = df.copy()

    for idx in df_unmatched.index:
        name = str(df.at[idx, 'name']).strip()
        ticker = str(df.at[idx, 'ticker']).strip()

        # 수정 시도 1: 종목명 뒤에 붙은 숫자/특수문자 제거
        clean1 = name.replace(' ', '')
        # 수정 시도 2: 약어 변환 (예: 'CJ4우(전환)' → 'CJ')
        clean2 = name.split('(')[0].strip().replace(' ', '')
        # 수정 시도 3: 끝 숫자/우선주 표기 제거
        import re
        clean3 = re.sub(r'[0-9]*[우]?[A-Z]?(\(전환\))?$', '', clean1)

        # 부분 매칭: WICS 이름에 포함되는지
        partial_matches = []
        for wics_name in wics_names:
            # 미분류 이름이 WICS 이름을 포함하거나 그 반대
            if len(clean3) >= 2 and (clean3 in wics_name or wics_name in clean3):
                if abs(len(clean3) - len(wics_name)) <= 3:  # 길이 차이 3자 이내
                    partial_matches.append(wics_name)

        if partial_matches:
            # 가장 유사한 것 선택 (길이 차이가 가장 작은 것)
            best = min(partial_matches, key=lambda x: abs(len(x) - len(clean3)))
            if best in wics_name_dict:
                t1, t2, t3 = wics_name_dict[best]
                df.at[idx, 'tier1'] = t1
                df.at[idx, 'tier2'] = t2
                df.at[idx, 'tier3'] = t3
                df.at[idx, 'match_status'] = 'fuzzy_fixed'
                print(f"  ✓ [FIXED] {ticker} {name} → '{best}' → {t1}/{t2}")
                fixed_count += 1
                continue

        # 매칭 실패 - 수동 분류 제안
        print(f"  ✗ [MANUAL] {ticker} {name} — WICS에서 유사 이름 못 찾음")

    print(f"\n  자동 수정: {fixed_count}건, 수동 필요: {len(df_unmatched) - fixed_count}건")
    return df


# ============================================================
# 수동 분류 테이블 (WICS에 없는 종목용)
# ============================================================
MANUAL_CLASSIFICATION = {
    # ticker: (tier1, tier2, tier3) - 필요 시 여기에 추가
    '005300': ('소비재/유통', '음식료', '음료'),           # 롯데칠성
    '025540': ('IT하드웨어/전자부품', '전자부품', '커넥터'),  # 한국단자
    '069260': ('에너지/화학', '석유화학', '석유화학'),       # TKG휴켐스
    '001820': ('IT하드웨어/전자부품', '전자부품', '수동부품'), # 삼화콘덴서
    '001200': ('금융/보험', '증권', '증권'),               # 유진투자증권
    '344820': ('철강/소재', '유리', '유리'),               # KCC글라스
    '221800': ('금융/보험', '지주', '지주'),               # 지구홀딩스
    '900140': ('금융/보험', '지주', '지주'),               # 엘브이엠씨홀딩스
    '017390': ('에너지/화학', '가스', '도시가스'),          # 서울가스
    '005680': ('IT하드웨어/전자부품', '전자부품', '전자부품'), # 삼영전자
    '000390': ('에너지/화학', '기초화학', '도료'),          # 삼화페인트
    '013580': ('건설/부동산', '건설', '종합건설'),          # 계룡건설
    '307750': ('전력인프라/에너지장비', '전력설비', '전력기기'), # 국전
    '004090': ('에너지/화학', '석유', '정유'),             # 한국석유
    '009070': ('기계/산업재', '운송', '물류'),             # KCTC
    '090470': ('기계/산업재', '로봇/자동화', '로봇'),       # 제이스로보틱스
    '011700': ('기계/산업재', '일반기계', '산업기계'),      # 한신기계
    '005870': ('방산/항공우주', '방산', '방산전자'),        # 휴니드
    '004100': ('철강/소재', '금속가공', '금속가공'),        # 태양금속
    '002200': ('기계/산업재', '포장', '포장재'),           # 한국수출포장
}

# 우선주/전환주 → 보통주 ticker로 매핑
PREFERRED_TO_COMMON = {
    '00104K': '001040',   # CJ4우(전환) → CJ
    '37550L': '375500',   # DL이앤씨2우(전환) → DL이앤씨
}


def apply_manual_classification(df):
    """수동 분류 + 우선주 보통주 상속 적용"""
    print("\n[검증 3-2] 수동 분류 적용")
    fixed = 0

    for idx in df[df['tier1'] == '미분류'].index:
        ticker = str(df.at[idx, 'ticker']).strip()

        # 수동 분류 테이블
        if ticker in MANUAL_CLASSIFICATION:
            t1, t2, t3 = MANUAL_CLASSIFICATION[ticker]
            df.at[idx, 'tier1'] = t1
            df.at[idx, 'tier2'] = t2
            df.at[idx, 'tier3'] = t3
            df.at[idx, 'match_status'] = 'manual'
            print(f"  ✓ {ticker} {df.at[idx, 'name']} → {t1}")
            fixed += 1

        # 우선주 → 보통주 상속
        elif ticker in PREFERRED_TO_COMMON:
            common_ticker = PREFERRED_TO_COMMON[ticker]
            common_row = df[df['ticker'].astype(str).str.strip() == common_ticker]
            if len(common_row) > 0 and common_row.iloc[0]['tier1'] != '미분류':
                df.at[idx, 'tier1'] = common_row.iloc[0]['tier1']
                df.at[idx, 'tier2'] = common_row.iloc[0]['tier2']
                df.at[idx, 'tier3'] = common_row.iloc[0]['tier3']
                df.at[idx, 'match_status'] = 'preferred_manual'
                print(f"  ✓ {ticker} {df.at[idx, 'name']} → 보통주({common_ticker}) 상속: {common_row.iloc[0]['tier1']}")
                fixed += 1

    print(f"  수동 분류 적용: {fixed}건")
    remaining = len(df[df['tier1'] == '미분류'])
    print(f"  최종 미분류: {remaining}건")
    return df


# ============================================================
# 검증 결과 저장
# ============================================================
def save_verified(df):
    """검증 완료된 마스터 테이블 저장"""
    # 섹터 요약 재생성
    df_classified = df[df['tier1'] != '미분류']
    sector_summary = df_classified.groupby('tier1').agg(
        종목수=('ticker', 'count'),
        **({'평균시총_억': ('시가총액(억)', 'mean'),
            '총시총_억': ('시가총액(억)', 'sum')} if '시가총액(억)' in df.columns else {}),
    ).round(0).sort_values('종목수', ascending=False)

    with pd.ExcelWriter(OUTPUT_FIXED, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='전체종목', index=False)
        sector_summary.to_excel(writer, sheet_name='섹터요약')
        df_still_unmatched = df[df['tier1'] == '미분류']
        if len(df_still_unmatched) > 0:
            df_still_unmatched.to_excel(writer, sheet_name='미분류', index=False)

    print(f"\n[저장] 검증 완료 마스터: {OUTPUT_FIXED}")
    print(f"  총 {len(df)}종목, 분류 완료 {len(df_classified)}건, 미분류 {len(df) - len(df_classified)}건")


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 60)
    print("PHASE0: 분류 결과 검증")
    print(f"입력: {INPUT_EXCEL}")
    print("=" * 60)

    df = pd.read_excel(INPUT_EXCEL, sheet_name='전체종목')
    print(f"로드 완료: {len(df)}종목\n")

    # 검증 1: 정량
    q_pass = check_quantitative(df)

    # 검증 2: 스팟체크
    s_pass = check_spot(df)

    # 검증 3: 미분류 분석 + 자동 수정
    df = analyze_and_fix_unmatched(df)

    # 수동 분류 적용
    df = apply_manual_classification(df)

    # 검증 완료 파일 저장
    save_verified(df)

    # 최종 요약
    print("\n" + "=" * 60)
    print("검증 최종 요약")
    print("=" * 60)
    total = len(df)
    classified = len(df[df['tier1'] != '미분류'])
    print(f"  총 종목: {total}")
    print(f"  분류 완료: {classified} ({classified/total*100:.1f}%)")
    print(f"  미분류: {total - classified} ({(total-classified)/total*100:.1f}%)")
    print(f"  정량 검증: {'PASS' if q_pass else 'FAIL'}")
    print(f"  스팟체크: {'PASS' if s_pass else 'FAIL'}")
    print("=" * 60)


if __name__ == '__main__':
    main()
