# 字图 ZìTú — Chinese Character Blueprints

Printable flashcard packs for learning Chinese characters. Each card shows the full story of a character: the strokes that build it, the scripts that write it, the words that grow from it.

Cards print duplex on landscape A4, cut to 135×190 mm (portrait). Front: character in 米字格 + stroke construction sequence. Back: script styles (宋/黑/楷/美/行), stroke reference, blueprint, word web, cultural note.

---

## Quick start

```bash
# 1. Set up
pip install -r requirements.txt

# 2. See what packs exist
python scripts/generate_pack.py --list

# 3. Build a pack (HTML only, no image fetch)
python scripts/generate_pack.py --pack 02 --skip-fetch

# 4. Build a pack with glyph images
python scripts/generate_pack.py --pack 02
```

Output lands in `packs/pack-02/index.html`. Open it in a browser, print at 100% scale on landscape A4, flip on the long edge.

---

## CLI reference

```
python scripts/generate_pack.py --pack N
```

| Flag | What it does |
|---|---|
| `--pack N` | Generate pack N (assign if needed → fetch images → build HTML) |
| `--skip-fetch` | Skip image download; rebuild HTML from existing data |
| `--force-fetch` | Re-download images even if they already exist |
| `--list` | Show all packs and their assigned characters |
| `--assign-only` | Run pack assignment and write manifest, then stop |

---

## File layout

```
zitu-cards/
  scripts/
    generate_pack.py    ← main CLI entry point
    assign_packs.py     ← assigns characters to packs, seeds characters.json
    fetch_resources.py  ← downloads oracle/bronze glyph images
    build_cards.py      ← renders Jinja2 HTML from character data

  data/
    characters.json     ← global character database (content fallback — see below)
    hsk1.json           ← ordered HSK 1 source list (drives pack assignment)
    pack_manifest.json  ← which characters go in which pack + pack metadata

  packs/
    pack-01/
      index.html                        ← script-generated output
      data/
        characters-manual.json          ← pack-specific content overrides (edit this)
        characters-prepared.json        ← merged, ready-to-render data (auto-generated)
      assets/
        glyphs/         ← {pinyin}-oracle.png, {pinyin}-bronze.png

  system/
    style.css           ← design system (all packs link here)
```

---

## Workflow for a new pack

### 1. Check the assignment

```bash
python scripts/generate_pack.py --list
```

Packs 01–10 are pre-assigned from HSK 1. To add more or inspect the assignment:

```bash
python scripts/generate_pack.py --assign-only
```

Then open `data/pack_manifest.json` and set `title`, `subtitle`, and `description` for the new pack before building.

### 2. Add content manually

There are two places to add content. The **pack-specific file takes precedence**.

#### Pack-specific file (preferred)

```
packs/pack-NN/data/characters-manual.json
```

Create this file if it doesn't exist. It's an array — one object per character:

```jsonc
[
  {
    "character": "我",
    "compounds": [
      {"zh": "我们", "pinyin": "wǒmen", "en": "we / us"},
      {"zh": "我的", "pinyin": "wǒde",  "en": "my / mine"},
      {"zh": "自我", "pinyin": "zìwǒ",  "en": "self"},
      {"zh": "我国", "pinyin": "wǒguó", "en": "our country"}
    ],
    "cultural_note": "The halberd (戈) was a prestige weapon — 我 may originally have meant a decorated weapon before becoming the first-person pronoun.",
    "blueprint": "Phonosemantic: 手 shǒu (hand) signals meaning; 戈 gē (halberd) approximates the sound.",
    "formula": "hand <span class=\"han\">手</span> + halberd <span class=\"han\">戈</span> = <span class=\"han\">我</span>",
    "mnemonic": "A hand holding a halberd — 'I' arm myself to stand apart."
  }
]
```

Only include the fields you want to override. Fields not present here fall back to `data/characters.json`.

#### Global fallback

```
data/characters.json
```

Same field names. Useful for content that applies across packs. Pack-specific values always win.

#### What each field renders on the card

