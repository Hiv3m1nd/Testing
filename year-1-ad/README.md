# Year by Year — Episode "1 AD"

A 2 min 54 s vertical (1080×1920, 30 fps) historical documentary about the
year 1 AD. Every frame and every sound is generated in code on a 4-core CPU,
with no GPU and no paid services.

| Deliverable | Where |
|---|---|
| Finished film | `output/Year_1_AD.mp4` |
| Narration script with timecodes | `script/narration.md` (source of truth: `src/script_data.py`) |
| Research dossier: sources, claims, uncertainties, licences | `research/research.md` |
| Technical report and feasibility assessment | `docs/technical_report.md` |
| Source code | `src/` |
| Fonts (OFL), Natural Earth vectors, Kokoro vocab | `assets/` |

## Pipeline

```
script_data.py ──► narrate.py ──► build/narration.wav + build/timeline.json (per-word timestamps)
                                        │
terrain tiles ──► terrain.py ──► build/tex/*.png (equirectangular relief textures)
                                        │
            scenes_a.py / scenes_b.py ◄─┴─ globe.py, geo.py, relief.py, environments.py, fx.py, captions.py
                                        │
                     render.py ──► build/video.mp4 (parallel x264 segments)
                                        │
           music.py ──► build/mix_premaster.wav (score + SFX + ducked voice)
                                        │
                     master.py ──► output/Year_1_AD.mp4 (−14 LUFS, H.264/AAC)
```

All shot timing is derived from the narration timestamps, so you can rewrite a
line and re-run the pipeline: pictures, captions, sound effects and music cues
all follow the new timing.

## Reproduce

```bash
python3 -m venv venv && . venv/bin/activate
pip install onnxruntime onnx numpy scipy soundfile skia-python shapely pillow opencv-python-headless \
            numba librosa spacy phonemizer-fork espeakng-loader num2words addict regex
pip install --no-deps --ignore-requires-python misaki==0.9.4
apt-get install -y espeak-ng libegl1 libgl1 zstd
# spaCy en_core_web_sm 3.8.0: from conda-forge (spacy-model-en_core_web_sm) or the spaCy releases
# Kokoro-82M ONNX (fp32) + voices: set KOKORO_DIR to a folder with kokoro-fp32.onnx and voices/*.bin

python src/fetch_data.py        # AWS terrain tiles (~55 MB)
python src/terrain.py           # relief textures
python src/narrate.py           # voice + word timings
python src/render.py            # picture (~45 min on 4 cores)
python src/music.py             # score, SFX, mix
python src/master.py build/video.mp4 output/Year_1_AD.mp4
```

Useful while iterating:

- `python src/render.py --frames 12.5,60,130` writes PNG stills.
- `python src/render.py --from 60 --to 75 --out build/test.mp4` renders a range.
