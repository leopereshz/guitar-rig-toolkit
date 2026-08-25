# Symptom reference — Guitar Rig

Symptom → cause → action decision tree for Guitar Rig. Deltas are normalised 0–1 and represent ONE step, not a final value: apply, listen, repeat.

*Extracted from: 349 presets, 98 components, 1039 parameters.*

## Order of diagnosis

```
1. LEVEL        is it clipping? is there headroom?
2. NOISE        hiss, hum, feedback
3. TONE         frequency balance (EQ, cabinet, mic)
4. DYNAMICS     compression, sustain, touch response
5. SPACE        reverb, delay, stereo
```

Do not skip stages. Each one contaminates the next: adjusting EQ while the signal clips is pointless, because the harshness that bothers you is the clip, not the tone. Setting a gate before fixing excess gain masks the noise and eats sustain. Setting reverb before tone makes you compensate EQ with space, and the result sits distant and unfocused.

## Electric guitar frequency map

| Band | Hz | What it does |
|---|---|---|
| Sub | 20–60 | guitar does not live here; it only eats headroom |
| Weight | 60–120 | foundation. Missing = thin. Excess = boomy |
| Body | 120–250 | warmth. Missing = no body. Excess = covers the bass |
| Mud | 250–500 | **the mud zone**. Excess = woolly, undefined |
| Box | 500–800 | Excess = nasal, boxy, cardboard |
| Definition | 800–1500 | note attack. Missing = **lost in the mix** |
| Presence | 1500–3000 | intelligibility. Missing = **muffled** |
| Attack | 3000–5000 | pick bite. Excess = **harsh** |
| Brightness | 5000–8000 | Excess = **fizz, buzzsaw** |
| Air | 8000–20000 | under distortion this is mostly rubbish. A real speaker rolls off above ~5–6 kHz |

## Level

### Clipping, crackling, breaking up badly

**How people say it:** "clipping", "crackling", "popping", "breaking up badly", "distorting wrong", "spitting", "harsh on attack", "farting out"

**Measurement:** `peak_dbfs` >= -0.1 — reliably measurable

**Ear test:** Roll the guitar volume back halfway. If the harshness disappears instantly, it is clipping, not tone.

**interface input gain set too high**
> Outside Guitar Rig — Play the hardest chord you actually use; the input meter should peak between −12 and −6 dBFS, never in the red.

**preset output too hot**

- `Preset Volume.PV` **−0.08**

**gain stacking through the chain**

- `Skreamer.Vol` **−0.08** — *if value > 0.8*
- `Treble Booster.Bs` **−0.10** — *if value > 0.8*
- `Gain Booster.B` **−0.10** — *if value > 0.8*
- `CabPanel.Vol` **−0.08** — *if value > 0.8*
- `Cabinets & Mics.MV` **−0.08** — *if value > 0.8*
- `Matched Cabinet.MV` **−0.08** — *if value > 0.8*

**compressor makeup gain too high**

- `Tube Compressor.Out` **−0.08**

**input level inside the rack**

- `Input Level.v` **−0.08**
    acts ahead of every gain stage in the chain; fixes the cause, not the symptom
- `Input Level.o` **−0.05**

**Safety net**

- `Limiter.Lm` **= 0.87**
    a level ceiling; it is a safety net, not a fix

⚠️ Lowering PV does not help if the clip already happens at the interface input.

⚠️ Lowering preamp V1 reduces the clip AND the distortion. To drop level only, use master V2.

### Overall level too low (playing alone)

**How people say it:** "too quiet", "low volume", "weak", "no level"

**Measurement:** `rms_dbfs` < -20 with peak < -6 — reliably measurable

**Not to be confused with** → *Lost in the mix (with a band)*

**preset output too low**

- `Preset Volume.PV` **+0.08**
- `CabPanel.Vol` **+0.05**

**amp master too low**

- `V2|Mast` (any amp) **+0.05**

**volume pedal rolled back**

- `Volume Pedal.Vol` **+0.10**
- `Volume Pedal.Pd`
    check the pedal is not rolled down

⚠️ Do not raise preamp V1 to gain volume: that adds distortion. Use the master.

## Noise

### Hiss — steady high-pitched “ssss”

**How people say it:** "hiss", "hissing", "background noise", "noise when not playing", "ssssss"

**Measurement:** `noise_floor_dbfs` > -45 in silence — reliably measurable

**Ear test:** Halve V1/Gn. If the hiss drops with it, the chain is amplifying noise: treat the cause.

