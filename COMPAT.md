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
| Guitar Rig 7 | NISH | `…hsin` | in place only — same rule as Guitar Rig 6 |

Guitar Rig 6 **reads** both containers. Verified: a Guitar Rig 5 preset was edited through
the full recompression path (file grew 6033 → 6056 bytes, so the container's length headers
had to be rewritten) and Guitar Rig 6.2.0 loaded it with its 18-component chain intact.

Guitar Rig 7 **reads** both containers too: 537 Guitar Rig 4/5 SoundShell presets were
indexed and loaded by GR 7.0.2 with no conversion step.

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

Measured on **Guitar Rig 7.0.2 (x64)**, Windows, installed alongside 5 and 6.

| | GR6 (real install) | GR7 (real install) |
|---|---|---|
| `User.kad` components | 122 | 138 |
| categories | 15 | 15 |
| components removed | — | 0 |
| database file | `Database/gr6db` | `Database/gr7db`, same `JL` header |

**The 16 new components are confirmed**, and they are exactly the 16 the manual listed:
AC Box XV, Bass Rage, Cabinet IR Loader, Chainsaw, Fire Seeker, Ivp Stomp, Kolor,
Maximizer, Noise Machine, Red Fuzz, Reverb Delight, Seattle Fuzz, Skreamer Deluxe,
Super Fast 100, Tape Wobble, Vintage Vibrato. Nothing from the GR6 catalog disappeared.

**The renames the manual shows are display names only.** `User.kad` in Guitar Rig 7 still
says `Wahwah`, `Demon`, `MeZone`, `EQ Graphic`, `Phaser Nine`, `Volume Pedal`, `Flanger`
and `Traktor Delay` — the spellings the manual gives as `Wah Wah`, `Demon Distortion` and
so on do not appear in the catalog or in preset XML. A GR6-scanned dictionary therefore
matches a GR7 install by name as well as by id. The alias machinery in `scan.py` stays
because it costs nothing and the manual spellings are what users will type.

None of the 16 new components has parameter data yet: `scan.py --coverage` reports 98 of
138 components covered, and the 40 uncovered ones are the new arrivals plus components no
preset in the sample happens to use. Parameters are learned from presets, so building a
rack with a new component in GR7 and saving it is what fills those in.

### Reading and editing

537 Guitar Rig 4/5 presets copied into `User Content/Guitar Rig 7/Rack Presets` all parse,
and `test_roundtrip.py` rebuilds 1132 of 1133 discovered presets byte-for-byte (the one
exception is the single NISH file, which is skipped by design). Guitar Rig 7 loads
SoundShell files directly — no conversion step.

**Guitar Rig 7 writes NISH**, the same container as Guitar Rig 6. A preset saved from
inside GR 7.0.2 reads back as:

```
container  : nish  (width-preserving edits only: True)
written by : Guitar Rig 7.0.2 build 0
```

So the width-preserving rule applies to GR7-saved presets exactly as it does to GR6 ones,
and `rackbuild.py --replace-container` is still how a different chain gets installed over
such a slot. No code changed to read it: the container is chosen by magic bytes.

Its rack header carries the same five attributes GR6 writes — `build-number`,
`major-version`, `minor-version`, `micro-version`, `time` — and none of the four GR4/GR5
pack attributes came back. One oddity: GR7 writes `build-number="0"` where GR6 wrote a real
build number, so read the version from `major/minor/micro` and treat the build as unreliable.

Note for name matching: the internal Loop Machine component is called **Loop Machine Pro**
in GR7 (`id=53000`, unchanged). Ids stay stable across versions; names do not, which is why
nothing in the toolkit keys off a component name alone.

### External audio

Two components reference a file outside the preset, and only one of them is fragile.

| component | element | what is stored | survives a move |
|---|---|---|---|
| Reflektor | `convolutionreverb` | base64 samples in `channel0`/`channel1`, plus the source `filename` | ✅ the audio travels inside the preset |
| Tapedeck | `tapedeckbase` | a path, nothing else | ❌ but it is only the practice backing track |

Measured over 12 Reflektor slots in 11 presets: all 12 decoded to exactly
`numsamples × numchannels × 4` bytes, and 0 of the 12 `filename` paths existed on the
machine — they pointed into other people's `Downloads` and `Impulses` folders. The presets
play their IRs regardless. `library.py assets` checks the byte count rather than the path,
which is the only test that distinguishes a lost IR from a stale path.

### The library scan

This is the part that bites hardest in practice and it is not version-specific — see
`python library.py check`. Guitar Rig indexes a preset under the `<name>` stored *inside*
the file and then resolves that entry back to `<name>.ngrr` on disk. Copying a pack whose
files are named `Artist - Song.ngrr` while the soundinfo still says `Song` leaves every
entry unresolvable, and the scan drops them without a word.

Measured on this install: of 537 files in the GR7 folder, the **93 whose file name matched
their internal name were indexed and the other 444 were not** — the split was exact in both
directions. `library.py fix` makes the two names agree again.

## What this means per version

| you have | read presets | edit presets | catalog | dictionary |
|---|---|---|---|---|
| GR5 only | ✅ sndf | ✅ full rewrite | ❌ none | from preset scan |
| GR6 | ✅ both | ✅ sndf full, nish in place | ✅ 122 components | scan + catalog coverage |
| GR7 | ✅ both | ✅ sndf full, nish in place | ✅ 138 components | scan + catalog coverage |
