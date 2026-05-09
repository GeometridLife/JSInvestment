"""Finnhub fetchers."""
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

_ROOT = Path(__file__).resolve().parents[2]
_NEWS_GENERAL_CACHE_DIR = _ROOT / "data" / "cache" / "finnhub" / "news_general"


def _load_env() -> None:
    env_path = _ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


def fetch_general_news() -> list[dict]:
    """Fetch Finnhub /news?category=general. Returns most recent items (no date filter)."""
    _load_env()
    api_key = os.environ["FINNHUB_API_KEY"]
    url = "https://finnhub.io/api/v1/news?" + urlencode(
        {"category": "general", "token": api_key}
    )
    with urlopen(url, timeout=30) as resp:
        return json.loads(resp.read())


def save_general_news(items: list[dict]) -> dict[date, int]:
    """Group items by UTC date and write to cache, deduping by `id` against existing files.

    Cache path: data/cache/finnhub/news_general/<YYYY-MM-DD>.json
    Returns: {date: total_item_count_in_cache_after_save}.
    """
    _NEWS_GENERAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    by_date: dict[date, list[dict]] = {}
    for it in items:
        d = datetime.fromtimestamp(it["datetime"], tz=timezone.utc).date()
        by_date.setdefault(d, []).append(it)

    counts: dict[date, int] = {}
    for d, day_items in by_date.items():
        path = _NEWS_GENERAL_CACHE_DIR / f"{d.isoformat()}.json"
        existing: dict[int, dict] = {}
        if path.exists():
            for prev in json.loads(path.read_text()):
                existing[prev["id"]] = prev
        for it in day_items:
            existing[it["id"]] = it
        merged = sorted(existing.values(), key=lambda x: x["datetime"])
        path.write_text(json.dumps(merged, ensure_ascii=False, indent=2))
        counts[d] = len(merged)
    return counts


if __name__ == "__main__":
    items = fetch_general_news()
    counts = save_general_news(items)
    print(f"items fetched: {len(items)}")
    for d in sorted(counts):
        print(f"  {d}: {counts[d]} total in cache")
