#!/usr/bin/env python3
"""
prepare_pack.py — Phase 1 data prep for ZìTú packs.

Downloads makemeahanzi data (once), extracts stroke SVG paths and metadata,
classifies stroke names geometrically, merges manual fields, and writes
packs/pack-NN/data/characters-prepared.json.

Usage:
    python prepare_pack.py --pack 01
"""

import argparse
import json
import math
import sys
from pathlib import Path
from urllib.request import urlretrieve

ROOT = Path(__file__).parent
DATA = ROOT / "data"
MAKEMEAHANZI_DIR = DATA / "makemeahanzi"
GRAPHICS_URL = (
    "https://raw.githubusercontent.com/skishore/makemeahanzi/master/graphics.txt"
)
DICT_URL = (
    "https://raw.githubusercontent.com/skishore/makemeahanzi/master/dictionary.txt"
)


# ── Download ───────────────────────────────────────────────────────────────────

def ensure_makemeahanzi() -> None:
    if (MAKEMEAHANZI_DIR / "graphics.txt").exists():
        return
    print("Downloading makemeahanzi data (one-time setup)...")
    MAKEMEAHANZI_DIR.mkdir(parents=True, exist_ok=True)
    print("  Fetching graphics.txt ...")
    urlretrieve(GRAPHICS_URL, MAKEMEAHANZI_DIR / "graphics.txt")
    print("  Fetching dictionary.txt ...")
    urlretrieve(DICT_URL, MAKEMEAHANZI_DIR / "dictionary.txt")
    print("  Done.")


# ── Data loading ───────────────────────────────────────────────────────────────

def load_txt_index(path: Path) -> dict:
    """Load a newline-delimited JSON file keyed by 'character'."""
    index = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            char = obj.get("character")
            if char:
                index[char] = obj
    return index


def load_json(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ── Geometry utilities ────────────────────────────────────────────────────────

def _angle(dx: float, dy: float) -> float:
    """Angle in degrees (-180, 180]. makemeahanzi uses Y-up coordinates."""
    if dx == 0.0 and dy == 0.0:
        return 0.0
    return math.degrees(math.atan2(dy, dx))


def _diff(center: float, angle: float) -> float:
    """Smallest signed angle FROM center TO angle, in (-180, 180]."""
    return (angle - center + 180.0) % 360.0 - 180.0


def _in_range(angle: float, center: float, tol: float) -> bool:
    return abs(_diff(center, angle)) <= tol


# ── Median (centerline) analysis ──────────────────────────────────────────────
#
# makemeahanzi stroke paths are CLOSED filled outlines (start == end), so
# direction analysis must use the 'medians' field instead — these are open
# polyline centerlines that correctly represent the stroke's direction.
#
# Y-up coordinate system (origin bottom-left, Y increases upward):
#   横 (rightward)  ≈   0°     竖 (downward) ≈ -90°
#   撇 (down-left)  ≈ -120°    捺 (down-right) ≈ -40°

def median_features(median: list, all_medians: list) -> dict | None:
    """Extract directional features from a stroke median centerline polyline."""
    if len(median) < 2:
        return None
    pts = median

    overall = _angle(pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1])
    end     = _angle(pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1])

    seg_angles = [
        _angle(pts[j + 1][0] - pts[j][0], pts[j + 1][1] - pts[j][1])
        for j in range(len(pts) - 1)
    ]
    seg_lens = [
        math.hypot(pts[j + 1][0] - pts[j][0], pts[j + 1][1] - pts[j][1])
        for j in range(len(pts) - 1)
    ]
    total_len = sum(seg_lens)

    max_turn = max(
        (abs(_diff(seg_angles[j - 1], seg_angles[j])) for j in range(1, len(seg_angles))),
        default=0.0,
    )

    char_lens = [
        sum(math.hypot(m[k + 1][0] - m[k][0], m[k + 1][1] - m[k][1]) for k in range(len(m) - 1))
        for m in all_medians if len(m) >= 2
    ]
    # Use max stroke length as anchor: 点 strokes are ≤28% of max; use 30% threshold.
    # avg_len is unreliable when one stroke (竖钩/卧钩) dominates and inflates the mean.
    max_len  = max(char_lens) if char_lens else 300.0
    is_short = total_len < max_len * 0.30

    return {
        "overall":   overall,
        "end":       end,
        "max_turn":  max_turn,
        "is_short":  is_short,
        "total_len": total_len,
    }


# ── Stroke classification ──────────────────────────────────────────────────────

