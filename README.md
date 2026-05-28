# 字图 ZìTú — Chinese Character Blueprints

Printable flashcard packs for learning Chinese characters. Each card shows the full story of a character: the picture it came from, the strokes that build it, the words that grow from it.

Cards print duplex A4, cut to 100×142 mm. Front: character + mnemonic. Back: etymology, stroke order, word web, cultural note.

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

Output lands in `packs/pack-02/index.html`. Open it in a browser, print at 100% scale on A4, flip on the long edge.

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
    characters.json     ← master character database (edit this to fill in content)
    hsk1.json           ← ordered HSK 1 source list (drives pack assignment)
    pack_manifest.json  ← which characters go in which pack + pack metadata

  packs/
    pack-01/            ← hand-authored (Elements: 人水火山木日月大小心)
    pack-02/            ← generated output
      index.html
      assets/
        glyphs/         ← {pinyin}-oracle.png, {pinyin}-bronze.png
        mnemonics/      ← {pinyin}-mnemonic.png

  system/
    style.css           ← design system (all packs link here)
    template.html       ← blank structural reference
    symbols.html        ← reusable SVG defs

  requirements.txt
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

### 2. Fill in the data (optional but recommended)

Open `data/characters.json` and find the characters for your pack. Each entry has these content fields you can fill in manually:

```jsonc
{
  "character": "我",
  "pinyin": "wǒ",
  "mnemonic": "A hand holding a halberd — 'I' arm myself to stand apart.",
  "blueprint": "Phonosemantic: 手 shǒu (hand) signals meaning; 戈 gē (halberd) approximate sound.",
  "formula": "hand <span class=\"han\">手</span> + halberd <span class=\"han\">戈</span> = <span class=\"han\">我</span>",
  "cultural_note": "The halberd (戈) was a prestige weapon — 我 may originally have meant a decorated weapon before becoming the first-person pronoun.",
  "compounds": [
    {"zh": "我们", "pinyin": "wǒmen", "en": "we/us"},
    {"zh": "我的", "pinyin": "wǒde", "en": "my/mine"},
    {"zh": "自我", "pinyin": "zìwǒ", "en": "self"},
    {"zh": "我国", "pinyin": "wǒguó", "en": "our country"}
  ],
  "stroke_order": [
    {"n": 1, "han": "丿", "name": "撇", "pinyin": "piě"},
    ...
  ],
  "strokes": 7,
  "radical": "戈",
  "radical_pinyin": "gē"
}
```

Any field left blank renders as a visible dashed placeholder in the card — a reminder to fill it in later.

### 3. Fetch glyph images

```bash
python scripts/generate_pack.py --pack 03
```

This downloads oracle bone and bronze script images from [chineseetymology.org](https://www.chineseetymology.org/) into `packs/pack-03/assets/glyphs/`. If an image is not found, a grey placeholder is saved and a warning is logged.

To re-fetch images that already exist:

```bash
python scripts/generate_pack.py --pack 03 --force-fetch
```

To fetch a single character only:

```bash
python scripts/fetch_resources.py --pack 03 --char 我
```

### 4. Build the HTML

```bash
python scripts/generate_pack.py --pack 03 --skip-fetch
```

Opens `packs/pack-03/index.html` in a browser to review. Mnemonic images go in `packs/pack-03/assets/mnemonics/{pinyin}-mnemonic.png` — drop them in and reload.

### 5. Iterate

Fill in more content in `characters.json`, then rebuild:

```bash
python scripts/generate_pack.py --pack 03 --skip-fetch
```

The builder is fast (~instant). Fetch is the slow step; skip it unless images changed.

---

## characters.json field reference

| Field | Type | Notes |
|---|---|---|
| `character` | string | The hanzi |
| `pinyin` | string | With tone marks: `rén`, `shuǐ` |
| `tone` | int | 1–4, or 0 for neutral |
| `type` | string | `pictograph` · `indicative` · `compound` · `phono-semantic` |
| `english` | array | First item = primary meaning shown on front |
| `hsk_level` | int | HSK level (1–6) |
| `strokes` | int | Total stroke count |
| `radical` | string | Radical character |
| `radical_pinyin` | string | Radical pinyin with tone |
| `stroke_order` | array | `{n, han, name, pinyin}` per stroke; max 4 shown |
| `compounds` | array | `{zh, pinyin, en}` × 4; focus character is highlighted automatically |
| `mnemonic` | string | Front card caption |
| `blueprint` | string | Back card etymology annotation (HTML allowed) |
| `formula` | string | Component formula line (HTML allowed, use `<span class="han">`) |
| `cultural_note` | string | Back card cultural context (HTML allowed) |
| `pack` | string | `"01"` – `"10"` |
| `pack_position` | int | 1–10 within the pack |

---

## pack_manifest.json metadata fields

```jsonc
"pack-03": {
  "characters": ["我","你","他","她","们","的","是","有","不","来"],
  "title": "People",               // shown in cover header
  "subtitle": "Pronouns & presence",  // shown in cover header
  "description": "...",            // HTML, shown as lede paragraph
  "type_note": "Pack 03 = ...",    // shown in type-badge legend panel
  "series": "一",
  "volume": "03"
}
```

---

## Printing

1. Open `packs/pack-NN/index.html` in Chrome or Firefox
2. File → Print (or Cmd/Ctrl+P)
3. Paper size: **A4**; Scale: **100%**; Margins: **None**
4. Enable **background graphics**
5. Duplex: **flip on long edge**
6. Cut along the card borders — finished size 100×142 mm
