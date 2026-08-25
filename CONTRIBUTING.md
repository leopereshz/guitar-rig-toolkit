# Contributing

## Never commit presets

`.ngrr` files are excluded by `.gitignore` and must stay that way. Presets are other
people's work and are not ours to redistribute. This repository carries code and extracted
interface metadata — component names, parameter ids, value ranges — nothing else.

The same applies to `User.kad`, `Controller Assignments.shm` and the `gr*db` databases:
read them locally, commit only what the tools derive from them.

## Where to send what

**Pull request** for anything that is a file: a preset bank entry, dictionary coverage, a fix,
a documentation correction. `.github/PULL_REQUEST_TEMPLATE.md` carries the checklist, and CI
runs the validators on every PR.

**Issue** for anything that is a measurement rather than a file — Guitar Rig 7 output, a
`realevent-id` sample. Both have templates under `.github/ISSUE_TEMPLATE/`. Neither needs you
to write code.

## Contributing a preset to the bank

The bank (`bank/entries/`) is what makes the toolkit useful on a machine with no presets at
all. Entries are JSON, one file each, and `bank.py` writes them for you:

```bash
python tools/bank.py add "<your preset.ngrr>" --id my-tone --name "My Tone" --author "Your Name"
```

Then fill in `description`, `reference` and `notes` by hand — they are what let someone who has
never heard the tone know whether it is what they want — and check it:

```bash
python tools/bank.py validate
```

Open a PR with the resulting file. The `--author` flag is the authorship claim, and the git
history is what records it.

**Only contribute presets you made.** A preset's parameter values are its creative content, so
extracting them from someone else's pack is redistribution with a conversion step in the
middle, whatever the entry ends up being called. Downloading freely does not change that: a
pack posted on a forum is public in the same sense a photograph posted online is public.

There is one trap worth naming, because it catches people acting in good faith. `rackbuild.py`
harvests component blocks **with their values** from presets already on your machine — so a
rack you just built and have not dialled yet is carrying whatever numbers came with those
blocks. Tune it before you contribute it.

`validate` also warns when an entry omits parameters. That is a reproducibility problem rather
than an ethical one: anything you leave out inherits from whichever local preset supplied that
component, so the same entry would sound different on someone else's machine.

## The most useful contribution: dictionary coverage

`catalog.py` reads Guitar Rig's own component list — 122 components. `scan.py` can only
learn parameter ids and ranges from components that appear in presets someone actually owns,
so coverage is always partial.

```bash
python query.py missing
```

If you own presets using any of the components listed, run:

```bash
python scan.py --path "/wherever/your/presets/live"
```

`scan.py` merges by default, so it adds what it finds without discarding what was already
there. Send the `components.json` diff as a pull request. Please say which Guitar Rig
version wrote the presets — that context matters for `COMPAT.md`.

## The second most useful: Guitar Rig 7

No Guitar Rig 7 install was available while this was written, so the GR7 section of
`COMPAT.md` is prediction, not measurement. If you have it, this turns it into fact:

```bash
python paths.py
```

```bash
python catalog.py
```

```bash
python test_roundtrip.py
```

Open an issue with the output. Particularly interesting: which container Guitar Rig 7
writes, whether its `User.kad` still carries the `CP://` component catalog, and whether the
`<gr-instrument-chunk>` header gained or lost attributes.

## Open problems worth solving

Two things would make this markedly better and neither is blocked by anything except effort.
Official reference for both:
<https://docs.native-instruments.com/ni-tech-manuals/guitar-rig-manual/en/automation-and-midi-control>

### 1. Drive Guitar Rig live over a virtual MIDI port

The point of this one is **real-time control without any hardware**. A virtual MIDI port is a
software cable between two programs on the same machine — `loopMIDI` on Windows, the built-in
IAC Driver on macOS. The tool opens one end and Guitar Rig listens on the other, so Guitar Rig
believes a controller is plugged in while it is really a script sending control-change
messages. That is what lets "a bit more gain" move a knob **while you play**, with no file
write, no reload and no double-click.

Nobody needs to own a pedalboard for this. The machine this was developed on had zero MIDI
inputs, which is exactly the situation a virtual port fixes.

Guitar Rig stores controller assignment in two layers, and the manual confirms the split:
macro and Rack Tools mappings are **global**, ordinary rack component mappings are **per
preset**.

`macros.py` already writes the per-preset layer — which macro drives which parameter, with a
value range. What is missing is the global layer: which MIDI CC drives which macro.

That layer lives in `Controller Assignments.shm` under Guitar Rig's application data. It is a
`" LMX"` wrapper around plain XML — the same wrapper as the `tsrp` chunk inside a preset, so
the existing reader already handles it:

```xml
<controllerdatabase-config num-controller="16">
  <controller lock="0" name="RK Pedal" num-param="0" realevent-id="4294967295" slot-id="0" toggle="1"/>
```

