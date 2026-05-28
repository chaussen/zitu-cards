# 字图 ZìTú — How to build a pack

The build manual for new packs in the **字图 ZìTú** Chinese-character
learning system. Read this end-to-end before touching files.

The reference implementation is `ZìTú Pack 01 — Elements.html` at the
project root. When in doubt, copy from Pack 01 — it is the canonical
example of every card type.

---

## 0. What is a pack?

A pack is a printable kit for learning **ten simplified Chinese
characters** that share a theme. Each pack contains:

| Pages | Format | Contents |
|---|---|---|
| 6 sheets | A4, 4 cards per sheet | 3 fronts + 3 backs, duplex-mirrored. 10 character cards + 2 colophon tiles. |
| 1 sheet | A4 portrait | Sample practice sheet for the lead character (7 activity zones). |
| 1 sheet | A3 landscape | Sample classroom poster for the lead character. |

Plus a **screen-only cover** showing the design system at a glance:
brand strip, palette, tone-coding key, type-coding key, typography
specimen, roster of the ten characters, print instructions.

A printed-and-cut pack yields **10 double-sided flashcards** at
92 × 135 mm, one practice sheet, and one poster.

### Print geometry (do not change without versioning)

- **Card:** 92 × 135 mm — fits 4-up on a 190 × 277 mm safe area
  (A4 minus 10 mm `@page` margin all around).
- **Sheet:** 190 × 277 mm portrait (cards + practice), 400 × 277 mm
  landscape (poster). Sheets display in HTML at the **exact size they
  will print** — there's no scaling, no surprise clipping.
- **`@page` rules** (in `zitu.css`):
  ```css
  @page          { size: A4; margin: 10mm; }
  @page poster   { size: A3 landscape; margin: 10mm; }
  .sheet.a3-landscape { page: poster; }
  ```
  This makes a single file print as **7 × A4 portrait + 1 × A3
  landscape** automatically — the user just sends to the printer.

---

## 1. Folder layout

```
project-root/
├── ZìTú Pack 01 — Elements.html      ← reference; do not modify casually
├── ZìTú Pack 02 — Numbers.html       ← new packs go at root
├── ZìTú Pack NN — <Theme>.html
└── _system/
    ├── README.md
    ├── HOW-TO-BUILD-A-PACK.md        ← this file
    ├── zitu.css                      ← the canonical stylesheet
    └── zitu-symbols.html             ← reusable SVG <symbol> library
```

Filename convention: **`ZìTú Pack NN — <Theme>.html`** — em-dash, Title-case theme.
Pack number is two-digit, zero-padded. Theme is the same word used on
the cover (Elements, Numbers, Time, Family, Nature, …).

---

## 2. The five series

Series 一 (Foundations) is the launch plan. Pack themes and characters
are listed here so any pack-2/3/4 spec can be picked up later without
re-deciding the character set.

| Pack | Theme | Characters |
|---|---|---|
| 01 | Elements | 人 水 火 山 木 日 月 大 小 心 |
| 02 | Numbers  | 一 二 三 四 五 六 七 八 九 十 |
| 03 | Time     | 年 月 日 时 今 明 昨 早 晚 上 |
| 04 | Family   | 爸 妈 哥 姐 弟 妹 朋 友 老 师 |
| 05 | Nature   | 天 地 风 雨 雪 云 花 草 鸟 鱼 |

If the user proposes a different set, follow it — but flag any
characters that clash with the curated list (e.g. 月 appears in both
Pack 01 and Pack 03 above; pick one).

---

## 3. Workflow (short version)

1. **Define** — confirm pack number, theme, and the 10 characters with the user.
2. **Gather data** — fill the Character Data record (§4) for all 10.
3. **Draw SVGs** — one mnemonic scene + one oracle glyph per character (§5).
4. **Assemble** — start from a copy of `ZìTú Pack 01 — Elements.html`,
   replace data and SVG references per card (§6–§8).
5. **Verify** — run the overflow check (§10).
6. **Done** — `done` the file, `fork_verifier_agent` for a full sweep.

---

## 4. Character data schema

