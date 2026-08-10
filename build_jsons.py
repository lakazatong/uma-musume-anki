import json
import pathlib
import re
import xml.etree.ElementTree as ET
from typing import Any

import mwparserfromhell

from utils import normalize_filename


def parse_character_templates(xml_data: str) -> dict:
	root = ET.fromstring(xml_data)
	ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""

	result = {}

	for page in root.findall(f"{ns}page"):
		for revision in page.findall(f"{ns}revision"):
			text_elem = revision.find(f"{ns}text")
			if text_elem is None or not text_elem.text:
				continue

			parsed = mwparserfromhell.parse(text_elem.text)
			for template in parsed.filter_templates():
				name = str(template.name.strip())
				params = {str(param.name.strip()): str(param.value.strip()) for param in template.params}

				if name not in result:
					result[name] = []
				result[name].append(params)

	return result


def clean_wikitext_line(line: str) -> str:
	line = re.sub(r"<ref.*?>.*?</ref>", "", line, flags=re.DOTALL)
	line = re.sub(r"<ref.*?>", "", line)
	line = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", line)
	line = re.sub(r"\[https?://\S+\s+([^\]]+)\]", r"\1", line)
	line = re.sub(r"\[https?://\S+\]", "", line)
	line = re.sub(r"'''?", "", line)
	line = re.sub(r"^\*+\s*", "", line)
	return line.strip()


def clean_role_name(raw_role: str) -> str:
	cleaned = raw_role.strip().lower()
	if cleaned in ("members", "team members"):
		return "Member"
	words = cleaned.replace("-", " ").replace("_", " ").split()
	return " ".join(w.capitalize() for w in words) if words else "Member"


def parse_teams_and_clubs(filepath: pathlib.Path) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
	if not filepath.exists():
		return {}, {}

	xml_data = filepath.read_text(encoding="utf-8")
	root = ET.fromstring(xml_data)
	ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""

	text_elem = root.find(f".//{ns}text")
	if text_elem is None or not isinstance(text_elem.text, str):
		return {}, {}

	wikitext = text_elem.text

	teams_data: dict[str, dict[str, Any]] = {}
	character_to_teams: dict[str, list[str]] = {}

	current_category = ""
	current_team_obj: dict[str, Any] | None = None
	current_team_name = ""
	current_role = ""

	for line in wikitext.splitlines():
		line_str = line.strip()
		if not line_str:
			continue

		h1_match = re.match(r"^=\s*([^=]+)\s*=$", line_str)
		if h1_match:
			current_category = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", h1_match.group(1)).strip()
			current_team_obj = None
			current_team_name = ""
			current_role = ""
			continue

		h2_match = re.match(r"^==\s*([^=]+)\s*==$", line_str)
		if h2_match:
			team_title = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", h2_match.group(1)).strip()
			if team_title.lower() in ("references", "see also"):
				current_team_obj = None
				current_team_name = ""
				current_role = ""
				continue

			current_team_name = team_title
			current_role = ""

			teams_data.setdefault(current_category, {})
			current_team_obj = {"members": {}}
			teams_data[current_category][current_team_name] = current_team_obj
			continue

		h3_match = re.match(r"^===\s*([^=]+)\s*===$", line_str)
		if h3_match and current_team_obj:
			current_role = h3_match.group(1).strip()
			continue

		if not current_team_obj or not current_role:
			continue

		if current_role.lower() == "notes":
			if line_str.startswith("*"):
				cleaned = clean_wikitext_line(line_str)
				if cleaned:
					current_team_obj.setdefault("notes", []).append(cleaned)
		else:
			icon_matches = re.findall(r"\{\{Character Round Icon\|([^}]+)\}\}", line_str)
			for icon_content in icon_matches:
				parts = [p.strip() for p in icon_content.split("|")]
				char_name = parts[0]
				if char_name.startswith(("IRL:", "Game:")) and len(parts) > 1:
					char_name = parts[1]
				else:
					char_name = re.sub(r"^(IRL:|Game:)", "", char_name)

				char_name = char_name.strip()
				if char_name:
					formatted_role = clean_role_name(current_role)
					current_team_obj["members"][char_name] = formatted_role

					if char_name not in character_to_teams:
						character_to_teams[char_name] = []

					if current_team_name not in character_to_teams[char_name]:
						character_to_teams[char_name].append(current_team_name)

	return teams_data, character_to_teams


