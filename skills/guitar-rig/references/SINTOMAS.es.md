# Referencia de síntomas — Guitar Rig

Árbol de diagnóstico síntoma → causa → acción para Guitar Rig. Los deltas están normalizados 0–1 y representan UN paso, no un valor final: aplica, escucha, repite.

*Extraído de: 349 presets, 98 componentes, 1039 parámetros.*

## Orden de diagnóstico

```
1. NIVEL        ¿satura? ¿queda headroom?
2. RUIDO        siseo, zumbido, realimentación
3. TIMBRE       equilibrio de frecuencias (EQ, pantalla, micro)
4. DINÁMICA     compresión, sustain, respuesta al toque
5. ESPACIO      reverb, delay, estéreo
```

No te saltes etapas. Cada una contamina la siguiente: ajustar la EQ mientras la señal satura no sirve de nada, porque la aspereza que molesta es el recorte, no el timbre. Poner una puerta antes de resolver el exceso de ganancia enmascara el ruido y se come el sustain. Ajustar el reverb antes que el timbre te lleva a compensar EQ con espacio, y el resultado queda lejano y sin foco.

## Mapa de frecuencias de la guitarra eléctrica

| Banda | Hz | Qué hace |
|---|---|---|
| Sub | 20–60 | la guitarra no vive aquí; solo consume headroom |
| Peso | 60–120 | fundamento. Falta = delgado. Exceso = retumbante |
| Cuerpo | 120–250 | calidez. Falta = sin cuerpo. Exceso = tapa el bajo |
| Barro | 250–500 | **la zona del barro**. Exceso = atropellado, sin definición |
| Caja | 500–800 | Exceso = nasal, enlatado, cartón |
| Definición | 800–1500 | ataque de nota. Falta = **se pierde en la mezcla** |
| Presencia | 1500–3000 | inteligibilidad. Falta = **apagado** |
| Ataque | 3000–5000 | mordida de la púa. Exceso = **estridente** |
| Brillo | 5000–8000 | Exceso = **fizz, sierra** |
| Aire | 8000–20000 | con distorsión esto es casi solo basura. Un altavoz real corta por encima de ~5–6 kHz |

## Nivel

### Satura, crepita, rompe feo

**Cómo se dice:** "satura", "crepita", "chasquea", "rompe feo", "distorsiona mal", "escupe", "áspero en el ataque"

**Medición:** `peak_dbfs` >= -0.1 — medible con fiabilidad

**Prueba de oído:** Baja el volumen de la guitarra a la mitad. Si la aspereza desaparece al instante, es saturación digital, no timbre.

**ganancia de entrada de la interfaz demasiado alta**
> Fuera de Guitar Rig — Toca el acorde más fuerte que uses de verdad; el medidor de entrada debe llegar entre −12 y −6 dBFS, nunca al rojo.

**salida del preset demasiado alta**

- `Preset Volume.PV` **−0.08**

**acumulación de ganancia a lo largo de la cadena**

- `Skreamer.Vol` **−0.08** — *si valor > 0.8*
- `Treble Booster.Bs` **−0.10** — *si valor > 0.8*
- `Gain Booster.B` **−0.10** — *si valor > 0.8*
- `CabPanel.Vol` **−0.08** — *si valor > 0.8*
- `Cabinets & Mics.MV` **−0.08** — *si valor > 0.8*
- `Matched Cabinet.MV` **−0.08** — *si valor > 0.8*

**ganancia de compensación del compresor demasiado alta**

- `Tube Compressor.Out` **−0.08**

**nivel de entrada dentro del rack**

- `Input Level.v` **−0.08**
    actúa antes de toda la ganancia de la cadena; corrige la causa, no el síntoma
- `Input Level.o` **−0.05**

**Red de seguridad**

- `Limiter.Lm` **= 0.87**
    techo de nivel; es red de seguridad, no solución

⚠️ Bajar PV no resuelve nada si el recorte ya ocurre en la entrada de la interfaz.

⚠️ Bajar el previo V1 reduce el recorte Y la distorsión. Para bajar solo el nivel, usa el master V2.

### Nivel general bajo (tocando solo)

**Cómo se dice:** "volumen bajo", "suena flojo", "débil", "sin nivel"

