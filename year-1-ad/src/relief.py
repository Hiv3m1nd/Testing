"""Height-field relief rendering: struck silver coins and carved marble.

Shapes are drawn as 2D masks with skia, turned into height fields by multi-scale
blurring (rounded relief) or distance transforms (V-cut letters), then lit with
a moving light. This gives real specular highlights and shadows that respond to
the camera move, instead of a flat picture of a coin.
"""
from __future__ import annotations

import math
from functools import lru_cache

import cv2
import numpy as np
import skia

import gfx
from gfx import Canvas, paint


def normals(h, strength=1.0):
    gx = cv2.Sobel(h, cv2.CV_32F, 1, 0, ksize=3) / 8.0 * strength
    gy = cv2.Sobel(h, cv2.CV_32F, 0, 1, ksize=3) / 8.0 * strength
    n = np.dstack([-gx, -gy, np.ones_like(h)])
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def light(n, az_deg, el_deg):
    a, e = math.radians(az_deg), math.radians(el_deg)
    L = np.array([math.cos(a) * math.cos(e), -math.sin(a) * math.cos(e), math.sin(e)], np.float32)
    ndl = np.clip(n @ L, 0, 1)
    R = 2 * n[..., 2:3] * n - np.array([0, 0, 1], np.float32)  # reflection of view vector (0,0,1)
    spec = np.clip(R @ L, 0, 1)
    return ndl, spec


def mask_from(draw_fn, size):
    cv = Canvas(size, size)
    draw_fn(cv)
    return cv.arr[..., 3].astype(np.float32) / 255.0


def blur(m, s):
    k = int(s * 3) * 2 + 1
    return cv2.GaussianBlur(m, (k, k), s)


def text_on_circle(cv: Canvas, s, cx, cy, r, f, start_deg, span_deg, rgb=(1, 1, 1), inward=False):
    """Draw letters along an arc (clockwise from start_deg, 0 = up)."""
    glyphs = f.textToGlyphs(s)
    widths = list(f.getWidths(glyphs))
    total = sum(widths)
    gap = (math.radians(span_deg) * r - total) / max(1, len(s) - 1)
    ang = math.radians(start_deg)
    for ch, wdt in zip(s, widths):
        mid = ang + (wdt / 2) / r
        x = cx + r * math.sin(mid)
        y = cy - r * math.cos(mid)
        cv.c.save()
        cv.c.translate(x, y)
        cv.c.rotate(math.degrees(mid) + (180 if inward else 0))
        gfx.draw_text(cv, ch, 0, f.getSize() * 0.35, f, rgb, 1.0, align="center")
        cv.c.restore()
        ang += (wdt + gap) / r


# ----------------------------------------------------------------------------- coins
SIZE = 1000


def _coin_blank(seed):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    ang = np.arctan2(yy - SIZE / 2, xx - SIZE / 2)
    rad = np.hypot(yy - SIZE / 2, xx - SIZE / 2)
    wob = 0.0
    for k, amp in [(2, 9), (3, 7), (5, 4), (9, 2)]:
        wob = wob + amp * np.sin(k * ang + rng.uniform(0, 6.28))
    R = SIZE * 0.46 + wob
    disc = np.clip((R - rad) / 2.0, 0, 1)
    return disc, rad, R


def _beaded_border(cv, r, n=90, dot=7):
    for i in range(n):
        a = 2 * math.pi * i / n
        cv.c.drawCircle(SIZE / 2 + r * math.cos(a), SIZE / 2 + r * math.sin(a), dot, paint((1, 1, 1)))


def _finish_coin(relief_fine, relief_soft, seed, wear=0.35):
    disc, rad, R = _coin_blank(seed)
    h = 0.45 * blur(relief_soft, 7) + 0.4 * blur(relief_soft, 2.5) + 0.25 * blur(relief_fine, 1.4)
    rim = np.clip((rad - (R - 26)) / 10, 0, 1) * disc * 0.35
    edge_drop = np.clip((R - rad) / 30, 0, 1)
    noise = gfx.fbm(SIZE, SIZE, 140, seed, 5)
    pits = gfx.fbm(SIZE, SIZE, 12, seed + 5, 2)
    h = (h * (1 - wear * noise) + rim) * edge_drop * disc + (pits - 0.5) * 0.0025 * disc + (noise - 0.5) * 0.03 * disc
    # toning: dark patina in recesses, bright on worn high points
    cavity = np.clip(blur(h, 6) - h, 0, None) * 18
    return h.astype(np.float32), disc.astype(np.float32), np.clip(cavity, 0, 1).astype(np.float32)


