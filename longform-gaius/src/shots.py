"""The cold open, shot by shot. Every shot returns a scene-linear frame of the active picture
(2.39:1); film.py adds the global finish, letterbox and dissolves.

Times are seconds on the narration timeline (build/timeline.json)."""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np

import post
from post import ease, ease_io, fade

ROOT = Path(__file__).resolve().parents[1]
TL = json.load(open(ROOT / "build" / "timeline.json"))


def word(line_id, w, which=0):
    """Start time of the `which`-th occurrence of word w in line line_id."""
    for l in TL["lines"]:
        if l["id"] == line_id:
            hits = [x for x in l["words"] if x["w"].lower().strip(",.:") == w.lower()]
            return hits[which]["s"]
    raise KeyError((line_id, w))


def lerp(a, b, x):
    return np.asarray(a, float) * (1 - x) + np.asarray(b, float) * x


def smooth_noise(t, seed, freq=1.0):
    """Cheap 1D smooth noise in [-1, 1]."""
    s = 0.0
    for k, (f, a) in enumerate(((1.0, 0.6), (2.3, 0.3), (5.1, 0.1))):
        s += a * math.sin(2 * math.pi * f * freq * t + seed * (1.7 + k) + math.sin(seed * 3.1 + k))
    return s


TORCH_RGB = np.array([1.0, 0.56, 0.24])
TORCH_RGB = TORCH_RGB / (0.2126 * TORCH_RGB[0] + 0.7152 * TORCH_RGB[1] + 0.0722 * TORCH_RGB[2])


def flicker(t, seed=0.0):
    return 0.86 + 0.10 * smooth_noise(t, seed, 3.1) + 0.05 * smooth_noise(t, seed + 9, 9.7)


def label_place(img, t, a, b, title, sub):
    """Place label: lower-left, Cinzel + Garamond italic, a gold hairline above (the film's style)."""
    al = fade(t, a, b, 0.7, 0.7)
    if al <= 0:
        return img
    H, W = img.shape[:2]
    s = W / 3840
    x0, y0 = 0.055 * W, H - 0.20 * H
    grow = ease((t - a) / 1.1)
    hl = int(380 * s * grow)
    y = int(y0 - 64 * s)
    img[y:y + max(1, int(2 * s)), int(x0):int(x0) + hl] = img[y:y + max(1, int(2 * s)), int(x0):int(x0) + hl] * (1 - al) + \
        np.array([0.62, 0.48, 0.24], np.float32) * al
    return post.label(img, [(title, "cinzel", 60, 600, 0.25, post.PALE_GOLD),
                            (sub, "garamond-italic", 54, 500, 0.0, (0.96, 0.93, 0.86))], 0.055, 0.80, al)


def label_source(img, t, a, b, text):
    al = fade(t, a, b, 0.7, 0.7) * 0.85
    if al <= 0:
        return img
    return post.label(img, [(text, "cinzel", 38, 500, 0.18, (0.96, 0.93, 0.86))], 0.945, 0.93, al, align="right",
                      level=0.45)


# =============================================================================== A. aerial
@lru_cache(maxsize=1)
def _terrain():
    import terrain_night
    return terrain_night.Terrain()


def shot_aerial(t, W, H, frame):
    import sdf
    T = _terrain()
    a, b = 0.0, 6.9
    x = ease_io((t - a) / (b - a))
    pos = lerp((-3400, 3900, -17500), (-1300, 1650, -7200), x)
    tgt = lerp((200, 250, 2500), (0, 60, 0), x)
    cam = sdf.look_at(pos, tgt, W * lerp(0.80, 0.98, x).item(), roll=0.012 * math.sin(t * 0.4))
    md = np.array([0.80, 0.36, -0.48])
    md /= np.linalg.norm(md)
    moon = np.array([*md, 0.30, 0.36, 0.52])
    g = ease((t - 1.6) / 2.5) * flicker(t, 2.0)
    glow = np.array([0.0, 25.0, 0.0, 9.0 * g, 4.9 * g, 1.9 * g, 0.0011])
    img, dep = T.render(W, H, cam, moon, glow, frame)
    img = label_place(img, t, word("l1", "coast") - 0.2, 6.5, "LIMYRA", "Lycia, on the southern coast of Turkey · today")
    img = label_source(img, t, 1.0, 6.5, "Copernicus Sentinel-2 & WorldDEM-30")
    return img, dep, dict(focus=1e9, coc=0.0)


