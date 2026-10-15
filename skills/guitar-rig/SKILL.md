---
name: guitar-rig
description: Diagnose and fix tone problems in Native Instruments Guitar Rig, edit its preset files, and build racks from scratch. Use this skill whenever someone describes a sound as wrong in any language — "it's muffled", "too harsh", "hissing", "clipping", "no sustain", "gets lost in the mix", "tá abafado", "tá chiando", "o som tá estourando", "suena apagado", "ça sature", "trop d'aigus" — or asks for the tone of a particular artist, song, amp or pedal. Electric guitar is the main case, but this applies to bass, vocals or anything else running through a Guitar Rig rack. Also use it for anything involving .ngrr preset files, the Guitar Rig rack, amp/cabinet/effect components, macro controls, or MIDI mapping in Guitar Rig. Trigger even when Guitar Rig is never named, as long as the person is talking about an electric guitar sound they want changed — most people describe the symptom, not the software. Not for other amp simulators, Guitar Rig installation or crash problems, physical instrument or pedal repair, music theory, DAW operation, or mixing tracks whose preset you cannot edit.
---

# Guitar Rig toolkit

Guitar tone complaints are almost always described as a feeling — muddy, harsh, thin, lost —
and the useful move is to turn that feeling into a diagnosis and then into a specific
parameter change. This skill carries the mapping, the tools that read and write the preset
files, and the knowledge of Guitar Rig's own quirks.

Everything asserted here about the file formats was measured on real presets and verified by
loading the result in Guitar Rig. Where something is unverified, the reference files say so.

## Before anything else

Tools live in `../../tools/` relative to this file. Run them with `python`.

If `tools/components.json` is missing or the user has never run setup, do setup first — the
dictionary of parameters is built from the presets on *their* machine, and without it every
suggestion would be a guess:

```bash
python tools/paths.py
```

```bash
python tools/catalog.py
```

```bash
python tools/scan.py
```

`paths.py` finds the Guitar Rig install and preset folders on Windows and macOS. `catalog.py`
reads Guitar Rig's own component list. `scan.py` learns parameter ids and value ranges from
the user's presets and merges into what is already known. Report the coverage number it
prints — it tells the user how much of Guitar Rig this install can actually speak about.

## Two modes, and only one needs setup

**Fixing a preset the user already has** works immediately. Edit their file in place, always
after a backup.

**Building a new tone** needs somewhere to put it. Guitar Rig only lists presets its own
database indexed; it does not watch its preset folder, so a file written there appears only
after the user does one of these, once:

- Build a preset anywhere with `rackbuild.py`, then have them use Guitar Rig's
  **Main menu → File → Import…** and pick it. Import copies the file into
  `User Content/Guitar Rig <n>/Rack Presets/` and registers it. From then on, write to that
  copy.
- Or have them save any preset from inside Guitar Rig under a name like `AI Workbench`.
- Or, for a whole folder at once, **File → Preferences → Library → Scan**.

Either way it is one action, once. Explain why rather than just asking — people reasonably
assume a program watches its own folder, and this one does not.

### When the scan skips presets

The scan indexes a preset under the `<name>` stored *inside* the file, then resolves that
entry back to `<name>.ngrr` on disk. Packs shipped as `Artist - Song.ngrr` whose soundinfo
still says `Song` fail that lookup and are dropped without a message — on one Guitar Rig 7
install, 444 of 537 copied presets never appeared for exactly this reason.

If the user says presets they copied in are missing, run this before anything else:

```
python tools/library.py check --version 7
python tools/library.py fix   --version 7 --backup --apply
```

`fix` rewrites each file's internal name to match its file name, so the descriptive name is
what shows up in the browser. Then have them run the Scan again. Presets saved by Guitar
Rig 6 or later (NISH container) cannot have their metadata resized in place, so those need
`--mode rename`, which renames the file to the internal name instead.

The Scan **only adds**. An entry whose file was renamed or deleted stays in the browser and
fails to load, so after any renaming or deleting tell the user to clean the library —
**File → Preferences → Library** has the cleanup, and `python tools/library.py index
--stale` lists which rows are affected. Guitar Rig owns its database; nothing here writes
to it.

