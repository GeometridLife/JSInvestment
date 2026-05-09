"""GDELT fetchers."""
import json
from datetime import date, datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def fetch_doc_articles(
    query: str,
    day: date,
    max_records: int = 250,
) -> list[dict]:
    """Fetch GDELT DOC 2.0 ArtList for `query` on UTC `day` (00:00:00 ~ 23:59:59).

    Each article has: url, url_mobile, title, seendate (YYYYMMDDTHHMMSSZ),
    socialimage, domain, language, sourcecountry.
    """
    ymd = day.strftime("%Y%m%d")
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urlencode(
        {
            "query": query,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": max_records,
            "sort": "DateDesc",
            "startdatetime": ymd + "000000",
            "enddatetime": ymd + "235959",
        }
    )
    req = Request(url, headers={"User-Agent": "narrative-fetcher/0.1"})
    with urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data.get("articles", [])


if __name__ == "__main__":
    from datetime import timezone

    today = datetime.now(timezone.utc).date()
    items = fetch_doc_articles("stock market", today)
    dates = sorted(
        {datetime.strptime(it["seendate"], "%Y%m%dT%H%M%SZ").date() for it in items}
    )
    print(f"day requested (UTC): {today}")
    print(f"items: {len(items)}")
    if dates:
        print(f"date range returned: {dates[0]} ~ {dates[-1]} ({len(dates)} unique days)")
