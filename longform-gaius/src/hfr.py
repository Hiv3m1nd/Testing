"""Heightfield ray tracer (numba, CPU, linear-light HDR).

One engine for every "relief" object in the film: real photographs lifted to
2.5D with estimated depth, coins, carved inscriptions and the title stone.
A heightfield sits in a local frame (U across, V down, N out of the surface);
rays are traced through it with max-height tile skipping and bisection, then
lit by point lights (with soft shadows marched through the same heightfield),
a moon/key directional light and ambient occlusion.

Units are arbitrary but consistent (metres for stone, centimetres would do
for coins). Radiance 1.0 = diffuse white (203 nits in the PQ master).
"""
from __future__ import annotations

import math

import numpy as np
from numba import njit, prange

HOLE = -1e4  # heights below this are empty (cut-out photographs, round coins)


@njit(cache=True, inline="always")
def smoothstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


@njit(cache=True, inline="always")
def hash2(ix, iy, s):
    h = (ix * 374761393 + iy * 668265263 + s * 1440662683) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF) / 16777215.0


@njit(cache=True, inline="always")
def hsample(hm, x, y):
    """Bilinear height in texel coords; returns HOLE outside or if any corner is a hole."""
    Hh, Wh = hm.shape
    if x < 0.0 or y < 0.0 or x > Wh - 1.001 or y > Hh - 1.001:
        return HOLE
    i, j = int(x), int(y)
    fx, fy = x - i, y - j
    a, b, c, d = hm[j, i], hm[j, i + 1], hm[j + 1, i], hm[j + 1, i + 1]
    if a <= HOLE or b <= HOLE or c <= HOLE or d <= HOLE:
        # nearest valid-or-hole: treat as hole unless the nearest corner is solid
        n = a if fx < 0.5 and fy < 0.5 else (b if fy < 0.5 else (c if fx < 0.5 else d))
        return n
    return (a + (b - a) * fx) + ((c + (d - c) * fx) - (a + (b - a) * fx)) * fy


@njit(cache=True, inline="always")
def csample(img, x, y, c):
    Hh, Wh = img.shape[0], img.shape[1]
    x = min(max(x, 0.0), Wh - 1.001)
    y = min(max(y, 0.0), Hh - 1.001)
    i, j = int(x), int(y)
    fx, fy = x - i, y - j
    a = img[j, i, c] + (img[j, i + 1, c] - img[j, i, c]) * fx
    b = img[j + 1, i, c] + (img[j + 1, i + 1, c] - img[j + 1, i, c]) * fx
    return a + (b - a) * fy


@njit(cache=True)
def trace(hm, tmax_map, T, ox, oy, oh, dx, dy, dh, tlimit, hmin, hmax):
    """Trace a ray in texel space (x, y in texels, h in height units).
    Returns (t, kind): kind 0 = top surface, 1 = side wall, -1 = miss."""
    Hh, Wh = hm.shape
    # slab: x in [0, Wh-1], y in [0, Hh-1], h in [hmin, hmax]
    t0, t1 = 0.0, tlimit
    for a in range(3):
        o = ox if a == 0 else (oy if a == 1 else oh)
        d = dx if a == 0 else (dy if a == 1 else dh)
        lo = 0.0 if a < 2 else hmin
        hi = (Wh - 1.001) if a == 0 else ((Hh - 1.001) if a == 1 else hmax)
        if abs(d) < 1e-12:
            if o < lo or o > hi:
                return -1.0, -1
        else:
            ta = (lo - o) / d
            tb = (hi - o) / d
            if ta > tb:
                ta, tb = tb, ta
            t0 = max(t0, ta)
            t1 = min(t1, tb)
    if t1 <= t0:
        return -1.0, -1
    duv = math.sqrt(dx * dx + dy * dy)
    fine = 0.45 / max(duv, 1e-9)
    if abs(dh) > 1e-12:
        # never step more than a sixth of the slab's height range along the ray
        fine = min(fine, (hmax - hmin) / abs(dh) / 6.0)
    t = t0 + 1e-5
    first = True
    prev_t = t
    nt = tmax_map.shape
    for _ in range(200000):
        if t > t1:
            return -1.0, -1
        x, y, h = ox + t * dx, oy + t * dy, oh + t * dh
        # tile skipping
        ti, tj = int(x) // T, int(y) // T
        if 0 <= ti < nt[1] and 0 <= tj < nt[0]:
            tm = tmax_map[tj, ti]
            # exit of this tile along the ray (uv DDA)
            if dx > 0:
                ex = ((ti + 1) * T - x) / dx
            elif dx < 0:
                ex = (ti * T - x) / dx
            else:
                ex = 1e30
            if dy > 0:
                ey = ((tj + 1) * T - y) / dy
            elif dy < 0:
                ey = (tj * T - y) / dy
            else:
                ey = 1e30
            te = min(ex, ey) + 1e-4
            hend = h + te * dh
            if h > tm and hend > tm:
                first = False
                prev_t = t
                t += te
                continue
        s = hsample(hm, x, y)
        if s > HOLE and h <= s:
            if first:
                return t, 1  # entered through the side of the slab
            lo, hi = prev_t, t
            for _ in range(14):
                m = 0.5 * (lo + hi)
                xm, ym, hmm = ox + m * dx, oy + m * dy, oh + m * dh
                sm = hsample(hm, xm, ym)
                if sm > HOLE and hmm <= sm:
                    hi = m
                else:
                    lo = m
            # did we come in through a hole wall?
            sp = hsample(hm, ox + lo * dx, oy + lo * dy)
            if sp <= HOLE:
                return hi, 1
            return hi, 0
        first = False
        prev_t = t
        t += fine
    return -1.0, -1


