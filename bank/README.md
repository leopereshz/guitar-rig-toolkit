# Preset bank

Starting points for people who own no presets yet.

Guitar Rig ships factory content, but a fresh install gives the toolkit almost nothing to
work from: `rackbuild.py` can only place components it has seen in a preset, and `scan.py`
can only learn parameter ranges from presets that exist. Someone installing the plugin on a
clean machine would be told to go research gear and dial everything by ear. This bank is the
answer to that.

## What goes in here

**Only presets whose author is contributing them.** Each entry records who made it, and by
adding one you are stating it is your own work, released under this repository's MIT licence.

That rule is not decoration. Preset packs circulate widely and are easy to harvest, but the
parameter values in a preset are its creative content — extracting them into JSON is
redistribution with an extra step, no matter what the entry is called. Free download does not
waive copyright either; a pack posted on a forum is public in the same sense a photograph
posted online is public.

So: dial it yourself, or build it from documented gear with `references/ARTIST-TONE.md` and
`tools/gearmap.json`, then contribute that.

## Why authored beats harvested anyway

A bank written by a handful of people who each check their work is more coherent than one
scraped from thirty strangers. Entries end up calibrated on comparable monitoring, with a
consistent macro layout, and with notes explaining what each one is for. A scraped bank is a
patchwork where every entry assumes a different guitar, interface and room.

## Naming and artist references

Describing what gear a tone is built on is a statement of fact. Implying an official or
endorsed preset is not.

- Good: `"reference": "Hiwatt-style clean stack with a Big Muff in front, as documented for
  late-70s Pink Floyd live rigs"`
- Good: `"name": "Muff Into Clean Stack"`
- Avoid: naming an entry as if it were an artist's actual patch, or claiming it reproduces a
  specific recording

The `reference` field exists precisely so the gear reasoning is visible and the claim stays
honest.

## Entry format

One JSON file per entry under `entries/`, so contributions never collide. Required fields are
`id`, `name`, `author`, `chain`. See any existing entry, or:

```bash
python tools/bank.py schema
```

## Using the bank

```bash
python tools/bank.py list
```

```bash
python tools/bank.py show british-crunch
```

```bash
python tools/bank.py apply british-crunch --into "<indexed preset.ngrr>" --backup
```

`apply` builds the chain, sets every value and assigns the macros in one step. The target has
to be a preset Guitar Rig already indexed — see the README's note on why.

## Contributing an entry

```bash
python tools/bank.py add "<your preset.ngrr>" --id my-tone --name "My Tone" --author "Your Name"
```

That reads the preset you dialled, writes the entry, and prints what it captured. Fill in
`reference` and `notes` by hand — they are what make the entry useful to someone who has never
heard it. Then:

```bash
python tools/bank.py validate
```

Every component and parameter has to resolve against `tools/components.json`, and `apply` only
works for components that can actually be placed, so `validate` reports both.
