<!--
Contributing a preset to the bank? Fill in the section below.
Anything else — a fix, a doc correction, dictionary coverage — just delete it and
describe your change normally.
-->

## What this changes

<!-- one or two sentences -->

---

## Preset bank entry

Delete this whole section if the PR is not adding a bank entry.

**Authorship.** By opening this PR you are stating that you made this preset yourself and are
releasing it under the repository's MIT licence.

That matters more here than in most projects. A preset's parameter values are its creative
content, so an entry harvested out of somebody else's pack is redistribution with an extra
step — regardless of what the entry is called or whether the source is credited. Free download
does not change that either: a pack posted on a forum is public in the same sense a photograph
posted online is public.

If you built the rack with `rackbuild.py`, be aware it harvests component blocks **with their
values** from presets already on your machine. A freshly built rack you have not dialled yet
is carrying someone else's numbers. Dial it before contributing.

- [ ] I made this preset. The values are mine, not extracted from a preset pack.
- [ ] `python tools/bank.py validate` passes with no errors and no warnings.
- [ ] `description`, `reference` and `notes` are filled in — they are what make the entry
      usable to someone who has never heard the tone.
- [ ] The `reference` field describes **gear**, not anyone's patch. "Hiwatt-style clean stack
      with a Big Muff in front" is a statement of fact; "Gilmour's actual settings" is not.
- [ ] Every parameter has a value. Omitted ones inherit from whatever local preset supplied
      the component, so the entry would sound different on someone else's machine.

**What it is for**

<!-- What kind of playing? What guitar and pickup did you dial it on? What should someone
     reach for first if it does not sit right on their rig? -->
