---
name: Guitar Rig 7 report
about: Fill the last gaps in the GR7 section of COMPAT.md
title: "GR7: "
labels: compatibility, data
---

Guitar Rig 7.0.2 has now been measured on Windows: the catalog holds 138 components, the 16
additions the manual lists are confirmed, nothing was removed, the renames in the manual are
display names only, GR7 writes the same NISH container as GR6 with the same five header
attributes, and 537 Guitar Rig 4/5 presets parse and rebuild byte-for-byte. See `COMPAT.md`.

One thing is still open on Windows, plus macOS in general.

## Parameters for the 16 new components

`scan.py --coverage` reports 98 of 138 components with parameter data. The 16 GR7 additions
have none, because parameters are learned from presets and no preset in the sample uses them.

Build a rack in GR7 containing any of AC Box XV, Bass Rage, Cabinet IR Loader, Chainsaw,
Fire Seeker, Ivp Stomp, Kolor, Maximizer, Noise Machine, Red Fuzz, Reverb Delight,
Seattle Fuzz, Skreamer Deluxe, Super Fast 100, Tape Wobble or Vintage Vibrato, save it, then:

```
$ python tools/scan.py --path "<folder with that preset>"

```

and attach the resulting `components.json` diff. No preset file is needed and none should be
attached — the dictionary is the contribution.

## macOS

Everything above was measured on Windows. `paths.py` has macOS branches that have never run
against a real install, so its output on a Mac is also useful:

```
$ python tools/paths.py

```
