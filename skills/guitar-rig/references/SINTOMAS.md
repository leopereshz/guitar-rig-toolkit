# Referência de sintomas — Guitar Rig

Árvore de diagnóstico sintoma → causa → ação para Guitar Rig. Os deltas são normalizados 0–1 e representam UM passo, não valor final: aplique, escute, repita.

*Extraído de: 349 presets, 98 componentes, 1039 parâmetros.*

## Ordem de diagnóstico

```
1. NÍVEL        está clipando? tem headroom?
2. RUÍDO        chiado, zumbido, microfonia
3. TOM          equilíbrio de frequências (EQ, cabinet, mic)
4. DINÂMICA     compressão, sustain, resposta ao toque
5. ESPAÇO       reverb, delay, estéreo
```

Não pule etapas. Cada uma contamina a seguinte: ajustar EQ enquanto clipa é inútil, porque a aspereza que incomoda é o clip, não o tom. Ajustar gate antes de resolver ganho excessivo mascara o ruído e come o sustain. Ajustar reverb antes do tom faz você compensar EQ com espaço, e o resultado fica distante e sem foco.

## Mapa de frequências da guitarra elétrica

| Faixa | Hz | O que faz |
|---|---|---|
| Subgrave | 20–60 | guitarra não vive aqui; só come headroom |
| Peso | 60–120 | fundamento. Falta = magro. Excesso = retumbante |
| Corpo | 120–250 | calor. Falta = sem corpo. Excesso = encobre o baixo |
| Lama | 250–500 | **zona da lama**. Excesso = embolado, sem definição |
| Caixa | 500–800 | Excesso = nasal, enlatado, papelão |
| Definição | 800–1500 | ataque de nota. Falta = **some na mistura** |
| Presença | 1500–3000 | inteligibilidade. Falta = **abafado** |
| Ataque | 3000–5000 | garra da palheta. Excesso = **estridente** |
| Brilho | 5000–8000 | Excesso = **fizz, chiado, serra** |
| Ar | 8000–20000 | em distorção, quase só lixo. Alto-falante real corta acima de ~5–6 kHz |

## Nível

### Estourando, crepitando, distorcendo feio

**Como se fala:** "estourando", "estourado", "estalando", "crepitando", "quebrando", "distorcendo feio", "distorcendo errado", "sujo", "chiado no ataque"

**Medição:** `peak_dbfs` >= -0.1 — medível com confiança

**Teste de ouvido:** Baixe o volume da guitarra pela metade. Se a aspereza sumir na hora, é clipping, não é timbre.

**ganho de entrada da interface alto demais**
> Fora do Guitar Rig — Toque o acorde mais forte que você usa; o medidor de entrada deve parar entre −12 e −6 dBFS, nunca no vermelho.

**saída do preset alta demais**

- `Preset Volume.PV` **−0.08**

**empilhamento de ganho na cadeia**

- `Skreamer.Vol` **−0.08** — *se valor > 0.8*
- `Treble Booster.Bs` **−0.10** — *se valor > 0.8*
- `Gain Booster.B` **−0.10** — *se valor > 0.8*
- `CabPanel.Vol` **−0.08** — *se valor > 0.8*
- `Cabinets & Mics.MV` **−0.08** — *se valor > 0.8*
- `Matched Cabinet.MV` **−0.08** — *se valor > 0.8*

**makeup do compressor alto**

- `Tube Compressor.Out` **−0.08**

**nível de entrada dentro do rack**

- `Input Level.v` **−0.08**
    age antes de todo o ganho da cadeia; corrige a causa, não o sintoma
- `Input Level.o` **−0.05**

**Rede de segurança**

- `Limiter.Lm` **= 0.87**
    teto de nível; é rede de segurança, não solução

⚠️ Baixar o PV não resolve se o clip já acontece na entrada da interface.

⚠️ Baixar o preamp V1 reduz o clip E a distorção. Para só baixar nível, mexa no master V2.

### Volume geral baixo (tocando sozinho)

**Como se fala:** "volume baixo", "som baixo", "fraco", "sem volume"

