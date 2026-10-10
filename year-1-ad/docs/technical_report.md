# Technical report — "Year by Year: 1 AD"

## 1. What was built

`output/Year_1_AD.mp4` is a 2 min 53.6 s vertical documentary (1080 × 1920,
30 fps, H.264 High / AAC-LC 48 kHz, −14 LUFS). Every pixel and every sample was
made by code in this repository:

- A narrator voice synthesised locally.
- A ray-cast 3D globe with real terrain and reconstructed AD 1 frontiers.
- Relief-lit coins and a carved inscription.
- Painted parallax environments.
- Brush-ink calligraphy, particles, typography and captions.
- A procedurally synthesised score and sound design.

There is no stock footage, no AI video service and no paid API. Generation
cost: **$0**.

## 2. Environment and constraints actually encountered

| Constraint | Effect | What I did |
|---|---|---|
| Cloud container: 4 CPU cores, 15 GB RAM, **no GPU** | No GPU rendering, no diffusion models | Wrote a CPU renderer in numpy/OpenCV/Skia; parallelised over 4 processes |
| **Network allow-list**: HuggingFace, Natural Earth CDN, Wikipedia, museum APIs and NASA were all blocked; PyPI, npm, conda-forge, GitHub raw/codeload and AWS S3 were reachable | The usual model and data hosts were unavailable | Kokoro weights from an Apache-2.0 npm mirror (with your approval, checksum-verified); Natural Earth vectors from GitHub raw; terrain from AWS Terrain Tiles; spaCy model from conda-forge |
| The **auto-mode safety classifier** refused to assemble model weights from an unofficial mirror | Blocked the TTS until you approved | Asked you; you chose the npm mirror. The q8 file matched its published SHA-256, and I compared fp32 against q8 |
| **No image generation**: I'm Claude, not Codex, so GPT Image wasn't available, and no local diffusion model could be fetched or run usefully on CPU | No AI stills at all | Everything is procedural: map, globe, coins, stone, ink, architecture, the pheasant |
| **I can't hear audio** | Couldn't judge the voice or the music by ear | Objective proxies: pitch analysis to choose the voice; EBU R128 loudness; per-line voice-to-bed ratios; spectrogram inspection; ASR word error rate on the mix vs. the dry voice |
| WebFetch blocked as well | No reading of full source pages | Verified claims with multiple web searches; primary texts cited by standard reference (see `research/research.md`) |

## 3. Pipeline and tools

| Stage | Tooling | Notes |
|---|---|---|
| Script | `src/script_data.py` | Lines tagged by scene, with inline phoneme overrides for names (Wang Mang, Yuanshi, Exiguus, …) |
| Voice | **Kokoro-82M** (fp32 ONNX) through **onnxruntime**; **misaki** G2P + spaCy + espeak-ng fallback | Voice `am_michael`, chosen for its low (110 Hz), expressive and unhurried delivery. ~4× faster than real time on CPU |
| Word timing | I patched Kokoro's ONNX graph to **expose the duration predictor's per-phoneme frame counts** as a second output | Exact word timestamps with no ASR or forced alignment. Every caption, cut, title reveal and sound cue keys off these |
| Terrain | AWS Terrain Tiles (z4 global, z6 Old World and Mesoamerica) → equirectangular reprojection → multi-directional hillshade + natural palette | Water mask from Natural Earth: reservoirs removed, the **Aral Sea restored** to its pre-1960 shoreline, **Lake Texcoco refilled** |
| Globe | `globe.py`: per-pixel ray–sphere intersection in numpy, textures sampled with `cv2.remap`, mip selection by pixel footprint | Sun lighting and terminator, ocean glint, limb haze, an atmospheric rim; perspective camera with tilt and heading; great-circle "flight" interpolation |
| History layer | `geo.py`: hand-built AD 1 outlines clipped to coastlines with **shapely** | Rome, client kingdoms, Parthia, Armenia (contested), Han, the Tarim protectorate; the pre-AD 11 lower Yellow River |
| Relief | `relief.py`: masks → height fields (multi-scale blur or distance-transform V-cuts) → normals → moving light | The Gaius & Lucius denarius and Musa's drachm, recreated after the real coin types; a rubricated consular inscription |
| Environments | `environments.py`: Skia silhouettes in 5–6 depth layers with haze, god-rays from radial blur, animated mist, dust | Rome at dusk; Han Chang'an at dawn |
| Typography and FX | **skia-python** (anti-aliased paths, variable fonts, blur filters) | OFL fonts: Cinzel (Roman capitals), Cormorant Garamond, Inter (captions), LXGW WenKai TC (brush Kai), Noto Serif TC |
| Edit | `render.py`: shot list with overlap dissolves; 16 chunks × 4 processes; x264 per chunk, then concat | Captions burned in, kept clear of the platforms' UI safe zones |
| Music and SFX | `music.py`: additive pads, Karplus–Strong lyre/guqin (numba), inharmonic gongs and bowls, frame drums, a ney-like flute line, impacts, whooshes, chisel taps, wind, convolution reverb | All cues timed from the narration. The bed is ducked to a **target voice-to-music ratio** rather than a fixed amount |
| Master | `master.py`: two-pass `loudnorm` to −14 LUFS / −1 dBTP; H.264 High 4.2, AAC 320 k, faststart | |

## 4. What worked well

- **Narration-driven timing.** Patching the TTS graph so it reports durations
  turned out to be the most valuable trick. Captions are word-exact, and the
  whole edit re-flows automatically if a line changes.