def _draw_figure(c, cx, base_y, s, mirror=1, layer="soft"):
    """Standing togate prince, round shield at his outer side, spear behind it
    (Gaius/Lucius denarius type, RIC I 207)."""
    p = paint((1, 1, 1))
    sx = cx - mirror * 62 * s  # shield centre x (outer side)
    if layer == "soft":
        c.drawCircle(cx, base_y - 318 * s, 30 * s, p)                       # head
        c.drawRect(skia.Rect.MakeLTRB(cx - 12 * s, base_y - 292 * s, cx + 12 * s, base_y - 270 * s), p)
        body = skia.Path()
        body.moveTo(cx - 56 * s, base_y - 268 * s)                          # shoulders
        body.cubicTo(cx - 70 * s, base_y - 200 * s, cx - 52 * s, base_y - 110 * s, cx - 46 * s, base_y - 10 * s)
        body.lineTo(cx - 40 * s, base_y)
        body.lineTo(cx + 40 * s, base_y)
        body.lineTo(cx + 46 * s, base_y - 10 * s)
        body.cubicTo(cx + 52 * s, base_y - 110 * s, cx + 70 * s, base_y - 200 * s, cx + 56 * s, base_y - 268 * s)
        body.cubicTo(cx + 30 * s, base_y - 282 * s, cx - 30 * s, base_y - 282 * s, cx - 56 * s, base_y - 268 * s)
        c.drawPath(body, p)
        c.drawCircle(sx, base_y - 92 * s, 64 * s, p)                       # shield
    else:
        st = paint((1, 1, 1), 1, stroke=6 * s)
        c.drawLine(sx - mirror * 20 * s, base_y + 6 * s, sx - mirror * 20 * s, base_y - 400 * s,
                   paint((1, 1, 1), 1, stroke=8 * s))                       # spear shaft
        tip = skia.Path()
        tx = sx - mirror * 20 * s
        tip.moveTo(tx, base_y - 440 * s)
        tip.lineTo(tx - 12 * s, base_y - 392 * s)
        tip.lineTo(tx + 12 * s, base_y - 392 * s)
        tip.close()
        c.drawPath(tip, p)
        c.drawCircle(sx, base_y - 92 * s, 64 * s, st)                      # shield rim
        c.drawCircle(sx, base_y - 92 * s, 16 * s, p)                       # boss
        for k in (-1, 1):                                                   # toga folds
            f = skia.Path()
            f.moveTo(cx + k * 40 * s, base_y - 262 * s)
            f.cubicTo(cx - k * 6 * s, base_y - 200 * s, cx + k * 18 * s, base_y - 120 * s, cx + k * 4 * s, base_y - 14 * s)
            c.drawPath(f, st)
        sash = skia.Path()
        sash.moveTo(cx - 50 * s, base_y - 250 * s)
        sash.cubicTo(cx - 10 * s, base_y - 200 * s, cx + 20 * s, base_y - 180 * s, cx + 48 * s, base_y - 150 * s)
        c.drawPath(sash, st)


@lru_cache(maxsize=None)
def coin_gaius_lucius():
    f_leg = gfx.font("cinzel", 62, 700)
    f_ex = gfx.font("cinzel", 74, 700)

    def soft(cv):
        _draw_figure(cv.c, SIZE * 0.40, SIZE * 0.745, 1.0, mirror=1)
        _draw_figure(cv.c, SIZE * 0.60, SIZE * 0.745, 1.0, mirror=-1)
        # simpulum (ladle) and lituus (augur's staff) between them
        c = cv.c
        c.drawLine(SIZE * 0.465, SIZE * 0.30, SIZE * 0.465, SIZE * 0.37, paint((1, 1, 1), 1, stroke=7))
        c.drawCircle(SIZE * 0.465, SIZE * 0.385, 14, paint((1, 1, 1)))
        lit = skia.Path()
        lit.moveTo(SIZE * 0.535, SIZE * 0.40)
        lit.lineTo(SIZE * 0.535, SIZE * 0.32)
        lit.cubicTo(SIZE * 0.535, SIZE * 0.28, SIZE * 0.575, SIZE * 0.28, SIZE * 0.57, SIZE * 0.315)
        c.drawPath(lit, paint((1, 1, 1), 1, stroke=8))
        c.drawLine(SIZE * 0.22, SIZE * 0.755, SIZE * 0.78, SIZE * 0.755, paint((1, 1, 1), 1, stroke=6))

    def fine(cv):
        _draw_figure(cv.c, SIZE * 0.40, SIZE * 0.745, 1.0, mirror=1, layer="fine")
        _draw_figure(cv.c, SIZE * 0.60, SIZE * 0.745, 1.0, mirror=-1, layer="fine")
        _beaded_border(cv, SIZE * 0.43, 96, 7)
        text_on_circle(cv, "AVGVSTI·F·COS·DESIG·PRINC·IVVENT", SIZE / 2, SIZE / 2, SIZE * 0.37, f_leg, -128, 256)
        gfx.draw_text(cv, "C·L·CAESARES", SIZE / 2, SIZE * 0.84, f_ex, (1, 1, 1), tracking=0.04)

    return _finish_coin(mask_from(fine, SIZE), mask_from(soft, SIZE), seed=11)


