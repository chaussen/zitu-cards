"""
build_practice.py — generate packs/pack-{N}/practice.html from characters-prepared.json.

One A4 portrait practice sheet per character, with:
  Zone A  涂一涂  colour the outline character
  Zone B  画一画  blank 米字格 to draw from memory
  Zone C  找一找  find-it grid (target mixed with confusables)
  Zone D  英文意思 write the English meaning
  Zone E  描一描  trace row (4 reps)
  Zone F  写一写  write row (4 empty cells)
  Zone G  造句    sentence zone using compounds

Usage:
    python scripts/build_practice.py --pack 01
"""
import argparse
import json
import random
from pathlib import Path

from jinja2 import Environment, BaseLoader

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

# ── Pinyin helpers (shared with build_cards.py) ────────────────────────────────

_TONE_MAP = {
    "ā": ("a", 1), "á": ("a", 2), "ǎ": ("a", 3), "à": ("a", 4),
    "ē": ("e", 1), "é": ("e", 2), "ě": ("e", 3), "è": ("e", 4),
    "ī": ("i", 1), "í": ("i", 2), "ǐ": ("i", 3), "ì": ("i", 4),
    "ō": ("o", 1), "ó": ("o", 2), "ǒ": ("o", 3), "ò": ("o", 4),
    "ū": ("u", 1), "ú": ("u", 2), "ǔ": ("u", 3), "ù": ("u", 4),
    "ǖ": ("ü", 1), "ǘ": ("ü", 2), "ǚ": ("ü", 3), "ǜ": ("ü", 4),
}

_TONE_NAMES = {1: "level", 2: "rising", 3: "dipping", 4: "falling"}


def pinyin_html(pinyin: str) -> str:
    """Wrap the toned vowel in a <span class="tm-N"> for colour."""
    for toned, (_, tone_num) in _TONE_MAP.items():
        if toned in pinyin:
            idx = pinyin.index(toned)
            return (
                pinyin[:idx]
                + f'<span class="tm-{tone_num}">{toned}</span>'
                + pinyin[idx + 1:]
            )
    return pinyin


# ── Find-it grid ───────────────────────────────────────────────────────────────

def make_find_grid(character: str, confusables: list, rows: int = 4, cols: int = 6) -> list:
    """Return a deterministic shuffled grid of rows×cols cells."""
    total = rows * cols          # 24
    target_count = total // 3   # 8 targets out of 24

    rng = random.Random(ord(character[0]))

    cells = [character] * target_count
    pool = list(confusables) if confusables else [character]
    while len(cells) < total:
        cells.extend(pool)
    cells = cells[:total]
    rng.shuffle(cells)
    return cells


# ── Data loading ───────────────────────────────────────────────────────────────

def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def prepare_practice(raw: dict, pack_num: str, position: int, total: int) -> dict:
    tone = raw.get("tone", 0)
    pinyin = raw.get("pinyin", "")
    character = raw["character"]
    compounds = raw.get("compounds", [])
    confusables = raw.get("confusables", [])

    compound_str = " · ".join(c["zh"] for c in compounds)

    return {
        "character":      character,
        "pinyin_raw":     pinyin,
        "pinyin_html":    pinyin_html(pinyin),
        "tone":           tone,
        "tone_name":      _TONE_NAMES.get(tone, ""),
        "english_primary": raw.get("english_primary", ""),
        "english_secondary": raw.get("english_secondary", []),
        "position":       position,
        "total":          total,
        "position_str":   f"{position:02d} / {total:02d}",
        "pack_num":       pack_num,
        "compounds":      compounds,
        "compound_str":   compound_str,
        "find_grid":      make_find_grid(character, confusables),
    }


# ── Jinja2 template ────────────────────────────────────────────────────────────