- **The procedural globe.** Continuous camera flights (Rome → Pandateria →
  Rhodes → Euphrates → Indian Ocean → Chang'an) give the film a real sense of
  geography and motion, and they carry the narrative as one move rather than a
  set of slides.
- **Relief rendering** made the coins and the inscription look physically
  lit. It costs almost nothing per frame.
- **Brush-ink reveals and seals** for the Chinese sequences, which use
  traditional characters in a Kai brush face.
- **Research discipline.** Every claim is tagged DATED / CONTEXT / ESTIMATE /
  TRADITION, the narration attributes contested claims ("Josephus says…", "the
  official history notes…"), and the setup for 2 AD is accurate.

## 5. Limitations and honest weaknesses

- **Illustration ceiling.** Without generative imagery, people appear only as
  coin figures, names and silhouettes; there are no faces or scenes of daily
  life. The environments are stylised silhouettes, not photoreal sets. A
  local image model (e.g. FLUX-schnell on a GPU) or permitted museum
  photography (CC0) would lift this considerably.
- **Voice.** Kokoro's male voices are its weaker voices. The read is clear and
  well paced, but a human narrator or a larger expressive TTS would add
  warmth and emphasis. Pronunciation of Chinese names is an English
  approximation.
- **Music.** The procedural score is functional and culturally coloured
  (Dorian/minor pads, a pentatonic guqin for Han China, a Phrygian-dominant
  ney for Parthia), but it isn't composed music. Verified objectively only.
- **Borders** are hand-drawn approximations, documented as such.
- **Render time.** About 45 min for the full film on 4 CPU cores; globe frames
  dominate at 1.5–4 s each.

## 6. Measured numbers

| Item | Value |
|---|---|
| Runtime | 2:53.6, under the 3:00 Shorts/Reels limit |
| Narration | 438 words, 31 lines, 2:50 of speech; ~45 s to synthesise on CPU |
| Frames | 5,208 at 30 fps, 1080×1920 |
| Full render, 4 CPU cores | 46 min (globe frames 1.5–4 s each; coins, paper and type 0.2–0.8 s) |
| Partial re-render after QA (11 of 16 chunks) | ~25 min |
| Audio | −14.0 LUFS integrated, ≤ −1 dBTP, LRA ≈ 2.5 LU; voice ≈ 18–20 dB above the bed in the speech band during narration |
| Cost | $0 (local compute, free/open data and models) |
| Agent wall-clock, start to delivery | ≈ 3 h, including building every tool from scratch |

## 7. Assessment: two professional-quality episodes per day, with minimal human intervention?

**Short answer:**

- **Compute is not the constraint:** two renders a day cost about 1.5 CPU-hours.
- **Editorial quality is.**
- With the toolkit built here, **two good, accurate episodes per day are
  feasible with roughly 20–30 minutes of human review per episode.**
- **"Professional" at a broadcast level** additionally needs a better voice
  and a way to show people and daily life.

**Why it scales**

- Most of this session went into reusable infrastructure: globe and flights,
  historical borders, relief artifacts, painted environments, ink calligraphy,
  captions, music engine, mastering.
- A new episode is mostly data: a script with scene tags, a few camera
  keyframes, border tweaks, and one or two new artifacts or environments.
- Timing flows from the narration automatically.
- An agent can plausibly take an episode from research to master in **2–4
  hours** of unattended work. Two parallel sessions cover a morning BC
  release and an evening AD release.

**What still needs a human, and why**

1. **Fact review of the script, about 10–15 min.**
   - Accuracy is the brand. Agents can verify a lot, but they can still
     mis-date events or over-read a source. This session's sandbox couldn't
     even open primary pages.
   - A historian-in-the-loop sign-off on `research.md` before rendering is
     cheap insurance.
2. **Final watch, about 5–10 min.** Catch visual glitches and pronunciation
   that the automated checks miss. I couldn't listen to my own audio; a human
   ear can.
3. **Quiet years.**
   - Many years, especially deep BC, have few securely dated events. The
     series needs an editorial policy so the system never pads or invents:
     - Continue the multi-year threads.
     - Do regional deep-dives.
     - Run "state of the world" episodes.
     - Allow shorter runtimes.
   - That's a human decision about format, not an automation problem.

**Gaps to close for higher production value**

- **Imagery of people and places.** A GPU plus a permissively licensed local
  image model, or network access to CC0 museum collections (the Met,
  Smithsonian, Cleveland), would add portraits, artifacts and scenes of daily
  life. The parallax and relief pipeline here can animate either.
- **Voice.** Kokoro is clear but not warm. A larger local expressive TTS on a
  GPU, or a consistent licensed narrator voice, would lift perceived quality
  more than any visual change.
- **Variety at volume.**
  - At two episodes a day, repetition becomes the main risk.
  - Grow the template library deliberately: battles and troop movements, city
    reconstructions, trade and data visualisations, dynasty and family trees,
    inscriptions in many scripts, artifacts from each culture.
  - Track which templates each episode used.
- **Series memory.**
  - Keep a running "story bible" in machine-readable form: characters, ages,
    open threads, the borders' state per year.
  - Every episode then inherits continuity. `research.md` and `geo.py` are its
    seed.

**Verdict:** the approach works and is economically trivial to run. With a
light daily human editorial pass, it can sustain two credible, accurate,
visually distinctive episodes per day. With a GPU-backed voice and image model
added, it would approach professional documentary quality at that cadence.
