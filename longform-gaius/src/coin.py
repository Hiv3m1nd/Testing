"""The Gaius & Lucius denarius (RIC I 207 reverse), the same design as in the Shorts,
re-drawn at 2.4x resolution and turned into a real 3D object for hfr.

Reverse: Gaius and Lucius standing, shields and spears, simpulum and lituus between;
legend AVGVSTI F COS DESIG PRINC IVVENT, exergue C L CAESARES. (Illustration.)"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "year-1-ad" / "src"))
import relief  # noqa: E402
from gfx import Canvas  # noqa: E402

import hfr  # noqa: E402

S = 2.4
N = int(relief.SIZE * S)


def _mask_hi(draw_fn, size):
    cv = Canvas(N, N)
    cv.c.scale(S, S)
    draw_fn(cv)
    return cv.arr[..., 3].astype(np.float32) / 255.0


def _blur(m, s):
    s = s * S
    return cv2.GaussianBlur(m, (0, 0), s)


def _fbm(h, w, scale, seed, octaves=5, persistence=0.5):
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


def _finish(fine, soft, seed=11, wear=0.35):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    ang = np.arctan2(yy - N / 2, xx - N / 2)
    rad = np.hypot(yy - N / 2, xx - N / 2)
    wob = 0.0
    for k, amp in [(2, 9), (3, 7), (5, 4), (9, 2)]:
        wob = wob + amp * S * np.sin(k * ang + rng.uniform(0, 6.28))
    R = N * 0.46 + wob
    disc = np.clip((R - rad) / (2.0 * S), 0, 1)
    h = 0.45 * _blur(soft, 7) + 0.4 * _blur(soft, 2.5) + 0.25 * _blur(fine, 1.2)
    rim = np.clip((rad - (R - 26 * S)) / (10 * S), 0, 1) * disc * 0.35
    edge_drop = np.clip((R - rad) / (30 * S), 0, 1)
    noise = _fbm(N, N, 140 * S, seed, 6)
    pits = _fbm(N, N, 5 * S, seed + 5, 3)
    scratches = _fbm(N, N, 40 * S, seed + 9, 4)
    h = (h * (1 - wear * noise) + rim) * edge_drop * disc + (pits - 0.5) * 0.004 * disc + (noise - 0.5) * 0.03 * disc
    h += (np.abs(scratches - 0.5) < 0.004) * -0.004 * disc
    cavity = np.clip((_blur(h, 6) - h) * 18, 0, 1)
    return h.astype(np.float32), disc.astype(np.float32), cavity.astype(np.float32), R


def build(diameter_mm=19.0, thickness_mm=1.7, relief_mm=0.55):
    old = relief.mask_from
    relief.mask_from = _mask_hi
    try:
        # call the undecorated builder so the 1 AD cache is untouched; intercept the finish step
        captured = {}
        old_finish = relief._finish_coin
        relief._finish_coin = lambda f, s, seed, wear=0.35: captured.update(f=f, s=s, seed=seed) or None
        relief.coin_gaius_lucius.__wrapped__()
        relief._finish_coin = old_finish
    finally:
        relief.mask_from = old
    h, disc, cav, R = _finish(captured["f"], captured["s"], captured["seed"])
    texel = diameter_mm / 1000.0 / (2 * R.mean())          # metres per texel
    hn = h / max(h.max(), 1e-6)
    height = (thickness_mm + relief_mm * hn) / 1000.0
    height = np.where(disc > 0.5, height, hfr.HOLE).astype(np.float32)
    # silver, toned dark in the recesses, bright where worn
    silver = np.array([0.80, 0.78, 0.74], np.float32)
    tone = np.array([0.20, 0.16, 0.13], np.float32)
    k = np.clip(cav * 0.85, 0, 1)[..., None]
    alb = silver * (1 - k) + tone * k
    alb *= (0.85 + 0.15 * _fbm(N, N, 60 * S, 3, 4))[..., None]
    matmap = np.clip(1.0 - cav * 0.7, 0.2, 1.0).astype(np.float32)
    return dict(hm=height, albedo=alb.astype(np.float32), matmap=matmap, texel=texel, size=N)


def relief_object(centre=(0, 0, 0), yaw=0.0, pitch=0.0):
    b = build()
    tx = b["texel"]
    # local frame rotated by yaw (about y) and pitch (about x); face looks toward -z at yaw 0
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    u = np.array([cy, 0, sy])
    n0 = np.array([-sy, 0, cy]) * -1          # out of the face, toward the camera
    v0 = np.array([0, -1.0, 0])
    v = v0 * cp + n0 * sp
    n = n0 * cp - v0 * sp
    o = np.asarray(centre, float) - u * (b["size"] / 2) * tx - v * (b["size"] / 2) * tx
    R = hfr.Relief(b["hm"], b["albedo"], o, u, v, n, tx, 1.0, matmap=b["matmap"])
    R.hmin = 0.0
    return R
