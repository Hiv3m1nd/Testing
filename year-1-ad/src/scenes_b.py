"""Shots 6-12: Rome, the journey east, Chang'an, the white pheasant, the close, next year, end card."""
from __future__ import annotations

import math
from functools import lru_cache

import cv2
import numpy as np
import skia

import environments as env
import fx
import geo
import gfx
import relief
from geo import CITIES
from gfx import (GOLD, HAN, IVORY, PALE_GOLD, PARTHIA, ROME, Canvas, H, W, draw_text, draw_text_reveal, ease_io,
                 ease_out, fade_io, font, lerp, paint, seg, smooth)
from globe import Camera, fly, project
from scenes_a import globe_shot, great_circle, night_lights, project_xyz, sun_behind
from timeline import TL


def _coin_rgba(which, size, t, yaw, az):
    coin = relief.coin_gaius_lucius() if which == "gl" else relief.coin_musa()
    return relief.render_coin(coin, size, az=az, el=36, yaw=yaw)


def _darken(img, amt, center=(0.5, 0.42)):
    if amt <= 0:
        return img
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot((xx / W - center[0]) * 1.2, yy / H - center[1])
    m = 1 - amt * np.clip(0.55 + d * 0.9, 0, 1)
    return img * m[..., None]


# ----------------------------------------------------------------------------- 6. Rome at dusk + the heirs
def s_rome(t):
    T = TL()
    E = env.rome()
    u = seg(t, 62.0, 75.0)
    img = env.compose(E, t, dolly=(lerp(-110, 110, u), lerp(10, -10, u)), push=lerp(1.0, 1.08, ease_io(u)))
    tc = T.s(12) - 0.3
    dim = smooth(seg(t, tc - 0.3, tc + 0.6))
    img = _darken(img, 0.62 * dim)
    cv = Canvas.from_float(np.clip(img, 0, 1))
    fx.dust(cv, t, n=70, alpha=0.45 * (1 - dim * 0.6), drift=(10, -6))
    out_t = 1 - smooth(seg(dim, 0.0, 0.45))
    a_t = smooth(seg(t, T.s(11) - 0.2, T.s(11) + 0.6)) * out_t
    draw_text(cv, "ROME", W / 2, 250, font("cinzel", 40, 700), PALE_GOLD, a_t * 0.9, tracking=0.6, shadow=0.6)
    pa = seg(t, T.w(11, "Augustus") - 0.25, T.w(11, "Augustus") + 0.9)
    draw_text_reveal(cv, "AUGUSTUS", W / 2, 420, font("cinzel", 132, 700), pa, PALE_GOLD, a=out_t, tracking=0.08,
                     glow=22, shadow=0.6)
    a_s = smooth(seg(t, T.w(11, "sixties") - 0.3, T.w(11, "sixties") + 0.5)) * out_t
    draw_text(cv, "born 63 BC · in power since 31 BC", W / 2, 500, font("garamond-italic", 48, 500), IVORY,
              a_s, shadow=0.8)
    lb = seg(t, T.w(11, "bloodline") - 0.3, T.w(11, "bloodline") + 0.9)
    if lb > 0 and dim < 1:
        y0, y1 = 540, 540 + 330 * ease_out(lb)
        cv.c.drawLine(W / 2, y0, W / 2, y1, paint(GOLD, (1 - dim) * 0.5, stroke=8, blur=6))
        cv.c.drawLine(W / 2, y0, W / 2, y1, paint(PALE_GOLD, 1 - dim, stroke=2.5))
    if dim > 0:
        p = ease_out(seg(t, tc, tc + 1.2))
        size = int(560 + 80 * p)
        yaw = lerp(-38, 10, ease_io(seg(t, tc, T.e(12) + 0.3)))
        coin = _coin_rgba("gl", size, t, yaw, lerp(115, 160, seg(t, tc, T.e(12))))
        base = cv.to_float()
        fx.paste(base, coin, W / 2, 770 + (1 - p) * 40, alpha=dim)
        cv = Canvas.from_float(np.clip(base, 0, 1))
        a_h = smooth(seg(dim, 0.55, 1.0))
        draw_text(cv, "THE HEIRS", W / 2, 330, font("cinzel", 44, 700), PALE_GOLD, a_h * 0.9, tracking=0.5,
                  shadow=0.6)
        draw_text(cv, "silver denarius, struck c. 2 BC – 4 AD", W / 2, 392, font("garamond-italic", 42, 500),
                  IVORY, a_h * 0.85, shadow=0.6)
        for name, born, x, word in (("GAIUS", "born 20 BC", W / 2 - 170, "Gaius"),
                                    ("LUCIUS", "born 17 BC", W / 2 + 170, "Lucius")):
            a = smooth(seg(t, T.w(12, word) - 0.2, T.w(12, word) + 0.4)) * dim
            draw_text(cv, name, x, 1135, font("cinzel", 52, 700), IVORY, a, tracking=0.1, shadow=0.8)
            draw_text(cv, born, x, 1185, font("garamond-italic", 40, 500), PALE_GOLD, a, shadow=0.8)
        aa = smooth(seg(t, T.w(12, "adopted") - 0.2, T.w(12, "adopted") + 0.5)) * dim
        draw_text(cv, "adopted by Augustus as his sons, 17 BC", W / 2, 1262, font("garamond-italic", 42, 500),
                  PALE_GOLD, aa, shadow=0.8)
    return cv.to_float()


