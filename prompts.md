# ZìTú — Zone 1 & Zone 2 Redesign Specification
# Version 3.0 — Fully Automated, makemeahanzi-Sourced

---

## BACKGROUND AND RATIONALE

Both Zone 1 (front right panel) and Zone 2 (back stroke order
zone) were previously designed around data that AI cannot
reliably produce at render time: pictograph SVG overlays with
correct stroke annotation numbers, and accurate stroke names
and sequences. Both zones produced incorrect output because
they required precise technical recall, not reasoning.

This specification replaces both zones with a fully automated
design sourced from makemeahanzi — a verified, human-authored
dataset of SVG stroke path data for Chinese characters, used
in production by multiple professional Chinese learning
applications.

No AI reasoning is involved in either zone after this
redesign. All data is prepared once, stored as static assets,
and rendered mechanically by the build script.

---

## DATA SOURCE: MAKEMEAHANZI

Repository: https://github.com/skishore/makemeahanzi
Licence: CC BY 4.0 — permitted for commercial educational use
with attribution in product documentation.

Two files are used:

**graphics.txt**
One JSON object per line, one line per character. Each object
contains:
- strokes: array of SVG path strings, one per stroke, in
  correct stroke order
- medians: array of median polylines, one per stroke
  (used for stroke direction rendering if needed)

**dictionary.txt**
One JSON object per line, one line per character. Each object
contains:
- pinyin: romanisation with tone marks
- english: English definition array
- decomposition: component decomposition string
- etymology: object with type, hint, and component fields

The graphics.txt file is the primary source for Zone 1 and
Zone 2. The dictionary.txt file supplements characters.json
for fields that can be automated.

---

## PIPELINE ARCHITECTURE

The system separates into two distinct phases. These phases
are never mixed.

### Phase 1: Data Preparation (one-shot, runs before any pack is built)

A standalone script, run once per pack, that:
1. Reads the pack manifest to get the character list
2. Looks up each character in the local makemeahanzi files
3. Extracts and transforms the required data
4. Writes a fully resolved asset file for the pack
5. Reports any characters not found in makemeahanzi

This script is the only place where data is looked up,
transformed, or validated. It produces a single output file.

### Phase 2: Build (pure rendering, no lookups)

The existing build script reads the asset file produced by
Phase 1 and renders it into HTML. It makes no network calls,
no lookups, and no decisions about data. It only applies the
template.

### Principle: The build is a function of its inputs

Given the same asset file, the build script must always
produce the same output. There is no randomness, no AI call,
no network dependency in the build phase.

---

## PHASE 1 SPECIFICATION: PREPARATION SCRIPT

### Script name and invocation

    python prepare_pack.py --pack 01

Running this command for an already-prepared pack overwrites
the existing asset file. It does not affect the built HTML.

### Inputs

- packs/pack-01/ directory with the pack manifest
  (character list already defined)
- data/makemeahanzi/graphics.txt (local copy, downloaded once)
- data/makemeahanzi/dictionary.txt (local copy, downloaded once)
- packs/pack-01/data/characters-manual.json (manual fields,
  see below)

### Outputs

A single file: packs/pack-01/data/characters-prepared.json

This file is the complete, resolved data for the pack. The
build script reads only this file. Nothing else.

### Downloading makemeahanzi

The first time prepare_pack.py is run, it checks whether
data/makemeahanzi/ exists. If not, it downloads graphics.txt
and dictionary.txt from the makemeahanzi GitHub repository
and saves them locally. All subsequent runs use the local
copy. The download step never runs again unless the directory
is deleted.

### What the script extracts per character

From graphics.txt for each character:
- All stroke SVG path strings, in order, as an array
- Total stroke count (length of strokes array)
- The full character outline path (union of all strokes,
  computed by combining all stroke paths)

From dictionary.txt for each character:
- Stroke names in Chinese with romanisation
  (derived from the decomposition and etymology fields)
- Character type: pictograph / ideograph / compound /
  phono-semantic (derived from etymology.type)
- Component decomposition (from decomposition field)

### Stroke names

makemeahanzi does not provide stroke names directly. Stroke
names must be derived from a separate stroke name lookup
table bundled with the project.

