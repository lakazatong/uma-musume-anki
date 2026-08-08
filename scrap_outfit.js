function scrapOutfit() {
	const internal = document.querySelector("a.internal");

	if (!internal) {
		throw new Error("No internal image found");
	}

	return new URL(internal.href, location.origin).href;
}
