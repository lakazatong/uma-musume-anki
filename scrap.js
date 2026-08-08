import { chromium } from "playwright";
import fs from "fs/promises";
import path from "path";

const BASE_URL = "https://umamusu.wiki";

const teamsScript = await fs.readFile("./scrap_teams.js", "utf8");
const charactersScript = await fs.readFile("./scrap_characters.js", "utf8");
const outfitScript = await fs.readFile("./scrap_outfit.js", "utf8");

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

async function scrapCharacters() {
	await page.goto(`${BASE_URL}/List_of_Characters`);

	return page.evaluate((script) => {
		eval(script);
		return scrapCharacters();
	}, charactersScript);
}

async function scrapCharacter(url) {
	await page.goto(`${url}/edit`);

	return page.evaluate((script) => {
		eval(script);
		return scrapCharacter();
	}, charactersScript);
}

async function scrapOutfit(url) {
	await page.goto(url);

	return page.evaluate((script) => {
		eval(script);
		return scrapOutfit();
	}, outfitScript);
}

async function downloadOutfits(name, data) {
	const folder = path.join("outfits", name);
	await fs.mkdir(folder, { recursive: true });

	const outfits = ["main", "race", "proto", "stage"].filter(
		(outfit_name) => data[`image_${outfit_name}`],
	);

	const files = await fs.readdir(folder);

	// avoid unnecessary navigation
	if (outfits.every((outfit_name) => files.some((file) => file.startsWith(`${outfit_name}.`))))
		return;

	for (const outfit_name of outfits) {
		const outfit_file = data[`image_${outfit_name}`];
		const file_url = `${BASE_URL}/File:${outfit_file.replaceAll(" ", "_")}`;

		const image_url = await scrapOutfit(file_url);
		const ext = path.extname(new URL(image_url).pathname);
		const filename = `${outfit_name}${ext}`;
		const filepath = path.join(folder, filename);

		try {
			await fs.access(filepath);
			continue;
		} catch {}

		const response = await fetch(image_url);

		if (!response.ok) {
			throw new Error(
				`Failed to download ${image_url}: ${response.status} ${response.statusText}`,
			);
		}

		const buffer = Buffer.from(await response.arrayBuffer());
		await fs.writeFile(filepath, buffer);
	}
}

// start

const teams = await scrapTeams();
const characters = await scrapCharacters();

const characterTeams = new Map();

for (const [teamName, team] of Object.entries(teams)) {
	const newMembers = [];
	for (const member of team.members) {
		const teamNames = characterTeams.get(member.name) ?? [];
		teamNames.push(teamName);
		characterTeams.set(member.name, teamNames);
		newMembers.push({
			name: member.name,
			...(member.role ? { role: member.role } : {}),
		});
	}
	team.members = newMembers;
}

let characterData = {};

try {
	characterData = JSON.parse(await fs.readFile("characters.json", "utf8"));
} catch (error) {
	if (error.code !== "ENOENT") {
		throw error;
	}
}
let i = 0;
let n = 10;

for (const category of characters) {
	for (const { name, url } of category.characters) {
		if (characterData[name]) continue;
		if (i >= n) break;
		i++;

		console.log(`Scrapping ${name}`);

		const data = await scrapCharacter(url);
		data.url = url;

		if (characterData[name]) {
			throw new Error(`Duplicate character name: ${name}`);
		}

		const teams = characterTeams.get(name);
		if (teams) {
			data.teams = teams;
		}

		characterData[name] = data;

		await downloadOutfits(name, data);
	}
}

await fs.writeFile("characters.json", JSON.stringify(characterData, null, 4), "utf8");
await fs.writeFile("teams.json", JSON.stringify(teams, null, 4), "utf8");

await browser.close();

console.log("Done");
