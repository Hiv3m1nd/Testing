# HANDOFF — "Year by Year" series: from episode 1 AD to episode 2 AD

**For:** the next agent, running **locally** on the user's machine.
**From:** the agent that made episode 1 AD in a cloud container (October 2026).
**Branch with all the work:** `ccr-7b5c772c-oaxbng`. It is not merged to `main`.

Read this whole file before writing anything. Then read, in this order:

1. `year-1-ad/research/research.md`: how claims are sourced and tagged.
2. `year-1-ad/docs/technical_report.md`: what worked, what didn't, the QA log.
3. `year-1-ad/src/script_data.py`: the 1 AD script, which is the house style for narration.

Watch the finished film too:
`https://raw.githubusercontent.com/Hiv3m1nd/Testing/ccr-7b5c772c-oaxbng/year-1-ad/output/Year_1_AD.mp4`.
If you can't watch video, extract a contact sheet with the ffmpeg command in
§10.

---

## 0. Your task in one paragraph

Produce **episode 2 AD**: a vertical documentary for YouTube Shorts,
Instagram Reels and TikTok.

- **Look and feel:** it must look, sound and read like the same series as 1 AD.
- **Story:** it must pay off the two promises 1 AD made, and continue its
  threads.
- **Pipeline and process:** use the same code-only pipeline and the same
  research discipline.
- **Deliverables:** the same set as 1 AD (§6).

**Work locally. Do not use cloud sessions.** Cost must stay **$0**.

---

## 1. The user's brief (applies to every episode)

These are the user's requirements. They are not suggestions.

**Format**

- 1080×1920 (9:16), 30 fps minimum.
- H.264 MP4 with synchronized narration, music and sound.
- Burned-in captions with attractive, readable typography.

**Duration**

- Story-driven: some years need 40 s, some nearly 3 min. Never pad, never rush.
- Hard ceiling: the most restrictive platform limit, currently **3:00**
  (YouTube Shorts 3:00; Instagram Reels 3:00 for most accounts; TikTok 10:00+).
- 1 AD ran 2:53.6. Re-check the limits if months have passed.

**Style and audience**

- A premium historical documentary: cinematic storytelling with motion
  graphics.
- Intelligent, dramatic, engaging and historically credible, for a general
  audience.
- It must not feel like an automated slideshow.

**Visuals**

- Generated with code. This is the core of the experiment.
- Dynamic compositions: animated maps, camera moves, depth, particles,
  lighting, typography and real transitions.
- Pick the visual form that fits the story: maps for geopolitics, environments
  for places and daily life, diagrams for systems.
- Avoid repeating the same template.

**Accuracy (non-negotiable)**

- Never invent events.
- Distinguish events securely dated to the year from background
  circumstances.
- No invented or misattributed quotations.
- Keep a separate research document listing sources, claims and
  uncertainties.
- Say when the evidence is incomplete.

**Structure**

- A strong hook.
- A narrative, not trivia.
- Close with a setup for the next episode, which here is 3 AD.

**Series vision**

- Two tracks: BC counting down towards 1 BC, and AD counting up from 1 AD
  towards 2027.
- Eventually a BC episode in the morning and an AD episode in the evening.
- Continuity: recurring people stay recognisable, conflicts have
  consequences, and multi-episode arcs connect events across continents.

**Audio**

- A free, local TTS narrator. No paid speech APIs, and no recording another
  AI's voice through a microphone.
- Free or self-generated music and SFX that are safe for monetised YouTube.
- A professional mix: the narration must always stay clearly audible.

**Money**

- Zero additional spend: no billable APIs, no paid TTS, image, video or asset
  services, no paid cloud rendering, no new subscriptions.
- Don't bypass subscription limits or automate consumer UIs.

**Workflow**

- Treat the first render as a draft. Verify playback, inspect every scene,
  check narration, pronunciation, captions and sync, look for historical
  errors, fix them, and render again.
- Work autonomously.
- Don't build websites, dashboards, schedulers or uploaders.

**Deliverables** (every episode)