**Medição:** `rms_dbfs` < −20 com pico < −6 — medível com confiança

**Não confundir com** → *Sumindo na mistura (com banda)*

**saída do preset baixa**

- `Preset Volume.PV` **+0.08**
- `CabPanel.Vol` **+0.05**

**master do amp baixo**

- `V2|Mast` (qualquer amp) **+0.05**

**volume pedal abaixado**

- `Volume Pedal.Vol` **+0.10**
- `Volume Pedal.Pd`
    verificar se o pedal não está abaixado

⚠️ Não suba o preamp V1 para ganhar volume: isso adiciona distorção. Use o master.

## Ruído

### Chiado — "chiiii" agudo e constante

**Como se fala:** "chiando", "chiado", "ruído de fundo", "barulho parado", "chiiii"

**Medição:** `noise_floor_dbfs` > −45 em silêncio — medível com confiança

**Teste de ouvido:** Baixe V1/Gn pela metade. Se o chiado cair junto, a cadeia está amplificando ruído: trate a causa.

**drive/preamp excessivo (causa raiz)**

- `Skreamer.Dr` **−0.10** — compensar em `Vol` +0.05
- `V1|Gn` (qualquer amp) **−0.08** — compensar em `V2|Mast` +0.05
- `Treble Booster.Bs` **−0.10**

**sem redução de ruído**
> só depois da causa raiz

- `Noise Reduction.T` **+0.05** — *repetir até chiado sumir parado*
- `Noise Reduction.H` **+0.10** — *se chiado agudo e contínuo*
- `Noise Reduction.R` **+0.10** — *se notas cortam seco*
- `Noise Gate.T` **+0.05** — *se Noise Reduction ausente*
- `Solid Dynamics.G8` **+0.05**
- `Solid Dynamics.G7` **−0.15**
    Range atenua em vez de silenciar: evita o efeito de porta batendo

⚠️ Threshold alto demais come o sustain — ver “Notas cortando”.

⚠️ Gate não remove chiado enquanto você toca, só nas pausas.

### Zumbido — "zzzz" grave e constante

**Como se fala:** "zumbido", "ronco", "zumbindo", "zzzz", "barulho grave"

**Medição:** `energy_60_120_180hz` picos estreitos na frequência da rede elétrica — medível com confiança

**Teste de ouvido:** Gire o corpo com a guitarra na mão. Se muda de intensidade, é captação eletromagnética. Encoste nas cordas: se some, é aterramento.

**interferência eletromagnética**
> Fora do Guitar Rig — Mudar de posição, afastar de monitor, fonte ou carregador, verificar o aterramento.

**paliativo no preset**

- `EQ Parametric.G1` **−0.30** @ 60 Hz Q estreito
- `EQ Parametric.G2` **−0.25** @ 120 Hz Q estreito

⚠️ Gate é ferramenta errada para zumbido: destrói o sustain e o zumbido volta na nota.

### Fizz — chiado agudo dentro da distorção

**Como se fala:** "serra elétrica", "abelha", "areia no som", "chiado agudo", "distorção áspera", "fizz"

**Medição:** `energy_above_6khz` excessiva durante as notas — medível com confiança

**Distinguir de *Chiado — "chiiii" agudo e constante*:** fizz só aparece enquanto você toca; hiss é constante e some com gate

**falta de cabinet ou cabinet errado**
> Confirmar que existe na cadeia: `Cabinets & Mics`, `Matched Cabinet`, `CabPanel`

- `CabPanel.Air` **−0.15**
- `CabPanel.MPos` **−0.15**
    afastar do centro do cone; é o controle mais eficaz aqui
- `CabPanel.Trb` **−0.10**
- `Matched Cabinet.a` **−0.15**

**excesso de alta frequência da distorção**

- `EQ Parametric.G2` **−0.20** @ 7500 Hz Q médio
- `Skreamer.Dr` **−0.08**
- `Solid EQ.L13` @ 7000 Hz
    passa-baixa derruba tudo acima; melhor que corte em sino para fizz
