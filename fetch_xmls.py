import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup


def get_categorized_characters() -> dict[str, list[str]]:
	url = "https://umamusu.wiki/w/api.php?" + urllib.parse.urlencode(
		{
			"action": "parse",
			"page": "List_of_Characters",
			"prop": "text",
			"format": "json",
		}
	)

	req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
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


def fetch_xml(page_title: str) -> str:
	formatted_name = urllib.parse.quote(page_title.replace(" ", "_"))
	url = f"https://umamusu.wiki/w/index.php?title=Special:Export&pages={formatted_name}&wpDownload=1&action=submit"

	req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
	with urllib.request.urlopen(req) as response:
		return response.read().decode("utf-8")


def main():
	xml_dir = pathlib.Path("xmls")
	xml_dir.mkdir(exist_ok=True)

	jsons_dir = pathlib.Path("jsons")
	jsons_dir.mkdir(exist_ok=True)

	existing_characters = set()
	characters_json = jsons_dir / "characters.json"
	if characters_json.exists():
		try:
			with open(characters_json, encoding="utf-8") as f:
				existing_characters = set(json.load(f).keys())
		except (json.JSONDecodeError, OSError):
			pass

	teams_xml_path = xml_dir / "Teams_and_Clubs.xml"
	if not teams_xml_path.exists():
		print("Downloading XML for Teams and Clubs...")
		try:
			xml_data = fetch_xml("Teams_and_Clubs")
			teams_xml_path.write_text(xml_data, encoding="utf-8")
		except urllib.error.URLError as e:
			print(f"Failed to fetch Teams and Clubs: {e}")
		time.sleep(1.0)

	categorized = get_categorized_characters()

	with open(jsons_dir / "categories.json", "w", encoding="utf-8") as f:
		json.dump(categorized, f, indent=4, ensure_ascii=False)

	for names in categorized.values():
		for name in names:
			if name in existing_characters:
				continue

			safe_filename = name.replace("/", "_") + ".xml"
			filepath = xml_dir / safe_filename

			if filepath.exists():
				continue

			print(f"Downloading XML for {name}...")
			try:
				xml_data = fetch_xml(name)
				filepath.write_text(xml_data, encoding="utf-8")
			except urllib.error.URLError as e:
				print(f"Failed to fetch {name}: {e}")

			time.sleep(1.0)


if __name__ == "__main__":
	main()
