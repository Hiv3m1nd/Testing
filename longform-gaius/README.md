# Year by Year long-form #1 — "Gaius Caesar: The Heir Who Never Came Home"

The cold open (script v3), built as a 4K HDR10 test piece for approval before the rest of the film.

- 3840×2160, 24 fps, 2.39:1 letterbox, HEVC Main10 HDR10 (PQ / BT.2020, mastering display 1000 nits)
  plus an SDR BT.709 version and a small 1080p phone preview.
- Narration: Kokoro `bm_lewis` at speed 0.95 with British pronunciation rules.
- Audio: −14 LUFS integrated, true peak ≤ −1 dBTP.
- Captions ship as `captions_en.srt` (not burned in), as for the long-form.
- $0 and local throughout. Every image licence allows monetised use (see `research/research.md`).

## What is new compared with the Shorts

| Shot | Technique |
|---|---|
| Night flight over Lycia | Real Copernicus DEM + Sentinel-2 imagery, ray-traced as a heightfield under moonlight with shadows, mist and a rippled sea (`src/terrain_night.py`) |
| Torch through the ruins | A 3D scene baked into a 2 cm signed-distance grid (eroded edges, fluted shafts, rubble cores, chipped blocks), sphere-traced with a flickering torch (soft shadows), moonlight, ambient occlusion, water reflections, grass, embers and lit dust (`src/sdf.py`, `src/scene_limyra.py`, `src/grass.py`) |
| The two Met heads | Real CC0 photographs lifted to 2.5D with Depth Anything V2 Small, de-lit, then relit by a moving torch with real cast shadows (`src/portrait.py`, `src/hfr.py`) |
| His titles, the coin, the title | Heightfield objects: V-cut letters with gold leaf, the Shorts' coin redrawn at 2.4× as a 3D silver object with environment reflections (`src/carve.py`, `src/coin.py`) |
| Finish | Scene-linear HDR throughout: thin-lens depth of field, bloom, glare, grain, vignette; PQ encode with a soft roll-off to 1000 nits (`src/post.py`, `src/hdr.py`) |
| Score | Synthesised strings, brass, choir, lyre (Gaius's D-minor theme), taiko, sub-boom; torch fire, footsteps, wind, chisel, coin; band-split ducking under the voice (`src/score.py`) |

## Build

```bash
cd longform-gaius/src
python narrate.py                     # voice + word timings -> build/timeline.json
python depth.py ../plan/real_images/3_met_*dark.jpg   # depth for the Met heads
python terrain_data.py                # DEM resampled onto the Sentinel grid
python score.py                       # score + mix -> build/mix_premaster.wav
python film.py --stills 8.5,19,40.6 --width 960       # QA stills (build/stills)
python film.py --width 1920 --sdr-only --tag draft1   # draft
python film.py --width 3840 --tag master              # 4K HDR10 + SDR segments
python finalize.py --tag master --hdr                 # audio master, join, captions, preview
```

Models (not committed): Kokoro-82M ONNX + voices (`KOKORO_DIR`), and
`depth_anything_v2_vits.onnx` from github.com/fabio-sim/Depth-Anything-ONNX (Apache-2.0).

`plan/` holds the production digest of the "2AD video production" thread (A–D), the real-image
provenance sidecars and the HDR encode test.
