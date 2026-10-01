import json

with open("books.json") as f:  # or whatever your Stage 3 output file is called
    records = json.load(f)

print(len(records))  # sanity check — should be 60

missing = [r["product_url"] for r in records if not r.get("rating_text")]
print(f"{len(missing)} missing rating_text")
print(missing)