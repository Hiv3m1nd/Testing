"""Shots 1-5: cold open, the calendar, Roman consular dating, Yuanshi, two empires."""
from __future__ import annotations

import math
from functools import lru_cache

import cv2
import numpy as np
import skia

import fx
import geo
import gfx
import relief
from geo import CITIES
from gfx import (GOLD, HAN, IVORY, PALE_GOLD, PARTHIA, ROME, Canvas, H, W, draw_text, draw_text_reveal, ease_io,
                 ease_out, fade_io, font, lerp, paint, seg, smooth)
from globe import Camera, ll2v, project, render
from timeline import TL

INK_DARK = (0.12, 0.1, 0.09)


# ----------------------------------------------------------------------------- shared globe helpers
@lru_cache(maxsize=1)
def fires():
    """Scattered night fires in populated regions (artistic, weighted by rough population)."""
    rng = np.random.default_rng(12)
    clusters = [  # lat, lon, spread_lat, spread_lon, count
        (42, 13, 3, 5, 50), (38, 23, 2, 3, 25), (31, 31, 2.5, 1.0, 40), (36, 36, 2, 2, 30), (33, 44, 2, 2.5, 35),
        (37, 10, 2, 4, 20), (40, 30, 2, 5, 25), (46, 4, 3, 4, 30), (40, -4, 3, 4, 20), (33, 52, 3, 6, 25),
        (26, 82, 3, 6, 70), (25, 72, 4, 4, 35), (14, 78, 4, 3, 35), (35, 111, 2, 5, 80), (31, 116, 3, 4, 50),
        (29, 106, 2, 3, 25), (23, 112, 2, 3, 15), (17, 34, 1.5, 1.5, 12), (19.5, -99, 1, 1, 8), (17.5, -90, 1.5, 1.5, 10),
    ]
    pts = []
    for la, lo, sla, slo, n in clusters:
        for _ in range(n):
            pts.append((la + rng.normal(0, sla), lo + rng.normal(0, slo), rng.uniform(0.2, 1.0)))
    big = [(CITIES[c], w) for c, w in [("Rome", 1.0), ("Alexandria", 0.85), ("Antioch", 0.6), ("Seleucia", 0.6),
                                        ("Carthage", 0.5), ("Athens", 0.4), ("Chang'an", 0.85), ("Luoyang", 0.75),
                                        ("Pataliputra", 0.6), ("Meroë", 0.35), ("Teotihuacan", 0.4)]]
    return np.array(pts), big


def night_lights(cv: Canvas, cam: Camera, sun, a=1.0, t=0.0):
    if a <= 0.003:
        return
    pts, big = fires()
    S = ll2v(*sun)
    x, y, vis = project(cam, pts[:, 0], pts[:, 1])
    dark = ll2v(pts[:, 0], pts[:, 1]) @ S < -0.02
    for xi, yi, v, d, b in zip(x, y, vis, dark, pts[:, 2]):
        if v and d and 0 <= xi < W and 0 <= yi < H:
            fl = 0.75 + 0.25 * math.sin(t * 2.3 + xi * 0.1)
            cv.c.drawCircle(float(xi), float(yi), 1.6, paint((1.0, 0.7, 0.35), a * b * 0.8 * fl))
    for (la, lo), w in big:
        bx, by, bv = project(cam, [la], [lo])
        if bv[0] and float(ll2v(la, lo) @ S) < 0.02:
            cv.c.drawCircle(float(bx[0]), float(by[0]), 14 * w, paint((1.0, 0.62, 0.3), a * 0.55 * w, blur=10 * w))
            cv.c.drawCircle(float(bx[0]), float(by[0]), 2.6 * w + 1, paint((1.0, 0.85, 0.6), a))


def globe_shot(cam, sun, stars=1.0, **kw):
    rgb, cov, lat, lon, hit = render(cam, sun=sun, **kw)
    if stars:
        rgb = rgb + fx.starfield() * (1 - cov[..., None]) * stars
    return rgb, cov


def screen_radius(cam: Camera):
    C, F, R, U, f = cam.basis()
    d = float(np.linalg.norm(C))
    return f * math.tan(math.asin(1 / d)), C, F, R, U, f