**excessive drive or preamp gain (root cause)**

- `Skreamer.Dr` **−0.10** — compensate with `Vol` +0.05
- `V1|Gn` (any amp) **−0.08** — compensate with `V2|Mast` +0.05
- `Treble Booster.Bs` **−0.10**

**no noise reduction in the chain**
> only after the root cause

- `Noise Reduction.T` **+0.05** — *repeat until hiss gone while you are not playing*
- `Noise Reduction.H` **+0.10** — *if hiss is high-pitched and constant*
- `Noise Reduction.R` **+0.10** — *if notes cut off abruptly*
- `Noise Gate.T` **+0.05** — *if Noise Reduction is absent*
- `Solid Dynamics.G8` **+0.05**
- `Solid Dynamics.G7` **−0.15**
    Range attenuates instead of muting: avoids the slamming-door effect

⚠️ Too high a threshold eats sustain — see “Notes cutting out”.

⚠️ A gate does not remove hiss while you play, only in the gaps.

### Hum — steady low-pitched buzz

**How people say it:** "hum", "buzz", "humming", "mains buzz", "low rumble"

**Measurement:** `energy_60_120_180hz` narrow peaks at the mains frequency — reliably measurable

**Ear test:** Turn your body while holding the guitar. If the level changes, it is electromagnetic pickup. Touch the strings: if it stops, it is grounding.

**electromagnetic interference**
> Outside Guitar Rig — Change position, move away from monitors, power supplies and chargers, check the grounding.

**workaround inside the preset**

- `EQ Parametric.G1` **−0.30** @ 60 Hz Q narrow
- `EQ Parametric.G2` **−0.25** @ 120 Hz Q narrow

⚠️ A gate is the wrong tool for hum: it destroys sustain and the hum returns under the note.

### Fizz — harsh hiss inside the distortion

**How people say it:** "fizz", "buzzsaw", "bees", "sand in the sound", "harsh hiss", "gritty distortion"

**Measurement:** `energy_above_6khz` excessive while notes ring — reliably measurable

**Distinguish from *Hiss — steady high-pitched “ssss”*:** fizz only appears while you play; hiss is constant and a gate removes it

**missing cabinet, or the wrong one**
> Confirm these exist in the chain: `Cabinets & Mics`, `Matched Cabinet`, `CabPanel`

- `CabPanel.Air` **−0.15**
- `CabPanel.MPos` **−0.15**
    move off the cone centre; the most effective control here
- `CabPanel.Trb` **−0.10**
- `Matched Cabinet.a` **−0.15**

**too much high frequency from the distortion**

- `EQ Parametric.G2` **−0.20** @ 7500 Hz Q medium
- `Skreamer.Dr` **−0.08**
- `Solid EQ.L13` @ 7000 Hz
    a low-pass drops everything above; better than a bell cut for fizz
- `Pro-Filter.F` @ 7000 Hz
    low-pass mode, high slope

⚠️ Lowering amp Treble also kills the useful attack at 3–4 kHz. Work on the cabinet and mic instead.

### Notes cutting out, chopping, dying early

**How people say it:** "notes cutting out", "chopping", "notes disappear", "cuts off at the end", "stuttering"

**Measurement:** `envelope_decay` abrupt drop instead of a smooth decay — partly measurable

**gate set too aggressively**

- `Noise Reduction.T` **−0.08**
- `Noise Reduction.R` **+0.10**
- `Noise Gate.T` **−0.08**
- `Noise Gate.H` **+0.10**
- `Noise Gate.R` **+0.10**
- `Solid Dynamics.G8` **−0.08**
- `Solid Dynamics.G11` **+0.10**
- `Solid Dynamics.G7` **−0.15**

⚠️ If you need a high threshold to hold back the hiss, the real problem is excess gain — see “Hiss”.

## Tone

### Muffled, dull, “blanket over the amp”

**How people say it:** "muffled", "dull", "blanket over the amp", "no top end", "dark", "no definition up top"

**Measurement:** `energy_2k_5k+spectral_centroid` low — reliably measurable

- Rule out first: guitar tone control rolled off
- Rule out first: neck pickup selected
- Rule out first: old strings
- Rule out first: poor headphones or monitors

**dark mic placement**

- `CabPanel.MPos` **+0.15**
    mic toward the cone centre; the most powerful control and the least obvious
- `CabPanel.Dst` **−0.10**
- `CabPanel.Trb` **+0.10**
- `CabPanel.Air` **+0.10**

