import os
import random
from typing import cast

import genanki

from anki.model import model
from common.config import BASE_WIKI_URL
from common.utils import dorm_page, file_page, link_wrap, wiki_page


class StableNote(genanki.Note):
	@property
	def guid(self):
		fields = cast(list[str], self.fields)
		return genanki.guid_for("umamusume", fields[0])

	@guid.setter
	def guid(self, val):
		self._guid = val


class UmaDeck(genanki.Deck):
	def __init__(self, teams):
		random.seed("Umamusume Characters")
		super().__init__(
			random.randrange(1 << 30, 1 << 31),
			"Umamusume Characters",
		)
		self.teams = teams

	def get_images(self, name, character):
		folder = os.path.join("outfits", name)
		if not os.path.isdir(folder):
			raise FileNotFoundError("Missing", folder)

		outfit_fields = {
			"main": character.get("image_main"),
			"race": character.get("image_race"),
			"proto": character.get("image_proto"),
			"stage": character.get("image_stage"),
		}
		outfit_fields = {name: value for name, value in outfit_fields.items() if value}

		images = [x for x in os.listdir(folder) if x.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]

		expected = set(outfit_fields)
		actual = {os.path.splitext(x)[0].lower() for x in images}

		if actual != expected:
			missing = expected - actual
			unexpected = actual - expected

			if missing:
				raise RuntimeError(f"Missing outfits for {name}: {', '.join(sorted(missing))}")

			if unexpected:
				raise RuntimeError(f"Unexpected outfit files for {name}: {', '.join(sorted(unexpected))}")

		order = ["main", "race", "proto", "stage"]
		images_by_name = {os.path.splitext(x)[0].lower(): x for x in images}

		return outfit_fields, [images_by_name[outfit_name] for outfit_name in order if outfit_name in images_by_name]

	def get_character_teams(self, name, character):
		character_teams = []

		for team_name in character.get("teams", []):
			team = self.teams[team_name]
			role = next(member.get("role") for member in team["members"] if member["name"] == name) or "Member"

			anchor = team_name.replace(" ", "_")
			if team_name.endswith(" (DLC)"):
				anchor = anchor.replace("_(DLC)", "(DLC)")

			label = link_wrap(
				team_name,
				f"{BASE_WIKI_URL}/Teams_and_Clubs#{anchor}",
			)
			character_teams.append(f"{label} ({role})")

		return character_teams

	def add_character(self, name, character):
		# build outfit

		outfit_html = []
		outfit_fields, images = self.get_images(name, character)

		for i, image in enumerate(images):
			outfit_name = os.path.splitext(image)[0].lower()
			wiki_filename = outfit_fields[outfit_name]
			media_name = f"{name.replace(' ', '_')}_{image}"

			outfit_html.append(
				f"""
                <div class="outfit{"" if i == 0 else " hidden"}">
                    <img src="{media_name}">
                    <a class="outfit-file-link" href="{file_page(wiki_filename)}">
                        Image File
                    </a>
                </div>
                """
			)

		# build name

		# this way of displaying the character_type is temporary
		character_type = character.get("type", "unknown")
		name_html = f"[{character_type}] {
			link_wrap(
				name,
				character.get('url', wiki_page(name)),
			)
		}"

		# build attributes

		attributes = "<table class='infobox'>"

		def add_attr(label, value):
			nonlocal attributes
			assert value, f"No value for {label = }"
			attributes += f"""
				<tr>
					<td>{label}</td>
					<td>{value}</td>
				</tr>
			"""

		def add_opt_attr(label, value):
			if value:
				add_attr(label, value)

		def add_list_attr(singular, plural, values):
			if len(values) == 1:
				add_attr(singular, values[0])
			elif values:
				add_attr(
					plural,
					f"<ul>{''.join(f'<li>{x}</li>' for x in values)}</ul>",
				)

		def add_separator(label):
			nonlocal attributes
			attributes += f"""
				<tr class="separator">
					<th colspan="2">{label}</th>
				</tr>
			"""

		dorm = character.get("dorm")
		roommate = character.get("roommate")
		voice_actor = character.get("seiyuu")
		irl_page = character.get("irl_page")

		add_separator("Names")
		add_opt_attr("Title", character.get("epithet"))
		add_opt_attr("Japanese", character.get("name_jp"))
		add_opt_attr("Traditional Chinese", character.get("name_tcn"))
		add_opt_attr("Simplified Chinese", character.get("name_scn"))
		add_opt_attr("Korean", character.get("name_kr"))
		add_list_attr("Nickname", "Nicknames", character.get("nicknames", []))

		add_separator("Profile")
		add_opt_attr("Height", character.get("height"))
		add_opt_attr("Three Sizes", character.get("threesizes"))
		add_opt_attr("Shoe Size", character.get("shoesize"))

		add_separator("Social")
		add_opt_attr("Class", character.get("class"))
		add_opt_attr("Dorm", link_wrap(dorm, dorm_page(dorm)))
		add_opt_attr("Roommate", link_wrap(roommate, wiki_page(roommate)))
		add_list_attr("Team", "Teams", self.get_character_teams(name, character))
		add_opt_attr("Calls Self", character.get("calls_self"))
		add_opt_attr("Calls Trainer", character.get("calls_trainer"))

		add_separator("IRL")
		add_opt_attr("Birthday", character.get("birthday"))
		add_opt_attr("Voice Actor", link_wrap(voice_actor, wiki_page(voice_actor)))
		add_opt_attr("Hong Kong Jockey Club", character.get("name_hkjc"))
		add_opt_attr("IRL Page", link_wrap(irl_page.removeprefix("IRL:") if irl_page else None, wiki_page(irl_page)))

		add_separator("Other")
		add_opt_attr("Game ID", character.get("game_id"))

		attributes += "</table>"

		# build note

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
