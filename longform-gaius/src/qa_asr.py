"""Narration intelligibility: pocketsphinx WER per line, dry voice vs. full mix (relative measure)."""
import json, re, sys
from pathlib import Path
import jiwer, numpy as np, soundfile as sf
from pocketsphinx import Decoder
from scipy.signal import resample_poly
ROOT = Path(__file__).resolve().parents[1]
d = json.load(open(ROOT / "build" / "timeline.json"))
dec = Decoder()
def asr(x, sr):
    x16 = resample_poly(x, 16000, sr)
    dec.start_utt(); dec.process_raw((np.clip(x16, -1, 1) * 32767).astype(np.int16).tobytes(), full_utt=True); dec.end_utt()
    return dec.hyp().hypstr if dec.hyp() else ""
for name in sys.argv[1:]:
    x, sr = sf.read(name)
    if x.ndim > 1: x = x.mean(1)
    refs, hyps = [], []
    for line in d["lines"]:
        a, b = int((line["start"] - 0.05) * sr), int((line["end"] + 0.1) * sr)
        refs.append(re.sub(r"\[([^\]]+)\]\(/[^)]*/\)", r"\1", line["text"]).lower())
        refs[-1] = re.sub(r"[^a-z0-9' ]", " ", refs[-1])
        seg = x[a:b]
        hyps.append(asr(seg / (np.abs(seg).max() + 1e-9) * 0.8, sr))
    print(Path(name).name, "WER", round(jiwer.wer(" ".join(refs), " ".join(hyps)), 3))
