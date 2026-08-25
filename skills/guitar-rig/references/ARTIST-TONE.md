# Chasing an artist or song tone

A method, not a database.

A curated list of "here are the settings for 30 famous songs" is a trap: tone opinion is
endless and contested, any fixed list pleases almost nobody, and the values would in
practice be someone else's preset copied into a different file format. So this repository
ships two things instead — `gearmap.json`, which says what each Guitar Rig component
models, and this document, which says how to get from "I want the Comfortably Numb solo" to
a rack.

## Step 0 — check the bank, then what is already installed

Two cheap lookups before any research.

**The bank** ships with the toolkit, so it works on a machine with no presets at all:

```bash
python tools/bank.py list
```

```bash
python tools/bank.py apply <id> --into "<indexed preset>" --backup
```

Entries are archetypes rather than song recreations — British crunch, American clean, Vox
chime, Muff into a clean stack. Most artist requests are really a request for an archetype
plus a tweak, so start there and adjust rather than building from nothing.

**Then their own presets.** Preset packs circulate widely and are usually named after the song
or the player.

```bash
python query.py preset "<path>"
```

```bash
python paths.py
```

Search the discovered preset folders for the artist, the song, and the band. A preset
someone built by ear beats anything synthesised from a gear list, and it costs nothing to
try. Only move on when nothing turns up.

## Step 1 — research the gear, never the settings

Search for **what was used**, not for numbers:

- `"<artist> <song> guitar rig"`, `"<artist> <album> amp"`, `"<artist> pedalboard <year>"`
- `"<artist> gear rundown"`, `"<song> tone how to"`

What you want out of it: amp, drive pedals in front, time-based effects, roughly how much
gain, and which guitar and pickup position. Nothing more.

**Do not** collect knob positions from a forum post and present them as fact. They were
dialled on different gear in a different room, and they are usually somebody's preset in
prose form. Gear is a fact about the world; settings are a judgement about a specific rig.

### Source quality

| tier | what | how to treat it |
|---|---|---|
| best | interviews with the player or their tech, manufacturer rig features, credible gear databases, documented touring rigs | quote confidently, name the source |
| useful | long-running gear forums where regulars cite sources, well-sourced fan sites | usable, say where it came from |
| weak | a single forum post, video comments, AI-generated tone blogs, sites that mostly repeat each other | ignore, or say explicitly that it is unverified |

Two things to keep in mind. Rigs change constantly — album, tour and later re-recordings
often differ, so pin down *which* version is wanted. And what is on the record is often not
the live rig; studio tone includes the room, the mic, the desk and the mix.

### When sources disagree

They will. Say so rather than picking a winner:

> Two amps come up for this: a Hiwatt DR103 and a Yamaha RA-200 rotary, and there is decent
> evidence both were used on different parts. I'll start with the Hiwatt because the
> sustained solo tone is the recognisable part. If it sounds too static we can add the
> rotary.

## Step 2 — translate gear to Guitar Rig components

`gearmap.json` maps real gear to what Guitar Rig calls it. Native Instruments named the
models after the originals, so most of the table is unambiguous — `High White` is a Hiwatt,
`Big Fuzz` is a Big Muff, `Skreamer` is a Tube Screamer.

Every entry carries a `confidence`. Use it honestly:

- `high` — state the mapping plainly
- `medium` — the obvious reading, but say it is not confirmed
- `unknown` — do not guess. Pick by *voice* instead, and say that is what you did.

When there is no match, substitute by character rather than by brand. A Vox AC30 part on an
install without `AC Box` is better served by a low-gain chimey amp than by a Rectifier.

Check what can actually be placed:

```bash
python rackbuild.py --list
```

Components are harvested from presets on the machine, so a component in the catalog with no
local preset using it **cannot be placed**. Say so and offer the nearest available voice.

## Step 3 — build the chain

Signal order for a normal electric guitar rig:

```
wah / filter → compressor → drive and boost → amp → cabinet → modulation → delay → reverb
```

```bash
python rackbuild.py --backup --into "<indexed preset>" --chain "Big Fuzz,High White,Matched Cabinet,Delay Man,Studio Reverb"
```

Remember the constraint from the README: Guitar Rig only lists presets its own database
indexed, so write into a slot it created. Ask the user to save a placeholder preset first if
there is no spare slot.

## Step 4 — set starting values from voice, not from copied numbers

Use the `voice` field in `gearmap.json` and the frequency map in the symptom reference.
Translate descriptions into parameter moves:

| description | what it means |
|---|---|
| "edge of breakup" | preamp around 0.4–0.5, master carrying the level |
| "cranked, cleans up with the volume knob" | preamp high, low output from the guitar side |
| "scooped" | mid low, bass and treble up — check `lost_in_mix` before committing |
| "mid-forward, cuts through" | mid up, Tube Screamer in front with low drive and high level |
| "thick and dark" | treble and presence down, cab mic away from the cone centre |
| "glassy, chimey" | low gain, treble and presence up, mic toward the cone centre |

Then hand over to `macros.py` so the player can dial the rest without hunting knobs:

```bash
python macros.py assign "<preset>" --map "1=High White:V1" --label "1=Gain"
```

## Step 5 — iterate with the symptom reference

The first attempt will be wrong. That is expected — this is where the real work happens, and
`SINTOMAS.md` / `SYMPTOMS.md` is built for exactly this loop. Ask what is off in plain
language and act on the diagnosis, not on the complaint:

> "too harsh" → `harsh`: presence first, then mic position, then a narrow cut swept
> between 2.5 and 5 kHz

## What to tell the user, every time

Say this early rather than after they are disappointed:

- **The preset is maybe 40% of it.** Guitar, pickups, string age, and above all the player's
  hands carry the rest. Gilmour's tone is substantially a Strat and Gilmour.
- **A record is not a rig.** What you hear includes the room, mics, console, tape and mixing.
  No preset reproduces a recording.
- **This is "in the style of".** Describing what gear someone used is a fact. Implying an
  official or endorsed preset is not, and this project makes no such claim.
- **Say which parts are researched and which are inferred**, so the user knows where to
  push back.
