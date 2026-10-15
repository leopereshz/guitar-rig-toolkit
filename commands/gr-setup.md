---
description: Set up the Guitar Rig toolkit — find the install, read the component catalog, and learn parameters from your presets
---

Set up the Guitar Rig toolkit on this machine. The parameter dictionary is built from the
presets the user actually owns, so this has to run once before any advice is grounded in
something real rather than guessed.

Run these from the plugin root, in order, and report what each one finds:

```bash
python tools/paths.py
```

```bash
python tools/catalog.py
```

```bash
python tools/scan.py
```

```bash
python tools/library.py check
```

If `paths.py` finds no presets, ask where they keep them and re-run `scan.py --path <dir>`.
If `catalog.py` reports no component catalog, the install is Guitar Rig 5 — that version does
not ship one, and the dictionary will come from the preset scan alone. Say so rather than
treating it as an error.

Then report, in plain language:

- which Guitar Rig version was found, and where
- how many presets were scanned
- catalog coverage — how many components have parameter data, out of how many exist
- how many components can be placed in a built rack (`python tools/rackbuild.py --list | head -1`)
- whether `library.py check` found presets the Guitar Rig browser will not show

If `library.py check` reports mismatches, say so immediately — those presets are on disk but
invisible in Guitar Rig, and the user has probably already noticed and not known why. Explain
that the scan indexes a preset under the name stored inside the file and then looks for a
file of that name, so a pack renamed to `Artist - Song.ngrr` cannot be resolved. Offer the
repair, which keeps the descriptive file names:

```bash
python tools/library.py fix --backup --apply
```

Then they run **File → Preferences → Library → Scan** again. Do not run `fix --apply` without
asking: it edits their files, and the choice between rewriting the internal name and renaming
the file is theirs to make.

Finally, explain the one manual step and why it exists. Guitar Rig lists only presets its own
database indexed; it does not watch its preset folder, so a file written there shows up only
after an import, a save from inside Guitar Rig, or a Library Scan. Building new tones needs
one registered slot.

Offer the user the choice:

- **Import a ready-made one** — build a starter preset with `rackbuild.py` somewhere outside
  the Guitar Rig folders, then have them use **Main menu → File → Import…** and pick it.
  Import copies the file into their Rack Presets folder and registers it.
- **Save one themselves** — load any preset in Guitar Rig and save it as `AI Workbench`.

Both take a few seconds and only happen once. Fixing presets they already have needs neither,
so if they only want to fix existing tones, tell them setup is already complete.
