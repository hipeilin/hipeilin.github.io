"""
Fetches publications from Google Scholar and writes publications.json.
Set SCHOLAR_ID to your Google Scholar author ID (the string after user= in your profile URL).

If the SCRAPER_API_KEY environment variable is set, requests are routed through
ScraperAPI (needed on GitHub Actions, where Google Scholar blocks datacenter IPs).
Without it, the script connects to Google Scholar directly (fine for local runs).
"""

import json
import os
from scholarly import scholarly

SCHOLAR_ID = os.environ.get("SCHOLAR_ID", "uR88WY8AAAAJ")

def fetch_scholar_data():
    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(author, sections=['basics', 'indices', 'publications'])
    
    data = {
        "name": author.get("name"),
        "affiliation": author.get("affiliation"),
        "citations": author.get("citedby", 0),
        "h_index": author.get("hindex", 0),
        "i10_index": author.get("i10index", 0),
        "publications": []
    }
    
    for pub in author.get("publications", []):
        bib = pub.get("bib", {})
        data["publications"].append({
            "title": bib.get("title"),
            "year": bib.get("pub_year"),
            "citations": pub.get("num_citations", 0),
            "venue": bib.get("citation", "")
        })
        
    # Sort publications by year descending
    data["publications"].sort(key=lambda x: str(x["year"] or "0"), reverse=True)
    
    with open("scholar_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    fetch_scholar_data()
