"""Cinematic post in scene-linear light: lens blur, bloom, anamorphic glare, the torch flame,
embers, dust motes, film grain, vignette and on-screen labels. All sizes scale with frame width
so a 1080p draft and the 4K master look the same."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import cv2
import numpy as np
from numba import njit, prange

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "year-1-ad" / "src"))
import gfx  # noqa: E402
from gfx import Canvas  # noqa: E402

PALE_GOLD = (0.93, 0.84, 0.62)


# ============================================================================ projection
def project(cam, p):
    """World point -> (x_px, y_px, depth) for the sdf/hfr camera convention (W/2,H/2 centre added by caller)."""
    o, f, r, u, fp = cam[0:3], cam[3:6], cam[6:9], cam[9:12], cam[12]
    d = np.asarray(p, float) - o
    z = d @ f
    if z <= 1e-6:
        return None
    return (d @ r) / z * fp, -(d @ u) / z * fp, float(np.linalg.norm(d))


# ============================================================================ lens blur
def _disc(r):
    r = max(1, int(round(r)))
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    k = np.clip(r + 0.5 - np.sqrt(x * x + y * y), 0, 1).astype(np.float32)
    return k / k.sum()


def _blur_disc(img, r):
    if r < 0.75:
        return img
    if r <= 6:
        return cv2.filter2D(img, -1, _disc(r), borderType=cv2.BORDER_REFLECT)
    f = r / 6.0
    h, w = img.shape[:2]
    small = cv2.resize(img, (max(1, int(w / f)), max(1, int(h / f))), interpolation=cv2.INTER_AREA)
    small = cv2.filter2D(small, -1, _disc(6), borderType=cv2.BORDER_REFLECT)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)


def dof(img, depth, focus, strength, max_r=None):
    """Thin-lens blur. strength = CoC radius in px (at this width) for an object at infinity
    when focused at `focus`; CoC = strength * |1 - focus/depth|."""
    W = img.shape[1]
    if strength <= 0:
        return img
    max_r = max_r or W * 0.012
    coc = np.clip(strength * np.abs(1.0 - focus / np.maximum(depth, 1e-3)), 0, max_r).astype(np.float32)
    # let foreground blur bleed: dilate the CoC of near pixels
    near = (depth < focus).astype(np.float32) * coc
    near = cv2.dilate(near, np.ones((5, 5), np.uint8))
    near = cv2.GaussianBlur(near, (0, 0), max(1.0, max_r * 0.3))
    coc = np.maximum(coc, near)
    levels = [0.0, 1.5, 3.0, 5.5, 9.0, 14.0, 22.0, 34.0, 52.0]
    levels = [l for l in levels if l <= max_r * 1.05] + ([max_r] if max_r > 52 else [])
    out = np.zeros_like(img)
    blurred = [img if l == 0 else _blur_disc(img, l) for l in levels]
    for k in range(len(levels) - 1):
        a, b = levels[k], levels[k + 1]
        w = np.clip((coc - a) / (b - a), 0, 1)
        sel = ((coc >= a) & (coc < b)) | ((k == len(levels) - 2) & (coc >= b))
        w = np.where(sel, w, 0)[..., None]
        out += np.where(sel[..., None], blurred[k] * (1 - w) + blurred[k + 1] * w, 0)
    return out


# ============================================================================ bloom / glare
def bloom(img, amount=0.05, radius_frac=(0.002, 0.006, 0.016, 0.04)):
    W = img.shape[1]
    acc = np.zeros_like(img)
    wsum = 0.0
    for k, rf in enumerate(radius_frac):
        s = rf * W
        f = max(1, int(s / 3))
        small = cv2.resize(img, (img.shape[1] // f, img.shape[0] // f), interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (0, 0), s / f)
        acc += cv2.resize(small, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR) * (0.6 ** k)
        wsum += 0.6 ** k
    return img * (1 - amount) + acc / wsum * amount


def glare(img, threshold=2.5, amount=0.06, length_frac=0.18, tint=(1.0, 0.85, 0.7)):
    """Horizontal streak from the brightest highlights (anamorphic-style, kept subtle)."""
    W = img.shape[1]
    lum = img.max(axis=2)
    bright = img * np.clip((lum - threshold) / threshold, 0, 4)[..., None]
    if bright.max() <= 0:
        return img
    f = 4
    small = cv2.resize(bright, (img.shape[1] // f, img.shape[0] // f), interpolation=cv2.INTER_AREA)
    L = int(length_frac * W / f) | 1
    k = np.exp(-np.abs(np.linspace(-3, 3, L))).astype(np.float32)
    k /= k.sum()
    streak = cv2.filter2D(small, -1, k[None, :])
    streak = cv2.GaussianBlur(streak, (0, 0), 1.0)
    streak = cv2.resize(streak, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    return img + streak * amount * np.asarray(tint, np.float32)


# ============================================================================ sprites (flame, embers, motes)
@njit(cache=True, inline="always")
def _h(i, j, s):
    h = (i * 374761393 + j * 668265263 + s * 1440662683) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFF) / 16777215.0


@njit(cache=True)
def _vn(x, y):
    ix, iy = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - ix, y - iy
    ux, uy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = _h(ix, iy, 3), _h(ix + 1, iy, 3), _h(ix, iy + 1, 3), _h(ix + 1, iy + 1, 3)
    return a + (b - a) * ux + (c - a) * uy + (a - b - c + d) * ux * uy


@njit(cache=True)
def _fbm2(x, y, o):
    s, a, t = 0.0, 0.5, 0.0
    for _ in range(o):
        s += a * _vn(x, y)
        t += a
        x, y = x * 2.05 + 1.3, y * 2.05 - 0.7
        a *= 0.5
    return s / t


@njit(cache=True, parallel=True)
def _flame(img, depth, cx, cy, d, size_px, t, gain, lean, seed):
    """Turbulent torch flame rising from (cx, cy), height size_px, depth-tested, additive HDR."""
    H, W = depth.shape
    x0, x1 = int(cx - size_px * 0.8), int(cx + size_px * 0.8)
    y0, y1 = int(cy - size_px * 1.35), int(cy + size_px * 0.10)
    for y in prange(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            if depth[y, x] < d - 0.05:
                continue
            v = (cy - y) / size_px
            u = (x - cx) / size_px
            if v < -0.06 or v > 1.3:
                continue
            tv = max(v, 0.0)
            # sideways turbulence grows with height; the whole flame leans with motion / wind
            sw = (_fbm2(tv * 2.2 - t * 2.6 + seed, t * 0.9 + seed, 3) - 0.5) * 0.55
            uu = u - sw * tv ** 1.1 - lean * tv * tv
            width = 0.24 * (1.0 - min(tv / 1.15, 1.0)) ** 0.55 * (0.55 + 0.45 * min(tv * 5.0 + 0.25, 1.0))
            if width <= 1e-4:
                continue
            q = abs(uu) / width
            env = max(0.0, 1.0 - q * q)
            if env <= 0.0:
                continue
            # rising billows: noise advected upward breaks the top into tongues
            n = _fbm2(uu * 6.0 + seed, tv * 4.0 - t * 5.0, 4)
            dens = env * (0.45 + 0.95 * n) - 0.55 * tv
            if v < 0.0:
                dens *= (1.0 + v / 0.06)
            if dens <= 0.0:
                continue
            dens = min(dens, 1.0)
            temp = dens * (1.0 - 0.45 * tv)
            I = gain * dens ** 1.3
            r = I * (0.9 + 2.2 * temp * temp)
            g = I * (0.30 + 1.9 * temp * temp * temp + 0.25 * temp)
            b = I * (0.04 + 1.1 * temp ** 4)
            img[y, x, 0] += r
            img[y, x, 1] += g
            img[y, x, 2] += b


@njit(cache=True, parallel=True)
def _stick(img, depth, ax, ay, ad, bx, by, bd, wa, wb, col_r, col_g, col_b, glow):
    """A tapered dark rod from screen point A (top) to B (bottom), depth-tested, lit from the top."""
    H, W = depth.shape
    x0 = int(max(0, min(ax, bx) - max(wa, wb) - 2))
    x1 = int(min(W, max(ax, bx) + max(wa, wb) + 3))
    y0 = int(max(0, min(ay, by) - max(wa, wb) - 2))
    y1 = int(min(H, max(ay, by) + max(wa, wb) + 3))
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy + 1e-9
    for y in prange(y0, y1):
        for x in range(x0, x1):
            s = ((x - ax) * vx + (y - ay) * vy) / L2
            if s < 0.0 or s > 1.0:
                continue
            px, py = ax + s * vx, ay + s * vy
            w = wa + (wb - wa) * s
            dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
            if dist > w + 1.0:
                continue
            dd = ad + (bd - ad) * s
            if depth[y, x] < dd:
                continue
            cov = min(1.0, w + 1.0 - dist)
            across = dist / max(w, 0.5)
            lit = glow * (1.0 - s) ** 3 * (1.0 - 0.6 * across)
            r = col_r * (0.4 + 0.6 * (1 - across)) + lit
            g = col_g * (0.4 + 0.6 * (1 - across)) + lit * 0.45
            b = col_b * (0.4 + 0.6 * (1 - across)) + lit * 0.12
            img[y, x, 0] = img[y, x, 0] * (1 - cov) + r * cov
            img[y, x, 1] = img[y, x, 1] * (1 - cov) + g * cov
            img[y, x, 2] = img[y, x, 2] * (1 - cov) + b * cov


@njit(cache=True)
def _splat(img, depth, xs, ys, ds, rad, cols, n):
    """Soft discs (bokeh-ish) for particles, depth tested, additive."""
    H, W = depth.shape
    for k in range(n):
        x, y, d, r = xs[k], ys[k], ds[k], rad[k]
        R = int(r * 2.0) + 2
        xi, yi = int(x), int(y)
        if xi < -R or yi < -R or xi >= W + R or yi >= H + R:
            continue
        norm = 1.0 / (1.0 + r * r * 0.9)
        for yy in range(max(0, yi - R), min(H, yi + R + 1)):
            for xx in range(max(0, xi - R), min(W, xi + R + 1)):
                if depth[yy, xx] < d:
                    continue
                q = math.sqrt((xx - x) ** 2 + (yy - y) ** 2) / max(r, 0.6)
                w = max(0.0, 1.0 - q * q) if r > 2.0 else math.exp(-q * q * 2.0)
                if w <= 0:
                    continue
                w *= norm
                img[yy, xx, 0] += cols[k, 0] * w
                img[yy, xx, 1] += cols[k, 1] * w
                img[yy, xx, 2] += cols[k, 2] * w


def flame(img, depth, cam, pos, t, height_m=0.34, gain=10.0, lean=0.0, seed=0.0, handle=True, I=1.0, handle_vec=None):
    """A burning torch: tapered wooden handle, pitch-soaked head, turbulent flame. pos = flame base."""
    H, W = depth.shape
    p = project(cam, pos)
    if p is None:
        return
    sx, sy, d = p
    cx, cy = sx + W / 2, sy + H / 2
    fp = cam[12]
    if handle:
        top = np.asarray(pos, float) + np.array([0.0, -0.01, 0.0])
        head_b = top + np.array([0.0, -0.11, 0.0])
        bot = top + (np.array([0.06, -0.85, -0.10]) if handle_vec is None else np.asarray(handle_vec, float))
        A, Bh, Bb = project(cam, top), project(cam, head_b), project(cam, bot)
        if A and Bh and Bb:
            # head: thick, charred, glowing at the top
            _stick(img, depth, A[0] + W / 2, A[1] + H / 2, A[2], Bh[0] + W / 2, Bh[1] + H / 2, Bh[2],
                   fp * 0.034 / A[2], fp * 0.026 / Bh[2], 0.012 * I, 0.006 * I, 0.003 * I, 0.9 * I)
            # handle
            _stick(img, depth, Bh[0] + W / 2, Bh[1] + H / 2, Bh[2], Bb[0] + W / 2, Bb[1] + H / 2, Bb[2],
                   fp * 0.016 / Bh[2], fp * 0.019 / Bb[2], 0.020 * I, 0.011 * I, 0.006 * I, 0.25 * I)
    size = fp * height_m / max(d, 0.05)
    if size < 1.0:
        return
    _flame(img, depth, cx, cy, d, size, t, gain, lean, seed)


def particles(img, depth, cam, P, cols, coc_strength=0.0, focus=1.0, min_r=0.7):
    """P: (n,3) world positions; cols: (n,3) radiance-ish colours (already lit)."""
    H, W = depth.shape
    o, f, r, u, fp = cam[0:3], cam[3:6], cam[6:9], cam[9:12], cam[12]
    d = P - o
    z = d @ f
    ok = z > 0.05
    d, z, cols = d[ok], z[ok], cols[ok]
    xs = (d @ r) / z * fp + W / 2
    ys = -(d @ u) / z * fp + H / 2
    dist = np.linalg.norm(d, axis=1)
    rad = np.maximum(min_r * W / 3840 * 2, coc_strength * np.abs(1 - focus / dist))
    # energy: spread the same light over the bokeh disc
    _splat(img, depth, xs.astype(np.float64), ys.astype(np.float64), dist.astype(np.float64), rad.astype(np.float64),
           np.ascontiguousarray(cols, np.float64), len(xs))


# ============================================================================ grain / vignette / grade
def grain(img, frame, amount=0.018, seed=0):
    H, W = img.shape[:2]
    rng = np.random.default_rng(seed * 100003 + frame)
    # grain at ~1.5 px scale at 4K: generate at reduced size and upsample
    f = max(1, int(round(W / 2560)))
    n = rng.standard_normal((H // f + 1, W // f + 1)).astype(np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_LINEAR)[:H, :W]
    lum = img.mean(axis=2, keepdims=True)
    # film grain is most visible in the mid-tones; scale with sqrt of luminance (shot-noise-like)
    return np.maximum(img + n[..., None] * amount * np.sqrt(np.clip(lum, 0, 4) * 0.25 + 1e-5), 0)


def vignette(img, strength=0.35, roundness=1.0):
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    x = (xx - W / 2) / (W / 2)
    y = (yy - H / 2) / (H / 2) * roundness * H / W * 1.6
    r2 = x * x + y * y
    v = 1.0 - strength * np.clip(r2 * 0.6, 0, 1) ** 1.3
    return img * v[..., None]


def grade(img, lift=(0.0, 0.0, 0.0), gain=(1.0, 1.0, 1.0), sat=1.0, shadow_tint=(0.0, 0.0, 0.0)):
    out = img * np.asarray(gain, np.float32)
    lum = (out * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(2, keepdims=True)
    out = lum + (out - lum) * sat
    # tint the shadows (cool) without touching highlights
    w = np.clip(1.0 - lum / 0.05, 0, 1)
    out = out + w * np.asarray(shadow_tint, np.float32) + np.asarray(lift, np.float32)
    return np.maximum(out, 0)


# ============================================================================ labels
def label(img, lines, x_frac, y_frac, alpha, align="left", level=0.62, backing=0.45):
    """lines: [(text, font, size_at_4k, weight, tracking, rgb)]. Drawn in display-ish linear light at `level`,
    over a soft dark backing (blurred text mask) so it reads on any background."""
    if alpha <= 0.003:
        return img
    H, W = img.shape[:2]
    s = W / 3840
    cv = Canvas(W, H)
    y = y_frac * H
    x = x_frac * W
    for (txt, fname, size, wt, tr, rgb) in lines:
        f = gfx.font(fname, size * s, wt)
        gfx.draw_text(cv, txt, x, y, f, rgb, 1.0, tracking=tr, align=align, shadow=0.9)
        y += size * s * 1.45
    a = cv.arr.astype(np.float32) / 255.0
    if backing > 0:
        m = cv2.dilate(a[..., 3], np.ones((int(9 * s) | 1, int(9 * s) | 1), np.uint8))
        m = cv2.GaussianBlur(m, (0, 0), 36 * s)
        m = np.clip(m / max(float(m.max()), 1e-6) * 1.6, 0, 1)
        img = img * (1 - backing * alpha * m[..., None])
    col = np.where(a[..., 3:4] > 0, a[..., :3] / np.maximum(a[..., 3:4], 1e-6), 0)
    col = (col ** 2.2) * level
    al = a[..., 3:4] * alpha
    return img * (1 - al) + col * al


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def fade(t, a, b, fin=0.6, fout=0.6):
    """1 inside [a, b] with soft ramps."""
    return ease((t - a) / fin) * ease((b - t) / fout)
