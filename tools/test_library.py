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

    tmp = tempfile.mkdtemp(prefix="grlib-")
    try:
        write_preset(tmp, "FUINK - Kravitz.ngrr", "FUINK - Kravitz")
        write_preset(tmp, "FUINK - chery2.ngrr", "FUINK - chery2")
        write_preset(tmp, "Untouched.ngrr", "Untouched")
        library.cmd_rename(argparse.Namespace(
            preset=None, to=None, replace="FUINK=FUNK", path=tmp, version=None,
            apply=True, backup=False))
        left = sorted(os.listdir(tmp))
        check("bulk rename renames the files",
              left == ["FUNK - Kravitz.ngrr", "FUNK - chery2.ngrr", "Untouched.ngrr"], str(left))
        check("bulk rename rewrites the internal name too",
              library.read_preset_name(os.path.join(tmp, "FUNK - Kravitz.ngrr"))[1]
              == "FUNK - Kravitz")
        check("bulk rename leaves non-matching presets alone",
              library.read_preset_name(os.path.join(tmp, "Untouched.ngrr"))[1] == "Untouched")
        check("renamed presets still satisfy check",
              all(r["matches"] for r in library.survey(tmp, None)))

        library.cmd_rename(argparse.Namespace(
            preset=os.path.join(tmp, "Untouched.ngrr"), to="Renamed By Hand", replace=None,
            path=None, version=None, apply=True, backup=False))
        check("single rename moves the file",
              os.path.isfile(os.path.join(tmp, "Renamed By Hand.ngrr")))
        check("single rename rewrites the internal name",
              library.read_preset_name(os.path.join(tmp, "Renamed By Hand.ngrr"))[1]
              == "Renamed By Hand")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # indexed_names against a synthetic database. The layout is the one a real gr<n>db
    # uses: a GR<n>:// key per preset, the name repeated after it for presets the scan
    # imported, and the display name placed before the key for ones Guitar Rig saved
    # itself. "ZZ GR7 TEST" is the regression: a bare "GR" terminator truncated it to "ZZ ".
    tmp = tempfile.mkdtemp(prefix="grlib-")
    try:
        dbdir = os.path.join(tmp, "Guitar Rig 7", "Database")
        os.makedirs(dbdir)
        db = os.path.join(dbdir, "gr7db")
        K = "GR7://RackPreset/User/"
        blob = (
            b"\x00\x01binary junk\x00"
            + f"{K}Plain TonePlain Tone".encode()
            + f"{K}Band & Co - RiffBand & Co - Riff".encode()
            + f"New Preset{K}ZZ GR7 TEST".encode()
            + f"{K}80 FUZZ - GRIT80 FUZZ - GRIT".encode()
            + b"\x00\xff tail"
        )
        open(db, "wb").write(blob)
        names = library.indexed_names(db)
        for want in ("Plain Tone", "Band & Co - Riff", "ZZ GR7 TEST", "80 FUZZ - GRIT"):
            check(f"indexed_names finds {want!r}", want in names,
                  "" if want in names else f"got {sorted(names)}")
        check("indexed_names does not keep the truncation", "ZZ " not in names)

        # stale_entries needs a preset folder to compare the database against
        presets = os.path.join(tmp, "Rack Presets")
        os.makedirs(presets)
        for stem in ("Plain Tone", "Band & Co - Riff", "ZZ GR7 TEST"):
            write_preset(presets, stem + ".ngrr", stem)
        stale = library.stale_entries(db, presets)
        check("stale_entries finds the entry with no file",
              stale == ["80 FUZZ - GRIT"], str(stale))

        # a preset whose name repeats its own opening must not be split and declared
        # missing — the whole run is checked against the folder first
        write_preset(presets, "Wah-Wah - Clean Talk.ksd.ngrr", "Wah-Wah - Clean Talk.ksd")
        open(db, "wb").write(f"{K}Wah-Wah - Clean Talk.ksd".encode())
        check("an undoubled name is matched whole, not split at its repeat",
              library.stale_entries(db, presets) == [],
              str(library.stale_entries(db, presets)))

        # names that repeat a letter must not be split into it, and an imported entry
        # carries the folder it came from after the name
        open(db, "wb").write(
            f"{K}ZZTOOL".encode()
            + f"{K}Import Test 01C:\\Users\\x\\PresetsImport Test 01".encode()
            + f"{K}Kravitz 1Kravitz 1".encode()
            + f"{K}KravitzKravitz".encode()
        )
        stale = library.stale_entries(db, presets)
        check("ZZTOOL is not truncated to Z", "ZZTOOL" in stale, str(stale))
        check("an imported entry's path is stripped", "Import Test 01" in stale, str(stale))
        check("names sharing a prefix stay separate",
              "Kravitz" in stale and "Kravitz 1" in stale, str(stale))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # _entry_name: every shape a real database record was seen to take
    check("entry name from the plain doubled form",
          library._entry_name("Plain TonePlain Tone") == "Plain Tone")
    check("entry name with author and comment glued on",
          library._entry_name("Afraid DemonAfraid DemonBen J.californian sound")
          == "Afraid Demon")
    check("entry name with binary bytes between the copies",
          library._entry_name("Gilmour chorus癣㜶Gilmour chorusVC 76")
          == "Gilmour chorus")
    check("a name that merely repeats a letter is left whole",
          library._entry_name("ZZTOOL") == "ZZTOOL")
    # _entry_name on its own would split "Wah-Wah - Clean Talk.ksd" at "Wah", because the
    # repetition it looks for is really there. Only stale_entries can know better, by
    # checking the whole run against the files on disk first — so that is where the
    # guarantee is tested.
    check("_entry_name alone over-splits a name that repeats its own opening",
          library._entry_name("Wah-Wah - Clean Talk.ksd") == "Wah")

    # rack_fingerprint: the same rack saved twice must hash the same
    base = (
        '<gr-instrument-chunk build-number="2447" time="Sat May 12 17:37:02 2018">'
        '<metadata preset-author="&lt;none>" preset-comment="" preset-name="A">'
        '<component id="1000" name="Lead 800" uuid="AAAA">'
        '<parameter id="V1" value="0.750000"/></component>'
        '<automatable-parameter automation-number="17"/>'
        '<automatable-parameter automation-number="41"/>'
        '<preset-ordering order-number="9" tag-path="RP://GR3"/>'
        '<view scroll-position="-54" view-mode="0"/>'
        '</gr-instrument-chunk>'
    )
    copy = (base.replace('uuid="AAAA"', 'uuid="BBBB"')
                .replace('build-number="2447"', 'build-number="2641"')
                .replace('order-number="9"', 'order-number="26"')
                .replace('scroll-position="-54"', 'scroll-position="-170"')
                .replace('<automatable-parameter automation-number="17"/>'
                         '<automatable-parameter automation-number="41"/>',
                         '<automatable-parameter automation-number="41"/>'
                         '<automatable-parameter automation-number="17"/>'))
    check("fingerprint ignores uuid, build, ordering, view and automation order",
          library.rack_fingerprint(base) == library.rack_fingerprint(copy))
    check("fingerprint ignores the preset name, which is compared separately",
          library.rack_fingerprint(base)
          == library.rack_fingerprint(base.replace('preset-name="A"', 'preset-name="B"')))
    check("fingerprint still sees a changed parameter",
          library.rack_fingerprint(base)
          != library.rack_fingerprint(base.replace('0.750000', '0.250000')))
    check("metadata survives the > inside preset-author",
          library.rack_metadata(base) == {"preset-author": "&lt;none>", "preset-comment": "",
                                          "preset-name": "A"},
          str(library.rack_metadata(base)))

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