**Medición:** `rms_dbfs` < -20 con pico < -6 — medible con fiabilidad

**No confundir con** → *Se pierde en la mezcla (con banda)*

**salida del preset baja**

- `Preset Volume.PV` **+0.08**
- `CabPanel.Vol` **+0.05**

**master del ampli bajo**

- `V2|Mast` (cualquier ampli) **+0.05**

**pedal de volumen bajado**

- `Volume Pedal.Vol` **+0.10**
- `Volume Pedal.Pd`
    comprueba que el pedal no esté bajado

⚠️ No subas el previo V1 para ganar volumen: eso añade distorsión. Usa el master.

## Ruido

### Siseo — “ssss” agudo y constante

**Cómo se dice:** "siseo", "ruido de fondo", "ruido al no tocar", "ssss"

**Medición:** `noise_floor_dbfs` > -45 en silencio — medible con fiabilidad

**Prueba de oído:** Baja V1/Gn a la mitad. Si el siseo baja con él, la cadena está amplificando ruido: ataca la causa.

**drive o previo excesivo (causa raíz)**

- `Skreamer.Dr` **−0.10** — compensa con `Vol` +0.05
- `V1|Gn` (cualquier ampli) **−0.08** — compensa con `V2|Mast` +0.05
- `Treble Booster.Bs` **−0.10**

**sin reducción de ruido en la cadena**
> solo después de la causa raíz

- `Noise Reduction.T` **+0.05** — *repite hasta que el siseo desaparezca mientras no tocas*
- `Noise Reduction.H` **+0.10** — *si el siseo es agudo y continuo*
- `Noise Reduction.R` **+0.10** — *si las notas se cortan de golpe*
- `Noise Gate.T` **+0.05** — *si no hay Noise Reduction*
- `Solid Dynamics.G8` **+0.05**
- `Solid Dynamics.G7` **−0.15**
    Range atenúa en vez de silenciar: evita el efecto de puerta que golpea

⚠️ Un umbral demasiado alto se come el sustain — ver “Notas que se cortan”.

⚠️ La puerta no quita el siseo mientras tocas, solo en las pausas.

### Zumbido — grave y constante

**Cómo se dice:** "zumbido", "ronroneo", "zumba", "ruido grave"

**Medición:** `energy_60_120_180hz` picos estrechos en la frecuencia de la red — medible con fiabilidad

**Prueba de oído:** Gira el cuerpo con la guitarra en la mano. Si cambia de intensidad, es captación electromagnética. Toca las cuerdas: si desaparece, es toma de tierra.

**interferencia electromagnética**
> Fuera de Guitar Rig — Cambia de posición, aléjate de monitores, fuentes y cargadores, revisa la toma de tierra.

**paliativo dentro del preset**

- `EQ Parametric.G1` **−0.30** @ 60 Hz Q estrecha
- `EQ Parametric.G2` **−0.25** @ 120 Hz Q estrecha

⚠️ La puerta de ruido es la herramienta equivocada para el zumbido: destruye el sustain y el zumbido vuelve bajo la nota.

### Fizz — siseo agudo dentro de la distorsión

**Cómo se dice:** "sierra eléctrica", "abejas", "arena en el sonido", "siseo agudo", "distorsión áspera"

**Medición:** `energy_above_6khz` excesiva mientras suenan las notas — medible con fiabilidad

**Distinguir de *Siseo — “ssss” agudo y constante*:** el fizz solo aparece mientras tocas; el siseo es constante y la puerta lo elimina

**falta de pantalla, o la equivocada**
> Confirma que existen en la cadena: `Cabinets & Mics`, `Matched Cabinet`, `CabPanel`

- `CabPanel.Air` **−0.15**
- `CabPanel.MPos` **−0.15**
    aléjate del centro del cono; el control más eficaz aquí
- `CabPanel.Trb` **−0.10**
- `Matched Cabinet.a` **−0.15**

**exceso de agudos de la propia distorsión**

- `EQ Parametric.G2` **−0.20** @ 7500 Hz Q media
- `Skreamer.Dr` **−0.08**
- `Solid EQ.L13` @ 7000 Hz
    un pasa-bajos tumba todo lo de arriba; mejor que un corte en campana para el fizz
