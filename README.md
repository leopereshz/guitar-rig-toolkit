# guitar-rig-toolkit

Read and edit Native Instruments Guitar Rig presets (`.ngrr`) from Python, plus a
component/parameter dictionary you build from the presets you own.

Nothing here is official and there is no affiliation with Native Instruments; Guitar Rig is
their trademark. The formats were reverse-engineered from real preset files, and the tests
below are the evidence that the parser and writer are correct.

## Install as a Claude Code plugin

The whole point is to stop typing commands and start describing the sound.

```bash
/plugin marketplace add leopereshz/guitar-rig-toolkit
```

```bash
/plugin install guitar-rig-toolkit
```

```bash
/gr-setup
```

After that, say what is wrong — "it's muffled", "tá chiando", "suena apagado" — and the skill
diagnoses it and edits the preset. `/gr-fix <complaint>` does the same explicitly. Requires
Python 3; the tools have no third-party dependencies.

## Layout

```
.claude-plugin/     plugin and marketplace manifests
skills/guitar-rig/  SKILL.md and the reference documents it reads
commands/           /gr-setup and /gr-fix
tools/              the Python that does the file work
bank/               authored preset starting points, contributed as JSON
evals/              trigger calibration for the skill description
```

The symptom references under `skills/guitar-rig/references/` are generated —
edit `tools/sintomas.json` and `tools/i18n/*.json`, then run `python tools/build_docs.py`.

## Files

| file | what it is |
|---|---|
| `tools/ngrr.py` | container reader/writer for the SoundShell/zlib `.ngrr` format |
| `tools/grpreset.py` | CLI: `info`, `dump`, `set`, `rename` — works on both container formats |
| `tools/paths.py` | cross-platform discovery of preset folders and the Guitar Rig database |
| `tools/library.py` | `check`, `index`, `fix`, `rename`, `import`, `dupes`, `assets` — the library and what is in it |
| `tools/catalog.py` | extracts Guitar Rig's own component catalog from `User.kad`, across versions |
| `tools/catalog.json` | 138 components in 15 categories, with the version each first appeared in |
| `tools/scan.py` | builds/extends the parameter dictionary by scanning presets |
| `tools/rackbuild.py` | composes a rack from harvested component blocks |
| `tools/macros.py` | assigns Guitar Rig's 16 macro controls to rack parameters |
| `tools/query.py` | point queries against the dictionary and catalog, for tools and LLMs |
| `tools/components.json` | the dictionary: component id → parameters → ranges and observed values |
| `COMPONENTS.md` | the same dictionary as a readable reference table |
| `tools/schema.txt` | every distinct XML element path seen in the rack documents |
| `COMPAT.md` | measured version-compatibility matrix (GR4/5/6/7) |
| `skills/guitar-rig/references/SINTOMAS.md` and its en/es/fr siblings | the symptom reference, generated per language |
| `tools/sintomas.json` | the decision tree, machine-readable and language-neutral |
| `tools/i18n/*.json` | every translatable string, one catalog per language |
| `tools/build_docs.py` | renders the symptom reference from structure + catalog |
| `tools/validate_sintomas.py` | checks component/parameter references and catalog key parity |
| `tools/gearmap.json` | what real-world gear each Guitar Rig component models |
| `skills/guitar-rig/references/ARTIST-TONE.md` | how to chase an artist or song tone — a method, not a database |
| `tools/docs-index.json` | index of the official Guitar Rig manual: which page answers which question |
| `tools/test_roundtrip.py` | parses every preset found and rebuilds it byte-for-byte |
| `tools/test_fixture.py` | self-contained tests on a synthetic preset; needs no preset files |
| `tools/bank.py` | the preset bank: list, show, add, apply, validate |
| `tools/topology.py` | learns wiring conventions from a corpus: what follows what, where each category sits |
| `tools/topology.json` | the learned conventions — structure only, no parameter values |
| `bank/entries/*.json` | authored starting points — chain, values and macros, one file each |

## Quick start

Nothing is hardcoded to a particular machine — preset folders and the Guitar Rig database
are discovered per platform. Check what was found:

```bash
python tools/paths.py
```

Then build the two knowledge layers:

```bash
python tools/catalog.py
```

```bash
python tools/scan.py --path "/wherever/you/keep/presets"
```