For each of the 10 characters, gather this record. Write it out in your
working notes before touching markup — it's much faster to do all 10
records first, then mechanically fill the markup.

```yaml
character:   人                      # one character, simplified only
pinyin:      rén                     # with tone marks
tone:        2                       # 1 | 2 | 3 | 4 | n  (neutral)
type:        pictograph              # pictograph | indicative | compound | phonosem
strokeCount: 2
radical:
  chinese:   人
  pinyin:    rén
hsk:         1                       # HSK level 1–6

english:
  primary:   person, people          # appears in 14.5pt display
  secondary: human                   # optional, after " · ", in italic 11pt

# ── front-card mnemonic scene ─────────────────────────────────────
mnemonic:
  svgId:     m-ren                   # symbol id; viewBox "0 0 60 70"
  caption:   person walking — two legs mid-stride.   # ≤ 12 words, end with .

# ── back-card etymology strip ─────────────────────────────────────
oracle:
  svgId:     o-ren                   # symbol id; viewBox "0 0 30 36"

# ── back-card blueprint zone ──────────────────────────────────────
blueprint:
  scope:     self                    # "self" for pictograph/indicative; "compound" for 会意/形声
  note:      |
    Two strokes — a pair of legs in mid-stride, a person seen in
    profile. Its compressed form 亻 stands on the left of
    person-related characters.
  formula:   "left leg 丿 + right leg ㇏ = 人"
                                     # short equation; wrap chars in <span class="han">
                                     # in markup. Use real stroke glyphs where possible.

# ── back-card stroke order ────────────────────────────────────────
strokeOrder:                         # up to 4 displayed; pad with "faded" steps if fewer
  - { glyph: 丿, name: 撇, py: piě }
  - { glyph: ㇏, name: 捺, py: nà }

# ── back-card word web ────────────────────────────────────────────
wordWeb:                             # exactly 4 compounds
  - { compound: 人口, focus: 0, pinyin: rénkǒu, english: population }
  - { compound: 人民, focus: 0, pinyin: rénmín, english: the people }
  - { compound: 工人, focus: 1, pinyin: gōngrén, english: worker }
  - { compound: 大人, focus: 1, pinyin: dàrén,   english: adult }
  # focus: 0 if the focal hanzi is the first character, 1 if it's the second

# ── back-card cultural note ───────────────────────────────────────
culture:
  lead:      Cultural note           # short uppercase tag; usually "Cultural note"
  text:      |
    In oracle-bone script, 人 depicted a person walking <strong>in profile</strong>
    — the defining mark of humanity in ancient pictographs. The
    front-facing form became 大.
                                     # use <strong>…</strong> sparingly for the punch line
```

### Notes on the data

- **Simplified only.** Never use traditional characters anywhere — not in
  examples, not in cultural notes, not in formulas. 漢 → 汉, 學 → 学,
  習 → 习, 龍 → 龙, 風 → 风, etc.
- **Pinyin tone marks.** Use proper diacritics: ā á ǎ à / ē é ě è /
  ī í ǐ ì / ō ó ǒ ò / ū ú ǔ ù / ǖ ǘ ǚ ǜ.
- **Strokes.** If `strokeCount` < 4, pad the stroke-order row with
  `<div class="step faded"><span class="han">·</span></div>` so the
  row always has 4 cells.
- **HSK level.** All Pack-01 characters are HSK 1; most foundational
  characters are.

---

## 5. SVG drawing guide

Add two symbols per character to `_system/zitu-symbols.html` **and**
inline them in the pack HTML file (the file needs its own copy for
self-contained `<use href="#…">` resolution).

### Mnemonic scene  `#m-<id>`

- **viewBox:** `0 0 60 70`
- **Style:** gold lines, `stroke="#a78a3d"`, `stroke-width="2"`,
  `stroke-linecap="round"`, `stroke-linejoin="round"`, `fill="none"`.
- **Accent:** 1–2 cinnabar `#b83a25` strokes or dots for emphasis.
- **Strokes:** 3–5 max. Aim for a scene where the lines *echo the
  character's own stroke shapes* — so the picture and the character
  reinforce each other in memory.
- **No fill** (line-art only), **no text**, no detail under 1mm.

