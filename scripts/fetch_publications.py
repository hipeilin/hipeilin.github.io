"""
Fetches a Google Scholar profile via SerpApi and writes publications.json.

Needs the SERPAPI_KEY and SCHOLAR_ID environment variables.

SerpApi cost per run:
  - 1 search per 100 publications for the profile list (1 for most profiles)
  - plus 1 search per paper whose author list Scholar truncates ("..."),
    but only the first time: the full list is saved in author_cache.json
    and reused on later runs.
"""

import json
import os
import re
import sys

import requests

API_KEY = os.environ.get("SERPAPI_KEY")
SCHOLAR_ID = os.environ.get("SCHOLAR_ID")
ENDPOINT = "https://serpapi.com/search.json"
PAGE_SIZE = 100            # SerpApi maximum per request
MAX_DETAIL_FETCHES = 5     # cap on extra searches per run, to protect the monthly quota
OUTPUT_PATH = "publications.json"
AUTHOR_CACHE_PATH = "author_cache.json"

# Lowercase name particles that belong to the surname ("Stef van den Elzen" -> "S van den Elzen")
SURNAME_PARTICLES = {"van", "von", "der", "den", "de", "del", "della", "da", "di", "du", "la", "le", "dos", "das", "ter", "ten"}


def serpapi(params: dict) -> dict:
    params = {"engine": "google_scholar_author", "author_id": SCHOLAR_ID,
              "api_key": API_KEY, "hl": "en", **params}
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


def abbreviate(full_name: str) -> str:
    """'Jason S Carroll' -> 'JS Carroll', matching Google Scholar's short style."""
    tokens = full_name.split()
    if len(tokens) < 2:
        return full_name
    start = len(tokens) - 1
    while start > 1 and tokens[start - 1].lower() in SURNAME_PARTICLES:
        start -= 1
    initials = "".join(part[0] for token in tokens[:start] for part in token.split("-") if part)
    return f"{initials} {' '.join(tokens[start:])}"


def is_truncated(authors: str) -> bool:
    return bool(authors) and authors.rstrip().endswith(("...", "…"))


def merge_authors(listing: str, full: str) -> str | None:
    """Keep Scholar's short names as shown, and append the missing ones abbreviated."""
    visible = [a.strip() for a in re.split(r",\s*", listing.rstrip(" .…")) if a.strip()]
    full_names = [a.strip() for a in full.split(",") if a.strip()]
    if len(full_names) <= len(visible):
        return None  # nothing new, or unexpected format
    return ", ".join(visible + [abbreviate(n) for n in full_names[len(visible):]])


def load_cache() -> dict:
    try:
        with open(AUTHOR_CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def complete_authors(article: dict, cache: dict, budget: list) -> str:
    """Return the full author list, using the cache or one extra SerpApi search."""
    authors = article.get("authors") or ""
    if not is_truncated(authors):
        return authors

    citation_id = article.get("citation_id")
    if not citation_id:
        return authors
    if citation_id in cache:
        return cache[citation_id]
    if budget[0] <= 0:
        print(f"Detail fetch limit reached, keeping short author list for: {article.get('title')}")
        return authors

    budget[0] -= 1
    try:
        detail = serpapi({"view_op": "view_citation", "citation_id": citation_id})
        merged = merge_authors(authors, (detail.get("citation") or {}).get("authors") or "")
    except Exception as exc:  # noqa: BLE001 - keep the short list, try again next run
        print(f"Could not fetch full author list for '{article.get('title')}': {exc}")
        return authors

    if not merged:
        print(f"No extra authors found for: {article.get('title')}")
        return authors
    cache[citation_id] = merged
    print(f"Fetched full author list for: {article.get('title')}")
    return merged


def fetch_articles(first_page: dict) -> list:
    articles = list(first_page.get("articles", []))
    page, start = first_page, PAGE_SIZE
    # Fetch more pages only if the profile has more than 100 publications.
    while len(page.get("articles", [])) == PAGE_SIZE:
        page = serpapi({"num": PAGE_SIZE, "start": start})
        articles.extend(page.get("articles", []))
        start += PAGE_SIZE
    return articles


def write_json(path: str, data) -> None:
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(temp_path, path)


def fetch_scholar_data():
    first = serpapi({"num": PAGE_SIZE, "start": 0})
    articles = fetch_articles(first)
    if not articles:
        raise RuntimeError("SerpApi returned no publications; not overwriting publications.json")

    cache = load_cache()
    budget = [MAX_DETAIL_FETCHES]
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
            "authors": complete_authors(article, cache, budget),
            "venue": article.get("publication"),
            "year": article.get("year"),
            "citations": (article.get("cited_by") or {}).get("value") or 0,
        })

    data["publications"].sort(key=lambda x: str(x["year"] or "0"), reverse=True)

    write_json(AUTHOR_CACHE_PATH, cache)
    write_json(OUTPUT_PATH, data)
    used = MAX_DETAIL_FETCHES - budget[0]
    print(f"Wrote {len(data['publications'])} publications to {OUTPUT_PATH} "
          f"(citations: {data['citations']}, h-index: {data['h_index']}, extra author lookups: {used})")


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
