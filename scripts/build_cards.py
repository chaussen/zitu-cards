"""
build_cards.py — generate packs/pack-{N}/index.html from characters-prepared.json.

Usage:
    python scripts/build_cards.py --pack 01
"""
import argparse
import json
import math
import re
from pathlib import Path

from jinja2 import Environment, BaseLoader

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"

# ── Pinyin helpers ─────────────────────────────────────────────────────────────

_TONE_MAP = {
    "ā": ("a", 1), "á": ("a", 2), "ǎ": ("a", 3), "à": ("a", 4),
    "ē": ("e", 1), "é": ("e", 2), "ě": ("e", 3), "è": ("e", 4),
    "ī": ("i", 1), "í": ("i", 2), "ǐ": ("i", 3), "ì": ("i", 4),
    "ō": ("o", 1), "ó": ("o", 2), "ǒ": ("o", 3), "ò": ("o", 4),
    "ū": ("u", 1), "ú": ("u", 2), "ǔ": ("u", 3), "ù": ("u", 4),
    "ǖ": ("ü", 1), "ǘ": ("ü", 2), "ǚ": ("ü", 3), "ǜ": ("ü", 4),
}
_BARE_MAP = {k: v[0] for k, v in _TONE_MAP.items()}
_BARE_MAP["ü"] = "u"


def pinyin_bare(pinyin: str) -> str:
    for t, b in _BARE_MAP.items():
        pinyin = pinyin.replace(t, b)
    return pinyin


def pinyin_html(pinyin: str) -> str:
    for toned, (_, tone_num) in _TONE_MAP.items():
        if toned in pinyin:
            idx = pinyin.index(toned)
            return (
                pinyin[:idx]
                + f'<span class="tm-{tone_num}">{toned}</span>'
                + pinyin[idx + 1:]
            )
    return pinyin


# ── Type metadata ──────────────────────────────────────────────────────────────

_TYPE_INFO = {
    "pictograph":    {"css": "pictograph", "han": "象形", "en": "Pictograph",    "phrase": "self-contained pictograph"},
    "indicative":    {"css": "indicative", "han": "指事", "en": "Indicative",    "phrase": "abstract indicative"},
    "ideograph":     {"css": "indicative", "han": "指事", "en": "Indicative",    "phrase": "abstract indicative"},
    "compound":      {"css": "compound",   "han": "会意", "en": "Compound",      "phrase": "compound ideograph"},
    "phono-semantic":{"css": "phonosem",   "han": "形声", "en": "Phono-semantic","phrase": "phono-semantic compound"},
}


# ── Zone 1: stroke construction sequence (front card) ─────────────────────────

_INK    = "#1a1614"
_ACCENT = "#a78a3d"   # dark gold — visible on light paper background
_SVG_TRANSFORM = 'translate(0,900) scale(1,-1)'


def _compute_stages(n: int) -> list:
    """Compute which stage indices to show as Zone 1 frames."""
    if n == 0:
        return []
    if n <= 8:
        stages = list(range(1, n + 1))
    elif n <= 12:
        stages = list(range(2, n + 1, 2))
        if n not in stages:
            stages.append(n)
    else:
        stages = list(range(3, n + 1, 3))
        if n not in stages:
            stages.append(n)
    # Cap at 6 frames
    while len(stages) > 6:
        step = math.ceil(n / 5)
        stages = list(range(step, n + 1, step))
        if n not in stages:
            stages.append(n)
        stages = sorted(set(stages))
    return stages


def _render_stroke_frame(strokes: list, stage: int, n: int, is_final: bool) -> str:
    """Render one SVG construction frame."""
    parts = []
    if is_final:
        for s in strokes:
            parts.append(f'<path fill="{_INK}" d="{s["path"]}"/>')
    else:
        for s in strokes[:stage - 1]:
            parts.append(f'<path fill="{_INK}" d="{s["path"]}"/>')
        parts.append(f'<path fill="{_ACCENT}" d="{strokes[stage - 1]["path"]}"/>')
        for s in strokes[stage:]:
            parts.append(f'<path fill="{_INK}" fill-opacity="0.12" d="{s["path"]}"/>')

    inner = "".join(parts)
    label = "" if is_final else f'<span class="sb-num">{stage}</span>'
    return (
        f'<div class="sb-fw">'
        f'<svg class="sb-f" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">'
        f'<g transform="{_SVG_TRANSFORM}">{inner}</g>'
        f'</svg>'
        f'{label}</div>'
    )


