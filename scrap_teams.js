function scrapTeams() {
	// clear();

	const root = document.querySelector(".mw-content-ltr.mw-parser-output");

	const tree = { children: [] };
	const stack = [{ level: 0, node: tree }];

	[...root.children].forEach((el) => {
		const m = el.className.match(/\bmw-heading(\d)\b/);

		if (m) {
			const level = +m[1];
			const node = { el, level, children: [] };

			while (stack.at(-1).level >= level) stack.pop();

			stack.at(-1).node.children.push(node);
			stack.push({ level, node });
		} else {
			stack.at(-1).node.children.push(el);
		}
	});

	function passNotes(node) {
		if (!node.children) return;

		for (const child of node.children) {
			if (
				child.el?.classList.contains("mw-heading3") &&
				child.el.textContent.toLowerCase().includes("note")
			) {
				child.label = "Notes";
				child.content = child.children
					.map((c) => c.el?.textContent ?? c.textContent)
					.join("");
				delete child.children;
				delete child.el;
				delete child.level;
			} else {
				passNotes(child);
			}
		}
	}

	function passSingles(node) {
		if (!node.children) return;

		for (const child of node.children) {
			if (
				child.el?.classList.contains("mw-heading3") &&
				!child.el.textContent.toLowerCase().includes("member")
			) {
				const imgChildren = child.children.filter(
					(c) => c.el?.querySelector("img") || c.querySelector?.("img"),
				);

				if (imgChildren.length !== 1) {
					throw new Error("Expected exactly one child containing img");
				}

				const a =
					imgChildren[0].el?.querySelector("a") || imgChildren[0].querySelector("a");

				if (!a) {
					throw new Error("Expected link in img child");
				}

				child.href = a.href;
				child.title = a.title;
				child.label = child.el.textContent;

				delete child.children;
				delete child.el;
				delete child.level;
			} else {
				passSingles(child);
			}
		}
	}

	function passMembers(node) {
		if (!node.children) return;

		for (const child of node.children) {
			if (
				child.el?.classList.contains("mw-heading3") &&
				child.el.textContent.toLowerCase().includes("member")
			) {
				child.label = "members";

				child.members = child.children
					.filter((c) => c.el?.querySelector("img") || c.querySelector?.("img"))
					.map((c) => {
						const a = c.el?.querySelector("a") || c.querySelector("a");

						return {
							href: a.href,
							title: a.title,
						};
					});

				delete child.children;
				delete child.el;
				delete child.level;
			} else {
				passMembers(child);
			}
		}
	}

	function passTeams(node) {
		if (!node.children) return;

		for (const child of node.children) {
			if (child.el?.classList.contains("mw-heading2")) {
				const team = {
					label: child.el.textContent,
					singles: [],
				};

				for (const c of child.children) {
					if (!c.label) {
						console.log(c);
						throw new Error("Unprocessed child found in team");
					}

					if (c.label === "members") {
						team.members = c.members;
					} else if (c.label === "Notes") {
						team.notes = c.content;
					} else {
						team.singles.push(c);
					}
				}

				Object.assign(child, team);

				delete child.children;
				delete child.el;
				delete child.level;
			} else {
				passTeams(child);
			}
		}
	}

	function passCategories(node) {
		if (!node.el?.classList.contains("mw-heading1")) {
			throw new Error("Expected mw-heading1");
		}

		for (const team of node.children) {
			if (!team.label) {
				throw new Error("Unprocessed team in category");
			}
		}

		node.teams = node.children;
		node.label = node.el.textContent;

		delete node.children;
		delete node.el;
		delete node.level;
	}

	function normalizeName(name) {
		return name.replaceAll(/[\/\\:*?"<>|]/g, "-");
	}

	tree.children = tree.children.slice(1); // pop Contents
	tree.children.at(-1).children.pop(); // pop References

	tree.children.forEach(passNotes);
	tree.children.forEach(passSingles);
	tree.children.forEach(passMembers);
	tree.children.forEach(passTeams);
	tree.children.forEach(passCategories);

	return Object.fromEntries(
		tree.children.flatMap((category) =>
			category.teams.map(({ label, members = [], singles = [], notes = "", ...team }) => {
				const name = label.replace("(DLC)", " (DLC)");

				return [
					name,
					{
						...team,
						origin: category.label,
						notes,
						members: [
							...members.map(({ title, ...member }) => ({
								...member,
								name: normalizeName(title),
							})),
							...singles.map(({ label, title, ...single }) => ({
								...single,
								name: normalizeName(title),
								role: label,
							})),
						],
					},
				];
			}),
		),
	);
}
