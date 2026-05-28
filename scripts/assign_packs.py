"""
assign_packs.py — assign HSK 1 characters to packs and write pack_manifest.json.

Usage:
    python scripts/assign_packs.py
    python scripts/assign_packs.py --dry-run
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

PACK_SIZE = 10

# Thematic cluster overrides applied BEFORE sequential fallback.
# Characters listed here are grouped together when first encountered.
# Any character not covered by a cluster is placed sequentially.
CLUSTERS: list[list[str]] = [
    ["一","二","三","四","五","六","七","八","九","十"],  # numbers
    ["我","你","他","她","们","的","个","是","有","不"],  # pronouns + basics
    ["来","去","说","看","听","做","吃","喝","写","读"],  # verbs I
    ["年","天","上","下","今","明","昨","时","分","点"],  # time
    ["中","里","外","前","后","左","右","家","国","在"],  # place/direction
    ["好","多","少","高","冷","热","新","老","开","回"],  # adjectives + more verbs
    ["口","手","目","耳","足","头","土","石","风","雨"],  # body + nature
    ["云","地","花","草","买","卖","给","要","走","跑"],  # nature II + actions
]


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  wrote {path.relative_to(ROOT)}")


def assign(dry_run: bool = False):
    hsk1 = load_json(DATA / "hsk1.json")
    manifest = load_json(DATA / "pack_manifest.json")

    # Build ordered HSK character list (cluster-aware)
    hsk_chars = [e["character"] for e in hsk1]
    ordered: list[str] = []
    placed: set[str] = set()

    # Place cluster members first, preserving cluster order
    for cluster in CLUSTERS:
        for ch in cluster:
            if ch in hsk_chars and ch not in placed:
                ordered.append(ch)
                placed.add(ch)

    # Append any remaining HSK chars not covered by clusters
    for ch in hsk_chars:
        if ch not in placed:
            ordered.append(ch)

    # Find already-assigned characters
    assigned: set[str] = set()
    for pack_data in manifest.values():
        assigned.update(pack_data["characters"])

    # Find next pack number
    existing_nums = []
    for key in manifest:
        try:
            existing_nums.append(int(key.split("-")[1]))
        except (IndexError, ValueError):
            pass
    next_num = max(existing_nums, default=0) + 1

    # Assign remaining characters sequentially, 10 per pack
    remaining = [ch for ch in ordered if ch not in assigned]
    new_packs: dict[str, list[str]] = {}
    for i in range(0, len(remaining), PACK_SIZE):
        batch = remaining[i : i + PACK_SIZE]
        if not batch:
            break
        key = f"pack-{next_num:02d}"
        new_packs[key] = batch
        next_num += 1

    if not new_packs:
        print("All HSK 1 characters already assigned.")
        return

    print("\nNew pack assignments:")
    for key, chars in new_packs.items():
        print(f"  {key}: {''.join(chars)}")

    if dry_run:
        print("\n(dry-run — manifest not updated)")
        return

    # Merge into manifest with default metadata
    for key, chars in new_packs.items():
        manifest[key] = {
            "characters": chars,
            "title": f"Pack {key.split('-')[1]}",
            "subtitle": "",
            "description": "Not just a flashcard. Each character's <em>full story</em> on one page.",
            "type_note": "",
            "series": "一",
            "volume": key.split("-")[1],
        }

    save_json(DATA / "pack_manifest.json", manifest)
    print(f"\nAdded {len(new_packs)} pack(s) to pack_manifest.json")

    # Also seed characters.json with any new characters (basic data from hsk1.json)
    characters = load_json(DATA / "characters.json")
    existing_chars = {c["character"] for c in characters}
    hsk_lookup = {e["character"]: e for e in hsk1}

    newly_seeded = 0
    for pack_key, chars in new_packs.items():
        pack_num = pack_key.split("-")[1]
        for pos, ch in enumerate(chars, 1):
            if ch in existing_chars:
                continue
            h = hsk_lookup.get(ch, {})
            characters.append({
                "character": ch,
                "pinyin": h.get("pinyin", ""),
                "tone": h.get("tone", 0),
                "type": "pictograph",
                "english": [h.get("english", "")],
                "hsk_level": 1,
                "hsk_order": 0,
                "strokes": 0,
                "radical": "",
                "radical_pinyin": "",
                "stroke_order": [],
                "compounds": [],
                "blueprint": "",
                "formula": "",
                "cultural_note": "",
                "mnemonic": "",
                "pack": pack_num,
                "pack_position": pos,
            })
            existing_chars.add(ch)
            newly_seeded += 1

    if newly_seeded:
        save_json(DATA / "characters.json", characters)
        print(f"Seeded {newly_seeded} new character(s) into characters.json")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    assign(dry_run=dry_run)
