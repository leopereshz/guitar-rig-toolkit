---
description: Diagnose a guitar tone problem and fix it in a Guitar Rig preset
argument-hint: [what is wrong with the sound]
---

The user says something is wrong with their guitar sound: **$ARGUMENTS**

Work through it as a diagnosis, not as a lookup. The same complaint often has opposite causes,
and applying the wrong fix makes the problem worse while convincing the user the tool does not
work.

1. **Find out which preset.** If they have not said, ask, or list what is loaded. Do not guess
   — editing the wrong file is worse than asking one question.

2. **Read it before changing it.**

   ```bash
   python tools/query.py preset "<file.ngrr>"
   ```

   Knowing which components are actually in the chain matters: advice about a Noise Reduction
   that is not there wastes everyone's time.

3. **Diagnose.** Open the symptom reference in the user's language —
   `skills/guitar-rig/references/SYMPTOMS.md`, or `SINTOMAS.md`, `SINTOMAS.es.md`,
   `SYMPTOMES.fr.md`. Find the symptom, check what it says to rule out first, and ask the one
   distinguishing question if the complaint is ambiguous. "Hissing" alone does not say whether
   it is hiss, hum or fizz, and those three have different and partly opposite fixes.

4. **Back up, then change a small number of things.**

   ```bash
   cp "<file.ngrr>" "<file.ngrr>.bak"
   ```

   ```bash
   python tools/grpreset.py set "<file.ngrr>" -o "<file.ngrr>" --set "Component:Param=value"
   ```

   The deltas in the reference are one step, not a destination. Two or three rounds of one
   change each teach the user what the control does; twelve changes at once teach nothing and
   usually overshoot.

5. **Tell them to double-click the preset** in Guitar Rig to hear it. A single click on the
   preset that is already loaded does nothing — Guitar Rig serves it from memory. Say this
   every time, otherwise they will conclude the change failed.

6. **Ask what changed**, and iterate. If the cause turns out to sit outside Guitar Rig — input
   gain, old strings, buffer size, grounding — say so plainly instead of turning a knob that
   cannot fix it.