def _musa_profile(c, s=1.0, ox=0.0, oy=0.0):
    """Bust of Musa facing left with a tall tiered tiara (after her drachms)."""
    def P(x, y):
        return ox + x * s, oy + y * s
    p = paint((1, 1, 1))
    face = skia.Path()
    face.moveTo(*P(452, 318))
    face.cubicTo(*P(430, 345), *P(418, 372), *P(414, 398))     # forehead
    face.cubicTo(*P(410, 412), *P(400, 418), *P(392, 430))     # brow
    face.cubicTo(*P(380, 452), *P(366, 474), *P(352, 492))     # nose ridge
    face.cubicTo(*P(350, 500), *P(362, 506), *P(382, 506))     # nose tip / underside
    face.cubicTo(*P(384, 516), *P(374, 524), *P(372, 532))     # upper lip
    face.cubicTo(*P(380, 538), *P(380, 542), *P(374, 548))     # mouth
    face.cubicTo(*P(380, 560), *P(386, 566), *P(384, 578))     # lower lip
    face.cubicTo(*P(384, 600), *P(396, 618), *P(420, 626))     # chin
    face.cubicTo(*P(446, 634), *P(466, 640), *P(478, 650))     # jaw/throat
    face.cubicTo(*P(486, 690), *P(486, 740), *P(468, 790))     # neck front
    face.cubicTo(*P(430, 820), *P(380, 850), *P(360, 900))     # chest
    face.lineTo(*P(720, 900))
    face.cubicTo(*P(700, 840), *P(680, 790), *P(668, 740))     # back
    face.cubicTo(*P(700, 700), *P(740, 650), *P(730, 590))     # hair bun
    face.cubicTo(*P(724, 540), *P(706, 470), *P(690, 420))     # back of head
    face.lineTo(*P(676, 330))
    face.close()
    c.drawPath(face, p)
    # tall tiara: tapered crown
    t = skia.Path()
    t.moveTo(*P(440, 330))
    t.lineTo(*P(468, 150))
    t.cubicTo(*P(530, 128), *P(610, 128), *P(660, 150))
    t.lineTo(*P(690, 340))
    t.close()
    c.drawPath(t, p)


def _musa_fine(c, s=1.0, ox=0.0, oy=0.0):
    def P(x, y):
        return ox + x * s, oy + y * s
    p = paint((1, 1, 1))
    for row, y in enumerate([300, 255, 210, 170]):
        x0 = 455 + (330 - y) * 0.12
        x1 = 680 - (330 - y) * 0.1
        n = 7 - row
        for k in range(n):
            c.drawCircle(*P(x0 + (x1 - x0) * (k + 0.5) / n, y), 9 * s, p)
    c.drawLine(*P(455, 330), *P(688, 330), paint((1, 1, 1), 1, stroke=10 * s))
    # eye, ear-ring, necklace
    eye = skia.Path()
    eye.moveTo(*P(404, 446))
    eye.cubicTo(*P(414, 438), *P(426, 438), *P(432, 446))
    eye.cubicTo(*P(424, 452), *P(412, 452), *P(404, 446))
    c.drawPath(eye, paint((1, 1, 1), 1, stroke=5 * s))
    c.drawCircle(*P(560, 560), 12 * s, p)
    for k in range(9):
        a = math.radians(200 + k * 14)
        c.drawCircle(*P(560 + 150 * math.cos(a) * 0.9 + 40, 790 + 40 * math.sin(a)), 8 * s, p)
    for k in range(5):  # hair strands
        pth = skia.Path()
        pth.moveTo(*P(600 + k * 18, 360))
        pth.cubicTo(*P(620 + k * 18, 450), *P(640 + k * 14, 520), *P(660 + k * 10, 600))
        c.drawPath(pth, paint((1, 1, 1), 1, stroke=6 * s))


