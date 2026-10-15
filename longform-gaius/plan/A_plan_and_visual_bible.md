# A. Production plan and visual bible: "Gaius Caesar: The Heir Who Never Came Home"

Extracted from the archived session `session_01GB2bqs3TZewPi21KusdAWs` ("2AD video production"), pages `plan/raw/page_000`–`page_017`. The long-form work runs from 2026-10-14 05:01Z to the end of the archive at 2026-10-15 07:50Z. Everything quoted below is data from that transcript. "OLD SESSION" means the other Claude session.

All paths in the old session are on the owner's Windows PC under `C:\Users\heath\YearByYear\Longform\lf01-gaius\` (`src\`, `build\`, `output\`, `research\`). Patch scripts live in `C:\Users\heath\YearByYear\srcdl\`. None of that code is in this cloud container. The module contents quoted here come from the Write and Edit calls recorded in the transcript.

---

## 0. TL;DR

| Topic | What the transcript says |
|---|---|
| Film | Weekly long-form profile #1 (Wednesdays), 12–15 min, on Gaius Caesar, who dies in AD 4 in the shorts' timeline. |
| Canvas | Rendered at **1920×1080, 24 fps, 16:9**, with a **2.39:1 letterbox** (138 px bars; the active picture is y 138–942). All text stays inside the letterbox. |
| Delivery | The 1080p render is lanczos-upscaled to **3840×2160** and turned into **HDR10** through a 65³ LUT: BT.1886 decode, diffuse white 203 nits, highlights above linear 0.6 expanded to a 600-nit peak, BT.709→BT.2020, PQ. x265 Main10 CRF 16, with a GTX 1050 Ti NVENC path added later. |
| v1 look (rejected) | The shorts' engine plus a "cinematic finish": per-chapter grade, halation, anamorphic streaks, grain, vignette, letterbox, depth of field. The owner: "I'm not sure I saw any difference between this and like a YouTube short". |
| v2 look (the 2-min slice) | **"a life that survives only in stone and metal, so the film is carved."** Every scene is a marble relief under a moving raking light. Maps are inlaid marble with the empire in red porphyry. The sea is carved waves under a gilded moon. Backgrounds are lamp-lit Roman ashlar. The stone **cracks and weathers chapter by chapter**. Titles are **carved and gilded**. |
| Motifs | The gold **laurel wreath losing its leaves** (fortune falling away). The **gold coin of Gaius and Lucius**. **Stone weathering**. A **lamp going out** at his death. The **Limyra tomb** opening and closing the film. Gaius's **lyre theme** in D minor, with a major-key form only for Augustus's letter. |
| Built and rendered | Only a **2:00 SDR 1080p slice** (`output\slice_0-2min_1080p.mp4`, 2,880 frames, 137 MB), first narrated by am_fenrir, then re-voiced as `_bm_george.mp4` and `_bm_lewis.mp4` without re-rendering the picture. **No 4K HDR of the rework was ever made**; the owner said to skip it. The full rework render was killed. |
| Latest plan | **Script v3** (2026-10-15 07:50Z) with parenthetical **show notes** for visuals and music. It replaces the hook the slice was built on. |
| Feedback | Overlapping text. A quote that flashed by too fast to read. A weak hook. "too similar to our shorts". "add more detail". Visuals "can't just be like an image popped up". Big moments (adoption, Julia's exile, Artagira) "need to be intense". The script must be "a story … less like a list of facts". |

---

## 1. Timeline of the long-form work

| UTC | Event |
|---|---|
| 10-14 05:01 | Owner's brief for the weekly long-form (§2.1). The OLD SESSION picks Gaius, researches him and writes the script. |
| 10-14 05:24–05:40 | Engine converted to 16:9 at 24 fps. `cine.py` (cinematic finish), `lf_art.py` (Gaius art), `lf_scenes.py` (~50 shots), a contact-sheet QA, then the full render starts. |
| 10-14 05:40–12:05 | Score (`composeLF1.py`), 4K HDR (`hdr.py`), captions, thumbnail, fact fixes (twelfth consulship), then delivery of v1. 12:18.7, 4K HDR10, 1.9 GiB. Title: "Rome's Golden Heir Begged Not to Come Home. He Never Did". |
| 10-14 18:13 | Owner's critique of v1 (§2.3). The film is pulled from Ready For YT. |
| 10-15 01:05–01:24 | **Rework.** `stone.py` carved-relief engine, new hook, new voice (af_heart, unavailable, so am_fenrir), typography restyle, ambience, text-QA tool, then the full render starts. |
| 10-15 02:13–02:24 | Render-speed talk. Policy: one thread per worker, lossless caching, no half-res shading, NVENC only for the HDR encode. |
| 10-15 02:28–03:15 | Main render paused. The **2-minute slice** is rendered with the faster code, the main render killed, and the slice delivered at 1080p (§9). |
| 10-15 04:22–04:50 | Voice audition (11 Kokoro voices). George and Lewis versions of the slice built. |
| 10-15 06:50–07:50 | Script printed. Owner's long script critique (§2.5). **Script v2**, a second critique, then **script v3**. The style rules are saved as memory `longform-script-style`. |

---

## 2. The owner's requirements, verbatim

### 2.1 Original brief (2026-10-14 05:01Z)
> "I want to go ahead and begin uh, work uh, preparing to uh, start creating our long-form content … releasing uh, every Wednesday. It'd be about 15 minutes long. You know, somewhere between 12 and 15 minutes long … a pro- profile on a prominent first uh, person that's featured in our first seven shorts."

> "it wouldn't be good to choose someone in the in the storyline who is going to be alive for the next 50 episodes … So maybe either someone who just died … or is going to die … within … a very short period of time."

> "I'd like these to be like narrative driven … delivered as a story. And of course, it's got its hook in the beginning too"

> "every episode shouldn't feel the same. It really should be based on what their life was like. So if their life was intense, maybe it should feel intense, or if their life was kind of like peaceful and uh, regal, then it should feel … Style the video around the person."

> "if you were doing a profile on um you know Stalin, it would be like scary or like you know, paranoid"

### 2.2 Format adds (2026-10-14 05:25Z, 05:26Z)
> "oh! forgot to say, please export at 4k. nice hdr if possible, too."

> "make it more cinematic that the shorts"

### 2.3 Critique of v1 (2026-10-14 18:13Z). Two screenshots were attached; only their placeholders survive in the archive.
> "the first you can see this is like overlapping text in one of the screenshots … the second one, there was this quote that popped up really quickly. And like no one got to read … I need you to check over all the visuals. And fix that."

> "the hook in the very beginning, needs some work. It's um, it's okay, but … I need you to step it up. Visually, and um, maybe a work on the the words a little bit."

> "it's too similar to our shorts. It, it's it's nice that we have the continuity, like the little bell at the end, all that different thing. Um, yeah, I need it to be different."

> "I want you to take a second pass through all of the visuals not only to check them for mistakes, but also to um, make them more detailed and better. The idea is that the long-form videos are a better quality than the shorts. The shorts are really, really nice, but when this translates to a long-form … it's admittedly less watchable."

> "what vibe were you going for um, because I'm not sure I saw any difference between this and like a YouTube short … I think the audio needs work, the visuals need work, the hook needs work, and then there are some mistakes in it."

Follow-ups at 2026-10-15 01:05–01:09Z:
> "ensure the quality of the visuals is higher than the shorts as well as the othe4r things ive said"

> "also use a different voice than the shorts use. same quality or higher - free. nothing that costs money"

> (via AskUserQuestion) "I REALLY wish that you would have just gotten to work … don't do that again. just do what i asked"

This became memory `work-dont-ask`.

### 2.4 Process rules (2026-10-15 02:18Z, 02:23Z)
> "if I have to make another edit to it, let's just do not only a preview of it … but also it should just be a slice of it. Like I could probably tell within the first two or three minutes whether I'm going to approve the video"

> "I don't want to use Blender."

> "do the caching, but not the half resolution shading. From option three, do option two, um, try option four for the for the HDR encode … don't do that [move the drawing to the GPU]."

These were saved to memory (`year-by-year-longform.md`):
> "**Render speed policy (owner, 2026-10-14):** One thread per render worker … Lossless caching of static work (verified identical output). **No** half-resolution shading. The GPU (NVENC) for the 4K HDR encode only, with x265 as the fallback. Never move the frame drawing to the GPU."

> "**Machine:** 12 threads, 16 GB RAM, GTX 1050 Ti (4 GB, Pascal)."

### 2.5 Script critique (2026-10-15 07:24Z), visual excerpts
> "this whole thing … should be like you pick two or three big stories from his life and fill in the little details in between."

> "they were no longer his grandsons. They were sons, heirs, and Caesars … that's like an important moment … I would make the visuals here intense. Um, and the music…"

> "On Rome's great altar of peace … when you show it, you should show the altar of peace that you're talking about in the video … you can put show notes in here … in parentheses"

> "this big event in … Artagira … This would be like that moment where everything seems hopeless in a story … this is probably the biggest. His mother and father being sent away is a big one … being adopted … would be a big one."

> "A monument was raised to him and its ruins are still there. So, like, yeah, if you bring that up … you gotta definitely gotta show it. Show of the ruins. Um, and when you're showing the ruins and the visuals, like, you gotta make it look nice. It can't just be like an image popped up. You gotta do some work to it to make it, like, really pop. I want you to put that in the notes."

> "don't say them explicitly in the video … that is a an AI faux pas"

Second note (07:48Z) on the tomb:
> "the tomb thing is confusing. you wrote that its an empty tomb and at the end the big reveal is that it isn't a tomb? … I would just take that out. when you mention it in the beginning and the end you can call it a tomb, but you don't need to mention the empty part."

The saved style memory `longform-script-style` (07:49Z) includes these visual lines:
> "**Show notes in parentheses** in scripts, for visuals and music: show what's named (the real Ara Pacis, the ruins); make the visuals worked and beautiful, never a pasted image; make big moments intense."

> "**Why:** the long-form must be dramatic, gripping and narrative-driven, clearly better than the shorts."

### 2.6 Earlier series-wide rules that also bind the film
- **C2, no empty screens** (owner, 2026-10-11 20:18Z): "there were a few spots in the video where it sat on a black screen with just a few words for long periods of time … make sure going forward we don't have thhat happen again." `lf_scenes.py` states the rule: "Every shot keeps something moving (the C2 rule): a camera push or dolly, light that travels, particles, or an animated element."
- **C1, clarity:** few names, roles over names, sources on screen not in the voice, era terms explained once in modern words.
- **C3, the hook** gets special attention in the first 10 seconds, "in a subtle way, in like a nice way".
- Local-only, $0, no Blender, no paid services. Never touch YouTube; that's Codex's job.

---

## 3. Format and technical spec as built

### 3.1 Canvas, frame rate, letterbox
From `srcdl\lf_setup.py`:
```
s = s.replace('W, H, FPS = 1080, 1920, 30', 'W, H, FPS = 1920, 1080, 24  # long-form: 16:9 at 24 fps')
...
s = s.replace('END_CARD = 4.1', 'END_CARD = 9.0')
```
From `src\cine.py`:
```
ASPECT = 2.39
BAR = int(round((H - W / ASPECT) / 2))         # 138 px at 1920x1080
ACTIVE_Y0, ACTIVE_Y1 = BAR, H - BAR
```
> "ACTIVE_Y0 / ACTIVE_Y1: the picture area inside the letterbox. Keep all text inside it."

Plan note (thinking, 10-14 05:26Z):
> "I'll give the long-form cut a distinct cinematic identity: 2.39:1 letterbox at 24fps with slow parallax camera moves, lens flares/grain/vignette, chapter-specific color grading shifting warm-to-cold, dip-to-black cards, and a recurring musical theme—optimized to shine in HDR."

### 3.2 4K and HDR (`src\hdr.py`, LONGFORM.md §9)
> "The SDR render is turned into HDR10 by a 65³ LUT: BT.1886 decode; diffuse white at 203 nits (BT.2408); highlights above linear 0.6 expanded to a 600-nit peak; BT.709 primaries carried into BT.2020; PQ encode. Then a lanczos upscale to 3840×2160 and x265 Main10 at CRF 16 (preset fast). HDR10 metadata: mastering display 1000 nits, MaxCLL 600, MaxFALL 180."

> "The render's x264 stream uses the BT.601 matrix with no tags, so every re-encode must decode with `in_color_matrix=bt601`."

The `hdr.py` docstring explains the intent:
> "expand only the highlights above a knee (linear luminance 0.6) smoothly up to PEAK nits (flames, the sun, metal glints and gilded text gain real HDR brightness), scaling RGB together to keep hue and saturation; convert BT.709 primaries to BT.2020 (the colours stay inside the 709 gamut: no fake saturation)"

Constants: `PEAK = 600.0`, `WHITE = 203.0`, `KNEE = 0.6`, `N = 65`. The tone curve is `nits_Y = WHITE*Y + (PEAK-WHITE)*x**2`, where `x = clip((Y-KNEE)/(1-KNEE))`.

Delivery check on v1 (10-14 12:04Z):
> "colors stay accurate with no channel mix-up, and only the sun's highlight gains real extra brightness on HDR screens."

So the v1 grade produced very little HDR "pop".

**GPU path** (`hdr.encode_nvenc`, added 10-15 02:26Z). Colour work runs on the CPU with the main ffmpeg and is piped as raw yuv420p10le into ImageMagick's ffmpeg 4.2.3 (the 1050 Ti driver R580 is too old for the new NVENC API):
```
-c:v hevc_nvenc -profile:v main10 -preset slow -rc vbr_hq -cq 20 -b:v 0 -maxrate 60M -bufsize 120M -spatial-aq 1
-tag:v hvc1 -color_primaries bt2020 -color_trc smpte2084 -colorspace bt2020nc -color_range tv  (AAC 320k 48 kHz)
```
> "NVENC can't write the optional ST 2086 / MaxCLL SEI; the stream carries the required BT.2020 / PQ colour tags."

It ran at about 7 fps (about 5× faster), with x265 as the automatic fallback.

### 3.3 Render pipeline
- `render.py --workers N --chunks 28`, x264 CRF 10 intermediates (`-preset medium -crf 10`). `finalize.py` handles concat, fallback, preview and deliver. `autofinish.py` and `.cmd` are a detached finisher that survives usage limits.
- **Lesson:** "Never run two render processes over overlapping chunk sets. Both write `segments/seg_NNN.mp4`."
- Cost: about 3–7 s per frame per core for the stone look (Euphrates and Rome reliefs 7–9 s). About 1.2 GB per worker, so about 7 workers fit in 16 GB.
- Speed-ups (`srcdl\lf_speed1.py`): `OMP/OPENBLAS/MKL/NUMEXPR_NUM_THREADS=1`, `cv2.setNumThreads(1)`, x264 `-threads 2`. Lossless caches: `wear_maps` (lru 16), `_wall_base(kind, wear)`, and `_STATIC` normals and AO for static height fields. Verified "pixel-identical across all six test frames".

### 3.4 Audio spec
−14 LUFS, true peak ≤ −1 dBTP (limiter ceiling 0.74, giving about −1.3 to −1.8 dBTP). Ducking is driven by the narration. Narration runs at Kokoro speed 0.95 (the shorts use 1.0).

### 3.5 Length
v1 ran 12:18.7. The rework ran 11:54, padded by `respace.py` (+0.42 s per line, +0.6 s at chapter ends, the hook untouched) to reach the 12–15 min target.

---

## 4. Visual concept

### 4.1 v1, the "cinematic finish" over the shorts' engine (rejected)
`src\cine.py` docstring:
> "Cinematic finishing for the long-form films (more filmic than the shorts).
> - GRADES: one look per chapter (lift / gamma / gain, saturation, split toning), crossfaded at chapter boundaries, so the film moves from warm gold (youth) to cold blue (Limyra).
> - finish(): grade, halation (a soft warm glow around highlights), anamorphic streaks (horizontal flares on the brightest points), vignette, film grain and a 2.39:1 letterbox.
> - compose_dof(): environments.compose with depth of field: each painted layer is blurred by its distance from the focus depth, for rack-focus shots."

`finish()` chains `blend_grades` → `halation(amt=0.22)` → `streaks(amt=0.35)` (bluish horizontal smear of points with lum > 0.86) → `gfx.finish(grain=0.018, vig=0.42, bloom_amt=0.12)` → `letterbox`.

The scenes reused the shorts' painted parallax environments (`environments.rome()`, `env2.euphrates()`, `env2.fortress()`), globe maps, `art3.night_sea`, lacquer and paper backgrounds, and card styles. That reuse is why the owner saw no difference from the shorts.

### 4.2 v2, "the carved world": the current look and the one in the 2-min slice
The OLD SESSION's summary to the owner (10-15 01:29Z), verbatim:
> "**A look built around Gaius:** he survives today almost only in stone and metal, so the whole film is carved.
> - Every scene is a marble relief under a moving raking light.
> - Maps are inlaid marble, with the empire in red porphyry.
> - The sea is carved waves under a gilded moon.
> - Backgrounds are lamp-lit Roman masonry.
> - The stone weathers and cracks chapter by chapter as his life falls apart."

`src\stone.py` docstring:
> "The long-form look for Gaius: a life that survives only in stone and metal, so the film is carved.
> - relief_env(E, ...): an environment's silhouette layers become a carved, lightly painted marble relief, lit by a low raking light that travels across it (cast shadows, ambient occlusion, a light pool). Nearer layers stand higher. Weathering (cracks, stains) grows through the film as his life comes apart.
> - wall(t, ...): Roman ashlar masonry under a moving pool of lamplight, the ground for title, card and text scenes.
> - marble_map(img, ...): a globe/map render turned into a map inlaid in marble (land raised, sea polished dark stone).
> - carved(cv, ...): letters cut into stone (shadowed incision with a lit lower edge), optionally filled with gilding."

How `stone.py` works (2.5D relief shading, all CPU numpy/OpenCV, float32 sRGB at 1920×1080):
- **Marble albedo and bump** (`marble()`): fbm cloud plus sine-warped veins plus fine veins. Base albedo `(0.88, 0.85, 0.79)` after tuning (it started at `(0.80, 0.765, 0.70)`).
- **Height field from parallax layers:** each environment layer's alpha, placed with dolly and push parallax, becomes a raised plateau at `6 + 46*depth` px, softened by `1.2 + 2.2*depth` px blur. Saturated, opaque details keep "traces of ancient paint" (`paint=0.55`).
- **Lighting** (`shade()`): normals from the height gradient. A Lambert key with warm lamplight `KEY = (1.0, 0.86, 0.68)`. A cool fill `FILL = (0.55, 0.62, 0.78)`. Blinn specular. Cast shadows by 6-step height-field ray marching (offsets 3–40 px). Cavity AO (computed at ¼ resolution). A Gaussian **light pool** limits the light to an area. **Metal and gilding** get coloured, stronger highlights.
- **Light moves during each shot:** in `env_shot`, the azimuth sweeps `lerp(168, 128)` while the camera dollies and pushes. Elevation is about 19° (tuned between 17° and 24°). Key 1.8, ambient 0.08, pool radius 0.52·W, floor 0.16 (tunable per shot).
- **The sun as gilded relief:** a disc plus rays carved into the stone and gilded, masked by `skyvis` so it sits *behind* the buildings.
- **Cracks:** a 9-seed random-walk crack network, revealed progressively by `wear` (each crack has an `order` rank), cut into the height (−9 px) with light staining.
- **Ashlar wall:** blocks 230–290 × 480–820 px with drafted margins, travertine colour variation and pits, under a drifting lamplight pool (night variant tinted `(0.82, 0.86, 1.0)`).
- **Marble map:** land raised in marble, sea in "dark green-black serpentine" `(0.10, 0.17, 0.20)`, space near-black. The empire is in red porphyry, per the OLD SESSION's description.
- **Carved text:** a lit lower lip offset (+1.6, +1.8) at 35%, a dark incision `(0.05, 0.04, 0.035)`, and an optional gold fill `(0.92, 0.72, 0.36)`.

Self-review of the first stone frames (thinking, 01:10Z):
> "flat/beige lighting needing lower, deeper shadows, a sun carved on top of buildings instead of behind them, a haze layer picking up paint as an orange stripe, ink-like cracks, and a tile-like wall texture."

All of these were fixed. Then (01:11Z):
> "the relief still needs more lighting on its faces."

Key went to 1.8, with the AO blur at ¼ resolution for speed.

### 4.3 Weathering schedule (stone condition follows his life)
`lf_scenes.wear_at(t)`:
```
WEAR = [("a1", 0.0), ("c1", 0.08), ("d1", 0.12), ("e1", 0.16), ("f1", 0.3), ("g1", 0.5), ("i1", 0.68), ("j1", 0.8)]
w = 0.55   # the cold open is told from the ruins
```
> "How weathered the stone is: pristine in his golden years, cracking as his life comes apart."

### 4.4 Colour grades per chapter (`cine.GRADES`; still applied over the stone look in the slice)
| Look | Character | Used for |
|---|---|---|
| gold | warm lift, gain 1.05/1.0/0.9, saturation 1.08 | youth, Rome, the title, coins, Augustus's letter |
| violet | cool, desaturated (0.78) | Julia's exile (III), Lucius's death, the Livia rumour |
| ochre | warm earth, highlights orange | the East, the Euphrates, maps |
| ember | red-orange, saturation 1.1 | the dinner threat, Lollius, Artagira |
| ash | near-monochrome (saturation 0.62) | Syria, Augustus's grief, the Pisa decree; the cracking-Rome shot in the cold open |
| night | blue shadows, warm highlights | the sea, the lamp, Limyra, the tomb, the end |
| neutral | none | chapter cards |

Shots overlap by 0.6 s, and the overlap is a **dissolve that blends both picture and grade**:
```
w = gfx.smoother(gfx.seg(t, a2, b1)); img = f1(t)*(1-w) + f2(t)*w; looks = [(l1, 1-w), (l2, w)]
img = cine.finish(img, idx, looks)
fade out over the last 1.2 s; fade in over the first 0.6 s
```

### 4.5 Palette and type (inherited constants)
`GOLD = (0.89, 0.72, 0.42)`, `PALE_GOLD = (0.96, 0.88, 0.70)`, `IVORY = (0.96, 0.93, 0.86)`, Rome crimson `(0.80, 0.16, 0.20)`, Parthia teal `(0.18, 0.66, 0.62)`. Fonts are **Cinzel** (caps, wide tracking; titles, labels, citations) and **EB Garamond italic** (`"garamond-italic"`; subtitles, quotes, translations).

---

## 5. Typography and title treatment

### 5.1 Main title (rework `o_title`)
- Wall: `stone.wall(t, "night", 0.32, wear=0.3)`, with the light pool travelling from 0.2·W to 0.75·W. Gold dust drifts. A faint **wreath** sits behind (r 300, alpha 0.55).
- **"GAIUS CAESAR"**: `stone.carved(..., font("cinzel", 120, 700), gold=0.9*rv, tracking=0.12)`. It is revealed and gilded on the word "Gaius" (`rv = smooth(seg(t, tg-0.2, tg+1.6))`).
- **"THE HEIR WHO NEVER CAME HOME"**: Cinzel 40/600, IVORY, tracking 0.32. **"20 BC – AD 4"**: Garamond italic 36, PALE_GOLD. Both appear after the line ends.
- Chapter tag **"I · THE BOY WHO WAS BOUGHT"**: Cinzel 26/700, PALE_GOLD, tracking 0.3, at the bottom of the active area.
- Slow push 1.0 → 1.05.
- v3 show note: "(SHOW: the title is carved into the stone and catches gold as the light passes. MUSIC: a single deep hit on "Gaius Caesar".)"

v1 used `draw_text_reveal` (Cinzel 112, PALE_GOLD, glow 24) instead of carved stone.

### 5.2 Chapter cards (`chapter_card`)
- Ground `("night", 0.35)` (stone wall in v2). Dust. Fade in and out 0.8 s.
- The **wreath** (r 130) above, losing leaves per chapter (§6.1).
- Roman numeral: Cinzel 40, PALE_GOLD. Title: `draw_text_reveal` Cinzel 52, IVORY, tracking 0.22, glow 8. Date subline: Garamond italic 34, PALE_GOLD. Push 1.0 → 1.04.
- Sound (rework): "a stone door closing on the chapter" (`boom(3.5, 34)`) plus `shimmer(4.0, 880)`. v1 used a whoosh plus a bowl.

### 5.3 Labels, quotes, plaques (rework, `srcdl\lf_rework2.py`): "the film's own typography … distinct from the shorts"
- **Place labels** (`cine.lower_third`): lower-left of the active area. Cinzel 30 PALE_GOLD (tracking 0.25), with a Garamond italic 28 IVORY subline. A **gold hairline** grows above the label, on a **soft black backing** (blur 36, 45%).
- **Source citations** (`cine.source`): lower-right, Cinzel 20, IVORY at 85%, on a soft backing.
- **Quotes** (`quote()`): Garamond italic in curly single quotes, Cinzel citation below, on a "soft dark band behind so they read on any background".
- **Family-tree cards:** first "small marble plaques with carved, gilded names". These were found "hard-to-read gold-on-cream", so they became "dark bronze with gold-leaf letters (legible)": plate `(0.13, 0.10, 0.08)`, bronze rim, names `(0.98, 0.82, 0.5)`.
- **Cast name supers:** "documentary name supers: no box, a gold hairline, a soft shadow behind for legibility."
- Latin set as inscriptions: "PER AES ET LIBRAM", "AVGVSTVS · CONSVL XII", the Pisa decree lines ("CRVDELIBVS FATIS EREPTVM", "POPVLO ROMANO", "DIEM QVO C · CAESAR OBIIT", "PRO ALLIENSI"), and "IMPERATOR".
- Illustrations are labelled as such, e.g. "illustration after the frieze, 13–9 BC", "the cenotaph of Gaius Caesar · illustration", "AD 3 · the site is not securely identified".

### 5.4 Thumbnail (`thumb.py`)
Built from the film's own art: the Euphrates at sunset (ember grade), the **gold** coin of Gaius and Lucius inside a wreath "that's losing its leaves", and the text **"HE GAVE IT ALL UP"**. For the rework it was rebuilt in stone, darkened for contrast, with the small line "Rome's heir · dead at twenty-three".

---

## 6. Recurring motifs

### 6.1 The laurel wreath losing its leaves
`lf_art.wreath()`: "a gold laurel wreath whose leaves can fall (the film's motif: his fortunes falling away)". There are 44 leaves after the fix. Lost leaves stay gone; only newly lost ones fall during a card. Leaves kept per chapter card:
```
KEEP = {"I": 1.0, "II": 1.0, "III": 0.95, "IV": 0.95, "V": 0.9, "VI": 0.9, "VII": 0.6, "VIII": 0.45, "IX": 0.3}
```
It also appears behind the title, at the wounding (`r_wound`: keep 0.9 → 0.6), on the end card (keep 0.25) and on the thumbnail. v3 show note at the end: "(SHOW: the wreath, with its last few leaves falling. MUSIC: the theme, alone, unresolved.)"

### 6.2 The coin of Gaius and Lucius
`relief.render_coin(relief.coin_gaius_lucius(), …)` is a procedurally lit relief coin with travelling light azimuth and elevation, yaw, gold metal `(0.98, 0.79, 0.42)` and toning. It is the "same coin as in our shorts".
- Cold open: "the name on the money, under a travelling light". Citation "DENARIUS OF GAIUS AND LUCIUS · C · L · CAESARES".
- v3 notes: "struck again and again and pouring across the frame", and at Lucius's death "one of the two figures slowly fades from it". The closing line also refers to the coins.

### 6.3 Stone weathering and cracks (§4.3)
The cold open's `o_crack` cracks Rome across on "walk away". v3 note: "(SHOW: Syria; a lamp-lit tent; the stone around him slowly cracking.)" and "(SHOW: two figures in relief, back to back, and a crack running through the stone between them.)"

### 6.4 Light as meaning
The raking light travels in every shot. In the cold open a lamp goes out on "dead". v3 notes: "the light drifts away from Julia's name and leaves it in darkness"; "Lollius's name plaque goes dark"; "the boys' names are cut into the stone as the light hits them"; "the Pisa decree as a real inscription, with the light reading along its lines"; and at the end "the light passes over the ruins one last time and goes out."

### 6.5 Limyra tomb bookends
The film opens on the ruined monument at Limyra by torchlight at night and returns to it at dusk at the end: "the same … tomb the film opened on, now at dusk, the light passing over it one last time". v3: "(SHOW: back to the Limyra ruins from the opening, now at dusk. Make it gorgeous.)"

### 6.6 Music motif
Gaius's lyre theme in D minor, `THEME = ["D4","F4","A4","G4","F4","E4","D4",None,"C4","D4","F4","E4","D4"]`. A tender major form, `THEME_MAJ`, plays only for Augustus's birthday letter. v3: "the theme, tender, in a major key, the only time we hear it this way". Each chapter has its own colour: warm F major (I), C major brighter (II), D minor sparse and cold (III), a Phrygian colour with the ney/Parthian flute (IV), drums and impact (VI, Artagira), ash (VII), sea, lamp and a solemn decree (VIII).

### 6.7 The series bell (tension)
The owner liked "the continuity, like the little bell at the end" but wants the film "to be different". Script v3 ends with "MUSIC: the series bell at the very end." The bell is the one deliberate carry-over from the shorts.

---

## 7. Scene list and show notes

### 7.1 Script v3 (latest, 2026-10-15 07:50Z): structure and every show note, verbatim
Chapters: **Cold open · I. The Chosen Boy · II. A Family Built for Power · III. The Mother · IV. Into the East · V. The Island in the River · VI. Artagira · VII. The Man Who Wanted to Stop · VIII. The Long Way Home.** v2 named VIII "The Empty Tomb"; it was renamed after the owner rejected the empty-tomb reveal. The full v3 text is in `plan/_extract_latest.txt` (lines 599 onward).

| Where | Show note (verbatim) |
|---|---|
| Cold open, start | (SHOW: Night. A torch moves slowly through the ruins at Limyra, over carved stone, broken columns and dust drifting in the light. It has to look beautiful: real light and depth, never a picture that just pops up. MUSIC: one low drone and the crackle of the torch.) |
| Cold open, end | (SHOW: the title is carved into the stone and catches gold as the light passes. MUSIC: a single deep hit on "Gaius Caesar".) |
| I, open | (SHOW: Rome in carved relief, warm morning light. MUSIC: hopeful.) |
| I, the eagles | (SHOW: the eagles carried back into Rome, in relief, with the crowd's arms raised.) |
| I, adoption | (SHOW: the scales tip; the bronze lands; the boys' names are cut into the stone as the light hits them. MUSIC: the theme rises in full for the first time. This is the first big moment, so make it land hard.) |
| I, Ara Pacis | (SHOW: the Ara Pacis, the real Altar of Peace procession frieze in marble, with light travelling across it. Slowly reveal the little boy clutching a man's toga.) |
| II, open | (MUSIC: the warmth drains out.) |
| II, Tiberius and Julia | (SHOW: two figures in relief, back to back, and a crack running through the stone between them.) |
| II, coins | (SHOW: the coin of the two brothers standing with their shields, the same coin as in our shorts, struck again and again and pouring across the frame. MUSIC: proud, bright.) |
| III, open | (SHOW: the carved city darkens; cold violet light.) |
| III, end | (SHOW: the light drifts away from Julia's name and leaves it in darkness. MUSIC: a long held note, then silence.) |
| IV, open | (SHOW: the map inlaid in marble, with Rome in red porphyry and Parthia across the desert.) |
| IV, the letter | (SHOW: the letter on papyrus, writing itself in warm lamplight. MUSIC: the theme, tender, in a major key, the only time we hear it this way.) |
| V, open | (SHOW: the Euphrates in carved relief at sunset, campfires on both banks, and the island with its pavilion in the middle.) |
| V, Lollius | (SHOW: Lollius's name plaque goes dark. MUSIC: drops to nothing, then one low note.) |
| V, Lucius | (SHOW: the coin of the two brothers; one of the two figures slowly fades from it.) |
| VI, open | (SHOW: night. A fortress wall carved in stone, torches flickering along it. MUSIC: low, tense, building.) |
| VI, the strike | (SHOW: a flash of red light across the stone. MUSIC: cut to total silence on "struck", then one deep boom. This is the biggest moment in the film; give it room.) |
| VII, open | (SHOW: Syria; a lamp-lit tent; the stone around him slowly cracking.) |
| VII, the Senate | (SHOW: the Senate hall in carved relief, with Augustus reading the letter aloud.) |
| VIII, open | (SHOW: a small ship on the carved sea under the gilded moon, the Lycian coast in the dark.) |
| VIII, death | (MUSIC: silence; only wind.) |
| VIII, Pisa | (SHOW: the Pisa decree as a real inscription, with the light reading along its lines.) |
| VIII, ending | (SHOW: the wreath, with its last few leaves falling. MUSIC: the theme, alone, unresolved.) |
| VIII, Limyra | (SHOW: back to the Limyra ruins from the opening, now at dusk. Make it gorgeous.) |
| Last frame | (SHOW: the light passes over the ruins one last time and goes out. MUSIC: the series bell at the very end.) |

The dramatic peaks the owner named are the **adoption**, **Julia's exile** and **Artagira**, "probably the biggest". v3 marks Artagira as "the biggest moment in the film".

### 7.2 v1 chapter list and shot list (as built on 10-14; most shots kept in the rework, restyled in stone)
`CHAPTERS` (v1 and the rework):
```
I THE BOY WHO WAS BOUGHT (Rome, 20 BC) · II PRINCE OF YOUTH (6 – 5 BC) · III THE MOTHER (2 BC) ·
IV INTO THE EAST (1 BC – AD 1) · V THE ISLAND IN THE RIVER (AD 2) · VI ARTAGIRA (AD 3) ·
VII THE MAN WHO WANTED TO DISAPPEAR (AD 3 – 4) · VIII LIMYRA (AD 4) · IX THE MAN WHO WAS LEFT (AD 4)
```
SHOTS as `(renderer, start, end, look)`, with about 50 entries including the cards:
- **Open (v1):** `o_coin` gold · `o_island` ochre · `o_coast` night · `o_empire` neutral (globe to Rome) · `o_title` gold.
- **Open (rework, in the slice):** `o_tomb` night · `o_coin` gold · `o_island` ochre · `o_crack` ash · `o_lamp` night · `o_title` gold.
- **I:** `b_rome` (Rome relief; JULIA and GAIUS plaques) · `b_standards` (Rome with marching eagle-standard silhouettes; "THE STANDARDS LOST AT CARRHAE, 53 BC"; Dio quote) · `b_family` (family tree plaques; "a permanent annual sacrifice on his birthday") · `b_scales` (bronze scales tilt, ingot drops; "PER AES ET LIBRAM") · `b_adopted` (tree re-links to Augustus in gold; "GAIUS CAESAR · LUCIUS CAESAR"; Dio 54.18 quote) · `b_tablet` (wax tablet traced "AVGVSTVS", oil lamp, Suetonius 64 quotes) · `b_frieze` (procedural Ara Pacis-style procession relief panned under moving light, child holding a toga highlighted) · `b_tiberius`. All gold.
- **II:** `p_rhodes` · `p_toga` (AVGVSTVS · CONSVL XII) · `p_shield` (silver shield and spear) · `p_coins` (falling coins). All gold.
- **III:** `m_letter` (Suetonius: Augustus informs the Senate) · `m_island` (Pandateria) · `m_alone`. All violet.
- **IV:** `e_map` (globe, now marble map) · `e_three` (three witness cards) · `e_dinner` (ember) · `e_letter` (papyrus letter writing itself; "AUGUSTUS TO GAIUS · PRESERVED BY AULUS GELLIUS, 15.7"). Ochre, ember, gold.
- **V:** `i_flight` · `i_summit` (Euphrates with campfires; Velleius "truly a notable…") · `i_lollius` (ember) · `i_lucius` (violet).
- **VI:** `r_fortress` (`env2.fortress` with nine flickering wall torches; camera push 1.05 → 1.22; **camera shake and a red flash on "struck"**; "9 SEPTEMBER, AD 3" in red glow; "IMPERATOR") · `r_wound` (wreath sheds leaves). Ember.
- **VII:** `v_syria` · `v_augustus` (ash) · `v_ship` (night).
- **VIII:** `l_coast` · `l_lamp` · `l_pisa` (lit marble slab with the carved Latin decree and highlighted lines) · `l_cenotaph` (stone tomb at dusk). Night, ash.
- **IX:** `x_augustus` · `x_rumor` (violet) · `x_tiberius` · `x_shield` · `x_coins` · `x_end` (papyrus letter fades, wreath at keep 0.25, "GAIUS CAESAR / 20 BC – AD 4", and "His years are told day by day in our shorts: 1 AD · 2 AD · 3 AD · 4 AD").

### 7.3 Art pieces (`src\lf_art.py`; "All illustrations")
wreath · scales (bronze balance, `per aes et libram`) · wax_tablet (letters traced into wax) · shield_spear · frieze (procedural height-field procession: togate adults at two depths with diagonal folds, one small child holding a toga, lit by moving light) · papyrus (letter appears line by line) · slab (marble with carved Latin under a sweeping raking light; one line can be gilded) · cenotaph · witness_card · standards (eagle standards in silhouette, marching).

### 7.4 Real imagery
The OLD SESSION built everything procedurally; no photographs or museum images were used. In script v3 the owner's direction calls for **"the real Ara Pacis"**, **"the Pisa decree as a real inscription"** and **showing the actual Limyra ruins**, each "worked and beautiful, never a pasted image".

---

## 8. The cold open: intended and built

### 8.1 Intended (script v3, the newest)
Narration (101 words):
> "Near the southern coast of Turkey, among the ruins of an ancient town, stands a tomb built for a Roman prince.
> The young man it was built for was supposed to inherit the Roman world. His grandfather, Augustus, the master of that world, had planned his entire life for him: his name, his titles, his future. Rome even put his name on its coins.
> And then, at twenty-two, with all of it finally within reach, he asked to walk away.
> He never made it home.
> This is the story of Gaius Caesar: the boy who was given everything, except a choice."

Visual and music notes: night, a torch moving slowly through the Limyra ruins, carved stone, broken columns, dust in the light. "real light and depth, never a picture that just pops up." One low drone and torch crackle. The title is carved into stone and catches gold as the light passes, with a single deep hit on "Gaius Caesar". Per the owner, the tomb is "just a tomb, at the start and the end. The 'empty' reveal is gone."

### 8.2 Built (rework, 10-15 01:13–01:23Z; this is what the 2-min slice shows)
The hook text it was built on (old version, superseded by v3):
```
h1 "In the ruins of an old town in southern Turkey, there is a tomb with no one inside it."
h2 "It was built for a young man the whole Roman world had been told was its future."
h3 "His name was on coins all across the empire. At twenty-one, he dined with the King of Parthia, on an island in the middle of the Euphrates."
h4 "He was heir to everything. And at twenty-two, he asked to walk away from all of it."
h5 "A few months later, he was dead. He never made it home."
h6 "This is the story of Gaius Caesar."
```
Shots, with the OLD SESSION's description to the owner: "A torch moves through the ruined tomb at Limyra, then the gold coin, then the Euphrates. Rome cracks apart on 'walk away', and a lamp goes out on 'he was dead'. The title is carved and gilded."

| Shot | Lines | Grade | Visual |
|---|---|---|---|
| `o_tomb` | h1–h2 | night | `tomb_env()`: hills; a ruined monument with 4 steps, a podium and cornice, 6 standing columns (some broken, capitals on the tall ones), a surviving architrave stretch and 5 fallen drums; then grass and rubble. Rendered with `stone.relief_env(az 195→160, el 14, wear 0.5, sun=False, pool_xy=torch position, pool_r 0.36, floor 0.06)`. Dolly −120 → +80, push 1.02 → 1.12. **The torch** (shaft, a 210 px glow, 5 licking flame ovals, a hot core) moves from 0.2·W to 0.62·W and **is the key light**. 90 ember-coloured dust motes. Lower third "LIMYRA, IN LYCIA / southern Turkey · the empty tomb of a Roman prince". **This label must change: the owner removed "empty".** |
| `o_coin` | h3 (first half) | gold | Relief coin of Gaius and Lucius at 700 px. The light sweeps az 200 → 110 and el 22 → 34; the coin yaws −18 → 12. Warm radial glow on the wall, dust, zoom 1.0 → 1.1. Citation "DENARIUS OF GAIUS AND LUCIUS · C · L · CAESARES". |
| `o_island` | h3 "twenty-one…" | ochre | Euphrates relief (wear 0), dolly −160 → 60, push 1.04 → 1.12, campfires (`scenes_d._fires`). "THE EUPHRATES / AD 2". |
| `o_crack` | h4 | ash | Rome relief. **Wear ramps 0 → 0.95 from "walk"**, the image darkens 35%, and the dust count jumps from 40 to 160 as stone dust falls. |
| `o_lamp` | h5 | night | An oil lamp on a stone ledge in front of the ashlar wall. **The flame dies on "dead"** (0.9 s), the wall falls dark with it, smoke rises, slow zoom. |
| `o_title` | h6 | gold | §5.1. |

Music cues for that hook (`music.py`): a D2 drone across the open. A pad (D3, A3, E4). A shimmer at h2. A **ney** (Parthian flute) phrase D5–Eb5–F#5–G5 at "twenty-one". Waves at "Euphrates". Chords Dm → Bb at "walk" with `boom(4.0, 38)`. `bowl(392)` plus `boom` on "dead". A riser into h6, then `boom(5.0, 50)` plus a shimmer on "Gaius", a Dm9 chord, and the lyre THEME. Ambience regions: h1–h3 wind, fire and crickets; h3–h4 river and fire; h4–h6 room and wind.

v1's cold open (10-14) was coin → Euphrates → night sea with a ship and a lamp going out on "dead" → globe pushing to Rome → title. The owner called it "okay" but said it needed to "step it up. Visually".

---

## 9. The 2-minute slice: what was built and rendered

- **Why:** the owner asked (10-15 02:28Z) to "deliver me the your first two minutes of the main video using this these new rendering methods … don't do the low quality version". He also wanted a 4K HDR before/after, then cancelled it: "finish the ten eighty p slice, but after that, don't keep going to the … 4K stuff".
- **Code:** `src_next\`, a copy of `src\` with `lf_speed1.py` applied. Frames were verified identical. Text fixes from `lf_textfix1.py` went into both copies.
- **Render:** `render.py --workers 6 --chunks 6 --to 120 --segdir ../build/slice_segments --out ../build/slice_1080.mp4`, six 480-frame pieces. When the owner had the paused main render killed, the unfinished pieces were cut at their current frame, and the rest (frames 403–480, 881–960 and 1203–1440) were re-rendered on 10 workers into `build\slice_rest\r0..r2`. Everything was concatenated with absolute paths (a relative-path bug broke the first join).
- **Speed:** "The tomb, coin, Euphrates and cracking-Rome shots are full carved-stone scenes, at about 3–4.5 seconds per frame on one core … The Euphrates and Rome pieces … about 7–9 seconds per frame: the carved river scene with campfires, and the city relief." Caching helps these shots least because the camera moves every frame.
- **Output:** `output\slice_0-2min_1080p.mp4`, exactly **2,880 frames, 2:00, 137 MB**. The final encode converts BT.601 → BT.709 with tags, x264 CRF 17, AAC 256k. SDR only.
- **Content:** "the new hook, the carved-stone look, the new narrator and the ambience". At the time that meant `o_tomb` … `o_title`, then chapter I up to about the wax-tablet shot. The script marks "(the 2-minute preview ends here)" after "…he trained them to copy his own handwriting."
- **Voices:** the slice was narrated by **am_fenrir**, which the owner rejected ("i dont want to use that voice"). After the audition (Kokoro's grades: am_puck C+, bm_george C, **bm_lewis D+**, am_onyx D, am_adam F+; downloaded af_heart A, af_bella A−, bf_emma B−, af_nicole B−), the owner said "we're gonna go with lewis or george". `swapvoice.py` laid each new take at the old line starts, re-reading at speed 0.97–0.99 where a take ran long, giving `output\slice_0-2min_1080p_bm_george.mp4` and `…_bm_lewis.mp4`. Caveat: "Effects tied to specific words, like the crack on 'walk away', may land a fraction of a second off."
- **Owner feedback on the slice's picture:** none recorded. His next messages were about the voice and then the script.

---

## 10. QA and review findings on visuals

### 10.1 From the owner
- v1: overlapping text (the screenshot was of the family tree; fixed by "Julia and Agrippa step back while the quote takes their place"). A quote that flashed too fast ("The Suetonius quote now stays up for its whole line, about 6.5 s, instead of 1 s"). A weak hook. "too similar to our shorts". "less watchable". "make them more detailed and better".
- Shorts, C2: no long static black screens with a few words.
- Script stage: show what's named (the real Ara Pacis, the ruins), work the images so they "really pop", make the big moments intense.

### 10.2 OLD SESSION self-QA (contact sheets via `lf_qa.py`; per-shot stills)
- v1 art test: "the marble frieze figures are too crude, the carved inscription is hard to read, and the wreath is sparse." Fixed: 44 leaves and a new two-depth frieze.
- v1 contact sheet: "the Pisa inscription overflowing its slab, overly dark Artagira fortress scenes, and a slow-rendering falling-coins shot." Fixed: shorter decree lines, a smaller slab, wall torches plus `img*1.7+0.03`, cached coins.
- v1 delivery: a leftover caption error ("his thirteenth consulship") was found on the final frames and patched by re-rendering 250 frames.
- Stone tests: listed in §4.2.
- Rework stills (01:22Z): "the weak opening tomb shot, hard-to-read gold-on-cream family-tree plaques, an overexposed fortress, and overall flat contrast." Fixed: the tomb became "a real ruin (podium, standing broken columns, frieze, steps), a big torch, deep night"; the plaques became bronze; the brightening hack was removed from the fortress.

### 10.3 Automated text QA (`src\lf_textqa.py`)
It instruments `gfx.draw_text`, renders frames at 2 fps through the real pipeline, and reports:
> "OVERLAP t "text A" x "text B" — two visible texts whose boxes intersect; SHORT "text" visible Xs < needed Ys (needed = 1.2 s + words / 3.0, for texts of 4+ words)"

Flagged SHORT items: "truly a notable", "accidental or voluntary", "GAIUS CAESAR · 20 BC", "snatched away from the Roman", "the Gauls' defeat", "QVOS IVVENES", "to be allowed to stop", "His years are told". They were fixed so that "quotes appear with their line, not on its last word". No overlaps were found in the second half.

### 10.4 Other technical QA
- Every intermediate is BT.601 untagged, so decode with `in_color_matrix=bt601`. The shorts had a related tagging bug that was fixed separately.
- The v1 HDR check showed that only the sun gained real HDR brightness. The SDR-derived highlight expansion (knee 0.6) gives little HDR impact unless the grade itself puts deliberate highlights above the knee (flames, gilding, metal glints, the sun).

---

## 11. Audio direction (for the drama brief)
- Narrator: Kokoro, speed 0.95, a voice different from the shorts' am_michael. The owner now picks **bm_lewis**.
- Score: synthesized pads, drones, lyre and plucks, ney, drums, `boom`, `bowl`, `shimmer`, `riser`, `whoosh`, `waves`. Gaius's THEME and THEME_MAJ (§6.6).
- Ambience (`src\ambience.py`), synthesized with no samples: wind, air, room, sea, river, fire (crackle), crickets, birds. Crossfaded regions are keyed to line ids at about −30 dBFS and ducked under the voice (target ratio 24 dB).
- Mix: music ducked to about 16.5 dB under the voice (median about 18.9 dB). Master at −14 LUFS and ≤ −1 dBTP.
- v3's music beats: hopeful (I); "warmth drains out" (II); proud and bright (coins); "a long held note, then silence" (Julia); the tender major theme (letter); "drops to nothing, then one low note" (Lollius); "low, tense, building … cut to total silence on 'struck', then one deep boom" (Artagira); "silence; only wind" (death); "the theme, alone, unresolved" (the end); the series bell (last frame).

---

## 12. Files and modules (old session, Windows PC)

| Path (under `Longform\lf01-gaius\`) | Role |
|---|---|
| `src\script_data.py` | Lines `(id, scene, text, pause)` with phoneme overrides (`GAIUS = "[Gaius](/ɡˈIəs/)"`, LUCIUS, VELL, LIMYRA, ARTAGIRA, LOLLIUS, ALLIA, AD, BC). |
| `src\narrate.py`, `revoice.py`, `respace.py`, `swapvoice.py` | Narration, per-line re-voice, re-spacing, voice swap that keeps the timeline. |
| `src\gfx.py` (from the shorts) | Canvas (skia), fonts, `draw_text`/`draw_text_reveal`, `fbm`, `finish`; W, H, FPS = 1920, 1080, 24. |
| `src\cine.py` | Grades, halation, anamorphic streaks, letterbox, DOF compose, `lower_third`, `source`. |
| `src\stone.py` | The carved-relief engine (§4.2). |
| `src\lf_art.py` | Gaius art (§7.3). |
| `src\lf_scenes.py` | All shots, chapter cards, `wear_at`, `tomb_env`, `sea_env`/`stone_sea`, `quote`, `env_shot`. |
| `src\render.py` | SHOTS list, dissolves, `frame()`, chunked render (`--workers --chunks --from --to --segdir --frames --stills`). |
| `src\music.py` (from `srcdl\composeLF1.py`), `ambience.py`, `master.py` | Score, ambience, loudness. |
| `src\lf_qa.py`, `lf_textqa.py` | Contact-sheet QA, text overlap and reading-time QA. |
| `src\hdr.py` | LUT plus x265 and NVENC 4K HDR10 encodes. |
| `src\finalize.py`, `autofinish.py/.cmd`, `render_all.sh`, `patch_frames.py`, `after_patch.sh` | Assembly, preview, delivery, unattended finishing, frame patching. |
| `src\lf_meta.py`, `thumb.py` | Captions, chapters, thumbnail. |
| `research\research.md`, `research\data\` | Claim → source table and primary texts. |
| `output\` | `slice_0-2min_1080p*.mp4`, `voice_samples\`, `script.md`, `YOUTUBE_UPLOAD.md`, `captions_en.srt`, `thumbnail.jpg`. |
| `..\LONGFORM.md` | The long-form pipeline doc. |
| memories | `year-by-year-longform.md`, `longform-script-style.md`, `work-dont-ask.md`. |
| `srcdl\lf_rework1.py`, `lf_rework2.py`, `lf_speed1.py`, `lf_textfix1.py`, `lf_fix1-4.py`, `lf_art_fix1.py`, `lf_render_patch.py` | Patch scripts; the record of every change. |

The engine modules reused from the shorts are `environments`, `env2`, `art2`, `art3`, `art4`, `cast`, `fx`, `geo`, `globe`, `relief`, `scenes_a`…`scenes_d` and `timeline`.

---

## 13. Gaps and implications for the next build
1. **The script changed after the slice.** The slice uses the old hook ("tomb with no one inside it", "dined with the King of Parthia", "A few months later, he was dead"). v3's cold open drops the Euphrates and "dead" lines, so the built `o_island` and `o_lamp` beats no longer match. v3 only specifies a torch-lit Limyra open and a carved, gilded title.
2. **Remove "empty"** from the tomb label ("southern Turkey · the empty tomb of a Roman prince"). The owner explicitly dropped that framing.
3. **4K HDR was never produced for the reworked look.** Only v1 shipped in HDR, and there only "the sun's highlight" gained HDR brightness. HDR impact needs deliberate highlights (torch, gilding, coin metal) above the 0.6 knee, or a native HDR grade.
4. **Real images were never used.** v3's notes ask for the real Ara Pacis, the real Pisa inscription and the actual Limyra ruins, treated with depth and moving light rather than shown flat.
5. **Voice:** the owner now wants **bm_lewis**. Kokoro's own grade for it is D+ (the OLD SESSION's table), and it is British while the pipeline uses American phonemization (a caveat stated for bf_emma; it likely applies to Lewis too). The slice's per-word effects were timed for am_fenrir.
6. **Bell:** v3 keeps "the series bell at the very end". The owner wanted continuity elements like the bell, but "different" overall.
7. **Render budget:** at 3–9 s per frame on CPU at 1080p, native 4K is far heavier. Policy: preview-first slices, one thread per worker, lossless caching, no half-res shading, GPU only for the encode, no Blender.
