"""Burned-in captions synced to the narration's word timestamps.

One short line at a time (Shorts/Reels/TikTok style), placed above the
platforms' bottom UI band, with the spoken word highlighted in gold.
"""
from __future__ import annotations

import re
from functools import lru_cache

import skia

import gfx
from gfx import Canvas, W, paint
from timeline import TL

Y = 1468          # baseline; keeps clear of the bottom ~22% covered by platform UI
MAX_W = 820       # keeps clear of the right-hand action buttons
SIZE = 50


@lru_cache(maxsize=1)
def chunks():
    """Split each narration line into caption chunks of whole words."""
    f = gfx.font("inter", SIZE, 600)
    out = []
    for li, line in enumerate(TL().lines):
        words = line["words"]
        # map display text tokens (with punctuation) onto timed words
        disp = line["text"].split()
        cur, cur_text = [], []
        k = 0
        for w in words:
            n_parts = len(w["w"].split())
            tok = " ".join(disp[k:k + n_parts]) if k < len(disp) else w["w"]
            k += n_parts
            trial = " ".join(cur_text + [tok])
            if cur and (gfx.text_width(trial, f) > MAX_W or len(cur) >= 7):
                out.append((li, cur, cur_text))
                cur, cur_text = [], []
            cur.append(w)
            cur_text.append(tok)
            if re.search(r"[.:;?!,]$", tok) and len(cur) >= 3:
                out.append((li, cur, cur_text))
                cur, cur_text = [], []
        if cur:
            out.append((li, cur, cur_text))
    timed = []
    for i, (li, ws, toks) in enumerate(out):
        start = ws[0]["s"] - 0.08
        end = ws[-1]["e"] + 0.35
        if i + 1 < len(out):
            end = min(end, out[i + 1][1][0]["s"] - 0.1)
        timed.append((start, end, ws, toks))
    return timed


def draw(cv: Canvas, t):
    f = gfx.font("inter", SIZE, 600)
    for start, end, ws, toks in chunks():
        if not (start - 0.1 <= t <= end + 0.15):
            continue
        a = gfx.smooth(gfx.seg(t, start - 0.1, start + 0.06)) * (1 - gfx.smooth(gfx.seg(t, end, end + 0.15)))
        if a <= 0.01:
            continue
        text = " ".join(toks)
        width = gfx.text_width(text, f)
        x = W / 2 - width / 2
        pad_x, pad_y = 26, 20
        box = skia.Rect.MakeLTRB(x - pad_x, Y - SIZE * 0.92 - pad_y, x + width + pad_x, Y + SIZE * 0.3 + pad_y)
        cv.c.drawRRect(skia.RRect.MakeRectXY(box, 18, 18), paint((0.0, 0.0, 0.0), 0.42 * a, blur=6))
        space = gfx.text_width("a b", f) - gfx.text_width("ab", f)
        for w, tok in zip(ws, toks):
            active = w["s"] - 0.04 <= t <= w["e"] + 0.04
            done = t > w["e"]
            rgb = gfx.PALE_GOLD if active else (gfx.IVORY if done or t < w["s"] else gfx.IVORY)
            gfx.draw_text(cv, tok, x, Y, f, rgb, a * (1.0 if active or done else 0.82), align="left", shadow=0.6)
            x += gfx.text_width(tok, f) + space
        break
