#!/usr/bin/env python3
"""
generate_pack.py — main entry point for the ZìTú pack generation pipeline.

Examples:
    python generate_pack.py --pack 02               # assign → fetch → build
    python generate_pack.py --pack 02 --skip-fetch  # assign → build only
    python generate_pack.py --list                  # show all packs
    python generate_pack.py --assign-only           # update manifest, then stop
    python generate_pack.py --pack 02 --force-fetch # re-download existing images
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

import assign_packs
import build_cards
import fetch_resources

DATA = ROOT / "data"


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def cmd_list():
    manifest = load_json(DATA / "pack_manifest.json")
    print(f"\n{'Pack':<10} {'Title':<20} {'Characters'}")
    print("─" * 60)
    for key, data in manifest.items():
        chars = "".join(data["characters"])
        title = data.get("title", "")
        print(f"  {key:<10} {title:<20} {chars}")
    print()


def cmd_assign_only():
    print("\n=== Assign packs ===")
    assign_packs.assign(dry_run=False)


def cmd_generate(pack_num: str, skip_fetch: bool = False, force_fetch: bool = False):
    manifest = load_json(DATA / "pack_manifest.json")
    pack_key = f"pack-{int(pack_num):02d}"

    # 1. Assign if pack not yet in manifest
    if pack_key not in manifest:
        print(f"\n=== Assigning packs ('{pack_key}' not yet in manifest) ===")
        assign_packs.assign(dry_run=False)
        manifest = load_json(DATA / "pack_manifest.json")
        if pack_key not in manifest:
            print(f"ERROR: {pack_key} still not in manifest after assignment.")
            print("  The pack may be beyond the available HSK 1 characters.")
            sys.exit(1)
    else:
        print(f"\n=== Pack {pack_key} already in manifest — skipping assignment ===")

    # 2. Fetch images
    if skip_fetch:
        print("\n=== Skipping image fetch (--skip-fetch) ===")
    else:
        print(f"\n=== Fetching glyph images for {pack_key} ===")
        fetch_resources.fetch_pack(pack_num, force=force_fetch)

    # 3. Build HTML
    print(f"\n=== Building HTML for {pack_key} ===")
    out_path = build_cards.build_pack(pack_num)
    print(f"\n✓ Done → {out_path.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser(
        description="ZìTú pack generation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--pack", metavar="N", help="Pack number to generate (e.g. 02)")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip image download")
    parser.add_argument("--force-fetch", action="store_true", help="Re-download existing images")
    parser.add_argument("--list", action="store_true", help="List all packs and exit")
    parser.add_argument("--assign-only", action="store_true", help="Run assignment only and exit")

    args = parser.parse_args()

    if args.list:
        cmd_list()
        return

    if args.assign_only:
        cmd_assign_only()
        return

    if not args.pack:
        parser.print_help()
        sys.exit(1)

    cmd_generate(
        pack_num=args.pack,
        skip_fetch=args.skip_fetch,
        force_fetch=args.force_fetch,
    )


if __name__ == "__main__":
    main()