- `Pro-Filter.F` @ 7000 Hz
    modo passa-baixa, Slope alto

⚠️ Baixar o Treble do amp mata também o ataque útil em 3–4 kHz. Prefira mexer no cabinet e no mic.

### Notas cortando, falhando, sumindo no fim

**Como se fala:** "cortando", "falhando", "notas somem", "corta no fim", "engasgando"

**Medição:** `envelope_decay` queda abrupta em vez de decaimento suave — medível parcialmente

**gate agressivo demais**

- `Noise Reduction.T` **−0.08**
- `Noise Reduction.R` **+0.10**
- `Noise Gate.T` **−0.08**
- `Noise Gate.H` **+0.10**
- `Noise Gate.R` **+0.10**
- `Solid Dynamics.G8` **−0.08**
- `Solid Dynamics.G11` **+0.10**
- `Solid Dynamics.G7` **−0.15**

⚠️ Se você precisa de threshold alto para segurar o chiado, o problema real é ganho excessivo — ver “Chiado”.

## Tom

### Abafado, sem brilho, "cobertor no amplificador"

**Como se fala:** "abafado", "sem brilho", "cobertor", "surdo", "opaco", "sem definição no agudo"

**Medição:** `energy_2k_5k+spectral_centroid` baixa — medível com confiança

- Descartar antes: tone da guitarra fechado
- Descartar antes: captador do braço
- Descartar antes: cordas velhas
- Descartar antes: fone ou monitor ruim

**microfonação escura**

- `CabPanel.MPos` **+0.15**
    mic para o centro do cone; o controle mais poderoso e o menos óbvio
- `CabPanel.Dst` **−0.10**
- `CabPanel.Trb` **+0.10**
- `CabPanel.Air` **+0.10**

**falta de presença ou agudo no amp**

- `Pr|Prs|p` (qualquer amp) **+0.10**
- `T|Trb|t` (qualquer amp) **+0.08**
- `Skreamer.Br` **+0.10**
- `Skreamer.Tn` **+0.10**

**equalização**

- `EQ Shelving.G2` **+0.15** @ 3000 Hz
- `EQ Parametric.G1` **+0.15** @ 2500 Hz Q largo

⚠️ Se há lama em 250–500 Hz mascarando o agudo, subir treble deixa brilhante E lamacento. Cheque “Lamacento” antes.

### Estridente, agudo demais, cansativo

**Como se fala:** "estridente", "agudo demais", "dói o ouvido", "cansativo", "afiado", "na cara"

**Medição:** `energy_3k_6k` pico excessivo — medível com confiança

**Distinguir de *Fizz — chiado agudo dentro da distorção*:** estridente incomoda no ataque, em 3–5 kHz; fizz é ruído contínuo acima de 6 kHz

**presence alto**

- `Pr|Prs|p` (qualquer amp) **−0.10**

**microfonação brilhante**

- `CabPanel.MPos` **−0.15**
- `CabPanel.Trb` **−0.10**
- `CabPanel.Air` **−0.10**

**boost de agudo**

- `Treble Booster.Bs` **−0.15**
- `Skreamer.Tn` **−0.10**
- `T|Trb|t` (qualquer amp) **−0.08**

**corte cirúrgico**

- `EQ Parametric.G1` **−0.20** @ 3500 Hz (varrer 2500–5000 Hz) Q médio

### Lamacento, embolado, sem definição no grave

**Como se fala:** "lamacento", "embolado", "sujo no grave", "pesado demais", "sem definição", "borrado"

**Medição:** `energy_250_500` excessiva — medível com confiança

**excesso na zona da lama**

- `EQ Parametric.G1` **−0.20** @ 350 Hz (varrer 250–500 Hz) Q médio
    o corte mais transformador em guitarra elétrica
- `B|Bs|b` (qualquer amp) **−0.10**
- `CabPanel.Bs` **−0.10**
- `EQ Shelving.G1` **−0.15** @ 100 Hz
- `Skreamer.Bs` **−0.10**
- `Skreamer.Dr` **−0.08**
- `EQ Graphic.b2` **−0.15**
    ajustar mi/ma para a faixa 100-1000 Hz