# ----------------------------------------------------------------------------- 7. the journey east
def _journey_keys():
    T = TL()
    return [
        (T.s(13) - 0.6, Camera(40.2, 13.6, 0.72, tilt=30, heading=330, fov=36)),
        (T.e(13), Camera(40.6, 13.3, 0.58, tilt=34, heading=325, fov=36)),
        (T.s(14) + 1.6, Camera(38.7, 21.0, 1.05, tilt=28, heading=95, fov=36)),
        (T.e(14), Camera(38.5, 22.0, 0.97, tilt=30, heading=95, fov=36)),
        (T.s(15) + 2.2, Camera(35.5, 39.0, 1.35, tilt=30, heading=80, fov=36)),
        (T.e(15), Camera(35.0, 45.0, 1.45, tilt=28, heading=80, fov=36)),
        (T.e(18), Camera(34.2, 47.0, 1.3, tilt=26, heading=80, fov=36)),
        (T.s(19) + 1.6, Camera(23.0, 62.0, 3.5, tilt=8, heading=0, fov=34, shift_y=0.05)),
        (T.e(20), Camera(24.0, 64.0, 3.3, tilt=8, heading=0, fov=34, shift_y=0.05)),
        (T.e(20) + 1.3, Camera(34.3, 108.9, 0.8, tilt=30, heading=0, fov=36)),
    ]


def journey_cam(t):
    keys = _journey_keys()
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            u = ease_io(seg(t, t0, t1))
            return fly(a, b, u, arc=0.25)
    return keys[-1][1]


