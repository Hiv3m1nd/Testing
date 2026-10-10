"""Access to narration timing: line starts/ends and individual word times."""
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _norm(s):
    return re.sub(r"[^a-z0-9']", "", s.lower())


class Timeline:
    def __init__(self, path=ROOT / "build" / "timeline.json"):
        d = json.load(open(path))
        self.lines = d["lines"]
        self.duration = d["duration"]

    def s(self, i):
        return self.lines[i]["start"]

    def e(self, i):
        return self.lines[i]["end"]

    def w(self, i, word, nth=0, end=False):
        """Start (or end) time of the nth occurrence of `word` in line i."""
        target = _norm(word)
        hits = [x for x in self.lines[i]["words"] if _norm(x["w"]).startswith(target)]
        if not hits:
            raise KeyError(f"{word!r} not in line {i}: {self.lines[i]['text']}")
        x = hits[min(nth, len(hits) - 1)]
        return x["e"] if end else x["s"]


@lru_cache(maxsize=1)
def TL():
    return Timeline()
