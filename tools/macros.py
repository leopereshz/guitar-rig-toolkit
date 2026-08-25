"""Assign Guitar Rig's macro controls to rack parameters, from the command line.

Guitar Rig splits controller assignment into two layers:

    global    %LOCALAPPDATA%/Native Instruments/Guitar Rig <n>/Controller Assignments.shm
              maps a MIDI event to one of 16 controller slots. Slots are the macros.
    preset    <gr-instrument-chunk>/realtimecontroldb/remotecontroldb
              maps a controller slot to a component parameter, with a value range.

This tool writes the **preset** layer. That is the half that makes a rack usable: it puts
gain, tone and mix controls for a whole chain onto one macro panel, so dialling a sound no
longer means hunting knobs across several components.

It also means MIDI setup stops being per-preset busywork. Learn 8 CCs onto 8 macros once,
globally, and every preset that carries the same macro layout responds to the same knobs —
no MIDI Learn per parameter, per preset.

    python macros.py list   <preset.ngrr>
    python macros.py assign <preset.ngrr> --map "1=Jump:V1" --map "2=Jump:B" --range "1=0.2,0.8"
    python macros.py clear  <preset.ngrr>

Macro numbers are 1-16 as shown in Guitar Rig; internally they are slots 0-15.

SoundShell presets only (those written by Guitar Rig 4/5, and anything `rackbuild.py`
produces). Assignments add XML elements, which cannot be done inside the GR6 NISH container
without rewriting its nested length headers — see COMPAT.md.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngrr import NgrrFile
from grpreset import chain_element_ids

MAX_MACRO = 16


def _listeners(root: ET.Element) -> ET.Element:
    rtc = root.find("realtimecontroldb")
    if rtc is None:
        raise SystemExit("preset sem <realtimecontroldb> / preset has no <realtimecontroldb>")
    rcd = rtc.find("remotecontroldb")
    if rcd is None:
        rcd = ET.SubElement(rtc, "remotecontroldb", {"version": "4"})
    cel = rcd.find("component-event-listeners")
    if cel is None:
        cel = ET.SubElement(rcd, "component-event-listeners", {"num-event-listeners": "0"})
    return cel


def slot_names(root: ET.Element) -> dict[int, str]:
    ae = root.find("realtimecontroldb/aelayer")
    if ae is None:
        return {}
    return {int(ct.get("slot")): ct.get("name", "") for ct in ae.findall("controltarget")}


def relabel(root: ET.Element, slot: int, label: str) -> None:
    """Rename a controller slot. The name is what Guitar Rig prints under the macro knob,
    so an assigned macro can say 'Bass' instead of 'RK Switch 2'."""
    ae = root.find("realtimecontroldb/aelayer")
    if ae is None:
        return
    for ct in ae.findall("controltarget"):
        if int(ct.get("slot", -1)) == slot:
            ct.set("name", label[:24])
            return


def param_label(root: ET.Element, comp_name: str, param_id: str) -> str:
    """The human name Guitar Rig gives a parameter, for use as a macro label."""
    for c in root.iter("component"):
        if c.get("name") != comp_name:
            continue
        for p in c.iter("parameter"):
            if p.get("id") == param_id:
                return p.get("name") or param_id
    return param_id


def resolve(root: ET.Element, comp_name: str, param_id: str) -> str:
    """Component id for a named chain component, checking the parameter exists on it."""
    chain = chain_element_ids(root)
    matches = [c for c in root.iter("component")
               if c.get("name") == comp_name and id(c) in chain]
    if not matches:
        # fixed slots (Preset Volume, Tuner, ...) are legitimate targets too
        matches = [c for c in root.iter("component") if c.get("name") == comp_name]
    if not matches:
        raise SystemExit(f"componente nao esta neste preset / not in this preset: {comp_name}")
    if len(matches) > 1:
        print(f"  aviso: {comp_name} aparece {len(matches)}x; Guitar Rig enderecha por id, "
              f"entao todas as instancias respondem / all instances will respond")
    comp = matches[0]
    if not any(p.get("id") == param_id for p in comp.iter("parameter")):
        have = ", ".join(sorted({p.get("id") for p in comp.iter("parameter") if p.get("id")}))
        raise SystemExit(f"{comp_name} nao tem parametro '{param_id}'. Tem: {have}")
    return comp.get("id")


def cmd_list(root: ET.Element) -> None:
    names = slot_names(root)
    by_id = {}
    for c in root.iter("component"):
        by_id.setdefault(c.get("id"), c.get("name"))
    cel = root.find("realtimecontroldb/remotecontroldb/component-event-listeners")
    entries = [] if cel is None else cel.findall("connection-data/target")
    print(f"slots de controle / controller slots: {len(names)}")
    print(f"atribuicoes / assignments: {len(entries)}\n")
    for t in entries:
        slot = int(t.get("controller-slot-id"))
        cid = t.get("component-id")
        rng = f"{t.get('min-value')} – {t.get('max-value')}"
        print(f"  macro {slot + 1:>2} ({names.get(slot, '?'):<20}) -> "
              f"{by_id.get(cid, '?')}.{t.get('target-name')}   [{rng}]"
              f"{'' if t.get('enable') == '1' else '  (desabilitado/disabled)'}")
    if not entries:
        print("  (nenhuma / none)")


def cmd_assign(root: ET.Element, maps: list[str], ranges: dict[int, tuple[str, str]],
               labels: dict[int, str], keep: bool) -> None:
    cel = _listeners(root)
    if not keep:
        for child in list(cel):
            cel.remove(child)

    names = slot_names(root)
    for spec in maps:
        if "=" not in spec or ":" not in spec:
            raise SystemExit(f'--map invalido: {spec!r}; use "1=Componente:ParamId"')
        macro_s, target = spec.split("=", 1)
        comp_name, param_id = target.rsplit(":", 1)
        macro = int(macro_s.strip())
        if not 1 <= macro <= MAX_MACRO:
            raise SystemExit(f"macro fora de 1..{MAX_MACRO}: {macro}")
        slot = macro - 1
        cid = resolve(root, comp_name.strip(), param_id.strip())
        lo, hi = ranges.get(macro, ("0", "1"))

        label = labels.get(macro) or param_label(root, comp_name.strip(), param_id.strip())
        relabel(root, slot, label)

        cd = ET.SubElement(cel, "connection-data", {"version": "7"})
        ET.SubElement(cd, "target", {
            "component-id": cid, "controller-slot-id": str(slot), "enable": "1",
            "max-value": hi, "min-value": lo,
            "target-name": param_id.strip(), "target-number": "1",
        })
        print(f"  macro {macro:>2}  \"{label}\"  -> "
              f"{comp_name.strip()}.{param_id.strip()}   [{lo} – {hi}]")

    cel.set("num-event-listeners", str(len(list(cel))))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("list", help="show current macro assignments")
    a.add_argument("preset")

    a = sub.add_parser("assign", help="assign macros to parameters")
    a.add_argument("preset")
    a.add_argument("--map", action="append", required=True, metavar='"N=Component:ParamId"')
    a.add_argument("--range", action="append", default=[], metavar='"N=lo,hi"',
                   help="value range the macro sweeps (default 0,1)")
    a.add_argument("--label", action="append", default=[], metavar='"N=text"',
                   help="macro label (default: the parameter's own name)")
    a.add_argument("--keep", action="store_true", help="add to existing assignments")
    a.add_argument("--backup", action="store_true")

    a = sub.add_parser("clear", help="remove all macro assignments")
    a.add_argument("preset")
    a.add_argument("--backup", action="store_true")

    args = ap.parse_args()

    blob = open(args.preset, "rb").read()
    if blob[:4] != b"-in-":
        raise SystemExit(
            "container NISH do Guitar Rig 6: atribuir macros adiciona elementos XML, o que "
            "exige reescrever os cabecalhos de tamanho aninhados. Use um preset SoundShell "
            "(GR4/5, ou gerado pelo rackbuild.py).\n"
            "GR6 NISH container: assigning macros adds XML elements and needs a SoundShell "
            "preset.")

    pf = NgrrFile.parse(blob)
    root = ET.fromstring(pf.rack_xml)

    if args.cmd == "list":
        cmd_list(root)
        return

    if getattr(args, "backup", False):
        shutil.copy(args.preset, args.preset + ".bak")
        print(f"backup: {args.preset}.bak")

    if args.cmd == "clear":
        cel = _listeners(root)
        n = len(list(cel))
        for child in list(cel):
            cel.remove(child)
        cel.set("num-event-listeners", "0")
        print(f"removidas / removed: {n}")
    else:
        ranges: dict[int, tuple[str, str]] = {}
        for spec in args.range:
            k, v = spec.split("=", 1)
            lo, hi = v.split(",", 1)
            ranges[int(k)] = (lo.strip(), hi.strip())
        labels: dict[int, str] = {}
        for spec in args.label:
            k, v = spec.split("=", 1)
            labels[int(k)] = v.strip()
        cmd_assign(root, args.map, ranges, labels, args.keep)

    pf.rack_xml = ET.tostring(root, encoding="unicode", xml_declaration=True)
    pf.save(args.preset)
    print(f"\nescrito / written: {args.preset}  ({len(blob)} -> {os.path.getsize(args.preset)} bytes)")


if __name__ == "__main__":
    main()