def _arc_path(cam, a, b, prog, lift=0.02, dashed=False):
    pts = great_circle(a, b, 90, lift)
    n = max(2, int(len(pts) * prog))
    x, y, vis = project_xyz(cam, pts[:n])
    path = skia.Path()
    started = False
    for i, (xi, yi, v) in enumerate(zip(x, y, vis)):
        if not v or (dashed and (i // 3) % 2):
            started = False
            continue
        if not started:
            path.moveTo(float(xi), float(yi))
            started = True
        else:
            path.lineTo(float(xi), float(yi))
    return path, (float(x[-1]), float(y[-1]))


def _route_progress_path(cam, route, prog):
    path, end = geo.line_path(cam, route, step=0.25, upto=prog)
    return path, end


@lru_cache(maxsize=None)
def _route_cum(name):
    route = np.array(geo.SILK_ROAD if name == "silk" else (geo.SEA_ROUTE if name == "sea" else geo.SEA_ROUTE_N))
    seglen = np.hypot(np.diff(route[:, 0]), np.diff(route[:, 1]))
    cum = np.concatenate([[0], np.cumsum(seglen)])
    return route, cum / cum[-1]


def _route_point(name, u):
    route, cum = _route_cum(name)
    u = min(max(u, 0.0), 1.0)
    i = int(np.searchsorted(cum, u, side="right")) - 1
    i = min(i, len(route) - 2)
    w = (u - cum[i]) / max(cum[i + 1] - cum[i], 1e-9)
    return route[i] + (route[i + 1] - route[i]) * w


def s_journey(t):
    T = TL()
    cam = journey_cam(t)
    sun = (28.0, cam.lon - 25)
    img, cov = globe_shot(cam, sun, glint=0.18, haze=1.2)
    musa = fade_io(t, T.s(16) - 0.4, T.e(18) + 0.4, 0.6, 0.6)
    strabo = fade_io(t, T.w(20, "Strabo") - 0.4, T.e(20) + 0.2, 0.5, 0.5)
    trade = smooth(seg(t, T.s(19) - 0.2, T.s(19) + 1.2)) * (1 - smooth(seg(t, T.e(20) + 0.1, T.e(20) + 0.8)))
    img = _darken(img, 0.55 * musa + 0.6 * strabo)
    img = img * smooth(seg(t, T.s(13) - 0.6, T.s(13) + 0.2))
    cv = Canvas.from_float(np.clip(img, 0, 1))
    R = geo.regions()
    # Roman world, always faintly present; Parthia from "Parthia" on
    a_rome = 0.12 + 0.2 * smooth(seg(t, T.s(14), T.s(15) + 1))
    geo.fill_region(cv, cam, R["rome"], ROME, a_rome * (1 - musa * 0.6), edge_alpha=0.55 * (1 - musa * 0.6), glow=6)
    geo.fill_region(cv, cam, R["rome_clients"], ROME, 0.12 * (1 - musa * 0.6), edge_alpha=0.3 * (1 - musa * 0.6), glow=0)
    a_par = smooth(seg(t, T.w(15, "Parthia") - 0.3, T.w(15, "Parthia") + 0.6))
    geo.fill_region(cv, cam, R["parthia"], PARTHIA, 0.32 * a_par * (1 - musa * 0.5), edge_alpha=0.8 * a_par * (1 - musa * 0.5))
    geo.fill_region(cv, cam, R["armenia"], (0.85, 0.85, 0.85), 0.15 * a_par * (1 - musa), edge_alpha=0.4 * a_par * (1 - musa),
                    hatch=True, glow=0)
    geo.fill_region(cv, cam, R["han"], HAN, 0.3 * trade, edge_alpha=0.7 * trade)
    geo.draw_rivers(cv, cam, 0.35 + 0.3 * smooth(seg(t, T.w(15, "facing"), T.w(15, "facing") + 1)) * (1 - musa))

    # Julia on Pandateria
    aj = fade_io(t, T.s(13) - 0.2, T.s(14) + 0.8, 0.6, 0.6)
    geo.city_marker(cv, cam, "Rome", a=aj, size=40, sub=None)
    ti = T.w(13, "island")
    ajp = smooth(seg(t, T.w(13, "Julia") - 0.2, T.w(13, "Julia") + 0.5)) * aj
    geo.city_marker(cv, cam, "Pandateria", a=ajp, size=44, sub="Julia, exiled 2 BC", sub_size=40, dy=60, dx=0,
                    align="center", pulse=(seg(t, ti, ti + 1.2)) if t > ti else 0.0)
    # Tiberius on Rhodes
    at = fade_io(t, T.w(14, "Rhodes") - 0.4, T.e(14) + 0.8, 0.5, 0.6)
    geo.city_marker(cv, cam, "Rhodes", a=at, size=44, sub="Tiberius, there since 6 BC", sub_size=40, dx=0, dy=64,
                    align="center", pulse=seg(t, T.w(14, "Rhodes"), T.w(14, "Rhodes") + 1.2))
    geo.city_marker(cv, cam, "Rome", a=at, size=40)
    tr = T.w(14, "refused")
    pr = ease_out(seg(t, tr - 0.6, tr + 0.6)) * 0.55
    if pr > 0 and at > 0:
        path, end = _arc_path(cam, CITIES["Rhodes"], CITIES["Rome"], pr, 0.01, dashed=True)
        cv.c.drawPath(path, paint(IVORY, at * 0.9, stroke=4))
        ax = smooth(seg(t, tr + 0.4, tr + 0.8)) * at
        if ax > 0:
            x, y = end
            cv.c.drawLine(x - 22, y - 22, x + 22, y + 22, paint((1, 0.4, 0.3), ax, stroke=7))
            cv.c.drawLine(x - 22, y + 22, x + 22, y - 22, paint((1, 0.4, 0.3), ax, stroke=7))
    # Gaius in the East
    ag = fade_io(t, T.w(15, "Gaius") - 0.3, T.s(16) + 0.2, 0.5, 0.5)
    geo.city_marker(cv, cam, "Antioch", a=ag, label="GAIUS CAESAR", size=46, sub="consul, 1 AD · aged about 20",
                    sub_size=40, dx=0, dy=-120, align="center", r=9)
    a_lab = a_par * (1 - musa) * (1 - trade)
    geo.region_label(cv, cam, 32.5, 53.5, "PARTHIA", a_lab, size=64, rgb=IVORY, sub="the Arsacid empire")
    geo.region_label(cv, cam, 40.2, 43.0, "ARMENIA", a_lab * 0.9, size=36, sub="contested")
    geo.city_marker(cv, cam, "Ctesiphon", a=a_lab, size=34, r=6)

    # Musa
    if musa > 0:
        base = cv.to_float()
        p = ease_out(seg(t, T.s(16) - 0.3, T.s(16) + 1.0))
        tf = T.s(18)
        flip = ease_io(seg(t, tf - 0.2, tf + 1.4))
        yaw = lerp(lerp(-30, 6, ease_io(seg(t, T.s(16), T.e(17)))), 0, flip) + math.sin(flip * math.pi) * 28
        coin = _coin_rgba("musa", int(540 + 40 * p + 50 * flip), t, yaw, lerp(220, 150, seg(t, T.s(16), T.e(18))))
        fx.paste(base, coin, W / 2, 640, alpha=musa)
        cv = Canvas.from_float(np.clip(base, 0, 1))
        am = musa * smooth(seg(t, T.w(16, "Musa") - 0.3, T.w(16, "Musa") + 0.4))
        draw_text(cv, "MUSA", W / 2, 1025, font("cinzel", 92, 700), PALE_GOLD, am, tracking=0.2, glow=16, shadow=0.7)
        draw_text(cv, "queen of Parthia, beside her son Phraates V", W / 2, 1085, font("garamond-italic", 42, 500),
                  IVORY, am * 0.9, shadow=0.8)
        ai = musa * smooth(seg(t, T.w(17, "Italian") - 0.2, T.w(17, "Italian") + 0.5))
        draw_text(cv, "‘an Italian slave girl’, a gift from Augustus", W / 2, 1170,
                  font("garamond-italic", 42, 500), PALE_GOLD, ai, shadow=0.8)
        draw_text(cv, "JOSEPHUS, ANTIQUITIES 18.40", W / 2, 1222, font("cinzel", 28, 600), IVORY, ai * 0.7,
                  tracking=0.2, shadow=0.8)
        ac = musa * smooth(seg(t, tf, tf + 0.6))
        draw_text(cv, "ΘΕΑΣ ΟΥΡΑΝΙΑΣ ΜΟΥΣΗΣ "
                      "ΒΑΣΙΛΙΣΣΗΣ", W / 2, 285,
                  font("serif-tc", 36, 600), PALE_GOLD, ac, tracking=0.12, shadow=0.8)
        draw_text(cv, "‘of the heavenly goddess Musa, queen’", W / 2, 338, font("garamond-italic", 40, 500), IVORY,
                  ac * 0.9, shadow=0.8)

    # trade
    trade_full = trade
    trade = trade * (1 - 0.8 * strabo)
    if trade_full > 0:
        ts0, ts1 = T.w(19, "silk") - 0.2, T.w(19, "trader", nth=1, end=True)
        sp = ease_io(seg(t, ts0, ts1))
        silk = list(reversed(geo.SILK_ROAD))  # draw from Chang'an westward
        if sp > 0:
            route = np.array(geo.SILK_ROAD[::-1])
            path, _ = geo.line_path(cam, route, step=0.3, upto=sp)
            cv.c.drawPath(path, paint((1.0, 0.85, 0.55), trade * 0.4, stroke=10, blur=7))
            cv.c.drawPath(path, paint((1.0, 0.9, 0.7), trade * 0.95, stroke=3.2))
            # relay towns light up as the line passes: trader to trader
            n = len(silk)
            for k, (la, lo) in enumerate(silk):
                kk = k / (n - 1)
                if sp >= kk:
                    x, y, v = project(cam, [la], [lo])
                    if v[0]:
                        pulse = math.exp(-((sp - kk) * 12) ** 2)
                        cv.c.drawCircle(float(x[0]), float(y[0]), 5 + 10 * pulse, paint(PALE_GOLD, trade * (0.7 + 0.3 * pulse)))
            # bales of silk drifting west along the road
            for k in range(14):
                u = ((t * 0.035 + k / 14) % 1.0)
                if 1 - u > sp:
                    continue
                la, lo = _route_point("silk", 1 - u)
                x, y, v = project(cam, [la], [lo])
                if v[0]:
                    cv.c.drawCircle(float(x[0]), float(y[0]), 4.5, paint((1, 0.95, 0.85), trade * 0.9))
            geo.region_label(cv, cam, 44.2, 82.0, "SILK", trade * smooth(seg(t, ts0 + 0.6, ts0 + 1.4)), size=40,
                             rgb=PALE_GOLD, tracking=0.5)
        te0, te1 = T.w(20, "Egypt") - 0.3, T.w(20, "India", end=True)
        ep = ease_io(seg(t, te0, te1))
        if ep > 0:
            for name, route in (("sea", geo.SEA_ROUTE), ("sean", geo.SEA_ROUTE_N)):
                path, _ = geo.line_path(cam, route, step=0.3, upto=ep)
                cv.c.drawPath(path, paint((0.6, 0.85, 1.0), trade * 0.35, stroke=10, blur=7))
                cv.c.drawPath(path, paint((0.75, 0.92, 1.0), trade * 0.9, stroke=3, ))
            for k in range(5):
                u = (t * 0.05 + k / 5) % 1.0
                if u > ep:
                    continue
                la, lo = _route_point("sea", u)
                x, y, v = project(cam, [la], [lo])
                if v[0]:
                    fx.ship(cv, float(x[0]), float(y[0]), 16, trade, (0.85, 0.95, 1.0))
            for nm in ("Myos Hormos", "Muziris", "Barygaza"):
                geo.city_marker(cv, cam, nm, a=trade * smooth(seg(t, te0 + 0.4, te0 + 1.2)), size=30, r=6)
            am = trade * smooth(seg(t, T.w(20, "monsoon") - 0.3, T.w(20, "monsoon") + 0.6))
            for k in range(3):  # summer monsoon blowing from the south-west
                pts = [(5 + k * 4 + s * 9, 52 + k * 3 + s * 13) for s in np.linspace(0, 1, 20)]
                ph = (t * 0.5 + k * 0.3) % 1.0
                path, end = geo.line_path(cam, pts, step=0.4, upto=1.0)
                inter = skia.DashPathEffect.Make([26.0, 18.0], -ph * 44)
                pp = paint((0.85, 0.95, 1.0), am * 0.55, stroke=3)
                pp.setPathEffect(inter)
                cv.c.drawPath(path, pp)
            geo.region_label(cv, cam, 8.0, 60.0, "MONSOON", am, size=34, rgb=(0.85, 0.95, 1.0), tracking=0.5)
        if strabo > 0:
            draw_text(cv, "120", W / 2, 640, font("cinzel", 150, 700), PALE_GOLD, strabo, glow=20, shadow=0.8)
            draw_text(cv, "ships a year, from one Egyptian port to India", W / 2, 715, font("garamond-italic", 46, 500),
                      IVORY, strabo, shadow=0.8)
            fill = ease_out(seg(t, T.w(20, "Strabo"), T.w(20, "hundred") + 1.2), 2)
            for k in range(120):
                if k / 120 > fill:
                    break
                cx = W / 2 - 11 * 64 / 2 + (k % 12) * 64
                cy = 800 + (k // 12) * 40
                fx.ship(cv, cx, cy, 13, strabo, PALE_GOLD)
            draw_text(cv, "STRABO, GEOGRAPHY 2.5.12", W / 2, 1240, font("cinzel", 28, 600), IVORY, strabo * 0.75,
                      tracking=0.2, shadow=0.8)
    return cv.to_float()


# ----------------------------------------------------------------------------- 8. Chang'an
@lru_cache(maxsize=1)
def _mist_tex():
    return gfx.fbm(H // 2, W, 120, 77, 5)


def _mist(out, i, t):
    if i not in (0, 1, 2, 3):
        return out
    tex = _mist_tex()
    shift = int((t * (12 + i * 9)) % W)
    m = np.roll(tex, shift, axis=1)
    m = cv2.resize(m, (W, H))
    band_y = [0.52, 0.58, 0.64, 0.7][i]
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    band = np.exp(-((yy - band_y) / 0.05) ** 2)
    a = np.clip((m - 0.35) * 1.6, 0, 1) * band * 0.55
    col = np.array([0.86, 0.8, 0.72], np.float32)
    return out * (1 - a[..., None]) + col * a[..., None]


def s_changan(t):
    T = TL()
    E = env.changan()
    u = seg(t, 118.5, 129.5)
    img = env.compose(E, t, dolly=(lerp(90, -90, u), lerp(-10, 10, u)), push=lerp(1.0, 1.07, ease_io(u)), mist=_mist)
    img = np.clip((img - 0.42) * 1.18 + 0.42, 0, 1) * np.array([1.06, 1.0, 0.9], np.float32)
    cards = smooth(seg(t, T.s(22) - 0.3, T.s(22) + 0.5))
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    img = img * (1 - 0.45 * np.exp(-((yy - 0.24) / 0.16) ** 2))
    img = img * (1 - 0.5 * cards)
    cv = Canvas.from_float(np.clip(img, 0, 1))
    fx.dust(cv, t, n=50, alpha=0.3, rgb=(1.0, 0.92, 0.8), drift=(-6, -4))
    a = smooth(seg(t, T.s(21) - 0.1, T.s(21) + 0.8)) * (1 - cards * 0.75)
    draw_text(cv, "長安", W / 2, 420, font("kai", 150), (0.95, 0.9, 0.82), a, shadow=0.8, glow=10)
    draw_text(cv, "CHANG’AN", W / 2, 520, font("cinzel", 70, 700), PALE_GOLD, a, tracking=0.25, shadow=0.8)
    draw_text(cv, "capital of the Han · ‘Lasting Peace’", W / 2, 585, font("garamond-italic", 44, 500),
              IVORY, a * 0.9, shadow=0.8)
    a1 = smooth(seg(t, T.w(22, "boy") - 0.3, T.w(22, "boy") + 0.4)) * (1 - 0.45 * smooth(seg(t, T.w(22, "Real"), T.w(22, "Real") + 0.6)))
    draw_text(cv, "漢平帝", W / 2, 760, font("kai", 92), (0.95, 0.9, 0.82), a1, shadow=0.8)
    draw_text(cv, "EMPEROR PING", W / 2, 830, font("cinzel", 46, 700), IVORY, a1, tracking=0.2, shadow=0.8)
    draw_text(cv, "aged about nine", W / 2, 882, font("garamond-italic", 42, 500), PALE_GOLD, a1, shadow=0.8)
    a2 = smooth(seg(t, T.w(22, "Wang") - 0.3, T.w(22, "Wang") + 0.5))
    draw_text(cv, "王莽", W / 2, 1105, font("kai", 170), PALE_GOLD, a2, shadow=0.8, glow=22, glow_rgb=GOLD)
    draw_text(cv, "WANG MANG", W / 2, 1185, font("cinzel", 64, 700), IVORY, a2, tracking=0.2, shadow=0.8)
    draw_text(cv, "regent · aged about 45", W / 2, 1240, font("garamond-italic", 44, 500), PALE_GOLD, a2,
              shadow=0.8)
    return cv.to_float()


# ----------------------------------------------------------------------------- 9. the white pheasant
@lru_cache(maxsize=1)
def _pheasant_bg():
    img = fx.paper("night").copy()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cone = np.exp(-((xx - W / 2) / (260 + yy * 0.25)) ** 2) * np.clip(1 - yy / H * 0.9, 0, 1)
    img += cone[..., None] * np.array([0.10, 0.12, 0.14], np.float32)
    pool = np.exp(-((xx - W / 2) / 420) ** 2 - ((yy - 1050) / 140) ** 2)
    img += pool[..., None] * np.array([0.07, 0.08, 0.09], np.float32)
    return img


def s_pheasant(t):
    T = TL()
    img = _pheasant_bg().copy()
    fog = cv2.resize(np.roll(_mist_tex(), int(t * 25) % W, axis=1), (W, H))
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    img += (np.clip(fog - 0.4, 0, 1) * np.exp(-((yy - 0.6) / 0.12) ** 2) * 0.22)[..., None] * np.array([0.7, 0.8, 0.9], np.float32)
    t_zhou, t_title, t_arr = T.w(24, "Duke"), T.s(25), T.s(26)
    t_named = T.w(25, "named")
    # ghost characters of the Duke of Zhou
    az = fade_io(t, t_zhou - 0.3, t_named, 0.9, 0.6)
    cv = Canvas.from_float(np.clip(img, 0, 1))
    if az > 0:
        draw_text(cv, "周公", W / 2, 1000, font("kai", 560), (0.6, 0.7, 0.8), az * 0.13, glow=30)
    ab = smooth(seg(t, T.s(23) - 0.4, T.s(23) + 1.4)) * (1 - smooth(seg(t, t_named - 0.6, t_named + 0.1)))
    ab = max(ab, smooth(seg(t, t_arr - 0.2, t_arr + 0.8)))
    rise = (1 - smooth(seg(t, T.s(23) - 0.4, T.s(23) + 1.6))) * 40
    later = smooth(seg(t, t_arr - 0.2, t_arr + 0.8))
    bx, by, bs = lerp(560, 600, later), lerp(830, 980, later) + rise, lerp(0.9, 0.78, later)
    fx.draw_pheasant(cv, bx, by, bs, t, a=ab)
    fx.dust(cv, t, n=40, alpha=0.4 * ab, rgb=(0.9, 0.95, 1.0), drift=(-10, 18), size=1.6)
    aw = fade_io(t, T.w(23, "white") - 0.2, t_zhou - 0.2, 0.6, 0.5)
    draw_text(cv, "白雉", W / 2, 360, font("kai", 120), IVORY, aw, glow=14)
    draw_text(cv, "THE WHITE PHEASANT", W / 2, 440, font("cinzel", 44, 700), PALE_GOLD, aw, tracking=0.25)
    draw_text(cv, "brought by envoys from the far south", W / 2, 498, font("garamond-italic", 42, 500), IVORY, aw * 0.9)
    adz = fade_io(t, t_zhou - 0.2, t_title + 0.9, 0.5, 0.5)
    draw_text(cv, "THE DUKE OF ZHOU", W / 2, 360, font("cinzel", 52, 700), PALE_GOLD, adz, tracking=0.2, glow=10)
    draw_text(cv, "regent for the boy King Cheng,", W / 2, 425, font("garamond-italic", 44, 500), IVORY, adz * 0.9)
    draw_text(cv, "around the 11th century BC", W / 2, 478, font("garamond-italic", 44, 500), IVORY, adz * 0.9)
    # the title: 安漢公
    at = fade_io(t, T.w(25, "Wang") - 0.3, T.e(26) + 0.6, 0.4, 0.6) * (1 - 0.7 * later)
    if at > 0:
        base = cv.to_float()
        for k, (ch, word) in enumerate((("安", "named"), ("漢", "Duke"), ("公", "Secures"))):
            tw = T.w(25, word)
            pr = seg(t, tw - 0.25, tw + 0.75)
            if pr > 0:
                fx.paste(base, fx.ink_char(ch, 230, pr, rgb=(0.97, 0.88, 0.62), bleed=0.6), 330, 470 + k * 275, alpha=at)
        cv = Canvas.from_float(np.clip(base, 0, 1))
        al = at * smooth(seg(t, T.w(25, "named") - 0.2, T.w(25, "named") + 0.5))
        draw_text(cv, "Ānhàn Gōng", 560, 640, font("garamond", 70, 600), PALE_GOLD, al, align="left")
        draw_text(cv, "‘Duke Who", 560, 720, font("garamond-italic", 54, 500), IVORY, al, align="left")
        draw_text(cv, "Secures the Han’", 560, 780, font("garamond-italic", 54, 500), IVORY, al, align="left")
        draw_text(cv, "WANG MANG, 1 AD", 560, 860, font("cinzel", 34, 600), IVORY, al * 0.8, tracking=0.15,
                  align="left")
        fx.seal(cv, 330, 1300, 110, "王莽", a=at * smooth(seg(t, T.e(25) - 0.2, T.e(25) + 0.1)))
    # the red thread: he arranged it himself
    if later > 0:
        th = smooth(seg(t, T.w(26, "arranged") - 0.3, T.w(26, "arranged") + 0.6))
        ax_, ay_ = bx + (530 - 600) * bs, by - 80 * bs
        top = 250
        cv.c.drawLine(ax_, top, ax_, top + (ay_ - top) * th, paint((0.9, 0.12, 0.1), 0.4, stroke=8, blur=6))
        cv.c.drawLine(ax_, top, ax_, top + (ay_ - top) * th, paint((0.95, 0.2, 0.15), 0.95, stroke=2.5))
        fx.seal(cv, ax_, top - 40, 100, "莽", a=th)
        draw_text(cv, "HANSHU (BOOK OF HAN), CH. 99", W / 2, 150, font("cinzel", 28, 600), IVORY,
                  later * 0.75 * smooth(seg(t, T.w(26, "history"), T.w(26, "history") + 0.6)), tracking=0.2)
    return cv.to_float()


# ----------------------------------------------------------------------------- 10. the close
def s_close(t):
    T = TL()
    split = smooth(seg(t, T.w(28, "Rome") - 0.4, T.w(28, "Rome") + 0.3))
    out = np.zeros((H, W, 3), np.float32)
    if split < 1:
        cam = Camera(lat=30, lon=lerp(54, 62, seg(t, 149, 154)), dist=4.4, fov=34, shift_y=0.04)
        sun = sun_behind(cam, 0.35, 0.15)
        img, cov = globe_shot(cam, sun, glint=0.2)
        cv = Canvas.from_float(np.clip(img, 0, 1))
        R = geo.regions()
        g = 0.75 + 0.25 * math.sin(t * 1.3)
        geo.fill_region(cv, cam, R["rome"], ROME, 0.18 * g, edge_alpha=0.6 * g, glow=14)
        geo.fill_region(cv, cam, R["han"], HAN, 0.18 * g, edge_alpha=0.6 * g, glow=14)
        geo.fill_region(cv, cam, R["parthia"], PARTHIA, 0.1 * g, edge_alpha=0.35 * g, glow=8)
        night_lights(cv, cam, sun, a=1.0, t=t)
        draw_text(cv, "1 AD", W / 2, 300, font("cinzel", 90, 600), PALE_GOLD, smooth(seg(t, 149.3, 150.3)), glow=16)
        out = cv.to_float() * (1 - split)
    if split > 0:
        top = np.zeros((H, W, 3), np.float32)
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        top += np.array([0.16, 0.03, 0.04], np.float32) * np.exp(-((yy - 0.25) / 0.25) ** 2)
        a_cn = smooth(seg(t, T.w(28, "China") - 0.4, T.w(28, "China") + 0.3))
        top += np.array([0.17, 0.11, 0.03], np.float32) * np.exp(-((yy - 0.72) / 0.2) ** 2) * a_cn
        yaw = lerp(-20, 20, seg(t, 153, 161))
        coin = _coin_rgba("gl", 520, t, yaw, 140)
        fx.paste(top, coin, W / 2, 470, alpha=split)
        cv = Canvas.from_float(np.clip(top, 0, 1))
        draw_text(cv, "ROME", W / 2, 165, font("cinzel", 46, 700), PALE_GOLD, split, tracking=0.6)
        ar = smooth(seg(t, T.w(28, "ageing") - 0.2, T.w(28, "ageing") + 0.4))
        draw_text(cv, "an ageing emperor · two young heirs", W / 2, 840, font("garamond-italic", 46, 500), IVORY,
                  ar)
        cv.c.drawLine(80, 960, W - 80, 960, paint(GOLD, split * 0.4, stroke=6, blur=5))
        cv.c.drawLine(80, 960, W - 80, 960, paint(PALE_GOLD, split * 0.9, stroke=1.5))
        draw_text(cv, "CHINA", W / 2, 1060, font("cinzel", 46, 700), PALE_GOLD, a_cn, tracking=0.6)
        draw_text(cv, "平帝", W / 2 - 190, 1215, font("kai", 120), (0.95, 0.9, 0.82), a_cn * 0.75)
        draw_text(cv, "王莽", W / 2 + 160, 1235, font("kai", 170), PALE_GOLD, a_cn, glow=18, glow_rgb=GOLD)
        ac = smooth(seg(t, T.w(28, "boy") - 0.2, T.w(28, "boy") + 0.4))
        draw_text(cv, "a boy emperor · an ambitious regent", W / 2, 1310, font("garamond-italic", 46, 500), IVORY,
                  ac)
        out = out + cv.to_float() * split
    return out


# ----------------------------------------------------------------------------- 11. next year
def s_next(t):
    T = TL()
    img = fx.paper("parchment").copy()
    cv = Canvas.from_float(img)
    fx.dust(cv, t, n=40, alpha=0.3)
    a = smooth(seg(t, T.s(29) - 0.3, T.s(29) + 0.5))
    draw_text(cv, "NEXT YEAR", W / 2, 230, font("cinzel", 40, 700), GOLD, a, tracking=0.6)
    draw_text(cv, "2 AD", W / 2, 380, font("cinzel", 150, 700), PALE_GOLD, a, glow=20)
    lamps = smooth(seg(t, T.s(30) - 0.4, T.s(30) + 0.3))
    ag = a * (1 - lamps)
    if ag > 0:
        tc = T.w(29, "count")
        fill = ease_io(seg(t, tc - 0.2, T.w(29, "million", end=True)))
        cols, rows = 25, 24
        sx, sy = 33.0, 30.0
        x0 = W / 2 - (cols - 1) * sx / 2
        y0 = 560
        n = int(596 * fill)
        for k in range(596):
            r_, c_ = divmod(k, cols)
            lit = k < n
            cv.c.drawCircle(x0 + c_ * sx, y0 + r_ * sy, 7 if lit else 4,
                            paint(PALE_GOLD if lit else IVORY, ag * (0.95 if lit else 0.12)))
        val = int(59_600_000 * fill / 100_000) * 100_000
        draw_text(cv, f"{val:,}", W / 2, 500, font("cinzel", 62, 700), IVORY, ag * smooth(seg(t, tc - 0.2, tc + 0.3)),
                  glow=10)
        draw_text(cv, "HAN CENSUS · ONE DOT = 100,000 PEOPLE", W / 2, y0 + rows * sy + 30, font("cinzel", 28, 600),
                  PALE_GOLD, ag * 0.8, tracking=0.2)
    if lamps > 0:
        tn = T.w(30, "not")
        out_f = 1 - smooth(seg(t, tn + 0.1, tn + 0.9))
        draw_text(cv, "ROME", W / 2, 600, font("cinzel", 46, 700), PALE_GOLD, lamps, tracking=0.6)
        draw_text(cv, "two heirs", W / 2, 660, font("garamond-italic", 46, 500), IVORY, lamps * 0.9)
        fx.oil_lamp(cv, 250, 1060, 1.45 * lamps, 1.0 * lamps, t, seed=1)
        fxp = fx.oil_lamp(cv, 690, 1060, 1.45 * lamps, out_f * lamps, t, seed=2)
        fx.smoke(cv, fxp[0], fxp[1], t, (1 - out_f) * lamps * (1 - smooth(seg(t, tn + 2.5, tn + 4.0))), seed=3)
    return cv.to_float()


# ----------------------------------------------------------------------------- 12. end card
def s_end(t):
    T = TL()
    t0 = T.e(30) + 0.45
    img = fx.paper("parchment").copy() * 0.8
    cv = Canvas.from_float(img)
    fx.dust(cv, t, n=60, alpha=0.4)
    a = smooth(seg(t, t0, t0 + 0.8))
    draw_text(cv, "NEXT EPISODE", W / 2, 760, font("cinzel", 40, 700), GOLD, a, tracking=0.6)
    draw_text_reveal(cv, "2 AD", W / 2, 990, font("cinzel", 240, 700), seg(t, t0 + 0.1, t0 + 1.0), PALE_GOLD,
                     tracking=0.04, glow=28)
    ab = smooth(seg(t, t0 + 0.8, t0 + 1.6))
    draw_text(cv, "YEAR BY YEAR", W / 2, 1150, font("cinzel", 42, 600), IVORY, ab, tracking=0.6)
    draw_text(cv, "the human story, one year at a time", W / 2, 1210, font("garamond-italic", 44, 500), PALE_GOLD,
              ab * 0.9)
    return cv.to_float()
