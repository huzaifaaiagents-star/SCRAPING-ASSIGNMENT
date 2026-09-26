import os
import json
import time
from datetime import datetime, timezone
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
    all_book_entries = []  # list of {"url": ..., "source_page": ...}
    current_url = urljoin(BASE_URL, "page-1.html")
    page_num = 1

    while page_num <= MAX_PAGES:
        html = get_page(page_num, current_url)
        if html is None:
            break

        soup = BeautifulSoup(html, "html.parser")

        for article in soup.find_all("article"):
            link_tag = article.find("a")
            if link_tag and link_tag.get("href"):
                absolute_url = urljoin(current_url, link_tag["href"])
                all_book_entries.append({
                    "url": absolute_url,
                    "source_page": current_url
                })

        if page_num == MAX_PAGES:
            break

        next_li = soup.find("li", class_="next")
        if not next_li:
            print("No next link found — stopping.")
            break

        next_href = next_li.find("a")["href"]
        current_url = urljoin(current_url, next_href)
        page_num += 1

    # Dedupe on URL, keep first-seen source_page
    seen_urls = set()
    unique_entries = []
    for entry in all_book_entries:
        if entry["url"] not in seen_urls:
            seen_urls.add(entry["url"])
            unique_entries.append(entry)

    print(f"catalogue_pages={page_num}")
    print(f"discovered={len(all_book_entries)}")
    print(f"unique_urls={len(unique_entries)}")

    with open("discovered_urls.json", "w", encoding="utf-8") as f:
        json.dump(unique_entries, f, indent=2)

    return unique_entries


if __name__ == "__main__":
    discover_pages()

# --- reuse from Stage 1/2 ---
CACHE_DIR = "cache"
HEADERS = {
    "User-Agent": "FlyRankInternshipA9/1.0 (+https://github.com/huzaifaaiagents-star/SCRAPING-ASSIGNMENT)"
}
TIMEOUT = 5
DELAY = 0.5


def get_page(cache_filename, page_url):
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT — {cache_filename} — {len(html)} bytes")
        return html

    response = requests.get(page_url, headers=HEADERS, timeout=TIMEOUT)
    response.encoding = "utf-8"  # fixes the Â£ bug

    if response.status_code != 200:
        print(f"FAILED FETCH — {cache_filename} — status {response.status_code}")
        return None

    html = response.text
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"FETCH — {cache_filename} — {len(html)} bytes")

    time.sleep(DELAY)  # only after a real request
    return html


def extract_record(book_url, source_page):
    # cache filename derived from the book's slug, so each detail page gets its own file
    slug = book_url.rstrip("/").split("/")[-2]
    cache_filename = f"detail-{slug}.html"

    html = get_page(cache_filename, book_url)
    if html is None:
        return None

    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("div", class_="product_main").find("h1").get_text(strip=True)

    price_text = soup.find("p", class_="price_color").get_text(strip=True)

    availability_text = soup.find("p", class_="instock availability").get_text(strip=True)

    rating_tag = soup.find("p", class_="star-rating")
    rating_text = rating_tag["class"][1] if rating_tag else None

    desc_heading = soup.find("div", id="product_description")
    if desc_heading:
        description = desc_heading.find_next_sibling("p").get_text(strip=True)
    else:
        description = None

    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # pyrefly: ignore [invalid-syntax]
    return {
        "title": title,
        "product_url": book_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }


if __name__ == "__main__":
    # Load the book URLs discovered in Stage 2 — adjust this to however you saved them
    with open("discovered_urls.json", "r", encoding="utf-8") as f:
        book_entries = json.load(f)  # expects list of {"url": ..., "source_page": ...}

    records = []
    for entry in book_entries:
        record = extract_record(entry["url"], entry["source_page"])
        if record:
            records.append(record)

    print(json.dumps(records[0], indent=2))
    print(f"detail_pages={len(records)}")

    with open("records.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)