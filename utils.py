import html
from urllib.parse import quote


def normalize_filename(title: str) -> str:
	return title.replace(" ", "_").replace("/", "_") + ".xml"


def link_wrap(text, href):
	if text and href:
		return f'<a href="{html.escape(href, quote=True)}">{html.escape(text)}</a>'
	return None


def dorm_page(dorm):
	if dorm:
		return f"https://umamusu.wiki/Roommates/{dorm.replace(' ', '_')}_Dorm"
	return None


def file_page(filename):
	return f"https://umamusu.wiki/File:{quote(filename.replace(' ', '_'))}"


def wiki_page(name):
	if name:
		return f"https://umamusu.wiki/{quote(name.replace(' ', '_'))}"
	return None