- `EQ Graphic.b3` **−0.15**
- `Solid EQ.H12` @ 85 Hz
    passa-alta limpa o subgrave que só come headroom

⚠️ Lama de 250–500 Hz é confundida com “muito grave”. Cortar em 80 Hz não resolve e ainda deixa o som magro.

### Nasal, enlatado, som de telefone

**Como se fala:** "nasal", "enlatado", "caixa de papelão", "som de telefone", "abafado e nasal"

**Medição:** `energy_500_900` pico — medível com confiança

**ressonância de caixa**

- `EQ Parametric.G1` **−0.20** @ 700 Hz (varrer 500–900 Hz) Q médio-estreito
- `M|Mid|m` (qualquer amp) **−0.10**
- `CabPanel.Sz` **+0.10**
- `CabPanel.Dst` **+0.10**

### Fino, magro, sem corpo

**Como se fala:** "fino", "magro", "sem corpo", "sem peso", "fraquinho", "sem graves"

**Medição:** `energy_100_250` baixa — medível com confiança

**falta de corpo**

- `B|Bs|b` (qualquer amp) **+0.10**
- `CabPanel.Bs` **+0.10**
- `CabPanel.Sz` **+0.10**
- `CabPanel.Dst` **+0.08**
- `EQ Shelving.G1` **+0.15** @ 150 Hz
- `Skreamer.Bs` **+0.10**
- `Skreamer.Cl` **+0.10**
- `Hot Solo+.D8` **+0.10**
- `Van 51.R6` **+0.10**

⚠️ Corpo está em 100–250 Hz; lama em 250–500 Hz. Se ficou pesado E embolado, você errou a faixa.

### Sumindo na mistura (com banda)

**Como se fala:** "sumindo", "some na banda", "não aparece", "perdido na mistura", "guitarra atrás"

**Medição:** `energy_800_2k_relative` baixa — medível parcialmente

> Só faz sentido ouvindo a mistura completa, nunca a guitarra solada.

**Não confundir com** → *Volume geral baixo (tocando sozinho)*

**faixa própria da guitarra vazia**

- `EQ Parametric.G1` **+0.15** @ 1200 Hz (varrer 800–2000 Hz) Q largo
- `M|Mid|m` (qualquer amp) **+0.10**
- `Pr|Prs|p` (qualquer amp) **+0.08**

**guitarra disputando faixa do baixo**

- `EQ Shelving.G1` **−0.15** @ 100 Hz

**reverb empurrando para trás**

- `Studio Reverb.Wet` **−0.10**

⚠️ O timbre “scooped” soa impressionante sozinho e é o pior possível numa mistura. Mantenha um preset separado para cada situação.

### Palm mute sem impacto, corda grave flácida

**Como se fala:** "palm mute sem impacto", "corda grave flácida", "sem chug", "grave mole", "sem soco"

**Medição:** `attack_transient` lento — depende do ouvido

**grave descontrolado borrando o ataque**

- `EQ Parametric.G1` **−0.15** @ 90 Hz Q estreito
- `Skreamer.Dr` **= 0.2**
    drive baixo + Vol alto: corta grave antes da distorção, uso clássico do Tube Screamer
- `Skreamer.Vol` **= 0.8**

**resposta lenta do amp**

- `Rsp` (qualquer amp) **+0.10**
- `Sg` (qualquer amp) **−0.10**
- `Var` (qualquer amp) **+0.10**
- `Bi` (qualquer amp) **+0.10**

## Dinâmica

### Pouca distorção, limpo demais

**Como se fala:** "pouca distorção", "limpo demais", "sem drive", "sem peso na distorção", "fraco"

**ganho insuficiente**