@njit(cache=True)
def shadow(hm, tmax_map, T, x, y, h, lx, ly, lh, dist, hmin, hmax, k):
    """Soft visibility toward a light in texel space (lx,ly,lh normalised direction)."""
    Hh, Wh = hm.shape
    res = 1.0
    duv = math.sqrt(lx * lx + ly * ly)
    step = 0.9 / max(duv, 1e-6)
    t = 1.2 / max(duv, 0.3)
    nt = tmax_map.shape
    for _ in range(4000):
        if t > dist:
            break
        px, py, ph = x + t * lx, y + t * ly, h + t * lh
        if ph > hmax:
            break
        if px < 0 or py < 0 or px >= Wh - 1 or py >= Hh - 1:
            break
        ti, tj = int(px) // T, int(py) // T
        if 0 <= ti < nt[1] and 0 <= tj < nt[0] and ph > tmax_map[tj, ti] + 0.5:
            t += step * T * 0.5
            continue
        s = hsample(hm, px, py)
        if s > HOLE:
            dd = ph - s
            if dd < 0:
                return 0.0
            res = min(res, k * dd / t)
        t += step * (1.0 + t * 0.01)
    return smoothstep(0.0, 1.0, res)


@njit(cache=True, parallel=True, fastmath=True)
def render(W, H, cam, frame_o, frame_u, frame_v, frame_n, texel, hscale, hm, tmax_map, T, hmin, hmax,
           albedo, aomap, matmap, lights, nlights, keydir, ambient, mat, seed, bg, hm_sh, tmax_sh, env):
    """cam: [ox,oy,oz, fx,fy,fz, rx,ry,rz, ux,uy,uz, focal_px] (world)
    frame_*: the heightfield's world frame (origin at texel (0,0) h=0; U per texel along x, V along y, N up)
    texel: world size of one texel; hscale: world units per height unit.
    albedo (Hh,Wh,3) linear; aomap (Hh,Wh); matmap (Hh,Wh): 0..1 'gold'/'metal' weight.
    lights: (8, 8) rows [x,y,z (world), r,g,b intensity, radius, shadow 0/1]
    keydir: [dx,dy,dz, r,g,b] directional light (world, toward light) with shadow.
    ambient: [r,g,b]; mat: [spec, rough_exp, metal_spec, metal_rough_exp, sheen, sss, gold_r, gold_g]
    bg: [r,g,b] for misses.
    Returns rgb (H,W,3), depth (H,W), alpha (H,W)."""
    img = np.zeros((H, W, 3), np.float32)
    depth = np.full((H, W), 1e9, np.float32)
    alpha = np.zeros((H, W), np.float32)
    Hh, Wh = hm.shape
    inv_t = 1.0 / texel
    inv_hs = 1.0 / hscale
    for j in prange(H):
        for i in range(W):
            sx = (i + 0.5 + (hash2(i, j, seed) - 0.5) * 0.9 - W * 0.5) / cam[12]
            sy = -(j + 0.5 + (hash2(j, i, seed + 3) - 0.5) * 0.9 - H * 0.5) / cam[12]
            dxw = cam[3] + sx * cam[6] + sy * cam[9]
            dyw = cam[4] + sx * cam[7] + sy * cam[10]
            dzw = cam[5] + sx * cam[8] + sy * cam[11]
            L = math.sqrt(dxw * dxw + dyw * dyw + dzw * dzw)
            dxw, dyw, dzw = dxw / L, dyw / L, dzw / L
            # world -> texel space
            qx, qy, qz = cam[0] - frame_o[0], cam[1] - frame_o[1], cam[2] - frame_o[2]
            ox = (qx * frame_u[0] + qy * frame_u[1] + qz * frame_u[2]) * inv_t
            oy = (qx * frame_v[0] + qy * frame_v[1] + qz * frame_v[2]) * inv_t
            oh = (qx * frame_n[0] + qy * frame_n[1] + qz * frame_n[2]) * inv_hs
            dx = (dxw * frame_u[0] + dyw * frame_u[1] + dzw * frame_u[2]) * inv_t
            dy = (dxw * frame_v[0] + dyw * frame_v[1] + dzw * frame_v[2]) * inv_t
            dh = (dxw * frame_n[0] + dyw * frame_n[1] + dzw * frame_n[2]) * inv_hs
            t, kind = trace(hm, tmax_map, T, ox, oy, oh, dx, dy, dh, 1e7, hmin, hmax)
            if t < 0:
                img[j, i, 0], img[j, i, 1], img[j, i, 2] = bg[0], bg[1], bg[2]
                continue
            x, y, h = ox + t * dx, oy + t * dy, oh + t * dh
            # world hit point
            pxw = cam[0] + t * dxw
            pyw = cam[1] + t * dyw
            pzw = cam[2] + t * dzw
            depth[j, i] = t
            alpha[j, i] = 1.0
            # normal in texel space -> world
            if kind == 0:
                e = 1.0
                hl = hsample(hm, x - e, y)
                hr = hsample(hm, x + e, y)
                hu = hsample(hm, x, y - e)
                hd = hsample(hm, x, y + e)
                hc = hsample(hm, x, y)
                if hl <= HOLE:
                    hl = hc
                if hr <= HOLE:
                    hr = hc
                if hu <= HOLE:
                    hu = hc
                if hd <= HOLE:
                    hd = hc
                gx = (hr - hl) * 0.5 * hscale * inv_t
                gy = (hd - hu) * 0.5 * hscale * inv_t
                nx = -gx * frame_u[0] - gy * frame_v[0] + frame_n[0]
                ny = -gx * frame_u[1] - gy * frame_v[1] + frame_n[1]
                nz = -gx * frame_u[2] - gy * frame_v[2] + frame_n[2]
            else:
                # side wall: outward normal = toward the empty side of the outline
                sxp = 1.0 if hsample(hm, x + 2.0, y) > HOLE else 0.0
                sxm = 1.0 if hsample(hm, x - 2.0, y) > HOLE else 0.0
                syp = 1.0 if hsample(hm, x, y + 2.0) > HOLE else 0.0
                sym = 1.0 if hsample(hm, x, y - 2.0) > HOLE else 0.0
                wx_, wy_ = sxm - sxp, sym - syp
                if abs(wx_) + abs(wy_) < 0.5:
                    wx_, wy_ = -dx, -dy
                nx = wx_ * frame_u[0] + wy_ * frame_v[0]
                ny = wx_ * frame_u[1] + wy_ * frame_v[1]
                nz = wx_ * frame_u[2] + wy_ * frame_v[2]
            nl = math.sqrt(nx * nx + ny * ny + nz * nz) + 1e-12
            nx, ny, nz = nx / nl, ny / nl, nz / nl
            ar = csample(albedo, x, y, 0)
            ag = csample(albedo, x, y, 1)
            ab = csample(albedo, x, y, 2)
            xi = min(max(int(x + 0.5), 0), Wh - 1)
            yi = min(max(int(y + 0.5), 0), Hh - 1)
            ao = aomap[yi, xi]
            mw = matmap[yi, xi]
            r = g = b = 0.0
            vx, vy, vz = -dxw, -dyw, -dzw
            for li in range(nlights):
                Lr = lights[li]
                lxw, lyw, lzw = Lr[0] - pxw, Lr[1] - pyw, Lr[2] - pzw
                d2 = lxw * lxw + lyw * lyw + lzw * lzw
                dl = math.sqrt(d2)
                lxw, lyw, lzw = lxw / dl, lyw / dl, lzw / dl
                ndl = nx * lxw + ny * lyw + nz * lzw
                if ndl <= 0.0:
                    continue
                sh = 1.0
                if Lr[7] > 0.5 and kind == 0:
                    lx = (lxw * frame_u[0] + lyw * frame_u[1] + lzw * frame_u[2]) * inv_t
                    ly = (lxw * frame_v[0] + lyw * frame_v[1] + lzw * frame_v[2]) * inv_t
                    lh = (lxw * frame_n[0] + lyw * frame_n[1] + lzw * frame_n[2]) * inv_hs
                    # direction per world unit in texel/height space; t is world distance
                    sh = shadow(hm_sh, tmax_sh, T, x, y, hsample(hm_sh, x, y) + 0.004 * (hmax - hmin), lx, ly, lh,
                                dl, hmin, hmax, dl / max(Lr[6], 1e-4) * 0.5)
                    if sh <= 0.0:
                        continue
                att = 1.0 / (d2 + 1e-4)
                hx, hy, hz = lxw + vx, lyw + vy, lzw + vz
                hn = math.sqrt(hx * hx + hy * hy + hz * hz) + 1e-9
                ndh = max(0.0, (nx * hx + ny * hy + nz * hz) / hn)
                spec_d = mat[0] * math.pow(ndh, mat[1]) * (mat[1] + 2) / 8.0
                spec_m = mat[2] * math.pow(ndh, mat[3]) * (mat[3] + 2) / 8.0
                # wrapped diffuse gives marble its soft, translucent fall-off
                wrap = (ndl + mat[5]) / (1.0 + mat[5])
                c = sh * att
                dr = ar * wrap * (1 - mw * 0.85) + spec_d * ndl * (1 - mw) + spec_m * ndl * mw * mat[6]
                dg = ag * wrap * (1 - mw * 0.85) + spec_d * ndl * (1 - mw) + spec_m * ndl * mw * mat[7]
                db = ab * wrap * (1 - mw * 0.85) + spec_d * ndl * (1 - mw) + spec_m * ndl * mw * mat[7] * 0.55
                r += dr * c * Lr[3]
                g += dg * c * Lr[4]
                b += db * c * Lr[5]
            # directional key (moon / sky)
            kdl = nx * keydir[0] + ny * keydir[1] + nz * keydir[2]
            if kdl > 0.0 and (keydir[3] + keydir[4] + keydir[5]) > 0.0:
                r += ar * kdl * keydir[3] * ao
                g += ag * kdl * keydir[4] * ao
                b += ab * kdl * keydir[5] * ao
            r += ar * ambient[0] * ao
            g += ag * ambient[1] * ao
            b += ab * ambient[2] * ao
            # environment reflection for metal: dim gradient + one soft box (env[0:3] top, 3:6 bottom,
            # 6:9 softbox direction, 9:12 softbox colour, 12 softbox sharpness)
            if mw > 0.0 and env[12] > 0.0:
                vn = dxw * nx + dyw * ny + dzw * nz
                rx_, ry_, rz_ = dxw - 2 * vn * nx, dyw - 2 * vn * ny, dzw - 2 * vn * nz
                tt_ = 0.5 + 0.5 * ry_
                er = env[3] + (env[0] - env[3]) * tt_
                eg = env[4] + (env[1] - env[4]) * tt_
                eb = env[5] + (env[2] - env[5]) * tt_
                sb = max(0.0, rx_ * env[6] + ry_ * env[7] + rz_ * env[8])
                sbk = math.pow(sb, env[12])
                er += env[9] * sbk
                eg += env[10] * sbk
                eb += env[11] * sbk
                f0 = mw * ao
                r += er * f0 * ar * 1.2
                g += eg * f0 * ag * 1.2
                b += eb * f0 * ab * 1.2
            img[j, i, 0], img[j, i, 1], img[j, i, 2] = r, g, b
    return img, depth, alpha