When the user wants a folder of downloaded presets brought in, use `library.py import
<folder>`, not a file copy. It skips what the library already holds (compared on the
rack, not the file name), takes one of any copies inside the batch, and corrects each
internal name on the way in — doing those in any other order wastes the work. It never
modifies the source folder, and defaults to a dry run.

A collection built from several downloads usually holds the same rack several times
(`Nighttrain`, `Nighttrain (2)`, `Nighttrain 1`). `python tools/library.py dupes` finds
them by fingerprinting the rack with the per-copy bookkeeping removed — byte comparison
finds nothing, because every copy has its own uuids and save stamp. It reports separately
the groups whose rack matches but whose **name or author differs**, and leaves those
alone: those are a decision for the user, not a cleanup. Never run `dupes --apply`
without showing the list first.

Renaming a preset is itself a way back into this mess, so use the command that does both
halves at once rather than moving files around:

```
python tools/library.py rename --version 7 --replace "OLD=NEW" --apply
python tools/library.py rename "<file.ngrr>" --to "New Name" --apply
```

### Impulse responses are not broken by moving files

If the user worries that a moved or renamed `.wav` broke a preset, check before agreeing.
**Reflektor embeds the impulse response in the preset** as base64 beside the original
`filename`; that path is provenance, not a lookup, and it is normally dead already because
the preset came from someone else's machine. Tapedeck stores a path only, but that is the
practice backing track, not the tone.

```
python tools/library.py assets --version 7
```

`audio intact` is the number that matters. `original path still resolves` can be 0 with
nothing wrong. Only a `BAD` line means a preset genuinely lost its IR, and the fix for that
is loading the `.wav` again in Reflektor — there is no file-shuffling that repairs it.

## The loop

Guitar Rig caches the preset it has loaded. After writing a file, tell the user to
**double-click** the preset in the browser — a single click on the already-loaded preset does
nothing. This is the one manual step per iteration and it is worth naming every time, because
otherwise they will think the change did not work.

```
listen → describe the problem → diagnose → change one thing → double-click → listen
```

Change a small number of parameters per round. The deltas in the symptom reference are one
step, not a destination. Two or three rounds of one change each teaches the user what each
control does; one round of twelve changes teaches them nothing and usually overshoots.

## Diagnosing a complaint