- `Pro-Filter.F` @ 7000 Hz
    modo pasa-bajos, pendiente alta

⚠️ Bajar el Treble del ampli mata también el ataque útil en 3–4 kHz. Trabaja sobre la pantalla y el micro.

### Notas que se cortan, fallan o mueren antes

**Cómo se dice:** "las notas se cortan", "falla", "las notas desaparecen", "corta al final", "tartamudea"

**Medición:** `envelope_decay` caída abrupta en vez de decaimiento suave — medible en parte

**puerta demasiado agresiva**

- `Noise Reduction.T` **−0.08**
- `Noise Reduction.R` **+0.10**
- `Noise Gate.T` **−0.08**
- `Noise Gate.H` **+0.10**
- `Noise Gate.R` **+0.10**
- `Solid Dynamics.G8` **−0.08**
- `Solid Dynamics.G11` **+0.10**
- `Solid Dynamics.G7` **−0.15**

⚠️ Si necesitas un umbral alto para contener el siseo, el problema real es exceso de ganancia — ver “Siseo”.

## Timbre

### Apagado, sin brillo, “manta sobre el ampli”

**Cómo se dice:** "apagado", "sin brillo", "manta sobre el ampli", "sordo", "opaco", "sin definición en agudos"

**Medición:** `energy_2k_5k+spectral_centroid` baja — medible con fiabilidad

- Descarta antes: tono de la guitarra cerrado
- Descarta antes: pastilla del mástil
- Descarta antes: cuerdas viejas
- Descarta antes: auriculares o monitores malos

**microfoneo oscuro**

- `CabPanel.MPos` **+0.15**
    micro hacia el centro del cono; el control más potente y el menos evidente
- `CabPanel.Dst` **−0.10**
- `CabPanel.Trb` **+0.10**
- `CabPanel.Air` **+0.10**

**falta de presencia o agudos del ampli**

- `Pr|Prs|p` (cualquier ampli) **+0.10**
- `T|Trb|t` (cualquier ampli) **+0.08**
- `Skreamer.Br` **+0.10**
- `Skreamer.Tn` **+0.10**

**ecualización**

- `EQ Shelving.G2` **+0.15** @ 3000 Hz
- `EQ Parametric.G1` **+0.15** @ 2500 Hz Q ancha

⚠️ Si hay barro en 250–500 Hz tapando los agudos, subir treble deja el sonido brillante Y embarrado. Revisa “Embarrado” primero.

### Estridente, demasiado agudo, cansa

**Cómo se dice:** "estridente", "demasiado agudo", "duele el oído", "cansa", "afilado", "en la cara"

**Medición:** `energy_3k_6k` pico excesivo — medible con fiabilidad

**Distinguir de *Fizz — siseo agudo dentro de la distorsión*:** lo estridente muerde en el ataque, sobre 3–5 kHz; el fizz es ruido continuo por encima de 6 kHz

**presencia demasiado alta**

- `Pr|Prs|p` (cualquier ampli) **−0.10**

**microfoneo brillante**

- `CabPanel.MPos` **−0.15**
- `CabPanel.Trb` **−0.10**
- `CabPanel.Air` **−0.10**

**realce de agudos en la cadena**

- `Treble Booster.Bs` **−0.15**
- `Skreamer.Tn` **−0.10**
- `T|Trb|t` (cualquier ampli) **−0.08**

**corte quirúrgico**

- `EQ Parametric.G1` **−0.20** @ 3500 Hz (barre 2500–5000 Hz) Q media

### Embarrado, sin definición en los graves

**Cómo se dice:** "embarrado", "atropellado", "sucio en graves", "demasiado pesado", "sin definición", "emborronado"

**Medición:** `energy_250_500` excesiva — medible con fiabilidad

**exceso en la zona del barro**

- `EQ Parametric.G1` **−0.20** @ 350 Hz (barre 250–500 Hz) Q media
    el corte que más transforma una guitarra eléctrica
- `B|Bs|b` (cualquier ampli) **−0.10**
- `CabPanel.Bs` **−0.10**
- `EQ Shelving.G1` **−0.15** @ 100 Hz
- `Skreamer.Bs` **−0.10**
- `Skreamer.Dr` **−0.08**
- `EQ Graphic.b2` **−0.15**
    ajusta mi/ma para cubrir el rango 100–1000 Hz
