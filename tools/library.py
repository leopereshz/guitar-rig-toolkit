"""
library.py - find out why presets sitting in the Rack Presets folder never show up in
Guitar Rig's browser, and repair them.

    python library.py check [--path DIR] [--json]
    python library.py index [--version 7]
    python library.py fix   --path DIR [--mode name|rename] [--apply] [--backup]

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
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths as grpaths
from ngrr import NgrrFile, NgrrError

NAME_RE = re.compile(r"<name>(.*?)</name>", re.S)


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

def indexed_names(db_path: str) -> set[str]:
    """Preset names the Guitar Rig database currently indexes under its User bank.

    Entries are stored as the key `GR<n>://RackPreset/User/<name>` followed by the same
    name again as the display string. Neither is length-prefixed in a way that has been
    decoded, so the name is recovered from the repetition.
    """
    m = re.search(r"Guitar Rig (\d+)", db_path)
    version = m.group(1) if m else "7"
    prefix = f"GR{version}://RackPreset/User/".encode()
    raw = open(db_path, "rb").read()

    names: set[str] = set()
    for hit in re.finditer(re.escape(prefix), raw):
        i = hit.end()
        j = i
        while j < len(raw) and raw[j] >= 0x20 and raw[j] != 0x7F:
            j += 1
        run = raw[i:j]
        cut = run.find(b"GR")
        if cut > 0 and run[cut:cut + 6].decode("latin-1", "ignore").startswith("GR"):
            maybe = run[:cut]
            if maybe:
                run = maybe
        text = run.decode("utf-8", "replace")
        if not text:
            continue
        # the record form repeats the name; the reference form does not
        half = len(text) // 2
        if half and text[:half] == text[half:half * 2]:
            names.add(text[:half])
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
    names = sorted(n for n in indexed_names(db_path) if n)
    print(f"database: {db_path}")
    print(f"user presets indexed: {len(names)}")
    for n in names[:args.limit]:
        print("  ", n)
    if len(names) > args.limit:
        print(f"  ... and {len(names) - args.limit} more")


# --------------------------------------------------------------------------- repair

def unique_target(directory: str, stem: str, taken: set[str]) -> str:
    candidate = stem
    n = 2
    while candidate.lower() in taken:
        candidate = f"{stem} ({n})"
        n += 1
    taken.add(candidate.lower())
    return candidate


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
    a.add_argument("--limit", type=int, default=50)
    a.set_defaults(func=cmd_index)

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
