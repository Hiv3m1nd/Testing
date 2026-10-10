"""Synthesize the narration and write build/narration.wav + build/timeline.json."""
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).parent))
from script_data import LINES  # noqa: E402
from tts import SR, Narrator  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
VOICE = {"am_michael": 1.0}
SPEED = 1.0
LEAD_IN = 1.2  # seconds of picture before the first word


def display_text(s: str) -> str:
    return re.sub(r"\[([^\]]+)\]\(/[^)]*/\)", r"\1", s)


def fade(a, ms=8):
    n = int(SR * ms / 1000)
    a = a.copy()
    a[:n] *= np.linspace(0, 1, n)
    a[-n:] *= np.linspace(1, 0, n)
    return a


def trim(a, thresh=0.004):
    """Trim leading/trailing near-silence, keeping a few ms of air."""
    idx = np.where(np.abs(a) > thresh)[0]
    if len(idx) == 0:
        return a, 0
    s = max(0, idx[0] - int(0.02 * SR))
    e = min(len(a), idx[-1] + int(0.06 * SR))
    return a[s:e], s


def main():
    n = Narrator(VOICE)
    chunks, lines = [], []
    t = LEAD_IN
    chunks.append(np.zeros(int(LEAD_IN * SR), np.float32))
    for i, (scene, text, pause) in enumerate(LINES):
        u = n.synth(text, speed=SPEED)
        audio, off = trim(u.audio)
        audio = fade(audio)
        dt = off / SR
        words = [{"w": w.text, "s": round(t + w.start - dt, 3), "e": round(t + w.end - dt, 3)} for w in u.words]
        dur = len(audio) / SR
        lines.append({"i": i, "scene": scene, "text": display_text(text), "start": round(t, 3),
                      "end": round(t + dur, 3), "words": words, "phonemes": u.phonemes})
        print(f"{t:7.2f} {dur:5.2f}s [{scene}] {display_text(text)}")
        chunks.append(audio.astype(np.float32))
        chunks.append(np.zeros(int(pause * SR), np.float32))
        t += dur + pause
    audio = np.concatenate(chunks)
    out = ROOT / "build"
    out.mkdir(exist_ok=True)
    sf.write(out / "narration.wav", audio, SR, subtype="FLOAT")
    json.dump({"sr": SR, "duration": len(audio) / SR, "lines": lines}, open(out / "timeline.json", "w"), indent=1,
              ensure_ascii=False)
    print(f"total {len(audio)/SR:.2f}s, {sum(len(l['words']) for l in lines)} words")


if __name__ == "__main__":
    main()