@lru_cache(maxsize=None)
def coin_musa():
    f_leg = gfx.font("serif-tc", 64, 700)  # Noto Serif TC carries Greek capitals

    def soft(cv):
        _musa_profile(cv.c, 0.62, 175, 150)

    def fine(cv):
        _musa_fine(cv.c, 0.62, 175, 150)
        _beaded_border(cv, SIZE * 0.43, 80, 8)
        text_on_circle(cv, "ΘΕΑΣ ΟΥΡΑΝΙΑΣ", SIZE / 2, SIZE / 2, SIZE * 0.375, f_leg, -150, 120)
        text_on_circle(cv, "ΜΟΥΣΗΣ ΒΑΣΙΛΙΣΣΗΣ", SIZE / 2, SIZE / 2, SIZE * 0.375, f_leg, 30, 140)

    return _finish_coin(mask_from(fine, SIZE), mask_from(soft, SIZE), seed=23, wear=0.45)


def render_coin(coin, size_px, az=135.0, el=38.0, yaw=0.0, metal=(0.80, 0.77, 0.71), toning=(0.24, 0.19, 0.15),
                relief_strength=520.0):
    """Light a coin height field and return premultiplied RGBA float (size_px square)."""
    h, disc, cavity = coin
    n = normals(h, relief_strength)
    ndl, spec = light(n, az, el)
    _, spec2 = light(n, az + 160, 18)
    base = np.array(metal, np.float32)
    tone = np.array(toning, np.float32)
    col = base * (1 - cavity[..., None] * 0.75) + tone * cavity[..., None] * 0.75
    rgb = col * (0.22 + 0.95 * ndl[..., None]) + (spec ** 28 * 0.9 + spec2 ** 12 * 0.15)[..., None]
    # faint environment gradient so flat fields read as metal, not paint
    env = 0.08 * (n[..., 1:2] * -0.5 + 0.5)
    rgb = rgb + env
    rgba = np.dstack([np.clip(rgb, 0, 1.4) * disc[..., None], disc])
    if yaw:
        # rotate about the vertical axis with perspective
        s = SIZE
        cy = math.cos(math.radians(yaw))
        sy = math.sin(math.radians(yaw))
        f = 2.6 * s
        pts = []
        for x, y in [(-s / 2, -s / 2), (s / 2, -s / 2), (s / 2, s / 2), (-s / 2, s / 2)]:
            X, Z = x * cy, x * sy
            k = f / (f + Z)
            pts.append([s / 2 + X * k, s / 2 + y * k])
        M = cv2.getPerspectiveTransform(np.float32([[0, 0], [s, 0], [s, s], [0, s]]), np.float32(pts))
        rgba = cv2.warpPerspective(rgba, M, (s, s), flags=cv2.INTER_LINEAR)
        # coin edge (thickness) as a darker band offset in the direction of rotation
        edge_w = int(abs(sy) * 26)
        if edge_w > 0:
            a = rgba[..., 3]
            shifted = np.roll(a, edge_w if yaw > 0 else -edge_w, axis=1)
            band = np.clip(shifted - a, 0, 1)
            rgba[..., :3] += band[..., None] * np.array([0.42, 0.40, 0.37], np.float32)
            rgba[..., 3] = np.maximum(a, shifted)
    return cv2.resize(rgba, (size_px, size_px), interpolation=cv2.INTER_AREA)


# ----------------------------------------------------------------------------- carved stone
@lru_cache(maxsize=None)
def marble(w, h, seed=5):
    n1 = gfx.fbm(h, w, 420, seed, 6)
    n2 = gfx.fbm(h, w, 90, seed + 1, 4)
    n3 = gfx.fbm(h, w, 260, seed + 7, 6)
    veins = np.clip(1 - np.abs(n3 - 0.5) * 28, 0, 1) ** 2 * 0.22 + np.clip(1 - np.abs(n1 - 0.47) * 40, 0, 1) * 0.12
    base = np.array([0.93, 0.9, 0.84], np.float32)
    col = base[None, None, :] * (0.92 + 0.1 * n2[..., None]) - veins[..., None] * np.array([0.32, 0.31, 0.3])
    rough = (gfx.fbm(h, w, 6, seed + 2, 2) - 0.5) * 0.006 + (n2 - 0.5) * 0.01
    return np.clip(col, 0, 1).astype(np.float32), rough.astype(np.float32)


def carve(text_lines, w, h, f, line_gap, y0, tracking=0.08):
    """Per-line carved letter height fields (V-cut) for an inscription."""
    out = []
    y = y0
    for line in text_lines:
        cv = Canvas(w, h)
        gfx.draw_text(cv, line, w / 2, y, f, (1, 1, 1), tracking=tracking)
        m = (cv.arr[..., 3] > 127).astype(np.uint8)
        d = cv2.distanceTransform(m, cv2.DIST_L2, 5).astype(np.float32)
        depth = np.clip(d / 7.0, 0, 1) * (cv.arr[..., 3].astype(np.float32) / 255)
        out.append(depth)
        y += line_gap
    return out
