"""
Fetches publications from Google Scholar and writes publications.json.
Set SCHOLAR_ID to your Google Scholar author ID (the string after user= in your profile URL).
"""

import json
import os
import signal
import sys
import time
from typing import Any, Callable

from scholarly import scholarly

SCHOLAR_ID = "uR88WY8AAAAJ"
MAX_RETRIES = 3
BACKOFF_SECONDS = 5
CALL_TIMEOUT_SECONDS = 60


def call_with_timeout(func: Callable[[], Any]) -> Any:
    if not hasattr(signal, "SIGALRM"):
        return func()

    def timeout_handler(_signum, _frame):
        raise TimeoutError(f"Operation timed out after {CALL_TIMEOUT_SECONDS}s")

    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(CALL_TIMEOUT_SECONDS)
    try:
        return func()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)


def format_authors(raw: str) -> str:
    """'John A. Smith and Jane Doe' → 'J. Smith, J. Doe'"""
    authors = []
    for name in raw.split(" and "):
        name = name.strip()
        if not name:
            continue
        if "," in name:
            last, first = name.split(",", 1)
            first = first.strip()
        else:
            parts = name.split()
            first = parts[0] if len(parts) > 1 else ""
            last = parts[-1]
        initial = (first[0] + ".") if first else ""
        authors.append(f"{initial} {last}".strip())
    return ", ".join(authors)


def retry_call(func: Callable[[], Any], operation: str, max_retries: int = MAX_RETRIES):
    """Retry transient Google Scholar failures with exponential backoff."""
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except Exception as exc:  # noqa: BLE001 - this is a network/Scholarly failure path
            last_error = exc
            if attempt == max_retries:
                raise RuntimeError(f"{operation} failed after {max_retries} attempts: {exc}") from exc
            wait_time = BACKOFF_SECONDS * attempt
            print(f"{operation} failed (attempt {attempt}/{max_retries}): {exc}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
    raise RuntimeError(f"{operation} failed after {max_retries} attempts: {last_error}")


def fetch_author():
    def get_author():
        author = scholarly.search_author_id(SCHOLAR_ID)
        scholarly.fill(author, sections=["publications"])
        return author

    return retry_call(lambda: call_with_timeout(get_author), "Fetch author metadata")


def fetch_publication_details(pub):
    def get_pub_details():
        scholarly.fill(pub)
        return pub

    return retry_call(
        lambda: call_with_timeout(get_pub_details),
        f"Fetch publication details for: {pub.get('bib', {}).get('title', 'unknown')}",
    )


def fetch():
    author = fetch_author()
    pubs = []

    for pub in author.get("publications", []):
        try:
            fetch_publication_details(pub)
        except RuntimeError as exc:
            print(f"Skipping publication due to fetch error: {exc}")
            continue

        bib = pub.get("bib", {})
        pubs.append({
            "title": bib.get("title", ""),
            "year": bib.get("pub_year", ""),
            "authors": format_authors(bib.get("author", "")),
            "venue": bib.get("journal", "") or bib.get("conference", "") or bib.get("publisher", "") or bib.get("citation", ""),
            "url": pub.get("pub_url", ""),
            "citations": pub.get("num_citations", 0),
        })

    pubs.sort(key=lambda p: str(p["year"] or "0"), reverse=True)

    output_path = "publications.json"
    temp_path = f"{output_path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(pubs, f, indent=2, ensure_ascii=False)

    os.replace(temp_path, output_path)
    print(f"Wrote {len(pubs)} publications to {output_path}")


if __name__ == "__main__":
    if SCHOLAR_ID == "YOUR_SCHOLAR_ID_HERE":
        print("Error: set SCHOLAR_ID in scripts/fetch_publications.py")
        sys.exit(1)

    try:
        fetch()
    except RuntimeError as exc:
        print(f"Skipping update due to transient fetch failure: {exc}", file=sys.stderr)
        print("Existing publications.json was left unchanged.")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001 - network failure path
        print(f"Failed to update publications: {exc}", file=sys.stderr)
        print("Existing publications.json was left unchanged.")
        sys.exit(1)
