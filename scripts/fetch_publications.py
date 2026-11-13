"""
Fetches a Google Scholar profile via SerpApi and writes publications.json.

Needs the SERPAPI_KEY and SCHOLAR_ID environment variables.
Each run costs one SerpApi search per 100 publications.
"""

import json
import os
import sys

import requests

API_KEY = os.environ.get("SERPAPI_KEY")
SCHOLAR_ID = os.environ.get("SCHOLAR_ID")
ENDPOINT = "https://serpapi.com/search.json"
PAGE_SIZE = 100  # SerpApi maximum per request
OUTPUT_PATH = "publications.json"


def get_page(start: int) -> dict:
    params = {
        "engine": "google_scholar_author",
        "author_id": SCHOLAR_ID,
        "api_key": API_KEY,
        "hl": "en",
        "num": PAGE_SIZE,
        "start": start,
    }
    response = requests.get(ENDPOINT, params=params, timeout=60)
    try:
        payload = response.json()
    except ValueError:
        raise RuntimeError(f"SerpApi returned non-JSON (HTTP {response.status_code}): {response.text[:200]}")
    if "error" in payload:
        # SerpApi explains problems (bad key, quota used up, bad author_id) in an "error" field.
        raise RuntimeError(f"SerpApi error (HTTP {response.status_code}): {payload['error']}")
    response.raise_for_status()
    return payload


def metric(table: list, name: str) -> int:
    """Pull e.g. 'h_index' -> 'all' out of SerpApi's cited_by table."""
    for row in table:
        if name in row:
            return row[name].get("all", 0) or 0
    return 0


def fetch_scholar_data():
    first = get_page(0)
    articles = list(first.get("articles", []))

    # Fetch more pages only if the profile has more than 100 publications.
    start = PAGE_SIZE
    page = first
    while len(page.get("articles", [])) == PAGE_SIZE:
        page = get_page(start)
        articles.extend(page.get("articles", []))
        start += PAGE_SIZE

    if not articles:
        raise RuntimeError("SerpApi returned no publications; not overwriting publications.json")

    author = first.get("author", {})
    table = (first.get("cited_by") or {}).get("table", [])

    data = {
        "name": author.get("name"),
        "affiliation": author.get("affiliations"),
        "citations": metric(table, "citations"),
        "h_index": metric(table, "h_index"),
        "i10_index": metric(table, "i10_index"),
        "publications": [],
    }

    for article in articles:
        data["publications"].append({
            "title": article.get("title"),
            "link": article.get("link"),
            "authors": article.get("authors"),
            "venue": article.get("publication"),
            "year": article.get("year"),
            "citations": (article.get("cited_by") or {}).get("value") or 0,
        })

    data["publications"].sort(key=lambda x: str(x["year"] or "0"), reverse=True)

    temp_path = OUTPUT_PATH + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(temp_path, OUTPUT_PATH)
    print(f"Wrote {len(data['publications'])} publications to {OUTPUT_PATH} "
          f"(citations: {data['citations']}, h-index: {data['h_index']})")


if __name__ == "__main__":
    if not API_KEY:
        sys.exit("Error: SERPAPI_KEY is not set (check the repository secret name).")
    if not SCHOLAR_ID:
        sys.exit("Error: SCHOLAR_ID is not set.")
    try:
        fetch_scholar_data()
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to update publications: {exc}", file=sys.stderr)
        print("Existing publications.json was left unchanged.")
        sys.exit(1)
