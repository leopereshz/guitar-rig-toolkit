# Référence des symptômes — Guitar Rig

Arbre de diagnostic symptôme → cause → action pour Guitar Rig. Les deltas sont normalisés 0–1 et représentent UN pas, pas une valeur finale : applique, écoute, recommence.

*Extrait de: 349 presets, 98 composants, 1039 paramètres.*

## Ordre de diagnostic

```
1. NIVEAU       ça écrête ? reste-t-il de la marge ?
2. BRUIT        souffle, ronflement, larsen
3. TIMBRE       équilibre des fréquences (EQ, baffle, micro)
4. DYNAMIQUE    compression, sustain, réponse au toucher
5. ESPACE       réverbération, delay, stéréo
```

Ne saute pas d'étape. Chacune contamine la suivante : régler l'EQ pendant que le signal écrête ne sert à rien, car la dureté qui gêne est l'écrêtage, pas le timbre. Poser un gate avant de régler l'excès de gain masque le bruit et mange le sustain. Régler la réverbération avant le timbre pousse à compenser l'EQ par de l'espace, et le résultat reste lointain et flou.

## Carte des fréquences de la guitare électrique

| Bande | Hz | Ce qu'elle fait |
|---|---|---|
| Sub | 20–60 | la guitare n'y vit pas ; ça ne fait que consommer de la marge |
| Poids | 60–120 | fondation. Manque = maigre. Excès = boomy |
| Corps | 120–250 | chaleur. Manque = sans corps. Excès = couvre la basse |
| Boue | 250–500 | **la zone de boue**. Excès = empâté, sans définition |
| Caisse | 500–800 | Excès = nasillard, en boîte, carton |
| Définition | 800–1500 | attaque de note. Manque = **perdue dans le mix** |
| Présence | 1500–3000 | intelligibilité. Manque = **étouffé** |
| Attaque | 3000–5000 | mordant du médiator. Excès = **agressif** |
| Brillance | 5000–8000 | Excès = **fizz, scie** |
| Air | 8000–20000 | sous distorsion, c'est presque uniquement du déchet. Un vrai haut-parleur coupe au-dessus de ~5–6 kHz |

## Niveau

### Ça sature, ça crépite, ça casse

**Comment on le dit:** "ça sature", "ça crépite", "ça craque", "ça casse", "distorsion moche", "ça crache", "agressif à l'attaque"

**Mesure:** `peak_dbfs` >= -0.1 — mesurable de façon fiable

**Test à l'oreille:** Baisse le volume de la guitare de moitié. Si la dureté disparaît aussitôt, c'est de l'écrêtage, pas le timbre.

**gain d'entrée de l'interface trop élevé**
> Hors de Guitar Rig — Joue l'accord le plus fort que tu utilises vraiment ; l'indicateur d'entrée doit culminer entre −12 et −6 dBFS, jamais dans le rouge.

**sortie du preset trop forte**

- `Preset Volume.PV` **−0.08**

**accumulation de gain dans la chaîne**

- `Skreamer.Vol` **−0.08** — *si valeur > 0.8*
- `Treble Booster.Bs` **−0.10** — *si valeur > 0.8*
- `Gain Booster.B` **−0.10** — *si valeur > 0.8*
- `CabPanel.Vol` **−0.08** — *si valeur > 0.8*
- `Cabinets & Mics.MV` **−0.08** — *si valeur > 0.8*
- `Matched Cabinet.MV` **−0.08** — *si valeur > 0.8*

**gain de compensation du compresseur trop élevé**

- `Tube Compressor.Out` **−0.08**

**niveau d'entrée dans le rack**

- `Input Level.v` **−0.08**
    agit avant tout le gain de la chaîne ; corrige la cause, pas le symptôme
- `Input Level.o` **−0.05**

**Filet de sécurité**

- `Limiter.Lm` **= 0.87**
    plafond de niveau ; c'est un filet de sécurité, pas une solution

⚠️ Baisser PV ne sert à rien si l'écrêtage a déjà lieu à l'entrée de l'interface.

⚠️ Baisser le préampli V1 réduit l'écrêtage ET la distorsion. Pour ne baisser que le niveau, utilise le master V2.

### Niveau général trop faible (en jouant seul)

**Comment on le dit:** "volume faible", "ça sort faible", "trop discret", "pas de niveau"

