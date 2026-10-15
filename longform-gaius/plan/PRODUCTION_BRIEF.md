# Production brief: cold open of "Gaius Caesar: The Heir Who Never Came Home"

Long-form #1 (weekly profile). This brief covers **only the cold open**, the first slice the owner will review before approving the rest of the film. Written 2026-10-15 ~08:55Z.

**Sources:**
- `A_plan_and_visual_bible.md`, `B_user_directives.md`, `C_assets_sources_research.md`, `D_audio_voice_music.md`
- The real-image and HDR-test findings. Their REPORT.md files were never written; the content was passed on as text.
- Script v3 (`_extract_latest.txt` from line 599).
- The code and stills already in `longform-gaius/src` and `longform-gaius/build`.

---

## 0. Decisions at a glance

| # | Decision |
|---|---|
| 1 | **Scope.** Deliver the complete v3 cold open, **0:00–0:48.2**: narration runs 3.2–44.05 s, then the title holds. A hard 30 s cut would fall in the middle of "he asked to walk away" (line 5 runs 28.86–34.01 s) and before the title hit. Delivering everything up to the title hit is the honest version of "the first 30 seconds". |
| 2 | **Format.** Rendered natively at **3840×2160, 24 fps**, with a **2.39:1 letterbox** (active picture 3840×1606, bars 277 px). Frames are made in scene-linear light. Deliverables: an **HDR10 master** (HEVC Main10, PQ, BT.2020) and an **SDR BT.709 companion**, both graded from the same linear frames. There is no upscale and no SDR→HDR LUT (those were v1's weaknesses). |
| 3 | **Look.** This keeps the carved world from the v2 plan ("he survives today almost only in stone and metal") but builds it in real 3D: ray-traced ruins, depth-lifted real marble, carved and gilded inscriptions. It drops the Shorts' painted environments entirely, because that reuse is why v1 "looked like a Short". |
| 4 | **Directing idea.** **One flame.** A single torch is the only warm light in the cold open, and it stands for him. It finds the tomb, passes over his face and then Augustus's, and reads his name, titles and future in the stone. On "walk away" it walks away; on "home" it gutters and dies. Darkness and silence follow. Then his name is struck out of the dark in gold, with one deep hit. |
| 5 | **Real visuals in this slice:** the real terrain and coast of Lycia (Copernicus DEM + Sentinel-2), the Met's "possibly Gaius" head, and the Met's Augustus portrait. Each is lifted to 3D and relit by the torch. The ruins, coin and inscriptions are code-built and labelled "illustration". |
| 6 | **Voice.** Kokoro `bm_lewis`, speed 0.95, British G2P. It is already narrated (`build/narration.wav`, `build/timeline.json`, 48.05 s). |
| 7 | **Music.** A new code-synthesized "orchestra" (bowed strings, low brass, modal drums, hall convolution), so it isn't the Shorts' pad-and-lyre palette. It includes **real silences** and a **single deep hit on "Gaius"**. The theme is only hinted: the full theme is saved for the adoption, and the series bell for the film's last frame. |
| 8 | **Accuracy.** Narration stays exactly as v3. On-screen fixes: "Prince of Youth" (not "Leader of the Youth"); the Augustus portrait is posthumous; the coin should read as silver; "tomb" is never "empty". A tagged `research.md` table is in §9. |
| 9 | **Process.** Per-shot stills → 1080p SDR draft with audio → full QA → partial re-render → quarter-res HDR pre-pass for MaxCLL/FALL → 4K HDR10 + SDR master → verify → deliver files → commit code only. After the whole film is built, run a second polish pass that improves without replacing (§11). |

---

## 1. Where the build stands (observed 08:48–08:53Z)

| Item | State |
|---|---|
| Narration | Done. `build/narration.wav` (24 kHz float) and `build/timeline.json` with word times, 48.05 s. `script_coldopen.py` holds v3 verbatim: `VOICE = "bm_lewis"`, `SPEED = 0.95`, `LEAD_IN = 3.2`. "Gaius" phonemizes as `ɡˈIəs` (verified in the timeline). |
| Engine | `hfr.py` traces heightfield reliefs (portraits, coin, slabs). `sdf.py` is the sparse SDF voxel tracer (ruins). `terrain_night.py` does the DEM + Sentinel-2 flight. `portrait.py` and `depth.py` do Depth Anything V2 **Small** (Apache-2.0) lifting. `carve.py` cuts and gilds letters. `coin.py` builds the RIC I 207 reverse. `post.py` handles DoF, bloom, glare, flame, embers, motes, grain, labels. `hdr.py` has the PQ and SDR transforms. `film.py` handles the edit, chunked encode and HDR10 command. |
| Edit | `shots.EDIT`: 8 shots, `DURATION = 48.2` s (§3). |
| Draft | `film.py --from 0 --to 48.2 --width 1920 --sdr-only --tag draft1` was running: about 2 s/frame at 1080p, so the 1,157 frames take about 40 min. |
| Stills | `build/stills/t*.png` (960 px). The QA findings from them are in §10. |
| Not started | Score, SFX, ambience, mix and master; tagged `research.md`; HDR pre-pass; 4K master. |

---

## 2. Narration: script v3 cold open, verbatim, with show notes

> (SHOW: Night. A torch moves slowly through the ruins at Limyra, over carved stone, broken columns and dust drifting in the light. It has to look beautiful: real light and depth, never a picture that just pops up. MUSIC: one low drone and the crackle of the torch.)
>
> Near the southern coast of Turkey, among the ruins of an ancient town, stands a tomb built for a Roman prince.
>
> The young man it was built for was supposed to inherit the Roman world. His grandfather, Augustus, the master of that world, had planned his entire life for him: his name, his titles, his future. Rome even put his name on its coins.
>
> And then, at twenty-two, with all of it finally within reach, he asked to walk away.
>
> He never made it home.
>
> This is the story of Gaius Caesar: the boy who was given everything, except a choice.
>
> (SHOW: the title is carved into the stone and catches gold as the light passes. MUSIC: a single deep hit on "Gaius Caesar".)

The owner's standing notes that apply here:
- The tomb is "just a tomb", never "empty".
- Real ruins must be "worked and beautiful, never a pasted image".
- The hook must pay off cleanly.
- His instructions are never spoken in the narration.

### 2.1 Measured timeline (seconds; `build/timeline.json`)

| Line | Start–end | Cue words (word onset) |
|---|---|---|
| lead-in | 0.00–3.20 | (torch crackle and drone only) |
| l1 | 3.20–10.20 | Turkey 4.56 · ruins 5.91 · tomb 8.33 · prince 9.78 |
| l2 | 11.20–15.70 | young 11.38 · inherit 14.10 · world 15.28 |
| l3 | 16.15–24.50 | grandfather 16.41 · Augustus 17.23 · master 18.23 · **name 22.51 · titles 23.31 · future 24.06** |
| l4 | 25.05–27.56 | Rome 25.16 · name 26.31 · **coins 27.01** |
| l5 | 28.86–34.01 | And 28.91 · twenty-two 29.56 · reach 32.01 · **walk 33.34 · away 33.59** |
| l6 | 35.11–36.50 | He 35.19 · never 35.39 · **home 36.12** |
| l7 | 38.10–40.42 | This 38.18 · **Gaius 39.63** · Caesar 40.01 |
| l8 | 40.97–44.05 | everything 42.23 · except 43.05 · **choice 43.60** |
| title hold | 44.05–48.20 | fade to black 47.0–48.2 |

Every picture and sound cue is keyed to these word times through `shots.word(line, word)`. Do not hard-code seconds. If the narration is ever re-voiced, the cues follow automatically.

---

## 3. Shot list (times fitted to the narration)

Overlaps are eased dissolves of picture and grade. Global fade from black over 0–1.4 s and to black over 47.0–48.2 s. **Every shot moves** (the C2 rule: no static frames).

| # | Shot (`shots.py`) | In–out (s) | Over | Picture | Camera and light | On screen | HDR peaks (nits) |
|---|---|---|---|---|---|---|---|
| A | `shot_aerial` | 0.0–6.6 | lead-in, l1 "Near the southern coast of Turkey, among the ruins…" | **Real** moonlit Lycian coast: Copernicus DEM heightfield draped with Sentinel-2 colour, Finike bay, the Arykanda valley. A single torch point kindles at Limyra at about 1.6 s. | A descent from about 17 km out to about 7 km, eased, with roll of ±0.7°. Cool moon key. | `LIMYRA` / *Lycia, on the southern coast of Turkey · today* from "coast" −0.2 s. Source line lower-right (§6.4). | torch beacon 400–700; moon glitter on the bay 150–300 (polish) |
| B | `shot_approach` | 5.8–11.5 | l1 "…an ancient town, stands a tomb built for a Roman prince." | Ground-level walk through the ruins: broken colonnade, frieze slabs at the foot of the cenotaph podium, fallen drums, ashlar wall, cliff with rock-cut tombs against the sky. | A 7 m forward dolly with walking bob (0.9 Hz). The torch is carried a pace ahead, left. The camera tilts up toward the podium on "tomb". DoF focus is on the torch. | `THE RUINS AT LIMYRA` / *illustration* from "stands" −0.3 s | flame core 800–1000; embers 300–700; torch-lit stone 60–150 |
| C | `shot_youth` | 10.95–16.5 | l2 "The young man it was built for…" | **Real**: Met 2011.376 head ("possibly Gaius"), depth-lifted and relit in darkness. The torch passes right to left, low. Dust drifts in front. | Orbit of ±4°, push-in r 1.22→1.02. Cool fill opposite the torch. | `POSSIBLY GAIUS CAESAR` / *head of a young man, c. 5 BC or later*; source *The Metropolitan Museum of Art · CC0* | lit alabaster 150–250 |
| D | `shot_augustus` | 15.95–22.25 | l3 "His grandfather, Augustus, the master of that world, had planned his entire life for him:" | **Real**: Met 07.286.115 portrait of Augustus, depth-lifted, torch left to right. | Orbit in the opposite direction, push-in. | `AUGUSTUS` / *his grandfather · portrait carved after his death* (fix, §9). Source *The Metropolitan Museum of Art · CC0* | 150–250 |
| E | `shot_titles` | 21.8–25.2 | l3 "…his name, his titles, his future." | A marble slab with gilded letters: `C · CAESAR` / `PRINC · IVVENT` / `COS · DESIG`. The camera rides from line to line, arriving 0.05 s before each word, and the torch sweeps across each line as it is spoken. | Vertical boom and drift. Torch sweep per word. | Plain-English subtitles: *C · CAESAR — Gaius Caesar*, *PRINC · IVVENT — **Prince of Youth*** (fix; currently "Leader of the Youth"), *COS · DESIG — consul-elect*. Source line: *as on his coins and inscriptions · illustration*. | gilding glints 300–600 |
| F | `shot_coin` | 24.8–29.05 | l4 "Rome even put his name on its coins." | Code-built **RIC I 207 reverse**: the two princes with shields and spears, simpulum and lituus, `C · L · CAESARES`, `AVGVSTI · F · COS · DESIG · PRINC · IVVENT`. | Macro push. The coin yaws −31°→+11°. A cool second light rakes the legend on "name". | `SILVER DENARIUS` / *struck c. 2 BC – 4 AD · illustration*; source *C · L · CAESARES — Gaius and Lucius* | specular 600–900 |
| G | `shot_gutter` | 28.6–38.3 | l5 + l6 "And then, at twenty-two … he asked to walk away. / He never made it home." | Wide shot in the ruins at night. On "walk away" the torch moves away from camera down the colonnade, stops, gutters from "home" −1.4 s, and dies on **"home"** (36.12). Only moonlight remains. | Near-static with a slow creep in. Torch intensity → 0; moon ×1.25. | (no text) | flame peak, then extinction; after the death, frame average < 2 nits |
| H | `shot_title` | 37.9–48.2 | l7 + l8 | The carved, gilded slab `GAIUS CAESAR` / `THE HEIR WHO NEVER CAME HOME`. It rises from black with a faint glow on "This"; **the light sweeps across the letters on "Gaius"** and settles. Gold dust drifts. | Slow push and drift. | *20 BC – 4 AD* from "the" +0.2 s; `YEAR BY YEAR` from "choice" +0.4 s | gilded glints 400–600 at the sweep |

Dissolve windows: A/B 5.8–6.6 · B/C 10.95–11.5 · C/D 15.95–16.5 · D/E 21.8–22.25 · E/F 24.8–25.2 · F/G 28.6–29.05 · G/H 37.9–38.3.

### 3.1 Intensity curve (direct to this)

| Time | Beat | Picture | Sound |
|---|---|---|---|
| 0–6.6 | Mystery | the dark coast and one spark | wind, one drone |
| 5.8–16.5 | Discovery and intimacy | the ruins, then his face | footsteps, crackle, cellos enter pp |
| 16–27.6 | Power | Augustus, his names carved, the coin | strings and horns rise; chisel strikes; coin ring |
| 28.9–33.3 | Turn and tension | the light leaves | heartbeat pulse speeds up; string cluster crescendo |
| **33.34** | **Rupture** | the torch walks away | **all music cuts on "walk"** |
| 34–38.1 | Loss | the torch dies on "home"; darkness | only wind; near silence |
| **39.6** | **The name** | gold sweeps across GAIUS CAESAR | **one deep hit** |
| 40–48.2 | Ache | the title holds and settles | a 4-note theme fragment, unresolved; decay |

---

## 4. Visual language (consistent with the plan in A §4–§6)

- **Concept.** "He survives today almost only in stone and metal, so the whole film is carved." Every image in the cold open is stone, marble, struck metal or a carved inscription, or the real land where he died. v2 faked this with 2.5D relief compositing (`stone.py`). This build makes it real geometry with real shadows.
- **Light as meaning.** Each shot has one practical warm source, the torch, at about 2000 K: linear `TORCH_RGB ≈ (1.0, 0.56, 0.24)` normalised to luminance 1. The only other light is a cool moon. The torch stands for his life and attention. Gold appears only on gilding, the coin and the title.
- **Palette.**
  - Night shadows run blue-teal; highlights are torch amber.
  - Type is `PALE_GOLD (0.93, 0.84, 0.62)` and IVORY `(0.96, 0.93, 0.86)`.
  - Gilding is about `(0.92, 0.72, 0.36)`.
  - The series colours stay reserved: **Rome crimson for Artagira's red flash**, Parthia teal for the East. Neither appears in the cold open.
- **Format.** 16:9 4K with a 2.39:1 letterbox (`film.active_h`). All text sits inside the active picture and at least 5% from the side edges.
- **Type.**
  - Cinzel caps (tracking 0.25) for names and places, with a Garamond italic subline and a gold hairline growing above (lower-left).
  - Source and licence lines in small Cinzel, lower-right, at 85%.
  - Labels sit at about 126 nits (`level=0.62`), never above 203.
  - Where the background behind a label is bright, add the v2 soft dark backing: blur ≈ 72 px at 4K, 45%.
- **Honesty labels.** "illustration" on every reconstruction, "today" on modern real views, "possibly" on contested identifications, and institution plus licence on real objects.
- **Finish** (`film.render_frame`): bloom 0.06, anamorphic glare (threshold 3.0, amount 0.05), vignette 0.30, grain 0.010, per-shot thin-lens DoF from true depth, eased dissolves.
- **Camera grammar.** Slow, motivated moves. Handheld bob only while "walking" (shot B). No Ken Burns on flat photos, ever.
- **Grades.** The night look (blue shadows, warm highlights) for A, B and G. Warm gold for C–F and H. The cold-open ruins sit at the plan's 0.55 wear level ("told from the ruins").
- **Year format.** "20 BC – 4 AD" (the series format, "2 AD").
- **Do not reuse** the Shorts' painted parallax environments, globe, lacquer or paper cards, or the Inter caption style. Long-form captions ship as a sidecar SRT, as v1 did (§12).

---

## 5. Real images: what can be used, under which licence, and how each comes alive

### 5.1 Used in the cold open

| Asset (`plan/real_images/`) | Licence | Brought to life by | Label |
|---|---|---|---|
| `1_s2_limyra-finike-kumluca_2025-07-06_10m_7680x4320.jpg` (Sentinel-2A, 6 Jul 2025, 10 m/px; Limyra at the centre pixel) + `terrain/Copernicus_DSM_COG_10_N36_00_E030_00_DEM.tif` (GLO-30) | Copernicus Sentinel terms; Copernicus DEM GLO-30-F. Free and commercial, attribution required. | Real 3D. The DEM is ray-traced as a heightfield (`terrain_night.py`, 20 m texel, 3840×2160 albedo) and day-for-night graded: moon key, sky, stars. A torch beacon kindles at Limyra. The camera descends. | "today". Source line on screen; full notices in the credits (§13). |
| `3_met_possibly-gaius-caesar_head_front-dark.jpg` (Met 2011.376, gypsum alabaster, "ca. 5 BCE, or later", 3000×4000) | CC0 (Met Open Access; "Is Public Domain = True" in the Met CSV and isOasc in the Met/Google mirror) | Depth Anything V2 Small depth → relief mesh in `hfr` → the baked studio light is partly divided out → relit by a moving torch with a cool fill and soft shadows → DoF and motes. | "POSSIBLY GAIUS CAESAR" (the Met's own tentative identification). |
| `3_met_augustus_marble-portrait_07-286-115_dark.jpg` (Met 07.286.115, "ca. 14–37 CE") | CC0 | Same treatment, with the torch moving the opposite way. | "AUGUSTUS · his grandfather · portrait carved after his death". |

### 5.2 Available but kept out of this slice (and why)

- **Other Met CC0 views** of the same heads (three-quarter, profile, grey) and the bronze boy Met 14.130.1 ("Gaius Caesar ?", speculative). Depth for the three-quarter-dark view is already in `build/depth/`. These are good for chapter I, not the hook.
- **Met CC0 coins of Octavian and Augustus** (08.170.88/.89, aurei 99.35.6 and 99.35.121). These are the **wrong type**. Never caption one as a coin of Gaius.
- **CC BY 2.0 photos from Open Images:**
  - What: Ara Pacis (ISAW, MCAD), Lycian tombs, Patara, Xanthos, the coast, the Euphrates at Dura.
  - Problems: they are only **1024 px** on the long side, and Flickr is blocked, so the licences have not been re-checked live.
  - Use only as small parallax layers or insets later, after re-checking each page.
  - Credit: "Photo: <author>, CC BY 2.0, cropped/graded".
- **Piranesi, Mausoleum of Augustus, 1756** (Cooper Hewitt, CC0, 8213×6807). Save it for chapter VIII ("his ashes … placed in the great tomb"). Confirm and tag that claim first.

### 5.3 Wanted but not reachable from this container

- **A real photo of the Limyra cenotaph.** livius.org lists Jona Lendering photos as CC0, but that is unverified, and the host gave no connection from here. Wikimedia is blocked, and many Commons files there are CC BY-SA, which the series does not allow.
- **A real RIC I 207 coin photo**, from a CC0 or public-domain museum (Yale, ANS, BM, Met). All are blocked or have no image.
- **Full-size Ara Pacis procession photos.** These are CC BY 2.0 on Flickr (blocked). The list is in `real_images/provenance/flickr_ccby_originals_to_fetch_from_laptop.json`.
- **If the owner allows these hosts or drops the files in:** add a 2–3 s "LIMYRA TODAY · the cenotaph of Gaius Caesar" plate after shot A. It gets the same depth-and-torch relight, which is exactly the "show the ruins … make it pop" note. It would replace part of B. Until then, the ruins stay an honestly labelled illustration.

---

## 6. HDR mastering spec

### 6.1 Pipeline
1. **Working space.** Scene-linear BT.709 RGB, float32, with 1.0 = diffuse white = **203 nits** (BT.2408). Photos are sRGB-decoded first.
2. **Roll-off** (`hdr.rolloff_nits`). Applied on max(R,G,B) to keep hue. Identity up to **420 nits**, then an exponential shoulder toward a **1000-nit** peak.
3. **Gamut.** BT.709 → BT.2020 using the BT.2087 matrix. Content stays inside the 709 gamut; there is no fake saturation.
4. **Transfer.** ST 2084 PQ, packed to rgb48le, then `zscale` → yuv420p10le with limited range, the BT.2020 NCL matrix, top-left chroma and error-diffusion dither.
5. **Encode** (`film.hdr_cmd`): libx265 Main10, **CRF 14**, preset `slow` (or `medium` if time-bound), `aq-mode=3`, `keyint=48`, `open-gop=0`, `repeat-headers=1`, `hdr10=1`, `hdr10-opt=1`, tag `hvc1`.
   - Mastering display: `G(13250,34500)B(7500,3000)R(34000,16000)WP(15635,16450)L(10000000,1)` (P3-D65, 1000/0.0001 nits).
   - `max-cll=<MaxCLL>,<MaxFALL>` **measured** (§6.3).
6. **Chunks.** 48-frame chunks are encoded independently and joined with `concat -c copy`. The test verified this is clean, with the SEI on every chunk's first frame. Then add audio and `+faststart`.
7. **SDR companion.** Made from the **same linear frame** with `hdr.to_sdr8`: exposure 0.62, an ACES-fit curve weighted toward luminance, BT.709 with 2.4 gamma. Encode with x264 High, CRF 14 at 4K, tagged bt709/tv. Do not derive it from the HDR file: ffmpeg's hable tonemap comes out flatter and darker.

### 6.2 Luminance budget (this is what makes the HDR visible; v1's SDR→HDR LUT only lifted the sun)

| Element | Target (nits) | Scene-linear ≈ |
|---|---|---|
| Moonlit stone, deep night | 0.5–8 | 0.0025–0.04 |
| Torch-lit stone near the flame | 40–150 | 0.2–0.75 |
| Lit marble or alabaster faces | 60–250 | 0.3–1.2 |
| Labels, subtitles, source lines | 100–130 (never > 203) | `level` 0.5–0.62 |
| Gilded letters as the light passes | 300–600 | 1.5–4 |
| Coin specular as the rake crosses it | 600–900 | 4–10 |
| Flame core, embers | 800–1000 core; 300–700 embers | 5–20+ (rolled off) |
| Frame average (MaxFALL) | expected 5–60 | — |

Never let large areas sit above about 300 nits. HDR impact comes from small, motivated highlights against deep blacks.

### 6.3 MaxCLL / MaxFALL
`film.py` currently signals fixed values: `max_cll=1000`, `max_fall=60`. Before the 4K master:
1. Run a quarter-res HDR stats pass at width 960. This takes about 1/16 of the pixels and a few minutes.
2. Signal `ceil(measured)`, using the **same values for every chunk**.
3. Cross-check against the `stats_*.json` that `film.py` writes during the master.

### 6.4 On-screen source lines (short forms; full notices in §13)
- Shot A: "Copernicus Sentinel-2 (2025) & WorldDEM-30 · modified". The current text, "Copernicus Sentinel-2 & WorldDEM-30", is acceptable; add "· modified" or carry it in the credits.
- Shots C and D: "The Metropolitan Museum of Art · CC0".

### 6.5 Verification (reuse `plan/hdr_test/verify_hdr.py`)
- **Stream:** hevc, Main 10, yuv420p10le, tv range, bt2020nc / smpte2084 / bt2020, top-left chroma, hvc1, 3840×2160, 24 fps.
- **Metadata:** mastering-display and CLL SEI present on every keyframe.
- **Decode:** a full decode gives 0 errors and **1,157 frames** (48.2 s × 24); both files have the same frame count.
- **Brightness:** decoded peak ≤ 1000 nits, and the decoded average matches the stats.
- **SDR file:** tagged bt709 and decodes cleanly.
- **Audio:** −14.0 ± 0.3 LUFS, true peak ≤ −1.0 dBTP, 48 kHz, AAC-LC 320k.
- **Sync:** A/V offset 0; the hit and the extinction land within ±1 frame of their words.

---

## 7. Audio

### 7.1 Voice
- **Settings:** `bm_lewis`, speed 0.95, `british=True`. The narration is already rendered.
- **Processing:** dry and centred: HPF 75 Hz, +1 dB presence, **no compressor** (HANDOFF rule). Resample 24 kHz → 48 kHz with soxr.
- **Caveat:** the Lewis slice the owner heard used American G2P, so this read will sound slightly different.

### 7.2 Music and sound cue sheet (keyed to words via the timeline)

| Cue | Time (s) | What | Sound design |
|---|---|---|---|
| M0 | 0.0 | Night | Wind bed (about −42 dBFS RMS) and sparse crickets from 0.4 s; fade in over 2 s. |
| M1 | 0.3 | **One low drone** (v3) | D1 + D2 bowed bass with a sub blend; slow swell over 5 s to about −28 dBFS. |
| M2 | ≈1.6 | Beacon | Distant torch ignition (soft "whumph", low-passed at 1.2 kHz); torch crackle fades in, far away. |
| M3 | 0.5–6.2 | Descent | Slow low air movement (band 60–400 Hz), not a tonal sweep. |
| M4 | 5.8–11.5 | Approach | Close crackle panned to follow the torch's screen x (about 30% left). Footsteps on gravel and stone locked to the camera bob (about 1.8 steps/s). The drone holds. |
| M5 | tomb −0.03 | Stone | A felt-not-heard sub thump of stone resonance. |
| M6 | 10.95 | His face | Divisi cellos enter pp on D3/A3 with a 3 s bow attack. The crackle pans right to left with the torch. |
| M7 | grandfather → Augustus | Power | Basses and low horns enter: Dm → Bb/D on "Augustus". Slow crescendo pp → mp until 22.4. |
| M8 | name / titles / future −0.03 | **Carving** | Three chisel strikes, each doubled by a low drum pitched **D2, F2, A2**. These are the first three notes of Gaius's theme, carved before the theme is ever played. |
| M9 | 25.0 / coins 27.01 | Coin | The strings lift to Gm/D. On "coins", **one silver ring**: a struck-metal modal synth with a 3 s tail. No clatter. |
| M10 | 27.7 → 33.3 | Dread | A heartbeat pulse starts: a low drum at about 66 bpm, pp, speeding up to about 76 bpm. Strings move to tremolo. |
| M11 | 30.4 → walk −0.05 | Rise | String cluster crescendo (a D–Eb–E rub, rising an octave) with a riser. It peaks at mf–f, still ducked under the voice. |
| M12 | **walk 33.34** | **The music walks away** | **All music cuts**, drone included, with an 80 ms fade; hall tails decay naturally over about 1.5 s. Left in the mix: wind, the receding crackle and receding footsteps as the torch walks away. |
| M13 | home −0.9 → home | Gutter | The torch sputters: gusts and stuttering crackle. |
| M14 | **home 36.12** | Extinction | The flame dies: a soft fwump, a hiss and two or three ember ticks. Then wind only, falling to about −50 dBFS. **36.7–38.1 is near silence.** |
| M15 | This 38.18 → Gaius | Inhale | A reversed-reverb swell into the hit, pp → mf, about 1.3 s. |
| M16 | **Gaius −0.05** | **THE single deep hit** (v3) | A sub boom (pitch 52→34 Hz, 5 s), a big modal drum and a stone-impact transient, with a cathedral tail of about 6 s. Keep the energy below about 150 Hz while he speaks, so "Gaius Caesar" stays clear. **Nothing stacked on top** (v1 added a shimmer, riser and lyre). |
| M17 | ≈40.2 | Ache | Out of the tail, low strings and horns hold a D-minor open fifth (D2–A2–D3), pp. |
| M18 | ≈41.0–44.0 | Unresolved | A **4-note fragment** of the theme on solo cello (high register) or lyre: D4–F4–A4–G4, with the last note held, unresolved, under "except a choice". The full theme is saved for the adoption ("the theme rises in full for the first time"). |
| M19 | 44.3–48.2 | Out | The chord decays, faint wind returns, and everything fades out with the picture. **No series bell**; it is saved for the film's last frame. |

### 7.3 Instruments (all synthesized in code: $0, no licence questions)
The Shorts' palette (additive pads, Karplus-Strong lyre, ney, frame drums) is exactly what the owner called "too similar". Build these new instruments instead:

- **Bowed string sections.** 8–12 detuned sawtooth voices (±6–12 cents) with per-voice vibrato (about 5.5 Hz, random onset and depth), bow noise, body-resonance biquads (cello peaks at about 200, 450 and 1000 Hz), and real-time stereo seating. Variants: tremolo (an amplitude chop of about 12 Hz with random phase per voice) and sul tasto (low-passed).
- **Low brass and horns.** Additive harmonics whose brightness follows velocity, a 0.15–0.4 s attack and a slight pitch scoop.
- **Drums.** Modal membrane synthesis (Bessel mode ratios 1, 1.59, 2.14, 2.30, 2.65 …) with a pitch drop, plus skin noise.
- **Sub boom.** An exponential sine sweep with a 2nd harmonic.
- **Coin ring.** Inharmonic modal partials (about 1, 2.76, 5.40, 8.93 × about 2.4 kHz) with a long decay.
- **Chisel.** A noise burst, stone modes at 2–5 kHz and a low thock.
- **Fire.** Brown noise low-passed at 180 Hz, crackle clicks high-passed at 1.8 kHz, and pops. Its intensity follows the shots' torch intensity, so the sound gutters exactly when the picture does.
- **Footsteps.** Granular gravel (40 ms grains, 300 Hz–4 kHz) plus a heel thud.
- **Reverb.** Convolution with a synthesized, frequency-dependent 4–6 s stone-hall IR, stereo-decorrelated.

Optional upgrade: the CC0 orchestral sample set VSCO-2 CE. GitHub answered 403 for `sgossner/VSCO-2-CE` from here, so it could only be fetched on the laptop or once access is allowed (§12).

### 7.4 Mix and master
- **Ducking:**
  - Music: 14.5 dB under the voice while he speaks.
  - SFX: 16.5/1.
  - Ambience: 24/12.
- **Change from v1:** replace the automatic gap floor with **authored automation**, so the dramatic gaps actually land:
  - Silence window: music bus muted from 33.5 to 39.4 s, except M15.
  - The hit M16 is exempt from the voice-band (>150 Hz) detector in its sub band.
  - Swells in the gaps (M9, M17) may come up to their written level.
- **Master:** −14.0 LUFS integrated (±0.3), true peak ≤ −1.0 dBTP. Use a look-ahead limiter with a ceiling of about 0.74, as before, and verify with `ebur128=peak=true`. Output 48 kHz, AAC-LC 320 kbps.
- **Loudness range:** expect an LRA of about 8–12 LU, wider than the Shorts. That is intended for a cinematic piece; do not compress it to Shorts levels.

---

## 8. Directing notes per shot (what has to read on screen)

- **A.** The audience must see that this is a real place: the coastline shape, the bay, mountains with snow-tipped ridges. The spark at Limyra is the hook's first question.
- **B.** "Ruins at night" must feel touchable: crisp broken edges, flame light falling off realistically, embers rising, dust in the beam.
- **C.** The face must turn into the light. The torch crosses the eyes on "young man". Keep the camera arc small enough that no stretched or smeared pixels appear (§10).
- **D.** Augustus is lit harder and from the opposite side. He is the counterweight.
- **E.** The name, titles and future are literally cut in stone. Each word lands as its line is lit; it should feel like a sentence being passed.
- **F.** The coin turns until the light catches the legend on "name". It's a silver denarius, so cool highlights, with the warm torch only as a rim.
- **G.** The key shot. The light walks away and dies. Hold the darkness about 1.4 s before the title.
- **H.** Gold in darkness. The sweep crosses `GAIUS` on the word. The letters stay fully inside the frame for the whole push.

---

## 9. Accuracy

### 9.1 On-screen fixes required before the master

| Where | Current | Change to | Why |
|---|---|---|---|
| E subtitle | "PRINC · IVVENT — Leader of the Youth" | "PRINC · IVVENT — Prince of Youth" | Script v3 (ch. II) uses "Prince of Youth"; keep one translation through the whole film (RG 14.1, *princeps iuventutis*). |
| D subline | "his grandfather · marble portrait" | "his grandfather · portrait carved after his death" (or "marble portrait, c. 14–37 AD") | Met 07.286.115 is posthumous (ca. 14–37 CE). It must not read as a lifetime image. |
| F | The coin renders gold under the torch, but the label says SILVER | Cool key, warm rim only | RIC I 207 is a silver denarius. |
| Any Limyra label | — | Never "empty tomb" | Owner's instruction (10-15 07:48Z). |
| B | "THE RUINS AT LIMYRA · illustration" | Keep as is | The ruins are a code reconstruction, "loosely after the lower city", not a survey. |
| A | "today" | Keep; add "· modified" or carry it in the credits | A real 2025 view with a night grade and a torch beacon added for storytelling. |

### 9.2 Claims table: paste into `longform-gaius/research/research.md` (with the repo's tags)

| Line | Claim | Tag | Source and note |
|---|---|---|---|
| l1 | A tomb for a Roman prince stands among the ruins of an ancient town near Turkey's south coast. | CONTEXT | The cenotaph of Gaius Caesar at Limyra (Yuvalılar, Lycia), about 5 km inland from Finike. J. Ganzert, *Das Kenotaph für Gaius Caesar in Limyra* (1984); vici.org #17237; Livius. "Tomb" is the owner's chosen word; strictly it is a cenotaph, since his remains went to Rome (Dio 55.12.1). Who built it is not attested. |
| l2 | He was meant to inherit the Roman world. | CONTEXT | Adopted by Augustus in 17 BC with Lucius (Dio 54.18.1; Suet. *Aug.* 64.1); "appointing them then and there successors to his office" (Dio 54.18.1). |
| l3 | Augustus planned his name, titles and future. | CONTEXT | Name: adoption made him C. Caesar. Titles: *princeps iuventutis* and consul designate "in his fifteenth year" (RG 14.1, 5 BC). Future: consulship in AD 1 (RG 14.1). The wording is interpretive. |
| l4 | Rome put his name on its coins. | CONTEXT | RIC I² 198–199 (c. 8 BC); RIC I² 205–212, C L CAESARES (Lugdunum, from 2 BC). The coin on screen is a recreation of RIC I 207, not a photo. |
| l5 | At twenty-two, he asked to walk away. | TRADITION + ESTIMATE | Dio 55.10a.8 ("begged leave to retire to private life … remain somewhere in Syria"); Vell. 2.102.3. AD 3, after the wound of 9 Sept AD 3. Age 22 by year count; birth month unknown (Dio 54.8.5 places the birth in 20 BC). |
| l6 | He never made it home. | DATED 4 AD (death) | Died at Limyra on the way back, 21 Feb AD 4 (Vell. 2.102.3; Dio 55.10a.9; CIL XI 1421, a.d. VIIII K. Mart.). Rhetorical: his remains did reach Rome (Dio 55.12.1). Chapter VIII pays this off. |
| title | 20 BC – 4 AD | DATED | Birth 20 BC (Dio 54.8.5); death AD 4 (above). |
| C label | "Possibly Gaius Caesar" | CONTEXT (identification contested) | Met 2011.376, "Stone head of a Julio-Claudian youth, possibly of Gaius Caesar", ca. 5 BC or later. The narration makes no identity claim; the hedge is on screen. |
| E | C · CAESAR / PRINC · IVVENT / COS · DESIG | CONTEXT | Legends of RIC I 205–212 (AVGVSTI F COS DESIG PRINC IVVENT). Shown as an illustration. |

### 9.3 Script v3 issues outside the cold open (fix before the full film, not now)
"In 3 AD, Armenia rose" (Dio puts the revolt in AD 2); "a letter came from the west" (should be "news came"); the misquoted Gellius line (Rolfe: "my eyes are eager for my Gaius"); the Euphrates date (attribute "by most reckonings"); and the unverified v2/v3 additions (C §3.5–3.6).

---

## 10. QA findings from the current stills (fix in the draft cycle)

1. **Portrait edge stretch (C, 13.5 s).** The left side of the head shows rubber-sheet smearing where depth jumps from the head to the background. Fixes:
   - Matte the sculpture (alpha from depth plus colour) and treat the background as a hole.
   - Erode the silhouette slightly.
   - Clamp the orbit so that disoccluded areas stay under about 10 px at 4K.
   - Check D the same way.
2. **Ruins read soft, almost like clay (B, 8.5 s; G, 30.5 s).** The fallen drums look melted and the back wall looks lumpy. Fixes:
   - Give the blocks crisp chipped arrises and larger-scale erosion.
   - Vary the albedo (lichen, soil in joints).
   - Add dry grass and thistle silhouettes against the moon, and low ground mist.
3. **Label legibility.**
   - "THE RUINS AT LIMYRA" sits over a bright fallen drum (8.5 s): add the soft dark backing.
   - The source line on the titles slab (top-right, 23.5 s) washes out in the light pool: move it lower-right or back it.
4. **Coin (26.5 s).** Besides the colour fix in §9.1, there is a soft ghost or smear to the right of the coin; find out whether it is the glare streak or a dissolve. Keep the glare thin and dim. The coin should not clip in SDR.
5. **Title framing.** An older still (44.0 s) had "GAIUS CAESAR" running past both frame edges; the newer one (40.6 s) fits, but the slab's right edge is visible. Check the whole 37.9–48.2 s push: the letters must stay within 90% of the width and the slab edge must never enter the frame.
6. **Aerial (0–6.6 s) is murky and flat in SDR.** Fixes:
   - Lift the moon a little.
   - Add moon glitter on Finike bay (an HDR highlight).
   - Add valley haze to separate the ridges.
   - Keep the beacon small.
7. **The invisible torch-bearer.** A torch on a pole that glides with a walking bob reads as uncanny. Recommendation:
   - In G, show a cloaked figure, back to camera, rim-lit by the torch only and never front-lit. It walks away and the light dies with him, which makes "walk away" literal.
   - In B, imply the carrier by framing the pole entering from the lower left.
   - Label nothing more; B is already marked "illustration".
8. **Text QA** (`lf_textqa` rule): no overlapping text boxes. Every text of 4 or more words must stay up at least 1.2 s + words/3.0.

---

## 11. Second polish pass (after the whole film is built; improve, don't replace)

For the cold open:
- **Ruins (B, G):** volumetric torch light (god rays through dust); wet-stone puddles reflecting the flame, which doubles the HDR highlights; heat shimmer above the flame; embers drifting across dissolves to stitch the shots together.
- **Portraits:** wrap or translucency lighting for the alabaster head (2011.376 is gypsum alabaster, so torchlight should glow at thin edges), micro-contrast on the carved hair, and slight focus breathing on the push.
- **Inscriptions and title:** varied gold leaf with micro-scratches and worn edges, faint gold dust motes, and a slower, heavier final settle.
- **Lens:** subtle oval anamorphic bokeh on embers, a touch of edge chromatic aberration, and halation around the flame.
- **Grain:** keep a 35 mm feel and check that x265 keeps it. If it smooths it away, use CRF 12–13 or `tune=grain` for the upload master.
- **Sound:** pan automation from the torch positions in every shot; a spatial "walk away" (receding Doppler-free distance filtering); and a sweetening pass on the hit's tail.

---

## 12. Open risks (and what the owner can do)

| Risk | Impact | Action |
|---|---|---|
| **Blocked hosts:** upload.wikimedia.org, commons.wikimedia.org, Flickr (live.staticflickr.com, www.flickr.com), numismatics.org, nomisma.org, images.metmuseum.org (a mirror was used instead), www.livius.org (no connection), GitHub repo `sgossner/VSCO-2-CE` (403) | No real photo of the Limyra cenotaph, no real RIC I 207 coin, no full-size Ara Pacis frieze, no CC0 orchestral samples | The owner can add these under **Allowed domains** in the cloud environment's Network access settings (session title bar → environment → Edit; see https://code.claude.com/docs/en/cloud-environments#network-access), or fetch the files on the laptop and drop them into `plan/real_images/` with their licence pages. Licence rule: CC0, PD or CC BY only; never CC BY-SA. |
| Real ruins photo missing | B stays an illustration | Labelled honestly; swap in or add a real "LIMYRA TODAY" plate when available (§5.3). |
| Voice quality and accent | Lewis is graded D+ by Kokoro, and British G2P now differs from the slice he heard | It is his pick. Listen for "Augustus", "Caesar" and "twenty-two". `revoice.py`-style single-line fixes keep the timings. |
| Render time on 4 cores, 15 GB RAM, about 21 GB free disk, no GPU | 4K at an estimated 6–10 s/frame → **about 2–3.5 h** for 1,157 frames with HDR + SDR encodes | Never dump raw 4K frames (50 MB each). Two processes may run on **disjoint** chunk ranges (e.g. 0–24.0 s and 24.0–48.2 s; 24.0 s = frame 576 = 12 × 48), never overlapping. |
| Fixed MaxFALL 60 in `film.py` | Wrong HDR metadata if the measured value differs | Run the quarter-res pre-pass first (§6.3). |
| HDR playback on the owner's side | An HDR file looks wrong on a non-HDR display or a player without HEVC support. Windows' HEVC extension costs money. | Ship the SDR companion as well. Recommend free VLC or mpv for the HDR file, with Windows "Play HDR" on. |
| Captions | CLAUDE.md's burned-in captions rule is for the Shorts. Long-form v1 used a sidecar SRT. | Keep the picture clean and ship `captions_en.srt`. Flag this to the owner in one line. |
| Depth model licence | Depth Anything V2 Base and Large are CC BY-NC | Use **Small only** (Apache-2.0), as now. |
| CC BY licences not re-checked live | None are used in this slice | Re-check each Flickr page before any later use. |
| Repo hygiene | `longform-gaius/` is untracked in `/home/user/Testing` (branch `ccr-7b5c772c-oaxbng`); `real_images` is 126 MB and the raw transcripts 33 MB | Add `longform-gaius/.gitignore` covering `build/`, `plan/hdr_test/out/`, `plan/raw/` and media over 50 MB. Commit code, plan and research only. The owner's long-form films never went to GitHub; deliver the video as files. |

---

## 13. Render, QA and delivery plan

1. **Picture lock on the timeline.** Narration is final (48.05 s); the edit is `shots.EDIT`, 48.2 s.
2. **Per-shot stills.** Render 2–3 key times per shot at 1920 SDR, plus a contact sheet at 1 s intervals (49 frames). Check them against §8–§10.
3. **Draft.** 1920 SDR x264 (draft1, already running). Mux it with the first audio mix.
4. **Audio.** Build the score, SFX and ambience per §7. Mix, then master to −14 LUFS and ≤ −1 dBTP.
5. **Full QA on the draft with sound:**
   - text QA (overlaps, reading time);
   - cue sync within ±1 frame ("name/titles/future", "coins", "walk", "home", "Gaius");
   - dissolves, flicker, firefly pixels in the ray tracing, banding in the dark gradients;
   - accuracy labels per §9.1;
   - the C2 moving-frame rule.
6. **Partial re-render.** Delete only the failing 48-frame `seg/<tag>/sdr_*.mp4` chunks; `film.py` skips the rest.
7. **HDR pre-pass** at quarter resolution to set MaxCLL/MaxFALL.
8. **4K master.** `film.py --width 3840 --tag master` writes HDR10 and SDR segments together, in disjoint ranges.
9. **Assemble.** Join with `concat -c copy` for each of HDR and SDR. Add audio (AAC-LC 320k, 48 kHz), `-tag:v hvc1` on HDR and `+faststart`.
10. **Verify** per §6.5.
11. **Deliver as files:**
    - `Gaius-Caesar_cold-open_4K_HDR10.mp4`
    - `Gaius-Caesar_cold-open_4K_SDR.mp4`
    - a small 1080p SDR preview (≤ about 95 MB) for the phone

    Add one or two lines on how to view the HDR file. Do not upload anywhere; YouTube is Codex's job.
12. **Commit** code, the plan and the tagged `research.md` on the current branch. No `build/`, no models, nothing over 100 MB.
13. **After approval:** build chapters I–VIII in the same engine, then run the second polish pass (§11) across the whole film.

---

## 14. Credits for this slice (put in the description and the research doc)

- **Sentinel-2:** "Contains modified Copernicus Sentinel data 2025."
- **DEM:** "Produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved. The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30."
- **Met heads:**
  - Head of a youth, possibly Gaius Caesar: The Metropolitan Museum of Art, 2011.376, Gift of George P. Tetzel, 2011 (Open Access, CC0).
  - Portrait of Augustus: The Metropolitan Museum of Art, 07.286.115, Rogers Fund, 1907 (Open Access, CC0).
- **Tools and type:**
  - Narration: Kokoro-82M, voice `bm_lewis` (Apache-2.0).
  - Depth: Depth Anything V2 Small (Apache-2.0).
  - Fonts: Cinzel, Garamond (SIL OFL).
  - Music and sound: original, synthesized in code.
