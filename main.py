import os
import requests

CACHE_PATH = "cache/catalogue-page-1.html"
URL = "https://books.toscrape.com/catalogue/page-1.html"
HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0 (+https://github.com/huzaifaaiagents-star/SCRAPING-ASSIGNMENT)"
}
TIMEOUT = 5  # seconds

def get_page():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT — {len(html)} bytes")
        return html

    response = requests.get(URL, headers=HEADERS, timeout=TIMEOUT)

    if response.status_code != 200:
        print(f"FAILED FETCH — status code {response.status_code}")
        return None

    html = response.text
    os.makedirs("cache", exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"FETCH — {len(html)} bytes")
    return html

if __name__ == "__main__":
    get_page()