| Field | Card side | Where it appears |
|---|---|---|
| `compounds` | Back | Word web — 4 compound words with pinyin and English gloss; the focus character is highlighted automatically |
| `cultural_note` | Back | Cultural note panel (indented quote block, left accent line) |
| `blueprint` | Back | Blueprint panel — etymology annotation; HTML allowed |
| `formula` | Back | Component formula line inside the blueprint panel; use `<span class="han">` for Chinese glyphs |
| `mnemonic` | — | Stored but not currently rendered on the card |

Any field left empty renders as a visible dashed placeholder — a reminder to fill it in.

### 3. Fetch glyph images

```bash
python scripts/generate_pack.py --pack 03
```

This downloads oracle bone and bronze script images from [chineseetymology.org](https://www.chineseetymology.org/) into `packs/pack-03/assets/glyphs/`. If an image is not found, a grey placeholder is saved and a warning is logged.

To re-fetch images that already exist:

```bash
python scripts/generate_pack.py --pack 03 --force-fetch
```

### 4. Build the HTML

```bash
python scripts/generate_pack.py --pack 03 --skip-fetch
```

Or to rebuild just the HTML for a pack whose data is already prepared:

```bash
python scripts/build_cards.py --pack 03
```

### 5. Iterate

Edit `packs/pack-NN/data/characters-manual.json`, then rebuild:

```bash
python scripts/build_cards.py --pack 03
```

The builder is fast (~instant). `prepare_pack.py` (which merges data and extracts stroke paths) only needs to re-run if the underlying stroke data changes.

---

## characters-manual.json field reference

These are the fields you edit. All are optional — omit any you haven't filled in yet.

| Field | Type | Notes |
|---|---|---|
| `character` | string | The hanzi — used to match against the prepared data |
| `compounds` | array | `{zh, pinyin, en}` × 4; focus character is highlighted automatically |
| `cultural_note` | string | Back card cultural/historical context; HTML allowed |
| `blueprint` | string | Etymology annotation; HTML allowed |
| `formula` | string | Component formula line; HTML allowed, use `<span class="han">` for glyphs |
| `mnemonic` | string | Mnemonic caption; stored but not currently rendered |

---

## characters.json full field reference

`data/characters.json` is the global database seeded by `assign_packs.py`. Edit it for content that spans packs, or as a base to copy from before creating a pack-specific manual file.

| Field | Type | Notes |
|---|---|---|
| `character` | string | The hanzi |
| `pinyin` | string | With tone marks: `rén`, `shuǐ` |
| `tone` | int | 1–4, or 0 for neutral |
| `type` | string | `pictograph` · `indicative` · `compound` · `phono-semantic` |
| `english` | array | First item = primary meaning on front card; rest = secondary |
| `hsk_level` | int | HSK level (1–6) |
| `radical` | string | Radical character |
| `radical_pinyin` | string | Radical pinyin with tone |
| `stroke_order` | array | `{n, han, name, pinyin}` per stroke — legacy field; stroke SVG paths come from makemeahanzi |
| `compounds` | array | `{zh, pinyin, en}` × 4 |
| `cultural_note` | string | HTML allowed |
| `blueprint` | string | HTML allowed |
| `formula` | string | HTML allowed |
| `mnemonic` | string | Stored, not rendered |

---

## pack_manifest.json metadata fields

```jsonc
"pack-03": {
  "characters": ["我","你","他","她","们","的","是","有","不","来"],
  "title": "People",                   // shown in cover header
  "subtitle": "Pronouns & presence",   // shown in cover header
  "description": "...",               // HTML, shown as lede paragraph
  "type_note": "Pack 03 = ...",       // shown in type-badge legend panel
  "series": "一",
  "volume": "03"
}
```

---

## Printing

1. Open `packs/pack-NN/index.html` in Chrome or Firefox
2. File → Print (or Cmd/Ctrl+P)
3. Paper size: **A4**; Orientation: **Landscape**; Scale: **100%**; Margins: **None**
4. Enable **background graphics**
5. Duplex: **flip on long edge** — back sheets are in the same column order as fronts, no mirroring needed
6. Cut along the **vertical dashed centre line** — finished card size 135×190 mm (portrait)