Pack-01 mnemonic catalogue (use as style reference): `m-ren`, `m-shui`,
`m-huo`, `m-shan`, `m-mu`, `m-ri`, `m-yue`, `m-da`, `m-xiao`, `m-xin`.

### Oracle / bronze glyph  `#o-<id>`

- **viewBox:** `0 0 30 36`
- **Style:** `stroke="currentColor"` (inherits panel colour),
  `stroke-width="1.6"` to `1.8`, `stroke-linecap="round"`, `fill="none"`.
- **Goal:** a primitive pictograph closer to the character's *meaning*
  than to its modern *shape*. For numbers (一 二 三), this is literal
  horizontal lines. For 鱼 it's a fish silhouette. For abstract
  characters (爱), make the closest plausible oracle-era picture.

### Naming

Use pinyin (without tone marks). Disambiguate only when two characters
in the *same pack* share a syllable:

```
#m-shi      → 时
#m-shi2     → 是   (suffix the second occurrence)
```

### Where to register them

1. Edit `_system/zitu-symbols.html` to add the new `<symbol>` definitions
   (so the library grows over time).
2. Copy the same `<symbol>` definitions into the pack HTML file's
   inline `<svg width="0" height="0">…<defs>…</defs></svg>` block.

> The library file is documentation; pack files are self-contained and
> need their own copies for `<use href="#…">` to resolve.

---

## 6. Pack HTML scaffold

Start every new pack from a copy of Pack 01:

```bash
# in tool calls:
copy_files: src="ZìTú Pack 01 — Elements.html" → dest="ZìTú Pack NN — Theme.html"
```

Then edit in this order:

