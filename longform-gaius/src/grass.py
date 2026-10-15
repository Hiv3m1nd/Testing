"""Dry grass and weeds growing between the stones, drawn as lit, wind-swayed blades with depth test.

Tufts are scattered on the ground with a preference for the foot of walls, column bases and
fallen blocks (where real ruins grow weeds), using the baked SDF to keep them out of the stone."""
from __future__ import annotations

import math

import numpy as np
from numba import njit, prange

import sdf


@njit(cache=True)
def _place(dist, G, gh, GH, n_try, seed, out):
    """Rejection-sample tuft bases: keep points near (but outside) stone, plus a sparse scatter."""
    k = 0
    for i in range(n_try):
        x = -6.5 + 13.0 * sdf.hash3(i, 1, seed)
        z = -3.5 + 21.0 * sdf.hash3(i, 2, seed)
        y = 0.0
        # ground height from the baked heightfield
        gx = (x - GH[0]) * GH[2]
        gz = (z - GH[1]) * GH[2]
        if gx < 1 or gz < 1 or gx >= gh.shape[1] - 2 or gz >= gh.shape[0] - 2:
            continue
        y = gh[int(gz), int(gx)]
        if y < -0.010:
            continue                      # no grass in the water
        d = sdf.grid_d(dist, G[0], G[1], G[2], G[3], x, y + 0.06, z)
        if d < 0.02:
            continue
        p = 0.06 + 0.9 * math.exp(-max(d - 0.02, 0.0) / 0.25)
        if sdf.hash3(i, 3, seed) < p:
            out[k, 0], out[k, 1], out[k, 2] = x, y, z
            out[k, 3] = sdf.hash3(i, 4, seed)       # size
            out[k, 4] = sdf.hash3(i, 5, seed)       # dryness
            k += 1
            if k >= out.shape[0]:
                break
    return k


def tufts(B, n=4200, seed=5):
    out = np.zeros((n, 5), np.float64)
    k = _place(B.dist, B.G, B.gh, B.GH, n * 12, seed, out)
    return out[:k]