- `EQ Graphic.b3` **−0.15**
- `Solid EQ.H12` @ 85 Hz
    un pasa-altos limpia el sub que solo consume headroom

⚠️ El barro de 250–500 Hz se confunde con “demasiados graves”. Cortar en 80 Hz no lo arregla y deja el sonido delgado.

### Nasal, enlatado, sonido de teléfono

**Cómo se dice:** "nasal", "enlatado", "caja de cartón", "sonido de teléfono", "gangoso"

**Medición:** `energy_500_900` pico — medible con fiabilidad

**resonancia de caja**

- `EQ Parametric.G1` **−0.20** @ 700 Hz (barre 500–900 Hz) Q media-estrecha
- `M|Mid|m` (cualquier ampli) **−0.10**
- `CabPanel.Sz` **+0.10**
- `CabPanel.Dst` **+0.10**

### Delgado, flaco, sin cuerpo

**Cómo se dice:** "delgado", "flaco", "sin cuerpo", "sin peso", "quebradizo", "sin graves"

**Medición:** `energy_100_250` baja — medible con fiabilidad

**falta de cuerpo**

- `B|Bs|b` (cualquier ampli) **+0.10**
- `CabPanel.Bs` **+0.10**
- `CabPanel.Sz` **+0.10**
- `CabPanel.Dst` **+0.08**
- `EQ Shelving.G1` **+0.15** @ 150 Hz
- `Skreamer.Bs` **+0.10**
- `Skreamer.Cl` **+0.10**
- `Hot Solo+.D8` **+0.10**
- `Van 51.R6` **+0.10**

⚠️ El cuerpo está en 100–250 Hz; el barro en 250–500 Hz. Si quedó pesado Y atropellado, apuntaste a la banda equivocada.

### Se pierde en la mezcla (con banda)

**Cómo se dice:** "se pierde en la mezcla", "desaparece con la banda", "no atraviesa", "enterrada", "la guitarra queda atrás"

**Medición:** `energy_800_2k_relative` baja — medible en parte

> Solo tiene sentido escuchando la mezcla completa, nunca la guitarra en solitario.

**No confundir con** → *Nivel general bajo (tocando solo)*

**la banda propia de la guitarra está vacía**

- `EQ Parametric.G1` **+0.15** @ 1200 Hz (barre 800–2000 Hz) Q ancha
- `M|Mid|m` (cualquier ampli) **+0.10**
- `Pr|Prs|p` (cualquier ampli) **+0.08**

**la guitarra compite con el bajo**

- `EQ Shelving.G1` **−0.15** @ 100 Hz

**el reverb la empuja hacia atrás**

- `Studio Reverb.Wet` **−0.10**

⚠️ Un timbre “scooped” impresiona en solitario y es lo peor posible en una mezcla. Mantén un preset distinto para cada situación.

### Palm mutes sin pegada, cuerda grave floja

**Cómo se dice:** "los palm mutes no pegan", "cuerda grave floja", "sin chug", "graves blandos", "sin golpe"

**Medición:** `attack_transient` lento — depende del oído

**graves descontrolados que emborronan el ataque**

- `EQ Parametric.G1` **−0.15** @ 90 Hz Q estrecha
- `Skreamer.Dr` **= 0.2**
    drive bajo y nivel alto: recorta graves antes de la distorsión, el truco clásico del Tube Screamer
- `Skreamer.Vol` **= 0.8**

**respuesta lenta del ampli**

- `Rsp` (cualquier ampli) **+0.10**
- `Sg` (cualquier ampli) **−0.10**
- `Var` (cualquier ampli) **+0.10**
- `Bi` (cualquier ampli) **+0.10**

## Dinámica

### Poca distorsión, demasiado limpio

**Cómo se dice:** "poca distorsión", "demasiado limpio", "sin drive", "la distorsión no pesa", "flojo"

**ganancia insuficiente**

- `V1|Gn` (cualquier ampli) **+0.10** — compensa con `V2|Mast` −0.05
- `Skreamer.Dr` **+0.15**
- `Treble Booster.Bs` **+0.15**
- `Gain Booster.B` **+0.15**
- `Lead 800.Hg` **= 1**
- `Jump.Hg` **= 1**
- `Van 51.H14` **= 1**
- `Citrus.Br` **= 1**
- `Big Fuzz.S` **+0.15**
    el fuzz es otra categoría, no “más distorsión”