Read `references/SYMPTOMS.md` (or `SINTOMAS.md` for Portuguese, `SINTOMAS.es.md` for Spanish,
`SYMPTOMES.fr.md` for French — match the user's language). It covers 22 symptoms with the
phrases people actually use, how to confirm each one, causes in order of likelihood, and the
concrete parameter move.

Three things in it matter more than the rest:

**Order is fixed: level → noise → tone → dynamics → space.** Each stage contaminates the next.
Adjusting EQ while the signal clips is pointless, because the harshness bothering them is the
clip and not the tone. Setting a gate before fixing excess gain masks the noise and eats the
sustain.

**The same complaint can have opposite causes.** "Too quiet" playing alone is a level problem;
"too quiet" with a band is a frequency-competition problem, and the fixes work against each
other. The reference says which to rule out first — follow it rather than pattern-matching on
the words.

**Hiss, hum and fizz are three different problems** that everyone calls the same thing. Hiss
is constant and a gate removes it. Hum is mains frequency and a gate makes it worse. Fizz only
exists while playing and a gate does nothing. Ask one distinguishing question instead of
guessing.

Some causes sit outside Guitar Rig entirely — interface gain, old strings, buffer size,
grounding. Say so plainly instead of adjusting a knob that cannot fix it.

**The reference is calibrated for electric guitar.** Guitar Rig happily processes bass,
vocals, drums or anything else, and the tools work the same on those racks — level, noise,
clipping and phase diagnosis all transfer unchanged, because they are properties of the
signal rather than of the instrument. The frequency map does not. A vocal's presence sits
higher than a guitar's, sibilance lives at 5–8 kHz where a guitar has fizz, and bass moves
everything down. When the source is not an electric guitar, use the structure — order of
diagnosis, one change at a time, cause before symptom — and say that the specific frequency
targets are guitar numbers rather than quoting them as if they applied.

## Reading and writing presets

```bash
python tools/query.py preset "<file.ngrr>"
```

```bash
python tools/grpreset.py dump "<file.ngrr>"
```

```bash
python tools/grpreset.py set "<file.ngrr>" -o "<file.ngrr>" --set "Lead 800:V1=0.75"
```

Parameter ids come from the dictionary, not from memory:

```bash
python tools/query.py component "Lead 800"
```

Two container formats exist and the tools detect which is which. Presets written by Guitar Rig
4 and 5 can be rewritten freely. Presets written by Guitar Rig 6 use a container where only
width-preserving value edits are possible — the tools refuse anything else rather than
corrupting the file, and the error message says what to do instead.

**Back up before writing.** `rackbuild.py` and `macros.py` take `--backup`; for `grpreset.py`,
copy the file first. This is not ceremony: the user's presets may be irreplaceable, and the
edit is in place because Guitar Rig gives no other option.

## Starting from the bank

Before building anything from scratch, look at what ships with the toolkit:

```bash
python tools/bank.py list
```

```bash
python tools/bank.py apply <id> --into "<indexed preset>" --backup
```

The bank holds authored starting points — archetypes rather than recreations. `apply` builds
the chain, writes every value and assigns the macros in one step, which is both faster and
more predictable than composing a rack and then dialling it. This is the only path that works
on a machine with no presets at all, since `rackbuild.py` can only place components it has
seen locally.

Entries are contributed by people who made them. If the user dials something they like, offer
to capture it:

```bash
python tools/bank.py add "<their preset>" --id <id> --name "<name>" --author "<them>"
```

Do not offer to add a rack they have not actually tuned. `rackbuild.py` harvests component
blocks **with the values from whichever local preset supplied them**, so an untouched build is
carrying someone else's numbers rather than theirs.

## Building a rack

```bash
python tools/rackbuild.py --list
```

```bash
python tools/rackbuild.py --backup --into "<indexed preset>" --chain "Skreamer,Lead 800,Matched Cabinet,Studio Reverb"
```

Signal order for a normal electric rig: wah/filter → compressor → drive → amp → cabinet →
modulation → delay → reverb.

Components are harvested from presets on the user's machine, so `--list` shows fewer
components than the catalog knows about. If something is unavailable, substitute by character
and say that is what you did — a Vox part on an install without `AC Box` is better served by
another chimey low-gain amp than by a Rectifier.

## Macro controls

After building, put the useful controls on one panel so the user can explore without hunting
knobs across five components:

```bash
python tools/macros.py assign "<preset>" --map "1=Lead 800:V1" --label "1=Gain" --range "1=0.1,0.9"
```

`--range` bounds a macro's sweep, which is how you stop reverb or delay from ever going
too far. Labels default to the parameter's own name, so the panel explains itself.

## Artist and song tones

Read `references/ARTIST-TONE.md`. Short version: look in the user's own presets first, because
preset packs circulate widely and a preset built by ear beats anything synthesised. Then
research the **gear** — never settings copied off a forum, which are somebody's preset in
prose and were dialled on different equipment in a different room. Translate gear to
components with `tools/gearmap.json`, which carries a confidence level per entry; where it
says `unknown`, pick by voice and say that is what you did.

Set expectations early rather than after disappointment: the preset is perhaps 40% of a tone,
a record is not a rig, and this is "in the style of" rather than anyone's official settings.

## Consulting the official manual

Native Instruments publishes a full manual. When a parameter's purpose is genuinely unclear,
look it up instead of inventing an explanation:

```bash
python tools/query.py docs "midi mapping"
```

That prints the URL of the page that answers it. Fetch the page when you need the wording.
There are no per-component pages — `components-reference` is one long page holding all of
them.

## What this cannot do

Say these plainly when they come up, because a confident wrong answer costs the user time:

- **It cannot make Guitar Rig notice a brand-new file.** Import, a manual save, or a Library
  Scan is required, and all three are the user's click.
- **It cannot reload the preset for them.** That is the double-click.
- **It cannot hear.** Every judgement about whether something sounds better comes from the
  user. The measurable symptoms — clipping, noise floor, band balance — could be confirmed by
  analysis, but the audio capture routine does not exist yet.
- **It cannot place a component nobody's preset uses**, because parameter data is learned from
  presets rather than shipped.
