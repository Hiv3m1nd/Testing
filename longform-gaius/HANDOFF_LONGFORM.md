# HANDOFF — Gaius Caesar long-form, cold open (for the local agent)

Read this first, then `README.md`, `plan/PRODUCTION_BRIEF.md` (the full spec: shot list §3, HDR §6,
audio cue sheet §7, accuracy §9, QA §10, polish §11, delivery §13) and `research/research.md`.
The repo rules in `/CLAUDE.md` still apply ($0, licences, accuracy, git).

## What the owner asked for (2026-10-15)
Long-form weekly profile #1 from script v3 ("Gaius Caesar: The Heir Who Never Came Home").
**First deliverable: the cold open only** (0:00–0:48.2 — the whole v3 cold open through the title;
a hard 30 s cut would land mid-sentence), for approval before the rest of the film. Requirements:
4K, HDR, far more cinematic than the Shorts, real visuals brought to life in 3D where possible,
more dramatic music (intense where the story needs it), voice **Kokoro `bm_lewis`**, then a second
polish pass over the visuals. The owner dislikes being asked questions — just do the work.

## State at hand-off (cloud session ran out of credit)
DONE and committed:
- Narration: `src/narrate.py` → `build/narration.wav` + `build/timeline.json` (48.05 s, bm_lewis,
  speed 0.95, **British G2P** via the new `british=True` flag in `year-1-ad/src/tts.py`).
- All engines and all 8 shots (`src/shots.py`, edit list `EDIT`, 48.2 s): real-terrain aerial,
  ray-traced ruins with a cloaked torchbearer, two real Met heads relit in 2.5D, carved titles,
  3D coin, gutter/extinction, carved gilded title. Stills look good (see `docs/preview_stills.jpg`).
- Score + mix to the brief's cue sheet (`src/score.py`): drone, crickets, fire that follows the
  torch, footsteps, chisel strikes doubled on D2/F2/A2, coin ring, quickening heartbeat, rising
  cluster, **all music cut on "walk"**, extinction on "home", silence, reverse swell, the single
  deep hit on "Gaius", open fifth, 4-note unresolved theme fragment. Narration WER (pocketsphinx)
  dry 0.255 → mix 0.50 (acceptable; Shorts were 0.37 → 0.57).
- Delivery tooling: `src/finalize.py` (−14 LUFS / ≤ −1 dBTP master, segment join, HDR10 + SDR
  files, <30 MB phone preview, `captions_en.srt`). HDR10 x265 command verified by
  `plan/hdr_test/` (verify.json ok).

NOT DONE:
1. A complete 1080p draft with sound of the *current* code (draft1 was stopped at frame 432 because
   the design changed after it started). Nothing after ~18 s has been checked in motion.
2. QA of that draft, fixes, 4K HDR10 master, verification, delivery.

## Local setup
- Python 3.11–3.13 with: numpy scipy numba opencv-python(-headless) skia-python soundfile
  onnxruntime onnx pyproj jiwer pocketsphinx librosa pillow, plus misaki 0.9.4
  (`pip install --no-deps misaki==0.9.4`), spacy + en_core_web_sm, espeak-ng (see
  `year-1-ad/README.md`). ffmpeg with libx265 + libx264 + zscale.
- Kokoro: set `KOKORO_DIR` to the folder with `kokoro-fp32.onnx` and `voices/bm_lewis.bin`
  (on the laptop: `C:\Users\heath\YearByYear\kokoro`). `narrate.py` otherwise defaults to the dead
  cloud path. You only need it if re-voicing; `build/` is NOT in git, so on a fresh checkout
  run it once.
- Depth model (Apache-2.0, Small only — Base/Large are NC): download
  https://github.com/fabio-sim/Depth-Anything-ONNX/releases/download/v2.0.0/depth_anything_v2_vits.onnx
  and set `DEPTH_MODEL` to its path.
- On Windows run Python with `-X utf8`. The laptop has 12 threads: run 2–3 `film.py` workers on
  **disjoint** time ranges (multiples of 2.0 s = 48-frame chunks), never overlapping.

