"""Build a Guitar Rig rack from scratch by composing harvested component blocks.

Guitar Rig's rack chain lives in a flat `<non-fix-components>` list, and each
`<component>` element is self-contained: its GUI view state, its parameters and their
ranges all sit inside it. So a rack can be composed by picking component blocks and
concatenating them — no need to synthesise a component's internals from a spec.

Two things stop this from being pure copy-paste:

1. `uuid` is per **instance**, not per component type (measured: 87 of 101 component types
   carry a different uuid in every preset they appear in). Every placed component gets a
   freshly generated one.
2. `realtimecontroldb/host-automationdb` holds `<automatable-parameter uuid=...>` entries
   pointing back at components. Stale entries would reference components that no longer
   exist, so the table is rebuilt for the new chain.

Component blocks are harvested from the presets already on this machine — nothing is
shipped or redistributed. A component can only be placed if some local preset uses it.

    python rackbuild.py --list
    python rackbuild.py --into "<preset.ngrr>" --chain "Skreamer,Lead 800,Matched Cabinet"

`--into` writes over an existing preset **in place**, because Guitar Rig only lists presets
its database has indexed — a brand-new file will not appear in the browser. Always keep a
backup; `--backup` makes one next to the file.
"""

from __future__ import annotations

import argparse
import base64
import copy
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngrr import NgrrFile
from paths import find_presets, preset_roots
from scan import read_rack_xml

HERE = os.path.dirname(os.path.abspath(__file__))


def new_uuid() -> str:
    """A fresh instance uuid in Guitar Rig's format: base64 of 16 random bytes."""
    return base64.b64encode(os.urandom(16)).decode("ascii")


def harvest(files: list[str]) -> dict[str, list[ET.Element]]:
    """First chain block found for each component name, across the presets.

    A block is a `<component>` plus any following siblings that are not themselves
    components. Guitar Rig parks per-component sidecar state next to the component rather
    than inside it — Loop Machine is followed by a `<loopstation>` element — and dropping
    those siblings would silently place a half-configured component.
    """
    library: dict[str, list[ET.Element]] = {}
    for path in files:
        try:
            xml, _ = read_rack_xml(path)
            if xml is None:
                continue
            root = ET.fromstring(xml)
        except Exception:  # noqa: BLE001
            continue
        nf = root.find("gr-rack/non-fix-components")
        if nf is None:
            continue
        kids = list(nf)
        for i, node in enumerate(kids):
            if node.tag != "component":
                continue
            name = node.get("name")
            if not name or name in library:
                continue
            block = [node]
            for sibling in kids[i + 1:]:
                if sibling.tag == "component":
                    break
                block.append(sibling)
            library[name] = [copy.deepcopy(e) for e in block]
    return library