`realevent-id="4294967295"` (`0xFFFFFFFF`) means unassigned. **How a real MIDI event is encoded
into that integer is not known**, because every slot was unassigned on the machine this was
developed on — there was no sample to reverse.

Decoding it takes one person, one virtual port and no hardware:

1. Install `loopMIDI` (Windows) or enable the IAC Driver (macOS) and create one port.
2. Enable that port as a MIDI input in Guitar Rig's Preferences.
3. Copy `Controller Assignments.shm` somewhere safe.
4. In Guitar Rig, right-click a macro and choose Learn MIDI Control, then send one control
   change into the port — `python-rtmidi` in three lines is enough, no controller required.
5. Copy the file again and diff the two.
6. Repeat with a different CC number and a different channel.

Two or three samples should show whether the integer packs channel, message type and CC
number, and in what order. Open an issue with the before/after XML — that alone is the
contribution, no code needed.

Once decoded, the tool can write the mappings itself and the whole setup collapses to nothing:
no MIDI Learn per parameter, no MIDI Learn per preset. Every preset it builds already carries
the same macro layout, and the same eight simulated knobs drive all of them.

Worth being clear about the trade-off, so this does not get oversold. MIDI control is 7-bit —
128 steps per parameter — and only reaches controls that are mapped. Editing the file reaches
every parameter at full float precision and can restructure the rack. So this is not a
replacement for the file path; it is the live-tweaking half, for adjusting while playing
instead of stopping to reload.

### 2. Make Guitar Rig reload an edited preset by itself

Right now the loop has a manual step in the middle. The tool writes the file, and then
**you have to double-click the preset in Guitar Rig** for it to re-read from disk. A single
click on the preset that is already loaded does nothing — Guitar Rig serves it from memory.

It works, and it is fast, but it breaks the flow: describe a problem, get a fix, click twice,
listen. The two clicks are the only part a person cannot delegate.

Avenues someone could explore, roughly in order of promise:

- **MIDI Program Change over the same virtual port.** Guitar Rig maps preset selection
  globally (the manual lists preset selection under global mappings). If a Program Change can
  select a preset, then sending "select something else" followed by "select this one again"
  would force a re-read from disk without anyone touching the UI. This needs the virtual port
  from problem 1, which is why the two are listed together — solve that one and this may fall
  out for free.
- **The plug-in in a DAW.** A host can reload plug-in state on its own terms; the constraint
  may simply not exist there.
- **The preset database.** `Database/gr<n>db` is a 4 MB undocumented binary. Injecting or
  invalidating an entry would solve both this and the "new files never appear" problem — but
  a bad write breaks the user's entire preset browser, so this tool deliberately does not go
  near it. Treat as research, not as a patch.

## Changing what the skill triggers on

The `description` in `skills/guitar-rig/SKILL.md` is the only thing Claude sees when deciding
whether to consult the skill. Both failure modes are silent: too eager and it interrupts
people who wanted to talk about something else, too timid and it never fires, which is
indistinguishable from the plugin not being installed.

So the description is calibrated against a test set rather than written by feel. See
`evals/README.md` for the method and the current numbers. If you change the description,
re-run both rounds:

```bash
python evals/aggregate.py easy
```

```bash
python evals/aggregate.py hard
```

New queries are welcome, especially near-misses that share vocabulary with the skill but need
something else. A query nobody would confuse for this skill tests nothing.

## Reverse-engineering notes

Everything asserted about the file formats was measured, not inferred, and the tests are the
evidence. Please keep it that way:

- If you add a claim about the format, add the check that demonstrates it.
- If something is untested, say so in the text rather than rounding up to certainty.
- `test_roundtrip.py` must stay at zero failures. It parses every preset it finds and
  rebuilds it byte-for-byte; a regression there means the writer is corrupting files.
- `validate_sintomas.py` must stay at zero errors. It checks that every component and
  parameter `sintomas.json` cites actually exists in the dictionary.

## Editing presets safely

The tools write in place, because Guitar Rig only lists presets its own database has
indexed. That makes backups non-optional:

- `--backup` on `rackbuild.py` and `macros.py` writes a `.bak` next to the target.
- Verify the result loads in Guitar Rig before deleting the backup.
- Double-click a preset in Guitar Rig to force a re-read from disk; a single click on the
  already-loaded preset does nothing.

## Tone reference

`sintomas.json` is the source of truth for the symptom reference; the Markdown is generated
from it. Corrections to the audio-engineering content are welcome, especially from people
who mix guitar for a living. Two rules:

- Every action must name a component and parameter that exists in `components.json`.
  `validate_sintomas.py` enforces this.
- A symptom needs a diagnosis, not just a fix. The same complaint often has opposite causes,
  and saying which to rule out first is the whole value of the document.
