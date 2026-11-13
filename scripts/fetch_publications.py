import json
import os
import requests

API_KEY = os.environ.get("SERPAPI_KEY")
SCHOLAR_ID = os.environ.get("SCHOLAR_ID")

def fetch_scholar_data():
    url = "https://serpapi.com"
    params = {
        "engine": "google_scholar_author",
        "author_id": SCHOLAR_ID,
        "api_key": API_KEY,
        "num": 100
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    raw_data = response.json()
    
    # Extract citation metrics
    cited_by = raw_data.get("cited_by", {}).get("table", [])
    citations = cited_by[0]["citations"]["all"] if len(cited_by) > 0 else 0
    h_index = cited_by[1]["h_index"]["all"] if len(cited_by) > 1 else 0
    i10_index = cited_by[2]["i10_index"]["all"] if len(cited_by) > 2 else 0

    data = {
        "name": raw_data.get("author", {}).get("name"),
        "affiliation": raw_data.get("author", {}).get("affiliations"),
        "citations": citations,
        "h_index": h_index,
        "i10_index": i10_index,
        "publications": []
    }
    
    # Extract publications
    for article in raw_data.get("articles", []):
        data["publications"].append({
            "title": article.get("title"),
            "link": article.get("link"),
            "authors": article.get("authors"),
            "venue": article.get("publication"),
            "year": article.get("year"),
            "citations": article.get("cited_by", {}).get("value") or 0
        })
        
    # Sort publications by year descending
    data["publications"].sort(key=lambda x: str(x["year"] or "0"), reverse=True)
    
    # Saves publications.json to the root directory when run from root
    with open("publications.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    fetch_scholar_data()
