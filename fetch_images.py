import json
import pathlib
import time
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def download_images():
	jsons_file = pathlib.Path("jsons/characters.json")
	if not jsons_file.exists():
		print("Error: jsons/characters.json not found.")
		return

	with open(jsons_file, encoding="utf-8") as f:
		characters = json.load(f)

	base_img_dir = pathlib.Path("images")
	base_img_dir.mkdir(exist_ok=True)

	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
		"Referer": "https://umamusu.wiki/",
	}

	for char_name, char_data in characters.items():
		images = char_data.get("images", {})
		if not images:
			continue
		assert isinstance(images, dict)

		safe_char_name = char_name.replace("/", "_")
		char_img_dir = base_img_dir / safe_char_name
		char_img_dir.mkdir(exist_ok=True)

		for img_type, raw_filename in images.items():
			assert isinstance(img_type, str) and isinstance(raw_filename, str)

			type_key = img_type.lower()
			if any(char_img_dir.glob(f"{type_key}.*")):
				continue

			filename = raw_filename.strip()
			if filename.lower().startswith("file:"):
				print("a")
				filename = filename[5:].strip()

			api_url = f"https://umamusu.wiki/w/api.php?action=query&titles=File:{quote(filename)}&prop=imageinfo&iiprop=url&redirects=1&format=json"

			try:
				api_req = Request(api_url, headers=headers)
				with urlopen(api_req) as resp:
					api_data = json.loads(resp.read().decode("utf-8"))

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

				img_req = Request(img_url, headers=headers)
				with urlopen(img_req) as resp, open(dest_file, "wb") as out_f:
					out_f.write(resp.read())
				print(f"Downloaded: {dest_file}")
				time.sleep(0.1)
			except (URLError, OSError) as e:
				print(f"Failed to download {filename}: {e}")


if __name__ == "__main__":
	download_images()
