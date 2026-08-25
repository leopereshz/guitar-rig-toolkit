"""
grpreset.py - inspect and edit Guitar Rig presets (.ngrr).

    python grpreset.py info    <preset.ngrr>
    python grpreset.py dump    <preset.ngrr> [--all]
    python grpreset.py set     <preset.ngrr> -o <out.ngrr> --set "Lead 800:V1=0.75" [--set ...]
    python grpreset.py rename  <preset.ngrr> -o <out.ngrr> --name "My Tone"

Edits are surgical string patches on the preset's rack XML: only the targeted
`value="..."` attribute changes, everything else stays byte-identical. Two container
flavours are handled:

    SoundShell / zlib  (Guitar Rig 4-5 presets, still loaded by GR6) - fully rewritable
    NISH native        (saved by Guitar Rig 6) - the XML is stored uncompressed inside a
                       nested length-prefixed container, so replacement values must keep
                       the exact character width of the original. Guitar Rig writes
                       continuous controls as %.6f, which leaves room for any 0.0-1.0
                       value; switches written as "0"/"1" can only be set to "0"/"1".
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngrr import NgrrFile

XML_OPEN = b"<?xml"
RACK_CLOSE = b"</gr-instrument-chunk>"


class EditError(Exception):
    pass


# --------------------------------------------------------------------------- container

class Preset:
    """Uniform read/write access to both preset container flavours."""

    def __init__(self, path: str):
        self.path = path
        self.blob = open(path, "rb").read()
        if self.blob[:4] == b"-in-":
            self.flavour = "sndf"
            self.file = NgrrFile.parse(self.blob)
            self.rack = self.file.rack_xml
            self._span = None
        else:
            self.flavour = "nish"
            self.file = None
            end = self.blob.find(RACK_CLOSE)
            if end == -1:
                raise EditError(f"{path}: no rack document found")
            end += len(RACK_CLOSE)
            start = self.blob.rfind(XML_OPEN, 0, end)
            self._span = (start, end)
            self.rack = self.blob[start:end].decode("utf-8")

    @property
    def fixed_width(self) -> bool:
        """True when edits must preserve the exact character width of each value."""
        return self.flavour == "nish"

    def save(self, out: str) -> None:
        if self.flavour == "sndf":
            self.file.rack_xml = self.rack
            self.file.save(out)
        else:
            start, end = self._span
            body = self.rack.encode("utf-8")
            if len(body) != end - start:
                raise EditError(
                    f"rack XML changed size by {len(body) - (end - start)} bytes; the GR6 "
                    "container stores lengths in nested headers, so only width-preserving "
                    "edits can be written back"
                )
            with open(out, "wb") as fh:
                fh.write(self.blob[:start] + body + self.blob[end:])

    # ---- preset name lives in the soundinfo document (zlib container only) ----

    def rename(self, new_name: str) -> None:
        if self.flavour != "sndf":
            raise EditError("rename is only supported for the SoundShell/zlib container")
        info = self.file.soundinfo_xml
        if info is None:
            raise EditError("no soundinfo chunk")
        patched, n = re.subn(r"<name>.*?</name>", f"<name>{new_name}</name>", info, count=1, flags=re.S)
        if not n:
            raise EditError("no <name> element in soundinfo")
        self.file.soundinfo_xml = patched


# --------------------------------------------------------------------------- model

def chain_element_ids(root: ET.Element) -> set[int]:
    """Object identities of the components sitting in the user chain.

    Classifying by component id is wrong: at least one component (Loop Machine, id 53000)
    exists both as a fixed rack slot and as a chain entry, so it has to be told apart by
    where it sits in the tree, not by what it is.
    """
    nf = root.find("gr-rack/non-fix-components")
    return set() if nf is None else {id(c) for c in nf.iter("component")}


def components(rack_xml: str):
    """Yield (component_id, component_name, is_fixed, [(param_id, param_name, value)])."""
    root = ET.fromstring(rack_xml)
    chain = chain_element_ids(root)
    for comp in root.iter("component"):
        cid, cname = comp.get("id"), comp.get("name")
        if cid is None:
            continue
        params = [
            (p.get("id"), p.get("name"), p.get("value"))
            for p in comp.iter("parameter")
            if p.get("id") is not None
        ]
        yield cid, cname, id(comp) not in chain, params


def format_to_width(value: str, width: int) -> str:
    """Render `value` as a numeric string of exactly `width` characters."""
    if len(value) == width:
        return value
    try:
        fv = float(value)
    except ValueError as exc:
        raise EditError(f"cannot fit non-numeric value {value!r} into {width} characters") from exc
    for decimals in range(12, -1, -1):
        s = f"{fv:.{decimals}f}"
        if len(s) == width:
            if float(s) != fv:
                print(f"  warning: {value} rounded to {s} to fit {width} characters")
            return s
    raise EditError(
        f"value {value!r} cannot be written in exactly {width} characters "
        f"(the original value's width); pick a value with the same magnitude"
    )


def set_param(rack_xml: str, comp_name: str, param_id: str, value: str, fixed_width: bool) -> str:
    """Patch one parameter's value attribute inside the first matching component block."""
    cm = re.search(rf'<component id="(\d+)" name="{re.escape(comp_name)}"', rack_xml)
    if cm is None:
        raise EditError(f"component {comp_name!r} not found in this preset")
    body_start = cm.end()
    nxt = re.search(r"<component id=", rack_xml[body_start:])
    body_end = body_start + (nxt.start() if nxt else len(rack_xml) - body_start)

    pm = re.search(
        rf'(<parameter id="{re.escape(param_id)}"[^>]*?value=")([^"]*)(")',
        rack_xml[body_start:body_end],
    )
    if pm is None:
        raise EditError(f"parameter {param_id!r} not found on component {comp_name!r}")

    old = pm.group(2)
    new = format_to_width(value, len(old)) if fixed_width else value
    lo = body_start + pm.start(2)
    hi = body_start + pm.end(2)
    print(f"  {comp_name}.{param_id}: {old} -> {new}")
    return rack_xml[:lo] + new + rack_xml[hi:]


