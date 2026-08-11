from pathlib import Path

BASE_WIKI_URL = "https://umamusu.wiki"
API_URL = f"{BASE_WIKI_URL}/w/api.php"

USER_AGENT = (
	"UmaMusumeAnkiFetcher/1.0 (https://github.com/lakazatong/uma-musume-anki; lakazatong@outlook.com) requests/2.34.2"
)
BASE_HEADERS = {
	"User-Agent": USER_AGENT,
	"Referer": BASE_WIKI_URL,
}


RAW_DIR = Path("raw")
PARSED_DIR = Path("parsed")
IMAGES_DIR = Path("images")

RAW_DIR.mkdir(exist_ok=True)
PARSED_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)
