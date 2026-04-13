import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

def fetch_page_text(url: str, max_chars: int = 5000) -> str:
    try:
        resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())
        return text
    except Exception:
        return ""


def duckduckgo_search(topic: str, num_results: int = 5) -> list[dict]:
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(topic, max_results=num_results):
            full_text = fetch_page_text(r["href"])
            results.append({
                "title": r["title"],
                "link": r["href"],
                "snippet": r["body"],
                "full_text": full_text,
            })
    return results
