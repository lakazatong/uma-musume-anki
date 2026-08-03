import html
from urllib.parse import quote


def link_wrap(text, href):
	return f'<a href="{html.escape(href)}">{html.escape(text)}</a>'


def wiki_page(name):
	return f"https://umamusu.wiki/{quote(name.replace(' ', '_'))}"


def file_page(filename):
	return f"https://umamusu.wiki/File:{filename}"