`catalog.py` reads Guitar Rig's own component list, so it is the same for everyone with the
same version. `scan.py` learns parameter ids and value ranges from presets, so it only knows
components your presets actually use — it **merges** by default, and reports how much of the
catalog it now covers.

## The two container formats

See `COMPAT.md` for the full version matrix. In short:

**SoundShell / zlib** — written by Guitar Rig 4 and 5, still read by 6.

```
"-in-" u32ver "#NI#CS#Document##NI#SoundShell#Sound#" pad u32const
chunk*  ->  "atad" u32ver name4 "bilz" u32comp u32orig  <zlib stream>
```

Chunk names are reversed 4CCs: `dnss`/`DNSS` are 16-byte open/close sentinels, `ofni` holds
the `<soundinfo>` metadata XML, `tsrp` holds `" LMX" u32ver u32len` followed by the
`<gr-instrument-chunk>` rack XML. Every length lives in its own chunk header, so this format
can be rewritten freely — payloads may grow or shrink.

**NISH** — written by Guitar Rig 6.

```
u32 filesize ... "hsin" ... nested "DSIN" records with u64/u32 length prefixes
```

The rack XML is stored **uncompressed** inside that nesting. The nested lengths were not
fully decoded, so edits here preserve the exact character width of each value and never
touch a length field. Guitar Rig writes continuous controls as `%.6f` (`0.500000`), which
has room for any 0.0–1.0 value; switches stored as `"0"`/`"1"` accept only `0` or `1`.

## Verification status

```
$ python test_roundtrip.py --path "D:/Downloads/Guitar Rig 5"
files scanned      : 351
SoundShell/zlib    : 350
  byte-exact rebuild : 350
  recompress + reload: 350
  failed             : 0
GR6 native (NISH)  : 1  (skipped, edited in place by grpreset.py)
```

Every SoundShell preset parses, rebuilds to identical bytes, and survives a
decompress/recompress cycle with identical payloads.

**Both container formats were confirmed to load in Guitar Rig 6.2.0 (build 135):**

| format | write path | result |
|---|---|---|
| NISH | width-preserving, 12 bytes changed, file size unchanged | loaded; the 12 edited macro values matched what was written, and the 4 untouched macros stayed put |
| SoundShell | full recompression, file grew 6033 → 6056 bytes | loaded with the complete 18-component chain intact; the edited amp came back bypassed with its knobs at the written extremes, while a second amp in the same rack was untouched |

The SoundShell case is the stronger result: recompressing the preset chunk changes its
length, so the container's length headers must be rewritten correctly or Guitar Rig cannot
parse the file at all.

Back up before editing presets you care about — copy to `.bak`, verify, then commit to it.

### Guitar Rig does not rescan the preset folder

Guitar Rig lists presets from its own index (`Database/gr<n>db`), not from the filesystem.
A newly created `.ngrr` will **not** appear in the browser, even after a restart, until
Guitar Rig reindexes.

Measured: writing a new `.ngrr` into the preset folder left `gr6db` byte-for-byte
unchanged, and the preset never appeared — not on a rescan, not after a restart. Dropping a
file in is not enough.

**Guitar Rig's own Import is the way in, and it works.** Main menu → File → Import…, pick the
file, Open. Verified in Guitar Rig 6.2.0 with a preset built by `rackbuild.py` and left
outside every Guitar Rig folder: it appeared in the browser immediately, the five-component
chain and all six macro labels intact. Import **copies** the file into
`User Content/Guitar Rig <n>/Rack Presets/` and registers it — after which that copy, not the
original, is the file to keep editing.

So a tool-built preset can be delivered to a user without asking them to recreate it by hand;
they import it once and it is theirs from then on.

**Reloading, on the other hand, is cheap.** Guitar Rig caches the preset it has loaded, so a
single click on the preset that is already current does nothing. **Double-clicking it
re-reads the file from disk** — an edited preset picks up its new values immediately, with
no restart. That is the fast way to iterate.

### Presets that are in the folder but not in the browser

Copying a pack into `User Content/Guitar Rig <n>/Rack Presets/` and running
**File → Preferences → Library → Scan** imports some presets and silently drops others.
There is no error and no log entry.