def tile_max(hm, T=16):
    Hh, Wh = hm.shape
    nh, nw = (Hh + T - 1) // T, (Wh + T - 1) // T
    pad = np.full((nh * T + 1, nw * T + 1), -1e9, np.float32)
    pad[:Hh, :Wh] = hm
    # include the neighbouring row/col so bilinear samples at tile borders are covered
    m = np.maximum(pad[:-1, :-1], np.maximum(pad[1:, :-1], np.maximum(pad[:-1, 1:], pad[1:, 1:])))
    return m.reshape(nh, T, nw, T).max(axis=(1, 3)).astype(np.float32)


def ao_map(hm, radius_px=(4, 12, 32, 80), strength=1.0):
    """Cheap multi-scale AO: how far a texel sits below its blurred surroundings."""
    import cv2
    h = np.where(hm <= HOLE, np.nan, hm).astype(np.float32)
    base = np.nan_to_num(h, nan=float(np.nanmin(h)))
    occ = np.zeros_like(base)
    rng = float(np.nanmax(h) - np.nanmin(h)) + 1e-6
    for r in radius_px:
        bl = cv2.GaussianBlur(base, (0, 0), r)
        occ += np.clip((bl - base) / (rng * 0.08 * (r / radius_px[0]) ** 0.5), 0, 1)
    ao = np.clip(1.0 - strength * occ / len(radius_px), 0.15, 1.0)
    return ao.astype(np.float32)


