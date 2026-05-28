"""
fetch_resources.py — download oracle-bone and bronze-script glyph images.

For each character:
  1. Fetches https://www.chineseetymology.org/CharacterASP/CharacterEtymology.aspx?characterInput={char}
  2. Finds the first oracle-bone (甲骨文) and bronze-script (金文) images
  3. Resizes to 200px height (nearest-neighbour) using Pillow
  4. Saves to packs/pack-{N}/assets/glyphs/{pinyin}-{oracle|bronze}.png

Usage:
    python scripts/fetch_resources.py --pack 02
    python scripts/fetch_resources.py --pack 02 --char 水       # single character
"""
import argparse
import json
import logging
import time
import urllib.parse
from io import BytesIO
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

BASE_URL = "https://www.chineseetymology.org/CharacterASP/CharacterEtymology.aspx"
REQUEST_DELAY = 1.0  # seconds between requests
GLYPH_HEIGHT = 200   # target height in pixels

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def pinyin_bare(pinyin: str) -> str:
    tone_map = {
        "ā":"a","á":"a","ǎ":"a","à":"a",
        "ē":"e","é":"e","ě":"e","è":"e",
        "ī":"i","í":"i","ǐ":"i","ì":"i",
        "ō":"o","ó":"o","ǒ":"o","ò":"o",
        "ū":"u","ú":"u","ǔ":"u","ù":"u",
        "ǖ":"u","ǘ":"u","ǚ":"u","ǜ":"u",
    }
    for toned, base in tone_map.items():
        pinyin = pinyin.replace(toned, base)
    return pinyin


def make_placeholder(height: int = GLYPH_HEIGHT) -> Image.Image:
    """Create a small grey placeholder image."""
    w = int(height * 0.8)
    img = Image.new("RGBA", (w, height), (200, 200, 200, 128))
    return img


def resize_to_height(img: Image.Image, height: int = GLYPH_HEIGHT) -> Image.Image:
    ratio = height / img.height
    new_w = max(1, int(img.width * ratio))
    return img.resize((new_w, height), Image.NEAREST)


def fetch_page(char: str, session: requests.Session) -> BeautifulSoup | None:
    url = f"{BASE_URL}?characterInput={urllib.parse.quote(char)}"
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.content, "html.parser")
    except requests.RequestException as exc:
        log.warning("Could not fetch page for %s: %s", char, exc)
        return None


def extract_script_images(soup: BeautifulSoup, script_labels: list[str]) -> list[str]:
    """
    Return absolute image URLs for a given script type.
    Searches for section headers containing any of the script_labels,
    then collects <img> tags that follow.
    """
    found_urls: list[str] = []

    # Strategy 1: look for <td> or <th> cells containing the label text
    for label in script_labels:
        cells = soup.find_all(
            lambda tag: tag.name in ("td", "th", "div", "span", "h2", "h3", "h4", "b")
            and label in (tag.get_text() or ""),
        )
        for cell in cells:
            # Check the cell itself and its parent row/container for images
            container = cell.find_parent("tr") or cell.find_parent("table") or cell
            for img in container.find_all("img"):
                src = img.get("src", "")
                if src and not src.endswith("spacer.gif") and "pixel" not in src.lower():
                    found_urls.append(src)
            if found_urls:
                return found_urls

    # Strategy 2: look for img tags whose src path hints at the script type
    script_hints = [label.lower() for label in script_labels]
    for img in soup.find_all("img"):
        src = (img.get("src") or "").lower()
        if any(hint in src for hint in script_hints):
            found_urls.append(img["src"])

    return found_urls


def absolute_url(src: str, base_url: str) -> str:
    if src.startswith("http"):
        return src
    parsed = urllib.parse.urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if src.startswith("/"):
        return base + src
    return urllib.parse.urljoin(base_url, src)


def download_image(url: str, session: requests.Session) -> Image.Image | None:
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content)).convert("RGBA")
    except Exception as exc:
        log.warning("Could not download image %s: %s", url, exc)
        return None


def save_glyph(img: Image.Image, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    resized = resize_to_height(img, GLYPH_HEIGHT)
    resized.save(out_path, "PNG")
    log.info("  saved %s", out_path.relative_to(ROOT))


def fetch_for_character(
    char_data: dict,
    glyphs_dir: Path,
    session: requests.Session,
    force: bool = False,
):
    char = char_data["character"]
    pinyin = pinyin_bare(char_data.get("pinyin", char))

    targets = {
        "oracle": glyphs_dir / f"{pinyin}-oracle.png",
        "bronze": glyphs_dir / f"{pinyin}-bronze.png",
    }

    # Skip if both already exist and not forcing
    if not force and all(p.exists() for p in targets.values()):
        log.info("Skipping %s — images already exist", char)
        return

    log.info("Fetching %s (%s)…", char, pinyin)
    soup = fetch_page(char, session)

    page_url = f"{BASE_URL}?characterInput={urllib.parse.quote(char)}"

    script_config = {
        "oracle": ["甲骨", "Oracle", "oracle", "jiaguwen", "jiagu"],
        "bronze": ["金文", "Bronze", "bronze", "jinwen"],
    }

    for script_key, out_path in targets.items():
        if not force and out_path.exists():
            continue

        img = None
        if soup is not None:
            urls = extract_script_images(soup, script_config[script_key])
            for url in urls[:1]:  # take only the first image
                abs_url = absolute_url(url, page_url)
                img = download_image(abs_url, session)
                if img:
                    log.info("  [%s] downloaded %s", script_key, abs_url)
                    break

        if img is None:
            log.warning("  [%s] no image found for %s — using placeholder", script_key, char)
            img = make_placeholder()

        save_glyph(img, out_path)
        time.sleep(REQUEST_DELAY)


def fetch_pack(pack_num: str, only_char: str | None = None, force: bool = False):
    manifest = load_json(DATA / "pack_manifest.json")
    characters_db = load_json(DATA / "characters.json")
    char_lookup = {c["character"]: c for c in characters_db}

    pack_key = f"pack-{int(pack_num):02d}"
    if pack_key not in manifest:
        log.error("Pack %s not found in pack_manifest.json", pack_key)
        return

    chars = manifest[pack_key]["characters"]
    if only_char:
        if only_char not in chars:
            log.error("Character %s not in %s", only_char, pack_key)
            return
        chars = [only_char]

    glyphs_dir = ROOT / "packs" / pack_key / "assets" / "glyphs"

    with requests.Session() as session:
        session.headers["User-Agent"] = (
            "Mozilla/5.0 (compatible; ZituCardsBot/1.0; educational use)"
        )
        for char in chars:
            data = char_lookup.get(char)
            if data is None:
                log.warning("No data for %s in characters.json — skipping", char)
                continue
            fetch_for_character(data, glyphs_dir, session, force=force)
            time.sleep(REQUEST_DELAY)

    log.info("Done. Glyphs in %s", glyphs_dir.relative_to(ROOT))


def main():
    parser = argparse.ArgumentParser(description="Fetch glyph images for a pack.")
    parser.add_argument("--pack", required=True, help="Pack number, e.g. 02")
    parser.add_argument("--char", default=None, help="Only fetch a single character")
    parser.add_argument("--force", action="store_true", help="Re-download existing images")
    args = parser.parse_args()
    fetch_pack(args.pack, only_char=args.char, force=args.force)


if __name__ == "__main__":
    main()
