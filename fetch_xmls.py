import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from utils import normalize_filename

USER_AGENT = "UmaMusumeAnkiFetcher/1.0 (https://github.com/lakazatong/uma-musume-anki; lakazatong@outlook.com) Python-urllib/3.12"


def get_categorized_characters() -> dict[str, list[str]]:
	url = "https://umamusu.wiki/w/api.php?" + urllib.parse.urlencode(
		{
			"action": "parse",
			"page": "List_of_Characters",
			"prop": "text",
			"format": "json",
		}
	)

	req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
	with urllib.request.urlopen(req) as response:
		data = json.loads(response.read().decode("utf-8"))

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
	params = {"action": "query", "format": "json", "export": "1", "exportnowrap": "1", "titles": "|".join(page_titles)}
	url = "https://umamusu.wiki/w/api.php?" + urllib.parse.urlencode(params)

	req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
	with urllib.request.urlopen(req) as response:
		return response.read().decode("utf-8")


def main():
	xml_dir = pathlib.Path("xmls")
	xml_dir.mkdir(exist_ok=True)

	jsons_dir = pathlib.Path("jsons")
	jsons_dir.mkdir(exist_ok=True)

	teams_xml_path = xml_dir / "Teams_and_Clubs.xml"
	if not teams_xml_path.exists():
		print("Downloading XML for Teams and Clubs...")
		try:
			xml_data = fetch_xml_batch(["Teams_and_Clubs"])
			teams_xml_path.write_text(xml_data, encoding="utf-8")
		except urllib.error.URLError as e:
			print(f"Failed to fetch Teams and Clubs: {e}")
		time.sleep(1.0)

	categorized = get_categorized_characters()

	with open(jsons_dir / "categories.json", "w", encoding="utf-8") as f:
		json.dump(categorized, f, indent=4, ensure_ascii=False)

	titles_to_fetch = []
	for names in categorized.values():
		for name in names:
			safe_filename = normalize_filename(name)
			if (xml_dir / safe_filename).exists():
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

			namespace = ""
			if "}" in root.tag:
				ns_uri = root.tag.split("}")[0][1:]
				ET.register_namespace("", ns_uri)
				namespace = f"{{{ns_uri}}}"

			siteinfo = root.find(f"{namespace}siteinfo")

			for page in root.findall(f"{namespace}page"):
				title_elem = page.find(f"{namespace}title")
				if title_elem is not None and title_elem.text:
					safe_filename = normalize_filename(title_elem.text)
					filepath = xml_dir / safe_filename

					new_root = ET.Element(root.tag, root.attrib)
					if siteinfo is not None:
						new_root.append(siteinfo)
					new_root.append(page)

					tree = ET.ElementTree(new_root)
					tree.write(filepath, encoding="utf-8", xml_declaration=True)

		except urllib.error.URLError as e:
			print(f"Failed to fetch batch {i // batch_size + 1}: {e}")
		except ET.ParseError as e:
			print(f"Failed to parse XML for batch {i // batch_size + 1}: {e}")

		time.sleep(1.0)


if __name__ == "__main__":
	main()
