"""Preset bank: authored starting points, stored as JSON rather than as preset files.

A fresh Guitar Rig install gives this toolkit very little to work with — `rackbuild.py` can
only place components it has seen in a preset, and `scan.py` only learns parameter ranges from
presets that exist. The bank fills that gap with entries somebody dialled deliberately and
contributed as their own work.

Entries are plain JSON, one file per entry, so they read as documentation and merge without
conflicts. `apply` turns one back into a real preset: it builds the chain, writes the values
and assigns the macros in a single step.

    python bank.py list
    python bank.py show <id>
    python bank.py schema
    python bank.py add <preset.ngrr> --id <id> --name "<name>" --author "<you>"
    python bank.py apply <id> --into <indexed preset.ngrr> [--backup]
    python bank.py validate

Only contribute presets you made. Parameter values are a preset's creative content, so
harvesting them out of someone else's pack is redistribution with an extra step — see
bank/README.md.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grpreset import Preset, chain_element_ids, set_param
from macros import relabel, resolve as resolve_component
from ngrr import NgrrFile
from rackbuild import build as build_rack, harvest
from paths import find_presets, preset_roots

HERE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.normpath(os.path.join(HERE, "..", "bank", "entries"))

SCHEMA = {
    "id": "kebab-case identifier, matches the filename",
    "name": "short display name",
    "author": {"name": "who made it", "contact": "optional"},
    "license": "MIT unless stated otherwise",
    "archetype": "optional grouping, e.g. british-crunch, american-clean, modern-high-gain",
    "description": "one or two sentences on what it is for",
    "reference": "the gear reasoning behind it, stated as gear rather than as anyone's patch",
    "guitar": {"pickups": "humbucker | single-coil | either", "position": "bridge | neck | any"},
    "chain": [{"component": "Component Name", "values": {"ParamId": 0.5}}],
    "macros": [{"slot": 1, "component": "Component Name", "param": "ParamId",
                "label": "Gain", "range": [0.0, 1.0]}],
    "notes": "what to reach for first if it is not right on this rig",
}


def entries() -> dict[str, dict]:
    out = {}
    for path in sorted(glob.glob(os.path.join(BANK, "*.json"))):
        e = json.load(open(path, encoding="utf-8"))
        e["_path"] = path
        out[e.get("id", os.path.basename(path)[:-5])] = e
    return out


def dictionary() -> dict:
    p = os.path.join(HERE, "components.json")
    if not os.path.exists(p):
        raise SystemExit("components.json ausente. Rode 'python scan.py'.")
    return json.load(open(p, encoding="utf-8"))["components"]


def by_name(comps: dict) -> dict:
    return {c["name"]: c for c in comps.values()}


# --------------------------------------------------------------------------- commands

def cmd_list(args) -> None:
    es = entries()
    if not es:
        print("banco vazio / bank is empty. Veja bank/README.md.")
        return
    print(f"{len(es)} entrada(s):\n")
    for eid, e in sorted(es.items()):
        chain = " -> ".join(c["component"] for c in e.get("chain", []))
        print(f"  {eid:<24} {e.get('name', '')}")
        print(f"  {'':24} {chain}")
        arch = e.get("archetype")
        author = e.get("author", {}).get("name", "?")
        print(f"  {'':24} arquetipo={arch or '—'}  autor={author}\n")


def cmd_show(args) -> None:
    e = entries().get(args.id)
    if e is None:
        raise SystemExit(f"sem entrada '{args.id}'. Rode 'python bank.py list'.")
    print(f"{e.get('name')}  [{e['id']}]")
    for field in ("archetype", "description", "reference", "notes"):
        if e.get(field):
            print(f"\n{field}:\n  {e[field]}")
    g = e.get("guitar")
    if g:
        print(f"\nguitarra: {g.get('pickups', 'any')} / {g.get('position', 'any')}")
    print(f"\nautor: {e.get('author', {}).get('name', '?')}   licenca: {e.get('license', 'MIT')}")
    print("\ncadeia:")
    for c in e.get("chain", []):
        vals = ", ".join(f"{k}={v}" for k, v in sorted(c.get("values", {}).items()))
        print(f"  {c['component']}")
        if vals:
            print(f"      {vals}")
    if e.get("macros"):
        print("\nmacros:")
        for m in e["macros"]:
            rng = m.get("range", [0, 1])
            print(f"  {m['slot']:>2} \"{m.get('label', '')}\" -> "
                  f"{m['component']}.{m['param']}  [{rng[0]}–{rng[1]}]")


def cmd_schema(args) -> None:
    print(json.dumps(SCHEMA, indent=2, ensure_ascii=False))


def cmd_add(args) -> None:
    pr = Preset(args.preset)
    root = ET.fromstring(pr.rack)
    chain_ids = chain_element_ids(root)
    nf = root.find("gr-rack/non-fix-components")
    if nf is None:
        raise SystemExit("preset sem cadeia / preset has no chain")

    chain = []
    for comp in nf:
        if comp.tag != "component" or comp.get("name") is None:
            continue
        values = {}
        for p in comp.iter("parameter"):
            pid, v = p.get("id"), p.get("value")
            if pid and v is not None:
                values[pid] = float(v) if "." in v else int(v)
        chain.append({"component": comp.get("name"), "values": values})

    macros = []
    cel = root.find("realtimecontroldb/remotecontroldb/component-event-listeners")
    names = {}
    for c in root.iter("component"):
        names.setdefault(c.get("id"), c.get("name"))
    slot_labels = {}
    ae = root.find("realtimecontroldb/aelayer")
    if ae is not None:
        slot_labels = {int(ct.get("slot")): ct.get("name", "") for ct in ae.findall("controltarget")}
    if cel is not None:
        for t in cel.findall("connection-data/target"):
            slot = int(t.get("controller-slot-id"))
            macros.append({
                "slot": slot + 1,
                "component": names.get(t.get("component-id"), "?"),
                "param": t.get("target-name"),
                "label": slot_labels.get(slot, ""),
                "range": [float(t.get("min-value", 0)), float(t.get("max-value", 1))],
            })

    entry = {
        "id": args.id,
        "name": args.name,
        "author": {"name": args.author},
        "license": "MIT",
        "archetype": args.archetype or "",
        "description": "",
        "reference": "",
        "guitar": {"pickups": "either", "position": "any"},
        "chain": chain,
        "macros": macros,
        "notes": "",
    }

    os.makedirs(BANK, exist_ok=True)
    out = os.path.join(BANK, f"{args.id}.json")
    if os.path.exists(out) and not args.force:
        raise SystemExit(f"{out} ja existe. Use --force para sobrescrever.")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(entry, fh, indent=2, ensure_ascii=False)

    print(f"escrito / written: {out}")
    print(f"  cadeia : {len(chain)} componentes, "
          f"{sum(len(c['values']) for c in chain)} valores")
    print(f"  macros : {len(macros)}")
    print("\nPreencha 'description', 'reference' e 'notes' a mao — sao eles que fazem a")
    print("entrada servir para quem nunca ouviu o timbre. Depois rode 'bank.py validate'.")
    print("\nSo contribua preset que voce fez. Ver bank/README.md.")


def cmd_apply(args) -> None:
    e = entries().get(args.id)
    if e is None:
        raise SystemExit(f"sem entrada '{args.id}'")

    library = harvest(find_presets(preset_roots(args.path)))
    wanted = [c["component"] for c in e["chain"]]
    missing = [c for c in wanted if c not in library]
    if missing:
        raise SystemExit(
            "estes componentes nao existem em nenhum preset local, entao nao podem ser "
            "colocados / not present in any local preset: " + ", ".join(missing))

    blob = open(args.into, "rb").read()
    if blob[:4] != b"-in-":
        raise SystemExit(
            "o alvo usa o container NISH do Guitar Rig 6. Use rackbuild.py "
            "--replace-container primeiro, ou aponte para um preset Guitar Rig 4/5.")

    if args.backup:
        shutil.copy(args.into, args.into + ".bak")
        print(f"backup: {args.into}.bak")

    # 1. structure
    tpl_xml = Preset(args.into).rack
    rack = build_rack(tpl_xml, [library[c] for c in wanted])
    pf = NgrrFile.parse(blob)
    pf.rack_xml = rack
    pf.save(args.into)
    print(f"cadeia  : {' -> '.join(wanted)}")

    # 2. values
    pr = Preset(args.into)
    n = 0
    for c in e["chain"]:
        for pid, v in sorted(c.get("values", {}).items()):
            try:
                pr.rack = set_param(pr.rack, c["component"], pid, str(v), pr.fixed_width)
                n += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  aviso: {c['component']}.{pid} -> {exc}")
    pr.save(args.into)
    print(f"valores : {n} aplicados")

    # 3. macros
    if e.get("macros"):
        pf = NgrrFile.load(args.into)
        root = ET.fromstring(pf.rack_xml)
        rtc = root.find("realtimecontroldb")
        rcd = rtc.find("remotecontroldb") if rtc is not None else None
        cel = rcd.find("component-event-listeners") if rcd is not None else None
        if cel is not None:
            for child in list(cel):
                cel.remove(child)
            for m in e["macros"]:
                slot = int(m["slot"]) - 1
                cid = resolve_component(root, m["component"], m["param"])
                lo, hi = m.get("range", [0, 1])
                cd = ET.SubElement(cel, "connection-data", {"version": "7"})
                ET.SubElement(cd, "target", {
                    "component-id": cid, "controller-slot-id": str(slot), "enable": "1",
                    "max-value": str(hi), "min-value": str(lo),
                    "target-name": m["param"], "target-number": "1"})
                if m.get("label"):
                    relabel(root, slot, m["label"])
            cel.set("num-event-listeners", str(len(list(cel))))
            pf.rack_xml = ET.tostring(root, encoding="unicode", xml_declaration=True)
            pf.save(args.into)
            print(f"macros  : {len(e['macros'])} atribuidos")

    print(f"\nescrito : {args.into}")
    print("Carregue com DOIS cliques no Guitar Rig — um clique no preset ja carregado nao rele.")
    if e.get("notes"):
        print(f"\nnota do autor: {e['notes']}")


def cmd_validate(args) -> None:
    comps = by_name(dictionary())
    library = harvest(find_presets(preset_roots(args.path)))
    es = entries()
    errors, warnings = [], []

    for eid, e in sorted(es.items()):
        if eid != e.get("id"):
            errors.append(f"{eid}: campo 'id' ({e.get('id')}) nao casa com o nome do arquivo")
        if not e.get("author", {}).get("name"):
            errors.append(f"{eid}: sem autor — obrigatorio, e a declaracao de que a entrada e sua")
        if not e.get("chain"):
            errors.append(f"{eid}: cadeia vazia")
        for field in ("description", "reference"):
            if not e.get(field):
                warnings.append(f"{eid}: '{field}' vazio — a entrada fica opaca para quem nao "
                                "conhece o timbre")
        for c in e.get("chain", []):
            cn = c.get("component")
            comp = comps.get(cn)
            if comp is None:
                errors.append(f"{eid}: componente '{cn}' nao existe no dicionario")
                continue
            if cn not in library:
                warnings.append(f"{eid}: '{cn}' nao esta em nenhum preset local, "
                                "logo 'apply' falharia aqui")
            for pid in c.get("values", {}):
                if pid not in comp["parameters"]:
                    errors.append(f"{eid}: '{cn}' nao tem parametro '{pid}'")
            # An entry that omits parameters is not reproducible: rackbuild harvests
            # component blocks from whatever local preset happens to have them, so every
            # unspecified value differs from machine to machine.
            omitted = set(comp["parameters"]) - set(c.get("values", {}))
            if omitted:
                warnings.append(
                    f"{eid}: '{cn}' deixa {len(omitted)} parametro(s) sem valor "
                    f"({', '.join(sorted(omitted)[:6])}"
                    f"{'...' if len(omitted) > 6 else ''}) — herdam do preset local de onde o "
                    "componente foi colhido, entao o resultado muda de maquina para maquina")
        for m in e.get("macros", []):
            if not 1 <= int(m.get("slot", 0)) <= 16:
                errors.append(f"{eid}: macro fora de 1..16: {m.get('slot')}")
            comp = comps.get(m.get("component"))
            if comp and m.get("param") not in comp["parameters"]:
                errors.append(f"{eid}: macro aponta para "
                              f"{m.get('component')}.{m.get('param')}, que nao existe")

    print(f"entradas : {len(es)}")
    print(f"erros    : {len(errors)}")
    for x in errors:
        print("  ERRO ", x)
    print(f"avisos   : {len(warnings)}")
    for x in warnings:
        print("  aviso", x)
    sys.exit(1 if errors else 0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("list"); a.set_defaults(func=cmd_list)
    a = sub.add_parser("schema"); a.set_defaults(func=cmd_schema)
    a = sub.add_parser("show"); a.add_argument("id"); a.set_defaults(func=cmd_show)

    a = sub.add_parser("add", help="capture a preset you made as a bank entry")
    a.add_argument("preset")
    a.add_argument("--id", required=True)
    a.add_argument("--name", required=True)
    a.add_argument("--author", required=True, help="you — this is the authorship claim")
    a.add_argument("--archetype")
    a.add_argument("--force", action="store_true")
    a.set_defaults(func=cmd_add)

    a = sub.add_parser("apply", help="write an entry into an indexed preset")
    a.add_argument("id")
    a.add_argument("--into", required=True)
    a.add_argument("--backup", action="store_true")
    a.add_argument("--path", action="append", default=[])
    a.set_defaults(func=cmd_apply)

    a = sub.add_parser("validate")
    a.add_argument("--path", action="append", default=[])
    a.set_defaults(func=cmd_validate)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
