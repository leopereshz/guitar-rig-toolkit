"""Extract Guitar Rig's own component catalog from its database, across installed versions.

`Database/User.kad` is a plain XML taxonomy that Guitar Rig ships and maintains. From
Guitar Rig 6 onward it lists every component the installation knows about, grouped by
category — independently of any preset. That makes it the authoritative catalog: a preset
scan only ever reveals the components that happen to be used.

Version note, measured rather than assumed: Guitar Rig 5's `User.kad` contains only the
preset tag taxonomy (`RP://` sets) and has **no** component catalog (`CP://` sets are
present but empty). So a GR5-only install yields no catalog, and the dictionary has to be
built from a preset scan alone. Guitar Rig 6 introduced the `CP://` catalog; later
versions are read the same way and picked up automatically.

    python catalog.py                  # scan every installed version, write catalog.json
    python catalog.py --path <file>    # use one specific User.kad
    python catalog.py --print          # dump JSON to stdout as well

Output shape:

    {
      "versions": {"6": {"categories": {...}, "count": 122}},
      "categories": {"Amplifiers": ["Gratifier", ...], ...},   # union, newest wins
      "components": {"Gratifier": "Amplifiers", ...},
      "since": {"Raum": "6", ...}                              # lowest version providing it
    }
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import database_dirs, find_kad, version_of

HERE = os.path.dirname(os.path.abspath(__file__))

# Categories that are not user-facing signal processors.
INTERNAL = {"Hidden", "Tools"}


def parse_kad(path: str) -> dict:
    """Component categories from one User.kad. Empty dict when the file has no catalog."""
    text = open(path, encoding="utf-8", errors="replace").read()

    categories: dict[str, list[str]] = {}
    for name, body in re.findall(r'<set name="CP://([^"]+)">(.*?)</set>', text, re.S):
        name = html.unescape(name)
        # Sub-sets are named "Category<TAB>Component" and only repeat pack tags;
        # the flat top-level sets are the catalog itself.
        if "\t" in name or name.startswith("__"):
            continue
        items = [html.unescape(m) for m in re.findall(r'<attribute name="CP://([^"]+)"', body)]
        if items and items != ["Factory"]:
            categories[name] = items

    return {"categories": categories,
            "components": {c: cat for cat, items in categories.items() for c in items}}


def collect(explicit: str | None = None) -> tuple[dict, list[str]]:
    """Parse User.kad for every installed Guitar Rig version. Returns (data, notes)."""
    if explicit:
        sources = [(version_of(explicit) or 0.0, explicit)]
    else:
        sources = []
        for d in database_dirs():
            kad = os.path.join(d, "User.kad")
            if os.path.isfile(kad):
                sources.append((version_of(d), kad))

    versions: dict[str, dict] = {}
    notes: list[str] = []
    for ver, kad in sorted(sources):
        parsed = parse_kad(kad)
        label = f"{ver:g}" if ver else "?"
        if not parsed["components"]:
            notes.append(f"Guitar Rig {label}: User.kad sem catalogo de componentes "
                         f"(sem sets CP://) / no component catalog in this version")
            continue
        versions[label] = {"categories": parsed["categories"],
                           "components": parsed["components"],
                           "count": len(parsed["components"]),
                           "path": kad}

    # union across versions, newest definition wins; `since` keeps the lowest version
    categories: dict[str, list[str]] = {}
    components: dict[str, str] = {}
    since: dict[str, str] = {}
    for label in sorted(versions, key=lambda s: float(s) if s != "?" else 0.0):
        v = versions[label]
        for cat, items in v["categories"].items():
            merged = categories.setdefault(cat, [])
            merged.extend(i for i in items if i not in merged)
        for comp, cat in v["components"].items():
            components[comp] = cat
            since.setdefault(comp, label)

    return {"versions": {k: {kk: vv for kk, vv in v.items() if kk != "components"}
                         for k, v in versions.items()},
            "categories": categories, "components": components, "since": since}, notes


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", help="explicit User.kad location")
    ap.add_argument("--print", dest="to_stdout", action="store_true")
    args = ap.parse_args()

    if args.path and not os.path.isfile(args.path):
        print(f"nao encontrado / not found: {args.path}", file=sys.stderr)
        sys.exit(1)
    if not args.path and find_kad() is None:
        print("Nenhum User.kad encontrado. Rode 'python paths.py' para ver o que foi "
              "detectado, ou passe --path.\nNo User.kad found.", file=sys.stderr)
        sys.exit(1)

    data, notes = collect(args.path)

    for n in notes:
        print(f"nota / note: {n}")
    if not data["components"]:
        print("\nNenhuma versao instalada expoe catalogo de componentes (precisa GR6+).\n"
              "No installed version exposes a component catalog (needs GR6+).", file=sys.stderr)
        sys.exit(2)

    print("\nversoes com catalogo / versions with a catalog:")
    for label, v in sorted(data["versions"].items()):
        print(f"  Guitar Rig {label}: {v['count']} componentes  ({v['path']})")

    cats = data["categories"]
    usable = {k: v for k, v in cats.items() if k not in INTERNAL}
    print(f"\nuniao / union : {len(data['components'])} componentes, {len(cats)} categorias"
          f"  ({sum(len(v) for v in usable.values())} fora de {sorted(INTERNAL)})")
    print()
    for cat, items in sorted(cats.items(), key=lambda kv: -len(kv[1])):
        print(f"  {cat:<16} {len(items):>3}  {', '.join(items)}")

    if args.to_stdout:
        print()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        out = os.path.join(HERE, "catalog.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        print(f"\nescrito / written: {out}")


if __name__ == "__main__":
    main()