def build(template_xml: str, blocks: list[list[ET.Element]]) -> str:
    """Return rack XML with the chain replaced by `blocks`, uuids and automation refreshed."""
    root = ET.fromstring(template_xml)

    nf = root.find("gr-rack/non-fix-components")
    if nf is None:
        raise SystemExit("template sem <non-fix-components> / template has no chain container")
    for child in list(nf):
        nf.remove(child)

    for block in blocks:
        for element in block:
            el = copy.deepcopy(element)
            # every component in the element (containers can nest) gets a fresh instance uuid
            for comp in el.iter("component"):
                comp.set("uuid", new_uuid())
            nf.append(el)

    # rebuild the host automation table: drop entries for the old chain, keep the rest
    ha = root.find("realtimecontroldb/host-automationdb")
    if ha is not None:
        alive = {c.get("uuid") for c in root.iter("component") if c.get("uuid")}
        for entry in list(ha):
            if entry.get("uuid") not in alive:
                ha.remove(entry)
        ha.set("num-parameters", str(len(list(ha))))

    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="show placeable components")
    ap.add_argument("--into", help="existing preset to overwrite in place")
    ap.add_argument("--chain", help="comma-separated component names, in signal order")
    ap.add_argument("--template", help="preset to take the header/fixed slots from "
                                       "(default: the file given to --into). Required when "
                                       "--into names a file that does not exist yet.")
    ap.add_argument("--name", help="preset name written into the soundinfo metadata "
                                   "(default: the output filename)")
    ap.add_argument("--backup", action="store_true", help="write a .bak next to --into first")
    ap.add_argument("--replace-container", action="store_true",
                    help="overwrite a GR6 NISH preset with a SoundShell one built from "
                         "--template. Guitar Rig only lists presets its database indexed, and "
                         "it indexes only what it saved itself; since it saves NISH, replacing "
                         "the container is the only way to put a built rack in an indexed slot.")
    ap.add_argument("--path", action="append", default=[], help="extra preset folder to harvest")
    ap.add_argument("--no-check", action="store_true",
                    help="skip the wiring-convention warnings from topology.py")
    args = ap.parse_args()

    files = find_presets(preset_roots(args.path))
    library = harvest(files)

    if args.list or not args.into:
        print(f"componentes colhidos de {len(files)} presets / harvested from {len(files)} presets: "
              f"{len(library)}\n")
        for name in sorted(library):
            n = sum(len(e.findall(".//parameter")) for e in library[name])
            extra = len(library[name]) - 1
            print(f"  {name:<24} {n:>3} parametros" + (f"  (+{extra} sidecar)" if extra else ""))
        if not args.into:
            return

    if not args.chain:
        raise SystemExit("--chain e obrigatorio com --into / --chain is required with --into")

    wanted = [c.strip() for c in args.chain.split(",") if c.strip()]
    missing = [c for c in wanted if c not in library]
    if missing:
        raise SystemExit("nao encontrados nos presets locais / not found in local presets: "
                         + ", ".join(missing))

    # Wiring conventions are advisory, never blocking — an unusual rack can be exactly right,
    # and the corpus only knows what it has seen. But a reversed pair is nearly always a slip.
    if not args.no_check:
        from topology import review
        for note in review(wanted):
            print(f"  aviso: {note}")

    creating = not os.path.exists(args.into)
    if creating and not args.template:
        raise SystemExit("--into nao existe; passe --template com um preset Guitar Rig 4/5 "
                         "para servir de base.\n--into does not exist; pass --template.")

    template_path = args.template or args.into
    tpl_xml, tpl_flavour = read_rack_xml(template_path)
    if tpl_xml is None:
        raise SystemExit(f"sem rack xml / no rack xml in {template_path}")

    # the container always comes from the template when creating, and from the target when
    # rewriting one in place
    source = template_path if (creating or args.replace_container) else args.into
    blob = open(source, "rb").read()
    if blob[:4] != b"-in-":
        raise SystemExit(
            f"{os.path.basename(source)} usa o container NISH do Guitar Rig 6, que so aceita "
            "edicao de largura fixa. Use um preset gravado pelo Guitar Rig 4/5 como base.\n"
            f"{os.path.basename(source)} uses the GR6 NISH container, which only supports "
            "width-preserving edits. Use a Guitar Rig 4/5 preset as the base.")

    if args.backup and not creating:
        shutil.copy(args.into, args.into + ".bak")
        print(f"backup: {args.into}.bak")

    new_xml = build(tpl_xml, [library[c] for c in wanted])

    pf = NgrrFile.parse(blob)
    pf.rack_xml = new_xml

    preset_name = args.name or os.path.splitext(os.path.basename(args.into))[0]
    info = pf.soundinfo_xml
    if info is not None:
        patched, n = re.subn(r"<name>.*?</name>", f"<name>{preset_name}</name>",
                             info, count=1, flags=re.S)
        if n:
            pf.soundinfo_xml = patched
    pf.save(args.into)

    check, _ = read_rack_xml(args.into)
    chain = ET.fromstring(check).find("gr-rack/non-fix-components")
    print(f"\ntemplate : {os.path.basename(template_path)} ({tpl_flavour})")
    print(f"escrito  : {args.into}  ({len(blob)} -> {os.path.getsize(args.into)} bytes)")
    print(f"nome     : {preset_name}")
    print(f"cadeia   : {len(list(chain))} componentes")
    for c in chain:
        print(f"    id={c.get('id'):<8} {c.get('name')}")


if __name__ == "__main__":
    main()
