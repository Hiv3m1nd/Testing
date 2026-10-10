"""Shared drawing helpers: canvas, typography, easing, noise and film finishing."""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
import skia

W, H, FPS = 1080, 1920, 30
ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "assets" / "fonts"

FONT_FILES = {
    "cinzel": "cinzel_Cinzel[wght].ttf",
    "garamond": "cormorantgaramond_CormorantGaramond[wght].ttf",
    "garamond-italic": "cormorantgaramond_CormorantGaramond-Italic[wght].ttf",
    "inter": "inter_Inter[opsz,wght].ttf",
    "kai": "lxgwwenkaitc_LXGWWenKaiTC-Bold.ttf",
    "serif-tc": "notoseriftc_NotoSerifTC[wght].ttf",
}

# palette (sRGB 0..1)
GOLD = (0.89, 0.72, 0.42)
PALE_GOLD = (0.96, 0.88, 0.70)
IVORY = (0.96, 0.93, 0.86)
ROME = (0.80, 0.16, 0.20)
PARTHIA = (0.18, 0.66, 0.62)
HAN = (0.93, 0.52, 0.16)
INK = (0.06, 0.05, 0.05)


# ----------------------------------------------------------------------------- easing
def clamp01(x):
    return max(0.0, min(1.0, x))


def seg(t, a, b):
    """0..1 progress of t through [a, b]."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp01((t - a) / (b - a))


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def smoother(x):
    x = clamp01(x)
    return x * x * x * (x * (6 * x - 15) + 10)


def ease_out(x, p=3):
    return 1 - (1 - clamp01(x)) ** p


def ease_in(x, p=3):
    return clamp01(x) ** p


def ease_io(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def fade_io(t, a, b, fin=0.5, fout=0.5):
    """Envelope that fades in over `fin` after a and out over `fout` before b."""
    return smooth(seg(t, a, a + fin)) * (1 - smooth(seg(t, b - fout, b)))


def lerp(a, b, t):
    return a + (b - a) * t


# ----------------------------------------------------------------------------- canvas
class Canvas:
    """RGBA uint8 buffer with a skia canvas drawing straight into it."""

    def __init__(self, w=W, h=H, arr=None):
        self.arr = arr if arr is not None else np.zeros((h, w, 4), np.uint8)
        self.surface = skia.Surface(self.arr, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
        self.c = self.surface.getCanvas()
        self.w, self.h = w, h

    @classmethod
    def from_float(cls, rgb):
        a = np.empty(rgb.shape[:2] + (4,), np.uint8)
        a[..., :3] = np.clip(rgb * 255 + 0.5, 0, 255).astype(np.uint8)
        a[..., 3] = 255
        return cls(rgb.shape[1], rgb.shape[0], a)

    def to_float(self):
        return self.arr[..., :3].astype(np.float32) / 255.0

    def rgba_float(self):
        return self.arr.astype(np.float32) / 255.0


def color(rgb, a=1.0):
    return skia.Color4f(float(rgb[0]), float(rgb[1]), float(rgb[2]), float(clamp01(a)))


def paint(rgb=(1, 1, 1), a=1.0, stroke=None, blur=0.0, aa=True, cap=None, blend=None):
    p = skia.Paint(AntiAlias=aa)
    p.setColor4f(color(rgb, a))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(cap or skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend is not None:
        p.setBlendMode(blend)
    return p


# ----------------------------------------------------------------------------- type
@lru_cache(maxsize=None)
def typeface(name, weight=None):
    tf = skia.Typeface.MakeFromFile(str(FONTS / FONT_FILES[name]))
    if weight is not None and tf.getVariationDesignParameters():
        coords = [skia.FontArguments.VariationPosition.Coordinate(0x77676874, float(weight))]  # 'wght'
        pos = skia.FontArguments.VariationPosition(skia.FontArguments.VariationPosition.Coordinates(coords))
        args = skia.FontArguments()
        args.setVariationDesignPosition(pos)
        tf = tf.makeClone(args)
    return tf


def font(name, size, weight=None):
    f = skia.Font(typeface(name, weight), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kSubpixelAntiAlias if False else skia.Font.Edging.kAntiAlias)
    f.setHinting(skia.FontHinting.kNone)
    return f


def text_width(s, f, tracking=0.0):
    if not s:
        return 0.0
    glyphs = f.textToGlyphs(s)
    return float(sum(f.getWidths(glyphs))) + tracking * f.getSize() * (len(glyphs) - 1)


def text_blob(s, f, x, y, tracking=0.0, align="center"):
    glyphs = f.textToGlyphs(s)
    widths = f.getWidths(glyphs)
    tr = tracking * f.getSize()
    total = float(sum(widths)) + tr * (len(glyphs) - 1)
    x0 = x - total / 2 if align == "center" else (x - total if align == "right" else x)
    xs, cx = [], x0
    for wdt in widths:
        xs.append(cx)
        cx += wdt + tr
    return skia.TextBlob.MakeFromPosTextH(s, xs, y, f), total


def draw_text(cv: Canvas, s, x, y, f, rgb=IVORY, a=1.0, tracking=0.0, align="center", glow=0.0,
              glow_rgb=None, shadow=0.0, stroke=None):
    """Draw text at baseline y. glow: blur radius of a soft halo; shadow: dark halo strength."""
    if a <= 0.003 or not s:
        return 0.0
    blob, total = text_blob(s, f, x, y, tracking, align)
    if shadow > 0:
        cv.c.drawTextBlob(blob, 0, 0, paint(INK, a * shadow, blur=f.getSize() * 0.12))
    if glow > 0:
        cv.c.drawTextBlob(blob, 0, 0, paint(glow_rgb or rgb, a * 0.55, blur=glow))
    if stroke:
        cv.c.drawTextBlob(blob, 0, 0, paint(stroke[0], a, stroke=stroke[1]))
    cv.c.drawTextBlob(blob, 0, 0, paint(rgb, a))
    return total


def draw_text_reveal(cv: Canvas, s, x, y, f, prog, rgb=IVORY, a=1.0, tracking=0.0, align="center",
                     glow=0.0, rise=18.0, stagger=0.6, shadow=0.0):
    """Per-letter fade/rise reveal; prog 0..1."""
    glyphs = f.textToGlyphs(s)
    widths = f.getWidths(glyphs)
    tr = tracking * f.getSize()
    total = float(sum(widths)) + tr * (len(glyphs) - 1)
    x0 = x - total / 2 if align == "center" else (x - total if align == "right" else x)
    n = len(s)
    cx = x0
    for i, (ch, wdt) in enumerate(zip(s, widths)):
        start = (i / max(1, n - 1)) * stagger if n > 1 else 0
        p = smooth(seg(prog, start, start + (1 - stagger)))
        if p > 0:
            draw_text(cv, ch, cx, y + (1 - p) * rise, f, rgb, a * p, 0, "left", glow, shadow=shadow)
        cx += wdt + tr
    return total


def wrap(s, f, max_w, tracking=0.0):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_width(trial, f, tracking) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


# ----------------------------------------------------------------------------- noise & textures
@lru_cache(maxsize=None)
def fbm(h, w, scale, seed, octaves=5, persistence=0.5):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = max(2, int(h / scale * 2 ** o) + 2), max(2, int(w / scale * 2 ** o) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        acc += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= persistence
    acc /= tot
    acc = (acc - acc.min()) / (acc.max() - acc.min() + 1e-6)
    acc.setflags(write=False)
    return acc


@lru_cache(maxsize=None)
def grain_bank(n=8, seed=3):
    rng = np.random.default_rng(seed)
    bank = []
    for _ in range(n):
        g = rng.normal(0, 1, (H, W)).astype(np.float32)
        bank.append(cv2.GaussianBlur(g, (3, 3), 0.55))
    return bank


@lru_cache(maxsize=None)
def vignette_mask(strength=0.55, roundness=1.0):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (x - W / 2) / (W / 2)
    ny = (y - H / 2) / (H / 2)
    r = np.sqrt((nx * roundness) ** 2 + ny ** 2) / math.sqrt(1 + roundness ** 2) * math.sqrt(2)
    return (1 - strength * np.clip(r - 0.35, 0, None) ** 1.6).astype(np.float32)


def bloom(img, thresh=0.75, strength=0.35, radius=40):
    small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    bright = np.clip(small - thresh, 0, None) / (1 - thresh)
    k = int(radius / 4) * 2 + 1
    b1 = cv2.GaussianBlur(bright, (k, k), 0)
    b2 = cv2.GaussianBlur(bright, (k * 3 | 1, k * 3 | 1), 0)
    b = cv2.resize(b1 * 0.6 + b2 * 0.4, (W, H), interpolation=cv2.INTER_LINEAR)
    return img + b * strength


def finish(img, frame, grain=0.022, vig=0.5, bloom_amt=0.3, lift=0.012, warm=0.0):
    """Film finishing: bloom, warm/cool split grade, vignette, grain."""
    img = bloom(img, strength=bloom_amt) if bloom_amt else img
    img = img * vignette_mask(vig)[..., None]
    if warm:
        lum = img.mean(-1, keepdims=True)
        img = img + warm * (np.array([0.03, 0.012, -0.02], np.float32) * lum +
                            np.array([-0.008, 0.0, 0.012], np.float32) * (1 - lum))
    img = lift + img * (1 - lift)
    if grain:
        g = grain_bank()[frame % 8]
        lum = np.clip(img.mean(-1, keepdims=True), 0, 1)
        img = img + g[..., None] * grain * (0.35 + 0.65 * (1 - lum) * lum * 4)
    return np.clip(img, 0, 1)


def over(dst, src_rgba):
    """Alpha-composite premultiplied RGBA float (H,W,4) over rgb float."""
    a = src_rgba[..., 3:4]
    return dst * (1 - a) + src_rgba[..., :3]


def screen(a, b):
    return 1 - (1 - a) * (1 - b)


def rgba_from(cv: Canvas):
    return cv.arr.astype(np.float32) / 255.0