# =============================================================================== B / G. ruins
@lru_cache(maxsize=1)
def _ruins():
    import scene_limyra as S
    B = S.baked()
    return S, B, S.relief_panels()


def figure_for(torch_pos, heading, phase, sway=0.0):
    """Place the cloaked torchbearer so his raised right hand holds the torch at torch_pos.
    Returns (fig array for sdf.render, handle vector from the flame base to the hand and beyond)."""
    c, s_ = math.cos(heading), math.sin(heading)

    def to_world(lx, lz):
        return c * lx + s_ * lz, -s_ * lx + c * lz

    ox, oz = to_world(0.27, 0.42)
    feet = (torch_pos[0] - ox, torch_pos[2] - oz)
    hx, hz = to_world(0.25, 0.34)
    hand = np.array([feet[0] + hx, 1.30, feet[1] + hz])
    hv = hand - np.asarray(torch_pos, float)
    hv = hv / np.linalg.norm(hv) * 0.52
    return np.array([feet[0], feet[1], heading, phase, sway, 1.0]), hv


NOFIG = np.zeros(6)


@lru_cache(maxsize=1)
def _tufts():
    import grass
    S, B, panels = _ruins()
    return grass.tufts(B)


def _ruins_frame(t, W, H, frame, cam, torch_pos, torch_I, embers_seed, focus, coc, moon_I=1.0, flame_on=True,
                 lean=0.0, fig=None, handle_vec=None):
    import sdf
    S, B, panels = _ruins()
    tc = TORCH_RGB * torch_I
    light = np.asarray(torch_pos) + np.array([0, 0.14, 0])
    torch = np.array([*light, *tc, 0.06, 0.00045, 0.035])
    md = np.array([0.62, 0.42, -0.55])
    md /= np.linalg.norm(md)
    moon = np.array([*md, 0.020 * moon_I, 0.030 * moon_I, 0.055 * moon_I])
    sky = np.array([0.0025, 0.0040, 0.0080, 0.010, 0.013, 0.022])
    fog = np.array([0.03, 0.6, -0.012])
    jit = np.array([0.0, 0.0, 1.0])
    img, dep = sdf.render(W, H, cam, B.dist, B.pid, B.coarse, B.G, B.gh, B.GH, B.prims, S.MATS, panels,
                          torch, moon, sky, fog, frame, jit, NOFIG if fig is None else fig)
    import grass
    grass.draw(img, dep, cam, B, _tufts(), t, torch, moon)
    img = post.dof(img, dep, focus, coc)
    # torch handle (dark stick under the flame) and the flame itself
    if flame_on and torch_I > 0.02:
        k = min(1.0, torch_I / 5.0)
        post.flame(img, dep, cam, torch_pos, t, height_m=0.34 * (0.4 + 0.6 * k), gain=9.0 * k,
                   lean=lean, seed=embers_seed * 3.7, I=k, handle_vec=handle_vec)
    # embers
    if torch_I > 0.05:
        P, C = _embers(t, torch_pos, embers_seed, torch_I / 5.0)
        if len(P):
            post.particles(img, dep, cam, P, C, coc_strength=coc, focus=focus)
    # dust motes lit by the torch
    P, C = _motes(t, light, tc, cam, seed=embers_seed)
    post.particles(img, dep, cam, P, C, coc_strength=coc, focus=focus)
    return img, dep


def _embers(t, base, seed, strength):
    rng = np.random.default_rng(int(seed) + 77)
    n = 70
    rate = 14.0                   # embers per second
    life = rng.uniform(0.8, 2.2, n)
    phase = rng.uniform(0, n / rate, n)
    v0 = rng.normal(0, 1, (n, 3)) * [0.10, 0.12, 0.10] + [0.0, 0.55, 0.0]
    P, C = [], []
    for k in range(n):
        age = (t - phase[k]) % (n / rate)
        if age > life[k]:
            continue
        a = age
        drift = np.array([0.18 * a + 0.05 * math.sin(3.1 * a + k), 0.0, 0.06 * math.sin(2.3 * a + k * 1.3)])
        p = np.asarray(base) + np.array([0, 0.22, 0]) + v0[k] * a + np.array([0, 0.35 * a * a, 0]) * 0.5 + drift
        heat = max(0.0, 1.0 - a / life[k])
        tw = 0.6 + 0.4 * math.sin(a * 23.0 + k)
        I = 2.2 * heat ** 1.5 * tw * strength
        P.append(p)
        C.append([I, I * 0.42 * heat, I * 0.08 * heat])
    return np.array(P).reshape(-1, 3), np.array(C).reshape(-1, 3)


