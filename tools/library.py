"""
library.py - find out why presets sitting in the Rack Presets folder never show up in
Guitar Rig's browser, and repair them.

    python library.py check  [--path DIR] [--json]
    python library.py index  [--version 7] [--stale]
    python library.py fix    --path DIR [--mode name|rename] [--apply] [--backup]
    python library.py rename --replace "OLD=NEW" [--apply]   |   rename <preset> --to NAME
    python library.py dupes  [--path DIR] [--include-renamed] [--apply]
    python library.py assets [--path DIR] [--json]

Why presets go missing
----------------------
Guitar Rig's library is an index (`Database/gr<n>db`), not a directory listing. Dropping
`.ngrr` files into `User Content/Guitar Rig <n>/Rack Presets` and running
*File > Preferences > Library > Scan* indexes them under the name stored **inside** the
file (the `<name>` element of the soundinfo document), and then resolves that entry back
to `<name>.ngrr` on disk.

When a preset was renamed on disk without its soundinfo being updated - which is what
happens to every pack that ships files as `Artist - Song.ngrr` - the entry cannot be
resolved and the preset is silently dropped from the scan.

Measured on a real Guitar Rig 7.0.2 install: of 537 presets copied into the folder, the
93 whose file name matched their internal name were indexed and the other 444 were not.
The correlation was exact in both directions.

Two ways to repair that, both of which make the two names agree again:

    --mode name     rewrite the soundinfo <name> to the file name  (default)
                    keeps the descriptive file names; the browser shows
                    "Guns n Roses - Dont cry" instead of "Dont cry"
    --mode rename   rename the file to the internal name
                    needed for presets saved by Guitar Rig 6+ (NISH container), whose
                    metadata cannot be resized in place

After either repair, run the Scan in Guitar Rig again.

`rename` exists so that renaming a preset does not recreate the problem: it moves the file
and rewrites the internal name in one step, which is the invariant everything else here
depends on. `--replace "FUINK=FUNK"` fixes a typo across a whole folder.

External audio
--------------
`assets` answers the other question a moved preset collection raises: does anything in it
point at an audio file that is no longer there? Two components store one.

    Reflektor / convolutionreverb   impulse response
    Tapedeck                        the loaded backing track

Reflektor embeds the impulse response in the preset, as `channel0`/`channel1` base64 next
to the original `filename`. The path is provenance, not a lookup - a preset whose IR came
from someone else's machine still plays it. `assets` decodes the base64 and checks it
against `numsamples * numchannels * 4`, which is what actually says whether the IR
survived. Tapedeck stores a path only, so a missing file there is a real loss, though it
costs nothing but the backing track.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths as grpaths
from grpreset import Preset, components
from ngrr import NgrrFile, NgrrError

NAME_RE = re.compile(r"<name>(.*?)</name>", re.S)
# a path or a URI scheme inside a database entry, either of which marks where the name
# ended. The drive-letter form needs its backslash: "CP://" is Guitar Rig's component
# preset scheme, not C: on a disk.
PATH_RE = re.compile(r"[A-Za-z]:\\|[A-Za-z]{2,}://|/Users/|/Volumes/")


class LibraryError(Exception):
    pass


# --------------------------------------------------------------------------- reading

def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _unescape(text: str) -> str:
    return text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def read_preset_name(path: str) -> tuple[str, str | None]:
    """Return (container_flavour, internal preset name)."""
    blob = open(path, "rb").read()
    if blob[:4] == b"-in-":
        info = NgrrFile.parse(blob).soundinfo_xml
        if info is None:
            return "sndf", None
        m = NAME_RE.search(info)
        return "sndf", _unescape(m.group(1)) if m else None

    # NISH: the soundinfo document is stored as plain XML inside the container
    start = blob.find(b"<soundinfo")
    if start == -1:
        return "nish", None
    end = blob.find(b"</soundinfo>", start)
    info = blob[start:end].decode("utf-8", "replace")
    m = NAME_RE.search(info)
    return "nish", _unescape(m.group(1)) if m else None


def write_preset_name(path: str, new_name: str, out: str) -> None:
    """Rewrite the soundinfo <name>. SoundShell/zlib container only."""
    blob = open(path, "rb").read()
    if blob[:4] != b"-in-":
        raise LibraryError(
            "the NISH container stores its metadata in nested length-prefixed records, "
            "so the name cannot be resized in place - use --mode rename for this file"
        )
    f = NgrrFile.parse(blob)
    info = f.soundinfo_xml
    if info is None:
        raise LibraryError("no soundinfo chunk")
    patched, n = NAME_RE.subn(f"<name>{_escape(new_name)}</name>", info, count=1)
    if not n:
        raise LibraryError("no <name> element in soundinfo")
    f.soundinfo_xml = patched
    f.save(out)


# --------------------------------------------------------------------------- database

def _user_entry_runs(db_path: str) -> list[str]:
    """The raw text following each `GR<n>://RackPreset/User/` key in the database."""
    m = re.search(r"Guitar Rig (\d+)", db_path)
    version = m.group(1) if m else "7"
    scheme = f"GR{version}://".encode()
    prefix = scheme + b"RackPreset/User/"
    raw = open(db_path, "rb").read()

    runs = []
    for hit in re.finditer(re.escape(prefix), raw):
        i = hit.end()
        j = i
        while j < len(raw) and raw[j] >= 0x20 and raw[j] != 0x7F:
            j += 1
        run = raw[i:j]
        cut = run.find(scheme)
        if cut > 0:
            run = run[:cut]
        text = run.decode("utf-8", "replace")
        if text:
            runs.append(text)
    return runs


def _entry_name(text: str) -> str:
    """The preset name inside one database entry's text.

    A record is `name + name` followed by the author, the comment and whatever opens the
    next record, all of it variable length - "Afraid Octaver DemonAfraid Octaver DemonBen
    J. Schlesingercalifornian grunge/metal sound !". The repetition is the only reliable
    signal, so the name is the longest prefix that appears twice in a row; how much of
    the text that accounts for says nothing.

    The two copies are not always adjacent: a couple of binary bytes can land between
    them and decode as anything, so the second copy is looked for anywhere later rather
    than immediately after the first.

    Splits shorter than three characters are refused, which is what keeps "ZZTOOL" from
    collapsing to "Z" on the coincidence of its first two letters.
    """
    half = len(text) // 2
    for n in range(half, 2, -1):
        if text[:n] == text[n:n * 2]:
            return text[:n]
    # the copies were not adjacent; allow a few bytes of slack, but no more, or a shared
    # prefix between two unrelated presets ("Blues Rock - X" / "Blues Rock - Y") passes
    for n in range(half, 2, -1):
        j = text.find(text[:n], n)
        if j != -1 and j - n <= 4:
            return text[:n]
    return text


def stale_entries(db_path: str, directory: str) -> list[str]:
    """Indexed names with no matching `<name>.ngrr` in `directory`.

    Guitar Rig's Scan is additive: it adds what it finds and leaves everything already in
    the database alone, so renaming or deleting a preset file leaves its old entry behind
    and the browser keeps offering a preset that cannot load. Measured by renaming six
    presets and rescanning: the six new names were added and the six old ones stayed.

    The names come from `_entry_name`, so an entry is called stale only when nothing on
    disk carries that exact name.
    """
    stems = {os.path.splitext(f)[0] for f in os.listdir(directory)
             if f.lower().endswith(".ngrr")}
    stale = []
    for text in _user_entry_runs(db_path):
        # An entry Guitar Rig imported stores the folder it came from after the name, so
        # cut at the first absolute path.
        cut = PATH_RE.search(text)
        if cut and cut.start() > 0:
            text = text[:cut.start()]
        # The whole run is tested before any splitting: "Wah-Wah - Clean Talk.ksd" is a
        # preset name, and asking _entry_name about it first would split it at "Wah".
        if text in stems or text[:-1] in stems:
            continue          # a single stray byte sometimes trails the name
        name = _entry_name(text)
        if name in stems or name[:-1] in stems:
            continue
        if name not in stale:
            stale.append(name)
    return stale


def indexed_names(db_path: str) -> set[str]:
    """Preset names the Guitar Rig database currently indexes under its User bank.

    Entries are stored as the key `GR<n>://RackPreset/User/<name>`, usually followed by the
    same name again as the display string, though a preset Guitar Rig saved itself carries
    its display name before the key instead. Neither is length-prefixed in a way that has
    been decoded, so the name is read up to whatever follows: the next `GR<n>://` key, or
    the end of the printable run.

    The terminator has to be the whole scheme. Cutting at a bare "GR" truncates every
    preset with those two letters in its name — "ZZ GR7 TEST" became "ZZ ".
    """
    names: set[str] = set()
    for text in _user_entry_runs(db_path):
        # The record form repeats the name, and whatever string starts the next record can
        # be glued to the end of it ("…RiffBand & Co - RiffNew Preset"), so the split is the
        # longest prefix that appears twice in a row rather than an exact halving. The
        # reference form does not repeat at all, hence the raw text as a candidate too.
        for n in range(len(text) // 2, 0, -1):
            if text[:n] == text[n:n * 2]:
                names.add(text[:n])
                break
        names.add(text)
    return names


def database_for(version: str | None) -> str | None:
    for d in grpaths.database_dirs():
        if version and f"Guitar Rig {version}" not in d:
            continue
        for entry in os.listdir(d):
            if re.fullmatch(r"gr\d+db", entry):
                return os.path.join(d, entry)
    return None


# --------------------------------------------------------------------------- survey

def survey(directory: str, db_path: str | None) -> list[dict]:
    known = indexed_names(db_path) if db_path else set()
    rows = []
    for entry in sorted(os.listdir(directory)):
        if not entry.lower().endswith(".ngrr"):
            continue
        full = os.path.join(directory, entry)
        stem = os.path.splitext(entry)[0]
        row = {"file": entry, "stem": stem}
        try:
            flavour, name = read_preset_name(full)
            row["container"] = flavour
            row["name"] = name
        except (NgrrError, OSError) as exc:
            row["error"] = str(exc)
            rows.append(row)
            continue
        row["matches"] = (name == stem)
        if db_path:
            row["indexed"] = bool(name) and name in known
        rows.append(row)
    return rows


def cmd_check(args) -> None:
    directory = args.path or default_preset_dir(getattr(args, "version", None))
    db_path = args.db or database_for(args.version)
    rows = survey(directory, db_path)

    if args.json:
        print(json.dumps({"directory": directory, "database": db_path, "presets": rows},
                         ensure_ascii=False, indent=2))
        return

    bad = [r for r in rows if not r.get("error") and not r["matches"]]
    broken = [r for r in rows if r.get("error")]
    print(f"folder   : {directory}")
    print(f"database : {db_path or '(not found)'}")
    print(f"presets  : {len(rows)}")
    print(f"  file name matches internal name : {len(rows) - len(bad) - len(broken)}")
    print(f"  mismatched (will not be indexed): {len(bad)}")
    if broken:
        print(f"  unreadable                      : {len(broken)}")

    if db_path:
        shown = sum(1 for r in rows if r.get("indexed"))
        print(f"  currently in the database       : {shown}")
        anomalies = [r for r in rows if r.get("indexed") and not r["matches"]]
        if anomalies:
            print(f"  indexed despite a mismatch      : {len(anomalies)}"
                  "  (name shared with another file)")

    if bad:
        print("\nmismatches (file name -> internal name):")
        for r in bad[:args.limit]:
            flag = "" if r["container"] == "sndf" else "   [NISH: use --mode rename]"
            print(f"  {r['stem']}\n     -> {r['name']!r}{flag}")
        if len(bad) > args.limit:
            print(f"  ... and {len(bad) - args.limit} more (--limit to see them)")
        print(f"\nrepair: python library.py fix --path \"{directory}\" --apply")
    for r in broken:
        print(f"  unreadable: {r['file']}: {r['error']}")


def cmd_index(args) -> None:
    db_path = args.db or database_for(args.version)
    if not db_path:
        raise LibraryError("no Guitar Rig database found")
    directory = args.path or default_preset_dir(args.version)

    if args.stale:
        stale = stale_entries(db_path, directory)
        print(f"database : {db_path}")
        print(f"folder   : {directory}")
        print(f"entries with no matching file: {len(stale)}")
        for n in stale:
            print("  ", n)
        if stale:
            print()
            print("The Scan only adds; it never removes. These entries are still offered in")
            print("the browser and will fail to load. Right-click each one there and delete")
            print("it — Guitar Rig owns its database and nothing here writes to it.")
        return

    names = sorted(n for n in indexed_names(db_path) if n)
    print(f"database: {db_path}")
    print(f"user presets indexed: {len(names)}")
    for n in names[:args.limit]:
        print("  ", n)
    if len(names) > args.limit:
        print(f"  ... and {len(names) - args.limit} more")


# --------------------------------------------------------------------------- duplicates

# Everything below is per-instance bookkeeping, library housekeeping or window state.
# None of it changes what the rack does, and all of it differs between two copies of the
# same preset that came out of a zip twice.
def _tag(name: str) -> re.Pattern:
    """Match one element by name, tolerating `>` inside a quoted attribute value.

    `<metadata[^>]*>` is wrong here and quietly so: Guitar Rig writes
    `preset-author="&lt;none>"`, whose `>` ends the match early and leaves the remaining
    attributes behind as text.
    """
    return re.compile(r'<' + name + r'((?:\s+[\w:.-]+="[^"]*")*)\s*/?>')


NOISE = (
    re.compile(r'\s+uuid="[^"]*"'),            # per-instance component id
    _tag("gr-instrument-chunk"),               # build number and save timestamp
    _tag("tapedeckbase"),                      # last backing track the author had open
    _tag("metronomau"),
    _tag("preset-ordering"),                   # position in the author's browser
    _tag("view"),                              # panel open, scrolled, zoomed
    re.compile(r'\s+(?:scroll-position|icons-visible|view-mode|stored-view-mode)="[^"]*"'),
)
# The name, author and comment are compared separately: two copies of one rack under
# different names are a decision for a person, not something to collapse silently.
METADATA = _tag("metadata")
AUTOMATION = re.compile(r'<automatable-parameter automation-number="(\d+)"\s*/>')
META_FIELD = re.compile(r'(preset-name|preset-author|preset-comment)="([^"]*)"')


def rack_fingerprint(rack_xml: str) -> str:
    """Hash of what the rack actually does, with per-copy bookkeeping removed.

    Automation numbers are sorted before hashing: two copies of one preset list the same
    set in a different order, which is serialisation order rather than a difference.
    """
    x = rack_xml
    for pattern in NOISE:
        x = pattern.sub("", x)
    x = METADATA.sub("<metadata>", x)
    numbers = sorted(AUTOMATION.findall(x))
    x = AUTOMATION.sub("", x) + "|automation:" + ",".join(numbers)
    x = re.sub(r"\s+", " ", x)
    return hashlib.sha256(x.encode("utf-8")).hexdigest()


def rack_metadata(rack_xml: str) -> dict:
    m = METADATA.search(rack_xml)
    return dict(META_FIELD.findall(m.group(1))) if m else {}


def rack_profile(rack_xml: str) -> tuple:
    """The chain and every parameter value, read as structure rather than as text.

    `rack_fingerprint` hashes a normalised document, so two racks that hash alike must
    agree on their components as well - but "must" is an argument, and deleting someone's
    presets deserves a check. This walks the parsed rack, and groups are compared on it
    element by element before anything is removed.
    """
    chain, fixed = [], []
    for cid, cname, is_fixed, params in components(rack_xml):
        entry = (cid, cname, tuple(sorted((pid, value) for pid, _n, value in params)))
        (fixed if is_fixed else chain).append(entry)
    return tuple(chain), tuple(sorted(fixed))


def profile_summary(profile: tuple) -> tuple[str, int]:
    chain, fixed = profile
    names = " > ".join(c[1] for c in chain) or "(empty chain)"
    return names, sum(len(c[2]) for c in chain) + sum(len(c[2]) for c in fixed)


def _keep_rank(entry: dict) -> tuple:
    """Lower sorts first: the copy worth keeping out of a group of identical racks.

    Order of preference: it credits an author, it carries a comment, its name is not a
    copy marker, it has no stray `.ksd` in it, and then the *longer* name wins. Longer is
    deliberate - the extra length is almost always the band or song someone added to make
    the preset findable ("Guns n Roses - Nighttrain" over "Nighttrain 1").
    """
    stem = os.path.splitext(entry["file"])[0]
    meta = entry["meta"]
    return (
        0 if meta.get("preset-author") else 1,
        0 if meta.get("preset-comment") else 1,
        1 if re.search(r"(?:\(\d+\)|\s\d+)$", stem) else 0,   # "… (2)", "… 1"
        1 if ".ksd" in stem.lower() else 0,
        -len(stem),
        stem.lower(),
    )


def find_duplicates(directory: str) -> tuple[list, list, list]:
    """Groups of copies: fully identical, same rack under another name, and - if the
    fingerprint ever disagreed with a component-level comparison - the groups where that
    happened, which are never touched and mean this code has a bug."""
    entries = []
    for f in sorted(os.listdir(directory)):
        if not f.lower().endswith(".ngrr"):
            continue
        try:
            rack = Preset(os.path.join(directory, f)).rack
        except Exception:
            continue
        entries.append({"file": f, "fingerprint": rack_fingerprint(rack),
                        "meta": rack_metadata(rack), "profile": rack_profile(rack),
                        "size": os.path.getsize(os.path.join(directory, f))})

    groups: dict[str, list] = {}
    for e in entries:
        groups.setdefault(e["fingerprint"], []).append(e)

    same, renamed, disputed = [], [], []
    for members in groups.values():
        if len(members) < 2:
            continue
        members.sort(key=_keep_rank)
        # independent of the hash: the chain and every parameter value must agree
        if any(m["profile"] != members[0]["profile"] for m in members[1:]):
            disputed.append(members)
            continue
        labels = {(m["meta"].get("preset-name", ""), m["meta"].get("preset-author", ""),
                   m["meta"].get("preset-comment", "")) for m in members}
        (same if len(labels) == 1 else renamed).append(members)
    for g in (same, renamed, disputed):
        g.sort(key=lambda m: m[0]["file"].lower())
    return same, renamed, disputed


def cmd_dupes(args) -> None:
    directory = args.path or default_preset_dir(args.version)
    same, renamed, disputed = find_duplicates(directory)

    if args.json:
        print(json.dumps({"directory": directory, "identical": same,
                          "same_rack_different_name": renamed,
                          "fingerprint_disputed": disputed}, ensure_ascii=False, indent=2))
        return

    print(f"folder : {directory}")
    print(f"identical presets         : {len(same)} group(s), "
          f"{sum(len(g) - 1 for g in same)} removable")
    print(f"same rack, different name : {len(renamed)} group(s), "
          f"{sum(len(g) - 1 for g in renamed)} removable")

    if disputed:
        print(f"\n{len(disputed)} group(s) hashed alike but their components do not match.")
        print("That is a bug in the fingerprint, not a duplicate. Left untouched:")
        for g in disputed:
            print("  " + " | ".join(m["file"] for m in g))

    if renamed:
        print("\nSame rack, different name or author. To a person these are not the same")
        print("preset, so they are left alone unless you pass --include-renamed:")
        for g in renamed:
            print("  " + " | ".join(
                f"{m['file']} [{m['meta'].get('preset-name') or '(sem nome)'}]" for m in g))

    targets = same + renamed if args.include_renamed else same
    if not targets:
        print("\nnothing to remove")
        return

    removed = 0
    print("\nkeeping the first of each group. The chain and parameter count shown were")
    print("compared component by component across the group, not just hashed:")
    for g in targets:
        chain, nparams = profile_summary(g[0]["profile"])
        print(f"\n  {chain}")
        print(f"  {len(g[0]['profile'][0])} in the chain, {nparams} parameter values, "
              f"identical across all {len(g)}")
        print(f"  KEEP {g[0]['file']}")
        for m in g[1:]:
            print(f"  del  {m['file']}")
            if args.apply:
                os.remove(os.path.join(directory, m["file"]))
            removed += 1

    print(f"\n{removed} file(s) {'deleted' if args.apply else 'would be deleted'}")
    if args.apply:
        print("Guitar Rig's database still lists them. Clean it from")
        print("File > Preferences > Library; 'library.py index --stale' shows which rows.")
    else:
        print("this was a dry run - add --apply to delete them")


# --------------------------------------------------------------------------- assets

ELEM_RE = re.compile(r'<([a-zA-Z0-9_-]+)((?:\s+[a-zA-Z0-9_-]+="[^"]*")*)\s*/?>')
ATTR_RE = re.compile(r'([a-zA-Z0-9_-]+)="([^"]*)"')
COMP_RE = re.compile(r'name="([^"]*)"')

# element -> (what it is, whether the audio travels inside the preset)
ASSET_ELEMENTS = {
    "convolutionreverb": ("impulse response", True),
    "tapedeckbase": ("backing track", False),
}


def audio_assets(rack_xml: str) -> list[dict]:
    """Every external audio file this rack points at, and whether it still has the audio."""
    import base64

    found = []
    for m in ELEM_RE.finditer(rack_xml):
        kind = ASSET_ELEMENTS.get(m.group(1))
        if kind is None:
            continue
        attrs = dict(ATTR_RE.findall(m.group(2)))
        filename = attrs.get("filename", "")
        if not filename and not attrs.get("irname"):
            continue

        start = rack_xml.rfind("<component ", 0, m.start())
        owner = COMP_RE.search(rack_xml[start:rack_xml.find(">", start)]) if start >= 0 else None

        row = {
            "element": m.group(1),
            "what": kind[0],
            "component": owner.group(1) if owner else "?",
            "filename": filename,
            "name": attrs.get("irname") or os.path.basename(filename.replace("\\", "/")),
            "path_resolves": bool(filename) and os.path.isfile(filename),
            "embeds_audio": kind[1],
        }
        if kind[1]:
            channels = sorted(k for k in attrs if k.startswith("channel"))
            try:
                got = sum(len(base64.b64decode(attrs[k])) for k in channels)
            except Exception:
                got = -1
            want = int(attrs.get("numsamples") or 0) * int(attrs.get("numchannels") or 1) * 4
            row.update(samples=attrs.get("numsamples", ""), channels=len(channels),
                       bytes=got, expected=want, intact=(got == want and want > 0))
        found.append(row)
    return found


def cmd_assets(args) -> None:
    directory = args.path or default_preset_dir(getattr(args, "version", None))
    rows = []
    for entry in sorted(os.listdir(directory)):
        if not entry.lower().endswith(".ngrr"):
            continue
        try:
            rack = Preset(os.path.join(directory, entry)).rack
        except Exception as exc:
            rows.append({"file": entry, "error": str(exc)[:80]})
            continue
        for asset in audio_assets(rack):
            rows.append(dict(asset, file=entry))

    if args.json:
        print(json.dumps({"directory": directory, "assets": rows}, ensure_ascii=False, indent=2))
        return

    embedded = [r for r in rows if r.get("embeds_audio")]
    external = [r for r in rows if "embeds_audio" in r and not r["embeds_audio"]]
    broken_embedded = [r for r in embedded if not r.get("intact")]
    missing_external = [r for r in external if not r["path_resolves"]]

    print(f"folder : {directory}")
    print(f"presets pointing at an audio file outside themselves : "
          f"{len({r['file'] for r in rows if 'what' in r})}")
    print()
    print(f"impulse responses (embedded in the preset) : {len(embedded)}")
    print(f"  audio intact                             : {len(embedded) - len(broken_embedded)}")
    print(f"  original path still resolves             : "
          f"{sum(1 for r in embedded if r['path_resolves'])}"
          "   (does not matter — see below)")
    factory = [r for r in missing_external if "Native Instruments" in r["filename"]]
    print(f"Tapedeck backing tracks (path only)        : {len(external)}")
    print(f"  file missing                             : {len(missing_external)}"
          f"   ({len(factory)} of them factory content)")

    if embedded:
        print("\nimpulse responses:")
        for r in embedded:
            mark = "ok " if r.get("intact") else "BAD"
            print(f"  [{mark}] {r['file']}")
            print(f"        {r['name']}  —  {r['samples']} samples x {r['channels']} ch, "
                  f"{r['bytes']} bytes embedded (expected {r['expected']})")
            if not r["path_resolves"] and r["filename"]:
                print(f"        original path is gone: {r['filename']}")
    if broken_embedded:
        print("\nThese impulse responses are NOT intact — the preset lost its audio and the\n"
              "IR has to be reloaded by hand in Reflektor.")
    elif embedded:
        print("\nEvery impulse response carries its own samples, so the dead paths above are\n"
              "cosmetic: Reflektor plays them without the original .wav. Copying those .wav\n"
              "files anywhere, or renaming them, changes nothing either way.")

    if missing_external:
        own = [r for r in missing_external if r not in factory]
        print(f"\nTapedeck remembers the last backing track the preset's author had loaded.")
        print(f"{len(missing_external)} of those paths do not exist here — {len(factory)} point at "
              f"Guitar Rig factory content that is")
        print(f"not installed, {len(own)} at files on someone else's machine. None of it affects "
              f"the tone:")
        print("Tapedeck is the practice player, not part of the signal chain. Nothing to repair.")
        if args.verbose:
            for r in missing_external:
                print(f"  {r['file']}\n     {r['filename']}")
        else:
            print("  (--verbose lists them)")

    for r in rows:
        if "error" in r:
            print(f"  unreadable: {r['file']}: {r['error']}")


# --------------------------------------------------------------------------- repair

def unique_target(directory: str, stem: str, taken: set[str]) -> str:
    candidate = stem
    n = 2
    while candidate.lower() in taken:
        candidate = f"{stem} ({n})"
        n += 1
    taken.add(candidate.lower())
    return candidate


def cmd_rename(args) -> None:
    """Rename presets, file and internal name together, so the pair stays consistent."""
    if args.preset:
        if not args.to:
            raise LibraryError("renaming one preset needs --to")
        jobs = [(os.path.dirname(os.path.abspath(args.preset)),
                 os.path.basename(args.preset), args.to)]
    else:
        if not args.replace or "=" not in args.replace:
            raise LibraryError('bulk renaming needs --replace "OLD=NEW"')
        old, new = args.replace.split("=", 1)
        directory = args.path or default_preset_dir(args.version)
        jobs = []
        for entry in sorted(os.listdir(directory)):
            if not entry.lower().endswith(".ngrr"):
                continue
            stem = os.path.splitext(entry)[0]
            if old in stem:
                jobs.append((directory, entry, stem.replace(old, new)))

    if not jobs:
        print("nothing matched")
        return

    done = skipped = 0
    for directory, entry, new_stem in jobs:
        src = os.path.join(directory, entry)
        dst = os.path.join(directory, new_stem + ".ngrr")
        flavour, name = read_preset_name(src)
        if flavour == "nish":
            print(f"  skip {entry}: NISH container, its name cannot be resized in place")
            skipped += 1
            continue
        if os.path.exists(dst) and os.path.abspath(dst) != os.path.abspath(src):
            print(f"  skip {entry}: {new_stem}.ngrr already exists")
            skipped += 1
            continue
        print(f"  {entry}  ->  {new_stem}.ngrr")
        print(f"       internal name {name!r} -> {new_stem!r}")
        if args.apply:
            if args.backup:
                shutil.copy2(src, src + ".bak")
            write_preset_name(src, new_stem, src)
            if os.path.abspath(dst) != os.path.abspath(src):
                os.rename(src, dst)
        done += 1

    print(f"\n{done} preset(s) {'renamed' if args.apply else 'would be renamed'}"
          f"{f', {skipped} skipped' if skipped else ''}")
    if args.apply:
        print("Guitar Rig's Scan only adds entries, it never removes them, so the old")
        print("names stay in the browser even after a rescan. 'library.py index --stale'")
        print("lists them; delete those in the browser by hand.")
    else:
        print("this was a dry run - add --apply to write the changes")


def cmd_fix(args) -> None:
    directory = args.path or default_preset_dir(args.version)
    rows = survey(directory, None)
    todo = [r for r in rows if not r.get("error") and not r["matches"]]
    if args.only:
        needle = args.only.lower()
        todo = [r for r in todo if needle in r["file"].lower()]
    if not todo:
        print(f"{directory}: nothing to repair, every file name already matches its preset name")
        return

    taken = {os.path.splitext(r["file"])[0].lower() for r in rows}
    changed = skipped = 0

    for r in todo:
        src = os.path.join(directory, r["file"])
        if args.strip and r["stem"].lower().endswith(args.strip.lower()):
            tidy = r["stem"][: -len(args.strip)].rstrip()
            if tidy and tidy.lower() not in taken:
                taken.discard(r["stem"].lower())
                taken.add(tidy.lower())
                new_file = tidy + ".ngrr"
                print(f"  {r['file']}  ->  {new_file}")
                if args.apply:
                    os.rename(src, os.path.join(directory, new_file))
                src = os.path.join(directory, new_file)
                r = dict(r, file=new_file, stem=tidy)
        if args.mode == "rename" or r["container"] == "nish":
            if not r["name"]:
                print(f"  skip {r['file']}: no internal name to rename to")
                skipped += 1
                continue
            if args.mode == "name" and r["container"] == "nish":
                print(f"  skip {r['file']}: NISH container, rerun with --mode rename")
                skipped += 1
                continue
            taken.discard(os.path.splitext(r["file"])[0].lower())
            target = unique_target(directory, r["name"], taken) + ".ngrr"
            print(f"  {r['file']}  ->  {target}")
            if args.apply:
                os.rename(src, os.path.join(directory, target))
        else:
            print(f"  {r['file']}: {r['name']!r} -> {r['stem']!r}")
            if args.apply:
                if args.backup:
                    shutil.copy2(src, src + ".bak")
                write_preset_name(src, r["stem"], src)
        changed += 1

    print(f"\n{changed} preset(s) {'repaired' if args.apply else 'would be repaired'}"
          f"{f', {skipped} skipped' if skipped else ''}")
    if args.apply:
        print("now run File > Preferences > Library > Scan in Guitar Rig")
    else:
        print("this was a dry run - add --apply to write the changes")


# --------------------------------------------------------------------------- cli

def default_preset_dir(version: str | None = None) -> str:
    roots = sorted(grpaths.preset_roots(), key=grpaths.version_of, reverse=True)
    for root in roots:
        if version and f"Guitar Rig {version}" not in root:
            continue
        candidate = os.path.join(root, "Rack Presets")
        if os.path.isdir(candidate):
            return candidate
    if version:
        raise LibraryError(f"no Rack Presets folder found for Guitar Rig {version}; pass --path")
    raise LibraryError("no Rack Presets folder found; pass --path")


def main() -> None:
    # preset names routinely carry accents and mojibake from old packs; a cp1252 console
    # would abort the run halfway through
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("check", help="report presets the library scan will ignore")
    a.add_argument("--path", help="Rack Presets folder (default: newest install)")
    a.add_argument("--version", help="Guitar Rig version whose database to read, e.g. 7")
    a.add_argument("--db", help="explicit path to gr<n>db")
    a.add_argument("--limit", type=int, default=20)
    a.add_argument("--json", action="store_true")
    a.set_defaults(func=cmd_check)

    a = sub.add_parser("index", help="list what the database currently holds")
    a.add_argument("--version")
    a.add_argument("--db")
    a.add_argument("--path", help="Rack Presets folder, for --stale")
    a.add_argument("--stale", action="store_true",
                   help="instead list indexed entries whose file is gone")
    a.add_argument("--limit", type=int, default=50)
    a.set_defaults(func=cmd_index)

    a = sub.add_parser("dupes", help="find presets that are copies of each other")
    a.add_argument("--path", help="Rack Presets folder (default: newest install)")
    a.add_argument("--version", help="pick the folder of this Guitar Rig version, e.g. 7")
    a.add_argument("--include-renamed", action="store_true",
                   help="also collapse groups whose rack matches but whose name or author differs")
    a.add_argument("--apply", action="store_true", help="delete (default is a dry run)")
    a.add_argument("--json", action="store_true")
    a.set_defaults(func=cmd_dupes)

    a = sub.add_parser("assets", help="report external audio (impulse responses, backing tracks)")
    a.add_argument("--path", help="Rack Presets folder (default: newest install)")
    a.add_argument("--version", help="pick the folder of this Guitar Rig version, e.g. 7")
    a.add_argument("--verbose", action="store_true", help="list every missing backing track")
    a.add_argument("--json", action="store_true")
    a.set_defaults(func=cmd_assets)

    a = sub.add_parser("rename", help="rename presets, file and internal name together")
    a.add_argument("preset", nargs="?", help="one preset; omit for a bulk --replace")
    a.add_argument("--to", help="the new name, with a single preset")
    a.add_argument("--replace", metavar='"OLD=NEW"',
                   help="substring substitution over a whole folder, e.g. \"FUINK=FUNK\"")
    a.add_argument("--path", help="Rack Presets folder (default: newest install)")
    a.add_argument("--version", help="pick the folder of this Guitar Rig version, e.g. 7")
    a.add_argument("--apply", action="store_true", help="write changes (default is a dry run)")
    a.add_argument("--backup", action="store_true", help="keep a .bak beside each edited file")
    a.set_defaults(func=cmd_rename)

    a = sub.add_parser("fix", help="make file names and internal names agree")
    a.add_argument("--path", help="Rack Presets folder (default: newest install)")
    a.add_argument("--version", help="pick the folder of this Guitar Rig version, e.g. 7")
    a.add_argument("--mode", choices=("name", "rename"), default="name",
                   help="name: rewrite the preset's internal name (default). "
                        "rename: rename the file instead")
    a.add_argument("--only", help="only files whose name contains this text")
    a.add_argument("--strip", metavar=".ksd",
                   help="first drop this trailing text from the file name "
                        "(packs that ship 'Tone.ksd.ngrr')")
    a.add_argument("--apply", action="store_true", help="write changes (default is a dry run)")
    a.add_argument("--backup", action="store_true", help="keep a .bak beside each edited file")
    a.set_defaults(func=cmd_fix)

    args = ap.parse_args()
    try:
        args.func(args)
    except LibraryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
