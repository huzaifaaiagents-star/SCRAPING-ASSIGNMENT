import os
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
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


BASE_URL = "https://books.toscrape.com/catalogue/"
CACHE_DIR = "cache"
HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0 (+https://github.com/huzaifaaiagents-star/SCRAPING-ASSIGNMENT)"
}
TIMEOUT = 5
MAX_PAGES = 3
DELAY = 0.5  # seconds, only for real requests


def get_page(page_num, page_url):
    cache_path = os.path.join(CACHE_DIR, f"catalogue-page-{page_num}.html")

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT — page {page_num} — {len(html)} bytes")
        return html

    response = requests.get(page_url, headers=HEADERS, timeout=TIMEOUT)
    if response.status_code != 200:
        print(f"FAILED FETCH — page {page_num} — status {response.status_code}")
        return None

    html = response.text
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"FETCH — page {page_num} — {len(html)} bytes")

    time.sleep(DELAY)  # only after a real network request
    return html


def discover_pages():
    all_book_links = []
    current_url = urljoin(BASE_URL, "page-1.html")
    page_num = 1

    while page_num <= MAX_PAGES:
        html = get_page(page_num, current_url)
        if html is None:
            break

        soup = BeautifulSoup(html, "html.parser")

        # Collect book links from this page
        for article in soup.find_all("article"):
            link_tag = article.find("a")
            if link_tag and link_tag.get("href"):
                absolute_url = urljoin(current_url, link_tag["href"])
                all_book_links.append(absolute_url)

        # Stop if we've hit our page cap
        if page_num == MAX_PAGES:
            break

        # Find the "next" link
        next_li = soup.find("li", class_="next")
        if not next_li:
            print("No next link found — stopping.")
            break

        next_href = next_li.find("a")["href"]
        current_url = urljoin(current_url, next_href)
        page_num += 1

    unique_urls = list(set(all_book_links))

    print(f"catalogue_pages={page_num}")
    print(f"discovered={len(all_book_links)}")
    print(f"unique_urls={len(unique_urls)}")

    return unique_urls


if __name__ == "__main__":
    discover_pages()