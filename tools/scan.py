"""Build the component/parameter dictionary by scanning .ngrr presets.

Preset folders are discovered automatically (see paths.py); pass --path to add more.
By default the existing components.json is extended rather than replaced, so the
dictionary grows as different people scan the presets they happen to own.

    python scan.py                        # discover, merge into components.json
    python scan.py --path D:\\Presets      # add another folder
    python scan.py --replace              # discard the existing dictionary first
    python scan.py --coverage             # only report catalog coverage, write nothing

Outputs, next to this script:
    components.json  component id -> parameters -> ranges and observed values
    COMPONENTS.md    the same dictionary as a readable reference
    schema.txt       distinct XML element paths seen in the rack documents
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngrr import NgrrFile
from paths import find_presets, preset_roots

HERE = os.path.dirname(os.path.abspath(__file__))
DICT_PATH = os.path.join(HERE, "components.json")
CATALOG_PATH = os.path.join(HERE, "catalog.json")


def read_rack_xml(path: str) -> tuple[str | None, str]:
    """Return (rack xml, container flavour), handling both preset containers."""
    blob = open(path, "rb").read()
    if blob[:4] == b"-in-":
        return NgrrFile.parse(blob).rack_xml, "sndf"
    end = blob.find(b"</gr-instrument-chunk>")
    if end == -1:
        return None, "unknown"
    end += len(b"</gr-instrument-chunk>")
    start = blob.rfind(b"<?xml", 0, end)
    if start == -1:
        return None, "unknown"
    return blob[start:end].decode("utf-8"), "nish"


def walk(elem, path, paths):
    paths.add(path)
    for child in elem:
        walk(child, f"{path}/{child.tag}", paths)


def blank_param(pid: str, pname: str | None) -> dict:
    return {"id": pid, "name": pname, "min": None, "max": None, "kind": None,
            "observed_min": None, "observed_max": None, "examples": [], "count": 0}


def scan(files: list[str], comps: dict, paths: set) -> tuple[Counter, list]:
    flavours, skipped = Counter(), []

    for path in files:
        name = os.path.basename(path)
        try:
            xml, flavour = read_rack_xml(path)
            if xml is None:
                skipped.append((name, "sem rack xml / no rack xml"))
                continue
            root = ET.fromstring(xml)
        except Exception as exc:  # noqa: BLE001
            skipped.append((name, str(exc)))
            continue
        flavours[flavour] += 1
        walk(root, root.tag, paths)

        # A component is "chain" when it sits under <non-fix-components>, not when its id is
        # absent from the fixed slots: Loop Machine (53000) exists as both.
        nf = root.find("gr-rack/non-fix-components")
        chain = set() if nf is None else {id(c) for c in nf.iter("component")}

        for comp in root.iter("component"):
            cid, cname = comp.get("id"), comp.get("name")
            if cid is None or cname is None:
                continue
            in_chain = id(comp) in chain
            entry = comps.setdefault(cid, {"id": cid, "name": cname, "fixed": not in_chain,
                                           "presets": 0, "aliases": [], "parameters": {}})
            entry["presets"] += 1
            if cname not in entry["aliases"]:
                entry["aliases"].append(cname)
            if in_chain:
                entry["fixed"] = False

            for param in comp.iter("parameter"):
                pid, pname, value = param.get("id"), param.get("name"), param.get("value")
                if pid is None:
                    continue
                p = entry["parameters"].setdefault(pid, blank_param(pid, pname))
                if p.get("name") is None:
                    p["name"] = pname
                base = param.find("base-parameters")
                if base is not None:
                    if base.get("remote-min") is not None:
                        p["min"] = base.get("remote-min")
                    if base.get("remote-max") is not None:
                        p["max"] = base.get("remote-max")
                if value is None:
                    continue
                p["count"] += 1
                try:
                    fv = float(value)
                    p["kind"] = "float" if "." in value else "int"
                    lo, hi = p["observed_min"], p["observed_max"]
                    p["observed_min"] = fv if lo is None else min(lo, fv)
                    p["observed_max"] = fv if hi is None else max(hi, fv)
                except ValueError:
                    p["kind"] = "text"
                if len(p["examples"]) < 6 and value not in p["examples"]:
                    p["examples"].append(value)

    return flavours, skipped


def coverage(comps: dict) -> tuple[list, list, dict]:
    """Compare the scanned dictionary against Guitar Rig's own catalog."""
    if not os.path.exists(CATALOG_PATH):
        return [], [], {}
    cat = json.load(open(CATALOG_PATH, encoding="utf-8"))
    # a component can be renamed between Guitar Rig versions (Master FX -> Global FX),
    # so match on every name the scan has ever seen for it
    known = {n for c in comps.values() for n in {c["name"], *c.get("aliases", [])}}
    catalog_names = set(cat["components"])
    missing = sorted(catalog_names - known)
    extra = sorted(known - catalog_names)
    return missing, extra, cat