@lru_cache(maxsize=4)
def _mote_field(seed, n=1400):
    rng = np.random.default_rng(seed)
    P = rng.uniform([-3.0, 0.1, -3.0], [3.0, 3.0, 16.0], (n, 3))
    ph = rng.uniform(0, 6.28, (n, 3))
    sz = rng.uniform(0.3, 1.0, n)
    return P, ph, sz


def _motes(t, light, tc, cam, seed=0):
    P0, ph, sz = _mote_field(int(seed) % 4)
    drift = np.stack([0.05 * np.sin(0.21 * t + ph[:, 0]) + 0.02 * t,
                      0.04 * np.sin(0.17 * t + ph[:, 1]) - 0.004 * t,
                      0.05 * np.sin(0.13 * t + ph[:, 2])], 1)
    P = P0 + drift
    d = P - light
    r2 = (d * d).sum(1) + 0.05
    # forward-scattering phase: brighter when the mote sits between camera and light
    v = P - cam[0:3]
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    l = -d / np.sqrt(r2)[:, None]
    cosang = (v * l).sum(1)
    phase = 0.35 + 1.4 * np.clip(cosang, 0, 1) ** 4
    I = 0.0016 * sz * phase / r2
    C = I[:, None] * tc[None, :]
    keep = I > 1e-5
    return P[keep], C[keep]


def shot_approach(t, W, H, frame):
    import sdf
    a, b = 5.6, 11.5
    x = ease_io((t - a) / (b - a))
    step_hz = 0.9
    bob = 0.022 * math.sin(2 * math.pi * step_hz * t)
    sway = 0.03 * smooth_noise(t, 1.0, 0.25)
    cpos = lerp((0.55, 1.20, -1.9), (0.10, 1.12, 4.9), x) + np.array([sway, bob, 0])
    tgt = lerp((-0.3, 1.35, 12.0), (0.1, 1.55, 15.0), x)
    tgt = tgt + np.array([0, 0.22 * ease((t - word("l1", "tomb") + 0.6) / 2.0), 0])
    cam = sdf.look_at(cpos, tgt, W * 0.95, roll=0.008 * smooth_noise(t, 3.0, 0.3))
    # the cloaked torchbearer walks a few paces ahead, left of the path, torch held high on his right
    xf = ease_io((t - a + 0.3) / (b - a))
    tp = lerp((-0.25, 1.63, 2.4), (-0.05, 1.60, 9.3), xf)
    phase = 2 * math.pi * step_hz * t
    tp = tp + np.array([0.012 * math.sin(phase), 0.018 * abs(math.sin(phase)), 0])
    fig, hv = figure_for(tp, 0.04, phase, sway=0.02 * math.sin(phase * 0.5))
    I = 5.0 * flicker(t, 1.0)
    focus = float(np.linalg.norm(np.asarray(tp) - cpos))
    img, dep = _ruins_frame(t, W, H, frame, cam, tp, I, 1, focus, coc=W * 0.004, lean=0.12, fig=fig, handle_vec=hv)
    img = label_place(img, t, word("l1", "stands") - 0.3, 11.0, "THE CENOTAPH OF GAIUS CAESAR",
                      "Limyra · its ruins today, as an illustration")
    return img, dep, dict(focus=focus, coc=W * 0.004)


