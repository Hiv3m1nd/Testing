"""The ruins at Limyra at night: scene layout for rt.py (an illustration, not a survey).

Loosely after the lower city: a rubble-cored podium (the cenotaph), fallen
column drums, a broken colonnade, ashlar walls, the Toçak Dağı cliff with its
rock-cut tombs against the sky.
"""
from __future__ import annotations

import math

import numpy as np

import rt

# material rows: r, g, b, bump, noise_scale, spec
MATS = np.array([
    [0.40, 0.33, 0.26, 0.6, 1.3, 0.00],   # 0 ground earth
    [0.74, 0.68, 0.58, 0.9, 1.1, 0.05],   # 1 limestone
    [0.80, 0.77, 0.71, 0.5, 2.0, 0.12],   # 2 marble (frieze)
    [0.52, 0.47, 0.41, 1.4, 0.9, 0.00],   # 3 rubble core
], np.float64)


def layout(seed=3):
    rng = np.random.default_rng(seed)
    boxes, cyls = [], []
    B, C = boxes.append, cyls.append
    # --- the podium (cenotaph core) at the far end of the walk, rubble core with marble facing remnants
    B(rt.box((0.0, 1.6, 14.0), (4.0, 1.6, 4.0), rt.rot(0.05), mat=3))
    B(rt.box((0.0, 3.35, 14.0), (3.2, 0.15, 3.2), rt.rot(0.05), mat=1))
    # frieze slabs leaning against the podium face (panel 0 carries the relief)
    B(rt.box((-1.4, 0.75, 9.75), (1.25, 0.75, 0.18), rt.rot(0.05, -0.12), mat=2, panel=0))
    B(rt.box((1.5, 0.55, 9.9), (1.0, 0.55, 0.16), rt.rot(-0.1, -0.08), mat=2, panel=1))
    # --- colonnade along the left of the walk: bases, standing shafts of varying height
    for k in range(6):
        z = 1.0 + k * 2.4
        x = -3.4
        B(rt.box((x, 0.18, z), (0.55, 0.18, 0.55), rt.rot(rng.uniform(-0.05, 0.05)), mat=1))
        h = [3.4, 2.1, 0.0, 4.2, 1.2, 2.8][k]
        if h > 0:
            C(rt.cyl((x, 0.36 + h / 2, z), (0, 1, 0), 0.38, h / 2, mat=1, flutes=20))
    # right side: low ashlar wall, broken
    for k in range(9):
        z = -0.5 + k * 1.3
        hgt = [1.0, 1.2, 0.6, 1.4, 0.9, 0.3, 1.1, 1.3, 0.7][k]
        B(rt.box((3.6 + rng.uniform(-0.05, 0.05), hgt / 2, z), (0.45, hgt / 2, 0.62),
                 rt.rot(rng.uniform(-0.04, 0.04)), mat=1))
    # fallen column drums on the ground
    for (x, z, yaw, r, hl) in ((-1.6, 3.2, 0.6, 0.36, 0.45), (1.2, 5.6, -0.3, 0.36, 0.5),
                               (-0.9, 7.4, 1.4, 0.36, 0.42), (2.0, 2.0, 2.2, 0.30, 0.35)):
        C(rt.cyl((x, r, z), (math.cos(yaw), 0, math.sin(yaw)), r, hl, mat=1, flutes=20))
    # scattered blocks
    for _ in range(14):
        x = rng.uniform(-2.6, 2.8)
        z = rng.uniform(0.5, 12.0)
        s = rng.uniform(0.15, 0.4)
        B(rt.box((x, s * 0.6, z), (s * 1.4, s * 0.6, s), rt.rot(rng.uniform(0, 3), rng.uniform(-0.15, 0.15)), mat=1))
    return np.array(boxes, np.float64), np.array(cyls, np.float64)