1. `<title>` and brand strip — pack number + theme.
2. The lede paragraph (rarely changes).
3. The **roster** in the cover (10 pips with han + pinyin + tone-coloured tn).
4. The instruction-step copy (rarely changes).
5. The SVG `<defs>` block — add 10 new `#m-*` and 10 new `#o-*` symbols.
6. The 12 cards across 6 sheets (see §7).
7. The 2 colophon tiles + 2 colophon backs (theme-specific copy).
8. The sample practice sheet (one character — the pack's lead).
9. The sample poster (same lead character).

### Required `<head>`

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>字图 ZìTú — Pack NN · Theme</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Long+Cang&family=Liu+Jian+Mao+Cao&family=ZCOOL+XiaoWei&family=Noto+Serif+SC:wght@400;700;900&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=DM+Sans:wght@300;400;500;700&family=Noto+Sans:wght@400;500&family=IBM+Plex+Mono:wght@300;400;500&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="_system/zitu.css" />
</head>
```

That's it — all styling is in `_system/zitu.css`.

---

## 7. Sheet layout & duplex mirror rule

The pack uses **6 print sheets** for the cards: 3 front-faces, 3 back-faces.

```
Sheet 1  Fronts  cards  [01][02]
                        [03][04]      ← printed face 1
Sheet 2  Backs   cards  [02][01]
                        [04][03]      ← printed face 2 (long-edge flip)

Sheet 3  Fronts  cards  [05][06]
                        [07][08]

Sheet 4  Backs   cards  [06][05]
                        [08][07]

Sheet 5  Fronts  cards  [09][10]
                        [colA][colB]  ← 2 chars + 2 colophon tiles

Sheet 6  Backs   cards  [10][09]
                        [colB-back][colA-back]
```

**Why mirror:** when paper is printed front+back and flipped on the
long edge, columns swap left↔right. Pre-mirroring the back-sheet markup
makes every back land directly behind its front when the page is held
up to the light.

**Rows do not swap** on long-edge flip — only columns. Keep the row
order the same on backs as on fronts.

---

## 8. Card markup templates

These are the minimum-required structures for each card type. Copy and
fill in. **All comments below are for you, the builder — strip them
from the actual file or keep them clearly bracketed.**

### 8.1 Front card

```html
<article class="card front" data-tone="2" data-type="pictograph">
  <div class="card-head">
    <span class="type-badge pictograph"><span class="han">象形</span>Pictograph</span>
    <span class="card-ref">Pack NN · <strong>01/10</strong></span>
  </div>
  <div class="hero">
    <div class="grid-box">
      <svg class="mizige"><use href="#mz"/></svg>
      <span class="han">人</span>
    </div>
    <div class="mnemonic">
      <div class="scene"><svg viewBox="0 0 60 70"><use href="#m-ren"/></svg></div>
      <div class="scene-label">Picture a…</div>
      <p class="caption">person walking — two legs mid-stride.</p>
    </div>
  </div>
  <div class="pinyin-bar">
    <span class="tone-dot t2">2</span>
    <span class="pinyin">r<span class="tm-2">é</span>n</span>
    <span class="seal-stamp">一</span>
  </div>
  <div class="meaning">person, people <em>· human</em></div>
</article>
```

**Swap points:**

| What | Where |
|---|---|
| Tone | `data-tone="2"` (1/2/3/4) + `.tone-dot.t2` + `.tm-2` on the toned vowel |
| Type | `data-type="pictograph"` + `.type-badge.pictograph` + `<span class="han">象形</span>Pictograph` |
| Card ref | `01/10`, `02/10`, … |
| Big hanzi | `<span class="han">人</span>` |
| Mnemonic | `<use href="#m-ren"/>` + caption text |
| Pinyin | `r<span class="tm-2">é</span>n` (wrap the toned vowel) |
| Seal | `一` (use simplified numerals 一 二 三 四 五 六 七 八 九 十) |
| Meaning | primary + `<em>· secondary</em>` |

### 8.2 Back card

```html
<article class="card back" data-tone="2" data-type="pictograph">
  <div class="card-head">
    <span class="card-ref" style="text-align:left">Pack NN · <strong>01/10</strong></span>
    <span class="han-mini">人</span>
  </div>

  <div class="bk-top">
    <aside class="etym">
      <div class="lbl">字形 · Evolution</div>
      <div class="stages">
        <div class="stg"><div class="gl"><svg viewBox="0 0 30 36" style="color:var(--paper-on-dk)"><use href="#o-ren"/></svg></div><div class="er">甲骨<em>oracle</em></div></div>
        <div class="stg"><div class="gl"><svg viewBox="0 0 30 36" style="color:var(--paper-on-dk)"><use href="#o-ren"/></svg></div><div class="er">金文<em>bronze</em></div></div>
        <div class="stg"><div class="gl seal">人</div><div class="er">篆书<em>seal</em></div></div>
        <div class="stg"><div class="gl clerc">人</div><div class="er">隶书<em>clerical</em></div></div>
        <div class="stg"><div class="gl modern">人</div><div class="er">楷书<em>regular</em></div></div>
      </div>
    </aside>
    <section class="bp">
      <div class="lbl">Blueprint <em>self-contained pictograph</em></div>
      <div class="body">
        <div class="glyph">人</div>
        <div class="ann">Two strokes — a pair of legs in mid-stride, a person seen in profile. Its compressed form <strong>亻</strong> stands on the left of person-related characters.</div>
      </div>
      <div class="formula">left leg <span class="han">丿</span> + right leg <span class="han">㇏</span> = <span class="han">人</span></div>
    </section>
  </div>

  <div class="stroke-row">
    <div class="lbl">Stroke order<em>2 strokes</em></div>
    <div class="strokes">
      <div class="step"><span class="n">1</span><span class="han">丿</span><span class="name">撇 <span class="py">piě</span></span></div>
      <div class="step"><span class="n">2</span><span class="han">㇏</span><span class="name">捺 <span class="py">nà</span></span></div>
      <div class="step faded"><span class="han">·</span></div>
      <div class="step faded"><span class="han">·</span></div>
    </div>
  </div>

  <div class="web">
    <div class="lbl">Word web<em>4 common compounds</em></div>
    <div class="items">
      <div class="w"><div class="ch"><span class="focus">人</span>口</div><div class="gloss">rénkǒu<span class="en">population</span></div></div>
      <div class="w"><div class="ch"><span class="focus">人</span>民</div><div class="gloss">rénmín<span class="en">the people</span></div></div>
      <div class="w"><div class="ch">工<span class="focus">人</span></div><div class="gloss">gōngrén<span class="en">worker</span></div></div>
      <div class="w"><div class="ch">大<span class="focus">人</span></div><div class="gloss">dàrén<span class="en">adult</span></div></div>
    </div>
  </div>

  <div class="culture">
    <span class="lead">Cultural note</span>
    In oracle-bone script, 人 depicted a person walking <strong>in profile</strong>
    — the defining mark of humanity in ancient pictographs.
  </div>

  <div class="stats">
    <div class="cell"><div class="k">Strokes</div><div class="v">2</div></div>
    <div class="cell"><div class="k">Radical</div><div class="v"><span class="han">人</span> rén</div></div>
    <div class="cell"><div class="k">HSK</div><div class="v">Level 1</div></div>
    <div class="cell"><div class="k">Type</div><div class="v">象形</div></div>
  </div>
</article>
```

**Tight space — these rules matter:**

- The back card budget is exactly **142 mm**. After your edits, run the
  verification step (§10) and trim if any back overflows.
- The cultural note's `<strong>` highlights are powerful — pick ONE
  punchline phrase per card, not several.
- The blueprint annotation text is **6.8pt body** with a tight 1.28
  line-height. Keep it to 2 short sentences (~25 words).

### 8.3 Colophon tiles (cards 11 & 12)

The two extra tiles on Sheet 5 (and their mirrored backs on Sheet 6)
are the **end-card** (closing message + 学 xué character) and the
**next-pack teaser** (listing the upcoming five series packs). Copy
from Pack 01's sheets 5–6 verbatim; only the next-pack teaser body
needs to be updated to mark the current pack `✓ done`.

### 8.4 Practice sheet (A4 portrait)

One per pack — use the **lead character** (typically character 01).
Copy from Pack 01's Sheet 7. Layout, in order:

```
Header (character + pinyin + meaning + tone label + seal)
── zones grid ──
│ A 涂一涂  colour outline   │ B 画一画  blank 米字格     │
│ C 找一找  find in grid     │ D 英文意思  write meaning │
│ E 描一描  trace 4 reps     │ F 写一写  write 4 reps  │
│ G 造句  sentence writing  (full-width)              │
──
Footer (name + date + pack ref)
```

Swap per pack:

- Character header (han + pinyin + tone color + meaning).
- Zone C find-grid: salt 24 cells with characters that *look like*
  the target (visual confusables) + several copies of the target.
- Zone E trace row: 4 reps of the target character.
- Zone F write row: 4 empty cells (`<div class="cell empty"></div>`).
- Zone G compound list: pull the 4 compounds from the character's
  word web.

**Do not** add `min-height` to zones or change E / F back to full-width
— the sheet is tuned to exactly fit 277 mm with this layout.

### 8.5 Poster (A3 landscape)

One per pack — same lead character. Copy from Pack 01's Sheet 8.
Swap: title hanzi + pinyin, mnemonic SVG, oracle SVG, blueprint
formula, word web entries, cultural text, stroke-order row, stats.

---

## 9. Reference tables

### 9.1 Tone classification

| Tone | Class | CSS var | Vowel diacritics | Feeling |
|---|---|---|---|---|
| 1 — flat   | `data-tone="1"` `.tone-dot.t1` `.tm-1` | `--tone-1` (slate)   | ā ē ī ō ū ǖ | level horizon |
| 2 — rising | `data-tone="2"` `.tone-dot.t2` `.tm-2` | `--tone-2` (moss)    | á é í ó ú ǘ | climbing |
| 3 — dipping| `data-tone="3"` `.tone-dot.t3` `.tm-3` | `--tone-3` (plum)    | ǎ ě ǐ ǒ ǔ ǚ | down-then-up |
| 4 — falling| `data-tone="4"` `.tone-dot.t4` `.tm-4` | `--tone-4` (cinnabar) | à è ì ò ù ǜ | sharp drop |
| neutral    | `data-tone` omit; use `.tone-dot.tn`   | `--tone-n` (grey)    | a e i o u   | whisper |

The toned vowel inside the pinyin gets wrapped in `<span class="tm-N">…</span>`
to colour just that one letter.

### 9.2 Character-type classification

| Type | Badge class | Han | When |
|---|---|---|---|
| 象形 Pictograph        | `.type-badge.pictograph` | 象形 | Direct pictures of the thing (人 山 木 月). |
| 指事 Indicative        | `.type-badge.indicative` | 指事 | Abstract concept shown by sign (大 小 上 下). |
| 会意 Compound (meaning)| `.type-badge.compound`   | 会意 | Two meanings combined (明 = 日 + 月). |
| 形声 Phono-semantic    | `.type-badge.phonosem`   | 形声 | Meaning + sound part (妈 = 女 + 马). Most modern characters. |

### 9.3 Stroke names (most common)

For the back card's stroke-order panel. Use the actual stroke glyph
where unicode allows, otherwise approximate.

| Glyph | Name (zh · pinyin) | English |
|---|---|---|
| 一 | 横 héng | horizontal |
| 丨 | 竖 shù | vertical |
| 丿 | 撇 piě | left-falling |
| ㇏ | 捺 nà | right-falling |
| 丶 | 点 diǎn | dot |
| 𠃌 | 横折 héngzhé | horizontal turn |
| 亅 | 竖钩 shùgōu | vertical hook |
| 乚 | 卧钩 wògōu | lying hook |
| 凵 | 竖折 shùzhé | vertical-bend |
| ㇇ | 横撇 héngpiě | horizontal-falling |
| 𠃌 | 横折钩 héngzhégōu | horizontal-turn-hook |

### 9.4 Seal-stamp numerals (front card, bottom-right)

Use **simplified arabic-Chinese numerals**, one per card:

```
一  二  三  四  五  六  七  八  九  十
1   2   3   4   5   6   7   8   9   10
```

Do NOT use the formal numerals 壹 贰 叁 肆 伍 陆 柒 捌 玖 拾 inside
seals on individual character cards. (The cover's instruction steps
*do* use formal numerals — 壹 贰 叁 肆 — by design, for visual rhythm.)

---

## 10. Verification

Before calling `done`, verify back cards fit:

```js
// run via eval_js in the live preview:
const backs = document.querySelectorAll('.card.back');
[...backs].map(c => c.scrollHeight - c.clientHeight);
// Expected: an array of all zeros. Any non-zero means that back card overflows.
```

If anything overflows:

1. First check **culture text length** — trim to 2 sentences max.
2. Then check **blueprint annotation** — should be ≤ 25 words.
3. Then check **word web English glosses** — keep each to ≤ 3 words.
4. Last resort: reduce `.bk-top { grid-template-columns: 23mm 1fr; }`
   to `21mm` to give the blueprint more room.

Also run:

```js
// confirm Kaiti is loaded for the big hanzi:
getComputedStyle(document.querySelector('.card.front .grid-box .han')).fontFamily;
// should start with "Ma Shan Zheng"
```

---

## 11. Final checklist

Before `done`:

- [ ] All 10 characters are simplified (no 漢, 學, 龍, 風, 龜, …).
- [ ] All pinyin uses proper tone diacritics (no numeric tones like `ren2`).
- [ ] Seal-stamp numerals are 一–十 (simplified arabic-Chinese), not 壹–拾.
- [ ] Back-card overflow check returns all zeros.
- [ ] All 10 mnemonic and 10 oracle symbols are defined in the file.
- [ ] Cover roster matches the actual 10 characters in the pack, in order.
- [ ] Sheet-mark labels match (sheet 1/3, 2/3, 3/3 of fronts and backs).
- [ ] Mirror order on back sheets: pairs 02·01 / 04·03 / 06·05 / 08·07 / 10·09 / colB·colA.
- [ ] Practice sheet's find-grid (zone C) contains the target character
      at least 5 times, plus visually-similar distractors.
- [ ] Poster's lead character matches Pack 01's pattern (lead = card 01).
- [ ] `<title>` and brand strip both name the pack correctly.
- [ ] New SVG symbols also added to `_system/zitu-symbols.html`.

Then:

```
done   path: "ZìTú Pack NN — Theme.html"
fork_verifier_agent
```
