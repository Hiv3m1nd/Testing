"""Painted 2.5D environments: Rome at dusk and Chang'an at dawn.

Each environment is a stack of procedurally drawn silhouette layers with a
depth value. Per frame the layers are re-projected for a slow dolly/push, which
produces real parallax; haze, light shafts, particles and birds are animated on
top. Architecture is kept period-plausible: Roman temples, insulae, aqueduct
arches, umbrella pines and cypresses (no domes); Han halls on rammed-earth
terraces with straight-eaved hip roofs and paired que gate towers.
"""
from __future__ import annotations

import math
from functools import lru_cache

import cv2
import numpy as np
import skia

import gfx
from gfx import Canvas, W, H, paint

LW, LH = int(W * 1.35), int(H * 1.12)  # layer canvas, larger than the frame for camera moves


def _rgb(hexs):
    return tuple(int(hexs[i:i + 2], 16) / 255 for i in (1, 3, 5))


def _mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


# ----------------------------------------------------------------------------- Roman shapes
def temple(c, x, base, w, h, col, cols=6, gap=None, statues=True):
    p = paint(col)
    pod = h * 0.18
    c.drawRect(skia.Rect.MakeLTRB(x - w / 2, base - pod, x + w / 2, base), p)
    colh = h * 0.5
    top = base - pod - colh
    ent = h * 0.1
    if gap is not None:  # sky between the columns of the porch
        c.drawRect(skia.Rect.MakeLTRB(x - w / 2 + w * 0.04, top, x + w / 2 - w * 0.04, base - pod), paint(gap))
        cw = w * 0.92 / (cols * 2 - 1)
        for i in range(cols):
            cx = x - w * 0.46 + i * 2 * cw
            c.drawRect(skia.Rect.MakeLTRB(cx, top, cx + cw, base - pod), p)
    else:
        c.drawRect(skia.Rect.MakeLTRB(x - w / 2 + w * 0.04, top, x + w / 2 - w * 0.04, base - pod), p)
    c.drawRect(skia.Rect.MakeLTRB(x - w / 2, top - ent, x + w / 2, top), p)
    ped = skia.Path()
    ped.moveTo(x - w / 2 - w * 0.01, top - ent)
    ped.lineTo(x, top - ent - w * 0.16)
    ped.lineTo(x + w / 2 + w * 0.01, top - ent)
    ped.close()
    c.drawPath(ped, p)
    if statues:
        for sx, sy, sc in [(x, top - ent - w * 0.16, 1.0), (x - w / 2, top - ent, 0.8), (x + w / 2, top - ent, 0.8)]:
            s = w * 0.035 * sc
            c.drawCircle(sx, sy - s * 4.2, s * 0.8, p)
            c.drawRect(skia.Rect.MakeLTRB(sx - s, sy - s * 3.6, sx + s, sy), p)


def insula(c, x, base, w, h, col, rng, lit=0.0, win_col=(1.0, 0.7, 0.35)):
    c.drawRect(skia.Rect.MakeLTRB(x, base - h, x + w, base), paint(col))
    roof = skia.Path()
    roof.moveTo(x - 4, base - h)
    roof.lineTo(x + w * 0.5, base - h - w * 0.12)
    roof.lineTo(x + w + 4, base - h)
    roof.close()
    c.drawPath(roof, paint(col))
    if lit > 0:
        floors = max(1, int(h / 34))
        for fl in range(floors):
            for k in range(max(1, int(w / 30))):
                if rng.random() < lit:
                    wx = x + 8 + k * 30
                    wy = base - h + 14 + fl * 34
                    c.drawRect(skia.Rect.MakeXYWH(wx, wy, 9, 13), paint(win_col, 0.9))
                    c.drawRect(skia.Rect.MakeXYWH(wx - 6, wy - 6, 21, 25), paint(win_col, 0.25, blur=6))


