import json
import time

import requests

from common.config import API_URL
from common.config import BASE_HEADERS as HEADERS

# Set to None when you want to run all ~2,127 skills
MAX_SKILLS = None
BATCH_SIZE = 20


def get_all_skill_ids():
	"""Pages Cargo database to collect all valid skill IDs."""
	skill_ids = []
	offset = 0
	limit = 500

	while True:
		params = {
			"action": "cargoquery",
			"tables": "Game_Skills",
			"fields": "skill_id",
			"limit": str(limit),
			"offset": str(offset),
			"format": "json",
		}
		res = requests.get(API_URL, params=params, headers=HEADERS).json()
		results = res.get("cargoquery", [])

		if not results:
			break

		for item in results:
			sid = item.get("title", {}).get("skill id")
			if sid:
				skill_ids.append(sid)

		if len(results) < limit:
			break

		offset += limit
		time.sleep(0.1)

	return sorted(set(skill_ids))


def fetch_skill_details(skill_ids, batch_size=20):
	"""Renders skillPage + effectsTables per ID and builds a dictionary keyed by ID."""
	detailed_data = {}

	for i in range(0, len(skill_ids), batch_size):
		batch = skill_ids[i : i + batch_size]

		# Plain text header delimiter (MediaWiki cannot strip this)
		wikitext_blocks = [
			f"===SKILL_ID:{sid}===\n"
			f"{{{{#invoke:Game/Skills|skillPage|{sid}}}}}\n"
			f"{{{{#invoke:Game/Skills|effectsTables|{sid}}}}}"
			for sid in batch
		]

		payload = "\n".join(wikitext_blocks)
		data_params = {
			"action": "expandtemplates",
			"text": payload,
			"prop": "wikitext",
			"format": "json",
		}

		res = requests.post(API_URL, data=data_params, headers=HEADERS)

		if res.status_code != 200:
			print(f"HTTP {res.status_code} error at index {i}, skipping batch...")
			continue

		try:
			rendered_text = res.json().get("expandtemplates", {}).get("wikitext", "")
			parts = rendered_text.split("===SKILL_ID:")

			batch_added = 0
			for part in parts:
				if not part.strip():
					continue
				lines = part.split("===", 1)
				if len(lines) == 2:
					sid = lines[0].strip()
					html_content = lines[1].strip()
					detailed_data[sid] = html_content
					batch_added += 1

			progress = min(i + batch_size, len(skill_ids))
			print(f"[{progress}/{len(skill_ids)}] Extracted {batch_added} skills from batch.")

		except json.decoder.JSONDecodeError:
			print(f"Failed to decode JSON response for batch starting at {i}")

		time.sleep(0.1)

	return detailed_data


if __name__ == "__main__":
	print("Fetching skill IDs from Cargo...")
	all_ids = get_all_skill_ids()
	print(f"Found {len(all_ids)} total skill IDs.")

	# Slice list if MAX_SKILLS limit is set
	target_ids = all_ids[:MAX_SKILLS] if MAX_SKILLS else all_ids
	print(f"Processing {len(target_ids)} skills...")

	skills_dict = fetch_skill_details(target_ids, batch_size=BATCH_SIZE)

	output_file = "skills.json"
	with open(output_file, "w", encoding="utf-8") as f:
		json.dump(skills_dict, f, ensure_ascii=False, indent=2)

	print(f"\nSaved {len(skills_dict)} skills to '{output_file}'.")
	print("Sample dictionary keys:", list(skills_dict.keys())[:5])
