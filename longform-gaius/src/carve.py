"""Letters cut into stone (V-section grooves) with optional gold leaf, as an hfr.Relief.

Text is rasterised with skia (Cinzel, OFL), the groove depth comes from the
distance to the letter edge (a true V-cut: deepest along each stroke's spine),
and the stone surface gets weathering, pitting and tooling marks."""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "year-1-ad" / "src"))
import gfx  # noqa: E402
from gfx import Canvas  # noqa: E402

import hfr  # noqa: E402


def fbm(h, w, scale, seed, octaves=5, persistence=0.5):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = max(2, int(h / scale * 2 ** o) + 2), max(2, int(w / scale * 2 ** o) + 2)
        acc += amp * cv2.resize(rng.random((gh, gw)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= persistence
    acc /= tot
    return (acc - acc.min()) / (acc.max() - acc.min() + 1e-6)


def text_mask(W, H, lines):
    """lines: [(text, font_name, size_px, weight, y_baseline, tracking)] -> float mask, plus per-line masks."""
    out = []
    for (s, fname, size, wt, y, tr) in lines:
        cv = Canvas(W, H)
        f = gfx.font(fname, size, wt)
        gfx.draw_text(cv, s, W / 2, y, f, (1, 1, 1), 1.0, tracking=tr)
        out.append(cv.arr[..., 3].astype(np.float32) / 255.0)
    return out


def vcut(mask, px_per_m, depth_ratio=0.9):
    """Groove height (negative, metres) from a letter mask: depth grows with distance to the edge."""
    m8 = (mask > 0.5).astype(np.uint8)
    d = cv2.distanceTransform(m8, cv2.DIST_L2, 5)
    # local stroke half-width = max distance in a neighbourhood
    half = cv2.dilate(d, np.ones((31, 31), np.uint8))
    prof = np.where(m8 > 0, d / np.maximum(half, 1.0), 0.0)
    depth = -prof * np.maximum(half, 1.0) / px_per_m * depth_ratio
    # anti-alias the lip of the cut
    return cv2.GaussianBlur(depth.astype(np.float32), (0, 0), 0.8), m8


def stone(W, H, px_per_m, seed=4, base=(0.66, 0.61, 0.53), marble=False):
    """Weathered limestone/marble face: height (m) and linear albedo."""
    n1 = fbm(H, W, px_per_m * 0.35, seed, 6)
    n2 = fbm(H, W, px_per_m * 0.04, seed + 1, 4)
    n3 = fbm(H, W, px_per_m * 0.008, seed + 2, 3)
    pits = (fbm(H, W, px_per_m * 0.006, seed + 3, 2) > 0.80).astype(np.float32)
    pits = cv2.GaussianBlur(pits, (0, 0), 1.2)
    # broad undulation + chisel-tooled texture + grain + pitting
    h = (n1 - 0.5) * 0.004 + (n2 - 0.5) * 0.0012 + (n3 - 0.5) * 0.0003 - pits * 0.0012
    # claw-chisel tooling: faint diagonal striations
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    tool = np.sin((xx * 0.7 + yy * 0.7) / (px_per_m * 0.0035)) * (fbm(H, W, px_per_m * 0.03, seed + 9, 3) - 0.3)
    h += np.clip(tool, 0, None) * 0.00012
    a = np.array(base, np.float32)
    k = (0.84 + 0.16 * (n1 - 0.5) + 0.22 * (n2 - 0.5) + 0.10 * (n3 - 0.5)) * (1 - 0.35 * pits)
    stain = np.clip((fbm(H, W, px_per_m * 0.12, seed + 5, 5) - 0.58) * 1.2, 0, 1)
    alb = a[None, None] * k[..., None] * (1 - 0.30 * stain[..., None])
    if marble:
        n4 = fbm(H, W, px_per_m * 0.25, seed + 7, 6)
        veins = np.clip(1 - np.abs(n4 - 0.5) * 30, 0, 1) ** 2 * 0.18
        alb = alb - veins[..., None] * np.array([0.30, 0.29, 0.28], np.float32)
    return h.astype(np.float32), np.clip(alb, 0, 1).astype(np.float32)


GOLD = np.array([0.95, 0.70, 0.30], np.float32)


def slab(W, H, width_m, lines, gold=1.0, seed=4, base=(0.66, 0.61, 0.53), marble=False, depth_ratio=0.9):
    """Build a carved slab. Returns dict with hm, albedo, matmap, texel, line masks (for staged reveals)."""
    px_per_m = W / width_m
    h, alb = stone(W, H, px_per_m, seed, base, marble)
    masks = text_mask(W, H, lines)
    groove = np.zeros((H, W), np.float32)
    letters = np.zeros((H, W), np.float32)
    for m in masks:
        g, m8 = vcut(m, px_per_m, depth_ratio)
        groove = np.minimum(groove, g)
        letters = np.maximum(letters, m)
    hm = (h + groove + 0.01).astype(np.float32)   # 1 cm proud of the slab origin
    gold_m = np.clip(letters, 0, 1) * gold
    alb = alb * (1 - gold_m[..., None]) + GOLD[None, None] * gold_m[..., None] * (0.8 + 0.2 * fbm(H, W, px_per_m * 0.01, 3, 3))[..., None]
    return dict(hm=hm, albedo=alb.astype(np.float32), matmap=gold_m.astype(np.float32), texel=1.0 / px_per_m,
                masks=masks, size=(W, H))


def relief_object(b, centre=(0, 0, 0), matmap=None):
    W, H = b["size"]
    tx = b["texel"]
    u, v, n = np.array([1.0, 0, 0]), np.array([0, -1.0, 0]), np.array([0, 0, -1.0])
    o = np.asarray(centre, float) - u * (W / 2) * tx - v * (H / 2) * tx
    return hfr.Relief(b["hm"], b["albedo"], o, u, v, n, tx, 1.0, matmap=b["matmap"] if matmap is None else matmap)