## Rebuild from a fresh checkout (all in `longform-gaius/src`)
```
python narrate.py
python depth.py ../plan/real_images/3_met_possibly-gaius-caesar_head_front-dark.jpg ../plan/real_images/3_met_augustus_marble-portrait_07-286-115_dark.jpg
python terrain_data.py            # Copernicus DEM -> Sentinel grid (20 m; step=1 in main() for 10 m)
python score.py                   # -> build/mix_premaster.wav
python film.py --stills 2.5,8,13.5,19,23.9,26.5,31,34.8,40.6,44 --width 960   # QA stills
python film.py --from 0 --to 48.2 --width 1920 --sdr-only --tag draft2      # ~2–3 s/frame on 4 cores
python finalize.py --tag draft2   # draft with sound + preview + srt in build/out
```
The ruins SDF bake (~40–80 s) is cached in `build/cache/ruins_<hash>.npz`; numba kernels cache too.

## QA checklist for draft2 (then partial re-render: delete failing `build/seg/<tag>/sdr_XXXXX.mp4`)
- Cue sync ±1 frame: chisel on name/titles/future, coin ring on "coins", music cut on "walk",
  flame dies on "home", hit + gold sweep on "Gaius".
- Text: no overlaps (esp. the titles→coin dissolve 25.2–25.6), every label readable long enough.
- Shot G: the torchbearer must stand still until "walk", then walk away; flame/handle sit in his hand.
- Shot B: figure distance/scale, grass + stone-chip density (chips read as snow if too many).
- Title (37.9–48.2): slab edges never in frame, letters within 90% of width.
- Portraits: no smeared/stretched edges at 4K (reduce orbit if so).
- Aerial: slightly murky in SDR; may lift the moon (`shots.shot_aerial`, moon array).
- Flicker/fireflies/banding in dark gradients; the C2 rule (every frame moves).

## Master (after the draft is approved internally)
1. MaxFALL pre-pass: render every 6th frame at 960 px and compute mean nits with `film.to_pq16`
   (or read `stats_*.json`); pass `--max-fall <ceil>` to `film.py`.
2. `python film.py --from A --to B --width 3840 --tag master --max-fall N` in 2–3 disjoint ranges
   (est. 6–10 s/frame per worker at 4K; HDR + SDR segments written together).
3. `python finalize.py --tag master --hdr`, then verify with `plan/hdr_test/verify_hdr.py`
   (hevc Main10, bt2020/smpte2084, SEI on keyframes, 1,157 frames, −14 LUFS, TP ≤ −1).
4. Deliver: `Gaius_Caesar_ColdOpen_4K_HDR10.mp4`, the SDR file, the 1080p preview and
   `captions_en.srt`. Tell the owner to view HDR in VLC/mpv with Windows "Play HDR" on.
   Commit code/docs only (no build/, no models, nothing >100 MB).

## Decisions already made (don't re-litigate)
- 3840×2160, 24 fps, 2.39:1 letterbox; scene-linear frames → PQ/BT.2020 (203-nit white, roll-off to
  1000) and a separate SDR filmic grade from the same frames. No upscale, no SDR→HDR LUT.
- One flame = his life: it finds the tomb, his face, Augustus, reads his titles, walks away on
  "walk", dies on "home". The torchbearer is a cloaked figure seen only from behind (illustration).
- Labels: "illustration" on reconstructions, "today" on the satellite view, "possibly" on the
  youth head, institution + CC0 on Met objects; "PRINC · IVVENT — Prince of Youth";
  Augustus portrait "carved after his death"; never "empty tomb"; years as "20 BC – 4 AD".
- Captions ship as SRT (not burned in) for the long-form. No series bell in the cold open.
- Real assets committed: Sentinel-2 crop, Copernicus DEM tile (+EULA), Met 2011.376 front and
  Met 07.286.115. All other candidates have provenance sidecars in `plan/real_images/*.json`.

## After approval
Build chapters I–VIII in the same engine (script v3 in `plan/_extract_latest.txt` from line 599;
fix the script issues listed in PRODUCTION_BRIEF §9.3 first), then the polish pass (§11).
