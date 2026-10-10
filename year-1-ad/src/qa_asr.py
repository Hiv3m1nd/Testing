"""QA helper: objective narration-intelligibility check with offline ASR.

Transcribes every narration line (cut by build/timeline.json) with pocketsphinx
and prints the word error rate against the script. Compare the dry voice with
the mix: a large jump means the music/SFX bed is masking speech.

  pip install pocketsphinx jiwer
  python qa_asr.py ../build/narration.wav ../build/mix_premaster.wav

Reference values from 1 AD: dry voice 0.37, final mix 0.57-0.58 (pocketsphinx
is far less noise-tolerant than human ears, and proper nouns inflate the
baseline; treat it as a relative measure only).
"""
import json
import re
import sys
from pathlib import Path

import jiwer
import numpy as np
import soundfile as sf
from pocketsphinx import Decoder
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[1]


def main():
    d = json.load(open(ROOT / "build" / "timeline.json"))
    dec = Decoder()

    def asr(x, sr):
        x16 = resample_poly(x, 16000, sr)
        pcm = (np.clip(x16, -1, 1) * 32767).astype(np.int16).tobytes()
        dec.start_utt()
        dec.process_raw(pcm, full_utt=True)
        dec.end_utt()
        return dec.hyp().hypstr if dec.hyp() else ""

    for name in sys.argv[1:]:
        x, sr = sf.read(name)
        if x.ndim > 1:
            x = x.mean(1)
        refs, hyps = [], []
        for line in d["lines"]:
            a, b = int((line["start"] - 0.05) * sr), int((line["end"] + 0.1) * sr)
            refs.append(re.sub(r"[^a-z0-9' ]", " ", line["text"].lower()))
            seg = x[a:b]
            hyps.append(asr(seg / (np.abs(seg).max() + 1e-9) * 0.8, sr))
        print(Path(name).name, "WER", round(jiwer.wer(" ".join(refs), " ".join(hyps)), 3))


if __name__ == "__main__":
    main()