1. `Year_<N>_AD.mp4`
2. the narration script
3. the research document with sources
4. the source code and reusable assets
5. a short technical report
6. an honest assessment of whether this approach can produce two
   professional videos a day

---

## 2. What exists (repo map)

```
Testing/                          (github.com/Hiv3m1nd/Testing, branch ccr-7b5c772c-oaxbng)
├── HANDOFF.md                    ← this file
├── CLAUDE.md                     ← short standing rules (auto-loaded by Claude Code)
└── year-1-ad/
    ├── README.md                 pipeline overview + reproduce commands
    ├── research/research.md      1 AD dossier: every claim, status tag, sources, uncertainties, licences
    ├── script/narration.md       timecoded script (generated from src/script_data.py)
    ├── docs/technical_report.md  tools, constraints, QA log, numbers, 2-videos/day assessment
    ├── output/Year_1_AD.mp4      final film (≈4.2 Mbps, 90.4 MB, fits GitHub's 100 MB limit)
    ├── output/Year_1_AD_preview_720p.mp4    ≤30 MiB preview
    ├── output/master/            10.4 Mbps master split into <100 MB parts + SHA256SUMS.txt
    ├── assets/fonts/             OFL fonts + licence texts
    ├── assets/geo/               Natural Earth GeoJSON (public domain)
    ├── assets/tts/kokoro_config.json   Kokoro phoneme vocab
    └── src/                      the pipeline (see §4)
```

The following are **not** in git; regenerate them locally:

- `build/`: terrain tiles, textures, narration, timeline, frames and mixes.
- `models/`: the Kokoro weights.

---

## 3. Local setup (do this first; verify each step)

```bash
git clone https://github.com/Hiv3m1nd/Testing && cd Testing
git checkout ccr-7b5c772c-oaxbng
git checkout -b year-2-ad          # do the new work on its own branch

python3 -m venv .venv && . .venv/bin/activate     # Python 3.12 or 3.13
pip install onnxruntime onnx numpy scipy soundfile skia-python shapely pillow \
            opencv-python-headless numba librosa spacy phonemizer-fork espeakng-loader \
            num2words addict regex pocketsphinx jiwer
pip install --no-deps --ignore-requires-python misaki==0.9.4   # its metadata says <3.13; it works on 3.13
python -m spacy download en_core_web_sm                       # (cloud used conda-forge; locally this works)
# system packages: ffmpeg, espeak-ng (Linux also needs libegl1 libgl1 for skia-python)
```

**Kokoro TTS weights** (Apache-2.0). The official source is the HuggingFace
repo `onnx-community/Kokoro-82M-v1.0-ONNX`:

- `onnx/model.onnx` → save as `year-1-ad/models/kokoro-fp32.onnx` (≈326 MB, fp32)
- `voices/*.bin` → `year-1-ad/models/voices/` (at least `am_michael.bin`)

`src/tts.py` reads `KOKORO_DIR`; the default is `<episode>/models`. On first
use it writes a patched copy, `kokoro-fp32-dur.onnx`, which exposes the
duration predictor (see §9).

*The cloud session had no HuggingFace access, so it used byte-identical npm
mirrors. Locally, use the official repo.*

**Build data and smoke-test** (from `year-1-ad/src`):

```bash
python fetch_data.py      # AWS Terrain Tiles → build/tiles (~55 MB, 784 tiles)
python terrain.py         # → build/tex/{global,oldworld,mesoamerica}.png (+ land/elev .npy), ~1 min
python narrate.py         # → build/narration.wav + build/timeline.json  (expect "total 169.97s, 438 words")
python render.py --frames 2.5,45,70,100,140 --stills ../build/stills   # stills must match the 1 AD film
```

Only start 2 AD once the stills match the shipped film. That proves your
setup reproduces the house look.

---

## 4. How the pipeline works

Each module is marked as **generic** (reuse it as-is) or **episode-specific**
(rewrite it per episode).

