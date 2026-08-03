import { chromium } from "playwright";
import fs from "fs/promises";
import path from "path";

const BASE_URL = "https://umamusu.wiki";

const teamsScript = await fs.readFile("./scrap_teams.js", "utf8");
const characterScript = await fs.readFile("./scrap_character.js", "utf8");

const browser = await chromium.launch({
	headless: false,
});

const page = await browser.newPage();

async function scrapTeams() {
	await page.goto(`${BASE_URL}/Teams_and_Clubs`);

	return await page.evaluate((script) => {
		eval(script);
		return scrapTeams();
	}, teamsScript);
}

async function scrapCharacter(href) {
	await page.goto(href);

	return page.evaluate((script) => {
		eval(script);
		return scrapCharacter();
	}, characterScript);
}

async function downloadOutfits(name, outfits) {
	const folder = path.join("outfits", name);

	await fs.mkdir(folder, { recursive: true });

	for (const outfit of outfits) {
		const ext = path.extname(new URL(outfit.url).pathname);
		const filename = `${outfit.name}${ext}`;
		const filepath = path.join(folder, filename);

		try {
			await fs.access(filepath);
			continue;
		} catch {}

		const response = await fetch(outfit.url);
		const buffer = Buffer.from(await response.arrayBuffer());

		await fs.writeFile(filepath, buffer);
	}
}

// start

const teams = await scrapTeams();

const characters = new Map();

for (const team of teams) {
	for (const member of team.members) {
		// trust href more than names for duplicates
		characters.set(member.href, member);
	}
}

const characterData = {};

const gameIds = JSON.parse(fs.readFileSync("game_ids.json", "utf-8"));

for (const { name, href } of characters.values()) {
	console.log(`Scrapping ${name}`);
	const data = await scrapCharacter(href);
	data.url = href;
	if (characterData[name]) {
		// we thus have to make sure there are no duplicate name with different urls
		throw new Error(`Duplicate character name: ${name}`);
	}
	if (gameIds[name] !== undefined) {
		data.game_id = gameIds[name];
	}
	characterData[name] = data;
	await downloadOutfits(name, data.outfits);
}

for (const team of teams) {
	// keep only name to find it inside characters.json
	// and role because it's unique to the team
	team.members = team.members.map(({ name, role }) => ({
		name,
		...(role ? { role } : {}),
	}));
}

await fs.writeFile("characters.json", JSON.stringify(characterData, null, 4), "utf8");
await fs.writeFile("teams.json", JSON.stringify(teams, null, 4), "utf8");

await browser.close();

console.log("Done");
