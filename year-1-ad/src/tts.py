"""Local Kokoro-82M narration with word-level timestamps.

Kokoro runs through onnxruntime on the CPU. The ONNX graph is patched (see
`patch_model`) to expose the duration predictor's per-phoneme frame counts as a
second output, so every word in the narration gets an exact start/end time for
subtitles and edit points - no ASR or forced alignment needed.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODELS = Path(os.environ.get("KOKORO_DIR", "/tmp/claude-0/-home-user-Testing/e9a9e9b1-4420-50a9-bd82-ad323edc7d03/scratchpad/models"))
SR = 24000
SAMPLES_PER_FRAME = 600  # one predicted duration unit = 25 ms at 24 kHz


def patch_model(src: Path, dst: Path) -> None:
    """Add the duration predictor's clipped frame counts as a graph output."""
    import onnx

    m = onnx.load(str(src))
    clip = [n for n in m.graph.node if n.op_type == "Clip"][0]
    m.graph.output.append(onnx.helper.make_tensor_value_info(clip.output[0], onnx.TensorProto.FLOAT, None))
    onnx.save(m, str(dst))


@dataclass
class Word:
    text: str
    start: float
    end: float


@dataclass
class Utterance:
    audio: np.ndarray
    words: list[Word] = field(default_factory=list)
    phonemes: str = ""


class Narrator:
    def __init__(self, voice: str | dict = "af_heart", model: str = "kokoro-fp32-dur.onnx"):
        import onnxruntime as ort
        from misaki import en, espeak

        path = MODELS / model
        if not path.exists():
            patch_model(MODELS / "kokoro-fp32.onnx", path)
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = os.cpu_count() or 4
        self.sess = ort.InferenceSession(str(path), opts, providers=["CPUExecutionProvider"])
        self.vocab = json.load(open(ROOT / "assets/tts/kokoro_config.json"))["vocab"]
        self.g2p = en.G2P(trf=False, british=False, fallback=espeak.EspeakFallback(british=False))
        self.voice = self._load_voice(voice)

    @staticmethod
    def _load_voice(voice):
        """A voice name, or a {name: weight} blend of style tables."""
        if isinstance(voice, str):
            voice = {voice: 1.0}
        acc = None
        for name, w in voice.items():
            v = np.fromfile(MODELS / "voices" / f"{name}.bin", dtype=np.float32).reshape(-1, 1, 256)
            acc = v * w if acc is None else acc + v * w
        return acc / sum(voice.values())

    def phonemize(self, text: str):
        ps, tokens = self.g2p(text)
        return ps, tokens

    def synth(self, text: str, speed: float = 1.0) -> Utterance:
        ps, tokens = self.phonemize(text)
        ids = [self.vocab[c] for c in ps if c in self.vocab]
        assert len(ids) <= 510, f"phrase too long ({len(ids)} phonemes): {text[:60]}"
        style = self.voice[len(ids)]
        audio, dur = self.sess.run(None, {
            "input_ids": np.array([[0, *ids, 0]], dtype=np.int64),
            "style": style.astype(np.float32),
            "speed": np.array([speed], dtype=np.float32),
        })
        audio = audio[0]
        dur = dur.reshape(-1).astype(int)  # len(ids)+2, includes boundary pads
        # cumulative time at the start of each phoneme character of `ps`
        kept = [c for c in ps if c in self.vocab]
        frame_t = np.concatenate([[0], np.cumsum(dur)]) * SAMPLES_PER_FRAME / SR
        # map: index in `kept` -> start time (offset 1 for leading pad)
        words = []
        cursor = 0  # position in ps (kept chars)
        kept_str = "".join(kept)
        for tk in tokens:
            if not tk.phonemes:
                continue
            p = "".join(c for c in tk.phonemes if c in self.vocab)
            if not p:
                continue
            idx = kept_str.find(p, cursor)
            if idx < 0:
                continue
            s = frame_t[1 + idx]
            e = frame_t[1 + idx + len(p)]
            cursor = idx + len(p)
            if re.search(r"\w", tk.text):
                words.append(Word(tk.text, float(s), float(e)))
        return Utterance(audio=audio, words=words, phonemes=ps)
