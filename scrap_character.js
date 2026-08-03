function normalizeName(name) {
	return name.replaceAll(/[\/\\:*?"<>|]/g, "-");
}

function scrapOutfits() {
	const tabs = [...document.querySelectorAll(".tabber__tabs .tabber__tab")];
	const files = [...document.querySelectorAll(".tabber__panel .mw-file-description")];

	if (tabs.length !== files.length) {
		throw new Error(`Outfit mismatch: ${tabs.length} tabs, ${files.length} files`);
	}

	return Promise.all(
		tabs.map(async (tab, i) => {
			const filePage = await fetch(files[i].href).then((r) => r.text());
			const doc = new DOMParser().parseFromString(filePage, "text/html");

			const internal = doc.querySelector(".internal");

			if (!internal) {
				throw new Error(`No internal image found for ${tab.textContent}`);
			}

			return {
				name: tab.textContent.trim(),
				url: new URL(internal.href, location.origin).href,
			};
		}),
	);
}

async function scrapCharacter() {
	const character = {};

	const table = document.querySelector(".infobox");
	if (!table) return character;

	for (const tr of table.querySelectorAll("tr")) {
		const cells = tr.querySelectorAll("td");
		if (cells.length !== 2) continue;

		const key = cells[0].textContent.trim();
		const value = cells[1];

		switch (key) {
			case "Japanese":
				character.japanese = value.textContent.trim();
				break;

			case "Nicknames":
				character.nicknames = value.innerHTML
					.split(/<br\s*\/?>/)
					.map((x) => x.replace(/<[^>]*>/g, "").trim())
					.filter(Boolean);
				break;

			case "Birthday":
				character.birthday = value.textContent.trim();
				break;

			case "Height":
				character.height = value.textContent.trim();
				break;

			case "Dorm":
				character.dorm = value.textContent.trim();
				break;

			case "Roommate":
				character.roommate = normalizeName(value.querySelector("a")?.title);
				break;

			case "Voice Actor":
				character.voiceActor = normalizeName(value.querySelector("a")?.title);
				break;
		}
	}

	const title = document.querySelector(".infobox .infobox-subheader i");
	if (title) character.title = title.textContent.replace(/^"|"$/g, "");
	character.outfits = await scrapOutfits();

	return character;
}