The reason: the scan indexes a preset under the `<name>` stored *inside* the file — in the
soundinfo document, not the file name — and then resolves that entry back to `<name>.ngrr`
on disk. Packs that ship as `Artist - Song.ngrr` while the soundinfo still says `Song` fail
that lookup, and the entry is thrown away.

Measured on a Guitar Rig 7.0.2 install: 537 files copied in, **93 indexed and 444 not**,
and the 93 were exactly the files whose name matched their internal name. The correlation
held in both directions, with no exceptions.

```bash
python tools/library.py check --version 7
```

```
presets  : 538
  file name matches internal name : 93
  mismatched (will not be indexed): 445
  currently in the database       : 103
```

```bash
python tools/library.py fix --version 7 --backup --apply
```

`fix` rewrites each file's internal name to its file name, so the browser shows
`Guns n Roses - Dont cry` rather than `Dont cry`. The rack is not touched — only the
`<name>` element of the soundinfo chunk changes. Run the Scan again afterwards.

Two options worth knowing:

- `--mode rename` renames the file to the internal name instead of editing the file. This
  is the only option for presets saved by Guitar Rig 6 or later, whose NISH container
  cannot have its metadata resized in place; `fix` detects those and says so.
- `--strip ".ksd"` first drops a stray second extension from file names, so
  `Blues Rock - Tweed Club.ksd.ngrr` becomes `Blues Rock - Tweed Club.ngrr` before the name
  is written.

`library.py index` prints what the database currently holds, which is the way to confirm a
scan did what you expected.

Renaming a preset afterwards would put it straight back into the broken state, so do it
with `rename`, which moves the file and rewrites the internal name in one step:

```bash
python tools/library.py rename --version 7 --replace "FUINK=FUNK" --apply
```

```bash
python tools/library.py rename "Old Name.ngrr" --to "Better Name" --apply
```

Both default to a dry run.

**The Scan only adds.** It never removes an entry whose file is gone, so a renamed or
deleted preset keeps its old row in the browser and that row fails to load. Measured by
renaming six presets and rescanning: the six new names were added and the six old ones
stayed. Guitar Rig owns its database and nothing here writes to it, so the cleanup is a
right-click → delete in the browser. To see which rows need it:

```bash
python tools/library.py index --version 7 --stale
```

### Bringing a folder of downloads in

Three things have to happen together, and in the wrong order the work is wasted: drop
what the library already has, drop the copies inside the batch itself, and make each
survivor's internal name match its file name so the Scan can index it.

```bash
python tools/library.py import "D:\Downloads\Top10p1" --version 7
```

```
presets in the batch        : 30
  already in the library    : 4
  copies inside the batch   : 0
  unreadable                : 0
  new to this library       : 26
```

"Already in the library" is decided on the rack, not the file name, so a download called
`moneyf.ngrr` is recognised as the `moneyfornoth.ngrr` already sitting there. Within the
batch, the copy that survives is chosen by the same ranking `dupes` uses, so it does not
depend on the order the filesystem happened to list the files in.

A file name already taken by a **different** rack is left alone by default, because on
Windows the match ignores case and `Back in Black.ngrr` would land on top of
`Back in black.ngrr`. `--on-clash suffix` keeps both by appending the first free number:

```
  ACDC - Back in Black.ngrr
     file name taken, saved as ACDC - Back in Black 2.ngrr; name 'ACDC Back in' -> 'ACDC - Back in Black 2'
```

The source folder is never modified. `--apply` copies; without it you get the list.

### The same preset extracted twice

A collection assembled from several downloads ends up with the same rack under
`Nighttrain.ngrr`, `Nighttrain (2).ngrr` and `Nighttrain 1.ngrr`. Comparing the files
byte for byte finds nothing, because each copy carries its own component uuids, its own
build stamp, its own position in whoever's browser it came from, and its own window
state. None of that changes the sound.

```bash
python tools/library.py dupes --version 7
```

The fingerprint is the rack with that bookkeeping removed: uuids, the
`<gr-instrument-chunk>` stamp, the Tapedeck path, `<preset-ordering>`, `<view>`, and the
order automation numbers happen to be serialised in. Measured on a 547-preset collection:
24 groups of genuine copies, 29 files removable.

The hash is not trusted on its own. Before a group is offered for deletion its members
are compared again as structure — the ordered chain of components, and every parameter
value of every component, read from the parsed rack — and any group where the two methods
disagree is reported as a bug and left alone. The dry run prints what was compared:

