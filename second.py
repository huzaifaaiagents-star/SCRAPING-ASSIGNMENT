import os
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

url = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
response = requests.get(url, headers={"User-Agent": "FlyRankInternshipA9/1.0 (+your-repo-link)"}, timeout=5)
response.encoding = "utf-8"

soup = BeautifulSoup(response.text, "html.parser")
tag = soup.find("p", class_="star-rating")

print(type(tag["class"]))
print(tag["class"])