def parse_nickname_entry(raw_nick: str) -> dict[str, str]:
	raw_nick = raw_nick.strip()
	outer_match = re.match(r"^(.*?)\s*[\(\（](.*?)[\)\）]$", raw_nick)
	if not outer_match:
		return {"en": raw_nick}

	jp_part = outer_match.group(1).strip()
	rest_part = outer_match.group(2).strip()

	inner_match = re.match(r"^(.*?)\s*[\(\（](.*?)[\)\）]$", rest_part)
	if inner_match:
		en_part = inner_match.group(1).strip()
		from_part = inner_match.group(2).strip()
		res = {"en": en_part, "jp": jp_part}
		if from_part:
			res["from"] = from_part
		return res

	return {"en": rest_part, "jp": jp_part}


def split_bilingual_list(en_str: str, jp_str: str) -> list[dict[str, str]]:
	en_items = [s.strip() for s in re.split(r",", en_str) if s.strip()]
	jp_items = [s.strip() for s in re.split(r"[、,]", jp_str) if s.strip()]

	result = []
	for i in range(max(len(en_items), len(jp_items))):
		item = {}
		if i < len(en_items):
			item["en"] = en_items[i]
		if i < len(jp_items):
			item["jp"] = jp_items[i]
		if item:
			result.append(item)
	return result


def parse_call_entry(val: str) -> dict[str, str] | list[dict[str, str]]:
	clean_val = re.sub(r"<br\s*/?>", "\n", val, flags=re.IGNORECASE)
	lines = [line.strip() for line in clean_val.split("\n") if line.strip()]

	parsed_entries = []
	for line in lines:
		match = re.match(r"^(.*?)\s*[\(\（](.*?)[\)\）]$", line)
		if match:
			jp_part, en_part = match.group(1).strip(), match.group(2).strip()
			entry = {}
			if en_part:
				entry["en"] = en_part
			if jp_part:
				entry["jp"] = jp_part
			parsed_entries.append(entry)
		else:
			parsed_entries.append({"jp": line})

	if len(parsed_entries) == 1:
		return parsed_entries[0]
	return parsed_entries


def transform_character_data(
	raw_templates: dict,
	teams: list[str],
	categorical_maps: dict[str, dict[str, list[str]]],
	char_name: str,
) -> dict[str, Any]:
	allowed_templates = (
		"Character",
		"Character Profile",
		"Character_Profile",
		"Character Discography",
		"Character_Discography",
	)

	character_data: dict[str, Any] = {}
	excluded_keys = {
		# redundant
		"media",  # with category
		# we have a separate table for it
		"category",
		"type",
		"dorm",
		"class",
		# specific to the wiki
		"previous",
		"next",
		# can be deduced from name
		"irl_page",
		"game_page",
		"partydash_page",
	}

	image_key_map = {
		"image_main": "main",
		"image_race": "race",
		"image_proto": "proto",
		"image_stage": "stage",
		"icon": "icon",
	}

	for template_name in allowed_templates:
		if template_name not in raw_templates:
			continue

		for template_params in raw_templates[template_name]:
			for key, val in template_params.items():
				if not isinstance(val, str):
					continue

				val = val.strip()
				if not val:
					continue

				val = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", val)

				if key in image_key_map:
					character_data.setdefault("images", {})[image_key_map[key]] = val
					continue

				if key in ("calls_self", "calls_trainer"):
					character_data[key] = parse_call_entry(val)
					continue

				if key == "class" and val == 'Unknown (listed as "???" in-game)':
					val = "Unknown"
				elif key == "dorm" and val.lower() == "lives alone":
					val = "Lives Alone"
				elif key == "type":
					val = val.lower()

				if key in ("type", "dorm", "class"):
					categorical_maps[key].setdefault(val, [])
					if char_name not in categorical_maps[key][val]:
						categorical_maps[key][val].append(char_name)
					continue

				if key in excluded_keys:
					continue

				parsed_val: Any
				if key in ("game_id", "height") and val.isdigit():
					parsed_val = int(val)
				elif key == "teams":
					parsed_val = [item.strip() for item in val.replace("\n", ",").split(",") if item.strip()]
				elif key == "nicknames":
					clean_val = re.sub(r"<br\s*/?>", "\n", val, flags=re.IGNORECASE)
					raw_list = [item.strip() for item in re.split(r"[\n,]", clean_val) if item.strip()]
					parsed_val = [parse_nickname_entry(item) for item in raw_list]
				else:
					parsed_val = val

				character_data[key] = parsed_val

	if teams:
		character_data["teams"] = teams

	name_map = {}
	for sub_key in ("jp", "ro", "tcn", "scn", "kr"):
		raw_k = f"name_{sub_key}"
		if raw_k in character_data:
			name_map[sub_key] = character_data.pop(raw_k)
	if name_map:
		character_data["name"] = name_map

	irl_map = {}
	if "name_hkjc" in character_data:
		irl_map["hkjc"] = character_data.pop("name_hkjc")
	if "birthday" in character_data:
		irl_map["birthday"] = character_data.pop("birthday")
	if "seiyuu" in character_data:
		irl_map["seiyuu"] = character_data.pop("seiyuu")
	if irl_map:
		character_data["irl"] = irl_map

	for list_field in ("strengths", "weaknesses"):
		jp_val = character_data.pop(f"{list_field}_jp", "")
		en_val = character_data.pop(list_field, "")
		if en_val or jp_val:
			character_data[list_field] = split_bilingual_list(en_val, jp_val)

	secrets = []
	i = 1
	while f"secret{i}" in character_data or f"secret{i}_jp" in character_data:
		sec_obj = {}
		if f"secret{i}" in character_data:
			sec_obj["en"] = character_data.pop(f"secret{i}")
		if f"secret{i}_jp" in character_data:
			sec_obj["jp"] = character_data.pop(f"secret{i}_jp")
		if sec_obj:
			secrets.append(sec_obj)
		i += 1
	if secrets:
		character_data["secrets"] = secrets

	jp_keys = [k for k in list(character_data.keys()) if k.endswith("_jp")]
	for jp_key in jp_keys:
		base_key = jp_key[:-3]
		jp_val = character_data.pop(jp_key)
		en_val = character_data.pop(base_key, None)

		bilingual_obj = {}
		if en_val is not None:
			bilingual_obj["en"] = en_val
		if jp_val is not None:
			bilingual_obj["jp"] = jp_val

		character_data[base_key] = bilingual_obj

	return character_data


