"""Round-trip check: parse every .ngrr found and rebuild it byte-for-byte.

Also re-encodes each rack/soundinfo XML through the setters so the recompression path is
exercised, and verifies the rebuilt file re-parses to identical payloads.

    python test_roundtrip.py                    # discovered preset folders
    python test_roundtrip.py --path D:\\Presets  # add another folder

Files in the GR6 native NISH container are counted separately: ngrr.py handles the
SoundShell/zlib container only, and grpreset.py edits NISH files in place instead.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngrr import NgrrFile, NgrrError
from paths import find_presets, preset_roots

ap = argparse.ArgumentParser(description=__doc__,
                             formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--path", action="append", default=[], help="extra preset folder")
args = ap.parse_args()

files = find_presets(preset_roots(args.path))
if not files:
    print("Nenhum preset encontrado. Rode 'python paths.py' ou passe --path.\n"
          "No presets found. Run 'python paths.py' or pass --path.", file=sys.stderr)
    sys.exit(1)

exact = recode = nish = failed = 0
errors: list[str] = []

for path in files:
    blob = open(path, "rb").read()
    if blob[:4] != b"-in-":
        nish += 1          # GR6 native container, not handled by ngrr.py
        continue
    try:
        pf = NgrrFile.parse(blob)

        # 1. identity rebuild must be byte-exact
        if pf.serialize() != blob:
            raise NgrrError("identity rebuild differs from source bytes")
        exact += 1

        # 2. round-trip the XML payloads through the setters and re-parse
        rack, info = pf.rack_xml, pf.soundinfo_xml
        if rack is not None:
            pf.rack_xml = rack
        if info is not None:
            pf.soundinfo_xml = info
        again = NgrrFile.parse(pf.serialize())
        if again.rack_xml != rack or again.soundinfo_xml != info:
            raise NgrrError("payload changed across recompression")
        if [c.name for c in again.chunks] != [c.name for c in pf.chunks]:
            raise NgrrError("chunk list changed across recompression")
        recode += 1
    except Exception as exc:  # noqa: BLE001
        failed += 1
        errors.append(f"{os.path.basename(path)}: {exc}")

print(f"files scanned      : {len(files)}")
print(f"SoundShell/zlib    : {exact + failed}")
print(f"  byte-exact rebuild : {exact}")
print(f"  recompress + reload: {recode}")
print(f"  failed             : {failed}")
print(f"GR6 native (NISH)  : {nish}  (skipped, edited in place by grpreset.py)")
for e in errors[:20]:
    print("  !", e)

sys.exit(1 if failed else 0)
