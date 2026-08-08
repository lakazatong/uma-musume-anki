import json
import os
import shutil

import genanki
from PIL import Image

from anki_deck import UmaDeck


def crop_transparent(src, dst):
	if src.lower().endswith((".jpg", ".jpeg")):
		shutil.copy2(src, dst)
	else:
		with Image.open(src) as img:
			img = img.convert("RGBA")

			bbox = img.getbbox()

			if bbox:
				img = img.crop(bbox)

			img.save(dst)

	with Image.open(dst) as img:
		return img.size


def main():
	with open("characters.json", encoding="utf8") as f:
		characters = json.load(f)

	with open("teams.json", encoding="utf8") as f:
		teams = json.load(f)

	deck = UmaDeck(teams)

	media_dir = ".anki_cropped_outfits"
	os.makedirs(media_dir, exist_ok=True)
	media = []

	for name in sorted(characters):
		folder = os.path.join("outfits", name)

		if not os.path.isdir(folder):
			continue

		for file in sorted(os.listdir(folder)):
			if not file.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
				continue

			src = os.path.abspath(os.path.join(folder, file))

			dst_name = f"{name.replace(' ', '_')}_{file}"
			dst = os.path.join(media_dir, dst_name)

			if not os.path.exists(dst):
				crop_transparent(src, dst)

			media.append(dst)

		character = characters[name]
		deck.add_character(name, character)

	package = genanki.Package(deck)
	package.media_files = media

	package.write_to_file("Umamusume Characters.apkg")


if __name__ == "__main__":
	main()