def main():
	xml_dir = pathlib.Path("xmls")
	jsons_dir = pathlib.Path("jsons")
	jsons_dir.mkdir(exist_ok=True)

	categories_file = jsons_dir / "categories.json"

	if not categories_file.exists():
		print("Error: jsons/categories.json not found. Run fetch_xmls.py first.")
		return

	teams_xml_path = xml_dir / "Teams_and_Clubs.xml"
	teams_data, character_to_teams = parse_teams_and_clubs(teams_xml_path)

	if teams_data:
		with open(jsons_dir / "teams.json", "w", encoding="utf-8") as f:
			json.dump(teams_data, f, indent=4, ensure_ascii=False)
		print(f"Generated teams.json with {len(teams_data)} categories.")

	with open(categories_file, encoding="utf-8") as f:
		categorized: dict[str, list[str]] = json.load(f)

	all_characters = {}
	categorical_maps = {
		"type": {},
		"dorm": {},
		"class": {},
	}

	for names in categorized.values():
		for name in names:
			safe_filename = normalize_filename(name)
			filepath = xml_dir / safe_filename

			if not filepath.exists():
				print(f"Warning: XML file for {name} missing ({safe_filename}), skipping...")
				continue

			try:
				xml_data = filepath.read_text(encoding="utf-8")
				raw_templates = parse_character_templates(xml_data)
				character_teams = character_to_teams.get(name) or []
				all_characters[name] = transform_character_data(raw_templates, character_teams, categorical_maps, name)
			except (ET.ParseError, UnicodeDecodeError) as e:
				print(f"Failed to parse XML for {name}: {e}")

	with open(jsons_dir / "characters.json", "w", encoding="utf-8") as f:
		json.dump(all_characters, f, indent=4, ensure_ascii=False)

	for cat_key, cat_map in categorical_maps.items():
		out_filename = "classes.json" if cat_key == "class" else f"{cat_key}s.json"
		with open(jsons_dir / out_filename, "w", encoding="utf-8") as f:
			json.dump(cat_map, f, indent=4, ensure_ascii=False)

	print(f"Generated characters.json with {len(all_characters)} characters and relational JSON tables in jsons/.")


if __name__ == "__main__":
	main()