def render_zone1(strokes: list) -> str:
    """Generate Zone 1 HTML (stroke construction sequence)."""
    if not strokes:
        return '<div class="sb-missing">STROKE DATA MISSING</div>'
    n = len(strokes)
    stages = _compute_stages(n)
    frames = [_render_stroke_frame(strokes, st, n, st == n) for st in stages]
    return f'<div class="sb-frames">{"".join(frames)}</div>'


# ── Zone 2: stroke order reference (back card) ────────────────────────────────

def _zone2_part_a_stages(n: int) -> list:
    """Compute up to 4 stages for Zone 2 Part A."""
    if n <= 4:
        return list(range(1, n + 1))
    mid = max(2, n // 2)
    second_last = n - 1
    stages = sorted(set([1, mid, second_last, n]))
    return stages[:4]


def render_zone2(strokes: list) -> str:
    """Generate Zone 2 HTML (Part A: mini sequence + Part B: stroke name list)."""
    if not strokes:
        return '<div class="sref-missing">STROKE DATA MISSING</div>'
    n = len(strokes)

    # Part A: miniature construction sequence
    stages_a = _zone2_part_a_stages(n)
    frames_a = [_render_stroke_frame(strokes, st, n, st == n) for st in stages_a]
    part_a = f'<div class="sref-a">{"".join(frames_a)}</div>'

    # Part B: stroke name list
    rows = []
    for s in strokes:
        zh = s.get("name_zh", "—")
        py = s.get("name_py", "—")
        en = s.get("name_en", "—")
        if zh == "UNMATCHED":
            zh = py = en = "—"
            extra = ' class="srow-unmatched"'
        else:
            extra = ""
        svg = (
            f'<svg class="srow-f" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">'
            f'<g transform="{_SVG_TRANSFORM}">'
            f'<path fill="{_INK}" d="{s["path"]}"/>'
            f'</g></svg>'
        )
        rows.append(
            f'<div class="srow">'
            f'<span class="srow-n">{s["order"]}</span>'
            f'{svg}'
            f'<span class="srow-zh"{extra}>{zh}</span>'
            f'<span class="srow-py">{py}</span>'
            f'<span class="srow-en">{en}</span>'
            f'</div>'
        )
    part_b = f'<div class="sref-b">{"".join(rows)}</div>'

    return part_a + part_b


# ── Data preparation ───────────────────────────────────────────────────────────

def prepare_card(raw: dict, pack_num: str, position: int) -> dict:
    char_type = raw.get("character_type", "pictograph").lower()
    type_info = _TYPE_INFO.get(char_type, _TYPE_INFO["pictograph"])
    tone = raw.get("tone", 0)
    py = raw.get("pinyin", "")

    english_primary = raw.get("english_primary", "")
    english_rest = raw.get("english_secondary", [])

    compounds = raw.get("compounds", [])
    while len(compounds) < 4:
        compounds = list(compounds) + [None]

    strokes = raw.get("strokes", [])
    stroke_count = raw.get("stroke_count", len(strokes))

    return {
        "character":       raw["character"],
        "pinyin":          py,
        "pinyin_bare":     pinyin_bare(py),
        "pinyin_html":     pinyin_html(py),
        "tone":            tone,
        "tone_class":      f"t{tone}" if tone else "tn",
        "tone_label":      str(tone) if tone else "·",
        "type_css":        type_info["css"],
        "type_han":        type_info["han"],
        "type_en":         type_info["en"],
        "type_phrase":     type_info["phrase"],
        "character_type":  char_type,
        "english_primary": english_primary,
        "english_rest":    english_rest,
        "stroke_count":    stroke_count,
        "radical":         raw.get("radical", ""),
        "radical_pinyin":  raw.get("radical_pinyin", ""),
        "hsk_level":       raw.get("hsk_level", 1),
        "compounds":       compounds,
        "blueprint":       raw.get("blueprint", ""),
        "formula":         raw.get("formula", ""),
        "cultural_note":   raw.get("cultural_note", ""),
        "mnemonic":        raw.get("mnemonic", ""),
        "zone1_html":      render_zone1(strokes),
        "zone2_html":      render_zone2(strokes),
        "pack_num":        pack_num,
        "pack_position":   position,
    }


def mirror_batch(batch: list) -> list:
    """[A,B,C,D] → [B,A,D,C] for duplex printing."""
    out = []
    for i in range(0, len(batch), 2):
        pair = batch[i:i + 2]
        out.extend(reversed(pair))
    return out


def compute_sheets(cards: list) -> list:
    sheets = []
    pair_count = (len(cards) + 1) // 2
    for pair_idx in range(pair_count):
        start = pair_idx * 2
        batch = cards[start:start + 2]
        first_pos = batch[0]["pack_position"]
        last_pos = batch[-1]["pack_position"]
        sheet_num = pair_idx * 2 + 1
        sheets.append({
            "type": "front",
            "pair_idx": pair_idx + 1,
            "sheet_num": sheet_num,
            "total_pairs": pair_count,
            "cards": batch,
            "screen_label": f"{sheet_num:02d} Fronts {first_pos}–{last_pos}",
            "first_pos": first_pos,
            "last_pos": last_pos,
        })
        back_range = (
            f"{batch[0]['pack_position']:02d}–{batch[1]['pack_position']:02d}"
            if len(batch) >= 2
            else f"{batch[0]['pack_position']:02d}"
        )
        sheets.append({
            "type": "back",
            "pair_idx": pair_idx + 1,
            "sheet_num": sheet_num + 1,
            "total_pairs": pair_count,
            "cards": batch,
            "screen_label": f"{sheet_num + 1:02d} Backs {first_pos}–{last_pos}",
            "back_range": back_range,
            "first_pos": first_pos,
            "last_pos": last_pos,
        })
    return sheets


# ── Jinja2 template ────────────────────────────────────────────────────────────

_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>字图 ZìTú — Pack {{ pack_num }} · {{ pack_meta.title }}</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Long+Cang&family=Liu+Jian+Mao+Cao&family=ZCOOL+XiaoWei&family=ZCOOL+QingKe+HuangYou&family=Noto+Serif+SC:wght@400;700;900&family=Noto+Sans+SC:wght@400;700&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=DM+Sans:wght@300;400;500;700&family=Noto+Sans:wght@400;500&family=IBM+Plex+Mono:wght@300;400;500&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="../../system/style.css">
</head>
<body>

<div class="shell">
  <header class="brand">
    <div class="mark"><span>字</span></div>
    <div>
      <div class="tag">字图 · ZìTú · Chinese character blueprints</div>
      <h1 class="name"><em>字图</em> — a character's <span style="font-style:italic">blueprint</span>.</h1>
      <div class="tag">Pack {{ pack_num }} · {{ pack_meta.title }} &nbsp;·&nbsp; {{ pack_meta.subtitle }} &nbsp;·&nbsp; Series {{ pack_meta.series }} / Vol. {{ pack_meta.volume }}</div>
    </div>
    <div class="seal-pip">印</div>
  </header>

  <p class="lede">{{ pack_meta.description | safe }}</p>

  <section class="spec-grid">

    <div class="panel span-5">
      <h3>Palette</h3>
      <p class="lead">Paper · ink · cinnabar. One dark panel for the etymological strip.</p>
      <div class="swatches">
        <div class="swatch" style="background:var(--paper); color:var(--ink)"><span class="nm">Paper</span><span class="hx">#F3ECE0</span></div>
        <div class="swatch" style="background:var(--paper-soft); color:var(--ink)"><span class="nm">Paper / soft</span><span class="hx">#EBE2D2</span></div>
        <div class="swatch" style="background:var(--ink); color:var(--paper)"><span class="nm">Ink</span><span class="hx">#1A1614</span></div>
        <div class="swatch" style="background:var(--ink-soft); color:var(--paper)"><span class="nm">Ink / soft</span><span class="hx">#5A4F44</span></div>
        <div class="swatch" style="background:var(--rule); color:var(--ink)"><span class="nm">Rule</span><span class="hx">#D8CDB8</span></div>
        <div class="swatch" style="background:var(--seal); color:var(--paper-on-dk)"><span class="nm">Seal</span><span class="hx">#B83A25</span></div>
        <div class="swatch" style="background:var(--midnight); color:var(--paper-on-dk)"><span class="nm">Midnight</span><span class="hx">#1C1A24</span></div>
        <div class="swatch" style="background:var(--gold-on-dk); color:var(--midnight)"><span class="nm">Gold / dk</span><span class="hx">#C9A960</span></div>
      </div>
    </div>

    <div class="panel span-3">
      <h3>Tone coding</h3>
      <p class="lead">A colour you can <em>feel</em> before you can read.</p>
      <div class="keys">
        <div class="key"><span class="dot" style="background:var(--tone-1)"></span><span class="l1">Tone 1 · level</span><span class="l2">ˉ</span><span class="han">妈</span></div>
        <div class="key"><span class="dot" style="background:var(--tone-2)"></span><span class="l1">Tone 2 · rising</span><span class="l2">ˊ</span><span class="han">麻</span></div>
        <div class="key"><span class="dot" style="background:var(--tone-3)"></span><span class="l1">Tone 3 · dipping</span><span class="l2">ˇ</span><span class="han">马</span></div>
        <div class="key"><span class="dot" style="background:var(--tone-4)"></span><span class="l1">Tone 4 · falling</span><span class="l2">ˋ</span><span class="han">骂</span></div>
        <div class="key"><span class="dot" style="background:var(--tone-n)"></span><span class="l1">Neutral · 轻声</span><span class="l2">·</span><span class="han">吗</span></div>
      </div>
    </div>

    <div class="panel span-4">
      <h3>Character-type badges</h3>
      <p class="lead">Every card opens with how the character was built. {{ pack_meta.type_note | safe }}</p>
      <div class="keys">
        <div class="key"><span class="dot" style="background:var(--type-pict)"></span><span class="l1">象形 · pictograph</span><span class="l2">image</span><span class="han">山</span></div>
        <div class="key"><span class="dot" style="background:var(--type-ideo)"></span><span class="l1">指事 · indicative</span><span class="l2">concept</span><span class="han">大</span></div>
        <div class="key"><span class="dot" style="background:var(--type-comp)"></span><span class="l1">会意 · compound</span><span class="l2">meaning</span><span class="han">明</span></div>
        <div class="key"><span class="dot" style="background:var(--type-phon)"></span><span class="l1">形声 · phono-sem.</span><span class="l2">sound</span><span class="han">妈</span></div>
      </div>
    </div>

    <div class="panel span-6">
      <h3>Typography</h3>
      <p class="lead">Handwritten Kaiti (楷体) for hanzi — clean enough to study, warm enough to want to copy.</p>
      <div class="type-grid">
        <div class="type-row"><div class="lbl">Hanzi · 楷</div><div class="han-sample">永 山 月 大</div></div>
        <div class="type-row"><div class="lbl">Hanzi · 篆</div><div class="seal-sample">永 山 月 大</div></div>
        <div class="type-row"><div class="lbl">Hanzi · 隶</div><div class="clerc-sample">永 山 月 大</div></div>
        <div class="type-row"><div class="lbl">Display</div><div class="disp-sample">A character's blueprint</div></div>
        <div class="type-row"><div class="lbl">Body</div><div class="body-sample">Foundational characters for the modern classroom.</div></div>
        <div class="type-row"><div class="lbl">Mono</div><div class="mono-sample">Pack {{ pack_num }} · 01/10 · Pictograph</div></div>
      </div>
    </div>

    <div class="panel span-6">
      <h3>Pack {{ pack_num }} · {{ pack_meta.title }}</h3>
      <p class="lead">{{ pack_meta.subtitle }}</p>
      <div class="roster">
        {% for c in cards %}
        <div class="pip"><span class="tn" style="background:var(--tone-{{ c.tone if c.tone else 'n' }})"></span><div class="han">{{ c.character }}</div><div class="py">{{ c.pinyin }}</div><div class="num">{{ '%02d'|format(c.pack_position) }}</div></div>
        {% endfor %}
      </div>
    </div>

  </section>

  <section class="instructions">
    <div class="stp"><div class="n">壹</div><h4>Print</h4><p>A4 stock at <strong>100% scale</strong>, 120 gsm or heavier. 米字格 grids print at hairline weight so they don't compete with the character.</p></div>
    <div class="stp"><div class="n">贰</div><h4>Duplex</h4><p>Landscape A4 · <strong>flip on long edge</strong>. Back sheets print in the same column order as fronts — no mirroring needed.</p></div>
    <div class="stp"><div class="n">叁</div><h4>Cut &amp; sort</h4><p>Cut along the vertical dashed centre line. Cards finish at <strong>135×190mm</strong> (portrait). Stack by tone, formation type, or HSK level.</p></div>
    <div class="stp"><div class="n">肆</div><h4>Use</h4><p>Quiz with the front. Study with the back. Drill on the practice sheet. Display the poster. <strong>One pack a week.</strong></p></div>
  </section>

  <div class="preview-strip"><span class="dot">●</span>&nbsp;&nbsp;Preview · the pages below are what will print</div>
</div>

<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <defs>
    <symbol id="mz" viewBox="0 0 100 100" preserveAspectRatio="none">
      <rect class="frame" x="0.4" y="0.4" width="99.2" height="99.2" fill="none" stroke="#c8b89c" stroke-width="0.55"/>
      <line x1="0" y1="50" x2="100" y2="50" stroke="#c8b89c" stroke-width="0.22" stroke-dasharray="1 1.2"/>
      <line x1="50" y1="0" x2="50" y2="100" stroke="#c8b89c" stroke-width="0.22" stroke-dasharray="1 1.2"/>
      <line x1="0" y1="0" x2="100" y2="100" stroke="#c8b89c" stroke-width="0.22" stroke-dasharray="1 1.2"/>
      <line x1="100" y1="0" x2="0" y2="100" stroke="#c8b89c" stroke-width="0.22" stroke-dasharray="1 1.2"/>
    </symbol>
  </defs>
</svg>

{% for sheet in sheets %}
{%- if sheet.type == 'front' %}
<!--
═══════════════════════════════════════════════════════════════
  SHEET {{ sheet.sheet_num }} — FRONTS · cards {{ '%02d'|format(sheet.first_pos) }}–{{ '%02d'|format(sheet.last_pos) }}
═══════════════════════════════════════════════════════════════
-->
<section class="sheet a4" data-screen-label="{{ sheet.screen_label }}">
  <div class="sheet-mark">
    <span>字图 · PACK {{ pack_num }} · {{ pack_meta.title | upper }} · FRONT {{ sheet.pair_idx }}/{{ sheet.total_pairs }}</span>
    <span><span class="pip">●</span> {{ '%02d'|format(sheet.first_pos) }}–{{ '%02d'|format(sheet.last_pos) }}</span>
  </div>
  <div class="cut-line"></div>
  {% for c in sheet.cards %}
  {{ render_front(c) }}
  {% endfor %}
</section>

{%- else %}
<!--
═══════════════════════════════════════════════════════════════
  SHEET {{ sheet.sheet_num }} — BACKS · cards {{ '%02d'|format(sheet.first_pos) }}–{{ '%02d'|format(sheet.last_pos) }}
═══════════════════════════════════════════════════════════════
-->
<section class="sheet a4" data-screen-label="{{ sheet.screen_label }}">
  <div class="sheet-mark">
    <span><span class="pip">●</span> {{ sheet.back_range }}</span>
    <span>字图 · PACK {{ pack_num }} · {{ pack_meta.title | upper }} · BACK {{ sheet.pair_idx }}/{{ sheet.total_pairs }}</span>
  </div>
  <div class="cut-line"></div>
  {% for c in sheet.cards %}
  {{ render_back(c) }}
  {% endfor %}
</section>
{% endif %}
{% endfor %}

</body>
</html>
"""

_FRONT_CARD = r"""
  <!-- {{ '%02d'|format(c.pack_position) }} {{ c.character }} {{ c.pinyin }} · tone {{ c.tone }} · {{ c.type_en }} -->
  <article class="card front" data-tone="{{ c.tone }}" data-type="{{ c.type_css }}">
    <div class="card-head">
      <span class="type-badge {{ c.type_css }}"><span class="han">{{ c.type_han }}</span>{{ c.type_en }}</span>
      <span class="card-ref">Pack {{ c.pack_num }} · <strong>{{ '%02d'|format(c.pack_position) }}/10</strong></span>
    </div>
    <div class="hero">
      <div class="grid-box">
        <svg class="mizige"><use href="#mz"/></svg>
        <span class="han">{{ c.character }}</span>
      </div>
      <div class="stroke-build">
        {{ c.zone1_html | safe }}
      </div>
    </div>
    <div class="pinyin-bar">
      <span class="tone-dot {{ c.tone_class }}">{{ c.tone_label }}</span>
      <span class="pinyin">{{ c.pinyin_html | safe }}</span>
      <span class="seal-stamp">{{ c.character }}</span>
    </div>
    <div class="meaning">{{ c.english_primary }}{% if c.english_rest %} <em>· {{ c.english_rest | join(' · ') }}</em>{% endif %}</div>
  </article>
"""

_BACK_CARD = r"""
  <!-- BACK {{ '%02d'|format(c.pack_position) }} {{ c.character }} -->
  <article class="card back" data-tone="{{ c.tone }}" data-type="{{ c.type_css }}">
    <div class="card-head">
      <span class="card-ref" style="text-align:left">Pack {{ c.pack_num }} · <strong>{{ '%02d'|format(c.pack_position) }}/10</strong></span>
      <span class="han-mini">{{ c.character }}</span>
    </div>
    <div class="script-strip">
      <div class="strip-head">书体变奏 · Script Styles</div>
      <div class="slots">
        <div class="slot">
          <span class="glyph song">{{ c.character }}</span>
          <span class="style-zh">宋体</span>
          <span class="style-ro">Sōng</span>
          <span class="context">print · books</span>
        </div>
        <div class="slot">
          <span class="glyph hei">{{ c.character }}</span>
          <span class="style-zh">黑体</span>
          <span class="style-ro">Hēi</span>
          <span class="context">screens · signs</span>
        </div>
        <div class="slot">
          <span class="glyph kai">{{ c.character }}</span>
          <span class="style-zh">楷体</span>
          <span class="style-ro">Kǎi</span>
          <span class="context">handwriting</span>
        </div>
        <div class="slot">
          <span class="glyph mei">{{ c.character }}</span>
          <span class="style-zh">美术体</span>
          <span class="style-ro">Měishù</span>
          <span class="context">titles · art</span>
        </div>
        <div class="slot">
          <span class="glyph xing">{{ c.character }}</span>
          <span class="style-zh">行书</span>
          <span class="style-ro">Xíng</span>
          <span class="context">fast writing</span>
        </div>
      </div>
    </div>
    <div class="stroke-ref">
      {{ c.zone2_html | safe }}
    </div>
    <section class="bp">
      <div class="lbl">Blueprint <em>{{ c.type_phrase }}</em></div>
      <div class="body">
        <div class="glyph">{{ c.character }}</div>
        {% if c.blueprint %}
        <div class="ann">{{ c.blueprint | safe }}</div>
        {% else %}
        <div class="ann" style="border:1.5px dashed #c8b89c;padding:6px;color:#a08060;font-size:10px">ADD: blueprint annotation</div>
        {% endif %}
      </div>
      {% if c.formula %}
      <div class="formula">{{ c.formula | safe }}</div>
      {% else %}
      <div class="formula" style="border:1.5px dashed #c8b89c;padding:4px;color:#a08060;font-size:10px">ADD: formula</div>
      {% endif %}
    </section>
    <div class="web">
      <div class="lbl">Word web<em>4 common compounds</em></div>
      <div class="items">
        {% for comp in c.compounds %}
        {% if comp %}
        <div class="w">
          <div class="ch">{{ comp.zh | replace(c.character, '<span class="focus">' + c.character + '</span>') | safe }}</div>
          <div class="gloss">{{ comp.pinyin }}<span class="en">{{ comp.en }}</span></div>
        </div>
        {% else %}
        <div class="w" style="border:1.5px dashed #c8b89c;padding:4px;color:#a08060;font-size:10px">ADD: compound</div>
        {% endif %}
        {% endfor %}
      </div>
    </div>
    <div class="culture">
      <span class="lead">Cultural note</span>
      {% if c.cultural_note %}
      {{ c.cultural_note | safe }}
      {% else %}
      <span style="border:1.5px dashed #c8b89c;padding:4px;color:#a08060;font-size:10px">ADD: cultural note</span>
      {% endif %}
    </div>
    <div class="stats">
      <div class="cell"><div class="k">Strokes</div><div class="v">{{ c.stroke_count if c.stroke_count else '?' }}</div></div>
      <div class="cell"><div class="k">Radical</div><div class="v">{% if c.radical %}<span class="han">{{ c.radical }}</span> {{ c.radical_pinyin }}{% else %}<span style="color:#a08060">ADD</span>{% endif %}</div></div>
      <div class="cell"><div class="k">HSK</div><div class="v">Level {{ c.hsk_level }}</div></div>
      <div class="cell"><div class="k">Type</div><div class="v">{{ c.type_han }}</div></div>
    </div>
  </article>
"""


# ── Renderer ───────────────────────────────────────────────────────────────────

class _StringLoader(BaseLoader):
    def get_source(self, environment, template):
        raise RuntimeError("use from_string only")


def _make_env() -> Environment:
    env = Environment(loader=_StringLoader(), autoescape=False)
    ft = env.from_string(_FRONT_CARD)
    bt = env.from_string(_BACK_CARD)
    env.globals["render_front"] = lambda c: ft.render(c=c)
    env.globals["render_back"]  = lambda c: bt.render(c=c)
    return env


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_pack(pack_num: str):
    manifest = load_json(DATA / "pack_manifest.json")
    pack_key = f"pack-{int(pack_num):02d}"
    display_num = f"{int(pack_num):02d}"

    if pack_key not in manifest:
        raise ValueError(
            f"Pack '{pack_key}' not found in pack_manifest.json. "
            "Run assign_packs.py first."
        )

    pack_meta_raw = manifest[pack_key]
    pack_meta = {
        "title":       pack_meta_raw.get("title", f"Pack {pack_num}"),
        "subtitle":    pack_meta_raw.get("subtitle", ""),
        "description": pack_meta_raw.get("description", ""),
        "type_note":   pack_meta_raw.get("type_note", ""),
        "series":      pack_meta_raw.get("series", "一"),
        "volume":      pack_meta_raw.get("volume", pack_num),
    }

    # Read from characters-prepared.json
    prepared_path = ROOT / "packs" / pack_key / "data" / "characters-prepared.json"
    if not prepared_path.exists():
        raise FileNotFoundError(
            f"{prepared_path.relative_to(ROOT)} not found. "
            f"Run: python prepare_pack.py --pack {display_num}"
        )
    prepared_list = load_json(prepared_path)
    char_lookup = {c["character"]: c for c in prepared_list}

    pack_chars = pack_meta_raw["characters"]

    cards: list = []
    for pos, char in enumerate(pack_chars, 1):
        raw = char_lookup.get(char)
        if raw is None:
            print(f"  WARNING: {char} not found in characters-prepared.json — skipping")
            continue
        cards.append(prepare_card(raw, display_num, pos))

    sheets = compute_sheets(cards)

    env = _make_env()
    tmpl = env.from_string(_TEMPLATE)
    html = tmpl.render(
        pack_num=display_num,
        pack_meta=pack_meta,
        cards=cards,
        sheets=sheets,
    )

    out_dir = ROOT / "packs" / pack_key
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"  wrote {out_path.relative_to(ROOT)}  ({len(cards)} cards, {len(sheets)} sheets)")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Build HTML for a pack.")
    parser.add_argument("--pack", required=True, help="Pack number, e.g. 01")
    args = parser.parse_args()
    build_pack(args.pack)


if __name__ == "__main__":
    main()