def shot_gutter(t, W, H, frame):
    import sdf
    a, b = 28.6, 38.3
    x = ease_io((t - a) / (b - a))
    cpos = lerp((0.9, 0.85, -2.6), (0.7, 0.95, -1.5), x) + np.array([0, 0.006 * math.sin(t * 0.8), 0])
    cam = sdf.look_at(cpos, (-0.1, 1.85, 14.0), W * 0.9)
    tw = word("l5", "walk") - 0.05
    th = word("l6", "home")
    # standing, torch raised, until "walk"; then he walks away down the path
    w = ease((t - tw) / 0.8) * 0.15 + 0.85 * ease_io((t - tw - 0.25) / (th - tw + 0.6))
    step_hz = 0.85
    moving = ease((t - tw) / 0.4)
    phase = 2 * math.pi * step_hz * max(t - tw, 0.0)
    tp = lerp((-0.55, 1.63, 1.9), (0.05, 1.60, 7.6), w)
    tp = tp + np.array([0.012 * math.sin(phase), 0.018 * abs(math.sin(phase)) * moving, 0])
    fig, hv = figure_for(tp, 0.08, phase, sway=0.02 * math.sin(phase * 0.5) * moving)
    # the light gutters and dies on "home"
    die = 1.0 - ease((t - (th - 0.9)) / 1.15)
    gut = 1.0
    if t > th - 1.4:
        gut = 0.65 + 0.35 * abs(math.sin(t * 31.0)) * abs(math.sin(t * 13.0 + 1))
    I = 5.0 * flicker(t, 4.0) * die * (gut if die < 1.0 else 1.0)
    focus = 6.0
    img, dep = _ruins_frame(t, W, H, frame, cam, tp, I, 3, focus, coc=W * 0.0025, moon_I=1.25, flame_on=I > 0.05,
                            lean=-0.12 * moving, fig=fig, handle_vec=hv)
    return img, dep, dict(focus=focus, coc=W * 0.0025)


# =============================================================================== C / D. portraits
CROPS = {"3_met_possibly-gaius-caesar_head_three-quarter-dark": (0, 3080, 0, 3000),
         "3_met_possibly-gaius-caesar_head_front-dark": (0, 3080, 0, 3000)}
TORCH_P = 0.70 * TORCH_RGB + 0.30


@lru_cache(maxsize=2)
def _portrait(name):
    import portrait
    R, b = portrait.relief(name, crop=CROPS.get(name))
    return R


def _portrait_frame(t, W, H, frame, name, cpos, tgt, focal, torch_pos, torch_I, rim, seed, sss=0.35):
    import sdf
    R = _portrait(name)
    cam = sdf.look_at(cpos, tgt, focal)
    tc = TORCH_P * torch_I
    fill_pos = (-torch_pos[0] * 0.8, -0.15, -0.55)
    lights = [(*torch_pos, *tc, 0.05, 1), (*fill_pos, *(np.array([0.55, 0.65, 0.9]) * 0.013), 0.2, 0)]
    img, dep, al = R.render(W, H, cam, lights, key=rim, ambient=(0.0016, 0.0020, 0.0032),
                            mat=[0.10, 30, 0, 60, 0, sss, 1, 0.8], seed=frame)
    img = post.dof(img, dep, float(np.linalg.norm(np.asarray(tgt) - np.asarray(cpos))), W * 0.003)
    # dust drifting through the light in front of the sculpture
    P0, ph, sz = _mote_field(seed + 10, 700)
    P = (P0 - np.array([0, 1.5, 6.0])) * np.array([0.12, 0.14, 0.05]) + np.array([0, 0, -0.25])
    P = P + np.stack([0.006 * np.sin(0.3 * t + ph[:, 0]) + 0.004 * t, 0.004 * np.sin(0.2 * t + ph[:, 1]),
                      0.004 * np.sin(0.25 * t + ph[:, 2])], 1)
    d = P - np.asarray(torch_pos)
    r2 = (d * d).sum(1) + 0.002
    C = (0.00002 * sz / r2)[:, None] * tc[None, :]
    focus = float(np.linalg.norm(np.asarray(tgt) - np.asarray(cpos)))
    post.particles(img, dep, cam, P, C, coc_strength=W * 0.006, focus=focus)
    return img, dep, dict(focus=focus, coc=W * 0.003)


YOUTH = "3_met_possibly-gaius-caesar_head_front-dark"


