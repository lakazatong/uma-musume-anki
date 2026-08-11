import json

import requests

from common.config import BASE_HEADERS, RAW_DIR

BASE_URL = "https://gametora.com"
MANIFEST_URL = f"{BASE_URL}/data/manifests/umamusume.json"

ENDPOINT = "umamusume/nicknames"
HEADERS = BASE_HEADERS.copy()
HEADERS["Referer"] = f"{BASE_URL}/{ENDPOINT}"


def fetch_raw_epithets():
	print("Fetching GameTora manifest...")
	res = requests.get(MANIFEST_URL, headers=HEADERS)

	if res.status_code != 200:
		print(f"Failed to fetch manifest. HTTP status: {res.status_code}")
		return

	manifest = res.json()
	nicknames_hash = manifest.get("nicknames")

	if not nicknames_hash:
		print("Error: 'nicknames' hash not found in manifest.")
		return

	json_url = f"{BASE_URL}/data/{ENDPOINT}.{nicknames_hash}.json"
	print(f"Fetching nicknames dataset from: {json_url}")

	data_res = requests.get(json_url, headers=HEADERS)
	if data_res.status_code == 200:
		titles_data = data_res.json()
		output_file = RAW_DIR / "epithets.json"
		with open(output_file, "w", encoding="utf-8") as f:
			json.dump(titles_data, f, ensure_ascii=False, indent=2)
		print(f"Successfully saved {len(titles_data)} raw epithets to '{output_file}'.")
	else:
		print(f"Failed to download JSON dataset. HTTP status: {data_res.status_code}")


if __name__ == "__main__":
	fetch_raw_epithets()