_TEMPLATE = r"""<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8"/>
<title>字图 ZìTú · Pack {{ pack_num }} · Practice</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Long+Cang&family=ZCOOL+XiaoWei&family=Noto+Serif+SC:wght@400;700;900&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=DM+Sans:wght@300;400;500;700&family=Noto+Sans:wght@400;500&family=IBM+Plex+Mono:wght@300;400;500&display=swap" rel="stylesheet"/>
<link rel="stylesheet" href="../../system/style.css"/>
</head>
<body>

<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <defs>
    <!-- standard 米字格 — header ch-block and Zone B -->
    <symbol id="mz" viewBox="0 0 100 100" preserveAspectRatio="none">
      <rect class="frame" x="0.4" y="0.4" width="99.2" height="99.2" fill="none" stroke="#c8b89c" stroke-width="0.55"/>
      <line x1="0" y1="50" x2="100" y2="50" stroke="#c8b89c" stroke-width="0.22" stroke-dasharray="1 1.2"/>
      <line x1="50" y1="0" x2="50" y2="100" stroke="#c8b89c" stroke-width="0.22" stroke-dasharray="1 1.2"/>
      <line x1="0" y1="0" x2="100" y2="100" stroke="#c8b89c" stroke-width="0.22" stroke-dasharray="1 1.2"/>
      <line x1="100" y1="0" x2="0" y2="100" stroke="#c8b89c" stroke-width="0.22" stroke-dasharray="1 1.2"/>
    </symbol>
    <!-- trace-cell 米字格 — print-weight strokes sized to the em-square -->
    <symbol id="mz-trace" viewBox="0 0 100 100" preserveAspectRatio="none">
      <rect x="0.5" y="0.5" width="99" height="99" fill="none" stroke="#c8b89c" stroke-width="1.0"/>
      <line x1="0" y1="50" x2="100" y2="50" stroke="#c8b89c" stroke-width="0.7" stroke-dasharray="4 3"/>
      <line x1="50" y1="0" x2="50" y2="100" stroke="#c8b89c" stroke-width="0.7" stroke-dasharray="4 3"/>
      <line x1="0" y1="0" x2="100" y2="100" stroke="#c8b89c" stroke-width="0.5" stroke-dasharray="3 3"/>
      <line x1="100" y1="0" x2="0" y2="100" stroke="#c8b89c" stroke-width="0.5" stroke-dasharray="3 3"/>
    </symbol>
  </defs>
</svg>

{% for p in practices %}
<!--
═══════════════════════════════════════════════════════
  PRACTICE {{ p.position_str }} — {{ p.character }} {{ p.pinyin_raw }}
═══════════════════════════════════════════════════════
-->
<section class="sheet a4-portrait-solo practice" data-screen-label="{{ p.position_str }} Practice {{ p.character }}">
  <div class="sheet-mark">
    <span>字图 · PACK {{ pack_num }} · {{ pack_title | upper }} · PRACTICE {{ p.position_str }}</span>
    <span><span class="pip">●</span> {{ p.character }} {{ p.pinyin_raw }} · version B</span>
  </div>

  <header class="ph-head">
    <div class="ch-block"><svg class="mizige"><use href="#mz"/></svg><span class="han">{{ p.character }}</span></div>
    <div class="meta">
      <div class="lbl">Practice · {{ p.position_str }}</div>
      <div class="py">{{ p.pinyin_html | safe }} &nbsp;<span style="color:var(--tone-{{ p.tone }}); font-style:italic; font-size:18pt;">·  tone {{ p.tone }} — {{ p.tone_name }}</span></div>
      <div class="mn"><em>{{ p.english_primary }}{% if p.english_secondary %}, {{ p.english_secondary | join(', ') }}{% endif %}</em></div>
    </div>
    <div class="sealcol">
      <div class="stamp">一</div>
      Pack {{ pack_num }} · {{ pack_type_han }}
    </div>
  </header>

  <section class="zones">

    <!-- Zone A: Colour the guide -->
    <div class="zone">
      <div class="zhd">
        <div class="zlb"><span class="han">涂一涂</span><em>colour the character</em></div>
        <div class="zix">A · TRACE WITH COLOUR</div>
      </div>
      <div class="outline-char">{{ p.character }}</div>
    </div>

    <!-- Zone B: Draw from memory -->
    <div class="zone">
      <div class="zhd">
        <div class="zlb"><span class="han">画一画</span><em>draw it from memory</em></div>
        <div class="zix">B · RECALL</div>
      </div>
      <div class="blank-mizige">
        <div class="mz"><svg><use href="#mz"/></svg></div>
      </div>
    </div>

    <!-- Zone C: Find it -->
    <div class="zone">
      <div class="zhd">
        <div class="zlb"><span class="han">找一找</span><em>circle every {{ p.character }} you find</em></div>
        <div class="zix">C · RECOGNISE</div>
      </div>
      <div class="find-grid">
        {% for cell in p.find_grid %}<div class="c">{{ cell }}</div>{% endfor %}
      </div>
    </div>

    <!-- Zone D: English meaning -->
    <div class="zone">
      <div class="zhd">
        <div class="zlb"><span class="han">英文意思</span><em>write the English meaning</em></div>
        <div class="zix">D · MEANING</div>
      </div>
      <div class="ans-line">
        <div style="font-family:var(--f-display); font-style: italic; font-size: 14pt; color: var(--ink-mute);">{{ p.character }} means…</div>
        <div class="ln"></div>
        <div class="ln"></div>
      </div>
    </div>

    <!-- Zone E: Trace row -->
    <div class="zone">
      <div class="zhd">
        <div class="zlb"><span class="han">描一描</span><em>trace the dotted characters</em></div>
        <div class="zix">E · TRACE · 4 reps</div>
      </div>
      <div class="trace-row">
        {% for _ in range(4) %}
        <div class="cell">
          <div class="char-frame">
            <svg class="cell-grid"><use href="#mz-trace"/></svg>
            <span class="han">{{ p.character }}</span>
          </div>
        </div>
        {% endfor %}
      </div>
    </div>

    <!-- Zone F: Write row -->
    <div class="zone">
      <div class="zhd">
        <div class="zlb"><span class="han">写一写</span><em>now write from memory</em></div>
        <div class="zix">F · WRITE · 4 reps</div>
      </div>
      <div class="trace-row">
        {% for _ in range(4) %}
        <div class="cell empty">
          <div class="char-frame">
            <svg class="cell-grid"><use href="#mz-trace"/></svg>
          </div>
        </div>
        {% endfor %}
      </div>
    </div>

    <!-- Zone G: Sentence writing -->
    <div class="zone full">
      <div class="zhd">
        <div class="zlb"><span class="han">造句</span><em>make a sentence using one compound</em></div>
        <div class="zix">G · APPLY · version B</div>
      </div>
      <div style="font-family:var(--f-display); font-style: italic; font-size: 12pt; color: var(--ink-soft); margin-bottom: 2mm;">
        Pick one word from the word web: <strong style="font-style:italic; color:var(--ink);">{{ p.compound_str }}</strong> &nbsp;— and write a sentence below.
      </div>
      <div class="sentence-line"></div>
      <div class="sentence-line"></div>
    </div>

  </section>

  <footer class="ph-foot">
    <span>字图 · ZìTú · Pack {{ pack_num }} · {{ pack_title }} · Practice {{ p.position_str }}</span>
    <span>NAME ________________________ &nbsp;&nbsp;&nbsp; DATE ____________</span>
  </footer>
</section>
{% endfor %}

</body>
</html>
"""


