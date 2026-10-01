## Target classification

**Site:** Books to Scrape (https://books.toscrape.com)

**Why this site:** The site's front page (books.toscrape.com) describes itself
as "a safe place for beginners learning web scraping." That's the
permission this assignment relies on — a site built for practice.

**robots.txt check:** Requested https://books.toscrape.com/robots.txt on
[DATE] → 404 Not Found. No robots file found. This tells us the file
doesn't exist — it does not by itself mean scraping is allowed. Permission
here comes from the front-page statement above, not from the absence of
a robots file.

**Scope:** First 3 catalogue pages only.

**Data collected:** Product name, product description, product
information (type, price incl. tax, availability).

**Why this is appropriate:** I only collect data I'll actually use, and
I don't touch anything tied to real people without their say-so — even
if it's public.

---

I will not reuse this code on another site without checking its rules
and terms first.


# Books Scraper: a polite, careful scraper

A small scraper for books.toscrape.com. It collects 60 books, validates each one, and writes a clean JSON file and a report of what happened.

## Target classification
- **Site:** books.toscrape.com, a practice site whose own text calls it a safe place for learning scraping.
- **robots.txt:** returned 404. I treat that as silence, not permission.
- **Scope:** the first 3 catalogue pages, 60 books.
- **Lane:** [YOUR STAGE 0 LANE, e.g. plain HTTP requests + BeautifulSoup, no browser]

## Install and run
```bash
pip install -r requirements.txt
python main.py
```
Output goes to `output/books.json`, `output/errors.json` and `output/run-report.json`. A fresh clone fetches 60 pages with a short delay between requests, so it takes a few minutes.

## Record schema
| Field | Type | Notes |
|---|---|---|
| title | text | required |
| product_url | text | required, must start with https://, the record's identity |
| price_text | text | raw value, e.g. "£51.77" |
| price_gbp | number | clean value, e.g. 51.77 |
| availability_text | text | required |
| rating_text | One to Five | required |
| description | text | optional, null if the page has none |
| source_page | text | catalogue page it was found on |
| fetched_at | text | UTC time of the fetch |

A record that fails validation goes to `errors.json` with the reason. It never reaches `books.json`.

## Politeness rules
- Named user-agent with a link to this repo.
- Delay of [YOUR DELAY]s between real requests.
- Timeout of [YOUR TIMEOUT]s on every request.
- Cache-first. A page already saved is never fetched again.
- One retry on a timeout or a 5xx. No retry on a 404 or a 403.
- One bad page is logged and skipped. The run keeps going.
- Reruns are safe. Records are stored by `product_url`, so 60 stays 60.

## Sample run report
```json
{
  "started_at": "2026-09-30T14:37:54Z",
  "duration_seconds": 1.63,
  "pages_fetched": 0,
  "cache_hits": 60,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}

This run was a rerun, so all 60 pages came from the cache. A first run on a fresh clone shows pages_fetched: 60
```

## Why no browser
The data is already in the HTML the server sends, so a browser would only add cost.

## Ethics
[WRITE THIS IN YOUR OWN WORDS. Cover three things: use an official API when one exists, never get around logins, paywalls or blocks, and only collect what you need. Draft: "If a site has an official API, I use that first. If a site blocks me or puts something behind a login or a paywall, I stop. I only take the data I need."]

## Limitation
The cache never refreshes. If a price changes on the site, this scraper won't see it until the cached page is deleted. [ADD YOUR OWN if you found another.]