| Module | Role | Type |
|---|---|---|
| `script_data.py` | Narration lines `(scene_tag, text, pause_after)`, with misaki phoneme overrides `[word](/phonemes/)` | **episode** |
| `narrate.py` | Kokoro TTS per line, trims silence, adds pauses, writes `narration.wav` and `timeline.json` (line start/end, **per-word timestamps**). Voice `am_michael`, speed 1.0, lead-in 1.2 s | generic |
| `tts.py` | Kokoro ONNX inference. Patches the graph to output per-phoneme durations (the `Clip` node after `Round`) → exact word times | generic |
| `timeline.py` | `TL().s(i)`, `.e(i)`, `.w(i, "word", nth=0, end=False)`: every animation keys off these | generic |
| `gfx.py` | Canvas (skia drawing into numpy), fonts, text with tracking/glow/reveal, easing, noise, bloom/grade/vignette/grain (`finish`), **palette constants** | generic |
| `globe.py` | Ray-cast globe: `Camera(lat, lon, dist, tilt, heading, fov, roll, shift_y)`, `fly()` for great-circle moves, `render()`, `project()` | generic |
| `terrain.py`, `fetch_data.py` | Elevation → natural, pre-modern relief textures (Aral restored, Texcoco refilled, reservoirs removed) | generic |
| `geo.py` | AD 1 frontiers (Rome, its clients, Parthia, Armenia, Han, Tarim, Kush), cities, routes, rivers (including the pre-AD 11 lower Yellow River); `fill_region`, `city_marker`, `region_label`, `line_path` | **mostly generic.** Borders change slowly; update them when history changes. Delete `build/geo_cache.pkl` after any border edit |
| `relief.py` | Height-field relief: coins (`coin_gaius_lucius`, `coin_musa`), marble and carved V-cut letters | generic engine; add new coins and inscriptions per episode |
| `environments.py` | Painted parallax environments: `rome()` at dusk and `changan()` at dawn; `compose(env, t, dolly, push, mist)` | generic engine + reusable scenes; add new places per episode |
| `fx.py` | Starfield, paper textures, dust, flare, **ink-brush character reveal**, red seals, the white pheasant, oil lamps, smoke, ship glyphs | generic |
| `scenes_a.py`, `scenes_b.py` | The twelve 1 AD shots, `s_*(t) -> float RGB`. They reference narration **line indices** | **episode** (copy the patterns, not the timings) |
| `captions.py` | Word-synced captions | generic |
| `render.py` | `SHOTS = [(fn, start, end)]`; overlaps are dissolves. 16 chunks × 4 processes → x264 segments → concat. `--frames`, `--from/--to`, `--only` | generic, but `SHOTS` and `END` are **episode** |
| `music.py` | Synth instruments + `compose()`, which **hard-codes 1 AD cues**; `mix()` with target-ratio ducking | instruments and `mix()` generic; **`compose()` episode** |
| `master.py` | Look-ahead limiter → exact gain to −14 LUFS (true peak ≤ −1 dBTP asserted) → H.264 High / AAC 320 k / faststart | generic |
| `qa_sheet.py`, `qa_asr.py` | QA helpers (§10) | generic |

**Fragility warning.** Scenes and music cues address narration by **line
index** (`T.s(11)`, `T.w(12, "Gaius")`). Insert a line and every later index
shifts. For 2 AD, consider adding a string `id` to each entry in `LINES` and
looking lines up by id (a small change to `timeline.py`). If you don't, fix up
the indices carefully after every script change.

---

## 5. Making 2 AD: step by step

1. **Copy the episode.** Copy `year-1-ad/` to `year-2-ad/`, excluding
   `build/`, `output/` and `models/`; symlink or copy `models/`. Keep 1 AD
   untouched as the reference.
   - Optional, longer term: factor the generic modules into a shared `engine/`.
     Only do this if it doesn't change the look.
2. **Research** (`year-2-ad/research/research.md`).
   - Use the same structure and status tags: **DATED 2 AD / CONTEXT / ESTIMATE
     / TRADITION / SETUP (3 AD)**.
   - You have normal internet access, so **read the primary texts**. The cloud
     agent could only search. Useful sources:
     - LacusCurtius: Velleius Paterculus II, Suetonius (*Augustus*,
       *Tiberius*), Cassius Dio LV
     - Perseus: Strabo, Josephus
     - ctext.org or zh.wikisource: *Hanshu* 12 (Pingdi ji), 99A (Wang Mang),
       28 (Dili zhi)
   - Verify every lead in §7 before using it.
