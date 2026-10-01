import os
import json
import time
from datetime import datetime, timezone
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
from typing import Literal, Optional
from pydantic import BaseModel, field_validator, ValidationError

# ---- KEEP YOUR OWN VALUES HERE ----
CACHE_DIR = "cache"
HEADERS = {"User-Agent": "FlyRankInternshipA9/1.0 (https://github.com/huzaifaaiagents-star/SCRAPING-ASSIGNMENT)"}
TIMEOUT = 10
DELAY = 0.5
RETRY_WAIT = 3
STATS = {"pages_fetched": 0, "cache_hits": 0}

BASE_URL = "https://books.toscrape.com/catalogue/"
MAX_PAGES = 3
# -----------------------------------


class Book(BaseModel):
    title: str
    product_url: str
    price_text: str                      # raw, kept as-is
    price_gbp: float                     # clean, a real number
    availability_text: str
    rating_text: Literal["One", "Two", "Three", "Four", "Five"]
    description: Optional[str] = None    # the only optional field
    source_page: str
    fetched_at: str

    @field_validator("product_url")
    @classmethod
    def url_must_be_https(cls, v):
        if not v.startswith("https://"):
            raise ValueError("product_url must start with https://")
        return v


def parse_price(price_text: str) -> float:
    return float(price_text.replace("£", "").strip())


def get_page(cache_filename, page_url):
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        STATS["cache_hits"] += 1
        print(f"CACHE HIT — {cache_filename} — {len(html)} bytes")
        return html

    for attempt in (1, 2):
        try:
            response = requests.get(page_url, headers=HEADERS, timeout=TIMEOUT)
        except (requests.Timeout, requests.ConnectionError) as e:
            if attempt == 2:
                raise RuntimeError(f"request failed after retry: {e}")
            print(f"RETRY — {cache_filename} — {type(e).__name__}")
            time.sleep(RETRY_WAIT)
            continue

        if response.status_code >= 500:
            if attempt == 2:
                raise RuntimeError(f"fetch failed with status {response.status_code} after retry")
            print(f"RETRY — {cache_filename} — status {response.status_code}")
            time.sleep(RETRY_WAIT)
            continue
        break  # 200, 404, 403 and the rest: no retry

    response.encoding = "utf-8"  # fixes the Â£ bug

    if response.status_code != 200:
        raise RuntimeError(f"fetch failed with status {response.status_code}")

    html = response.text
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)
    STATS["pages_fetched"] += 1
    print(f"FETCH — {cache_filename} — {len(html)} bytes")

    time.sleep(DELAY)
    return html


def extract_record(book_url, source_page):
    slug = book_url.rstrip("/").split("/")[-2]
    cache_filename = f"detail-{slug}.html"

    html = get_page(cache_filename, book_url)
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

def discover_urls():
    entries = []
    seen = set()
    page_url = urljoin(BASE_URL, "page-1.html")

    for page_num in range(1, MAX_PAGES + 1):
        html = get_page(f"catalogue-page-{page_num}.html", page_url)
        soup = BeautifulSoup(html, "html.parser")

        for article in soup.find_all("article"):
            link = article.find("a")
            if link and link.get("href"):
                url = urljoin(page_url, link["href"])
                if url not in seen:
                    seen.add(url)
                    entries.append({"url": url, "source_page": page_url})

        next_li = soup.find("li", class_="next")
        if not next_li or page_num == MAX_PAGES:
            break
        page_url = urljoin(page_url, next_li.find("a")["href"])

    return entries

if __name__ == "__main__":
    
    if os.path.exists("discovered_urls.json"):
        with open("discovered_urls.json", "r", encoding="utf-8") as f:
            book_entries = json.load(f)
    else:
        book_entries = discover_urls()
        with open("discovered_urls.json", "w", encoding="utf-8") as f:
            json.dump(book_entries, f, indent=2)

    started = datetime.now(timezone.utc)
    t0 = time.time()

    # --- Stage 3: fetch + extract (raw) ---
    records = []
    fetch_errors = []
    for entry in book_entries:
        try:
            records.append(extract_record(entry["url"], entry["source_page"]))
        except Exception as e:
            fetch_errors.append({
                "record": {"product_url": entry["url"], "source_page": entry["source_page"]},
                "reason": str(e),
            })

    print(f"detail_pages={len(records)}")

    with open("records.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    # --- Stage 4: clean + validate ---
    good = []
    errors = list(fetch_errors)
    for raw in records:
        try:
            raw = {**raw, "price_gbp": parse_price(raw["price_text"])}
            good.append(Book(**raw).model_dump())
        except (ValidationError, ValueError, KeyError) as e:
            errors.append({"record": raw, "reason": str(e)})

    # --- Stage 4: store (upsert by product_url) ---
    os.makedirs("output", exist_ok=True)
    path = "output/books.json"

    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            store = {b["product_url"]: b for b in json.load(f)}
    else:
        store = {}

    for book in good:
        store[book["product_url"]] = book

    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(store.values()), f, indent=2, ensure_ascii=False)

    with open("output/errors.json", "w", encoding="utf-8") as f:
        json.dump(errors, f, indent=2, ensure_ascii=False)

    print(f"good={len(good)} errors={len(errors)} stored={len(store)}")


    report = {
        "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": round(time.time() - t0, 2),
        "pages_fetched": STATS["pages_fetched"],
        "cache_hits": STATS["cache_hits"],
        "valid_records": len(good),
        "invalid_records": len(errors) - len(fetch_errors),
        "failed_pages": len(fetch_errors),
    }
    with open("output/run-report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(report)