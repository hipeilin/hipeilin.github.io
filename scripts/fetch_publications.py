"""
Fetches publications from Google Scholar and writes publications.json.
Set SCHOLAR_ID to your Google Scholar author ID (the string after user= in your profile URL).
"""

import json
import sys
from scholarly import scholarly, ProxyGenerator

SCHOLAR_ID = "YOUR_SCHOLAR_ID_HERE"


def fetch():
    try:
        author = scholarly.search_author_id(SCHOLAR_ID)
        scholarly.fill(author, sections=["publications"])
    except Exception as e:
        # Retry once with a free proxy if Google blocks the direct request
        print(f"Direct fetch failed ({e}), retrying with proxy...")
        pg = ProxyGenerator()
        pg.FreeProxies()
        scholarly.use_proxy(pg)
        author = scholarly.search_author_id(SCHOLAR_ID)
        scholarly.fill(author, sections=["publications"])

    pubs = []
    for pub in author.get("publications", []):
        bib = pub.get("bib", {})
        pubs.append({
            "title": bib.get("title", ""),
            "year": bib.get("pub_year", ""),
            "venue": bib.get("venue", ""),
            "abstract": bib.get("abstract", ""),
            "url": pub.get("pub_url", ""),
            "citations": pub.get("num_citations", 0),
        })

    # Most recent first
    pubs.sort(key=lambda p: p["year"] or "0", reverse=True)

    with open("publications.json", "w", encoding="utf-8") as f:
        json.dump(pubs, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(pubs)} publications to publications.json")


if __name__ == "__main__":
    if SCHOLAR_ID == "YOUR_SCHOLAR_ID_HERE":
        print("Error: set SCHOLAR_ID in scripts/fetch_publications.py")
        sys.exit(1)
    fetch()