def sun_behind(cam: Camera, up, side=0.0):
    """Sun direction placed behind the globe, peeking over its upper limb (as lat, lon)."""
    C, F, R, U, f = cam.basis()
    S = F + U * up + R * side
    S = S / np.linalg.norm(S)
    return float(np.degrees(np.arcsin(S[2]))), float(np.degrees(np.arctan2(S[1], S[0])))


def sun_flare_pos(cam: Camera, sun):
    """Point on the limb nearest the (hidden) sun."""
    r, C, F, R, U, f = screen_radius(cam)
    c0 = -C
    z = c0 @ F
    cx = W / 2 + (c0 @ R) / z * f
    cy = H / 2 + cam.shift_y * H - (c0 @ U) / z * f
    S = ll2v(*sun)
    dx, dy = S @ R, -(S @ U)
    n = math.hypot(dx, dy) + 1e-9
    return cx + dx / n * r * 0.995, cy + dy / n * r * 0.995


# ----------------------------------------------------------------------------- 1. cold open
def s_open(t):
    T = TL()
    p = seg(t, 0, 5.5)
    cam = Camera(lat=24, lon=lerp(28, 40, p), dist=lerp(3.9, 3.2, ease_io(p)), fov=34, shift_y=0.1)
    rise = smooth(seg(t, 0.4, 5.0))
    sun = sun_behind(cam, lerp(0.18, 0.42, rise), side=lerp(0.25, 0.1, rise))
    img, cov = globe_shot(cam, sun, glint=0.3)
    img = img * smooth(seg(t, 0.0, 1.4))
    cv = Canvas.from_float(np.clip(img, 0, 1))
    night_lights(cv, cam, sun, a=smooth(seg(t, 0.8, 2.0)), t=t)
    fxp = sun_flare_pos(cam, sun)
    fx.flare(cv, fxp[0], fxp[1], smooth(seg(t, 1.2, 3.6)) * 0.8)
    # titles
    tag = fade_io(t, 0.5, 6.0, 0.8, 0.6)
    draw_text(cv, "YEAR BY YEAR", W / 2, 200, font("cinzel", 34, 600), PALE_GOLD, tag * 0.85, tracking=0.5)
    w1 = T.w(0, "1")
    w2 = T.w(0, "1", nth=1)
    f = font("cinzel", 230, 600)
    a_one = smooth(seg(t, w1 - 0.15, w1 + 0.5))
    a_ad = a_one * (1 - smooth(seg(t, w2 + 0.4, w2 + 1.2)))
    wid_one = gfx.text_width("1", f)
    wid_ad = gfx.text_width("AD", f, 0.06)
    gap = 95
    x0 = W / 2 - (wid_one + gap + wid_ad) / 2
    shift = smooth(seg(t, w2 + 0.6, w2 + 1.6)) * (wid_ad + gap) / 2
    y = 430
    draw_text(cv, "1", x0 + wid_one / 2 + shift, y + (1 - a_one) * 30, f, PALE_GOLD, a_one, align="center", glow=26,
              glow_rgb=GOLD)
    draw_text(cv, "AD", x0 + wid_one + gap, y + (1 - a_one) * 30, f, PALE_GOLD, a_ad, tracking=0.06, align="left",
              glow=26, glow_rgb=GOLD)
    return cv.to_float()


# ----------------------------------------------------------------------------- 2. the calendar
def _ypos_ad(n):
    return n - 0.5


def _ypos_bc(n):
    return -(n - 0.5)


def _label_for(p):
    k = round(p + 0.5) if p > 0 else round(-p + 0.5)
    return (f"{k} AD" if p > 0 else f"{k} BC"), k


def _cal_camera(t):
    T = TL()
    kf = [
        (T.s(1) - 0.6, 0.5, 70.0),
        (T.w(1, "five"), 0.5, 70.0),
        ((T.w(1, "five") + T.w(1, "later", end=True)) / 2, 262.0, 1.9),
        (T.w(1, "later", end=True) + 0.3, 524.5, 10.0),
        (T.s(2), 524.5, 10.0),
        ((T.s(2) + T.w(2, "Jesus", end=True)) / 2, 262.0, 1.9),
        (T.w(2, "Jesus", end=True) + 0.2, 0.5, 70.0),
        (T.s(3) + 0.4, 0.5, 70.0),
        (T.s(3) + 1.8, -2.8, 105.0),
        (T.s(4), -2.8, 105.0),
        (T.s(4) + 0.9, 0.0, 215.0),
        (99.0, 0.0, 215.0),
    ]
    for (t0, c0, s0), (t1, c1, s1) in zip(kf[:-1], kf[1:]):
        if t <= t1:
            u = ease_io(seg(t, t0, t1))
            return c0 + (c1 - c0) * u, math.exp(math.log(s0) + (math.log(s1) - math.log(s0)) * u)
    return kf[-1][1], kf[-1][2]


