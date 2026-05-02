#!/usr/bin/env python3
"""
관세청 수출입 무역통계 크롤러
tradedata.go.kr 내부 API를 호출하여
수출입 통계를 CSV로 저장합니다. (총괄 / 품목별)

사용법:
  python crawl_customs.py                              # 총괄 최근 12개월
  python crawl_customs.py --from 202301 --to 202312    # 기간 지정
  python crawl_customs.py --mode YEAR --from 2020 --to 2025  # 연도별
  python crawl_customs.py --hs 85                      # 품목별 (HS 2단위, 예: 85=전기기기)
  python crawl_customs.py --hs 8541                    # 품목별 (HS 4단위)
  python crawl_customs.py --hs 85,87,90                # 여러 품목 동시 조회
  python crawl_customs.py --output my_data.csv         # 파일명 지정
"""

import argparse
import csv
import datetime
import sys
import time

import requests

BASE_URL = "https://tradedata.go.kr"
INDEX_URL = f"{BASE_URL}/cts/index.do"
API_URL_ALL = f"{BASE_URL}/cts/hmpg/retrieveTradeAll.do"
API_URL_ITEM = f"{BASE_URL}/cts/hmpg/retrieveTrade.do"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": INDEX_URL,
    "X-Requested-With": "XMLHttpRequest",
    "isAjax": "true",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

# 응답 JSON에서 추출할 필드와 CSV 컬럼명 매핑
FIELD_MAP_ALL = [
    ("priodTitle", "기간"),
    ("expCnt", "수출건수"),
    ("impCnt", "수입건수"),
    ("expTtwg", "수출중량"),
    ("impTtwg", "수입중량"),
    ("expUsdAmt", "수출금액(천달러)"),
    ("impUsdAmt", "수입금액(천달러)"),
]

FIELD_MAP_ITEM = [
    ("priodTitle", "기간"),
    ("hsSgn", "HS코드"),
    ("korePrlstNm", "품목명"),
    ("expCnt", "수출건수"),
    ("impCnt", "수입건수"),
    ("expTtwg", "수출중량"),
    ("impTtwg", "수입중량"),
    ("expUsdAmt", "수출금액(천달러)"),
    ("impUsdAmt", "수입금액(천달러)"),
    ("cmtrBlncAmt", "무역수지(천달러)"),
]


def get_session() -> requests.Session:
    """세션 쿠키를 획득합니다."""
    sess = requests.Session()
    sess.headers.update(HEADERS)
    sess.get(INDEX_URL, timeout=10)
    return sess


def _post_api(sess, url, params, retries=3, delay=1.0):
    """API POST 호출 (재시도 포함)."""
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            resp = sess.post(url, data=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_exc = e
            if attempt < retries:
                time.sleep(delay)
    raise last_exc


def fetch_trade_data(
    sess: requests.Session,
    mode: str = "MON",
    period_from: str = "202401",
    period_to: str = "202412",
    stats_base: str = "acptDd",
    weight_unit: str = "1000",
    page: int = 1,
    page_size: int = 500,
) -> dict:
    """총괄 수출입 통계 데이터를 반환합니다."""
    params = {
        "priodKind": mode,
        "priodFr": period_from,
        "priodTo": period_to,
        "statsBase": stats_base,
        "ttwgTpcd": weight_unit,
        "selectPaging": str(page),
        "showPagingLine": str(page_size),
        "sortColumn": "",
        "sortOrder": "",
    }
    return _post_api(sess, API_URL_ALL, params)


def fetch_trade_by_item(
    sess: requests.Session,
    hs_codes: str,
    mode: str = "MON",
    period_from: str = "202401",
    period_to: str = "202412",
    stats_base: str = "acptDd",
    weight_unit: str = "1000",
    page: int = 1,
    page_size: int = 500,
) -> dict:
    """품목별(HS코드) 수출입 통계 데이터를 반환합니다."""
    # HS 코드 자릿수로 그룹 단위 결정 (2,4,6,10단위)
    first_code = hs_codes.split(",")[0].strip()
    hs_digits = str(len(first_code))
    params = {
        "tradeKind": "ETS_MNK_1020000A",
        "priodKind": mode,
        "priodFr": period_from,
        "priodTo": period_to,
        "statsBase": stats_base,
        "ttwgTpcd": weight_unit,
        "selectPaging": str(page),
        "showPagingLine": str(page_size),
        "sortColumn": "",
        "sortOrder": "",
        "hsSgnGrpCol": hs_digits,
        "hsSgnWhrCol": hs_digits,
        "hsSgn": hs_codes,
        "subHsSgn": "Y",
    }
    return _post_api(sess, API_URL_ITEM, params)


def clean_value(val: str) -> str:
    """숫자 문자열의 공백·쉼표를 제거합니다."""
    if isinstance(val, str):
        return val.strip().replace(",", "")
    return str(val)


def save_csv(items: list, output_path: str, field_map: list):
    """수집된 데이터를 CSV로 저장합니다."""
    csv_columns = [col for _, col in field_map]
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=csv_columns)
        writer.writeheader()
        for item in items:
            row = {}
            for json_key, col_name in field_map:
                row[col_name] = clean_value(item.get(json_key, ""))
            writer.writerow(row)