The lookup table maps each SVG path's general shape
(determined by the path's control points) to the standard
stroke name. This table is a static JSON file authored
once and stored at data/stroke-names.json.

The table covers the eight fundamental stroke types and their
common variants:
- 横 héng and variants (横折, 横折钩, 横撇, 横折弯钩, etc.)
- 竖 shù and variants (竖钩, 竖折, 竖弯钩, etc.)
- 撇 piě and variants (短撇, 平撇, etc.)
- 捺 nà and variants (反捺, etc.)
- 点 diǎn and variants
- 折 zhé compound strokes
- 钩 gōu variants
- 弯 wān variants

Path-to-name matching uses the starting direction, ending
direction, and presence of turns or hooks in the path. This
is a deterministic geometric computation, not AI inference.

If a stroke path cannot be matched to a known name, the
script records the stroke with name "UNMATCHED" and logs
a warning. This is handled gracefully in the build — the
unmatched stroke renders visually correct but shows no name.

### Manual fields file

Some fields cannot be automated and require human authorship.
These are kept in a separate file so the preparation script
never overwrites them.

File: packs/pack-01/data/characters-manual.json

Fields per character in this file:
- cultural_note: one to two sentences of cultural or
  historical context (string, required)
- compounds: array of 3–4 compound words using this
  character, each with zh, pinyin, en fields (required)

The preparation script merges the manual file with the
automated data into the final characters-prepared.json.

If a character is missing from the manual file, its fields
in characters-prepared.json are set to null and the build
renders visible placeholders.

### characters-prepared.json structure per character

```
{
  "character": "人",
  "pinyin": "rén",
  "tone": 2,
  "character_type": "pictograph",
  "english_primary": "person",
  "english_secondary": ["people", "human"],
  "hsk_level": 1,
  "strokes": [
    {
      "order": 1,
      "path": "M 473 623 Q 450 588...",
      "name_zh": "撇",
      "name_py": "piě",
      "name_en": "left-falling"
    },
    {
      "order": 2,
      "path": "M 495 611 Q 540 548...",
      "name_zh": "捺",
      "name_py": "nà",
      "name_en": "right-falling"
    }
  ],
  "stroke_count": 2,
  "outline_path": "M 473 623 Q...",
  "radical": "人",
  "compounds": [...],
  "cultural_note": "..."
}
```

---

## ZONE 1 REDESIGN: STROKE CONSTRUCTION SEQUENCE

### What this zone communicates

How the character is built, stroke by stroke, from empty
space to complete character. The learner sees the writing
process frozen into a sequence of frames.

### Layout

A horizontal sequence of frames displayed side by side within
the Zone 1 panel. Each frame is a small square containing an
SVG rendering of the character at a particular stage of
construction.

### Frame count rules

- Characters with 1–4 strokes: show every stroke as a
  separate frame. Frame count equals stroke count.
- Characters with 5–8 strokes: show every stroke as a
  separate frame. Frame count equals stroke count.
- Characters with 9–12 strokes: show every second stroke.
  Frame count is stroke count divided by 2, rounded up.
- Characters with 13+ strokes: show every third stroke.
  Frame count is stroke count divided by 3, rounded up.
- Always include a final complete frame regardless of the
  sampling rule. The final frame always shows all strokes.
- Maximum frames displayed: 6. If the computed frame count
  exceeds 6, reduce the sampling interval until it fits.

For Pack 01, all 10 characters have 2–4 strokes and will
show every stroke as a frame.

### Frame rendering rules

Each frame is a fixed-size SVG that renders the character
using the stroke path data from characters-prepared.json.

Within a frame at construction stage N:
- Strokes 1 through N–1 (completed strokes): rendered in
  the card's primary text colour at full opacity.
- Stroke N (the stroke being added in this frame):
  rendered in the card's accent colour (gold/equivalent)
  at full opacity. This is the visually prominent stroke.
- Strokes N+1 through end (future strokes): rendered in
  a single combined ghost path using the outline_path
  field, in the primary text colour at 12% opacity.
  This shows the learner where the character is going.
- The final complete frame: all strokes rendered in the
  primary text colour at full opacity. No accent, no ghost.
  This frame always appears last.

Each frame has a small label beneath it showing the stroke
number being introduced (e.g. "3" or "3–4" if strokes are
sampled). The final frame has no number label — it shows
only the completed character.

### Frame sizing and spacing

All frames are equal in size. The panel fits as many frames
as the character requires within the available width. If
frames would overflow, reduce frame size proportionally.
Frames are separated by a consistent small gap with no
divider lines between them.

### What is never shown in this zone

- Stroke names. Stroke names appear only in Zone 2.
- Written instructions or captions.
- Annotations, callout circles, or numbered overlays on
  the strokes themselves.

The zone is silent — only visual. The information is
the sequence.

### Fallback

If a character's stroke data is missing from
characters-prepared.json (empty strokes array), the zone
renders a single box containing the complete character
in the primary display font with a visible placeholder
label: "STROKE DATA MISSING".

---

## ZONE 2 REDESIGN: STROKE ORDER REFERENCE

### What this zone communicates

The complete stroke order for the character, with each stroke
named using the standard Chinese stroke terminology. This is
a reference panel — complete and accurate.

### Layout

A two-part layout within Zone 2:

**Part A — Sequential character builds** (top section)

A miniature version of the Zone 1 construction sequence,
showing the same frames at a smaller size. This provides
visual continuity between Zone 1 (front card) and Zone 2
(back card).

Maximum 4 frames shown in this part regardless of stroke
count. If the character has more than 4 strokes, show
frames at stages 1, the midpoint, the second-to-last, and
the final complete character.

**Part B — Stroke name list** (below Part A)

A numbered list of every stroke in order. Each row:
- Stroke number (1, 2, 3…)
- The stroke rendered in isolation as a small SVG using
  that stroke's individual path from the strokes array
- The stroke name in Chinese characters
- The stroke name in pinyin with tone mark
- The stroke name translated to English

The stroke name is sourced from the name_zh, name_py, and
name_en fields in the character's strokes array, which were
populated by the preparation script from the stroke name
lookup table.

### Stroke name accuracy guarantee

Because stroke names are derived from a static lookup table
applied to verified geometric path data, and not generated
by AI at render time, the names are deterministic and
consistent. The same stroke shape always produces the same
name. If a name is unmatched, it renders as "—" in all
three name fields and a warning is visible.

### What replaces the old Zone 2

The old Zone 2 was the dark evolution strip showing oracle
bone, bronze, and seal script forms as images. This strip
is removed in its entirety.

The script styles panel (书体变奏, introduced in the earlier
redesign) remains. Its position is unchanged.

The new stroke order reference occupies a different vertical
position on the back card — below the script styles panel
and above the word web. The layout of all other back card
zones shifts accordingly but their content is unchanged.

---

## CHARACTERS.JSON CHANGES

The following fields are removed from characters.json because
they are now produced automatically by the preparation script:

- svg_overlay (removed — Zone 1 no longer uses this)
- svg_caption (removed — Zone 1 no longer shows captions)
- character_type (moved to characters-prepared.json,
  sourced from makemeahanzi etymology data)
- components (moved to characters-prepared.json,
  sourced from makemeahanzi decomposition data)
- strokes (entirely new, sourced from makemeahanzi)

The following fields remain in characters.json as the source
of truth for manually authored content:
- character
- pinyin (verified against makemeahanzi, manual wins on conflict)
- hsk_level
- hsk_order
- pack
- pack_position

The following fields move to characters-manual.json:
- cultural_note
- compounds

characters.json becomes a lightweight pack membership and
ordering file. All enriched data lives in characters-prepared.json.

---

## BUILD SCRIPT CHANGES

The build script (build_cards.py) is updated to:
- Read from characters-prepared.json instead of characters.json
- Render Zone 1 using the strokes array and the frame
  construction rules defined above
- Render Zone 2 Part A and Part B using the strokes array
- No longer render any svg_overlay, svg_caption, or
  etymology strip content

The build script must not contain any data transformation
logic. If data is missing or malformed in the input file,
the build renders a placeholder. It does not attempt to
compute, infer, or fetch missing data.

---

## CONSTRAINTS AND RULES

**Separation of concerns**
The preparation script transforms data. The build script
renders data. These responsibilities must not cross.
A developer reading build_cards.py should see no data
logic. A developer reading prepare_pack.py should see
no rendering logic.

**Determinism**
Given the same characters-prepared.json, the build must
always produce identical output. No randomness, no
environment-dependent behaviour, no AI calls.

**Graceful degradation**
Every field that could be missing has a defined fallback
that renders something visible. The build never crashes on
missing data.

**Stroke path coordinate system**
makemeahanzi paths use a 1000×1000 coordinate system.
All SVG frames in Zone 1 and Zone 2 must use the same
viewBox so that strokes from different characters align
consistently when rendered. The viewBox is 0 0 1024 1024.
Do not normalise or transform the coordinates.

**Ghost outline path**
The outline_path field used for ghost rendering of future
strokes is computed by the preparation script as the SVG
path string union of all strokes. If the preparation script
cannot compute this (library unavailable), it may store the
array of all stroke paths instead and the build renders
each future stroke individually at 12% opacity. The visual
result is identical.

**Attribution**
A plain-text attribution to makemeahanzi must appear in
the product's teacher instructions PDF:
"Stroke data sourced from makemeahanzi by Shaunak Kishore,
licensed CC BY 4.0. https://github.com/skishore/makemeahanzi"
This is a licence obligation, not optional.

---

## ACCEPTANCE CRITERIA

**Preparation script**
- Running prepare_pack.py --pack 01 produces
  characters-prepared.json with all 10 Pack 01 characters
- Each character entry contains a non-empty strokes array
  with the correct stroke count (人=2, 水=5, 火=4, 山=3,
  木=4, 日=4, 月=4, 大=3, 小=3, 心=4)
- Each stroke has a name_zh value that is not "UNMATCHED"
  for all Pack 01 characters
- Running the script a second time produces identical output

**Zone 1**
- Front card for 人 shows exactly 2 frames
- Front card for 水 shows exactly 5 frames
- In each frame, the most recently added stroke is visually
  distinct from completed and future strokes
- Future strokes are visible as a ghost at low opacity
- The final frame shows the complete character with no
  accent stroke
- No stroke names, labels, or captions appear in Zone 1

**Zone 2**
- Back card shows Part A (miniature sequence, max 4 frames)
  and Part B (stroke name list)
- Part B for 人 shows exactly 2 rows: 撇 piě and 捺 nà
- Part B for 月 shows exactly 4 rows with correct names
- No stroke name row contains "UNMATCHED" for any Pack 01
  character
- The old evolution strip (dark left panel) is absent

**Build integrity**
- Removing any field from characters-prepared.json causes
  a visible placeholder to appear, not a crash or blank space
- Running the build twice with the same input produces
  identical HTML output
- Print preview shows both zones without layout breakage