def write_markdown(ordered: dict, flavours: Counter, n_files: int, cat: dict) -> None:
    md = [
        "# Guitar Rig component dictionary", "",
        f"Extracted from {n_files} `.ngrr` presets "
        f"({flavours.get('sndf', 0)} SoundShell/zlib, {flavours.get('nish', 0)} GR6 native).", "",
        "`min`/`max` come from each parameter's `<base-parameters remote-min/remote-max>`.",
        "`observed` is the range actually used across the scanned presets — a practical hint",
        "for musically sane values. Most continuous controls are normalised floats in `0.0 - 1.0`.", "",
        "Category comes from Guitar Rig's own catalog (`catalog.json`), not from the presets.", "",
    ]
    comp_cat = cat.get("components", {})
    for section, fixed in (("Chain components", False), ("Fixed rack slots", True)):
        md += [f"## {section}", ""]
        for cid, c in ordered.items():
            if c["fixed"] != fixed:
                continue
            tag = comp_cat.get(c["name"])
            md += [f"### {c['name']}  `id={cid}`" + (f"  — *{tag}*" if tag else ""), "",
                   f"Seen in {c['presets']} preset(s). {len(c['parameters'])} parameter(s).", "",
                   "| param id | name | min | max | observed | examples |", "|---|---|---|---|---|---|"]
            for pid, p in c["parameters"].items():
                obs = (f"{p['observed_min']:g} – {p['observed_max']:g}"
                       if p["observed_min"] is not None else "—")
                ex = ", ".join(f"`{e}`" for e in p["examples"][:4]) or "—"
                md += [f"| `{pid}` | {p['name'] or '—'} | {p['min'] or '—'} | {p['max'] or '—'} "
                       f"| {obs} | {ex} |"]
            md += [""]
    with open(os.path.join(HERE, "COMPONENTS.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", action="append", default=[], help="extra preset folder")
    ap.add_argument("--replace", action="store_true", help="discard the existing dictionary")
    ap.add_argument("--coverage", action="store_true", help="report coverage only, write nothing")
    args = ap.parse_args()

    comps: dict = {}
    if not args.replace and os.path.exists(DICT_PATH):
        comps = json.load(open(DICT_PATH, encoding="utf-8")).get("components", {})
        # counts are recomputed from this scan, not carried over
        for c in comps.values():
            c["presets"] = 0

    if args.coverage:
        missing, extra, cat = coverage(comps)
        print(f"catalogo / catalog : {len(cat.get('components', {}))} componentes")
        print(f"com parametros     : {len(comps)}")
        print(f"faltando / missing : {len(missing)}")
        for m in missing:
            print(f"   {cat['components'][m]:<14} {m}")
        if extra:
            print(f"\nfora do catalogo (internos): {', '.join(extra)}")
        return

    roots = preset_roots(args.path)
    files = find_presets(roots)
    if not files:
        print("Nenhum preset encontrado. Rode 'python paths.py' ou passe --path.\n"
              "No presets found. Run 'python paths.py' or pass --path.", file=sys.stderr)
        sys.exit(1)

    paths: set = set()
    before = len(comps)
    flavours, skipped = scan(files, comps, paths)

    comps = {cid: c for cid, c in comps.items() if c["presets"] > 0 or not args.replace}
    ordered = dict(sorted(comps.items(), key=lambda kv: (kv[1]["fixed"], -kv[1]["presets"])))

    with open(DICT_PATH, "w", encoding="utf-8") as fh:
        json.dump({"generated_from": {"roots": roots, "preset_count": len(files)},
                   "containers": dict(flavours), "components": ordered}, fh,
                  indent=2, ensure_ascii=False)
    with open(os.path.join(HERE, "schema.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(sorted(paths)))

    missing, _extra, cat = coverage(ordered)
    write_markdown(ordered, flavours, len(files), cat)

    chain = [c for c in ordered.values() if not c["fixed"]]
    print("raizes / roots:")
    for r in roots:
        print(f"  {r}")
    print(f"\npresets       : {len(files)}  ({dict(flavours)})")
    print(f"componentes   : {len(ordered)}  ({len(chain)} de cadeia, {len(ordered) - len(chain)} fixos)")
    print(f"  novos nesta execucao / new this run: {len(ordered) - before}")
    print(f"parametros    : {sum(len(c['parameters']) for c in ordered.values())}")
    if cat:
        total = len(cat["components"])
        print(f"cobertura do catalogo: {total - len(missing)}/{total} "
              f"({100 * (total - len(missing)) // total}%) — faltam {len(missing)}")
    if skipped:
        print(f"ignorados     : {len(skipped)}")
        for n, why in skipped[:5]:
            print(f"  ! {n} - {why}")


if __name__ == "__main__":
    main()