3. **Story.** Choose the strongest supportable narrative. Pay off 1 AD's two
   promises: the census and the heir's death. See §7 for threads and ideas.
4. **Script** (`src/script_data.py`).
   - Hook first line.
   - About 400–440 words reads at about 2:45 with this voice at speed 1.0.
   - Add phoneme overrides for every non-English name. Reuse the existing ones
     verbatim (§8) so names sound the same across episodes.
5. **Narrate.** Run `narrate.py`, then check the total. Narration end plus
   ~4.5 s of end card must stay **≤ 3:00**; 1 AD aimed for 2:50–2:55.
6. **Shot design.**
   - Write the shot functions and update `render.py` `SHOTS` and `END`.
   - Reuse engines; add new assets where the story needs them (new coin,
     place or diagram). Vary the forms; don't clone 1 AD's sequence.
   - Check each shot with `qa_sheet.py` at 4–8 times **before** a full render.
7. **Score.** Rewrite `music.compose()` cues for the new timeline. Keep the
   instrument palette and harmonic language (§8). Then run `music.py`.
8. **Draft render.** Run `render.py --out ../build/video_v1.mp4`. It took
   ~46 min on 4 cores; more cores are faster.
9. **QA (§10).** Fix, then re-render only the affected chunks with
   `--only i,j,…`. If a change spans a chunk boundary, re-render both chunks.
10. **Master and deliver (§6).** Then update the README, write the technical
    report and commit.

---

## 6. Delivery recipe (what 1 AD shipped; do the same)

```bash
python master.py ../build/video_v2.mp4 ../build/Year_2_AD_master.mp4 --crf 19 --maxrate 12M   # ~10 Mbps master
# web copy that fits GitHub's 100 MB/file limit (two-pass, ~3.9 Mbps video + 256k AAC):
ffmpeg -y -i ../build/video_v2.mp4 -i ../build/mix_final.wav -map 0:v:0 -c:v libx264 -preset slow -profile:v high \
  -level 4.2 -pix_fmt yuv420p -b:v 3900k -maxrate 6M -bufsize 12M -pass 1 -passlogfile x264web -an -f mp4 /dev/null
ffmpeg -y -i ../build/video_v2.mp4 -i ../build/mix_final.wav -map 0:v:0 -map 1:a:0 -c:v libx264 -preset slow \
  -profile:v high -level 4.2 -pix_fmt yuv420p -b:v 3900k -maxrate 6M -bufsize 12M -pass 2 -passlogfile x264web \
  -c:a aac -b:a 256k -ar 48000 -movflags +faststart -shortest ../output/Year_2_AD.mp4
# master into <100 MB parts for git:
split -b 90M -d -a 2 ../build/Year_2_AD_master.mp4 ../output/master/Year_2_AD_master.mp4.part-
```

Watch the bitrate budget: about 3.9 Mbps fits under 95 MB only at about
2:55. Recompute for the actual runtime:
`bitrate_kbps ≈ 95e6*8/seconds/1000 − 256`.

**Verify before calling it done** (all of these passed for 1 AD):

- `ffmpeg -v error -i Year_2_AD.mp4 -f null -` prints nothing.
- `ffprobe` shows 1080×1920, 30/1, the expected frame count and the duration.
- `ffmpeg -i Year_2_AD.mp4 -vn -af ebur128=peak=true -f null -` shows
  **I = −14.0 LUFS** and true peak **≤ −1.0 dBFS**.
- Narration offset is 0 ms: cross-correlate the final audio against
  `build/narration.wav`.
- Commit `output/Year_2_AD.mp4`, the master parts, script, research, report and
  code. Never commit `build/`, `models/` or any file over 100 MB.

---

## 7. Series bible: continuity for 2 AD

### What 1 AD established (keep these consistent)