- `V1|Gn` (qualquer amp) **+0.10** — compensar em `V2|Mast` −0.05
- `Skreamer.Dr` **+0.15**
- `Treble Booster.Bs` **+0.15**
- `Gain Booster.B` **+0.15**
- `Lead 800.Hg` **= 1**
- `Jump.Hg` **= 1**
- `Van 51.H14` **= 1**
- `Citrus.Br` **= 1**
- `Big Fuzz.S` **+0.15**
    fuzz é outra categoria, não “mais distorção”
- `Fuzz.F` **+0.15**

⚠️ Amps limpos por natureza (Twang Reverb, AC Box, Tweedman, Jazz Amp, Tweed Delight) não viram high-gain com ganho. Troque de amp.

⚠️ Os de ganho alto: Gratifier, Van 51, Rammfire, Sledgehammer, MeZone.

### Pastoso, distorção sem definição

**Como se fala:** "pastoso", "distorção demais", "mush", "borrado", "acorde vira borrão", "sem separação"

**ganho excessivo**

- `V1|Gn` (qualquer amp) **−0.10** — compensar em `V2|Mast` +0.05
- `Skreamer.Dr` **−0.10**

**grave demais entrando na distorção**

- `Skreamer.Bs` **−0.10**
    causa número um de pastosidade
- `M|Mid|m` (qualquer amp) **+0.08**
- `Bi` (qualquer amp) **+0.08**
- `Sg` (qualquer amp) **−0.08**

### Sem sustain, notas morrem rápido

**Como se fala:** "sem sustain", "nota morre rápido", "não segura", "seco"

**Checar antes** → *Notas cortando, falhando, sumindo no fim*

**falta de compressão**

- `Tube Compressor.Th` **−0.10**
- `Tube Compressor.Rt` **+0.10**
- `Tube Compressor.Rl` **+0.10**
- `Stomp Compressor.S` **+0.15**
- `Sg` (qualquer amp) **+0.10**

### Achatado, não responde ao toque

**Como se fala:** "achatado", "sem dinâmica", "não responde ao toque", "tudo no mesmo volume", "sem expressão"

**compressão excessiva**

- `Tube Compressor.Rt` **−0.10**
- `Tube Compressor.Th` **+0.10**
- `Tube Compressor.Dyn` **+0.10**
- `Stomp Compressor.S` **−0.15**
- `Fast Comp.I0` **−0.10**

**ganho alto agindo como compressor**

- `V1|Gn` (qualquer amp) **−0.10**
- `Sg` (qualquer amp) **−0.10**
- `Rsp` (qualquer amp) **+0.10**

### Ataque de palheta forte demais, "click"

**Como se fala:** "click no ataque", "palheta forte demais", "bate na palheta", "ataque agressivo"

**transiente não controlado**

- `Tube Compressor.Att` **−0.10**
- `EQ Parametric.G1` **−0.12** @ 2500 Hz
- `CabPanel.MPos` **−0.10**

## Espaço

### Distante, lavado, "dentro de um poço"

**Como se fala:** "distante", "lavado", "dentro de um poço", "molhado", "reverb demais", "longe"

**excesso de espaço**

- `Studio Reverb.Wet` **−0.15**
- `Studio Reverb.Sz` **−0.10**
- `Spring Reverb.Wet` **−0.15**
- `Quad Delay.W` **−0.10**
- `Delay Man.m` **−0.10**
- `Little Reflektor.W1` **−0.15**

⚠️ Reverb é o que mais faz a guitarra sumir numa mistura. Use menos do que parece certo tocando sozinho.

### Reverb/delay embolando o grave

**Como se fala:** "reverb embolado", "cauda suja", "eco grave demais"

**cauda com grave demais**

- `Spring Reverb.B` **−0.15**
- `Little Reflektor.L4` **+0.15**
- `Quad Delay.LP` **−0.10**
- `Studio Reverb.L` **−0.10**

### Some ou fica oco em mono

**Como se fala:** "some em mono", "estéreo estranho", "fica oco", "fase estranha", "sumiu no celular"

**Medição:** `stereo_correlation` < 0 — medível com confiança

**cancelamento de fase**

- `Split Mix.iP` alternar 0/1
- `CabPanel.Phs` alternar 0/1
- `Control Room Pro.pi1` alternar 0/1
    checar mic a mic, pi1 a pi8
