import json
import os

from common.config import PARSED_DIR


def main():
	chars_file = PARSED_DIR / "characters.json"
	epithets_file = PARSED_DIR / "epithets.json"

	if not os.path.exists(epithets_file):
		print(f"Error: Missing '{epithets_file}'. Run build_epithets.py first.")
		return

	with open(epithets_file, "r", encoding="utf-8") as f:
		all_epithets = json.load(f)

	# If characters.json exists, enrich it
	if os.path.exists(chars_file):
		with open(chars_file, "r", encoding="utf-8") as f:
			characters_data = json.load(f)

		# Build map of char_id -> secret epithets
		char_epithets_map = {}
		general_epithets = []

		for ep in all_epithets:
			cid = ep.get("char_id")
			# Strip char_id internal key before outputting
			ep_clean = {k: v for k, v in ep.items() if k != "char_id"}

			if cid:
				char_key = str(cid)
				if char_key not in char_epithets_map:
					char_epithets_map[char_key] = []
				char_epithets_map[char_key].append(ep_clean)
			else:
				general_epithets.append(ep_clean)

		# Attach inlined secret epithets into character objects
		inlined_count = 0
		for key, char in characters_data.items():
			# Check matching by character ID or internal ID
			char_id_str = str(char.get("id") or char.get("chara_id") or key)
			if char_id_str in char_epithets_map:
				char["secret_epithets"] = char_epithets_map[char_id_str]
				inlined_count += len(char_epithets_map[char_id_str])
			else:
				char["secret_epithets"] = []

		# Save enriched characters.json
		with open(chars_file, "w", encoding="utf-8") as f:
			json.dump(characters_data, f, ensure_ascii=False, indent=2)

		# Save flattened general epithets back to parsed/epithets.json
		with open(epithets_file, "w", encoding="utf-8") as f:
			json.dump(general_epithets, f, ensure_ascii=False, indent=2)

		print(f"Successfully inlined {inlined_count} character-specific epithets into '{chars_file}'.")
		print(f"Flattened '{epithets_file}' down to {len(general_epithets)} general epithets.")

	else:
		print(f"Note: '{chars_file}' not found. Cleaning temporary keys from '{epithets_file}'...")
		general_epithets = [
			{k: v for k, v in ep.items() if k != "char_id"} for ep in all_epithets if not ep.get("char_id")
		]
		with open(epithets_file, "w", encoding="utf-8") as f:
			json.dump(general_epithets, f, ensure_ascii=False, indent=2)
		print(f"Saved {len(general_epithets)} general epithets to '{epithets_file}'.")


if __name__ == "__main__":
	main()
