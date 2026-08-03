import os
import random
from urllib.parse import urlparse

import genanki

from anki_model import model
from utils import file_page, link_wrap, wiki_page


class StableNote(genanki.Note):
	@property
	def guid(self):
		return genanki.guid_for("umamusume", self.fields[0])


class UmaDeck(genanki.Deck):
	def __init__(self):
		random.seed("Umamusume Characters")

		super().__init__(random.randrange(1 << 30, 1 << 31), "Umamusume Characters")

	def add_character(self, name, character, teams):
		folder = os.path.join("outfits", name)

		if not os.path.isdir(folder):
			return

		outfits = character["outfits"]

		expected = {x["name"]: x for x in outfits}

		images = [x for x in os.listdir(folder) if x.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
		for image in images:
			outfit_name = os.path.splitext(image)[0]

			if outfit_name not in expected:
				raise RuntimeError(f"Unexpected outfit file for {name}: {image}")

		if set(expected) != {os.path.splitext(x)[0] for x in images}:
			missing = set(expected) - {os.path.splitext(x)[0] for x in images}
			raise RuntimeError(f"Missing outfits for {name}: {', '.join(missing)}")

		images.sort()

		if "Main.png" in images:
			images.remove("Main.png")
			images.insert(0, "Main.png")

		outfit_html = []

		for i, image in enumerate(images):
			outfit = expected[os.path.splitext(image)[0]]
			wiki_filename = os.path.basename(urlparse(outfit["url"]).path)

			media_name = f"{name.replace(' ', '_')}_{image}"

			outfit_html.append(
				f"""
		<div class="outfit{"" if i == 0 else " hidden"}">
			<img src="{media_name}">
			<a class="outfit-file-link" href="{file_page(wiki_filename)}">Image File</a>
		</div>
		"""
			)

		attrs = []

		def add_attr(label, value):
			if value:
				attrs.append((label, value))

		add_attr("Japanese", character.get("japanese"))

		if character.get("nicknames"):
			add_attr("Nicknames", ", ".join(character["nicknames"]))

		add_attr("Title", character.get("title"))

		add_attr("Birthday", character.get("birthday"))

		add_attr("Height", character.get("height"))

		if character.get("dorm"):
			add_attr(
				"Dorm",
				link_wrap(
					character["dorm"],
					f"https://umamusu.wiki/Roommates/{character['dorm'].replace(' ', '_')}_Dorm",
				),
			)

		if character.get("roommate"):
			add_attr(
				"Roommate",
				link_wrap(character["roommate"], wiki_page(character["roommate"])),
			)

		character_teams = []

		for team in teams:
			for member in team.get("members", []):
				if member["name"] == name:
					role = member.get("role")

					label = team["name"]

					if role:
						label += f" ({role})"

					character_teams.append(
						link_wrap(
							label,
							f"https://umamusu.wiki/Teams_and_Clubs#{team['name'].replace(' ', '_')}",
						)
					)

		if character_teams:
			add_attr("Teams", ", ".join(character_teams))

		if character.get("voiceActor"):
			add_attr(
				"Voice Actor",
				link_wrap(character["voiceActor"], wiki_page(character["voiceActor"])),
			)

		if character.get("game_id"):
			add_attr("Game ID", character.get("game_id"))

		attributes = "<table class='infobox'>"

		for key, value in attrs:
			attributes += f"""
<tr>
<td><i>{key}</i></td>
<td>{value}</td>
</tr>
"""

		attributes += "</table>"

		name_html = link_wrap(name, character.get("url", wiki_page(name)))

		note = StableNote(
			model=model,
			fields=[
				name,
				"".join(outfit_html),
				name_html,
				attributes,
				"1" if len(images) > 1 else "",
			],
		)

		self.add_note(note)