# ── Builder ────────────────────────────────────────────────────────────────────

def build_practice(pack_num: str):
    manifest = load_json(DATA / "pack_manifest.json")
    pack_key = f"pack-{int(pack_num):02d}"
    display_num = f"{int(pack_num):02d}"

    if pack_key not in manifest:
        raise ValueError(f"Pack '{pack_key}' not found in pack_manifest.json.")

    pack_meta = manifest[pack_key]
    pack_title = pack_meta.get("title", f"Pack {display_num}")
    pack_type_han = "象形"  # default; could be added to manifest if needed

    prepared_path = ROOT / "packs" / pack_key / "data" / "characters-prepared.json"
    if not prepared_path.exists():
        raise FileNotFoundError(
            f"{prepared_path.relative_to(ROOT)} not found. "
            f"Run: python prepare_pack.py --pack {display_num}"
        )
    prepared_list = load_json(prepared_path)
    char_lookup = {c["character"]: c for c in prepared_list}

    pack_chars = pack_meta["characters"]
    total = len(pack_chars)

    practices = []
    for pos, char in enumerate(pack_chars, 1):
        raw = char_lookup.get(char)
        if raw is None:
            print(f"  WARNING: {char} not found in characters-prepared.json — skipping")
            continue
        practices.append(prepare_practice(raw, display_num, pos, total))

    env = Environment(loader=BaseLoader())
    tmpl = env.from_string(_TEMPLATE)
    html = tmpl.render(
        pack_num=display_num,
        pack_title=pack_title,
        pack_type_han=pack_type_han,
        practices=practices,
    )

    out_dir = ROOT / "packs" / pack_key
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "practice.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"  wrote {out_path.relative_to(ROOT)}  ({len(practices)} practice sheets)")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Build practice sheets for a pack.")
    parser.add_argument("--pack", required=True, help="Pack number, e.g. 01")
    args = parser.parse_args()
    build_practice(args.pack)


if __name__ == "__main__":
    main()
