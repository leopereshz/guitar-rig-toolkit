"""Self-contained tests: build a synthetic .ngrr in memory and exercise the writer on it.

`test_roundtrip.py` needs real presets, which not every checkout has and none of which can
be committed. These tests generate their own preset, so they run anywhere and are the ones
CI should gate on.

    python test_fixture.py
"""

from __future__ import annotations

import os
import struct
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngrr import MAGIC, IDENT, Chunk, NgrrFile, NgrrError

SOUNDINFO = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<soundinfo version="400">
  <properties>
    <name>Fixture</name>
  </properties>
</soundinfo>
"""

RACK = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<gr-instrument-chunk build-number="2673" major-version="5" micro-version="0" minor-version="1">
  <gr-rack version="1">
    <fix-components num-items="1">
      <fix-component id="55000" name="Preset Volume">
        <complete>
          <component id="55000" name="Preset Volume" uuid="AAAAAAAAAAAAAAAAAAAAAA==">
            <component-audio version="2">
              <parameters num-parameters="1">
                <parameter id="PV" name="Volume" value="0.500000">
                  <base-parameters remote-max="1" remote-min="0" />
                </parameter>
              </parameters>
            </component-audio>
          </component>
        </complete>
      </fix-component>
    </fix-components>
    <non-fix-components>
      <component id="56000" name="Lead 800" uuid="BBBBBBBBBBBBBBBBBBBBBB==">
        <component-audio version="2">
          <parameters num-parameters="2">
            <parameter id="V1" name="Pre Amp Volume" value="0.75">
              <base-parameters remote-max="1" remote-min="0" />
            </parameter>
            <parameter id="B" name="Bass" value="0.5">
              <base-parameters remote-max="1" remote-min="0" />
            </parameter>
          </parameters>
        </component-audio>
      </component>
    </non-fix-components>
  </gr-rack>
  <realtimecontroldb>
    <aelayer num-controller="1">
      <controltarget name="RK Pedal" slot="0" togglemode="0" />
    </aelayer>
    <remotecontroldb version="4">
      <component-event-listeners num-event-listeners="0" />
    </remotecontroldb>
    <host-automationdb num-parameters="0" />
  </realtimecontroldb>
</gr-instrument-chunk>
"""

SENTINEL = b"   -IN-5GiN    "[:16].ljust(16, b" ")


def make_fixture() -> bytes:
    """A minimal but structurally faithful SoundShell preset."""
    header = MAGIC + struct.pack("<I", 2) + IDENT + b"\x00" * 11 + struct.pack("<I", 0x145)
    body = RACK.encode("utf-8")
    prst = b" LMX" + struct.pack("<II", 1, len(body)) + body
    chunks = [
        Chunk(version=2, name=b"dnss", data=SENTINEL),
        Chunk(version=2, name=b"ofni", data=SOUNDINFO.encode("utf-8")),
        Chunk(version=2, name=b"tsrp", data=prst),
        Chunk(version=2, name=b"DNSS", data=SENTINEL),
    ]
    return header + b"".join(c.serialize() for c in chunks)


def check(label: str, condition: bool, detail: str = "") -> bool:
    print(f"  {'PASS' if condition else 'FAIL'}  {label}{'  ' + detail if detail else ''}")
    return condition


def main() -> int:
    print("fixture sintetica / synthetic fixture")
    blob = make_fixture()
    ok = True

    pf = NgrrFile.parse(blob)
    ok &= check("parseia", [c.label for c in pf.chunks] == ["dnss", "ofni", "tsrp", "DNSS"])
    ok &= check("rebuild byte-exato", pf.serialize() == blob, f"{len(blob)} bytes")
    ok &= check("rack xml recuperado", "<gr-instrument-chunk" in (pf.rack_xml or ""))
    ok &= check("soundinfo recuperado", "<name>Fixture</name>" in (pf.soundinfo_xml or ""))

    # recompression must survive a payload rewrite
    rack = pf.rack_xml
    pf.rack_xml = rack
    again = NgrrFile.parse(pf.serialize())
    ok &= check("recomprime e recarrega", again.rack_xml == rack)

    # a value edit must change exactly that value
    edited = rack.replace('id="V1" name="Pre Amp Volume" value="0.75"',
                          'id="V1" name="Pre Amp Volume" value="0.20"')
    pf.rack_xml = edited
    reread = NgrrFile.parse(pf.serialize())
    root = ET.fromstring(reread.rack_xml)
    v1 = next(p for p in root.iter("parameter") if p.get("id") == "V1")
    b = next(p for p in root.iter("parameter") if p.get("id") == "B")
    ok &= check("valor editado", v1.get("value") == "0.20", f"V1={v1.get('value')}")
    ok &= check("vizinho intacto", b.get("value") == "0.5", f"B={b.get('value')}")

    # chain classification: the fixed slot must not be counted as chain
    nf = root.find("gr-rack/non-fix-components")
    ok &= check("cadeia isolada", [c.get("name") for c in nf] == ["Lead 800"])

    # corrupt input must be refused, not silently accepted
    try:
        NgrrFile.parse(b"NOPE" + blob[4:])
        ok &= check("magic invalido recusado", False)
    except NgrrError:
        ok &= check("magic invalido recusado", True)

    try:
        NgrrFile.parse(blob[:len(blob) - 20])
        ok &= check("arquivo truncado recusado", False)
    except NgrrError:
        ok &= check("arquivo truncado recusado", True)

    print(f"\n{'todos os testes passaram / all tests passed' if ok else 'FALHOU / FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