- `CrossOver Mix.iP` alternar 0/1
    presets com CrossOver dividem por frequência; a metade aguda pode estar invertida
- `Matched Cabinet.st` **−0.15**

### Estéreo largo demais, instável

**Como se fala:** "estéreo largo demais", "instável", "som viajando", "espalhado demais"

**largura excessiva**

- `Split Mix.XFade`
    aproximar PanA/PanB do centro
- `Matched Cabinet.st` **−0.15**
- `Flanger.St` **−0.15**
- `Ensemble.S` **−0.15**
- `Stereo Tune.S3` **−0.15**
    este componente existe só para largura; é o primeiro a checar
- `Stereo Tune.D1` **−0.10**

## Causas fora do Guitar Rig

| Sintoma | Causa provável | Onde resolver |
|---|---|---|
| atraso entre tocar e ouvir | buffer alto ou driver errado | Audio Settings: ASIO, buffer 128-256 |
| estalos intermitentes | buffer baixo demais para a CPU | aumentar buffer |
| clipping na entrada | ganho da interface | knob de gain da interface |
| zumbido que muda com a posição | captação eletromagnética | posição, aterramento, blindagem |
| abafado em qualquer preset | cordas velhas ou tone fechado | guitarra |
| chiado com ganho baixo | cabo ou captador ruidoso | trocar cabo |

## Parâmetros comuns dos amps

```
V1|Gn        ganho de entrada / preamp — quantidade de distorção
V2|Mast      volume de saída / master — volume sem mudar a distorção
B|Bs|b       Bass
M|Mid|m      Mid
T|Trb|t      Treble
Pr|Prs|p     Presence — atua na etapa de potência, soa diferente de treble
Sg           Sag — compressão natural da fonte de alimentação
Rsp          Response — velocidade da resposta
Bi           Bias — assimetria da distorção
Var          Variac — tensão de alimentação, aperta o som
Hg           Boost embutido (Lead 800, Jump)
```

**Exceções — nestes amps V1/V2 não significam ganho e master**

- **Plex** — V1 = Bright Volume, V2 = Warm Volume — dois canais somados, não ganho + master
- **Cool Plex** — igual ao Plex
- **Van 51** — R0 = Rhythm Pre Gain, L1 = Lead Pre Gain, P5 = Post Gain, H14 = HiGainInput
- **AC Box** — Vol = Normal Volume, Br = Brilliant Volume — dois canais
- **High White** — nv = Normal Vol, bv = Brilliant Vol, Mst = Master
- **Tweedman** — VB = Volume Bright, VN = Volume Normal
- **Gratifier** — Gn = Gain, Mast = Master; M é Mode, não Mid
- **Rammfire** — Gn = Gain, Mast = Master; M é Mode, não Mid
- **Ultrasonic** — g = Gain, v = Volume, Mst = Master
- **Hot Solo+** — P0 = Normal, P1 = Overdrive, M6 = Master, O2 seleciona o canal
- **Citrus** — g = Gain, m = Master
- **Hot Plex** — igual ao Plex
- **Tweed Delight** — vb = Volume Bright, vn = Volume Normal; só t = Tone, sem B/M/T
- **Sledgehammer** — g = Gain, v = Volume; c = Contour com f = Frequency formam um médio varrível
- **MeZone** — D = Distortion, V = Volume; único com EQ PRÉ-distorção (PB, PQ, PM, PT)
- **Jazz Amp** — V = Volume; limpo por natureza, em = Ensemble Mode
- **Bass Pro** — G = Gain, D = Drive, V = Volume; EQ gráfico com bandas rotuladas em Hz
- **TransAmp** — D = Drive, V = Volume; A seleciona o amp, CM liga cab & mic

---

Os deltas são **um passo**, não valor final. Aplique, escute, repita. As frequências em Hz são alvo; o parâmetro correspondente é normalizado 0–1 e o mapeamento exato não foi decodificado — ajuste na tela. Componentes citados podem não existir no preset em uso.