def umbrella_pine(c, x, base, h, w, col, rng):
    p = paint(col)
    trunk = skia.Path()
    lean = rng.uniform(-0.12, 0.12) * h
    trunk.moveTo(x - h * 0.018, base)
    trunk.cubicTo(x - h * 0.01, base - h * 0.4, x + lean * 0.5, base - h * 0.7, x + lean, base - h * 0.86)
    trunk.lineTo(x + lean + h * 0.02, base - h * 0.86)
    trunk.cubicTo(x + lean * 0.5 + h * 0.02, base - h * 0.7, x + h * 0.02, base - h * 0.4, x + h * 0.018, base)
    trunk.close()
    c.drawPath(trunk, p)
    cx, cy = x + lean, base - h * 0.9
    for _ in range(26):
        ox = rng.uniform(-0.5, 0.5) * w
        oy = -rng.uniform(0, 0.12) * h * (1 - abs(ox) / w * 1.6)
        rx = rng.uniform(0.12, 0.22) * w
        ry = rx * rng.uniform(0.35, 0.5)
        c.drawOval(skia.Rect.MakeXYWH(cx + ox - rx, cy + oy - ry, rx * 2, ry * 2), p)
    c.drawRect(skia.Rect.MakeLTRB(cx - w * 0.45, cy - 2, cx + w * 0.45, cy + h * 0.03), p)


def cypress(c, x, base, h, w, col):
    pth = skia.Path()
    pth.moveTo(x, base - h)
    pth.cubicTo(x + w * 0.55, base - h * 0.7, x + w * 0.6, base - h * 0.2, x + w * 0.15, base)
    pth.lineTo(x - w * 0.15, base)
    pth.cubicTo(x - w * 0.6, base - h * 0.2, x - w * 0.55, base - h * 0.7, x, base - h)
    c.drawPath(pth, paint(col))


def aqueduct(c, x0, x1, base, h, n, col, gap):
    c.drawRect(skia.Rect.MakeLTRB(x0, base - h, x1, base), paint(col))
    aw = (x1 - x0) / n
    for i in range(n):
        ax = x0 + i * aw + aw * 0.18
        pth = skia.Path()
        pth.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(ax, base - h * 0.78, ax + aw * 0.64, base + aw), aw * 0.32, aw * 0.32))
        c.drawPath(pth, paint(gap))
    c.drawRect(skia.Rect.MakeLTRB(x0, base - h - h * 0.08, x1, base - h), paint(col))


def hill(c, x0, x1, base, top, col, rng, bumps=6):
    pth = skia.Path()
    pth.moveTo(x0, base)
    xs = np.linspace(x0, x1, bumps * 6)
    prof = np.sin(np.linspace(0, math.pi, len(xs))) ** 0.8
    jitter = np.convolve(rng.normal(0, 1, len(xs)), np.ones(5) / 5, "same") * 0.06
    for xx, pr, j in zip(xs, prof, jitter):
        pth.lineTo(xx, base - (base - top) * (pr + j))
    pth.lineTo(x1, base)
    pth.close()
    c.drawPath(pth, paint(col))


def statue(c, x, base, h, col):
    p = paint(col)
    c.drawRect(skia.Rect.MakeLTRB(x - h * 0.16, base - h * 0.32, x + h * 0.16, base), p)  # pedestal
    c.drawRect(skia.Rect.MakeLTRB(x - h * 0.2, base - h * 0.36, x + h * 0.2, base - h * 0.32), p)
    body = skia.Path()
    b = base - h * 0.36
    body.moveTo(x - h * 0.1, b)
    body.cubicTo(x - h * 0.13, b - h * 0.25, x - h * 0.12, b - h * 0.45, x - h * 0.07, b - h * 0.55)
    body.lineTo(x + h * 0.08, b - h * 0.55)
    body.cubicTo(x + h * 0.12, b - h * 0.4, x + h * 0.11, b - h * 0.2, x + h * 0.1, b)
    body.close()
    c.drawPath(body, p)
    c.drawCircle(x, b - h * 0.6, h * 0.055, p)
    arm = skia.Path()  # raised right arm (adlocutio pose)
    arm.moveTo(x + h * 0.06, b - h * 0.52)
    arm.lineTo(x + h * 0.2, b - h * 0.68)
    arm.lineTo(x + h * 0.225, b - h * 0.665)
    arm.lineTo(x + h * 0.09, b - h * 0.47)
    arm.close()
    c.drawPath(arm, p)