```
  Skreamer > Twang Reverb > Quad Delay > Cabinets & Mics > CabPanel > Studio Reverb > Loop Machine
  7 in the chain, 134 parameter values, identical across all 3
  KEEP Eric Johnson - 1987 (Ritmo).ngrr
  del  Eric Johnson -1988.ngrr
```

The preset's **name, author and comment are deliberately left out of the fingerprint and
compared separately**, because two copies of one rack saved under different names are not
the same thing to a person:

```
same rack, different name : 5 group(s)
  Alexi Lahio1.ngrr [Alexi Lahio] | Jimi Hendrix.ngrr [Jimi Hendrix]
  Evanescense.ngrr [(no name)] | LinkParkR.ngrr [LinkPark]
```

Those are reported and left alone unless you pass `--include-renamed`. Of the copies it
does collapse, it keeps the one that credits an author, then the one with a comment, then
the name without a `(2)` or trailing number, and then the **longer** name — the extra
length is almost always the band or song someone added to make the preset findable.

`--apply` deletes; without it you get the list. Afterwards the database still lists the
deleted presets, so clean it from **File → Preferences → Library**.

### Impulse responses and other external audio

A preset can point at an audio file outside itself in two places, and they behave very
differently when the collection moves to another machine.

**Reflektor embeds its impulse response.** The `<convolutionreverb>` element carries the
samples as base64 in `channel0`/`channel1`, right beside the `filename` they were imported
from. The path is provenance, not a lookup — a preset whose IR came from a stranger's
`D:\Impulses\` folder still plays it here. Checked across 12 IR slots in a real
collection: every one decoded to exactly `numsamples × numchannels × 4` bytes, and not one
of the 12 original paths existed on the machine.

So copying the `.wav` files alongside the presets, or renaming them, changes nothing in
either direction. The check that matters is the byte count, not the path:

```bash
python tools/library.py assets --version 7
```

```
impulse responses (embedded in the preset) : 12
  audio intact                             : 12
  original path still resolves             : 0   (does not matter)
