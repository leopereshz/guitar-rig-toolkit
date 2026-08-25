# Trigger calibration

A skill only helps if it fires when it should and stays quiet when it should not. The
`description` in `skills/guitar-rig/SKILL.md` is what decides that — Claude sees the skill's
name and description and nothing else when choosing whether to consult it.

These files are the evidence that the current description works, and the record of how it was
corrected when it did not.

## Method

Three independent judges are each given a realistic list of available skills — the guitar-rig
skill plus five plausible competitors — and the query text alone. They never see which answer
is expected; the `should_trigger` field is the hypothesis under test, and the judge prompt
tells them to ignore it.

Agreement between judges is the signal. A query all three agree on is a clear case. A split
marks a boundary the description does not draw sharply enough.

```bash
python aggregate.py easy
```

```bash
python aggregate.py hard
```

## Round 1 — baseline set

20 queries in Portuguese, English, Spanish and French. Half should trigger, half are
near-misses that share vocabulary but need something else: acoustic guitar mic technique,
mixing a vocal bus, learning a solo, buying a real amp, a physical amp humming.

**Result: 20/20, unanimous.**

That is a weaker result than it looks. A perfect score on the first attempt usually means the
test set was too easy rather than that the description is right — most of those near-misses
carry an obvious domain marker ("violão", "Logic", "tablatura", "Fender Blues Junior"), and an
attentive judge separates them without needing a good description.

## Round 2 — hard set

20 queries, all Portuguese, all deliberately on the line. Bass through Guitar Rig. A preset
that changed after an update, which reads like a support question. A parameter question rather
than a complaint. Comparing two preset files, with no audio symptom at all. The same symptom
on a competing amp simulator. Guitar Rig's tapedeck, which is the right software but not tone
work. Mastering someone else's track, where the symptom matches but there is no preset to
edit.

**First run: 19/20.** All three judges disagreed with the hypothesis on one query:

> *"passei um vocal pelo guitar rig pra dar uma sujeira e ficou estranho, muito áspero e sem
> inteligibilidade"*

The hypothesis said do not trigger, because the skill was written as electric-guitar-only. All
three judges triggered anyway, and they were right: it is Guitar Rig, it is component-level
rack work, and the tools behave identically. The restriction was arbitrary.

Both sides needed fixing rather than one:

- The **description** now says electric guitar is the main case but the skill applies to bass,
  vocals or anything else running through a Guitar Rig rack. It also names what the skill is
  *not* for, since a competing amp sim with an identical symptom was the case one judge found
  hardest.
- The **skill body** now warns that the symptom reference is calibrated for electric guitar.
  Level, noise, clipping and phase diagnosis transfer to any source because they are
  properties of the signal. The frequency map does not — a vocal's presence sits higher than a
  guitar's, and sibilance lives at 5–8 kHz where a guitar has fizz.

**Second run, corrected description: 20/20, unanimous.**

The risk in that edit was the exclusion clause, which is the classic way to cause
under-triggering: a model reads "not for DAW operation" and backs away from a legitimate case
that happens to mention a DAW. Query 8 was the canary —

> *"uso o guitar rig como plugin dentro do reaper e o preset que montei tá abafado só quando
> tá na sessão, sozinho soa bem"*

— an editable preset, described entirely in DAW terms. It still triggered unanimously.

## Files

| file | what it is |
|---|---|
| `trigger-eval.json` | round 1, mixed languages, baseline difficulty |
| `trigger-eval-hard.json` | round 2, boundary cases, with a note on why each is hard |
| `judge-*.json` | round 1 verdicts, one file per judge |
| `hard-judge-*.json` | round 2 verdicts, corrected description |
| `round1/hard-judge-*.json` | round 2 verdicts against the *original* description, kept as the before |
| `aggregate.py` | scores the verdicts and reports errors and splits |

## If you change the description

Re-run both rounds. A description edit that is not re-tested is a guess, and the failure mode
is silent — an over-eager description annoys people who wanted to talk about something else,
and a timid one simply never fires, which looks identical to the plugin not being installed.

Adding queries is welcome, especially near-misses. The valuable ones share vocabulary with the
skill and still need something else; a query nobody would confuse for this skill tests nothing.