def column(c, x, base, h, w, col, rim=None):
    p = paint(col)
    c.drawRect(skia.Rect.MakeLTRB(x - w * 0.62, base - h * 0.03, x + w * 0.62, base), p)  # base
    c.drawRect(skia.Rect.MakeLTRB(x - w / 2, base - h, x + w / 2, base - h * 0.03), p)
    cap = skia.Path()
    cap.moveTo(x - w * 0.5, base - h)
    cap.lineTo(x - w * 0.8, base - h - h * 0.05)
    cap.lineTo(x + w * 0.8, base - h - h * 0.05)
    cap.lineTo(x + w * 0.5, base - h)
    cap.close()
    c.drawPath(cap, p)
    c.drawRect(skia.Rect.MakeLTRB(x - w * 0.85, base - h - h * 0.075, x + w * 0.85, base - h - h * 0.05), p)
    if rim:
        c.drawRect(skia.Rect.MakeLTRB(x + w * 0.42, base - h, x + w * 0.5, base - h * 0.03), paint(rim, 0.6, blur=2))


# ----------------------------------------------------------------------------- layer stacks
class Env:
    def __init__(self, layers, sun_xy, shafts=None, sky=None):
        self.layers = layers  # list of (rgba float premult, depth)
        self.sun_xy = sun_xy
        self.shafts = shafts
        self.sky = sky


def _canvas():
    return Canvas(LW, LH)


def _to_rgba(cv):
    return cv.arr.astype(np.float32) / 255.0


def _sky_gradient(stops):
    ys = np.linspace(0, 1, LH, dtype=np.float32)
    pos = np.array([s[0] for s in stops], np.float32)
    cols = np.array([_rgb(s[1]) for s in stops], np.float32)
    col = np.stack([np.interp(ys, pos, cols[:, k]) for k in range(3)], -1)
    return np.repeat(col[:, None, :], LW, axis=1)


