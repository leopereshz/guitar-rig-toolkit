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

If `paths.py` finds no presets, ask where they keep them and re-run `scan.py --path <dir>`.
If `catalog.py` reports no component catalog, the install is Guitar Rig 5 — that version does
not ship one, and the dictionary will come from the preset scan alone. Say so rather than
treating it as an error.

Then report, in plain language:

- which Guitar Rig version was found, and where
- how many presets were scanned
- catalog coverage — how many components have parameter data, out of how many exist
- how many components can be placed in a built rack (`python tools/rackbuild.py --list | head -1`)

Finally, explain the one manual step and why it exists. Guitar Rig lists only presets its own
database indexed, and it indexes only what it saved or imported itself — a file written into
the preset folder never shows up, not even after a restart. So building new tones needs one
registered slot.

Offer the user the choice:

- **Import a ready-made one** — build a starter preset with `rackbuild.py` somewhere outside
  the Guitar Rig folders, then have them use **Main menu → File → Import…** and pick it.
  Import copies the file into their Rack Presets folder and registers it.
- **Save one themselves** — load any preset in Guitar Rig and save it as `AI Workbench`.

Both take a few seconds and only happen once. Fixing presets they already have needs neither,
so if they only want to fix existing tones, tell them setup is already complete.
