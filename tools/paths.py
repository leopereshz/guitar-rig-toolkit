"""Locate Guitar Rig's preset folders and database on this machine.

Nothing here is hardcoded to a particular user or install. Every function returns only
paths that actually exist, and every caller accepts an explicit override so the discovery
can be bypassed entirely.

Layouts covered:

    Windows   presets  %USERPROFILE%\\Documents\\Native Instruments\\...
              database %LOCALAPPDATA%\\Native Instruments\\Guitar Rig <n>\\Database
    macOS     presets  ~/Documents/Native Instruments/...
              database ~/Library/Application Support/Native Instruments/Guitar Rig <n>/Database

The version number is globbed rather than assumed, so Guitar Rig 5, 6 and any later
release are all picked up.
"""

from __future__ import annotations

import glob
import os
import sys

# Subfolders of "Native Instruments" that hold presets, newest layout first.
PRESET_SUBDIRS = (
    os.path.join("User Content", "Guitar Rig *"),
    "Guitar Rig *",
)


def _documents() -> str:
    return os.path.join(os.path.expanduser("~"), "Documents")


def _ni_root() -> str:
    return os.path.join(_documents(), "Native Instruments")


def preset_roots(extra: list[str] | None = None) -> list[str]:
    """Directories that may contain .ngrr presets. Only existing paths are returned."""
    roots: list[str] = []
    ni = _ni_root()
    if os.path.isdir(ni):
        for pattern in PRESET_SUBDIRS:
            roots.extend(sorted(glob.glob(os.path.join(ni, pattern))))

    for p in extra or []:
        roots.append(os.path.abspath(os.path.expanduser(p)))

    # de-duplicate while preserving order, drop non-directories and nested duplicates
    seen: list[str] = []
    for r in roots:
        if not os.path.isdir(r):
            continue
        norm = os.path.normcase(os.path.abspath(r))
        if any(norm == os.path.normcase(s) for s in seen):
            continue
        seen.append(r)
    return seen


def _app_support_roots() -> list[str]:
    """Per-platform base directories holding Guitar Rig's application data."""
    home = os.path.expanduser("~")
    if sys.platform == "darwin":
        return [os.path.join(home, "Library", "Application Support", "Native Instruments")]
    if os.name == "nt":
        bases = [os.environ.get("LOCALAPPDATA"), os.environ.get("APPDATA")]
        return [os.path.join(b, "Native Instruments") for b in bases if b]
    return [os.path.join(home, ".native-instruments")]


def version_of(path: str) -> float:
    """Trailing version number of a 'Guitar Rig <n>' path component, for sorting."""
    for part in reversed(path.split(os.sep)):
        if part.startswith("Guitar Rig "):
            try:
                return float(part[len("Guitar Rig "):].strip())
            except ValueError:
                return 0.0
    return 0.0


def database_dirs() -> list[str]:
    """Guitar Rig's Database folders (gr<n>db, User.kad), newest version first."""
    out = []
    for base in _app_support_roots():
        out.extend(glob.glob(os.path.join(base, "Guitar Rig *", "Database")))
    out = [d for d in out if os.path.isdir(d)]
    return sorted(out, key=version_of, reverse=True)


def find_kad(explicit: str | None = None) -> str | None:
    """Path to User.kad, the component taxonomy Guitar Rig ships with its database."""
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    for d in database_dirs():
        p = os.path.join(d, "User.kad")
        if os.path.isfile(p):
            return p
    return None


def find_presets(roots: list[str] | None = None, extra: list[str] | None = None) -> list[str]:
    """Every .ngrr under the given (or discovered) roots, sorted and de-duplicated."""
    search = roots if roots else preset_roots(extra)
    files: list[str] = []
    for root in search:
        files.extend(glob.glob(os.path.join(root, "**", "*.ngrr"), recursive=True))
    seen, out = set(), []
    for f in sorted(files):
        key = os.path.normcase(os.path.abspath(f))
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


def describe() -> str:
    """Human-readable summary of what discovery found. Used by --where."""
    lines = [f"platform: {sys.platform}", "", "preset roots:"]
    roots = preset_roots()
    lines += [f"  {r}" for r in roots] or ["  (nenhum encontrado / none found)"]
    lines += ["", "database dirs:"]
    dbs = database_dirs()
    lines += [f"  {d}" for d in dbs] or ["  (nenhum encontrado / none found)"]
    kad = find_kad()
    lines += ["", f"User.kad: {kad or '(nao encontrado / not found)'}"]
    lines += ["", f"presets encontrados / presets found: {len(find_presets(roots))}"]
    return "\n".join(lines)


if __name__ == "__main__":
    print(describe())
