"""Reusable visual effects: stars, dust, flares, paper, ink calligraphy, pheasant, lamps, ships."""
from __future__ import annotations

import math
from functools import lru_cache

import cv2
import numpy as np
import skia

import gfx
from gfx import Canvas, W, H, paint, seg, smooth


# ----------------------------------------------------------------------------- backgrounds
@lru_cache(maxsize=None)
def starfield(seed=1):
    rng = np.random.default_rng(seed)
    img = np.zeros((H, W, 3), np.float32)
    n = 2600
    xs, ys = rng.uniform(0, W, n), rng.uniform(0, H, n)
    mag = rng.power(6, n)
    tint = rng.choice([0, 1, 2], n, p=[0.7, 0.18, 0.12])
    cols = np.array([[1, 1, 1], [1.0, 0.85, 0.7], [0.75, 0.85, 1.0]], np.float32)
    for x, y, m, k in zip(xs, ys, mag, tint):
        b = 0.08 + 0.9 * m ** 3
        cv2.circle(img, (int(x), int(y)), 1 if m < 0.97 else 2, (cols[k] * b).tolist(), -1, cv2.LINE_AA)
    # faint milky band
    band = gfx.fbm(H, W, 300, seed + 3, 5)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.abs((yy - H * 0.3) - (xx - W * 0.5) * 0.9) / (H * 0.18)
    img += (np.exp(-d ** 2) * band * 0.07)[..., None] * np.array([0.8, 0.8, 1.0], np.float32)
    return cv2.GaussianBlur(img, (3, 3), 0.5)


