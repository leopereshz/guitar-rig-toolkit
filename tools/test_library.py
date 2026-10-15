"""Self-contained tests for library.py: the repair that makes Guitar Rig's scan see a preset.

Builds synthetic presets in a temporary folder, so this runs with no Guitar Rig install and
no real .ngrr file.

    python test_library.py
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import library
from test_fixture import make_fixture
from ngrr import NgrrFile

PASS, FAIL = "ok  ", "FAIL"
failures = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global failures
    if not condition:
        failures += 1
    print(f"{PASS if condition else FAIL}  {label}{'  ' + detail if detail else ''}")


def write_preset(directory: str, filename: str, internal_name: str) -> str:
    """Write a fixture preset whose soundinfo carries `internal_name`."""
    path = os.path.join(directory, filename)
    with open(path, "wb") as fh:
        fh.write(make_fixture())
    library.write_preset_name(path, internal_name, path)
    return path


def fix_args(path: str, **over):
    base = dict(path=path, version=None, mode="name", only=None, strip=None,
                apply=True, backup=False)
    base.update(over)
    return argparse.Namespace(**base)


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="grlib-")
    try:
        write_preset(tmp, "Artist - Song.ngrr", "Song")
        write_preset(tmp, "Already Right.ngrr", "Already Right")
        write_preset(tmp, "Pack - Tone.ksd.ngrr", "Tone")
        write_preset(tmp, "Band & Co - Riff.ngrr", "Riff")

        rows = library.survey(tmp, None)
        check("survey reads every file", len(rows) == 4, f"{len(rows)}")
        check("mismatch detected",
              sorted(r["file"] for r in rows if not r["matches"]) ==
              ["Artist - Song.ngrr", "Band & Co - Riff.ngrr", "Pack - Tone.ksd.ngrr"])
        check("match detected",
              [r["file"] for r in rows if r["matches"]] == ["Already Right.ngrr"])
        check("container identified", all(r["container"] == "sndf" for r in rows))

        before = open(os.path.join(tmp, "Artist - Song.ngrr"), "rb").read()
        rack_before = NgrrFile.parse(before).rack_xml

        library.cmd_fix(fix_args(tmp))

        check("every file now matches",
              all(r["matches"] for r in library.survey(tmp, None)))

        after = NgrrFile.load(os.path.join(tmp, "Artist - Song.ngrr"))
        check("rack untouched by the repair", after.rack_xml == rack_before)
        check("name written", library.read_preset_name(
            os.path.join(tmp, "Artist - Song.ngrr"))[1] == "Artist - Song")

        amp = library.read_preset_name(os.path.join(tmp, "Band & Co - Riff.ngrr"))[1]
        check("ampersand round-trips", amp == "Band & Co - Riff", repr(amp))
        check("soundinfo stays well-formed",
              "&amp;" in NgrrFile.load(os.path.join(tmp, "Band & Co - Riff.ngrr")).soundinfo_xml)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # --strip, --only and rename mode, each on its own folder
    tmp = tempfile.mkdtemp(prefix="grlib-")
    try:
        write_preset(tmp, "Pack - Tone.ksd.ngrr", "Tone")
        library.cmd_fix(fix_args(tmp, strip=".ksd"))
        check("--strip drops the second extension",
              os.path.isfile(os.path.join(tmp, "Pack - Tone.ngrr")))
        check("--strip then names the preset after the tidied file",
              library.read_preset_name(os.path.join(tmp, "Pack - Tone.ngrr"))[1] == "Pack - Tone")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    tmp = tempfile.mkdtemp(prefix="grlib-")
    try:
        write_preset(tmp, "A - One.ngrr", "One")
        write_preset(tmp, "A - Two.ngrr", "Two")
        library.cmd_fix(fix_args(tmp, only="Two"))
        names = {f: library.read_preset_name(os.path.join(tmp, f))[1]
                 for f in sorted(os.listdir(tmp))}
        check("--only repairs just the match", names == {"A - One.ngrr": "One",
                                                         "A - Two.ngrr": "A - Two"}, str(names))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    tmp = tempfile.mkdtemp(prefix="grlib-")
    try:
        write_preset(tmp, "Artist - Song.ngrr", "Song")
        write_preset(tmp, "Other - Song.ngrr", "Song")
        library.cmd_fix(fix_args(tmp, mode="rename"))
        left = sorted(os.listdir(tmp))
        check("rename mode renames the files", left == ["Song (2).ngrr", "Song.ngrr"], str(left))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # audio_assets is a pure function over rack XML, so it needs no preset on disk
    import base64
    samples = 8
    payload = base64.b64encode(b"\x00\x01\x02\x03" * samples).decode()
    rack = (
        '<gr-rack>'
        '<component id="118000" name="Reflektor">'
        f'<convolutionreverb channel0="{payload}" factory="0"'
        ' filename="D:\\someone\\else\\cab.wav" irname="cab"'
        f' numchannels="1" numsamples="{samples}" samplerate="44100" version="2"/>'
        '</component>'
        '<component id="56000" name="Tapedeck">'
        '<tapedeckbase filename="F:\\My Music\\111.wav"/>'
        '</component>'
        '</gr-rack>'
    )
    assets = library.audio_assets(rack)
    check("both asset kinds found", len(assets) == 2, str(len(assets)))
    ir = next(a for a in assets if a["element"] == "convolutionreverb")
    check("IR attributed to its component", ir["component"] == "Reflektor", ir["component"])
    check("IR counted as embedded", ir["embeds_audio"] is True)
    check("IR byte count matches numsamples", ir["intact"] is True,
          f"{ir['bytes']} vs {ir['expected']}")
    check("dead IR path reported as unresolved", ir["path_resolves"] is False)

    truncated = rack.replace(payload, base64.b64encode(b"\x00\x01\x02\x03" * 3).decode())
    bad = next(a for a in library.audio_assets(truncated)
               if a["element"] == "convolutionreverb")
    check("truncated IR detected", bad["intact"] is False, f"{bad['bytes']} vs {bad['expected']}")

    tape = next(a for a in assets if a["element"] == "tapedeckbase")
    check("backing track counted as path-only", tape["embeds_audio"] is False)

    print("\nall good" if not failures else f"\n{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