def classify_from_median(median: list, all_medians: list, names: dict) -> dict:
    """
    Classify a stroke type from its median centerline polyline.
    Returns {"name_zh": ..., "name_py": ..., "name_en": ...}.
    """
    def sn(key: str) -> dict:
        n = names.get(key, {"zh": key, "py": "?", "en": "?"})
        return {"name_zh": n["zh"], "name_py": n["py"], "name_en": n["en"]}

    unmatched = {"name_zh": "UNMATCHED", "name_py": "UNMATCHED", "name_en": "UNMATCHED"}
    f = median_features(median, all_medians)
    if f is None:
        return unmatched

    ov = f["overall"]
    end = f["end"]
    mt  = f["max_turn"]
    ir  = _in_range

    # Compound strokes (large directional change between adjacent segments).
    # Checked before is_short so that curved 撇 strokes (mt≈64°, ov≈-124°)
    # are classified by direction rather than incorrectly promoted to 点.
    # 点 strokes have mt ≤ 25° and never enter this block.
    if mt > 55:
        # Leftward hooks (end ≈ 150°–180°): 竖钩 or 横折钩
        if ir(end, 165, 20) or ir(end, -170, 20):
            # 竖钩: more vertical overall (≈ -99° to -101°)
            # 横折钩: more diagonal overall (≈ -79°)
            return sn("竖钩") if ov < -87 else sn("横折钩")

        # 横撇: ends lower-left (≈ -146°) but only when overall is not too steep.
        # Steep-left overall (ov < -107°) with a curved end = curved 撇, not 横撇.
        if ir(end, -143, 25) and ov > -107:
            return sn("横撇")

        # Upper hooks (end ≈ 90°–135°): 卧钩
        if ir(end, 113, 30):
            return sn("卧钩")

        # Curved 撇: very steep lower-left overall despite high max_turn
        if ov < -100:
            return sn("撇")

        # 竖折: sub-horizontal overall, ends upper-right after a sharp downward turn
        if ir(ov, -15, 30) and (ir(end, 45, 40) or ir(end, 0, 40)):
            return sn("竖折")

        # 横折: overall heading into third quadrant (≈ -62°), or starts rightward
        if ir(ov, -62, 20) or ir(ov, 0, 40):
            return sn("横折")

        if ir(ov, -90, 40):
            return sn("竖折")

    # Short non-horizontal strokes → 点.
    # Horizontal short strokes (interior 横 in 日/月, ov ≈ 5°) are excluded by the
    # angle guard and fall through to the 横 rule below.
    if f["is_short"] and not ir(ov, 5, 25):
        return sn("点")

    # Moderate turns (日-style 横折: mt ≈ 47°, overall ≈ -62°)
    if mt > 40 and ir(ov, -62, 20):
        return sn("横折")

    # Simple strokes classified by overall direction
    if ir(ov, 5, 20):      # rightward → 横
        return sn("横")
    if ir(ov, -90, 8):     # downward → 竖  (narrow range: -82° to -98°)
        return sn("竖")
    if ov < -97:           # steep lower-left → 撇  (撇 range: -104° to -131°)
        return sn("撇")
    if ir(ov, -38, 15):    # lower-right → 捺
        return sn("捺")
    if ir(ov, 90, 30):     # upper-right → 提
        return sn("提")

    # Extended fallbacks for edge cases
    if ir(ov, 0, 30):
        return sn("横")
    if ir(ov, -90, 20):
        return sn("竖")
    if ir(ov, -120, 35):
        return sn("撇")

    return unmatched


# ── Etymology type mapping ─────────────────────────────────────────────────────

_ETYM_MAP = {
    "pictographic":  "pictograph",
    "ideographic":   "ideograph",
    "pictophonetic": "phono-semantic",
    "compound":      "compound",
}


def _etym_type(etym: dict) -> str:
    return _ETYM_MAP.get((etym.get("type") or "").lower(), "")


# ── Character record builder ───────────────────────────────────────────────────