```

A `BAD` line there means the base64 does not match the declared sample count — that preset
really did lose its IR and it has to be reloaded by hand in Reflektor.

**Tapedeck stores a path and nothing else.** It remembers the last backing track the
preset's author had loaded, which is almost always a file on their machine. Those paths are
dead on arrival and it does not matter: Tapedeck is the practice player, not part of the
signal chain.

### Working with indexed slots

The index is the only real constraint, and there is a clean way around it that never touches
Guitar Rig's database:

1. **Once**: get one preset registered. Either build it with `rackbuild.py` anywhere and
   import it (Main menu → File → Import…), or save a placeholder from inside Guitar Rig.
   Either way this is a one-time step, and only Guitar Rig can do it.
2. **From then on**, write into that slot with `grpreset.py`, `rackbuild.py` or `macros.py`.
   Use the copy under `Rack Presets/`, which is the one Guitar Rig indexed.
3. **Double-click** the slot in Guitar Rig to load the new rack.
4. **To keep a result**, save it from inside Guitar Rig under its own name. That registers it
   properly and frees the working slot for the next idea.

Presets saved by Guitar Rig 6 or 7 use the NISH container, which only accepts width-preserving
edits — not enough to install a different chain. `rackbuild.py --replace-container` writes a
SoundShell container over that path instead. Verified in Guitar Rig 6.2.0: a NISH slot with
an empty rack (36908 bytes) was replaced with a SoundShell preset carrying a five-component
chain (4473 bytes), and Guitar Rig loaded it correctly on a double-click.

Injecting an entry into `gr6db` directly would be the "proper" fix. It is a 4 MB
undocumented binary, and a bad write would break the user's whole preset browser — so this
tool does not go near it.

## Usage

```bash
python grpreset.py info "Marshall Madness.ngrr"
```

```bash
python grpreset.py set "Marshall Madness.ngrr" -o "Marshall Hotter.ngrr" --set "Lead 800:V1=0.75" --set "Lead 800:B=0.62"
```

`--set` takes `Component Name:ParamId=value`. Component and parameter ids come from
`COMPONENTS.md`. The patch targets the first component with that name in the rack; if a
preset uses the same amp twice, edit a copy per instance or work with `ngrr.py` directly.

## Building a rack from scratch

`rackbuild.py` composes a signal chain instead of only editing values.

```bash
python rackbuild.py --list
```

```bash
python rackbuild.py --backup --into "Warp X.ngrr" --chain "Skreamer,Lead 800,Matched Cabinet,Studio Reverb"
```

How it works: Guitar Rig's chain is a flat `<non-fix-components>` list with no count
attribute, and each `<component>` element is self-contained — GUI state, parameters and
ranges all inside it. So a rack is composed by concatenating component blocks. Two details
make it more than copy-paste:

- **`uuid` is per instance, not per type.** Measured across 350 presets: 87 of 101 component
  types carry a different uuid in every preset they appear in. Each placed component gets a
  fresh one.
- **`host-automationdb` references those uuids.** Entries pointing at components that are no
  longer in the rack are dropped and `num-parameters` is recomputed. Not every entry belongs
  to the chain: the manual documents the `automation-number` ranges as 1–16 macros, 17–256
  rack components, 257–276 header, 277–384 Rack Tools, 385–512 Global FX — so entries outside
  17–256 must survive the prune.

Verified in Guitar Rig 6.2.0: a preset's 18-component chain was replaced with a
4-component chain built this way (6033 → 4309 bytes, automation table pruned 23 → 9 entries,
zero orphan references) and Guitar Rig loaded exactly the four requested components.

**Component blocks are harvested from presets already on your machine** — this repository
ships none. A component can only be placed if some local preset uses it, so `--list` will
show fewer components than `catalog.py` knows about. That is the same coverage gap
`scan.py --coverage` reports, and the same reason contributing scans is useful.

## Macro controls

Guitar Rig splits controller assignment into two layers, and they live in different places:

| layer | where | maps |
|---|---|---|
| global | `Controller Assignments.shm` (a `" LMX"` wrapper around XML) | MIDI event → one of 16 controller slots |
| preset | `realtimecontroldb/remotecontroldb` inside the preset | controller slot → component parameter, with a range |

The controller slots **are** the macros. `macros.py` writes the preset layer:

```bash
python macros.py assign "preset.ngrr" --map "1=Jump:V1" --map "2=Jump:B" --range "1=0.1,0.9" --label "1=Gain"
```

That puts a whole chain's useful controls on one panel — gain, tone, drive, reverb and delay
mix reachable without hunting knobs across five components — and each macro is relabelled to
say what it does instead of `RK Switch 2`. `--range` bounds the sweep, so a macro can be
prevented from ever pushing reverb past 60%.

It also removes the tedious part of MIDI. Learn 8 CCs onto 8 macros **once**, globally, and
every preset carrying the same macro layout answers to the same knobs — no MIDI Learn per
parameter, per preset.

Verified in Guitar Rig 6.2.0: eight assignments written into a built rack showed up with the
right labels and moved the right knobs.

**Not decoded:** the global layer's `realevent-id`, which encodes the MIDI event itself
(`4294967295` means unassigned). This is the missing piece for driving Guitar Rig live over a
**virtual MIDI port** — a software cable (`loopMIDI` on Windows, the IAC Driver on macOS) that
lets the tool simulate a controller and move knobs while you play, with no file write and no
reload. No hardware is needed for it, and none is needed to decode it either: create a virtual
port, MIDI-learn a macro, send one control change from a script, and diff
`Controller Assignments.shm`. Nothing was set up on this machine, so it is left open — see
CONTRIBUTING.md.

## Looking things up in the official manual

Native Instruments publishes a full Guitar Rig manual. `docs-index.json` maps topics to the
right page so a lookup does not turn into guesswork:

```bash
python query.py docs "midi mapping"
```

```bash
python query.py docs
```

Only titles, URLs and topic keywords are stored — no manual text is copied. Fetch the page
when you need the wording. Note there are no per-component pages: `components-reference` is
one long page holding every component.

The manual is also what confirmed the two-layer MIDI model this tool works with, and what
decoded the automation ID ranges used by `rackbuild.py`.

## Wiring conventions

`components.json` says what each knob is. `topology.json` says what goes *next to* what,
learned from a corpus rather than asserted:

```bash
python tools/topology.py build
```

```bash
python tools/topology.py show
```

The signal-path order comes out of the data rather than being written in. From 270 unique
chains, position along the rack (0 = first, 1 = last):

```
Dynamics      0.08    Cabinets      0.50
Pitch         0.13    Modulation    0.50
Filters       0.14    EQ            0.56
Distortion    0.15    Delay & Echo  0.75
Amplifiers    0.25    Reverb        0.83
```

That is the textbook chain, recovered empirically. `rackbuild.py` uses it to warn before it
writes:

```
aviso: Studio Reverb: esta antes do usual (posicao 0.00, tipico 0.86, n=140)
aviso: Lead 800 -> Skreamer: nunca visto, mas Skreamer -> Lead 800 aparece 5x — talvez invertido
```

Advisory, never blocking — pass `--no-check` to silence it. An unusual rack can be exactly
right, and the corpus only knows what it has seen.

Two rules keep the summary honest. **Duplicates are collapsed** by hashing each chain with its
values; in the corpus this was developed against, 81 of 351 presets were near-copies, and
counting them would be one preset shouting. **Patterns below `--min-n` (default 5) are
dropped**, because a pattern seen once is that preset's opinion — and at N=1 the "statistic"
is literally one file's contents.

Structure only: no parameter values, nothing that identifies a source preset. Wiring order is
convention rather than authorship, which is exactly why it can be summarised and shared when
values cannot.

## The preset bank

`rackbuild.py` can only place components it has seen in a local preset, so a clean Guitar Rig
install gives the toolkit very little to work with. The bank closes that gap with authored
starting points stored as JSON.

```bash
python tools/bank.py list
```

```bash
python tools/bank.py apply example-template --into "<indexed preset.ngrr>" --backup
```

`apply` builds the chain, writes every value and assigns the macros in one step.

Entries are contributed by the people who made them — see `bank/README.md` for why that
matters and how to add one. Note that `rackbuild.py` harvests component blocks with their
values, so a rack you have not dialled yet is not yet yours to contribute.

## Diagnosing by symptom

`SINTOMAS.md` maps plain-language complaints ("tá abafado", "tá chiando", "some na mistura")
to a diagnosis and a concrete parameter move. It is a decision tree, not a tip list — the
same complaint can have opposite causes, and it says which to rule out first. Order of work
is fixed: level → noise → tone → dynamics → space.

It exists in **Portuguese, English, Spanish and French**. All four are generated from one
source: `sintomas.json` holds the structure — English field names, English enum values,
component and parameter references, deltas and frequencies — and `i18n/<lang>.json` holds
every string. A correction to the decision tree lands in all four languages at once, and a
translation cannot drift out of structural sync.

```bash
python build_docs.py
```

```bash
python build_docs.py --lang fr
```

Adding a language means copying one catalog and translating 266 strings; the validator
refuses a catalog with a missing or orphaned key. Component names, parameter ids and metric
identifiers are never translated — they are what you type into the tools.

Every component and parameter it cites is checked against the extracted dictionary:

```
$ python validate_sintomas.py
sintomas           : 22
referencias        : 169
chaves de texto    : 175
idiomas            : 4
   en.json         175 texto +  91 ui   ok
   es.json         175 texto +  91 ui   ok
   fr.json         175 texto +  91 ui   ok
   pt-BR.json      175 texto +  91 ui   ok
erros              : 0
avisos             : 9      <- components rare enough that your preset may not have them
```

Symptoms marked **[medível]** can be confirmed by measurement rather than by ear (peak
level, noise floor, band energy). Closing that loop automatically needs a loopback capture
routine, which is not built yet.

## Contributing

The most useful contribution is dictionary coverage. `catalog.py` knows 122 components;
`scan.py` only learns the ones your presets use.

```bash
python scan.py --coverage
```

That lists every catalogued component with no parameter data yet. If you own presets using
any of them, run `scan.py` and send the `components.json` diff.

Guitar Rig 7.0.2 has been measured on Windows (catalog, containers, headers, the library
scan), so the open questions there are narrower now: parameter data for the 16 components
it added, and anything at all from a macOS install — `paths.py` has macOS branches that
have never run against a real one.

**Do not commit `.ngrr` files.** Presets are other people's work; this repository carries
only code and extracted interface metadata.

## Not implemented

- Making Guitar Rig notice a newly created file, so `rackbuild.py` writes over an existing
  indexed preset rather than creating one (see the indexing note above).
- Placing a component no local preset contains.
- Any audio analysis.