- `Fuzz.F` **+0.15**

⚠️ Los amplis limpios por diseño (Twang Reverb, AC Box, Tweedman, Jazz Amp, Tweed Delight) no se vuelven de alta ganancia por mucho que subas. Cambia de ampli.

⚠️ Los de alta ganancia: Gratifier, Van 51, Rammfire, Sledgehammer, MeZone.

### Pastoso, distorsión sin definición

**Cómo se dice:** "pastoso", "demasiada distorsión", "papilla", "emborronado", "los acordes se hacen sopa", "sin separación"

**ganancia excesiva**

- `V1|Gn` (cualquier ampli) **−0.10** — compensa con `V2|Mast` +0.05
- `Skreamer.Dr` **−0.10**

**demasiados graves entrando en la distorsión**

- `Skreamer.Bs` **−0.10**
    la causa número uno de la pastosidad
- `M|Mid|m` (cualquier ampli) **+0.08**
- `Bi` (cualquier ampli) **+0.08**
- `Sg` (cualquier ampli) **−0.08**

### Sin sustain, las notas mueren rápido

**Cómo se dice:** "sin sustain", "la nota muere rápido", "no aguanta", "seco"

**Revisa primero** → *Notas que se cortan, fallan o mueren antes*

**falta de compresión**

- `Tube Compressor.Th` **−0.10**
- `Tube Compressor.Rt` **+0.10**
- `Tube Compressor.Rl` **+0.10**
- `Stomp Compressor.S` **+0.15**
- `Sg` (cualquier ampli) **+0.10**

### Aplastado, no responde al toque

**Cómo se dice:** "aplastado", "sin dinámica", "no responde al toque", "todo al mismo volumen", "sin expresión"

**compresión excesiva**

- `Tube Compressor.Rt` **−0.10**
- `Tube Compressor.Th` **+0.10**
- `Tube Compressor.Dyn` **+0.10**
- `Stomp Compressor.S` **−0.15**
- `Fast Comp.I0` **−0.10**

**ganancia alta actuando como compresor**

- `V1|Gn` (cualquier ampli) **−0.10**
- `Sg` (cualquier ampli) **−0.10**
- `Rsp` (cualquier ampli) **+0.10**

### Ataque de púa demasiado fuerte, clic

**Cómo se dice:** "clic de púa", "ataque demasiado fuerte", "ruido de púa", "ataque agresivo"

**transitorio sin controlar**

- `Tube Compressor.Att` **−0.10**
- `EQ Parametric.G1` **−0.12** @ 2500 Hz
- `CabPanel.MPos` **−0.10**

## Espacio

### Lejano, lavado, “dentro de un pozo”

**Cómo se dice:** "lejano", "lavado", "dentro de un pozo", "demasiado húmedo", "demasiado reverb", "lejos"

**exceso de espacio**

- `Studio Reverb.Wet` **−0.15**
- `Studio Reverb.Sz` **−0.10**
- `Spring Reverb.Wet` **−0.15**
- `Quad Delay.W` **−0.10**
- `Delay Man.m` **−0.10**
- `Little Reflektor.W1` **−0.15**

⚠️ El reverb es lo que más hace desaparecer una guitarra en la mezcla. Usa menos del que parece correcto tocando solo.

### Reverb o delay embarrando los graves

**Cómo se dice:** "reverb embarrado", "cola sucia", "eco con demasiados graves"

**demasiados graves en la cola**

- `Spring Reverb.B` **−0.15**
- `Little Reflektor.L4` **+0.15**
- `Quad Delay.LP` **−0.10**
- `Studio Reverb.L` **−0.10**

### Desaparece o suena hueco en mono

**Cómo se dice:** "desaparece en mono", "estéreo raro", "suena hueco", "problema de fase", "se perdió en el móvil"

**Medición:** `stereo_correlation` < 0 — medible con fiabilidad

**cancelación de fase**

- `Split Mix.iP` alterna 0/1
- `CabPanel.Phs` alterna 0/1
- `Control Room Pro.pi1` alterna 0/1
    revisa micro por micro, de pi1 a pi8