@njit(cache=True, parallel=True)
def _draw(img, depth, cam, W, H, T, t, torch, moon, nblades, seed, shadow_t):
    """Draw every blade of every tuft. torch: [x,y,z, r,g,b]; moon: [dx,dy,dz, r,g,b]."""
    fp = cam[12]
    nt = T.shape[0]
    for k in prange(nt):
        bx, by, bz, size, dry = T[k, 0], T[k, 1], T[k, 2], T[k, 3], T[k, 4]
        # tuft lighting (once per tuft): torch with precomputed visibility + cool moon + ambient
        lx, ly, lz = torch[0] - bx, torch[1] - by - 0.1, torch[2] - bz
        d2 = lx * lx + ly * ly + lz * lz + 0.02
        It = shadow_t[k] / d2 * 0.55
        ar = 0.30 * dry + 0.16 * (1 - dry)
        ag = 0.27 * dry + 0.20 * (1 - dry)
        ab = 0.15 * dry + 0.08 * (1 - dry)
        cr = ar * (It * torch[3] + moon[3] * 0.5 + 0.004)
        cg = ag * (It * torch[4] + moon[4] * 0.5 + 0.005)
        cb = ab * (It * torch[5] + moon[5] * 0.5 + 0.008)
        nb = 6 + int(nblades * size)
        for bl in range(nb):
            h1 = sdf.hash3(k, bl, seed)
            h2 = sdf.hash3(k, bl, seed + 1)
            h3 = sdf.hash3(k, bl, seed + 2)
            hgt = (0.09 + 0.38 * size) * (0.55 + 0.45 * h1)
            ang = 6.2832 * h2
            lean = 0.15 + 0.55 * h3
            ox_ = 0.035 * size * (h1 - 0.5)
            oz_ = 0.035 * size * (h3 - 0.5)
            sway = 0.10 * math.sin(t * (1.1 + 0.6 * h2) + bx * 1.7 + bz * 1.3) + 0.04 * math.sin(t * 3.1 + h1 * 9)
            # blade as 6 segments of a curve
            px_prev, py_prev, d_prev = 0.0, 0.0, -1.0
            for s in range(7):
                u = s / 6.0
                bend = lean * u * u + sway * u * u
                wx = bx + ox_ + math.cos(ang) * bend * hgt
                wy = by + hgt * u * (1.0 - 0.25 * lean * u)
                wz = bz + oz_ + math.sin(ang) * bend * hgt
                qx, qy, qz = wx - cam[0], wy - cam[1], wz - cam[2]
                zc = qx * cam[3] + qy * cam[4] + qz * cam[5]
                if zc < 0.05:
                    d_prev = -1.0
                    continue
                sx = (qx * cam[6] + qy * cam[7] + qz * cam[8]) / zc * fp + W * 0.5
                sy = -(qx * cam[9] + qy * cam[10] + qz * cam[11]) / zc * fp + H * 0.5
                dist = math.sqrt(qx * qx + qy * qy + qz * qz)
                if s > 0 and d_prev > 0:
                    wpx = max(0.35, fp * 0.0025 * (1.0 - u * 0.85) / dist)
                    # tips catch more light
                    shade = 0.6 + 0.5 * u
                    x0 = int(min(px_prev, sx) - wpx - 1)
                    x1 = int(max(px_prev, sx) + wpx + 2)
                    y0 = int(min(py_prev, sy) - wpx - 1)
                    y1 = int(max(py_prev, sy) + wpx + 2)
                    if x1 < 0 or y1 < 0 or x0 >= W or y0 >= H or (x1 - x0) * (y1 - y0) > 40000:
                        px_prev, py_prev, d_prev = sx, sy, dist
                        continue
                    vx, vy = sx - px_prev, sy - py_prev
                    L2 = vx * vx + vy * vy + 1e-9
                    for yy in range(max(0, y0), min(H, y1)):
                        for xx in range(max(0, x0), min(W, x1)):
                            tt = ((xx - px_prev) * vx + (yy - py_prev) * vy) / L2
                            tt = min(max(tt, 0.0), 1.0)
                            ex = xx - (px_prev + tt * vx)
                            ey = yy - (py_prev + tt * vy)
                            dd = math.sqrt(ex * ex + ey * ey)
                            cov = min(1.0, wpx + 0.5 - dd)
                            if cov <= 0.0:
                                continue
                            bd = d_prev + (dist - d_prev) * tt
                            if depth[yy, xx] < bd:
                                continue
                            img[yy, xx, 0] = img[yy, xx, 0] * (1 - cov) + cr * shade * cov
                            img[yy, xx, 1] = img[yy, xx, 1] * (1 - cov) + cg * shade * cov
                            img[yy, xx, 2] = img[yy, xx, 2] * (1 - cov) + cb * shade * cov
                px_prev, py_prev, d_prev = sx, sy, dist


@njit(cache=True, parallel=True)
def _vis(dist, coarse, G, T, tx, ty, tz, radius):
    out = np.zeros(T.shape[0])
    for k in prange(T.shape[0]):
        px, py, pz = T[k, 0], T[k, 1] + 0.12, T[k, 2]
        lx, ly, lz = tx - px, ty - py, tz - pz
        dl = math.sqrt(lx * lx + ly * ly + lz * lz)
        out[k] = sdf.soft_shadow(dist, coarse, G, px, py, pz, lx / dl, ly / dl, lz / dl, dl - radius, 1.0 / radius)
    return out


def draw(img, depth, cam, B, T, t, torch, moon, seed=3, blades=14):
    H, W = depth.shape
    vis = _vis(B.dist, B.coarse, B.G, T, torch[0], torch[1], torch[2], 0.06)
    _draw(img, depth, np.asarray(cam, np.float64), W, H, T, t, np.asarray(torch[:6], np.float64),
          np.asarray(moon, np.float64), blades, seed, vis)
