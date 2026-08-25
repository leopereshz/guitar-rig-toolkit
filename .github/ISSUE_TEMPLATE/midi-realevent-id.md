---
name: MIDI realevent-id sample
about: Help decode how Guitar Rig encodes a MIDI event, so the tool can write mappings itself
title: "MIDI: realevent-id sample for CC "
labels: midi, data
---

This unlocks driving Guitar Rig live over a **virtual MIDI port** — a software cable
(`loopMIDI` on Windows, the IAC Driver on macOS) that lets the tool simulate a controller and
move knobs while you play, with no file write, no reload and no double-click.

No hardware is needed, for the feature or for this report. The machine this was developed on
had zero MIDI inputs, which is exactly what a virtual port fixes — and why the encoding was
never observed.

## What is missing

`Controller Assignments.shm` stores which MIDI event drives each of the 16 macro slots:

```xml
<controller lock="0" name="RK Pedal" num-param="0" realevent-id="4294967295" slot-id="0" toggle="1"/>
```

`4294967295` is `0xFFFFFFFF` — unassigned. **How a real event is packed into that integer is
unknown.** Two or three samples should reveal whether it carries channel, message type and CC
number, and in what order.

## How to capture one

1. Install `loopMIDI` (Windows) or enable the IAC Driver (macOS), and create one port.
2. In Guitar Rig, Preferences → MIDI, enable that port as an input.
3. Copy `Controller Assignments.shm` somewhere safe. It lives under
   `%LOCALAPPDATA%\Native Instruments\Guitar Rig <n>\` on Windows, or
   `~/Library/Application Support/Native Instruments/Guitar Rig <n>/` on macOS.
4. Right-click a macro, choose Learn MIDI Control, and send one control change into the port.
   Three lines of `python-rtmidi` is enough; a real controller works too if you have one.
5. Copy the file again.

To read either copy as XML:

```bash
python -c "import struct,sys; d=open(sys.argv[1],'rb').read(); o=d.find(b' LMX'); v,n=struct.unpack_from('<II',d,o+4); print(d[o+12:o+12+n].decode())" "<the .shm file>"
```

## Paste the samples

Please do at least two, varying **both** the CC number and the MIDI channel — one sample alone
cannot separate which bits are which.

**Sample 1** — CC number: `___`  channel: `___`  macro slot: `___`

```xml

```

**Sample 2** — CC number: `___`  channel: `___`  macro slot: `___`

```xml

```

Only the `<controller>` line that changed is needed, before and after. If a note-on or a
program change is easy for you to send as well, that would settle whether the message type is
encoded in the same integer.
