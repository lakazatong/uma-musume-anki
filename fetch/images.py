import json
import pathlib
import time

import requests

from common.config import API_URL, BASE_HEADERS, IMAGES_DIR, PARSED_DIR

HEADERS = BASE_HEADERS
HEADERS["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"


def download_images():
	jsons_file = PARSED_DIR / "characters.json"
	if not jsons_file.exists():
		print(f"Error: {jsons_file} not found.")
		return

	with open(jsons_file, encoding="utf-8") as f:
		characters = json.load(f)

	for char_name, char_data in characters.items():
		images = char_data.get("images", {})
		if not images:
			continue
		assert isinstance(images, dict)

		safe_char_name = char_name.replace("/", "_")
		char_img_dir = IMAGES_DIR / safe_char_name
		char_img_dir.mkdir(exist_ok=True)

		for img_type, raw_filename in images.items():
			assert isinstance(img_type, str) and isinstance(raw_filename, str)

			type_key = img_type.lower()
			if any(char_img_dir.glob(f"{type_key}.*")):
				continue

			filename = raw_filename.strip()
			if filename.lower().startswith("file:"):
				filename = filename[5:].strip()

			params = {
				"action": "query",
				"titles": "File:" + filename,
				"prop": "imageinfo",
				"iiprop": "url",
				"redirects": 1,
				"format": "json",
			}

			try:
				response = requests.get(API_URL, params=params, headers=HEADERS)
				response.raise_for_status()
				api_data = response.json()

				pages = api_data.get("query", {}).get("pages", {})
				img_url = None

				for page_data in pages.values():
					if page_data.get("imageinfo"):
						img_url = page_data["imageinfo"][0].get("url")
						break

				if not img_url:
					print(f"File not found on wiki: {filename}")
					continue

				if img_url.startswith("//"):
					img_url = f"https:{img_url}"

				ext = pathlib.Path(img_url).suffix.lower() or ".png"
				dest_file = char_img_dir / f"{type_key}{ext}"

				response = requests.get(img_url, headers=HEADERS)
				response.raise_for_status()

				with open(dest_file, "wb") as out_f:
					out_f.write(response.content)

				print(f"Downloaded: {dest_file}")
				time.sleep(0.1)

			except (requests.RequestException, OSError) as e:
				print(f"Failed to download {filename}: {e}")


if __name__ == "__main__":
	download_images()
