# 字图 ZìTú — Design System

A printable Chinese-character learning system. Each pack covers 10
simplified characters with a flashcard pair (front + back),
a practice sheet, and a classroom poster — all built on one consistent
visual language.

## What's in this folder

| File | Purpose |
|---|---|
| `HOW-TO-BUILD-A-PACK.md` | The build manual. Read this first when starting a new pack. |
| `zitu.css` | The canonical stylesheet. Every pack HTML file links to this. |
| `zitu-symbols.html` | SVG `<symbol>` library — the 米字格 grid + per-character mnemonic and oracle-bone glyphs. Reference only; pack files inline their own copies. |
| `README.md` | This file. |

## Adding a new pack

1. Confirm the pack's number, theme, and 10 characters with the user.
2. Open `HOW-TO-BUILD-A-PACK.md` and follow it end-to-end.
3. Use `ZìTú Pack 01 — Elements.html` (at the project root) as the
   reference implementation — copy-and-edit is the fastest path.

## Versioning

The system is v1.0. If you make breaking changes to `zitu.css` or
to a card's required markup, bump to v1.1 in the file header and note
the change here so older packs can be reviewed for compatibility.

## What you can change safely

- **CSS tokens** at the top of `zitu.css` (`--paper`, `--tone-*`,
  font stacks). These cascade to every existing pack on next load.
- **SVG library** in `zitu-symbols.html` — purely additive.

## What requires a version bump

- Class names (`.card`, `.bk-top`, `.tone-dot.t2`, etc.) — every pack
  references these in markup.
- Card geometry (the `--card-w` / `--card-h` variables) — changes
  break duplex alignment.
- The duplex-mirror rule (see HOW-TO §7) — changes break printing.
