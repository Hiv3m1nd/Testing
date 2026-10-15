"""Moonlit flight over the real Lycian coast (Copernicus DEM + Sentinel-2), traced as a heightfield.

World: x = east, y = up, z = north, metres, origin at Limyra.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from numba import njit, prange

import hfr
from hfr import hsample, csample, smoothstep, hash2

ROOT = Path(__file__).resolve().parents[1]


@njit(cache=True)
def vnoise2(x, y):
    ix, iy = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - ix, y - iy
    ux, uy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = hash2(ix, iy, 1), hash2(ix + 1, iy, 1)
    c, d = hash2(ix, iy + 1, 1), hash2(ix + 1, iy + 1, 1)
    return a + (b - a) * ux + (c - a) * uy + (a - b - c + d) * ux * uy


@njit(cache=True)
def fbm2(x, y, o):
    s, a, t = 0.0, 0.5, 0.0
    for _ in range(o):
        s += a * vnoise2(x, y)
        t += a
        x, y = x * 2.07 + 3.1, y * 2.07 - 1.7
        a *= 0.5
    return s / t


@njit(cache=True)
def sky(dx, dy, dz, moon, frame, stars=True):
    el = dy
    az = math.atan2(dx, dz)
    tt = smoothstep(-0.05, 0.6, el)
    r = 0.0105 * (1 - tt) + 0.0022 * tt
    g = 0.0135 * (1 - tt) + 0.0034 * tt
    b = 0.0215 * (1 - tt) + 0.0075 * tt
    md = dx * moon[0] + dy * moon[1] + dz * moon[2]
    if md > 0:
        gl = math.exp((md - 1.0) * 500.0) * 0.4 + math.exp((md - 1.0) * 20.0) * 0.03
        r += gl * 0.8
        g += gl * 0.88
        b += gl * 1.0
        if md > 0.99996:
            r += 25.0
            g += 24.5
            b += 23.0
    cl = fbm2(az * 3.0 + frame * 0.0004, el * 10.0, 6)
    cl = smoothstep(0.52, 0.80, cl) * smoothstep(0.02, 0.25, el)
    r = r * (1 - 0.6 * cl) + 0.008 * cl
    g = g * (1 - 0.6 * cl) + 0.010 * cl
    b = b * (1 - 0.6 * cl) + 0.014 * cl
    hs = hash2(int((az + 4.0) * 1500.0), int((el + 1.0) * 1500.0), 9)
    if stars and hs > 0.9991 and el > 0.0:
        tw = 0.6 + 0.4 * math.sin(frame * 0.3 + hs * 5000.0)
        st = (hs - 0.9991) / 0.0009 * 0.7 * tw * (1 - cl) * smoothstep(0.0, 0.08, el)
        r += st * 0.9
        g += st * 0.95
        b += st * 1.1
    return r, g, b


@njit(cache=True, parallel=True, fastmath=True)
def render(W, H, cam, org, texel, hm, tmax_map, T, hmin, hmax, albedo, moon, glow, frame, hsh, tsh):
    """moon: [dx,dy,dz (toward moon), r,g,b]; glow: [x,y,z, r,g,b, size] a warm point at Limyra."""
    img = np.zeros((H, W, 3), np.float32)
    depth = np.full((H, W), 1e9, np.float32)
    Hh, Wh = hm.shape
    inv = 1.0 / texel
    # moon direction in texel space (per world unit): U = +x, V = -z, N = +y
    mlx, mly, mlh = moon[0] * inv, -moon[2] * inv, moon[1]
    for j in prange(H):
        for i in range(W):
            sx = (i + 0.5 + (hash2(i, j, frame) - 0.5) * 0.9 - W * 0.5) / cam[12]
            sy = -(j + 0.5 + (hash2(j, i, frame + 5) - 0.5) * 0.9 - H * 0.5) / cam[12]
            dxw = cam[3] + sx * cam[6] + sy * cam[9]
            dyw = cam[4] + sx * cam[7] + sy * cam[10]
            dzw = cam[5] + sx * cam[8] + sy * cam[11]
            L = math.sqrt(dxw * dxw + dyw * dyw + dzw * dzw)
            dxw, dyw, dzw = dxw / L, dyw / L, dzw / L
            ox = (cam[0] - org[0]) * inv
            oy = -(cam[2] - org[2]) * inv
            oh = cam[1]
            dx, dy, dh = dxw * inv, -dzw * inv, dyw
            t, kind = hfr.trace(hm, tmax_map, T, ox, oy, oh, dx, dy, dh, 2e5, hmin, hmax)
            r = g = b = 0.0
            if t < 0:
                r, g, b = sky(dxw, dyw, dzw, moon, frame)
                tt = 2e5
            else:
                tt = t
                x, y = ox + t * dx, oy + t * dy
                hc = hsample(hm, x, y)
                pxw, pyw, pzw = cam[0] + t * dxw, cam[1] + t * dyw, cam[2] + t * dzw
                ar = csample(albedo, x, y, 0)
                ag = csample(albedo, x, y, 1)
                ab = csample(albedo, x, y, 2)
                sea = hc < 0.6 and (ab > ar * 0.9)
                if sea:
                    # wind-rippled sea: microfacet sparkle of the moon + sky reflection
                    wx = pxw * 0.004 + frame * 0.01
                    wz = pzw * 0.004
                    n1 = fbm2(wx, wz, 4) - 0.5
                    n2 = fbm2(wx + 13.0, wz - 7.0, 4) - 0.5
                    nx, ny, nz = n1 * 0.10, 1.0, n2 * 0.10
                    nl = math.sqrt(nx * nx + ny * ny + nz * nz)
                    nx, ny, nz = nx / nl, ny / nl, nz / nl
                    cosi = -(dxw * nx + dyw * ny + dzw * nz)
                    rx, ry, rz = dxw + 2 * cosi * nx, dyw + 2 * cosi * ny, dzw + 2 * cosi * nz
                    fres = 0.02 + 0.98 * (1 - max(cosi, 0.0)) ** 5
                    sr, sg, sb = sky(rx, abs(ry), rz, moon, frame, False)
                    r = sr * fres + 0.0006
                    g = sg * fres + 0.0009
                    b = sb * fres + 0.0014
                else:
                    e = 1.0
                    hl = hsample(hm, x - e, y)
                    hr = hsample(hm, x + e, y)
                    hu = hsample(hm, x, y - e)
                    hd = hsample(hm, x, y + e)
                    gx = (hr - hl) * 0.5 * inv
                    gy = (hd - hu) * 0.5 * inv
                    # texel-space normal (U=+x, V=-z): world n = (-gx, 1, +gy)
                    nx, ny, nz = -gx, 1.0, gy
                    nl = math.sqrt(nx * nx + ny * ny + nz * nz)
                    nx, ny, nz = nx / nl, ny / nl, nz / nl
                    ndl = nx * moon[0] + ny * moon[1] + nz * moon[2]
                    sh = 0.0
                    if ndl > 0:
                        sh = hfr.shadow(hsh, tsh, T, x, y, hsample(hsh, x, y) + 3.0, mlx, mly, mlh, 6e4, hmin, hmax, 40.0)
                    # night: albedo desaturated (scotopic), lifted a touch in the blue
                    lum = 0.30 * ar + 0.59 * ag + 0.11 * ab
                    ar2 = lum * 0.55 + ar * 0.45
                    ag2 = lum * 0.55 + ag * 0.45
                    ab2 = lum * 0.55 + ab * 0.45
                    amb = 0.35 + 0.65 * ny
                    r = ar2 * (ndl * sh * moon[3] + amb * 0.0045)
                    g = ag2 * (ndl * sh * moon[4] + amb * 0.0060)
                    b = ab2 * (ndl * sh * moon[5] + amb * 0.0100)
                # low mist lying on the plain and the bay: the part of the ray below ~160 m
                mist_top = 160.0
                if pyw < mist_top and cam[1] > pyw:
                    seg = t * (mist_top - pyw) / (cam[1] - pyw)
                    mk = (1.0 - math.exp(-seg / 2600.0)) * (0.75 + 0.25 * fbm2(pxw * 0.0004, pzw * 0.0004, 3))
                    r = r * (1 - mk) + 0.010 * mk
                    g = g * (1 - mk) + 0.013 * mk
                    b = b * (1 - mk) + 0.020 * mk
                # aerial perspective (moonlit haze)
                fog = 1.0 - math.exp(-t / 40000.0) * math.exp(-max(0.0, 1.0 - pyw / 1800.0) * t / 90000.0)
                hr_, hg_, hb_ = 0.0085, 0.0110, 0.0175
                r = r * (1 - fog) + hr_ * fog
                g = g * (1 - fog) + hg_ * fog
                b = b * (1 - fog) + hb_ * fog
            # warm glow at Limyra (the torch, seen from afar): a small soft point + halo
            vx, vy, vz = glow[0] - cam[0], glow[1] - cam[1], glow[2] - cam[2]
            vd = math.sqrt(vx * vx + vy * vy + vz * vz)
            if vd < tt + 50.0:
                ca = (vx * dxw + vy * dyw + vz * dzw) / vd
                ang = math.sqrt(max(0.0, 2.0 * (1.0 - ca)))
                core = math.exp(-(ang / glow[6]) ** 2)
                halo = 0.06 / (1.0 + (ang / (glow[6] * 6.0)) ** 2)
                k = core + halo
                r += k * glow[3]
                g += k * glow[4]
                b += k * glow[5]
            img[j, i, 0], img[j, i, 1], img[j, i, 2] = r, g, b
            depth[j, i] = tt
    return img, depth


class Terrain:
    def __init__(self):
        d = ROOT / "build" / "terrain"
        self.meta = json.load(open(d / "meta.json"))
        self.hm = np.ascontiguousarray(np.load(d / "height.npy"), np.float32)
        a = np.load(d / "albedo.npy").astype(np.float32)
        # greenhouse roofs and bare limestone are near-white in July sun; at night they would
        # not glare, so compress the top of the range (soft knee) before lighting
        lum = a.mean(2, keepdims=True)
        a = a * np.where(lum > 0.18, (0.18 + (lum - 0.18) * 0.35) / np.maximum(lum, 1e-6), 1.0)
        self.albedo = np.ascontiguousarray(a)
        import cv2
        self.hsh = cv2.GaussianBlur(self.hm, (0, 0), 1.5)
        self.T = 16
        self.tmax = hfr.tile_max(self.hm, self.T)
        self.tsh = hfr.tile_max(self.hsh, self.T)
        m = self.meta
        self.texel = m["texel"]
        # world origin at Limyra: texel (0,0) sits at x = -(le - ul_e), z = (ul_n - ln)
        self.org = np.array([-(m["limyra_e"] - m["ul_e"]), 0.0, (m["ul_n"] - m["limyra_n"])], np.float64)

    def render(self, W, H, cam, moon, glow, frame):
        return render(W, H, np.asarray(cam, np.float64), self.org, self.texel, self.hm, self.tmax, self.T,
                      -1.0, float(self.hm.max()) + 1.0, self.albedo, np.asarray(moon, np.float64),
                      np.asarray(glow, np.float64), frame, self.hsh, self.tsh)
