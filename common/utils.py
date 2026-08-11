import html
from urllib.parse import quote

from common.config import BASE_WIKI_URL


def normalize_filename(title: str) -> str:
	return title.replace(" ", "_").replace("/", "_") + ".xml"


def link_wrap(text, href):
	if text and href:
		return f'<a href="{html.escape(href, quote=True)}">{html.escape(text)}</a>'
	return None


def dorm_page(dorm):
	if dorm:
		return f"{BASE_WIKI_URL}/Roommates/{dorm.replace(' ', '_')}_Dorm"
	return None


def file_page(filename):
	return f"{BASE_WIKI_URL}/File:{quote(filename.replace(' ', '_'))}"


def wiki_page(name):
	if name:
		return f"{BASE_WIKI_URL}/{quote(name.replace(' ', '_'))}"
	return None