**not enough presence or treble from the amp**

- `Pr|Prs|p` (any amp) **+0.10**
- `T|Trb|t` (any amp) **+0.08**
- `Skreamer.Br` **+0.10**
- `Skreamer.Tn` **+0.10**

**equalisation**

- `EQ Shelving.G2` **+0.15** @ 3000 Hz
- `EQ Parametric.G1` **+0.15** @ 2500 Hz Q wide

⚠️ If mud at 250–500 Hz is masking the top, adding treble makes it bright AND muddy. Check “Muddy” first.

### Harsh, too bright, fatiguing

**How people say it:** "harsh", "too bright", "hurts the ears", "fatiguing", "piercing", "in your face"

**Measurement:** `energy_3k_6k` excessive peak — reliably measurable

**Distinguish from *Fizz — harsh hiss inside the distortion*:** harshness bites on the attack, around 3–5 kHz; fizz is continuous noise above 6 kHz

**presence too high**

- `Pr|Prs|p` (any amp) **−0.10**

**bright mic placement**

- `CabPanel.MPos` **−0.15**
- `CabPanel.Trb` **−0.10**
- `CabPanel.Air` **−0.10**

**treble boost in the chain**

- `Treble Booster.Bs` **−0.15**
- `Skreamer.Tn` **−0.10**
- `T|Trb|t` (any amp) **−0.08**

**surgical cut**

- `EQ Parametric.G1` **−0.20** @ 3500 Hz (sweep 2500–5000 Hz) Q medium

### Muddy, woolly, no definition in the low end

**How people say it:** "muddy", "boomy", "woolly", "too heavy", "no definition", "smeared"

**Measurement:** `energy_250_500` excessive — reliably measurable

**excess in the mud zone**

- `EQ Parametric.G1` **−0.20** @ 350 Hz (sweep 250–500 Hz) Q medium
    the single most transformative cut on electric guitar
- `B|Bs|b` (any amp) **−0.10**
- `CabPanel.Bs` **−0.10**
- `EQ Shelving.G1` **−0.15** @ 100 Hz
- `Skreamer.Bs` **−0.10**
- `Skreamer.Dr` **−0.08**
- `EQ Graphic.b2` **−0.15**
    set mi/ma to cover the 100–1000 Hz range
- `EQ Graphic.b3` **−0.15**
- `Solid EQ.H12` @ 85 Hz
    a high-pass clears the sub that only eats headroom

⚠️ Mud at 250–500 Hz gets mistaken for “too much bass”. Cutting at 80 Hz does not fix it and leaves the sound thin.

### Boxy, nasal, telephone-like

**How people say it:** "boxy", "nasal", "cardboard box", "telephone sound", "honky"

**Measurement:** `energy_500_900` peak — reliably measurable

**box resonance**

- `EQ Parametric.G1` **−0.20** @ 700 Hz (sweep 500–900 Hz) Q medium-narrow
- `M|Mid|m` (any amp) **−0.10**
- `CabPanel.Sz` **+0.10**
- `CabPanel.Dst` **+0.10**

### Thin, weedy, no body

**How people say it:** "thin", "weedy", "no body", "no weight", "brittle", "no low end"

**Measurement:** `energy_100_250` low — reliably measurable

**missing body**

- `B|Bs|b` (any amp) **+0.10**
- `CabPanel.Bs` **+0.10**
- `CabPanel.Sz` **+0.10**
- `CabPanel.Dst` **+0.08**
- `EQ Shelving.G1` **+0.15** @ 150 Hz
- `Skreamer.Bs` **+0.10**
- `Skreamer.Cl` **+0.10**
- `Hot Solo+.D8` **+0.10**
- `Van 51.R6` **+0.10**

⚠️ Body lives at 100–250 Hz; mud at 250–500 Hz. If it got heavy AND woolly, you aimed at the wrong band.

### Lost in the mix (with a band)

**How people say it:** "lost in the mix", "disappears with the band", "does not cut through", "buried", "guitar sits behind"

**Measurement:** `energy_800_2k_relative` low — partly measurable

> Only meaningful while listening to the full mix, never to the guitar soloed.

**Not to be confused with** → *Overall level too low (playing alone)*

**the guitar's own band is empty**

- `EQ Parametric.G1` **+0.15** @ 1200 Hz (sweep 800–2000 Hz) Q wide
- `M|Mid|m` (any amp) **+0.10**
- `Pr|Prs|p` (any amp) **+0.08**

**guitar competing with the bass**