**Rome**

- **Augustus**
  - Born 23 Sep 63 BC, so he was 62–63 in AD 1 and turns 64 in Sept AD 2 (no year zero).
  - On screen: "born 63 BC · in power since 31 BC".
- **Gaius Caesar**
  - Born 20 BC.
  - Consul in AD 1; in the East, facing Parthia over Armenia.
  - On screen: "consul, 1 AD · aged about 20".
- **Lucius Caesar**
  - Born 17 BC.
- **Shared by Gaius and Lucius**
  - Both are Augustus's grandsons, adopted as his sons in 17 BC.
  - Both are shown on the **Gaius & Lucius denarius**, `relief.coin_gaius_lucius()`.
- **Julia**
  - Augustus's daughter and the mother of Gaius and Lucius.
  - Exiled to **Pandateria** in 2 BC.
- **Tiberius**
  - Augustus's stepson.
  - Withdrew to **Rhodes** in 6 BC and was refused permission to come home.

**Parthia**

- **Phraates V (Phraataces)**, a young king, rules beside his mother **Musa**.
- Josephus calls her an Italian slave girl, a gift from Augustus.
- Her portrait is on the coins: `relief.coin_musa()`, legend ΘΕΑΣ ΟΥΡΑΝΙΑΣ
  ΜΟΥΣΗΣ ΒΑΣΙΛΙΣΣΗΣ.
- Armenia is contested and is drawn hatched.

**Han**

- **Emperor Ping** (漢平帝): born 9 BC, a boy of "about nine" in AD 1.
- **Wang Mang** (王莽): born c. 45 BC, regent; "aged about 45" on screen.
  - In AD 1 he engineered the **white pheasant** omen (Duke of Zhou parallel)
    and received the title **安漢公 Ānhàn Gōng, "Duke Who Secures the Han"**.
  - Source: *Hanshu* 99A.
- Era **Yuanshi 元始**, AD 1–5. So **AD 2 = 元始二年, Yuanshi year 2**.
- Grand Empress Dowager **Wang Zhengjun** is his aunt (mentioned in research,
  not on screen).

**Elsewhere**

- Silk and the monsoon trade (Strabo: up to 120 ships a year from Myos Hormos).
- Teotihuacan, the Maya, Kush and Germania were deliberately held back for
  later episodes.

### The two promises 1 AD made, which 2 AD must pay off

1. **"Next year, the Han will count their people: nearly sixty million."**
   - The census of Yuanshi 2, preserved in the *Hanshu* geography treatise
     (Dili zhi).
   - It records 12.2–12.4 M households and **57,671,400 or 59,594,978
     individuals**. The two totals differ by source and method; note both.
   - 1 AD's counter ended at **59,600,000** with "one dot = 100,000 people".
     Stay consistent with that.
2. **"And in Rome, one of the two heirs will not live to see the year's end."**
   - **Lucius Caesar died at Massilia on 20 Aug AD 2**, aged 18, of illness,
     on his way to the armies in Spain.
   - 1 AD deliberately didn't say which heir. It ended on **two Roman oil lamps
     with the right-hand one going out** (`fx.oil_lamp`, `fx.smoke`). A strong
     continuity device is to open 2 AD on those lamps.

### Leads for 2 AD (all to be verified against primary texts first)

- **Tiberius returns to Rome in AD 2.** Augustus allowed it with Gaius's
  consent; he lived as a private citizen (Suetonius *Tib.* 13–15). The cloud
  agent confirmed AD 2 by search.
- **The Euphrates summit.** Gaius and Phraataces met on an island in the
  Euphrates, with feasts on both banks.
  - Velleius Paterculus was an **eyewitness** (II.101). Most scholars date it
    to AD 2; livius.org says AD 1. Flag the date as debated.
  - Reported outcome: Parthia accepts Roman primacy in Armenia, and
    Phraataces's half-brothers stay in Rome. Verify.
  - 1 AD deliberately did **not** show this meeting; it was reserved for 2 AD.
