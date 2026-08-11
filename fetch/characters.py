import json
import time
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from common.config import API_URL, PARSED_DIR, RAW_DIR
from common.config import BASE_HEADERS as HEADERS
from common.utils import normalize_filename


def get_categorized_characters() -> dict[str, list[str]]:
	params = {
		"action": "parse",
		"page": "List_of_Characters",
		"prop": "text",
		"format": "json",
	}

	response = requests.get(API_URL, params=params, headers=HEADERS)
	response.raise_for_status()
	data = response.json()

	html_content = data["parse"]["text"]["*"]
	soup = BeautifulSoup(html_content, "html.parser")

	result = {}
	current_category = None

	for elem in soup.find_all(["h2", "a"]):
		if elem.name == "h2":
			headline = elem.find(class_="mw-headline")
			current_category = headline.get_text(strip=True) if headline else elem.get_text(strip=True)
			if current_category not in result and current_category != "Contents":
				result[current_category] = []
		elif elem.name == "a" and current_category:
			if elem.find_parent(class_="mw-editsection"):
				continue

			title = elem.get("title")
			if isinstance(title, str):
				if title.startswith(("Edit section", "Category:")):
					continue
				if title not in result[current_category]:
					result[current_category].append(title)

	return result


def fetch_xml_batch(page_titles: list[str]) -> str:
	params = {
		"action": "query",
		"format": "json",
		"export": "1",
		"exportnowrap": "1",
		"titles": "|".join(page_titles),
	}
	response = requests.get(API_URL, params=params, headers=HEADERS)
	response.raise_for_status()
	return response.text


def main():
	teams_xml_path = RAW_DIR / "Teams_and_Clubs.xml"
	if not teams_xml_path.exists():
		print("Downloading XML for Teams and Clubs...")
		xml_data = fetch_xml_batch(["Teams_and_Clubs"])
		teams_xml_path.write_text(xml_data, encoding="utf-8")
		time.sleep(1.0)

	categorized = get_categorized_characters()
	time.sleep(1.0)

	with open(PARSED_DIR / "categories.json", "w", encoding="utf-8") as f:
		json.dump(categorized, f, indent=4, ensure_ascii=False)

	def get_character_filepath(name):
		return RAW_DIR / "characters" / normalize_filename(name)

	titles_to_fetch = []
	for names in categorized.values():
		for name in names:
			if get_character_filepath(name).exists():
				continue

			if name not in titles_to_fetch:
				titles_to_fetch.append(name)

	batch_size = 50
	for i in range(0, len(titles_to_fetch), batch_size):
		batch = titles_to_fetch[i : i + batch_size]
		print(f"Downloading batch {i // batch_size + 1}/{(len(titles_to_fetch) + batch_size - 1) // batch_size}...")

		try:
			xml_data = fetch_xml_batch(batch)
			root = ET.fromstring(xml_data)
		except requests.RequestException as e:
			print(f"Failed to fetch batch {i // batch_size + 1}: {e}")
			continue

		time.sleep(1.0)

		try:
			namespace = ""
			if "}" in root.tag:
				ns_uri = root.tag.split("}")[0][1:]
				ET.register_namespace("", ns_uri)
				namespace = f"{{{ns_uri}}}"

			siteinfo = root.find(f"{namespace}siteinfo")

			for page in root.findall(f"{namespace}page"):
				title_elem = page.find(f"{namespace}title")
				if title_elem is not None and title_elem.text:
					filepath = get_character_filepath(title_elem.text)

					new_root = ET.Element(root.tag, root.attrib)
					if siteinfo is not None:
						new_root.append(siteinfo)
					new_root.append(page)

					tree = ET.ElementTree(new_root)
					tree.write(filepath, encoding="utf-8", xml_declaration=True)
		except ET.ParseError as e:
			print(f"Failed to parse XML for batch {i // batch_size + 1}: {e}")


if __name__ == "__main__":
	main()