- `EQ Shelving.G1` **−0.15** @ 100 Hz

**reverb pushing it backwards**

- `Studio Reverb.Wet` **−0.10**

⚠️ A scooped tone sounds impressive soloed and is the worst possible choice in a mix. Keep a separate preset for each situation.

### Palm mutes with no punch, floppy low string

**How people say it:** "palm mutes have no punch", "floppy low string", "no chug", "soft low end", "no thump"

**Measurement:** `attack_transient` slow — needs your ears

**uncontrolled low end smearing the attack**

- `EQ Parametric.G1` **−0.15** @ 90 Hz Q narrow
- `Skreamer.Dr` **= 0.2**
    low drive with high level: cuts bass before the distortion, the classic Tube Screamer trick
- `Skreamer.Vol` **= 0.8**

**slow amp response**

- `Rsp` (any amp) **+0.10**
- `Sg` (any amp) **−0.10**
- `Var` (any amp) **+0.10**
- `Bi` (any amp) **+0.10**

## Dynamics

### Not enough gain, too clean

**How people say it:** "not enough gain", "too clean", "no drive", "distortion has no weight", "weak"

**insufficient gain**

- `V1|Gn` (any amp) **+0.10** — compensate with `V2|Mast` −0.05
- `Skreamer.Dr` **+0.15**
- `Treble Booster.Bs` **+0.15**
- `Gain Booster.B` **+0.15**
- `Lead 800.Hg` **= 1**
- `Jump.Hg` **= 1**
- `Van 51.H14` **= 1**
- `Citrus.Br` **= 1**
- `Big Fuzz.S` **+0.15**
    fuzz is a different category, not “more distortion”
- `Fuzz.F` **+0.15**

⚠️ Amps that are clean by design (Twang Reverb, AC Box, Tweedman, Jazz Amp, Tweed Delight) do not become high gain no matter the setting. Change amp.

⚠️ The high-gain ones: Gratifier, Van 51, Rammfire, Sledgehammer, MeZone.

### Mushy, distortion with no definition

**How people say it:** "mushy", "too much gain", "mush", "smeared", "chords turn to soup", "no separation"

**excessive gain**

- `V1|Gn` (any amp) **−0.10** — compensate with `V2|Mast` +0.05
- `Skreamer.Dr` **−0.10**

**too much bass hitting the distortion**

- `Skreamer.Bs` **−0.10**
    the number one cause of mush
- `M|Mid|m` (any amp) **+0.08**
- `Bi` (any amp) **+0.08**
- `Sg` (any amp) **−0.08**

### No sustain, notes die fast

**How people say it:** "no sustain", "notes die fast", "does not hold", "dry"

**Check first** → *Notes cutting out, chopping, dying early*

**not enough compression**

- `Tube Compressor.Th` **−0.10**
- `Tube Compressor.Rt` **+0.10**
- `Tube Compressor.Rl` **+0.10**
- `Stomp Compressor.S` **+0.15**
- `Sg` (any amp) **+0.10**

### Squashed, no response to touch

**How people say it:** "squashed", "no dynamics", "does not respond to touch", "everything at one volume", "no expression"

**excessive compression**

- `Tube Compressor.Rt` **−0.10**
- `Tube Compressor.Th` **+0.10**
- `Tube Compressor.Dyn` **+0.10**
- `Stomp Compressor.S` **−0.15**
- `Fast Comp.I0` **−0.10**

**high gain acting as a compressor**

- `V1|Gn` (any amp) **−0.10**
- `Sg` (any amp) **−0.10**
- `Rsp` (any amp) **+0.10**

### Pick attack too strong, clicking

**How people say it:** "pick click", "attack too strong", "pick noise", "aggressive attack"

**uncontrolled transient**

- `Tube Compressor.Att` **−0.10**
- `EQ Parametric.G1` **−0.12** @ 2500 Hz
- `CabPanel.MPos` **−0.10**

## Space

### Distant, washed out, “down a well”

**How people say it:** "distant", "washed out", "down a well", "too wet", "too much reverb", "far away"

**too much space**

- `Studio Reverb.Wet` **−0.15**
- `Studio Reverb.Sz` **−0.10**
- `Spring Reverb.Wet` **−0.15**
- `Quad Delay.W` **−0.10**
- `Delay Man.m` **−0.10**
- `Little Reflektor.W1` **−0.15**

⚠️ Reverb is the biggest single reason a guitar vanishes in a mix. Use less than feels right when playing alone.

