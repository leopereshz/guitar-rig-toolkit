---
name: Guitar Rig 7 report
about: Turn the GR7 section of COMPAT.md from prediction into measurement
title: "GR7: "
labels: compatibility, data
---

No Guitar Rig 7 install was available while this was written, so everything `COMPAT.md` says
about GR7's **file format** is a prediction. Its component list came from the manual; nothing
else did.

If you have GR7, this is the single most useful thing you can send. It needs no code.

## Output

```
$ python tools/paths.py

```

```
$ python tools/catalog.py

```

```
$ python tools/test_roundtrip.py

```

## The three questions that matter

Answer whichever you can — partial is fine.

**Which container does GR7 write?** Save any preset from inside GR7, then:

```
$ python tools/grpreset.py info "<that preset>.ngrr"

```

`sndf` means it still writes the Guitar Rig 4/5 SoundShell format; `nish` means the Guitar
Rig 6 one; an error naming an unknown magic means a third format exists and this is very
interesting.

**Does its `User.kad` still carry the component catalog?** `catalog.py` reports this. Guitar
Rig 5 shipped the `CP://` sets empty and GR6 populated them; whether GR7 kept that is unknown.

**Did the header change again?** GR6 dropped four attributes that GR4 and GR5 wrote. Paste the
first three lines of a GR7 preset's rack XML:

```
$ python -c "import sys; sys.path.insert(0,'tools'); from scan import read_rack_xml; print(read_rack_xml(r'<preset>.ngrr')[0][:400])"

```

## Anything unexpected

Components the catalog reports that the manual does not list, names that differ from
`tools/docs-index.json`, a tool that errors — all worth mentioning.