def default_period():
    """기본 조회 기간: 최근 12개월."""
    now = datetime.date.today()
    to_ym = now.strftime("%Y%m")
    from_date = now.replace(year=now.year - 1, day=1)
    from_ym = from_date.strftime("%Y%m")
    return from_ym, to_ym


def main():
    parser = argparse.ArgumentParser(
        description="관세청 수출입 무역통계 크롤러 (tradedata.go.kr)"
    )
    parser.add_argument(
        "--mode", choices=["MON", "YEAR"], default="MON",
        help="조회 단위: MON(월별, 기본) 또는 YEAR(연도별)",
    )
    parser.add_argument(
        "--from", dest="period_from",
        help="시작 기간 (MON: YYYYMM, YEAR: YYYY)",
    )
    parser.add_argument(
        "--to", dest="period_to",
        help="종료 기간 (MON: YYYYMM, YEAR: YYYY)",
    )
    parser.add_argument(
        "--stats-base", default="acptDd", choices=["acptDd", "tkofDd"],
        help="통계기준: acptDd(수리일, 기본) / tkofDd(출항일)",
    )
    parser.add_argument(
        "--weight", default="1000", choices=["1000", "1"],
        help="중량단위: 1000(톤, 기본) / 1(kg)",
    )
    parser.add_argument(
        "--hs", dest="hs_codes", default=None,
        help="품목별 조회: HS코드 (예: 85, 8541, 85,87,90). 쉼표로 여러 코드 지정 가능",
    )
    parser.add_argument(
        "--output", default=None,
        help="출력 CSV 파일명 (기본: export_stats.csv 또는 export_stats_hs{코드}.csv)",
    )
    args = parser.parse_args()

    # 기간 기본값 설정
    # 수정 참고
    # dd
    # ddd
    if args.mode == "MON":
        default_from, default_to = default_period()
        period_from = args.period_from or default_from
        period_to = args.period_to or default_to
    else:
        period_from = args.period_from or "2020"
        period_to = args.period_to or "2025"

    is_item_mode = bool(args.hs_codes)
    output_path = args.output
    if output_path is None:
        if is_item_mode:
            safe = args.hs_codes.replace(",", "_")
            output_path = f"export_stats_hs{safe}.csv"
        else:
            output_path = "export_stats.csv"

    weight_label = "톤" if args.weight == "1000" else "kg"
    if is_item_mode:
        print(
            f"[조회] 품목별(HS={args.hs_codes}), 모드={args.mode}, "
            f"기간={period_from}~{period_to}, "
            f"통계기준={args.stats_base}, 중량단위={weight_label}"
        )
    else:
        print(
            f"[조회] 총괄, 모드={args.mode}, 기간={period_from}~{period_to}, "
            f"통계기준={args.stats_base}, 중량단위={weight_label}"
        )

    try:
        sess = get_session()
    except Exception as e:
        print(f"세션 초기화 실패: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if is_item_mode:
            result = fetch_trade_by_item(
                sess,
                hs_codes=args.hs_codes,
                mode=args.mode,
                period_from=period_from,
                period_to=period_to,
                stats_base=args.stats_base,
                weight_unit=args.weight,
            )
        else:
            result = fetch_trade_data(
                sess,
                mode=args.mode,
                period_from=period_from,
                period_to=period_to,
                stats_base=args.stats_base,
                weight_unit=args.weight,
            )
    except Exception as e:
        print(f"API 호출 실패: {e}", file=sys.stderr)
        sys.exit(1)

    items = result.get("items", [])
    count = result.get("count", 0)

    if not items:
        print("조회 결과가 없습니다.")
        sys.exit(1)

    # 품목별 조회 시 첫 행(총계)은 HS코드가 비어있으므로 제외
    if is_item_mode:
        items = [it for it in items if it.get("hsSgn", "").strip()]
        field_map = FIELD_MAP_ITEM
    else:
        field_map = FIELD_MAP_ALL

    save_csv(items, output_path, field_map)
    print(f"[완료] {len(items)}건 저장 → {output_path}")


if __name__ == "__main__":
    main()
