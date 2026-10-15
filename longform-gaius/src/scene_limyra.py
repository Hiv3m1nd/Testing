"""The ruins at Limyra at night, laid out for sdf.py (an illustration, not a survey).

Loosely after the lower city: the rubble-cored podium of the cenotaph with
marble frieze slabs lying at its foot, a broken colonnade along the left of
the walk, an ashlar wall to the right, fallen drums and scattered blocks, and
the Toçak Dağı cliff with its rock-cut tombs against the sky (drawn in the sky
shader). Shallow water stands in the hollows.
"""
from __future__ import annotations

import math

import numpy as np

import sdf
from sdf import prim, rot, axis_frame

# material rows: r, g, b, bump, noise_scale, spec
MATS = np.array([
    [0.30, 0.27, 0.23, 0.8, 1.6, 0.00],   # 0 earth
    [0.64, 0.61, 0.56, 1.0, 1.2, 0.04],   # 1 limestone
    [0.80, 0.77, 0.70, 0.6, 1.8, 0.10],   # 2 marble (frieze)
    [0.50, 0.48, 0.44, 1.3, 1.0, 0.00],   # 3 rubble core
], np.float64)

LO = (-9.0, -0.30, -4.0)
HI = (9.0, 6.2, 24.0)


def prims(seed=3):
    rng = np.random.default_rng(seed)
    P = [prim(2, (0, 0, 0), (0, 0, 0), mat=0, erosion=0.0)]   # ground must be index 0
    A = P.append
    # ---- cenotaph core: a massive rubble-and-mortar podium, its marble skin long gone
    A(prim(3, (0.4, 2.0, 17.2), (4.3, 2.0, 3.7), rot(0.06), rounding=0.35, erosion=0.05, seed=1.0,
           break_y=1.2, break_amp=0.9, mat=3))
    A(prim(3, (-0.6, 3.4, 18.0), (2.6, 1.4, 2.4), rot(0.10, 0.0, 0.02), rounding=0.4, erosion=0.06, seed=1.7,
           break_y=0.7, break_amp=1.0, mat=3))
    A(prim(3, (2.9, 1.1, 14.4), (1.3, 1.1, 1.0), rot(-0.2), rounding=0.3, erosion=0.05, seed=2.3,
           break_y=0.5, break_amp=0.6, mat=3))
    A(prim(0, (0.4, 0.30, 13.2), (4.6, 0.30, 0.30), rot(0.06), erosion=0.012, seed=2.0, mat=1))   # euthynteria
    A(prim(0, (-2.6, 0.85, 13.35), (1.0, 0.26, 0.26), rot(0.06), erosion=0.012, seed=3.0, mat=1))
    A(prim(0, (-0.7, 0.82, 13.32), (0.7, 0.24, 0.26), rot(0.07), erosion=0.012, seed=3.5, mat=1))
    # ---- frieze slabs at its foot (panels 0/1 carry the carved relief)
    A(prim(0, (-1.3, 0.62, 11.6), (1.30, 0.60, 0.17), rot(0.18, -0.16), erosion=0.012, seed=5.0, mat=2, panel=0))
    A(prim(0, (1.7, 0.40, 11.4), (0.95, 0.40, 0.15), rot(-0.25, -0.05, 0.03), erosion=0.012, seed=6.0, mat=2, panel=1,
           break_y=0.25, break_amp=0.18))
    # ---- colonnade on the left: plinths and broken fluted shafts
    for k in range(7):
        z = -1.0 + k * 2.5
        x = -3.6
        A(prim(0, (x, 0.22, z), (0.62, 0.22, 0.62), rot(rng.uniform(-0.04, 0.04)), erosion=0.010, seed=10 + k, mat=1))
        A(prim(0, (x, 0.52, z), (0.50, 0.08, 0.50), rot(rng.uniform(-0.04, 0.04)), erosion=0.008, seed=20 + k, mat=1))
        h = [4.6, 2.3, 0.0, 3.6, 1.1, 2.9, 0.6][k]
        if h > 0:
            A(prim(1, (x, 0.60 + h / 2 + 0.3, z), (0.40, h / 2 + 0.3, 0), rot(rng.uniform(0, 3)), flutes=20,
                   erosion=0.008, seed=30 + k, break_y=h / 2 - 0.15, break_amp=0.35, mat=1))
    # ---- ashlar wall on the right, courses of blocks, broken top line
    for k in range(10):
        z = -2.0 + k * 1.32
        top = [1.6, 1.9, 1.0, 2.2, 1.5, 0.6, 1.8, 2.0, 1.2, 0.8][k]
        y = 0.0
        c = 0
        while y < top - 0.05:
            hh = min(0.42, top - y)
            off = 0.0 if c % 2 == 0 else 0.33
            A(prim(0, (3.9 + rng.uniform(-0.04, 0.04), y + hh / 2, z + off), (0.42, hh / 2 - 0.004, 0.64),
                   rot(rng.uniform(-0.03, 0.03), 0, rng.uniform(-0.01, 0.01)), erosion=0.009, seed=40 + k * 5 + c, mat=1))
            y += hh
            c += 1
    # ---- fallen drums
    for (x, z, yaw, r, hl) in ((-1.7, 3.0, 0.6, 0.40, 0.48), (1.4, 6.0, -0.4, 0.40, 0.52),
                               (-0.9, 8.2, 1.4, 0.40, 0.44), (2.3, 1.6, 2.2, 0.34, 0.38), (-2.4, 10.2, 0.2, 0.40, 0.5)):
        A(prim(1, (x, r - 0.02, z), (r, hl, 0), axis_frame((math.cos(yaw), 0, math.sin(yaw))), flutes=20,
               erosion=0.008, seed=70 + x, mat=1))
    # ---- scattered blocks
    for q in range(22):
        x = rng.uniform(-2.8, 3.0)
        z = rng.uniform(-1.0, 12.5)
        if abs(x) < 0.6 and z < 9:
            x += 1.2 * np.sign(x + 1e-3)
        s = rng.uniform(0.12, 0.38)
        A(prim(0, (x, s * 0.55 - 0.02, z), (s * 1.5, s * 0.55, s), rot(rng.uniform(0, 3), rng.uniform(-0.12, 0.12)),
               erosion=0.008, seed=90 + q, mat=1))
    return np.array(P)