def shot_youth(t, W, H, frame):
    a, b = 10.9, 16.5
    x = ease_io((t - a) / (b - a))
    ang = lerp(-0.07, 0.07, x).item()
    r = lerp(1.22, 1.02, x).item()
    cpos = (math.sin(ang) * r + 0.02, 0.01, -math.cos(ang) * r)
    tgt = (-0.05, -0.04, 0.0)
    # torch drifts from right to left, low, as if carried past
    lx = lerp(0.55, -0.40, ease_io((t - a) / (b - a + 0.5))).item()
    tp = (lx, 0.02 + 0.03 * math.sin(t * 0.7), -0.42)
    I = 0.075 * flicker(t, 5.0) * ease((t - a) / 1.2)
    img, dep, info = _portrait_frame(t, W, H, frame, YOUTH, cpos, tgt,
                                     W * 1.30, tp, I, (0.55, 0.35, 0.75, 0.009, 0.013, 0.024), 1, sss=0.6)
    img = label_place(img, t, word("l2", "young") - 0.2, b - 0.6, "POSSIBLY GAIUS CAESAR",
                      "alabaster head of a young man, c. 5 BC or later")
    img = label_source(img, t, word("l2", "young") - 0.2, b - 0.6, "The Metropolitan Museum of Art · CC0")
    return img, dep, info


def shot_augustus(t, W, H, frame):
    a, b = 15.9, 22.2
    x = ease_io((t - a) / (b - a))
    ang = lerp(0.09, -0.05, x).item()
    r = lerp(1.25, 1.04, x).item()
    cpos = (math.sin(ang) * r + 0.03, 0.03, -math.cos(ang) * r)
    tgt = (0.06, 0.0, 0.0)
    lx = lerp(-0.55, 0.30, ease_io((t - a) / (b - a))).item()
    tp = (lx, 0.10 + 0.02 * math.sin(t * 0.9), -0.40)
    I = 0.075 * flicker(t, 6.0) * ease((t - a) / 1.0)
    img, dep, info = _portrait_frame(t, W, H, frame, "3_met_augustus_marble-portrait_07-286-115_dark", cpos, tgt,
                                     W * 1.30, tp, I, (-0.6, 0.3, 0.75, 0.008, 0.012, 0.022), 2)
    img = label_place(img, t, word("l3", "Augustus") - 0.15, b - 0.5, "AUGUSTUS", "his grandfather · portrait carved after his death")
    img = label_source(img, t, word("l3", "Augustus") - 0.15, b - 0.5, "The Metropolitan Museum of Art · CC0")
    return img, dep, info


# =============================================================================== E. titles carved
@lru_cache(maxsize=1)
def _titles_slab():
    import carve
    # 4800 x 2800 px over 2.53 m (1900 px/m); baselines 0.25 m apart so all three lines share the frame
    b = carve.slab(4800, 2800, 4800 / 1900, [("C · CAESAR", "cinzel", 220, 700, 1000, 0.10),
                                            ("PRINC · IVVENT", "cinzel", 220, 700, 1475, 0.10),
                                            ("COS · DESIG", "cinzel", 220, 700, 1950, 0.10)], gold=1.0, seed=8,
                   base=(0.70, 0.66, 0.59), marble=True)
    return b, carve.relief_object(b)