def _god_rays(occluder_alpha, sun_xy, strength=0.6, length=0.9, steps=48):
    """Radial blur of the sky's visibility toward the sun -> light shafts."""
    small = cv2.resize(1 - occluder_alpha, (LW // 4, LH // 4), interpolation=cv2.INTER_AREA)
    sx, sy = sun_xy[0] / 4, sun_xy[1] / 4
    yy, xx = np.mgrid[0:small.shape[0], 0:small.shape[1]].astype(np.float32)
    acc = np.zeros_like(small)
    for i in range(steps):
        s = 1 - length * i / steps
        mx = sx + (xx - sx) * s
        my = sy + (yy - sy) * s
        acc += cv2.remap(small, mx, my, cv2.INTER_LINEAR) * (1 - i / steps)
    acc /= steps * 0.5
    dist = np.hypot(xx - sx, yy - sy) / max(small.shape)
    acc *= np.exp(-dist * 2.2)
    return cv2.resize(acc, (LW, LH), interpolation=cv2.INTER_LINEAR) * strength


@lru_cache(maxsize=1)
def rome():
    rng = np.random.default_rng(4)
    horizon = LH * 0.6
    sun = (LW * 0.6, horizon - 70)
    sky = _sky_gradient([(0, "#0e1426"), (0.28, "#2a2740"), (0.45, "#6b3f4c"), (0.55, "#c46a4a"),
                         (0.6, "#f1a463"), (0.62, "#f7c47c"), (0.7, "#c98a5c"), (1.0, "#2a1c1c")])
    # sun + glow
    yy, xx = np.mgrid[0:LH, 0:LW].astype(np.float32)
    d = np.hypot(xx - sun[0], yy - sun[1])
    sky += (np.exp(-d / 420) * 0.55)[..., None] * np.array([1.0, 0.65, 0.35], np.float32)
    sky += (np.exp(-d / 90) * 0.6)[..., None] * np.array([1.0, 0.85, 0.6], np.float32)
    sky[d < 46] = np.array([1.0, 0.96, 0.86], np.float32)
    # thin lit cloud bands
    for k in range(7):
        cy = horizon - rng.uniform(140, 620)
        cx = rng.uniform(0, LW)
        band = np.exp(-((yy - cy) / rng.uniform(6, 14)) ** 2 - ((xx - cx) / rng.uniform(250, 600)) ** 2)
        lit = np.clip(1 - (horizon - cy) / 800, 0.2, 1)
        sky += (band * 0.35 * lit)[..., None] * np.array([1.0, 0.62, 0.45], np.float32)
    layers = []
    haze_col = _rgb("#e39a63")

    def layer(depth, draw, haze):
        cv = _canvas()
        draw(cv.c)
        rgba = _to_rgba(cv)
        a = rgba[..., 3:4]
        rgba[..., :3] = rgba[..., :3] * (1 - haze) + np.array(haze_col, np.float32) * a * haze
        layers.append((rgba, depth))
        return rgba

    far_col = _rgb("#5a3a3e")
    layer(0.1, lambda c: (hill(c, -100, LW * 0.55, horizon + 10, horizon - 70, far_col, rng, 4),
                          hill(c, LW * 0.45, LW + 100, horizon + 10, horizon - 110, far_col, rng, 5)), 0.55)

    def far_city(c):
        col = _rgb("#3d2629")
        for i in range(40):
            x = rng.uniform(0, LW)
            insula(c, x, horizon + 22, rng.uniform(40, 90), rng.uniform(25, 70), col, rng)
        aqueduct(c, LW * 0.72, LW * 1.05, horizon + 10, 60, 14, col, (0, 0, 0, 0)[:3])
    layer(0.25, far_city, 0.4)

    def mid_city(c):
        col = _rgb("#24171a")
        gap = _rgb("#e8935c")
        hill(c, LW * 0.08, LW * 0.5, horizon + 120, horizon - 70, col, rng, 4)   # Capitoline
        temple(c, LW * 0.27, horizon - 52, 230, 230, col, cols=6, gap=gap)       # Jupiter Optimus Maximus
        hill(c, LW * 0.55, LW * 1.0, horizon + 120, horizon - 40, col, rng, 5)   # Palatine
        for i in range(9):
            insula(c, LW * 0.55 + i * 52, horizon - 20 + rng.uniform(-10, 10), 48, rng.uniform(50, 100), col, rng,
                   lit=0.12)
        temple(c, LW * 0.78, horizon - 30, 150, 150, col, cols=4, gap=gap)
        for i in range(30):
            x = rng.uniform(0, LW)
            insula(c, x, horizon + 90, rng.uniform(50, 110), rng.uniform(60, 150), col, rng, lit=0.15)
        for x in rng.uniform(0, LW, 7):
            cypress(c, x, horizon + 95, rng.uniform(110, 170), 26, col)
        for x in (LW * 0.47, LW * 0.6, LW * 0.92):
            umbrella_pine(c, x, horizon + 100, rng.uniform(220, 280), rng.uniform(170, 220), col, rng)
    layer(0.45, mid_city, 0.12)

    def near(c):
        col = _rgb("#120b0c")
        c.drawRect(skia.Rect.MakeLTRB(0, horizon + 150, LW, LH), paint(col))
        for i in range(14):
            insula(c, i * 110 - 40, horizon + 190, 100, rng.uniform(80, 170), col, rng, lit=0.18)
        umbrella_pine(c, LW * 0.12, horizon + 230, 420, 330, col, rng)
        cypress(c, LW * 0.33, horizon + 200, 260, 40, col)
        cypress(c, LW * 0.37, horizon + 200, 220, 34, col)
    layer(0.7, near, 0.0)

    def foreground(c):
        col = _rgb("#070405")
        rim = _rgb("#f0a060")
        c.drawRect(skia.Rect.MakeLTRB(0, LH * 0.83, LW, LH), paint(col))       # terrace floor
        column(c, LW * 0.135, LH * 0.84, 1250, 130, col, rim)
        statue(c, LW * 0.80, LH * 0.80, 470, col)
        c.drawRect(skia.Rect.MakeLTRB(LW * 0.2, LH * 0.795, LW, LH * 0.84), paint(col))  # balustrade
        for k in range(26):
            bx = LW * 0.2 + k * 48
            c.drawRect(skia.Rect.MakeLTRB(bx, LH * 0.77, bx + 22, LH * 0.80), paint(col))
        c.drawRect(skia.Rect.MakeLTRB(LW * 0.2, LH * 0.765, LW, LH * 0.775), paint(col))
    layer(1.0, foreground, 0.0)

    occ = np.zeros((LH, LW), np.float32)
    for rgba, _ in layers:
        occ = np.maximum(occ, rgba[..., 3])
    shafts = _god_rays(occ, sun, 0.55)[..., None] * np.array([1.0, 0.7, 0.42], np.float32)[None, None, :]
    return Env(layers, sun, shafts, sky)


def _ridge(c, x0, x1, base, amp, col, rng, rough=1.0, steps=220):
    xs = np.linspace(x0, x1, steps)
    prof = np.zeros(steps)
    for k, a in [(1, 1.0), (2.3, 0.5), (5.1, 0.25), (11, 0.12), (23, 0.06 * rough)]:
        prof += a * np.sin(xs / LW * math.pi * k + rng.uniform(0, 6.28))
    prof = (prof - prof.min()) / (prof.max() - prof.min())
    pth = skia.Path()
    pth.moveTo(x0, LH)
    for x, p in zip(xs, prof):
        pth.lineTo(x, base - amp * p)
    pth.lineTo(x1, LH)
    pth.close()
    c.drawPath(pth, paint(col))


def han_hall(c, x, base, w, h, col, tiers=2, lit=0.0):
    p = paint(col)
    # rammed-earth terrace (stepped)
    t = h * 0.42
    for k in range(3):
        ww = w * (1.55 - k * 0.12)
        c.drawRect(skia.Rect.MakeLTRB(x - ww / 2, base - t * (k + 1) / 3, x + ww / 2, base - t * k / 3), p)
    y = base - t
    body_h = h * 0.22
    for tier in range(tiers):
        bw = w * (1 - tier * 0.28)
        c.drawRect(skia.Rect.MakeLTRB(x - bw / 2, y - body_h, x + bw / 2, y), p)
        if lit and tier == 0:
            for k in range(7):
                lx = x - bw / 2 + bw * (k + 0.5) / 7
                c.drawRect(skia.Rect.MakeLTRB(lx - 5, y - body_h * 0.7, lx + 5, y - 6), paint((1.0, 0.72, 0.4), lit))
        y -= body_h
        rw = bw * 1.35
        rh = h * 0.13
        roof = skia.Path()  # hip roof, nearly straight eaves (Han style)
        roof.moveTo(x - rw / 2, y + 4)
        roof.quadTo(x - rw * 0.36, y - rh * 0.55, x - bw * 0.32, y - rh)
        roof.lineTo(x + bw * 0.32, y - rh)
        roof.quadTo(x + rw * 0.36, y - rh * 0.55, x + rw / 2, y + 4)
        roof.close()
        c.drawPath(roof, p)
        c.drawRect(skia.Rect.MakeLTRB(x - bw * 0.33, y - rh - 6, x + bw * 0.33, y - rh + 2), p)  # ridge
        for sx in (-1, 1):
            c.drawRect(skia.Rect.MakeLTRB(x + sx * bw * 0.33 - 6, y - rh - 16, x + sx * bw * 0.33 + 6, y - rh), p)
        y -= rh
        body_h *= 0.8


def que_tower(c, x, base, w, h, col):
    p = paint(col)
    c.drawRect(skia.Rect.MakeLTRB(x - w / 2, base - h * 0.55, x + w / 2, base), p)
    y = base - h * 0.55
    for k in range(3):
        rw = w * (1.7 - k * 0.2)
        roof = skia.Path()
        roof.moveTo(x - rw / 2, y)
        roof.lineTo(x - rw * 0.3, y - h * 0.07)
        roof.lineTo(x + rw * 0.3, y - h * 0.07)
        roof.lineTo(x + rw / 2, y)
        roof.close()
        c.drawPath(roof, p)
        if k < 2:
            c.drawRect(skia.Rect.MakeLTRB(x - w * 0.38, y - h * 0.07 - h * 0.1, x + w * 0.38, y - h * 0.07), p)
        y -= h * 0.17


def pine_branch(c, x, y, length, col, rng, direction=1):
    p = paint(col, 1, stroke=18)
    pth = skia.Path()
    pth.moveTo(x, y)
    pts = []
    cx, cy = x, y
    for i in range(6):
        cx += direction * length / 6
        cy += rng.uniform(-20, 40)
        pts.append((cx, cy))
        pth.lineTo(cx, cy)
    c.drawPath(pth, p)
    for (px, py) in pts[1:]:
        for _ in range(3):
            ox, oy = rng.uniform(-60, 60), rng.uniform(-10, 50)
            rx, ry = rng.uniform(60, 110), rng.uniform(16, 26)
            c.drawOval(skia.Rect.MakeXYWH(px + ox - rx, py + oy - ry, rx * 2, ry * 2), paint(col))
            for k in range(14):  # needle tufts
                a = rng.uniform(0, math.pi)
                c.drawLine(px + ox, py + oy, px + ox + math.cos(a) * rx * 1.15, py + oy - math.sin(a) * ry * 2.2,
                           paint(col, 1, stroke=3))


@lru_cache(maxsize=1)
def changan():
    rng = np.random.default_rng(9)
    horizon = LH * 0.62
    sun = (LW * 0.36, LH * 0.38)
    sky = _sky_gradient([(0, "#141b27"), (0.22, "#2e3747"), (0.4, "#6e7280"), (0.52, "#c9a284"),
                         (0.6, "#e8be92"), (0.72, "#9a8678"), (1.0, "#2e2a29")])
    yy, xx = np.mgrid[0:LH, 0:LW].astype(np.float32)
    d = np.hypot(xx - sun[0], yy - sun[1])
    sky += (np.exp(-d / 380) * 0.35)[..., None] * np.array([1.0, 0.75, 0.55], np.float32)
    sky[d < 52] = sky[d < 52] * 0.3 + np.array([0.98, 0.72, 0.58], np.float32) * 0.7
    layers = []
    mist_col = np.array(_rgb("#d8c3a8"), np.float32)

    def layer(depth, draw, haze):
        cv = _canvas()
        draw(cv.c)
        rgba = _to_rgba(cv)
        a = rgba[..., 3:4]
        rgba[..., :3] = rgba[..., :3] * (1 - haze) + mist_col * a * haze
        layers.append((rgba, depth))

    for i, (depth, base, amp, col, haze) in enumerate([
            (0.05, horizon - 210, 260, "#6d7380", 0.55), (0.12, horizon - 120, 230, "#59606d", 0.42),
            (0.2, horizon - 40, 180, "#474c58", 0.3)]):
        layer(depth, lambda c, b=base, a=amp, cl=col: _ridge(c, -50, LW + 50, b, a, _rgb(cl), rng), haze)

    def city(c):
        col = _rgb("#2c2a2c")
        c.drawRect(skia.Rect.MakeLTRB(0, horizon + 40, LW, LH), paint(col))
        c.drawRect(skia.Rect.MakeLTRB(0, horizon - 10, LW, horizon + 40), paint(col))   # city wall
        for k in range(60):
            c.drawRect(skia.Rect.MakeXYWH(k * 26, horizon - 18, 14, 10), paint(col))
        han_hall(c, LW * 0.5, horizon + 5, 300, 420, col, tiers=2, lit=0.0)               # Front Hall, Weiyang
        han_hall(c, LW * 0.2, horizon + 20, 170, 230, col, tiers=1)
        han_hall(c, LW * 0.8, horizon + 20, 190, 250, col, tiers=2)
        for qx in (LW * 0.36, LW * 0.64):
            que_tower(c, qx, horizon + 30, 70, 300, col)
    layer(0.42, city, 0.22)

    def near(c):
        col = _rgb("#151416")
        c.drawRect(skia.Rect.MakeLTRB(0, horizon + 200, LW, LH), paint(col))
        for k in range(16):
            x = k * 95 + rng.uniform(-20, 20)
            hh = rng.uniform(70, 140)
            c.drawRect(skia.Rect.MakeLTRB(x, horizon + 200 - hh, x + 80, horizon + 200), paint(col))
            roof = skia.Path()
            ry = horizon + 200 - hh
            roof.moveTo(x - 30, ry + 6)
            roof.quadTo(x - 5, ry - 14, x + 14, ry - 34)
            roof.lineTo(x + 66, ry - 34)
            roof.quadTo(x + 85, ry - 14, x + 110, ry + 6)
            roof.close()
            c.drawPath(roof, paint(col))
            c.drawRect(skia.Rect.MakeLTRB(x + 10, ry - 40, x + 70, ry - 32), paint(col))
    layer(0.7, near, 0.06)

    def fg(c):
        col = _rgb("#0b0a0b")
        c.drawRect(skia.Rect.MakeLTRB(0, LH * 0.86, LW, LH), paint(col))
        # eave of a pavilion roof framing the top of the shot, with round tile-ends (wadang)
        eave = skia.Path()
        eave.moveTo(-40, -40)
        eave.lineTo(LW + 40, -40)
        eave.lineTo(LW + 40, LH * 0.075)
        eave.quadTo(LW * 0.5, LH * 0.11, -40, LH * 0.135)
        eave.close()
        c.drawPath(eave, paint(col))
        for k in range(34):
            x = k * 46 - 10
            yb = LH * 0.135 - (LH * 0.06) * (x / LW) - 0.0
            c.drawCircle(x, yb + 4, 17, paint(col))
        for bx in (LW * 0.28, LW * 0.72):  # bracket sets
            c.drawRect(skia.Rect.MakeLTRB(bx - 60, LH * 0.09, bx + 60, LH * 0.12), paint(col))
            c.drawRect(skia.Rect.MakeLTRB(bx - 18, LH * 0.12, bx + 18, LH * 0.16), paint(col))
    layer(1.0, fg, 0.0)
    occ = np.zeros((LH, LW), np.float32)
    for rgba, _ in layers:
        occ = np.maximum(occ, rgba[..., 3])
    shafts = _god_rays(occ, sun, 0.35)[..., None] * np.array([1.0, 0.85, 0.65], np.float32)[None, None, :]
    return Env(layers, sun, shafts, sky)


def compose(env: Env, t, dolly=(0.0, 0.0), push=1.0, mist=None, shaft_amt=1.0, seed=0):
    """Render the environment at time t with a camera offset (px) and push-in scale."""
    out = None
    dx, dy = dolly

    def place(img, depth):
        k = 0.15 + 0.85 * depth
        s = 1 + (push - 1) * k
        M = np.float32([[s, 0, W / 2 - s * (LW / 2 + dx * k)], [0, s, H / 2 - s * (LH / 2 + dy * k)]])
        return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    out = place(env.sky, 0.0)
    for i, (rgba, depth) in enumerate(env.layers):
        lay = place(rgba, depth)
        out = out * (1 - lay[..., 3:4]) + lay[..., :3]
        if mist is not None and i < len(env.layers) - 1:
            out = mist(out, i, t)
    if env.shafts is not None and shaft_amt:
        flick = 0.85 + 0.15 * math.sin(t * 0.9)
        out = out + place(env.shafts, 0.3) * shaft_amt * flick
    return out