def relief_panels(n=2, H=512, W=1024):
    """Height maps for the frieze slabs: a procession, cut in low relief (illustrative)."""
    import cv2
    out = np.zeros((n, H, W), np.float32)
    for p in range(n):
        m = np.zeros((H, W), np.float32)
        # figures: togate silhouettes built from ellipses, varied stance
        rng = np.random.default_rng(11 + p)
        x = 70
        while x < W - 60:
            s = rng.uniform(0.9, 1.08)
            base = int(H * 0.86)
            hgt = int(H * 0.66 * s)
            head_r = int(hgt * 0.075)
            cx = x
            # body (toga): a tapered ellipse stack
            cv2.ellipse(m, (cx, base - hgt // 2), (int(hgt * 0.13), hgt // 2 - head_r), 0, 0, 360, 1.0, -1)
            cv2.ellipse(m, (cx + int(hgt * 0.03), base - int(hgt * 0.62)), (int(hgt * 0.16), int(hgt * 0.16)), 0, 0, 360, 1.0, -1)
            cv2.circle(m, (cx + int(hgt * 0.02), base - hgt + head_r), head_r, 1.0, -1)
            # fold lines
            for f in range(5):
                a = cx - int(hgt * 0.1) + f * int(hgt * 0.05)
                cv2.line(m, (a, base - int(hgt * 0.55)), (a + int(hgt * 0.06), base - 6), 0.72, 3)
            x += int(hgt * 0.42) + int(rng.uniform(0, 30))
        m = cv2.GaussianBlur(m, (0, 0), 3.0)
        # cornice band and ground line
        m[: int(H * 0.08)] = np.maximum(m[: int(H * 0.08)], 0.95)
        m[int(H * 0.88):] = np.maximum(m[int(H * 0.88):], 0.85)
        # erosion of the carving
        noise = cv2.resize(np.random.default_rng(p).random((H // 16, W // 16)).astype(np.float32), (W, H),
                           interpolation=cv2.INTER_CUBIC)
        m = np.clip(m * (0.85 + 0.25 * noise) - 0.08 * (noise > 0.8), 0, 1)
        out[p] = cv2.GaussianBlur(m, (0, 0), 1.2)
    return out


_BAKED = None


def baked(h=0.02):
    """Bake once and cache on disk, keyed by the scene and SDF source (bit-identical reload)."""
    global _BAKED
    if _BAKED is None:
        import hashlib
        from pathlib import Path
        here = Path(__file__).resolve().parent
        key = hashlib.sha1((here / "sdf.py").read_bytes() + (here / "scene_limyra.py").read_bytes() +
                           str(h).encode()).hexdigest()[:12]
        cache = here.parent / "build" / "cache" / f"ruins_{key}.npz"
        if cache.exists():
            z = np.load(cache)
            B = sdf.Baked.__new__(sdf.Baked)
            for k in ("prims", "dist", "pid", "coarse", "G", "gh", "GH"):
                setattr(B, k, z[k])
            _BAKED = B
        else:
            _BAKED = sdf.Baked(prims(), LO, HI, h=h, band=0.3, coarse_cells=12)
            cache.parent.mkdir(parents=True, exist_ok=True)
            tmp = cache.with_suffix(".tmp.npz")
            np.savez(tmp, **{k: getattr(_BAKED, k) for k in ("prims", "dist", "pid", "coarse", "G", "gh", "GH")})
            tmp.replace(cache)
    return _BAKED