@lru_cache(maxsize=None)
def paper(kind="parchment", seed=2):
    """Full-frame paper texture, sRGB float."""
    fib = gfx.fbm(H, W, 3, seed, 3)
    cloud = gfx.fbm(H, W, 400, seed + 1, 5)
    if kind == "parchment":
        base = np.array([0.075, 0.06, 0.048], np.float32)
        img = base * (0.75 + 0.5 * cloud[..., None]) + (fib[..., None] - 0.5) * 0.012
    elif kind == "rice":
        base = np.array([0.91, 0.87, 0.78], np.float32)
        streak = cv2.resize(gfx.fbm(H // 8, W // 2, 2, seed + 4, 2), (W, H))
        img = base * (0.93 + 0.08 * cloud[..., None]) - (streak[..., None] - 0.5) * 0.05 - (fib[..., None] - 0.5) * 0.03
        img = img * (0.25 + 0.75 * gfx.vignette_mask(0.45))[..., None]
    else:  # dark ink-wash night
        base = np.array([0.03, 0.045, 0.055], np.float32)
        img = base * (0.6 + 0.8 * cloud[..., None])
    return np.clip(img, 0, 1).astype(np.float32)


# ----------------------------------------------------------------------------- particles
@lru_cache(maxsize=None)
def _dust_seed(n, seed):
    rng = np.random.default_rng(seed)
    return (rng.uniform(0, W, n), rng.uniform(0, H, n), rng.uniform(0.3, 1.0, n), rng.uniform(0, 6.28, n),
            rng.uniform(0.5, 2.5, n))


def dust(cv: Canvas, t, n=90, seed=7, rgb=(1.0, 0.85, 0.6), alpha=0.5, drift=(8, -14), size=2.2):
    xs, ys, br, ph, sz = _dust_seed(n, seed)
    for x, y, b, p, s in zip(xs, ys, br, ph, sz):
        px = (x + drift[0] * t + 18 * math.sin(t * 0.4 + p)) % W
        py = (y + drift[1] * t + 12 * math.cos(t * 0.3 + p)) % H
        a = alpha * b * (0.6 + 0.4 * math.sin(t * 1.3 + p * 3))
        cv.c.drawCircle(px, py, s * size, paint(rgb, a * 0.35, blur=s * size))
        cv.c.drawCircle(px, py, s * size * 0.45, paint(rgb, a))


def flare(cv: Canvas, x, y, strength, rgb=(1.0, 0.86, 0.62)):
    if strength <= 0.003:
        return
    c = cv.c
    c.drawCircle(x, y, 260 * strength, paint(rgb, 0.25 * strength, blur=120 * strength))
    c.drawCircle(x, y, 70 * strength, paint((1, 0.95, 0.85), 0.8 * strength, blur=30))
    c.drawRect(skia.Rect.MakeLTRB(x - 900 * strength, y - 2.5, x + 900 * strength, y + 2.5),
               paint((0.85, 0.9, 1.0), 0.55 * strength, blur=4))
    for k, (d, r, a) in enumerate([(0.35, 30, 0.12), (0.6, 60, 0.07), (0.9, 18, 0.15), (1.25, 90, 0.05)]):
        gx, gy = x + (W / 2 - x) * d * 2, y + (H / 2 - y) * d * 2
        c.drawCircle(gx, gy, r, paint((0.7, 0.8, 1.0) if k % 2 else rgb, a * strength, blur=r * 0.4))


# ----------------------------------------------------------------------------- ink calligraphy
@lru_cache(maxsize=None)
def _glyph(char, size, font_name="kai"):
    pad = int(size * 0.25)
    S = int(size * 1.5)
    cv = Canvas(S, S)
    f = gfx.font(font_name, size)
    gfx.draw_text(cv, char, S / 2, S / 2 + size * 0.36, f, (1, 1, 1))
    m = cv.arr[..., 3].astype(np.float32) / 255
    # brush texture: dry-brush streaks + soft bleed
    streak = cv2.resize(gfx.fbm(S // 6, S, 3, hash(char) % 999, 3), (S, S))
    rough = gfx.fbm(S, S, 9, hash(char) % 777 + 1, 3)
    order = np.mgrid[0:S, 0:S].astype(np.float32)
    order = (order[0] * 0.65 + order[1] * 0.35) / S  # roughly top-left to bottom-right stroke order
    return m, streak, rough, order, pad


def ink_char(char, size, prog, rgb=(0.05, 0.045, 0.05), font_name="kai", bleed=1.0):
    """Premultiplied RGBA float of a brush character being written (prog 0..1)."""
    m, streak, rough, order, pad = _glyph(char, size, font_name)
    thr = prog * 1.25 - 0.1
    reveal = np.clip((thr - (order * 0.85 + rough * 0.25)) / 0.06, 0, 1)
    a = m * reveal * (0.82 + 0.18 * streak)
    if bleed:
        halo = cv2.GaussianBlur(a, (0, 0), size * 0.025) * 0.35 * bleed
        a = np.maximum(a, halo)
    out = np.zeros(m.shape + (4,), np.float32)
    out[..., :3] = np.array(rgb, np.float32) * a[..., None]
    out[..., 3] = a
    return out


def paste(dst, rgba, x, y, alpha=1.0):
    """Composite premultiplied RGBA patch centred at (x, y) onto float RGB dst."""
    h, w = rgba.shape[:2]
    x0, y0 = int(round(x - w / 2)), int(round(y - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb:
        return dst
    patch = rgba[ya - y0:yb - y0, xa - x0:xb - x0] * alpha
    region = dst[ya:yb, xa:xb]
    dst[ya:yb, xa:xb] = region * (1 - patch[..., 3:4]) + patch[..., :3]
    return dst


def seal(cv: Canvas, x, y, size, text, a=1.0, rgb=(0.72, 0.1, 0.08)):
    """Square red seal stamp with characters in reverse (white) relief."""
    if a <= 0.003:
        return
    c = cv.c
    r = skia.Rect.MakeXYWH(x - size / 2, y - size / 2, size, size)
    c.drawRRect(skia.RRect.MakeRectXY(r, size * 0.06, size * 0.06), paint(rgb, a * 0.92))
    c.drawRRect(skia.RRect.MakeRectXY(r.makeInset(size * 0.06, size * 0.06), 3, 3),
                paint((0.98, 0.9, 0.85), a * 0.9, stroke=size * 0.03))
    n = len(text)
    f = gfx.font("serif-tc", size * (0.62 if n == 1 else 0.4), 900)
    if n == 1:
        gfx.draw_text(cv, text, x, y + size * 0.22, f, (0.98, 0.92, 0.88), a * 0.95)
    else:
        for i, ch in enumerate(text[:2]):
            gfx.draw_text(cv, ch, x, y - size * 0.05 + (i - 0.5) * size * 0.42 + size * 0.2, f,
                          (0.98, 0.92, 0.88), a * 0.95)


# ----------------------------------------------------------------------------- the white pheasant
def pheasant_path(s=1.0, ox=0.0, oy=0.0, t=0.0):
    """Side view, facing left. Returns dict of skia paths."""
    def P(x, y):
        return ox + x * s, oy + y * s
    bob = math.sin(t * 1.6) * 4
    paths = {}
    body = skia.Path()
    body.moveTo(*P(392, 300 + bob))
    body.cubicTo(*P(384, 360), *P(440, 412), *P(540, 420))       # breast to belly
    body.cubicTo(*P(630, 426), *P(700, 380), *P(735, 318))       # belly to rump
    body.cubicTo(*P(700, 292), *P(640, 272), *P(560, 268))       # back
    body.cubicTo(*P(480, 264), *P(420, 268), *P(392, 300 + bob))
    paths["body"] = body
    neck = skia.Path()
    neck.moveTo(*P(392, 312 + bob))
    neck.cubicTo(*P(370, 260 + bob), *P(330, 220 + bob), *P(306, 170 + bob))
    neck.lineTo(*P(340, 160 + bob))
    neck.cubicTo(*P(360, 210 + bob), *P(410, 250 + bob), *P(450, 270))
    neck.close()
    paths["neck"] = neck
    head = skia.Path()
    head.addOval(skia.Rect.MakeLTRB(*P(282, 132 + bob), *P(346, 184 + bob)))
    paths["head"] = head
    beak = skia.Path()
    beak.moveTo(*P(286, 150 + bob))
    beak.lineTo(*P(258, 160 + bob))
    beak.lineTo(*P(288, 166 + bob))
    beak.close()
    paths["beak"] = beak
    crest = skia.Path()
    crest.moveTo(*P(330, 138 + bob))
    crest.cubicTo(*P(350, 118 + bob), *P(372, 116 + bob), *P(386, 126 + bob))
    crest.cubicTo(*P(366, 130 + bob), *P(350, 140 + bob), *P(340, 150 + bob))
    crest.close()
    paths["crest"] = crest
    wing = skia.Path()
    wing.moveTo(*P(470, 300))
    wing.cubicTo(*P(540, 280), *P(640, 290), *P(700, 340))
    wing.cubicTo(*P(640, 380), *P(560, 392), *P(500, 380))
    wing.cubicTo(*P(470, 360), *P(460, 330), *P(470, 300))
    paths["wing"] = wing
    tail = []
    sway = math.sin(t * 0.9) * 6
    for k, (dy, ln, wd) in enumerate([(-34, 1.0, 20), (-14, 0.94, 18), (6, 0.84, 16), (-54, 0.78, 14),
                                      (22, 0.7, 13), (-70, 0.6, 12)]):
        pth = skia.Path()
        x0, y0 = 705, 318 + dy * 0.25
        x1, y1 = 705 + 470 * ln, 250 + dy * 1.2 + sway * (k + 1) * 0.5
        pth.moveTo(*P(x0, y0 - wd / 2))
        pth.cubicTo(*P(x0 + 120, y0 - 40 + dy * 0.2), *P(x1 - 120, y1 - 20), *P(x1, y1))
        pth.cubicTo(*P(x1 - 110, y1 + 4), *P(x0 + 130, y0 - 10 + dy * 0.2), *P(x0, y0 + wd / 2))
        pth.close()
        tail.append(pth)
    paths["tail"] = tail
    legs = skia.Path()
    for lx in (520, 570):
        legs.moveTo(*P(lx, 412))
        legs.lineTo(*P(lx - 10, 520))
        legs.lineTo(*P(lx - 34, 528))
        legs.moveTo(*P(lx - 10, 520))
        legs.lineTo(*P(lx + 14, 530))
    paths["legs"] = legs
    eye = (P(312, 152 + bob))
    paths["eye"] = eye
    return paths


def draw_pheasant(cv: Canvas, cx, cy, scale, t, a=1.0, glow=1.0):
    if a <= 0.003:
        return
    s = scale
    ox, oy = cx - 680 * s, cy - 320 * s
    P = pheasant_path(s, ox, oy, t)
    c = cv.c
    white = (0.97, 0.96, 0.93)
    shade = (0.74, 0.76, 0.82)
    if glow:
        for key in ("body", "neck", "head"):
            c.drawPath(P[key], paint((0.85, 0.9, 1.0), a * 0.35 * glow, blur=40 * s))
    for tp in P["tail"]:
        c.drawPath(tp, paint(shade, a))
        c.drawPath(tp, paint(white, a * 0.85))
    for tp in P["tail"]:
        c.drawPath(tp, paint((0.6, 0.62, 0.68), a * 0.5, stroke=1.6 * s))
    c.drawPath(P["legs"], paint((0.62, 0.55, 0.5), a, stroke=7 * s))
    c.drawPath(P["neck"], paint(white, a))
    body_shader = skia.GradientShader.MakeLinear(
        [skia.Point(ox, oy + 270 * s), skia.Point(ox, oy + 430 * s)],
        [skia.Color4f(*white, a).toColor(), skia.Color4f(*shade, a).toColor()])
    bp = paint(white, a)
    bp.setShader(body_shader)
    c.drawPath(P["body"], bp)
    c.drawPath(P["head"], paint(white, a))
    c.drawPath(P["crest"], paint(white, a))
    c.drawPath(P["wing"], paint((0.88, 0.88, 0.88), a))
    rng = np.random.default_rng(5)
    for k in range(40):  # scalloped body feathers
        fxk = ox + rng.uniform(430, 700) * s
        fyk = oy + rng.uniform(290, 400) * s
        arc = skia.Path()
        arc.addArc(skia.Rect.MakeXYWH(fxk - 14 * s, fyk - 8 * s, 28 * s, 18 * s), 20, 140)
        c.drawPath(arc, paint((0.7, 0.72, 0.78), a * 0.35, stroke=1.6 * s))
    for k in range(5):  # wing feather lines
        pth = skia.Path()
        pth.moveTo(ox + (520 + k * 30) * s, oy + (300 + k * 4) * s)
        pth.quadTo(ox + (600 + k * 20) * s, oy + (350 + k * 6) * s, ox + (690 - k * 6) * s, oy + (345 + k * 3) * s)
        c.drawPath(pth, paint((0.62, 0.64, 0.7), a * 0.6, stroke=2.2 * s))
    c.drawPath(P["beak"], paint((0.85, 0.76, 0.55), a))
    ex, ey = P["eye"]
    c.drawOval(skia.Rect.MakeXYWH(ex - 16 * s, ey - 12 * s, 30 * s, 26 * s), paint((0.8, 0.12, 0.1), a * 0.9))  # wattle
    c.drawCircle(ex, ey, 4.5 * s, paint((0.05, 0.03, 0.03), a))


# ----------------------------------------------------------------------------- lamps, ships, misc
def oil_lamp(cv: Canvas, x, y, scale, flame, t, seed=0):
    """Roman terracotta oil lamp silhouette with a living flame (flame 0..1)."""
    c = cv.c
    s = scale
    body = skia.Path()
    body.moveTo(x - 120 * s, y)
    body.cubicTo(x - 130 * s, y - 60 * s, x + 40 * s, y - 70 * s, x + 80 * s, y - 34 * s)
    body.lineTo(x + 150 * s, y - 30 * s)
    body.cubicTo(x + 170 * s, y - 28 * s, x + 170 * s, y + 2 * s, x + 150 * s, y + 4 * s)
    body.lineTo(x + 70 * s, y + 10 * s)
    body.cubicTo(x + 20 * s, y + 40 * s, x - 100 * s, y + 40 * s, x - 120 * s, y)
    body.close()
    sh = skia.GradientShader.MakeLinear([skia.Point(x, y - 70 * s), skia.Point(x, y + 40 * s)],
                                        [skia.Color4f(0.55, 0.32, 0.2, 1).toColor(),
                                         skia.Color4f(0.18, 0.09, 0.06, 1).toColor()])
    p = paint((1, 1, 1))
    p.setShader(sh)
    c.drawPath(body, p)
    c.drawOval(skia.Rect.MakeXYWH(x - 60 * s, y - 52 * s, 80 * s, 26 * s), paint((0.12, 0.06, 0.04), 0.9))
    c.drawPath(body, paint((1.0, 0.7, 0.4), 0.25 * flame, stroke=2 * s))
    fx, fy = x + 152 * s, y - 34 * s
    if flame > 0.01:
        fl = flame * (0.85 + 0.15 * math.sin(t * 13 + seed) * math.sin(t * 7.3 + seed * 2))
        c.drawCircle(fx, fy - 40 * s, 170 * s * fl, paint((1.0, 0.6, 0.25), 0.22 * fl, blur=90 * s))
        f = skia.Path()
        hgt = 95 * s * fl
        sway = math.sin(t * 3.1 + seed) * 6 * s
        f.moveTo(fx - 16 * s, fy)
        f.cubicTo(fx - 22 * s, fy - hgt * 0.4, fx + sway, fy - hgt * 0.8, fx + sway * 1.5, fy - hgt)
        f.cubicTo(fx + sway + 10 * s, fy - hgt * 0.7, fx + 22 * s, fy - hgt * 0.3, fx + 16 * s, fy)
        f.close()
        c.drawPath(f, paint((1.0, 0.55, 0.15), 0.9 * fl, blur=6 * s))
        c.drawPath(f, paint((1.0, 0.85, 0.5), 0.9 * fl, blur=2 * s))
    return fx, fy


def smoke(cv: Canvas, x, y, t, a, seed=0):
    if a <= 0.003:
        return
    rng = np.random.default_rng(seed)
    for k in range(14):
        ph = rng.uniform(0, 6.28)
        rise = (t * 60 + k * 22) % 300
        px = x + math.sin(rise * 0.03 + ph) * (10 + rise * 0.15)
        py = y - rise
        r = 10 + rise * 0.12
        c_a = a * (1 - rise / 300) * 0.25
        cv.c.drawCircle(px, py, r, paint((0.7, 0.7, 0.72), c_a, blur=r * 0.8))


def ship(cv: Canvas, x, y, size, a=1.0, rgb=gfx.PALE_GOLD, heading=1):
    """Tiny merchant ship glyph (hull + square sail)."""
    if a <= 0.003:
        return
    c = cv.c
    s = size
    hull = skia.Path()
    hull.moveTo(x - s * heading, y)
    hull.lineTo(x + s * heading, y)
    hull.lineTo(x + s * 0.7 * heading, y + s * 0.35)
    hull.lineTo(x - s * 0.8 * heading, y + s * 0.35)
    hull.close()
    c.drawPath(hull, paint(rgb, a))
    c.drawLine(x, y, x, y - s * 1.2, paint(rgb, a, stroke=max(1.0, s * 0.08)))
    c.drawRect(skia.Rect.MakeLTRB(x - s * 0.55, y - s * 1.1, x + s * 0.55, y - s * 0.35), paint(rgb, a * 0.85))