def s_calendar(t):
    T = TL()
    img = fx.paper("parchment").copy()
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    img += np.exp(-((yy - 0.45) / 0.35) ** 2) * np.array([0.05, 0.035, 0.02], np.float32)
    cv = Canvas.from_float(np.clip(img, 0, 1))
    c = cv.c
    fx.dust(cv, t, n=60, alpha=0.35)
    center, scale = _cal_camera(t)
    X = 250.0
    Y0 = H * 0.46

    def sy(p):
        return Y0 - (p - center) * scale

    draw_text(cv, "THE CALENDAR", W / 2, 210, font("cinzel", 34, 600), GOLD, 0.75, tracking=0.5)
    # spine
    c.drawLine(X, 0, X, H, paint(GOLD, 0.25, stroke=3))
    c.drawLine(X, 0, X, H, paint(GOLD, 0.5, stroke=1.2))
    lo, hi = center - (H * 0.6) / scale, center + (H * 0.6) / scale
    steps = [1, 5, 10, 25, 50, 100, 200]
    lab_step = next(st for st in steps if st * scale >= 72)
    tick_step = next(st for st in steps if st * scale >= 14)
    marks = []
    for n in range(1, 800):
        if n == 1 or n % tick_step == 0:
            marks.append((_ypos_ad(n), n == 1 or n % lab_step == 0))
    for n in range(1, 400):
        if n == 1 or n % tick_step == 0:
            marks.append((_ypos_bc(n), n == 1 or n % lab_step == 0))
    if lab_step > 1:  # avoid "1 AD"/"1 BC" crowding the first round-number labels
        marks = [(p, mj and not (abs(p) < 1 and lab_step * scale < 140)) if abs(p) < 1 else (p, mj)
                 for p, mj in marks]
    fl = font("cinzel", 44, 600)
    for p, major in marks:
        if not (lo < p < hi):
            continue
        y = sy(p)
        L = 34 if major else 14
        c.drawLine(X - L / 2, y, X + L / 2, y, paint(PALE_GOLD, 0.8 if major else 0.4, stroke=2.5 if major else 1.5))
        if major:
            lab, k = _label_for(p)
            fade_edge = smooth(seg(y, 260, 380)) * (1 - smooth(seg(y, H - 300, H - 120)))
            if a525_hide := fade_io(t, TL().w(1, "later") - 0.2, TL().s(2) + 1.2, 0.4, 0.5):
                if abs(p - 524.5) < 90:
                    fade_edge *= 1 - a525_hide
            draw_text(cv, lab, X + 46, y + 15, fl, IVORY, 0.85 * fade_edge, tracking=0.08, align="left")

    # AD 525: Dionysius Exiguus
    a525 = fade_io(t, T.w(1, "later") + 0.2, T.s(2) + 0.55, 0.6, 0.4)
    if a525 > 0:
        y = sy(524.5)
        c.drawCircle(X, y, 22, paint(GOLD, a525 * 0.5, blur=14))
        c.drawCircle(X, y, 9, paint(PALE_GOLD, a525))
        draw_text(cv, "525 AD", X + 46, y - 90, font("cinzel", 74, 700), GOLD, a525, tracking=0.06, align="left",
                  glow=14)
        an = a525 * smooth(seg(t, T.w(1, "Dionysius") - 0.2, T.w(1, "Dionysius") + 0.6))
        draw_text_reveal(cv, "DIONYSIUS EXIGUUS", X + 46, y + 62, font("cinzel", 46, 600), an, IVORY,
                         tracking=0.06, align="left")
        draw_text(cv, "a monk in Rome, building Easter tables", X + 46, y + 120, font("garamond-italic", 40, 500),
                  PALE_GOLD, an * 0.9, align="left")
        draw_text(cv, "ANNI DOMINI NOSTRI IESV CHRISTI", X + 46, y + 205, font("garamond", 34, 600), IVORY,
                  an * 0.8, tracking=0.12, align="left")
        draw_text(cv, "‘the years of our Lord Jesus Christ’", X + 46, y + 250,
                  font("garamond-italic", 34, 500), IVORY, an * 0.65, align="left")

    # AD 1: his starting point
    y1 = sy(0.5)
    a1 = smooth(seg(t, T.w(2, "birth") - 0.2, T.w(2, "birth") + 0.5)) * (1 - smooth(seg(t, T.s(4) - 0.3, T.s(4) + 0.3)))
    if a1 > 0:
        c.drawCircle(X, y1, 26, paint(GOLD, a1 * 0.45, blur=16))
        c.drawCircle(X, y1, 10, paint(PALE_GOLD, a1))
        draw_text(cv, "his count begins here", X + 200, y1 - 8, font("garamond-italic", 42, 500), PALE_GOLD,
                  a1, align="left")
        aq = smooth(seg(t, T.w(2, "wrong") - 0.1, T.w(2, "wrong") + 0.3))
        draw_text(cv, "?", X + 610, y1 + 6, font("garamond", 120, 600), (0.95, 0.45, 0.3), a1 * aq, glow=20)

    # Herod and the likely birth window
    ab = smooth(seg(t, T.w(3, "earlier") - 0.3, T.w(3, "earlier") + 0.5)) * (1 - smooth(seg(t, T.s(4) - 0.2, T.s(4) + 0.5)))
    if ab > 0:
        ytop, ybot = sy(_ypos_bc(4) + 0.5), sy(_ypos_bc(6) - 0.5)
        r = skia.Rect.MakeLTRB(X - 16, ytop, X + 16, ybot)
        c.drawRRect(skia.RRect.MakeRectXY(r, 16, 16), paint((1.0, 0.75, 0.4), ab * 0.35, blur=12))
        c.drawRRect(skia.RRect.MakeRectXY(r, 16, 16), paint((1.0, 0.82, 0.55), ab * 0.8, stroke=2.5))
        lx = X + 330
        draw_text(cv, "most estimates", lx, sy(_ypos_bc(5)) - 30, font("garamond-italic", 40, 500), PALE_GOLD, ab,
                  align="left")
        draw_text(cv, "for Jesus' birth:", lx, sy(_ypos_bc(5)) + 18, font("garamond-italic", 40, 500), PALE_GOLD,
                  ab, align="left")
        draw_text(cv, "c. 6–4 BC", lx, sy(_ypos_bc(5)) + 80, font("cinzel", 50, 700), IVORY, ab, align="left")
    ah = smooth(seg(t, T.w(3, "Herod") - 0.2, T.w(3, "Herod") + 0.5)) * (1 - smooth(seg(t, T.s(4) - 0.2, T.s(4) + 0.5)))
    if ah > 0:
        y = sy(_ypos_bc(4))
        c.drawLine(X + 20, y, X + 300, y, paint((0.9, 0.4, 0.3), ah * 0.8, stroke=2))
        draw_text(cv, "† HEROD", X + 330, y - 105, font("cinzel", 44, 700), (0.98, 0.6, 0.45), ah,
                  tracking=0.08, align="left")
        draw_text(cv, "dies, 4 BC", X + 330, y - 55, font("garamond-italic", 40, 500), (0.98, 0.7, 0.55), ah,
                  align="left")

    # no year zero
    az = smooth(seg(t, T.w(4, "zero") - 0.3, T.w(4, "zero") + 0.3))
    if az > 0:
        y0 = sy(0.0)
        ax = 1 - smooth(seg(t, T.w(4, "zero") + 0.6, T.w(4, "zero") + 1.6))
        c.drawLine(X - 24, y0, X + 24, y0, paint((0.95, 0.4, 0.3), az * ax, stroke=3))
        draw_text(cv, "0", X + 60, y0 + 18, font("cinzel", 54, 700), (0.95, 0.45, 0.32), az * ax, align="left")
        cr = smooth(seg(t, T.w(4, "zero") + 0.2, T.w(4, "zero") + 0.6)) * az * ax
        c.drawLine(X + 50, y0 - 30, X + 110, y0 + 30, paint((1, 0.5, 0.35), cr, stroke=6))
        c.drawLine(X + 50, y0 + 30, X + 110, y0 - 30, paint((1, 0.5, 0.35), cr, stroke=6))
        draw_text_reveal(cv, "NO YEAR", W - 80, 470, font("cinzel", 92, 700), az, IVORY, tracking=0.08, align="right")
        draw_text_reveal(cv, "ZERO", W - 80, 580, font("cinzel", 92, 700), az, (0.95, 0.5, 0.36), tracking=0.08,
                         align="right")
    ar = smooth(seg(t, T.w(4, "runs") - 0.2, T.w(4, "into", end=True)))
    if ar > 0:
        ya, yb = sy(_ypos_bc(1)), sy(_ypos_ad(1))
        path = skia.Path()
        path.moveTo(X - 40, ya)
        path.cubicTo(X - 170, ya - 20, X - 170, yb + 20, X - 40, yb)
        meas = skia.PathMeasure(path, False)
        seg_path = skia.Path()
        meas.getSegment(0, meas.getLength() * ar, seg_path, True)
        c.drawPath(seg_path, paint(PALE_GOLD, 0.9, stroke=5))
        if ar > 0.95:
            c.drawCircle(X - 40, yb, 8, paint(PALE_GOLD, 1))
    return cv.to_float()


