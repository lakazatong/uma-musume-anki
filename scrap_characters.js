function normalizeName(name) {
	return name.replaceAll(/[\/\\:*?"<>|]/g, "-").trim();
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

function parseCharacterTemplate(source) {
	const match = source.match(/\{\{Character\b([\s\S]*?)\}\}/);
	if (!match) {
		throw new Error("Character template not found");
	}

	const fields = {};

	for (const line of match[1].split(/\r?\n/)) {
		const match = line.match(/^\s*\|\s*([^=]+?)\s*=\s*(.*?)\s*$/);
		if (match) {
			fields[match[1].trim()] = match[2].trim();
		}
	}

	return fields;
}

function scrapCharacter() {
	const source = document.querySelector("#wpTextbox1").value;
	const fields = parseCharacterTemplate(source);

	return {
		...fields,
		game_id: Number.parseInt(fields.game_id, 10),
		nicknames: fields.nicknames
			?.split(/<br\s*\/?>/)
			.map((x) => x.trim())
			.filter(Boolean),
		solo_song: fields.solo_song?.slice(2, 2),
		seiyuu: fields.seiyuu?.slice(2, -2),
	};
}

function scrapCharacters() {
	return [
		...document
			.querySelector(".mw-content-ltr.mw-parser-output")
			.querySelectorAll("div.mw-heading2"),
	]
		.map((heading) => {
			const next = heading.nextElementSibling;
			return [
				heading,
				next?.tagName === "DIV" && !next.matches(".mw-heading2") ? next : null,
			];
		})
		.filter(([history, e]) => !!e)
		.map(([heading, e]) => ({
			category: heading.textContent.trim(),
			characters: [...e.querySelectorAll(".icon-box")],
		}))
		.map(({ category, characters }) => ({
			category,
			characters: characters.map((character) => {
				const link = character.querySelector(".name-box a");

				return {
					name: normalizeName(link.title),
					url: link.href,
				};
			}),
		}));
}
