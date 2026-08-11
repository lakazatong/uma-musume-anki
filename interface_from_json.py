import json
from collections import defaultdict

from common.config import PARSED_DIR


def analyze_schema(file_path, filter_fn=None, formatter_fn=None):
	with open(file_path, "r", encoding="utf-8") as f:
		data = json.load(f)

	if filter_fn is not None:
		data = {k: v for k, v in data.items() if filter_fn(k, v)}

	total_entries = len(data)
	if total_entries == 0:
		print("No entries matched the filter criteria.")
		return None

	key_counts = defaultdict(int)
	key_types = defaultdict(set)
	missing_entries = defaultdict(list)
	sub_schemas = {}

	for entry_key, entry in data.items():
		for key, value in entry.items():
			key_counts[key] += 1

			if isinstance(value, dict):
				key_types[key].add("dict")
				dicts = [value]
			elif isinstance(value, list) and any(isinstance(x, dict) for x in value):
				key_types[key].add("list[dict]")
				dicts = [x for x in value if isinstance(x, dict)]
			elif isinstance(value, list):
				elem_type = type(value[0]).__name__ if value else "any"
				key_types[key].add(f"list[{elem_type}]")
				dicts = []
			else:
				key_types[key].add(type(value).__name__)
				dicts = []

			if dicts:
				if key not in sub_schemas:
					sub_schemas[key] = {
						"parent_count": 0,
						"total_objects": 0,
						"sub_counts": defaultdict(int),
						"sub_types": defaultdict(set),
					}

				sub_schemas[key]["parent_count"] += 1
				sub_schemas[key]["total_objects"] += len(dicts)

				for d in dicts:
					for sub_key, sub_val in d.items():
						sub_schemas[key]["sub_counts"][sub_key] += 1
						sub_schemas[key]["sub_types"][sub_key].add(type(sub_val).__name__)

	all_keys = set(key_counts.keys())
	for entry_key, entry in data.items():
		for key in all_keys:
			if key not in entry:
				missing_entries[key].append(entry_key)

	analysis_result = {
		"total_entries": total_entries,
		"entries": data,
		"key_counts": key_counts,
		"key_types": key_types,
		"missing_entries": missing_entries,
		"sub_schemas": sub_schemas,
	}

	if formatter_fn is not None:
		return formatter_fn(analysis_result)

	return default_formatter(analysis_result)


def default_formatter(
	res,
	show_status=False,
	show_coverage=True,
	show_sub_schemas=True,
	outlier_threshold=None,
	outlier_extractor=None,
):
	total_entries = res["total_entries"]

	print(f"Total entries analyzed: {total_entries}\n")

	headers = ["Key", "Type(s)"]
	if show_status:
		headers.append("Status")
	if show_coverage:
		headers.append("Coverage")

	print(f"{headers[0]:<20} {headers[1]:<20}" + "".join(f" {h:<10}" for h in headers[2:]))
	print("-" * 65)

	for key in sorted(res["key_counts"].keys()):
		count = res["key_counts"][key]
		types = " | ".join(sorted(res["key_types"][key]))
		row = [f"{key:<20}", f"{types:<20}"]

		if show_status:
			status = "Optional" if count < total_entries else "Required"
			row.append(f"{status:<10}")
		if show_coverage:
			row.append(f"{count}/{total_entries}")

		print(" ".join(row))

	if outlier_threshold is not None:
		print("\n" + "=" * 65)
		print(f"Outliers (missing in <= {outlier_threshold} entries):\n")
		for key, missing in sorted(res["missing_entries"].items()):
			if 0 < len(missing) <= outlier_threshold:
				print(f"Key '{key}' missing in {len(missing)} entry/entries:")
				for entry_key in missing:
					entry = res["entries"][entry_key]
					info = outlier_extractor(entry_key, entry) if outlier_extractor else entry_key
					print(f"  - {entry_key}: {info}" if outlier_extractor else f"  - {entry_key}")
				print()

	if show_sub_schemas and res["sub_schemas"]:
		print("\n" + "=" * 65 + "\n")
		for parent_key in sorted(res["sub_schemas"].keys()):
			info = res["sub_schemas"][parent_key]
			parent_total = info["parent_count"]
			total_objs = info["total_objects"]

			print(
				f"Sub-schema for: '{parent_key}' (Present in {parent_total}/{total_entries} entries, {total_objs} total objects)"
			)
			print(
				f"{'Sub-key':<20} {'Type(s)':<20}"
				+ (" Status    " if show_status else "")
				+ (" Coverage" if show_coverage else "")
			)
			print("-" * 65)

			for sub_key in sorted(info["sub_counts"].keys()):
				sub_count = info["sub_counts"][sub_key]
				sub_types = " | ".join(sorted(info["sub_types"][sub_key]))
				row = [f"{sub_key:<20}", f"{sub_types:<20}"]
				if show_status:
					status = "Required" if sub_count == total_objs else "Optional"
					row.append(f"{status:<10}")
				if show_coverage:
					row.append(f"{sub_count}/{total_objs}")
				print(" ".join(row))
			print()


def print_outliers_only(res, max_missing=10, extractor=None):
	total = res["total_entries"]
	print(f"Outliers (missing in <= {max_missing} entries out of {total}):\n")

	found = False
	for key, missing in sorted(res["missing_entries"].items()):
		if 0 < len(missing) <= max_missing:
			found = True
			print(f"Key '{key}' (missing in {len(missing)}/{total}):")
			for entry_key in missing:
				entry = res["entries"][entry_key]
				label = extractor(entry_key, entry) if extractor else entry_key
				print(f"  - {label}")
			print()

	if not found:
		print(f"No keys found with <= {max_missing} missing entries.")


if __name__ == "__main__":

	def load_category_set(types_path, category):
		with open(types_path, "r", encoding="utf-8") as f:
			data = json.load(f)
		return set(data.get(category, []))

	def get_character_name(entry_key, entry):
		return entry_key

	horsegirls = load_category_set(PARSED_DIR / "types.json", "horsegirl")

	analyze_schema(
		PARSED_DIR / "characters.json",
		filter_fn=lambda key, val: key in horsegirls,
		formatter_fn=lambda res: print_outliers_only(res, max_missing=10, extractor=get_character_name),
	)