def prepare_character(
    char: str,
    position: int,
    graphics_idx: dict,
    dict_idx: dict,
    manual_data: dict,
    char_db: dict,
    names: dict,
) -> dict:
    raw = char_db.get(char, {})
    gfx = graphics_idx.get(char, {})
    dct = dict_idx.get(char, {})
    man = manual_data.get(char, {})

    # ── Strokes from makemeahanzi ─────────────────────────────────────────────
    raw_paths = gfx.get("strokes", [])
    medians   = gfx.get("medians", [])
    strokes = []
    for idx, path in enumerate(raw_paths, 1):
        median = medians[idx - 1] if idx - 1 < len(medians) else []
        name = classify_from_median(median, medians, names)
        if name["name_zh"] == "UNMATCHED":
            f = median_features(median, medians) if len(median) >= 2 else None
            if f:
                print(
                    f"    WARNING: {char} stroke {idx} UNMATCHED "
                    f"(ov={f['overall']:.0f}° end={f['end']:.0f}° "
                    f"mt={f['max_turn']:.0f}° short={f['is_short']})"
                )
            else:
                print(f"    WARNING: {char} stroke {idx} UNMATCHED (no median data)")
        strokes.append({"order": idx, "path": path, **name})

    # ── Metadata from makemeahanzi dictionary ─────────────────────────────────
    etym = dct.get("etymology") or {}
    char_type = _etym_type(etym) or raw.get("character_type") or raw.get("type", "pictograph")

    en_raw = dct.get("english", [])
    if isinstance(en_raw, str):
        en_raw = [en_raw]
    # Prefer makemeahanzi english; fall back to characters.json
    if not en_raw:
        en_raw = raw.get("english", [])
        if isinstance(en_raw, str):
            en_raw = [en_raw]
    eng_primary = en_raw[0] if en_raw else ""
    eng_secondary = list(en_raw[1:])

    # Pinyin: characters.json wins (verified human data)
    pinyin = raw.get("pinyin") or (dct.get("pinyin") or [""])[0]

    return {
        "character":        char,
        "pinyin":           pinyin,
        "tone":             raw.get("tone", 0),
        "character_type":   char_type,
        "english_primary":  eng_primary,
        "english_secondary": eng_secondary,
        "hsk_level":        raw.get("hsk_level", 1),
        "strokes":          strokes,
        "stroke_count":     len(strokes),
        "outline_path":     None,
        "radical":          raw.get("radical", ""),
        "radical_pinyin":   raw.get("radical_pinyin", ""),
        "compounds":        man.get("compounds") or raw.get("compounds", []),
        "cultural_note":    man.get("cultural_note") or raw.get("cultural_note", ""),
        "blueprint":        man.get("blueprint") or raw.get("blueprint", ""),
        "formula":          man.get("formula") or raw.get("formula", ""),
        "mnemonic":         man.get("mnemonic") or raw.get("mnemonic", ""),
        "confusables":      man.get("confusables") or raw.get("confusables", []),
        "pack":             raw.get("pack", ""),
        "pack_position":    position,
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare character data for a ZìTú pack."
    )
    parser.add_argument("--pack", required=True, help="Pack number, e.g. 01")
    args = parser.parse_args()

    pack_num = f"{int(args.pack):02d}"
    pack_key = f"pack-{pack_num}"

    ensure_makemeahanzi()

    print("Loading makemeahanzi data...")
    graphics_idx = load_txt_index(MAKEMEAHANZI_DIR / "graphics.txt")
    dict_idx = load_txt_index(MAKEMEAHANZI_DIR / "dictionary.txt")
    print(f"  {len(graphics_idx)} graphics, {len(dict_idx)} dictionary entries")

    names_path = DATA / "stroke-names.json"
    if not names_path.exists():
        print(f"ERROR: {names_path} not found", file=sys.stderr)
        sys.exit(1)
    names = load_json(names_path)

    manifest = load_json(DATA / "pack_manifest.json")
    if pack_key not in manifest:
        print(f"ERROR: '{pack_key}' not found in pack_manifest.json", file=sys.stderr)
        sys.exit(1)
    pack_chars = manifest[pack_key]["characters"]

    char_db_list = load_json(DATA / "characters.json")
    char_db = {c["character"]: c for c in char_db_list}

    manual_path = ROOT / "packs" / pack_key / "data" / "characters-manual.json"
    manual_data: dict = {}
    if manual_path.exists():
        raw_man = load_json(manual_path)
        if isinstance(raw_man, list):
            manual_data = {c["character"]: c for c in raw_man}
        else:
            manual_data = raw_man
        print(f"  Manual file: {len(manual_data)} entries")
    else:
        print(f"  No manual file at {manual_path.relative_to(ROOT)} — using characters.json fallback")

    print(f"\nPreparing Pack {pack_num}: {pack_chars}\n")

    prepared = []
    missing_gfx = []

    for pos, char in enumerate(pack_chars, 1):
        if char not in graphics_idx:
            print(f"  WARNING: {char!r} not found in graphics.txt")
            missing_gfx.append(char)
        record = prepare_character(
            char, pos, graphics_idx, dict_idx, manual_data, char_db, names
        )
        prepared.append(record)
        n = record["stroke_count"]
        named = sum(1 for s in record["strokes"] if s["name_zh"] != "UNMATCHED")
        print(f"  {char} {record['pinyin']}: {n} strokes, {named}/{n} named")

    out_dir = ROOT / "packs" / pack_key / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "characters-prepared.json"

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(prepared, fh, ensure_ascii=False, indent=2)

    print(f"\nWrote {out_path.relative_to(ROOT)}  ({len(prepared)} characters)")

    if missing_gfx:
        print(f"  Characters missing from makemeahanzi: {missing_gfx}")

    unmatched = sum(
        sum(1 for s in r["strokes"] if s["name_zh"] == "UNMATCHED")
        for r in prepared
    )
    if unmatched:
        print(f"  {unmatched} stroke(s) with UNMATCHED names — review warnings above")
    else:
        print("  All strokes named successfully")


if __name__ == "__main__":
    main()