- **Marcus Lollius.** Gaius's adviser was exposed (reportedly by Phraataces)
  for taking bribes from kings and died soon after (Velleius II.102; Pliny,
  *NH* 9.118). Verify.
- **Han, Yuanshi 2.** Drought and locusts are reported in the east (esp.
  Qingzhou), with relief measures and Wang Mang's conspicuous donations
  (*Hanshu* 12/99A). Verify the wording and details before use.
- **Future arcs. Don't spoil these; foreshadow at most.**
  - Rome:
    - Gaius is wounded at Artagira (9 Sep AD 3) and dies at Limyra
      (21 Feb AD 4).
    - Tiberius is adopted in AD 4.
    - The Varus disaster (Teutoburg) comes in AD 9.
    - Augustus dies in AD 14.
  - Han:
    - Wang Mang's daughter marries Emperor Ping in AD 4.
    - Ping dies in AD 6.
    - Wang Mang founds the Xin dynasty in AD 9.
    - The Yellow River shifts course in AD 11.
    - Wang Mang falls in AD 23.
  - Parthia: Musa and Phraataces are deposed c. AD 4.

### The setup for 3 AD

Pick something securely dated to AD 3 and set it up as accurately as 1 AD set
up AD 2. One known AD 3 event is Gaius being wounded at Artagira; verify it.

---

## 8. House style (keep identical for consistency)

**Branding and titles**

- Series name: **YEAR BY YEAR**. Tagline: *the human story, one year at a time*.
- Year format on screen: **"2 AD", "4 BC"**, in every title, label and
  timeline. The narration says "A D" through the `[AD](/ˌAdˈi/)` override.
- **Opening.** "YEAR BY YEAR" tag at the top (Cinzel 34, tracking 0.5, pale
  gold, y≈200). The big year title is Cinzel ~230, pale gold with a gold glow.
  1 AD opened on the night globe with a dawn rim; vary it, but keep the title
  treatment.
- **End card.** "NEXT EPISODE" / **"3 AD"** (Cinzel 240, gold glow) / "YEAR BY
  YEAR" / tagline, on dark parchment with dust, then a 0.7 s fade to black.

**Palette** (`gfx.py`): use these colours for these powers in every episode.

| Constant | RGB | Used for |
|---|---|---|
| `ROME` | (0.80, 0.16, 0.20), crimson | Rome; its client kingdoms are the same colour at lower alpha |
| `PARTHIA` | (0.18, 0.66, 0.62), teal | Parthia |
| `HAN` | (0.93, 0.52, 0.16), amber | Han |
| — | grey, hatched | Armenia (contested) |
| `GOLD`, `PALE_GOLD`, `IVORY` | — | UI and type |

**Fonts** (OFL, in `assets/fonts`)

- **Cinzel**: Roman capitals, titles and map labels.
- **Cormorant Garamond** and its Italic: subtitles, translations, pinyin with
  tone marks (Cinzel lacks them).
- **Inter 600**: captions.
- **LXGW WenKai TC Bold**: Chinese brush characters.
- **Noto Serif TC**: seals and Greek legends (Cinzel and Garamond lack Greek).
- Avoid "⅓"-style glyphs; most of these fonts lack them.

**Chinese text:** always traditional characters (漢, not 汉), in the Kai brush
face, revealed with `fx.ink_char`. Red seals come from `fx.seal`.

**Captions**

- Inter 600 at 50 px, baseline y=1468, max width 820 px, ≤ 7 words per chunk,
  breaking at punctuation.
- The spoken word is highlighted in pale gold. A soft dark rounded box sits
  behind the text.
- **Safe zones:** keep important text roughly between y≈150 and y≈1320. Keep
  the bottom ~22% and the right ~120 px clear (platform UI).

**Look**

- Every frame goes through `gfx.finish()`: bloom, vignette, warm/cool split
  grade, fine grain 0.022.
- Map style: realistic, pre-modern terrain under a dark documentary grade.
  Empire fills sit at about 0.3–0.4 alpha with glowing edges.
- Labels: Cinzel with a soft shadow; city markers are gold dots with a halo.

**Narration**