class Relief:
    """A heightfield object placed in the world."""

    def __init__(self, hm, albedo, origin, u, v, n, texel, hscale, matmap=None, ao=None, T=16, hm_shadow=None):
        self.hm = np.ascontiguousarray(hm, np.float32)
        self.hm_sh = self.hm if hm_shadow is None else np.ascontiguousarray(hm_shadow, np.float32)
        self.albedo = np.ascontiguousarray(albedo, np.float32)
        self.matmap = np.zeros(hm.shape, np.float32) if matmap is None else np.ascontiguousarray(matmap, np.float32)
        self.ao = ao_map(hm) if ao is None else np.ascontiguousarray(ao, np.float32)
        self.T = T
        self.tmax = tile_max(self.hm, T)
        self.tmax_sh = self.tmax if hm_shadow is None else tile_max(self.hm_sh, T)
        valid = self.hm[self.hm > HOLE]
        self.hmin, self.hmax = float(valid.min()) - 1e-3, float(valid.max()) + 1e-3
        self.o = np.asarray(origin, np.float64)
        self.u = np.asarray(u, np.float64) / np.linalg.norm(u)
        self.v = np.asarray(v, np.float64) / np.linalg.norm(v)
        self.n = np.asarray(n, np.float64) / np.linalg.norm(n)
        self.texel, self.hscale = float(texel), float(hscale)

    def render(self, W, H, cam, lights, key=None, ambient=(0, 0, 0), mat=None, seed=0, bg=(0, 0, 0), env=None):
        L = np.zeros((8, 8), np.float64)
        for k, l in enumerate(lights):
            L[k, :len(l)] = l
        key = np.zeros(6) if key is None else np.asarray(key, np.float64)
        mat = np.array([0.08, 24, 0.0, 60, 0, 0.25, 1.0, 0.8] if mat is None else mat, np.float64)
        return render(W, H, np.asarray(cam, np.float64), self.o, self.u, self.v, self.n, self.texel, self.hscale,
                      self.hm, self.tmax, self.T, self.hmin, self.hmax, self.albedo, self.ao, self.matmap,
                      L, len(lights), key, np.asarray(ambient, np.float64), mat, seed, np.asarray(bg, np.float64),
                      self.hm_sh, self.tmax_sh, np.zeros(13) if env is None else np.asarray(env, np.float64))
