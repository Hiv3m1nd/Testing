"""Synthesise the narration with Kokoro (bm_lewis, British G2P) and write word timings."""
import json
import os
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "year-1-ad" / "src"))
os.environ.setdefault("KOKORO_DIR", str(HERE.parents[1] / "year-1-ad" / "models"))
from tts import Narrator, SR  # noqa: E402

import script_coldopen as S  # noqa: E402

BUILD = HERE.parent / "build"


def main():
    nar = Narrator(S.VOICE, british=True)
    t = S.LEAD_IN
    chunks = [np.zeros(int(S.LEAD_IN * SR), np.float32)]
    lines = []
    for lid, text, pause in S.LINES:
        u = nar.synth(text, speed=S.SPEED)
        a = u.audio.astype(np.float32)
        # trim leading/trailing near-silence so pauses are exact
        env = np.abs(a) > 0.004
        i0 = max(0, np.argmax(env) - int(0.03 * SR))
        i1 = min(len(a), len(a) - np.argmax(env[::-1]) + int(0.08 * SR))
        a = a[i0:i1]
        off = i0 / SR
        words = [dict(w=w.text, s=round(t + w.start - off, 3), e=round(t + w.end - off, 3)) for w in u.words]
        lines.append(dict(id=lid, text=text, start=round(t, 3), end=round(t + len(a) / SR, 3), words=words,
                          phonemes=u.phonemes))
        print(f"{lid} {t:6.2f}-{t + len(a) / SR:6.2f}  {u.phonemes}")
        chunks += [a, np.zeros(int(pause * SR), np.float32)]
        t += len(a) / SR + pause
    audio = np.concatenate(chunks)
    BUILD.mkdir(exist_ok=True)
    sf.write(BUILD / "narration.wav", audio, SR, subtype="FLOAT")
    json.dump(dict(sr=SR, duration=len(audio) / SR, lines=lines), open(BUILD / "timeline.json", "w"), indent=1)
    print("total", round(len(audio) / SR, 2), "s")


if __name__ == "__main__":
    main()