def shot_titles(t, W, H, frame):
    import sdf
    b, R = _titles_slab()
    a, e = 21.8, 25.6
    tn, tt_, tf = word("l3", "name"), word("l3", "titles"), word("l3", "future")
    base = [(1400 - y) / 1900 for y in (1000, 1475, 1950)]
    mid = [y + 0.041 for y in base]
    x = ease_io((t - a) / (e - a))
    cy = lerp(0.02, -0.03, x).item()
    cpos = (lerp(-0.10, 0.08, x).item(), cy + 0.05, lerp(-2.15, -1.95, x).item())
    cam = sdf.look_at(cpos, (0.0, cy, 0.0), W * 0.88)
    # one torch reads the inscription like an eye: line 1 left to right, line 2 back, line 3 across
    keys = [(a, -1.5, mid[0]), (tn - 0.30, -0.95, mid[0]), (tn + 0.62, 0.92, mid[0]), (tt_ - 0.12, 0.95, mid[1]),
            (tt_ + 0.62, -0.92, mid[1]), (tf - 0.12, -0.95, mid[2]), (tf + 0.62, 0.92, mid[2]), (e + 0.4, 1.35, mid[2])]
    lx, ly = keys[-1][1], keys[-1][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(keys[:-1], keys[1:]):
        if t0 <= t < t1:
            u = ease_io((t - t0) / (t1 - t0))
            lx, ly = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
            break
    I = 0.12 * flicker(t, 7.0) * ease((t - a) / 0.4)
    lights = [(lx, ly + 0.17, -0.30, *(TORCH_RGB * I), 0.05, 1)]
    env = [0.02, 0.017, 0.014, 0.0, 0.0, 0.0, lx * 0.5, 0.5, -0.7, 1.6, 1.1, 0.5, 4.0]
    img, dep, al = R.render(W, H, cam, lights, key=(0, 0, 0, 0, 0, 0), ambient=(0.0010, 0.0011, 0.0015),
                            mat=[0.03, 12, 3.0, 40, 0, 0.1, 1.0, 0.74], seed=frame, env=env)
    img = post.dof(img, dep, 2.05, W * 0.004)
    # the plain meaning, set under each line as it is read, and left there
    tr = [("Gaius Caesar", tn), ("Prince of Youth", tt_), ("consul-elect", tf)]
    for (txt, ts), yb in zip(tr, base):
        p = post.project(cam, (0.0, yb - 0.065, -0.012))
        if p is None:
            continue
        yy = (p[1] + H / 2) / H
        al_ = fade(t, ts + 0.12, e - 0.25, 0.4, 0.3)
        img = post.label(img, [(txt, "garamond-italic", 74, 500, 0.02, (0.97, 0.94, 0.86))], 0.5, yy, al_,
                         align="center", level=0.60, backing=0.55)
    img = label_source(img, t, tn - 0.2, e - 0.45, "as on his coins and inscriptions · illustration")
    return img, dep, dict(focus=2.05, coc=W * 0.004)


# =============================================================================== F. the coin
@lru_cache(maxsize=1)
def _coin_build():
    import coin
    return coin.build()


def shot_coin(t, W, H, frame):
    import coin
    import hfr
    import sdf
    a, e = 25.2, 29.0
    x = ease_io((t - a) / (e - a))
    yaw = lerp(-0.55, 0.20, x).item()
    pitch = lerp(0.22, 0.05, x).item()
    b = _coin_build()
    R = _coin_relief(round(yaw, 4), round(pitch, 4))
    cpos = (0.003, 0.002, lerp(-0.050, -0.036, x).item())
    cam = sdf.look_at(cpos, (0.0, -0.0006, 0.0), W * 0.86)
    tn = word("l4", "name")
    lx = lerp(-0.06, 0.05, ease_io((t - a) / (e - a))).item()
    tp = (lx, 0.035, -0.04)
    I = 0.0042 * flicker(t, 8.0) * ease((t - a) / 0.6)
    # a second, cool light rakes across the legend as "name" is spoken
    sweep = ease_io((t - tn + 0.2) / 1.2)
    lights = [(*tp, *(TORCH_RGB * I), 0.004, 1),
              (lerp(-0.05, 0.05, sweep).item(), -0.02, -0.02, *(np.array([0.7, 0.8, 1.0]) * 0.0016 * fade(t, tn - 0.3, tn + 1.4, 0.4, 0.5)), 0.003, 1)]
    env = [0.05, 0.06, 0.08, 0.004, 0.004, 0.005, -0.4, 0.7, -0.6, 0.6, 0.7, 0.85, 12.0]
    img, dep, al = R.render(W, H, cam, lights, key=(0.5, 0.6, 0.6, 0.012, 0.018, 0.03), ambient=(0.003, 0.0035, 0.005),
                            mat=[0.0, 30, 1.6, 120, 0, 0.0, 0.92, 0.95], seed=frame, env=env)
    img = post.dof(img, dep, float(np.linalg.norm(cpos)), W * 0.003)
    img = label_place(img, t, 25.7, e - 0.4, "SILVER DENARIUS", "struck c. 2 BC – 4 AD · illustration")
    img = label_source(img, t, 25.7, e - 0.4, "C · L · CAESARES  — Gaius and Lucius")
    return img, dep, dict(focus=0.04, coc=W * 0.003)


_COIN_CACHE = {}


def _coin_relief(yaw, pitch):
    import coin
    import hfr
    b = _coin_build()
    key = "base"
    if key not in _COIN_CACHE:
        _COIN_CACHE[key] = hfr.Relief(b["hm"], b["albedo"], (0, 0, 0), (1, 0, 0), (0, -1, 0), (0, 0, -1), b["texel"], 1.0,
                                      matmap=b["matmap"])
        _COIN_CACHE[key].hmin = 0.0
    R = _COIN_CACHE[key]
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    u = np.array([cy, 0, sy])
    n0 = -np.array([-sy, 0, cy])
    v0 = np.array([0, -1.0, 0])
    v = v0 * cp + n0 * sp
    n = n0 * cp - v0 * sp
    R.u, R.v, R.n = u, v, n
    R.o = -u * (b["size"] / 2) * b["texel"] - v * (b["size"] / 2) * b["texel"]
    return R


# =============================================================================== H. the title
@lru_cache(maxsize=1)
def _title_slab():
    import carve
    # 1533 px/m: 6440 x 2600 px = 4.2 x 1.7 m, larger than the frame throughout the push
    b = carve.slab(6440, 2600, 4.2, [("GAIUS CAESAR", "cinzel", 400, 700, 1280, 0.10),
                                    ("THE HEIR WHO NEVER CAME HOME", "cinzel", 112, 600, 1600, 0.30)], gold=1.0, seed=4)
    return b, carve.relief_object(b)


def shot_title(t, W, H, frame):
    import sdf
    b, R = _title_slab()
    a, e = 37.9, 48.2
    x = ease_io((t - a) / (e - a))
    cpos = (lerp(-0.10, 0.06, x).item(), lerp(-0.02, 0.0, x).item(), lerp(-3.05, -2.75, x).item())
    cam = sdf.look_at(cpos, (0.0, 0.03, 0.0), W * 1.0)
    tg = word("l7", "Gaius")
    # the light: a faint glow on "This", then it travels across the letters on "Gaius", then settles
    sweep = ease_io((t - tg + 0.35) / 2.4)
    lx = lerp(-1.9, 1.1, sweep).item()
    rise = ease((t - word("l7", "This") + 0.2) / 1.2)
    I = (0.12 + 0.88 * ease((t - tg + 0.6) / 0.7)) * rise * 0.45 * flicker(t, 9.0)
    tp = (lx, 0.55, -0.50)
    lights = [(*tp, *(TORCH_RGB * I), 0.07, 1)]
    env = [0.03, 0.025, 0.02, 0.0, 0.0, 0.0, lx * 0.5, 0.5, -0.7, 2.8, 1.9, 0.85, 4.0]
    img, dep, al = R.render(W, H, cam, lights, key=(0, 0, 0, 0, 0, 0), ambient=(0.0008, 0.0009, 0.0013),
                            mat=[0.03, 12, 3.2, 40, 0, 0.1, 1.0, 0.74], seed=frame, env=env)
    img = post.dof(img, dep, 2.9, W * 0.0025)
    # gold dust drifting through the beam
    P0, ph, sz = _mote_field(7, 900)
    P = (P0 - np.array([0, 1.5, 6.0])) * np.array([0.6, 0.45, 0.08]) + np.array([0, 0.1, -0.5])
    P = P + np.stack([0.03 * np.sin(0.2 * t + ph[:, 0]) + 0.01 * t, 0.02 * np.sin(0.15 * t + ph[:, 1]) + 0.004 * t,
                      0.01 * np.sin(0.3 * t + ph[:, 2])], 1)
    d = P - np.asarray(tp)
    r2 = (d * d).sum(1) + 0.01
    C = (0.0005 * sz / r2)[:, None] * (TORCH_RGB * I)[None, :]
    post.particles(img, dep, cam, P, C, coc_strength=W * 0.005, focus=2.9)
    # series tag and dates, after the line has landed
    tl = word("l8", "choice") + 0.4
    img = post.label(img, [("20 BC – 4 AD", "garamond-italic", 70, 500, 0.02, post.PALE_GOLD)], 0.5, 0.86,
                     fade(t, word("l8", "the") + 0.2, 48.6, 0.9, 0.9), align="center", level=0.5)
    img = post.label(img, [("YEAR BY YEAR", "cinzel", 46, 600, 0.5, post.PALE_GOLD)], 0.5, 0.11,
                     fade(t, tl, 48.6, 1.0, 0.9), align="center", level=0.5)
    return img, dep, dict(focus=2.2, coc=W * 0.0025)


# =============================================================================== the edit
# (shot, start, end) — overlaps are dissolves
EDIT = [
    (shot_aerial, 0.0, 6.6),
    (shot_approach, 5.8, 11.5),
    (shot_youth, 10.95, 16.5),
    (shot_augustus, 15.95, 22.25),
    (shot_titles, 21.8, 25.6),
    (shot_coin, 25.2, 29.05),
    (shot_gutter, 28.6, 38.3),
    (shot_title, 37.9, 48.2),
]
DURATION = 48.2
