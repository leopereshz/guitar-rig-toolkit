# Version compatibility

Everything here was measured on real files, not inferred from documentation. Where a claim
is untested it says so.

Sample: 350 presets — 5 written by Guitar Rig 4, 343 by Guitar Rig 5, 2 by Guitar Rig 6.

## The short version

The tool keys off **file content**, never off a version number. Container format is decided
by magic bytes, parameters are found by walking the XML, and edits only rewrite the
`value="…"` attribute that was asked for. That is why reading and editing work across
versions without per-version code paths.

Version only matters in two places: which container a version can *write*, and whether a
version ships a component catalog.

## Container format

| written by | container | magic | rewritable |
|---|---|---|---|
| Guitar Rig 4 | SoundShell / zlib | `-in-` | fully — chunks carry their own lengths |
| Guitar Rig 5 | SoundShell / zlib | `-in-` | fully |
| Guitar Rig 6 | NISH | `…hsin` | in place only — values must keep their exact character width |
| Guitar Rig 7 | untested | — | see below |

Guitar Rig 6 **reads** both containers. Verified: a Guitar Rig 5 preset was edited through
the full recompression path (file grew 6033 → 6056 bytes, so the container's length headers
had to be rewritten) and Guitar Rig 6.2.0 loaded it with its 18-component chain intact.

Guitar Rig 5 reading a NISH file is **untested and unlikely** — NISH postdates it. Treat
Guitar Rig 5 as write-target `sndf` only.

Why NISH is restricted to width-preserving edits: its rack XML is stored uncompressed
inside nested length-prefixed records, and those nested lengths were not fully decoded.
Keeping the byte count identical sidesteps them entirely. In practice this is not much of a
limit — Guitar Rig writes continuous controls as `%.6f` (`0.500000`), which has room for any
0.0–1.0 value. Switches stored as `"0"`/`"1"` can only be set to `0` or `1`.

## Header attributes by version

`<gr-instrument-chunk>` lost four attributes in Guitar Rig 6:

| attribute | GR4 | GR5 | GR6 |
|---|---|---|---|
| `build-number`, `major/minor/micro-version`, `time` | ✅ 5/5 | ✅ 343/343 | ✅ 2/2 |
| `component-pack-id` | ✅ 5/5 | ✅ 338/343 | ❌ |
| `preset-pack-id` | ✅ 5/5 | ✅ 338/343 | ❌ |
| `framework-id` | ✅ 5/5 | ✅ 338/343 | ❌ |
| `sound-database/hires-mode` | ✅ 5/5 | ✅ 332/343 | ❌ |

Note the variation *within* Guitar Rig 5: 5 of 343 files omit the pack ids and 11 omit
`hires-mode`, depending on the build that wrote them (builds seen: 2447, 2476, 2641, 2673).
So even a single major version is not a single schema. Read leniently.

This matters only when **synthesising** a preset from scratch, which the tool does not do
yet. Editing never touches these attributes.

## Component catalog

`Database/User.kad` is where Guitar Rig lists the components it knows about.

| version | `CP://` component sets | `RP://` preset tag sets | catalog usable |
|---|---|---|---|
| Guitar Rig 5 | 0 populated | 26 | ❌ |
| Guitar Rig 6 | 140 populated | 23 | ✅ 122 components, 15 categories |

Guitar Rig 5's `User.kad` declares the `CP://` sets but leaves them empty — it carries only
the preset tag taxonomy. **A Guitar Rig 5-only install produces no catalog**, and the
dictionary must come from a preset scan alone. `catalog.py` reports this rather than
failing silently.

`catalog.json` records a `since` field per component, so the catalog can say which version
first provided a given component when more than one version is installed.

## Guitar Rig 7

Not installed here, so nothing about its **file format** is verified. Its **component set**
is now documented, though, from Native Instruments' own manual — see `docs-index.json` and
`python query.py docs`.

| | GR6 (read from a real install) | GR7 (from the manual) |
|---|---|---|
| components | 122 | 131 |

**16 components are new in Guitar Rig 7:** AC BOX XV, Bass Rage, Cabinet IR Loader, Chainsaw,
Fire Seeker, IVP Stomp, Kolor, Maximizer, Noise Machine, Red Fuzz, Reverb Delight,
Seattle Fuzz, Skreamer Deluxe, Super Fast 100, Tape Wobble, Vintage Vibrato.

**Around 25 components were renamed**, which matters more than the additions: a dictionary
scanned from Guitar Rig 6 presets will not match a Guitar Rig 7 catalog by name alone.
`Demon` → `Demon Distortion`, `MeZone` → `Mezone`, `EQ Graphic` → `Equalizer Graphic`,
`Phaser Nine` → `Phaser 9`, `Volume Pedal` → `Volume`, `Wahwah` → `Wah Wah`,
`Flanger` → `Flanger Chorus`, and every Traktor-derived effect gained a possessive
(`Traktor Delay` → `Traktor's Delay`). The full map is in `docs-index.json` under
`gr7_component_names.renamed_since_gr6`. This is why `scan.py` records `aliases` per
component id and matches on all of them — the id is stable, the name is not.

Seven components in the GR6 catalog are absent from the GR7 components reference — Analog
Sequencer, Container, Envelope, Global FX, Input Level, LFO, Step Sequencer. They were not
removed: the reference page covers signal processors only, and those live under the manual's
Modifiers, Tools Components and Rack Tools sections instead.

What is still unverified: which container Guitar Rig 7 writes, whether its `User.kad` keeps
the `CP://` catalog, and whether the `<gr-instrument-chunk>` header changed again. The design
degrades in a defined way:

- `paths.py` globs `Guitar Rig *`, so a GR7 install is discovered with no code change, and
  `database_dirs()` sorts newest-first so GR7 would take precedence.
- Container handling is by magic bytes. If GR7 writes NISH, editing works immediately. If it
  introduces a third container, `NgrrFile.parse` raises a clear error naming the unknown
  magic rather than corrupting anything.
- `catalog.py` parses whatever `CP://` sets it finds. A GR7 catalog with new components is
  picked up automatically and merged, with `since: "7"`.

If you have Guitar Rig 7, running `python paths.py`, `python catalog.py` and
`python test_roundtrip.py` and reporting the output is the single most useful contribution —
it turns this section from prediction into measurement.

## What this means per version

| you have | read presets | edit presets | catalog | dictionary |
|---|---|---|---|---|
| GR5 only | ✅ sndf | ✅ full rewrite | ❌ none | from preset scan |
| GR6 | ✅ both | ✅ sndf full, nish in place | ✅ 122 components | scan + catalog coverage |
| GR7 | expected ✅ | expected ✅ | expected ✅ | untested |