- Voice **Kokoro `am_michael`, speed 1.0**, lead-in 1.2 s.
- Pauses: 0.2–0.4 s within a scene, 0.7–0.9 s at scene changes.
- Tone: intelligent, dramatic and plain-spoken. Short sentences; one idea per
  line.
- Attribute contested claims in the sentence itself ("Josephus says…", "the
  official history notes…").
- Start with a hook line. End with the next-year setup, leaving some mystery
  without misleading.

**Pronunciation overrides already in use.** Reuse these exactly, so names
sound identical across episodes:

```
[AD](/ˌAdˈi/)  [BC](/bˌisˈi/)  [Gaius](/ɡˈIəs/)  [Lucius](/lˈusiəs/)  [Aemilius](/imˈɪliəs/)
[Paullus](/pˈɔləs/)  [Han](/hˈɑn/)  [Yuanshi](/juˈɛn ʃˈɜɹ/)  [Seres](/sˈɪɹiz/)  [Musa](/mˈusə/)
[Strabo](/stɹˈAbO/)  [Chang'an](/ʧˌɑŋˈɑn/)  [Wang Mang](/wˈɑŋ mˈɑŋ/)  [Zhou](/ʤˈO/)
[Dionysius Exiguus](/dˌIənˈɪsiəs ɛɡzˈɪɡjuəs/)
```

New names likely in 2 AD and suggested starting points (check the misaki output first):

- Massilia → `/məsˈɪliə/`
- Phraataces → `/fɹˌAətˈAsiz/`
- Velleius → `/vəlˈAəs/`
- Lollius → `/lˈɑliəs/`
- Qingzhou → `/ʧˈɪŋ ʤˈO/`

**Music palette**

| Element | Detail |
|---|---|
| Pads | D minor / Dorian additive pads with low drones |
| Rome | Karplus–Strong lyre arpeggios |
| China | Pentatonic guqin plucks (A minor pentatonic), gongs |
| Parthia | Ney flute in D Phrygian dominant |
| Rhythm and impacts | Frame drums for momentum; booms on title hits |
| Sound effects | Whooshes on camera flights; chisel taps for inscriptions; brush whooshes for calligraphy; singing bowls for omens |

**Mix targets**

- Music sits about 18–20 dB under the voice in the speech band. Use
  `target_ratio_gain` with music 11/5 and SFX 13/0; don't use fixed ducking.
- **No compressor on the voice.** It hurt intelligibility.
- Master to **−14.0 LUFS**, true peak **≤ −1 dBTP**, LRA about 2.5–3 LU.

---

## 9. Hard rules and lessons learned (things that bit me)

**Accuracy and licences**

- Never invent events or quotes. If a year is quiet, say so and use the
  ongoing threads.
- Every on-screen number needs a line in the research document.
- Mark illustrations as illustrations. In 1 AD that covered the inscription,
  the coins, the environments, the pheasant and the night lights.
- **Licences must allow commercial/monetised use.** Allowed: Apache, MIT, OFL,
  CC0, public domain, open data with attribution.
- Not allowed:
  - XTTS (CPML)
  - MusicGen (CC-BY-NC)
  - SD-Turbo and other non-commercial weights
  - anything CC-BY-SA dropped into the video
  - unlicensed stock

**TTS**

- **Kokoro word timing.** `tts.patch_model` adds the graph's `/encoder/Clip`
  output (durations in frames) as a second output. One frame is 600 samples
  at 24 kHz. Keep this: it drives captions and all cue timing.
- Numbers are spoken as words ("1 AD" → "one A D").
- Multi-word overrides become one timed "word" in the captions; that's fine.

**Fonts and globe**

- skia-python needs `libEGL`/`libGL` on Linux.
- Variable-font weights are set through `gfx.font(name, size, weight)`.
- **Globe performance:** 1.5–4 s per frame on 4 cores at 1080×1920; it
  dominates render time. Stay above `dist ≈ 0.3` Earth radii, because lower
  views get blurry (texture is ~42 px/°).
- `glint` above about 0.3 causes white smudges.
- An object behind the globe needs `project_xyz`, which handles occlusion;
  `project` only handles the front side of the globe.

**Rendering and QA**

- **Render chunks.** Segments must use identical x264 settings so they can be
  stream-copied together.
- `--only` re-renders specific chunks. For 16 chunks a chunk is
  `END*30/16` frames, about 10.85 s.
- Python modules load once per worker. Editing a file mid-render doesn't
  affect the running render.
- **QA by thumbnail lies.** Small contact sheets show phantom doubled text and
  faint captions mid-fade. Always confirm a suspected defect on a
  full-resolution frame before "fixing" it.

**Audio**

- `ffmpeg loudnorm` falls back to *dynamic* mode when it can't meet the
  true-peak target linearly. That's why `master.py` uses the limiter followed
  by an exact gain instead.
- **ASR as an objective proxy.** pocketsphinx WER on the dry voice was 0.37,
  and 0.57–0.58 on the final mix (proper nouns inflate it). If the mix jumps
  far above the dry voice, the bed is too loud. A human ear is still the real
  test; ask the user to listen if you can't.

**Delivery**

- **GitHub:** 100 MB per-file limit. Commit the ~95 MB web encode plus the
  master split into parts, with a SHA-256 file.
- The Claude app's file send was limited to 30 MiB in the cloud session; a
  720p ~1.2 Mbps preview fit.

---

## 10. QA procedure (do all of it; 1 AD found 12 defects this way)

1. Per shot, before rendering, run `python qa_sheet.py scenes_x s_shot t1,t2,…
   name.jpg`. Look at titles vs. caption zone, label collisions, contrast on
   bright backgrounds, and empty frames between beats.
2. After the draft render:
   - Make the contact sheet: `ffmpeg -i video.mp4 -vf
     "fps=0.5,scale=180:320,tile=8x6" sheet_%02d.jpg`.
   - Then pull full-res frames of anything suspicious: `ffmpeg -ss T -i
     video.mp4 -frames:v 1 f.png`.
3. Check every transition (dissolve overlaps) and every word-timed reveal: no
   dead air, and no title colliding with another title.
4. Audio:
   - `ebur128` loudness.
   - Per-line voice-minus-bed in the >150 Hz band (see the 1 AD session
     method in the technical report).
   - `qa_asr.py` on the dry voice and on the mix.
   - Look at the spectrogram: `ffmpeg -i mix.wav -lavfi
     showspectrumpic=s=1600x500:scale=log:fscale=log spec.png`.
5. Historical pass. Re-read every caption and on-screen label against
   `research.md`: dates, ages, spellings and year format.
6. Fix the problems, re-render the affected chunks, then repeat steps 2–5 on
   the new cut.

---

## 11. Known weaknesses to improve, without breaking consistency

**People and daily life.** 1 AD had none, so this is the biggest gap.
Locally, with network access, two options:

- **CC0 museum imagery:** the Met Open Access API, Smithsonian, Cleveland,
  Art Institute of Chicago. Use real artifacts: portrait busts of Augustus,
  Gaius and Tiberius; Han tomb figurines and bricks. Animate them with the
  existing parallax and relief tools, and credit them in the research
  document.
- **A permissively licensed local image model,** if the machine has a GPU and
  the licence allows commercial use. Verify both.

**Voice.** `am_michael` is clear but not warm. Keep it for consistency unless
the user approves a change. If you test alternatives, ask the user before
switching voices mid-series.

**Music.** It is procedural and functional. Keep the palette; small gains
would come from better voicing and reverb, not a new style.

**Index-based timing.** Fragile; see §4.

---

## 12. How the user likes to work

- Works on a phone through the Claude app. Give short progress lines during
  long jobs.
- Expects autonomy: don't ask about implementation choices.
- Ask only for genuinely theirs-to-decide items: changing the voice, or
  anything that would cost money.
- Wants a downloadable link at the end. The repo `Hiv3m1nd/Testing` is
  **public**, so give a `raw.githubusercontent.com/.../<branch>/<path>` link
  after pushing, plus a GitHub page link.
- Prefers honesty about limitations over polished claims.