- `CrossOver Mix.iP` alterna 0/1
    los presets con CrossOver dividen por frecuencia; la mitad aguda puede estar invertida
- `Matched Cabinet.st` **−0.15**

### Estéreo demasiado ancho, inestable

**Cómo se dice:** "estéreo demasiado ancho", "inestable", "el sonido se mueve", "demasiado disperso"

**anchura excesiva**

- `Split Mix.XFade`
    acerca PanA/PanB al centro
- `Matched Cabinet.st` **−0.15**
- `Flanger.St` **−0.15**
- `Ensemble.S` **−0.15**
- `Stereo Tune.S3` **−0.15**
    este componente existe solo para la anchura; es el primero a revisar
- `Stereo Tune.D1` **−0.10**

## Causas fuera de Guitar Rig

| Síntoma | Causa probable | Dónde resolverlo |
|---|---|---|
| retardo entre tocar y oír | buffer demasiado grande, o driver equivocado | Audio Settings: usa ASIO, buffer 128–256 |
| clics y cortes intermitentes | buffer demasiado pequeño para la CPU | aumenta el buffer |
| saturación en la entrada | ganancia de la interfaz | el mando de ganancia de la interfaz |
| zumbido que cambia al moverte | captación electromagnética | posición, toma de tierra, blindaje |
| apagado en cualquier preset | cuerdas viejas o control de tono cerrado | la guitarra |
| siseo incluso con poca ganancia | cable malo o pastilla ruidosa | cambia el cable |

## Parámetros comunes de los amplis

```
V1|Gn        ganancia de entrada / previo — cuánta distorsión
V2|Mast      volumen de salida / master — nivel sin cambiar la distorsión
B|Bs|b       Bass
M|Mid|m      Mid
T|Trb|t      Treble
Pr|Prs|p     Presence — actúa en la etapa de potencia, suena distinto al treble
Sg           Sag — compresión natural de la fuente de alimentación
Rsp          Response — velocidad de reacción del ampli
Bi           Bias — asimetría de la distorsión
Var          Variac — tensión de alimentación; aprieta el sonido
Hg           boost integrado (Lead 800, Jump)
```

**Excepciones — en estos amplis V1/V2 no significan ganancia y master**

- **Plex** — V1 = Bright Volume, V2 = Warm Volume — dos canales sumados, no ganancia + master
- **Cool Plex** — igual que el Plex
- **Van 51** — R0 = Rhythm Pre Gain, L1 = Lead Pre Gain, P5 = Post Gain, H14 = HiGainInput
- **AC Box** — Vol = Normal Volume, Br = Brilliant Volume — dos canales
- **High White** — nv = Normal Vol, bv = Brilliant Vol, Mst = Master
- **Tweedman** — VB = Volume Bright, VN = Volume Normal
- **Gratifier** — Gn = Gain, Mast = Master; M es Mode, no Mid
- **Rammfire** — Gn = Gain, Mast = Master; M es Mode, no Mid
- **Ultrasonic** — g = Gain, v = Volume, Mst = Master
- **Hot Solo+** — P0 = Normal, P1 = Overdrive, M6 = Master, O2 selecciona el canal
- **Citrus** — g = Gain, m = Master
- **Hot Plex** — igual que el Plex
- **Tweed Delight** — vb = Volume Bright, vn = Volume Normal; solo t = Tone, sin B/M/T
- **Sledgehammer** — g = Gain, v = Volume; c = Contour con f = Frequency forman un medio barrible
- **MeZone** — D = Distortion, V = Volume; el único con EQ PRE-distorsión (PB, PQ, PM, PT)
- **Jazz Amp** — V = Volume; limpio por diseño, em = Ensemble Mode
- **Bass Pro** — G = Gain, D = Drive, V = Volume; EQ gráfico con bandas rotuladas en Hz
- **TransAmp** — D = Drive, V = Volume; A selecciona el ampli, CM activa pantalla y micro

---

Los deltas son **un paso**, no un valor final. Aplica, escucha, repite. Las frecuencias en Hz son objetivos; el parámetro correspondiente está normalizado 0–1 y el mapeo exacto no se ha decodificado — ajústalo en pantalla. Los componentes citados pueden no existir en el preset que estés usando.