# ----------------------------------------------------------------------------- 3. Roman consular dating
@lru_cache(maxsize=1)
def _inscription():
    w, h = W, H
    alb, rough = relief.marble(w, h)
    lines = ["C·CAESARE", "L·AEMILIO·PAVLLO", "COS"]
    f = font("cinzel", 112, 700)
    widest = max(gfx.text_width(s, f, 0.08) for s in lines)
    if widest > 860:
        f = font("cinzel", 112 * 860 / widest, 700)
    depths = relief.carve(lines, w, h, f, 170, 830)
    # left-to-right reveal order within each line
    xs = np.linspace(0, 1, w, dtype=np.float32)[None, :].repeat(h, 0)
    return alb, rough, depths, xs


def s_inscription(t):
    T = TL()
    alb, rough, depths, xs = _inscription()
    times = [T.w(6, "Gaius"), T.w(6, "Lucius"), T.w(6, "consuls")]
    durs = [T.w(6, "Caesar", end=True) - times[0] + 0.3, T.w(6, "Paullus", end=True) - times[1] + 0.3, 0.6]
    height = rough * 1.0
    pig = np.zeros_like(rough)
    for d, t0, du in zip(depths, times, durs):
        pr = seg(t, t0 - 0.15, t0 + du)
        if pr <= 0:
            continue
        rv = np.clip((pr * 1.15 - xs) / 0.05, 0, 1)
        height = height - d * rv * 0.11
        pig = np.maximum(pig, d * rv)
    n = relief.normals(height, 75.0)
    az = lerp(150, 205, seg(t, T.s(5) - 0.5, T.e(6) + 0.5))
    ndl, spec = relief.light(n, az, 24)
    amb = 0.42
    pg = np.clip(pig * 1.6, 0, 1)[..., None]
    col = alb * (1 - pg * 0.95) + np.array([0.46, 0.05, 0.03], np.float32) * pg * 0.95
    img = col * (amb + 0.85 * ndl[..., None]) + (spec ** 30 * 0.25)[..., None]
    # raking light falloff across the slab
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    lx = W * (0.15 + 0.6 * seg(t, 27, 36))
    img *= (0.5 + 0.55 * np.exp(-((xx - lx) / 850) ** 2 - ((yy - 900) / 1100) ** 2))[..., None]
    img *= np.array([1.0, 0.96, 0.89], np.float32)
    s = lerp(1.0, 1.06, seg(t, 27, 36.5))
    M = np.float32([[s, 0, (1 - s) * W / 2], [0, s, (1 - s) * H * 0.48]])
    img = cv2.warpAffine(np.clip(img, 0, 1.2), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    img = img * smooth(seg(t, 27.0, 27.9))
    cv = Canvas.from_float(np.clip(img, 0, 1))
    a = smooth(seg(t, T.s(5) + 0.2, T.s(5) + 1.0))
    draw_text(cv, "ROME", W / 2, 330, font("cinzel", 50, 700), INK_DARK, a * 0.85, tracking=0.5)
    draw_text(cv, "a year was named for its two consuls", W / 2, 400, font("garamond-italic", 44, 500), INK_DARK,
              a * 0.8)
    at = smooth(seg(t, T.w(6, "consuls"), T.w(6, "consuls") + 0.8))
    draw_text(cv, "‘Gaius Caesar and Lucius Aemilius Paullus,", W / 2, 1260, font("garamond-italic", 42, 500),
              INK_DARK, at * 0.85)
    draw_text(cv, "being consuls’", W / 2, 1312, font("garamond-italic", 42, 500), INK_DARK, at * 0.85)
    return cv.to_float()


# ----------------------------------------------------------------------------- 4. Yuanshi
def s_yuanshi(t):
    T = TL()
    img = fx.paper("rice").copy()
    # drifting ink-wash cloud at the bottom
    cloud = gfx.fbm(H // 4, W // 4, 60, 41, 5)
    cloud = cv2.resize(cloud, (W, H))
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    wash = np.clip((cloud - 0.55) * 3, 0, 1) * np.clip((yy - 0.72) * 4, 0, 1)
    img = img * (1 - wash[..., None] * 0.35)
    cy0 = 300
    size = 245
    chars = [("元", T.w(7, "Yuanshi") - 0.55), ("始", T.w(7, "Yuanshi") - 0.1),
             ("元", T.w(7, "Original") - 0.1), ("年", T.w(7, "Original") + 0.4)]
    for k, (ch, t0) in enumerate(chars):
        pr = seg(t, t0, t0 + 0.9)
        if pr > 0:
            fx.paste(img, fx.ink_char(ch, size, pr), 330, cy0 + k * 270 + 110)
    cv = Canvas.from_float(np.clip(img, 0, 1))
    th = T.w(7, "Han")
    stamp = seg(t, th - 0.05, th + 0.15)
    a_big = smooth(stamp) * (1 - smooth(seg(t, T.w(7, "Yuanshi") - 0.9, T.w(7, "Yuanshi") - 0.4)))
    if a_big > 0:
        sz = 420 * (1 + 0.25 * (1 - ease_out(stamp)))
        fx.seal(cv, W / 2, 820, sz, "漢", a=a_big * 0.9)
        draw_text(cv, "HAN", W / 2, 1120, font("cinzel", 60, 700), INK_DARK, a_big * 0.8, tracking=0.5)
        draw_text(cv, "the ruling dynasty, since 202 BC", W / 2, 1178, font("garamond-italic", 44, 500), INK_DARK,
                  a_big * 0.75)
    ah = smooth(seg(t, T.w(7, "China") - 0.2, T.w(7, "China") + 0.6))
    draw_text(cv, "CHINA · THE HAN COURT", W / 2, 180, font("cinzel", 38, 700), INK_DARK, ah * 0.85,
              tracking=0.35)
    a1 = smooth(seg(t, T.w(7, "Yuanshi") + 0.3, T.w(7, "Yuanshi") + 1.0))
    draw_text(cv, "Yuánshǐ", 560, 470, font("garamond", 86, 600), INK_DARK, a1, align="left")
    draw_text(cv, "‘the Original", 560, 545, font("garamond-italic", 54, 500), (0.45, 0.1, 0.07), a1,
              align="left")
    draw_text(cv, "Beginning’", 560, 605, font("garamond-italic", 54, 500), (0.45, 0.1, 0.07), a1, align="left")
    a2 = smooth(seg(t, T.w(7, "Original") + 0.6, T.w(7, "Original") + 1.4))
    draw_text(cv, "YEAR ONE", 560, 1010, font("cinzel", 52, 700), INK_DARK, a2, tracking=0.12, align="left")
    draw_text(cv, "of the new era", 560, 1066, font("garamond-italic", 46, 500), INK_DARK, a2 * 0.85, align="left")
    draw_text(cv, "= 1 AD", 560, 1150, font("cinzel", 60, 700), (0.55, 0.12, 0.08), a2, align="left")
    fx.seal(cv, 330, 1395, 120, "元始", a=smooth(seg(t, T.w(7, "Original") + 1.0, T.w(7, "Original") + 1.3)))
    return cv.to_float()


# ----------------------------------------------------------------------------- 5. two empires
EMP_CAM = (Camera(lat=31, lon=58, dist=4.9, fov=34, shift_y=0.08), Camera(lat=33, lon=62, dist=4.4, fov=34, shift_y=0.08))


def _empires_cam(t):
    T = TL()
    a, b = EMP_CAM
    u = seg(t, T.s(8) - 0.6, T.e(10))
    cam = a.lerp(b, ease_io(u))
    # final dive toward Rome to hand over to the Rome environment
    d = ease_io(seg(t, T.e(10) + 0.05, T.e(10) + 0.85))
    if d > 0:
        cam = cam.lerp(Camera(lat=41.9, lon=12.5, dist=0.9, tilt=0, heading=0, fov=34, shift_y=0.0), d)
    return cam


def great_circle(a, b, n=120, lift=0.06):
    va, vb = ll2v(*a), ll2v(*b)
    om = math.acos(np.clip(va @ vb, -1, 1))
    pts = []
    for i in range(n + 1):
        u = i / n
        v = (math.sin((1 - u) * om) * va + math.sin(u * om) * vb) / math.sin(om)
        v = v * (1 + lift * math.sin(math.pi * u))
        pts.append(v)
    return np.array(pts)


def project_xyz(cam, P):
    C, F, R, U, f = cam.basis()
    v = P - C
    z = v @ F
    x = W / 2 + (v @ R) / z * f
    y = H / 2 + cam.shift_y * H - (v @ U) / z * f
    # visible if not hidden behind the globe
    d = v / np.linalg.norm(v, axis=-1, keepdims=True)
    b = d @ C
    c = C @ C - 1
    disc = b * b - c
    tt = -b - np.sqrt(np.maximum(disc, 0))
    hidden = (disc > 0) & (tt > 0) & (tt < np.linalg.norm(v, axis=-1) - 1e-3)
    return x, y, ~hidden


def s_empires(t):
    T = TL()
    cam = _empires_cam(t)
    sun = (20.0, cam.lon + 15)
    img, cov = globe_shot(cam, sun, glint=0.35)
    img = img * (0.78 + 0.22 * smooth(seg(t, T.e(10), T.e(10) + 0.6)))
    cv = Canvas.from_float(np.clip(img, 0, 1))
    R = geo.regions()
    dive = smooth(seg(t, T.e(10) - 0.2, T.e(10) + 0.5))
    a_rome = smooth(seg(t, T.w(8, "Rome") - 0.2, T.w(8, "Rome") + 0.6)) * (1 - dive * 0.6)
    a_han = smooth(seg(t, T.w(8, "Han") - 0.2, T.w(8, "Han") + 0.6)) * (1 - dive)
    a_par = smooth(seg(t, T.w(8, "opposite"), T.w(8, "opposite") + 1.0)) * 0.6 * (1 - dive)
    geo.fill_region(cv, cam, R["rome"], ROME, 0.42 * a_rome, edge_alpha=0.9 * a_rome)
    geo.fill_region(cv, cam, R["rome_clients"], ROME, 0.2 * a_rome, edge_alpha=0.4 * a_rome)
    geo.fill_region(cv, cam, R["parthia"], PARTHIA, 0.25 * a_par, edge_alpha=0.5 * a_par, glow=0)
    geo.fill_region(cv, cam, R["han"], HAN, 0.42 * a_han, edge_alpha=0.9 * a_han)
    geo.region_label(cv, cam, 50.5, 19.0, "ROME", a_rome * (1 - dive), size=50, sub="Roman Empire")
    geo.region_label(cv, cam, 27.0, 104.0, "HAN", a_han, size=50, sub="Han Empire")
    # 8,000 km arc
    t_arc = T.w(8, "eight")
    pr = smooth(seg(t, t_arc - 0.3, t_arc + 1.4))
    rumour = smooth(seg(t, T.w(10, "rumour") - 0.4, T.w(10, "rumour") + 0.4))
    if pr > 0:
        pts = great_circle(CITIES["Rome"], CITIES["Chang'an"], 160, 0.05)
        n = max(2, int(len(pts) * pr))
        x, y, vis = project_xyz(cam, pts[:n])
        path = skia.Path()
        started = False
        for i, (xi, yi, v) in enumerate(zip(x, y, vis)):
            if not v:
                started = False
                continue
            if rumour > 0 and (i // 4) % 2 == 1 and rumour > 0.5:
                started = False
                continue
            if not started:
                path.moveTo(float(xi), float(yi))
                started = True
            else:
                path.lineTo(float(xi), float(yi))
        aa = 1 - 0.55 * rumour
        cv.c.drawPath(path, paint(PALE_GOLD, 0.45 * aa * (1 - dive), stroke=9, blur=6))
        cv.c.drawPath(path, paint(PALE_GOLD, 0.95 * aa * (1 - dive), stroke=3))
        if pr >= 1:
            mx, my, mv = project_xyz(cam, pts[len(pts) // 2:len(pts) // 2 + 1])
            al = smooth(seg(t, t_arc + 0.8, t_arc + 1.4)) * (1 - dive)
            draw_text(cv, "8,000 km", float(mx[0]), float(my[0]) - 34, font("cinzel", 48, 700), IVORY, al,
                      tracking=0.1, shadow=1.0)
    for name in ("Rome", "Chang'an"):
        geo.city_marker(cv, cam, name, a=max(a_rome if name == "Rome" else a_han, 0) * (1 - dive), label=False, r=8)
    # population counter
    tc = T.w(9, "hundred")
    ac = fade_io(t, tc - 0.6, T.e(10) - 0.2, 0.5, 0.6)
    if ac > 0:
        val = int(100_000_000 * ease_out(seg(t, tc - 0.5, tc + 0.9), 4) / 1_000_000) * 1_000_000
        draw_text(cv, f"~{val:,}", W / 2, 300, font("cinzel", 92, 700), PALE_GOLD, ac, tracking=0.02, glow=18,
                  shadow=0.8)
        draw_text(cv, "people · a rough estimate", W / 2, 362, font("garamond-italic", 44, 500), IVORY, ac * 0.9,
                  shadow=0.8)
        ab = ac * smooth(seg(t, T.w(9, "third") - 0.3, T.w(9, "third") + 0.5))
        bx0, bx1, by = 190, W - 190, 430
        cv.c.drawRoundRect(skia.Rect.MakeLTRB(bx0, by, bx1, by + 16), 8, 8, paint(IVORY, ab * 0.25))
        fillw = (bx1 - bx0) * (1 / 3) * smooth(seg(t, T.w(9, "third"), T.w(9, "third") + 0.8))
        cv.c.drawRoundRect(skia.Rect.MakeLTRB(bx0, by, bx0 + fillw, by + 16), 8, 8, paint(GOLD, ab))
        sh = skia.GradientShader.MakeLinear([skia.Point(bx0 + fillw, 0), skia.Point(bx0 + (bx1 - bx0) * 0.55, 0)],
                                            [skia.Color4f(*GOLD, 0.6 * ab).toColor(),
                                             skia.Color4f(*GOLD, 0.0).toColor()])
        p = paint(GOLD, ab)
        p.setShader(sh)
        cv.c.drawRect(skia.Rect.MakeLTRB(bx0 + fillw, by, bx0 + (bx1 - bx0) * 0.55, by + 16), p)
        draw_text(cv, "a third or more of all people alive", W / 2, by + 66, font("garamond-italic", 40, 500),
                  PALE_GOLD, ab, shadow=0.8)
    # Seres
    ts = T.w(10, "Seres")
    a_s = fade_io(t, ts - 0.3, T.e(10) + 0.4, 0.5, 0.4)
    if a_s > 0:
        geo.region_label(cv, cam, 45.0, 97.0, "SERES", a_s, size=70, rgb=IVORY, tracking=0.3,
                         sub="‘the silk people’")
        # silk ribbon drifting west from China
        x0, y0, v0 = project(cam, [35.0], [100.0])
        if v0[0]:
            for k in range(6):
                path = skia.Path()
                ph = t * 1.4 + k * 0.5
                path.moveTo(float(x0[0]), float(y0[0]))
                for j in range(1, 30):
                    u = j / 29
                    path.lineTo(float(x0[0]) - u * 520 * smooth(seg(t, ts - 0.2, ts + 1.2)),
                                float(y0[0]) + math.sin(u * 6 + ph) * 26 * u + k * 5 - u * 60)
                cv.c.drawPath(path, paint((0.98, 0.9, 0.8), a_s * 0.18, stroke=4))
    flash = math.exp(-((t - (T.e(10) + 0.75)) / 0.18) ** 2)
    out = cv.to_float()
    return np.clip(out + flash * 0.75 * np.array([1.0, 0.85, 0.65], np.float32), 0, 1)