### Reverb or delay muddying the low end

**How people say it:** "muddy reverb", "dirty tail", "echo too bassy"

**too much low end in the tail**

- `Spring Reverb.B` **−0.15**
- `Little Reflektor.L4` **+0.15**
- `Quad Delay.LP` **−0.10**
- `Studio Reverb.L` **−0.10**

### Disappears or goes hollow in mono

**How people say it:** "disappears in mono", "odd stereo", "hollow", "phasey", "vanished on the phone"

**Measurement:** `stereo_correlation` < 0 — reliably measurable

**phase cancellation**

- `Split Mix.iP` toggle 0/1
- `CabPanel.Phs` toggle 0/1
- `Control Room Pro.pi1` toggle 0/1
    check mic by mic, pi1 through pi8
- `CrossOver Mix.iP` toggle 0/1
    presets using CrossOver split by frequency; the high half may be inverted
- `Matched Cabinet.st` **−0.15**

### Stereo too wide, unstable

**How people say it:** "stereo too wide", "unstable", "sound wandering", "too spread out"

**excessive width**

- `Split Mix.XFade`
    bring PanA/PanB closer to centre
- `Matched Cabinet.st` **−0.15**
- `Flanger.St` **−0.15**
- `Ensemble.S` **−0.15**
- `Stereo Tune.S3` **−0.15**
    this component exists only for width; check it first
- `Stereo Tune.D1` **−0.10**

## Causes outside Guitar Rig

| Symptom | Likely cause | Where to fix it |
|---|---|---|
| delay between playing and hearing | buffer too large, or the wrong driver | Audio Settings: use ASIO, buffer 128–256 |
| intermittent clicks and dropouts | buffer too small for the CPU | increase the buffer |
| clipping at the input | interface gain | the gain knob on the interface |
| hum that changes as you move | electromagnetic pickup | position, grounding, shielding |
| muffled in every preset | old strings or a rolled-off tone control | the guitar |
| hiss even at low gain | bad cable or a noisy pickup | replace the cable |

## Common amp parameters

```
V1|Gn        input / preamp gain — how much distortion
V2|Mast      output / master volume — level without changing distortion
B|Bs|b       Bass
M|Mid|m      Mid
T|Trb|t      Treble
Pr|Prs|p     Presence — acts in the power stage, sounds different from treble
Sg           Sag — natural power-supply compression
Rsp          Response — how fast the amp reacts
Bi           Bias — asymmetry of the distortion
Var          Variac — supply voltage; tightens the sound
Hg           built-in boost (Lead 800, Jump)
```

**Exceptions — on these amps V1/V2 do not mean gain and master**

- **Plex** — V1 = Bright Volume, V2 = Warm Volume — two channels summed, not gain + master
- **Cool Plex** — same as Plex
- **Van 51** — R0 = Rhythm Pre Gain, L1 = Lead Pre Gain, P5 = Post Gain, H14 = HiGainInput
- **AC Box** — Vol = Normal Volume, Br = Brilliant Volume — two channels
- **High White** — nv = Normal Vol, bv = Brilliant Vol, Mst = Master
- **Tweedman** — VB = Volume Bright, VN = Volume Normal
- **Gratifier** — Gn = Gain, Mast = Master; M is Mode, not Mid
- **Rammfire** — Gn = Gain, Mast = Master; M is Mode, not Mid
- **Ultrasonic** — g = Gain, v = Volume, Mst = Master
- **Hot Solo+** — P0 = Normal, P1 = Overdrive, M6 = Master, O2 selects the channel
- **Citrus** — g = Gain, m = Master
- **Hot Plex** — same as Plex
- **Tweed Delight** — vb = Volume Bright, vn = Volume Normal; only t = Tone, no B/M/T
- **Sledgehammer** — g = Gain, v = Volume; c = Contour with f = Frequency form a sweepable mid
- **MeZone** — D = Distortion, V = Volume; the only one with PRE-distortion EQ (PB, PQ, PM, PT)
- **Jazz Amp** — V = Volume; clean by design, em = Ensemble Mode
- **Bass Pro** — G = Gain, D = Drive, V = Volume; graphic EQ with bands labelled in Hz
- **TransAmp** — D = Drive, V = Volume; A selects the amp, CM enables cab & mic

---

Deltas are **one step**, not a final value. Apply, listen, repeat. Frequencies in Hz are targets; the matching parameter is normalised 0–1 and the exact mapping was not decoded — set it on screen. Components named here may not exist in the preset you are using.