**Mesure:** `rms_dbfs` < -20 avec crête < -6 — mesurable de façon fiable

**À ne pas confondre avec** → *Perdue dans le mix (avec un groupe)*

**sortie du preset faible**

- `Preset Volume.PV` **+0.08**
- `CabPanel.Vol` **+0.05**

**master de l'ampli trop bas**

- `V2|Mast` (n'importe quel ampli) **+0.05**

**pédale de volume baissée**

- `Volume Pedal.Vol` **+0.10**
- `Volume Pedal.Pd`
    vérifie que la pédale n'est pas baissée

⚠️ Ne monte pas le préampli V1 pour gagner du volume : ça ajoute de la distorsion. Utilise le master.

## Bruit

### Souffle — chuintement aigu et constant

**Comment on le dit:** "souffle", "bruit de fond", "ça souffle", "bruit quand je ne joue pas", "chuintement"

**Mesure:** `noise_floor_dbfs` > -45 en silence — mesurable de façon fiable

**Test à l'oreille:** Baisse V1/Gn de moitié. Si le souffle baisse avec, la chaîne amplifie du bruit : traite la cause.

**drive ou préampli excessif (cause racine)**

- `Skreamer.Dr` **−0.10** — compense avec `Vol` +0.05
- `V1|Gn` (n'importe quel ampli) **−0.08** — compense avec `V2|Mast` +0.05
- `Treble Booster.Bs` **−0.10**

**pas de réduction de bruit dans la chaîne**
> seulement après la cause racine

- `Noise Reduction.T` **+0.05** — *répète jusqu'à ce que le souffle disparaisse quand tu ne joues pas*
- `Noise Reduction.H` **+0.10** — *si le souffle est aigu et continu*
- `Noise Reduction.R` **+0.10** — *si les notes se coupent net*
- `Noise Gate.T` **+0.05** — *si Noise Reduction absent*
- `Solid Dynamics.G8` **+0.05**
- `Solid Dynamics.G7` **−0.15**
    Range atténue au lieu de couper : évite l'effet de porte qui claque

⚠️ Un seuil trop haut mange le sustain — voir “Notes qui se coupent”.

⚠️ Un gate ne supprime pas le souffle pendant que tu joues, seulement dans les silences.

### Ronflement — grave et constant

**Comment on le dit:** "ronflement", "bourdonnement", "ça ronfle", "bruit grave"

**Mesure:** `energy_60_120_180hz` pics étroits à la fréquence du secteur — mesurable de façon fiable

**Test à l'oreille:** Tourne-toi avec la guitare en main. Si l'intensité change, c'est une captation électromagnétique. Touche les cordes : si ça s'arrête, c'est la masse.

**interférence électromagnétique**
> Hors de Guitar Rig — Change de position, éloigne-toi des enceintes, alimentations et chargeurs, vérifie la mise à la masse.

**palliatif dans le preset**

- `EQ Parametric.G1` **−0.30** @ 60 Hz Q étroit
- `EQ Parametric.G2` **−0.25** @ 120 Hz Q étroit

⚠️ Le gate est le mauvais outil contre le ronflement : il détruit le sustain et le ronflement revient sous la note.

### Fizz — souffle aigu dans la distorsion

**Comment on le dit:** "scie électrique", "abeilles", "du sable dans le son", "souffle aigu", "distorsion rêche"

**Mesure:** `energy_above_6khz` excessive pendant que les notes sonnent — mesurable de façon fiable

**Distinguer de *Souffle — chuintement aigu et constant*:** le fizz n'apparaît que pendant le jeu ; le souffle est constant et le gate l'élimine

**baffle absent, ou mauvais baffle**
> Confirme leur présence dans la chaîne: `Cabinets & Mics`, `Matched Cabinet`, `CabPanel`

- `CabPanel.Air` **−0.15**
- `CabPanel.MPos` **−0.15**
    éloigne-toi du centre du cône ; le contrôle le plus efficace ici
- `CabPanel.Trb` **−0.10**
- `Matched Cabinet.a` **−0.15**

**excès d'aigus produit par la distorsion**

- `EQ Parametric.G2` **−0.20** @ 7500 Hz Q moyen
- `Skreamer.Dr` **−0.08**
- `Solid EQ.L13` @ 7000 Hz
    un passe-bas fait tomber tout ce qui est au-dessus ; mieux qu'une cloche pour le fizz
- `Pro-Filter.F` @ 7000 Hz
    mode passe-bas, pente élevée

⚠️ Baisser le Treble de l'ampli tue aussi l'attaque utile vers 3–4 kHz. Travaille plutôt le baffle et le micro.

### Notes qui se coupent, décrochent ou meurent tôt

**Comment on le dit:** "les notes se coupent", "ça décroche", "les notes disparaissent", "coupe à la fin", "ça bégaie"

**Mesure:** `envelope_decay` chute brutale au lieu d'une décroissance douce — partiellement mesurable

**gate trop agressif**

- `Noise Reduction.T` **−0.08**
- `Noise Reduction.R` **+0.10**
- `Noise Gate.T` **−0.08**
- `Noise Gate.H` **+0.10**
- `Noise Gate.R` **+0.10**
- `Solid Dynamics.G8` **−0.08**
- `Solid Dynamics.G11` **+0.10**
- `Solid Dynamics.G7` **−0.15**

⚠️ S'il te faut un seuil élevé pour contenir le souffle, le vrai problème est l'excès de gain — voir “Souffle”.

## Timbre

### Étouffé, terne, “une couverture sur l'ampli”

**Comment on le dit:** "étouffé", "sans brillance", "une couverture sur l'ampli", "sourd", "terne", "pas de définition dans l'aigu"

**Mesure:** `energy_2k_5k+spectral_centroid` faible — mesurable de façon fiable

- Écarte d'abord: tonalité de la guitare fermée
- Écarte d'abord: micro manche sélectionné
- Écarte d'abord: cordes usées
- Écarte d'abord: casque ou enceintes médiocres

**placement de micro sombre**

- `CabPanel.MPos` **+0.15**
    micro vers le centre du cône ; le contrôle le plus puissant et le moins évident
- `CabPanel.Dst` **−0.10**
- `CabPanel.Trb` **+0.10**
- `CabPanel.Air` **+0.10**

**manque de présence ou d'aigus côté ampli**

- `Pr|Prs|p` (n'importe quel ampli) **+0.10**
- `T|Trb|t` (n'importe quel ampli) **+0.08**
- `Skreamer.Br` **+0.10**
- `Skreamer.Tn` **+0.10**

**égalisation**

- `EQ Shelving.G2` **+0.15** @ 3000 Hz
- `EQ Parametric.G1` **+0.15** @ 2500 Hz Q large

⚠️ Si de la boue à 250–500 Hz masque l'aigu, monter le treble rend le son brillant ET boueux. Vérifie “Boueux” d'abord.

### Agressif, trop aigu, fatigant

**Comment on le dit:** "agressif", "trop aigu", "ça fait mal aux oreilles", "fatigant", "criard", "en pleine face"

**Mesure:** `energy_3k_6k` pic excessif — mesurable de façon fiable

**Distinguer de *Fizz — souffle aigu dans la distorsion*:** l'agressivité mord sur l'attaque, vers 3–5 kHz ; le fizz est un bruit continu au-dessus de 6 kHz

**présence trop élevée**

- `Pr|Prs|p` (n'importe quel ampli) **−0.10**

**placement de micro brillant**

- `CabPanel.MPos` **−0.15**
- `CabPanel.Trb` **−0.10**
- `CabPanel.Air` **−0.10**

**boost d'aigus dans la chaîne**

- `Treble Booster.Bs` **−0.15**
- `Skreamer.Tn` **−0.10**
- `T|Trb|t` (n'importe quel ampli) **−0.08**

**coupe chirurgicale**

- `EQ Parametric.G1` **−0.20** @ 3500 Hz (balaye 2500–5000 Hz) Q moyen

### Boueux, sans définition dans le grave

**Comment on le dit:** "boueux", "empâté", "sale dans le grave", "trop lourd", "sans définition", "brouillon"

**Mesure:** `energy_250_500` excessive — mesurable de façon fiable

**excès dans la zone de boue**

- `EQ Parametric.G1` **−0.20** @ 350 Hz (balaye 250–500 Hz) Q moyen
    la coupe qui transforme le plus une guitare électrique
- `B|Bs|b` (n'importe quel ampli) **−0.10**
- `CabPanel.Bs` **−0.10**
- `EQ Shelving.G1` **−0.15** @ 100 Hz
- `Skreamer.Bs` **−0.10**
- `Skreamer.Dr` **−0.08**
- `EQ Graphic.b2` **−0.15**
    règle mi/ma pour couvrir la plage 100–1000 Hz
- `EQ Graphic.b3` **−0.15**
- `Solid EQ.H12` @ 85 Hz
    un passe-haut nettoie le sub qui ne fait que consommer de la marge

⚠️ La boue de 250–500 Hz est confondue avec “trop de basses”. Couper à 80 Hz ne règle rien et rend le son maigre.

### Nasillard, en boîte, son de téléphone

**Comment on le dit:** "nasillard", "en boîte", "carton", "son de téléphone", "pincé"

**Mesure:** `energy_500_900` pic — mesurable de façon fiable

**résonance de caisse**

- `EQ Parametric.G1` **−0.20** @ 700 Hz (balaye 500–900 Hz) Q moyen-étroit
- `M|Mid|m` (n'importe quel ampli) **−0.10**
- `CabPanel.Sz` **+0.10**
- `CabPanel.Dst` **+0.10**

### Maigre, fluet, sans corps

**Comment on le dit:** "maigre", "fluet", "sans corps", "sans poids", "cassant", "pas de grave"

**Mesure:** `energy_100_250` faible — mesurable de façon fiable

**manque de corps**

- `B|Bs|b` (n'importe quel ampli) **+0.10**
- `CabPanel.Bs` **+0.10**
- `CabPanel.Sz` **+0.10**
- `CabPanel.Dst` **+0.08**
- `EQ Shelving.G1` **+0.15** @ 150 Hz
- `Skreamer.Bs` **+0.10**
- `Skreamer.Cl` **+0.10**
- `Hot Solo+.D8` **+0.10**
- `Van 51.R6` **+0.10**

⚠️ Le corps est à 100–250 Hz ; la boue à 250–500 Hz. Si c'est devenu lourd ET empâté, tu as visé la mauvaise bande.

### Perdue dans le mix (avec un groupe)

**Comment on le dit:** "perdue dans le mix", "disparaît avec le groupe", "ne passe pas", "enterrée", "la guitare reste derrière"

**Mesure:** `energy_800_2k_relative` faible — partiellement mesurable

> N'a de sens qu'en écoutant le mix complet, jamais la guitare seule.

**À ne pas confondre avec** → *Niveau général trop faible (en jouant seul)*

**la bande propre à la guitare est vide**

- `EQ Parametric.G1` **+0.15** @ 1200 Hz (balaye 800–2000 Hz) Q large
- `M|Mid|m` (n'importe quel ampli) **+0.10**
- `Pr|Prs|p` (n'importe quel ampli) **+0.08**

**la guitare se bat avec la basse**

- `EQ Shelving.G1` **−0.15** @ 100 Hz

**la réverbération la repousse en arrière**

- `Studio Reverb.Wet` **−0.10**

⚠️ Un timbre “scooped” impressionne en solo et c'est le pire choix possible dans un mix. Garde un preset distinct pour chaque situation.

### Palm mutes sans impact, corde grave molle

**Comment on le dit:** "les palm mutes ne claquent pas", "corde grave molle", "pas de chug", "grave mou", "pas d'impact"

**Mesure:** `attack_transient` lent — dépend de tes oreilles

**grave incontrôlé qui brouille l'attaque**

- `EQ Parametric.G1` **−0.15** @ 90 Hz Q étroit
- `Skreamer.Dr` **= 0.2**
    drive bas et niveau haut : coupe le grave avant la distorsion, l'usage classique du Tube Screamer
- `Skreamer.Vol` **= 0.8**

**réponse lente de l'ampli**

- `Rsp` (n'importe quel ampli) **+0.10**
- `Sg` (n'importe quel ampli) **−0.10**
- `Var` (n'importe quel ampli) **+0.10**
- `Bi` (n'importe quel ampli) **+0.10**

## Dynamique

### Pas assez de gain, trop clean

**Comment on le dit:** "pas assez de gain", "trop clean", "pas de drive", "la distorsion manque de poids", "faible"

**gain insuffisant**

- `V1|Gn` (n'importe quel ampli) **+0.10** — compense avec `V2|Mast` −0.05
- `Skreamer.Dr` **+0.15**
- `Treble Booster.Bs` **+0.15**
- `Gain Booster.B` **+0.15**
- `Lead 800.Hg` **= 1**
- `Jump.Hg` **= 1**
- `Van 51.H14` **= 1**
- `Citrus.Br` **= 1**
- `Big Fuzz.S` **+0.15**
    le fuzz est une autre catégorie, pas “plus de distorsion”
- `Fuzz.F` **+0.15**

⚠️ Les amplis clairs par conception (Twang Reverb, AC Box, Tweedman, Jazz Amp, Tweed Delight) ne deviennent pas high gain quoi que tu règles. Change d'ampli.

⚠️ Les amplis à fort gain : Gratifier, Van 51, Rammfire, Sledgehammer, MeZone.

### Pâteux, distorsion sans définition

**Comment on le dit:** "pâteux", "trop de distorsion", "bouillie", "brouillon", "les accords deviennent une soupe", "pas de séparation"

**gain excessif**

- `V1|Gn` (n'importe quel ampli) **−0.10** — compense avec `V2|Mast` +0.05
- `Skreamer.Dr` **−0.10**

**trop de grave à l'entrée de la distorsion**

- `Skreamer.Bs` **−0.10**
    la cause numéro un du côté pâteux
- `M|Mid|m` (n'importe quel ampli) **+0.08**
- `Bi` (n'importe quel ampli) **+0.08**
- `Sg` (n'importe quel ampli) **−0.08**

### Pas de sustain, les notes meurent vite

**Comment on le dit:** "pas de sustain", "la note meurt vite", "ça ne tient pas", "sec"

**Vérifie d'abord** → *Notes qui se coupent, décrochent ou meurent tôt*

**manque de compression**

- `Tube Compressor.Th` **−0.10**
- `Tube Compressor.Rt` **+0.10**
- `Tube Compressor.Rl` **+0.10**
- `Stomp Compressor.S` **+0.15**
- `Sg` (n'importe quel ampli) **+0.10**

### Écrasé, ne répond pas au toucher

**Comment on le dit:** "écrasé", "sans dynamique", "ne répond pas au toucher", "tout au même volume", "sans expression"

**compression excessive**

- `Tube Compressor.Rt` **−0.10**
- `Tube Compressor.Th` **+0.10**
- `Tube Compressor.Dyn` **+0.10**
- `Stomp Compressor.S` **−0.15**
- `Fast Comp.I0` **−0.10**

**gain élevé qui agit comme un compresseur**

- `V1|Gn` (n'importe quel ampli) **−0.10**
- `Sg` (n'importe quel ampli) **−0.10**
- `Rsp` (n'importe quel ampli) **+0.10**

### Attaque de médiator trop forte, clic

**Comment on le dit:** "clic de médiator", "attaque trop forte", "bruit de médiator", "attaque agressive"

**transitoire non maîtrisé**

- `Tube Compressor.Att` **−0.10**
- `EQ Parametric.G1` **−0.12** @ 2500 Hz
- `CabPanel.MPos` **−0.10**

## Espace

### Lointain, délavé, “au fond d'un puits”

**Comment on le dit:** "lointain", "délavé", "au fond d'un puits", "trop mouillé", "trop de réverbération", "loin"

**trop d'espace**

- `Studio Reverb.Wet` **−0.15**
- `Studio Reverb.Sz` **−0.10**
- `Spring Reverb.Wet` **−0.15**
- `Quad Delay.W` **−0.10**
- `Delay Man.m` **−0.10**
- `Little Reflektor.W1` **−0.15**

⚠️ La réverbération est la première raison pour laquelle une guitare disparaît dans un mix. Mets-en moins que ce qui semble juste en jouant seul.

### Réverbération ou delay qui embrouille le grave

**Comment on le dit:** "réverbération boueuse", "queue sale", "écho trop grave"

**trop de grave dans la queue**

- `Spring Reverb.B` **−0.15**
- `Little Reflektor.L4` **+0.15**
- `Quad Delay.LP` **−0.10**
- `Studio Reverb.L` **−0.10**

### Disparaît ou sonne creux en mono

**Comment on le dit:** "disparaît en mono", "stéréo bizarre", "son creux", "problème de phase", "a disparu sur le téléphone"

**Mesure:** `stereo_correlation` < 0 — mesurable de façon fiable

**annulation de phase**

- `Split Mix.iP` bascule 0/1
- `CabPanel.Phs` bascule 0/1
- `Control Room Pro.pi1` bascule 0/1
    vérifie micro par micro, de pi1 à pi8
- `CrossOver Mix.iP` bascule 0/1
    les presets avec CrossOver séparent par fréquence ; la moitié aiguë peut être inversée
- `Matched Cabinet.st` **−0.15**

### Stéréo trop large, instable

**Comment on le dit:** "stéréo trop large", "instable", "le son se balade", "trop dispersé"

**largeur excessive**

- `Split Mix.XFade`
    rapproche PanA/PanB du centre
- `Matched Cabinet.st` **−0.15**
- `Flanger.St` **−0.15**
- `Ensemble.S` **−0.15**
- `Stereo Tune.S3` **−0.15**
    ce composant n'existe que pour la largeur ; à vérifier en premier
- `Stereo Tune.D1` **−0.10**

## Causes hors de Guitar Rig

| Symptôme | Cause probable | Où le régler |
|---|---|---|
| décalage entre le jeu et le son | buffer trop grand, ou mauvais pilote | Audio Settings : ASIO, buffer 128–256 |
| clics et coupures intermittents | buffer trop petit pour le processeur | augmente le buffer |
| écrêtage à l'entrée | gain de l'interface | le potentiomètre de gain de l'interface |
| ronflement qui change quand tu bouges | captation électromagnétique | position, mise à la masse, blindage |
| étouffé sur tous les presets | cordes usées ou tonalité fermée | la guitare |
| souffle même à faible gain | mauvais câble ou micro bruyant | change le câble |

## Paramètres communs des amplis

```
V1|Gn        gain d'entrée / préampli — la quantité de distorsion
V2|Mast      volume de sortie / master — le niveau sans changer la distorsion
B|Bs|b       Bass
M|Mid|m      Mid
T|Trb|t      Treble
Pr|Prs|p     Presence — agit dans l'étage de puissance, sonne différemment du treble
Sg           Sag — compression naturelle de l'alimentation
Rsp          Response — vitesse de réaction de l'ampli
Bi           Bias — asymétrie de la distorsion
Var          Variac — tension d'alimentation ; resserre le son
Hg           boost intégré (Lead 800, Jump)
```

**Exceptions — sur ces amplis, V1/V2 ne veulent pas dire gain et master**

- **Plex** — V1 = Bright Volume, V2 = Warm Volume — deux canaux sommés, pas gain + master
- **Cool Plex** — comme le Plex
- **Van 51** — R0 = Rhythm Pre Gain, L1 = Lead Pre Gain, P5 = Post Gain, H14 = HiGainInput
- **AC Box** — Vol = Normal Volume, Br = Brilliant Volume — deux canaux
- **High White** — nv = Normal Vol, bv = Brilliant Vol, Mst = Master
- **Tweedman** — VB = Volume Bright, VN = Volume Normal
- **Gratifier** — Gn = Gain, Mast = Master ; M est Mode, pas Mid
- **Rammfire** — Gn = Gain, Mast = Master ; M est Mode, pas Mid
- **Ultrasonic** — g = Gain, v = Volume, Mst = Master
- **Hot Solo+** — P0 = Normal, P1 = Overdrive, M6 = Master, O2 sélectionne le canal
- **Citrus** — g = Gain, m = Master
- **Hot Plex** — comme le Plex
- **Tweed Delight** — vb = Volume Bright, vn = Volume Normal ; seulement t = Tone, pas de B/M/T
- **Sledgehammer** — g = Gain, v = Volume ; c = Contour avec f = Frequency forment un médium balayable
- **MeZone** — D = Distortion, V = Volume ; le seul avec une EQ AVANT la distorsion (PB, PQ, PM, PT)
- **Jazz Amp** — V = Volume ; clair par conception, em = Ensemble Mode
- **Bass Pro** — G = Gain, D = Drive, V = Volume ; EQ graphique avec des bandes libellées en Hz
- **TransAmp** — D = Drive, V = Volume ; A sélectionne l'ampli, CM active baffle et micro

---

Les deltas valent **un pas**, pas une valeur finale. Applique, écoute, recommence. Les fréquences en Hz sont des cibles ; le paramètre correspondant est normalisé 0–1 et la correspondance exacte n'a pas été décodée — règle-le à l'écran. Les composants cités peuvent ne pas exister dans le preset que tu utilises.
