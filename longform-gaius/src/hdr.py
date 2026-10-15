"""Scene-linear → display transforms.

Scene-linear BT.709 RGB with 1.0 = HDR reference (diffuse) white = 203 nits
(ITU-R BT.2408). The HDR10 master maps that to PQ / BT.2020 with a smooth
highlight roll-off to a 1000-nit peak; the SDR preview uses a filmic curve
with BT.709 primaries and a 2.4 display gamma, matched so mid-tones agree.
"""
from __future__ import annotations

import numpy as np

REF_WHITE = 203.0
PEAK = 1000.0
KNEE = 420.0

# BT.709 -> BT.2020 (linear), ITU-R BT.2087
M709_2020 = np.array([[0.6274, 0.3293, 0.0433],
                      [0.0691, 0.9195, 0.0114],
                      [0.0164, 0.0880, 0.8956]], np.float32)

_m1, _m2 = 2610 / 16384, 2523 / 4096 * 128
_c1, _c2, _c3 = 3424 / 4096, 2413 / 4096 * 32, 2392 / 4096 * 32


def pq_oetf(nits):
    y = np.clip(nits / 10000.0, 0, 1)
    ym = np.power(y, _m1)
    return np.power((_c1 + _c2 * ym) / (1 + _c3 * ym), _m2)


def rolloff_nits(n):
    """Identity below KNEE nits, exponential shoulder up to PEAK."""
    over = np.maximum(n - KNEE, 0.0)
    span = PEAK - KNEE
    return np.where(n <= KNEE, n, KNEE + span * (1 - np.exp(-over / span)))


def to_pq10(lin709):
    """Scene-linear BT.709 (H,W,3) -> 10-bit PQ BT.2020 code values (uint16, full 0..1023 scale
    mapped to limited range 64..940)."""
    x = np.maximum(lin709.astype(np.float32), 0)
    # roll off on max channel to preserve hue in highlights
    m = x.max(axis=2, keepdims=True) * REF_WHITE
    scale = np.where(m > 1e-6, rolloff_nits(m) / np.maximum(m, 1e-6), 1.0)
    nits = x * REF_WHITE * scale
    nits2020 = np.maximum(nits @ M709_2020.T, 0)
    e = pq_oetf(nits2020)
    return np.round(64 + e * 876).astype(np.uint16)


def aces_fit(x):
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)


def to_sdr8(lin709, exposure=0.62):
    """Filmic SDR preview, BT.709 / gamma 2.4 (decoded as BT.1886)."""
    x = np.maximum(lin709.astype(np.float32), 0) * exposure
    # tone-map luminance mostly, keep a little per-channel desaturation in highlights
    lum = 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]
    tl = aces_fit(lum)
    ratio = np.where(lum > 1e-7, tl / np.maximum(lum, 1e-7), 0)[..., None]
    y_lum = x * ratio
    y_ch = aces_fit(x)
    w = np.clip(tl, 0, 1)[..., None] ** 2
    y = y_lum * (1 - w) + y_ch * w
    y = np.clip(y, 0, 1) ** (1 / 2.4)
    return np.round(y * 255).astype(np.uint8)


def to_sdr_float(lin709, exposure=0.62):
    return to_sdr8(lin709, exposure).astype(np.float32) / 255.0