# --------------------------------------------------------------------------- commands

def cmd_info(args) -> None:
    p = Preset(args.preset)
    root = ET.fromstring(p.rack)
    chain = [(c, n) for c, n, fx, _ in components(p.rack) if not fx]
    print(f"file       : {os.path.basename(p.path)}  ({len(p.blob)} bytes)")
    print(f"container  : {p.flavour}  (width-preserving edits only: {p.fixed_width})")
    print(f"written by : Guitar Rig {root.get('major-version')}.{root.get('minor-version')}"
          f".{root.get('micro-version')} build {root.get('build-number')}  {root.get('time')}")
    if p.flavour == "sndf":
        m = re.search(r"<name>(.*?)</name>", p.file.soundinfo_xml or "", re.S)
        print(f"preset name: {m.group(1) if m else '?'}")
    print(f"chain      : {len(chain)} component(s)")
    for cid, cname in chain:
        print(f"    id={cid:<8} {cname}")


def cmd_dump(args) -> None:
    p = Preset(args.preset)
    for cid, cname, fixed, params in components(p.rack):
        if fixed and not args.all:
            continue
        tag = " [fixed slot]" if fixed else ""
        print(f"\n{cname}  id={cid}{tag}")
        for pid, pname, value in params:
            print(f"    {pid:<10} {(pname or ''):<24} = {value}")


def cmd_set(args) -> None:
    p = Preset(args.preset)
    print(f"editing {os.path.basename(p.path)} ({p.flavour})")
    for spec in args.set:
        if ":" not in spec or "=" not in spec:
            raise EditError(f'bad --set {spec!r}; expected "Component:ParamId=value"')
        target, value = spec.rsplit("=", 1)
        comp_name, param_id = target.rsplit(":", 1)
        p.rack = set_param(p.rack, comp_name.strip(), param_id.strip(), value.strip(), p.fixed_width)
    p.save(args.out)
    print(f"wrote {args.out}")


def cmd_rename(args) -> None:
    p = Preset(args.preset)
    p.rename(args.name)
    p.save(args.out)
    print(f"wrote {args.out}  (name: {args.name})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("info", help="summarise a preset")
    a.add_argument("preset")
    a.set_defaults(func=cmd_info)

    a = sub.add_parser("dump", help="list components and parameter values")
    a.add_argument("preset")
    a.add_argument("--all", action="store_true", help="include fixed rack slots")
    a.set_defaults(func=cmd_dump)

    a = sub.add_parser("set", help="change parameter values")
    a.add_argument("preset")
    a.add_argument("-o", "--out", required=True)
    a.add_argument("--set", action="append", required=True, metavar='"Comp:Param=value"')
    a.set_defaults(func=cmd_set)

    a = sub.add_parser("rename", help="change the preset's display name")
    a.add_argument("preset")
    a.add_argument("-o", "--out", required=True)
    a.add_argument("--name", required=True)
    a.set_defaults(func=cmd_rename)

    args = ap.parse_args()
    try:
        args.func(args)
    except EditError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
