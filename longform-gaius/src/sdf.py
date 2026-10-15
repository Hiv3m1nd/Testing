"""Sparse-banded SDF voxel tracer for the ruins (numba, CPU, linear-light HDR).

Geometry is baked once into a 2 cm int16 distance grid (mm units) with a
uint8 primitive-id grid, so eroded edges, chipped corners, fluted shafts and
rubble cores are real geometry with real silhouettes and real shadows. A
coarse 25 cm grid of conservative distances skips empty space. Sub-voxel
detail (pitting, tool marks, grain) comes from procedural normal and albedo
noise at shading time, which keeps 4K close-ups crisp.

Units: metres, y up. Radiance 1.0 = diffuse white (203 nits in the PQ master).
"""
from __future__ import annotations

import math

import numpy as np
from numba import njit, prange

# ============================================================================ noise


@njit(cache=True, inline="always")
def hash3(ix, iy, iz):
    h = (ix * 374761393 + iy * 668265263 + iz * 1440662683) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF) / 16777215.0


@njit(cache=True)
def vnoise(x, y, z):
    fx0, fy0, fz0 = math.floor(x), math.floor(y), math.floor(z)
    ix, iy, iz = int(fx0), int(fy0), int(fz0)
    fx, fy, fz = x - fx0, y - fy0, z - fz0
    ux = fx * fx * (3.0 - 2.0 * fx)
    uy = fy * fy * (3.0 - 2.0 * fy)
    uz = fz * fz * (3.0 - 2.0 * fz)
    a = hash3(ix, iy, iz)
    b = hash3(ix + 1, iy, iz)
    c = hash3(ix, iy + 1, iz)
    d = hash3(ix + 1, iy + 1, iz)
    e = hash3(ix, iy, iz + 1)
    f = hash3(ix + 1, iy, iz + 1)
    g = hash3(ix, iy + 1, iz + 1)
    h = hash3(ix + 1, iy + 1, iz + 1)
    k0 = a
    k1 = b - a
    k2 = c - a
    k3 = e - a
    k4 = a - b - c + d
    k5 = a - c - e + g
    k6 = a - b - e + f
    k7 = -a + b + c - d + e - f - g + h
    return k0 + k1 * ux + k2 * uy + k3 * uz + k4 * ux * uy + k5 * uy * uz + k6 * uz * ux + k7 * ux * uy * uz


@njit(cache=True)
def vnoise_d(x, y, z):
    """Value noise with analytic gradient (value, dx, dy, dz)."""
    fx0, fy0, fz0 = math.floor(x), math.floor(y), math.floor(z)
    ix, iy, iz = int(fx0), int(fy0), int(fz0)
    fx, fy, fz = x - fx0, y - fy0, z - fz0
    ux = fx * fx * (3.0 - 2.0 * fx)
    uy = fy * fy * (3.0 - 2.0 * fy)
    uz = fz * fz * (3.0 - 2.0 * fz)
    dux = 6.0 * fx * (1.0 - fx)
    duy = 6.0 * fy * (1.0 - fy)
    duz = 6.0 * fz * (1.0 - fz)
    a = hash3(ix, iy, iz)
    b = hash3(ix + 1, iy, iz)
    c = hash3(ix, iy + 1, iz)
    d = hash3(ix + 1, iy + 1, iz)
    e = hash3(ix, iy, iz + 1)
    f = hash3(ix + 1, iy, iz + 1)
    g = hash3(ix, iy + 1, iz + 1)
    h = hash3(ix + 1, iy + 1, iz + 1)
    k0 = a
    k1 = b - a
    k2 = c - a
    k3 = e - a
    k4 = a - b - c + d
    k5 = a - c - e + g
    k6 = a - b - e + f
    k7 = -a + b + c - d + e - f - g + h
    v = k0 + k1 * ux + k2 * uy + k3 * uz + k4 * ux * uy + k5 * uy * uz + k6 * uz * ux + k7 * ux * uy * uz
    gx = dux * (k1 + k4 * uy + k6 * uz + k7 * uy * uz)
    gy = duy * (k2 + k5 * uz + k4 * ux + k7 * uz * ux)
    gz = duz * (k3 + k6 * ux + k5 * uy + k7 * ux * uy)
    return v, gx, gy, gz


@njit(cache=True)
def fbm(x, y, z, octaves):
    a, s, tot = 0.5, 0.0, 0.0
    for _ in range(octaves):
        s += a * vnoise(x, y, z)
        tot += a
        x, y, z = x * 2.03 + 1.7, y * 2.03 - 0.3, z * 2.03 + 2.1
        a *= 0.5
    return s / tot


@njit(cache=True)
def fbm_d(x, y, z, octaves, gain):
    """fbm with gradient; returns (value, gx, gy, gz) in input-space units."""
    a, s, tot = 1.0, 0.0, 0.0
    gx = gy = gz = 0.0
    m = 1.0
    for _ in range(octaves):
        v, dx, dy, dz = vnoise_d(x, y, z)
        s += a * v
        gx += a * m * dx
        gy += a * m * dy
        gz += a * m * dz
        tot += a
        x, y, z = x * 2.03 + 1.7, y * 2.03 - 0.3, z * 2.03 + 2.1
        m *= 2.03
        a *= gain
    return s / tot, gx / tot, gy / tot, gz / tot


@njit(cache=True)
def cellular_id(x, y, z):
    """3D Worley: (F1, F2, random value of the nearest cell)."""
    ix, iy, iz = int(math.floor(x)), int(math.floor(y)), int(math.floor(z))
    f1, f2, cid = 9.0, 9.0, 0.0
    for a in range(-1, 2):
        for b in range(-1, 2):
            for c in range(-1, 2):
                cx, cy, cz = ix + a, iy + b, iz + c
                px = cx + hash3(cx, cy, cz)
                py = cy + hash3(cx + 17, cy - 5, cz + 3)
                pz = cz + hash3(cx - 9, cy + 23, cz - 11)
                d = math.sqrt((px - x) ** 2 + (py - y) ** 2 + (pz - z) ** 2)
                if d < f1:
                    f2 = f1
                    f1 = d
                    cid = hash3(cx + 101, cy - 37, cz + 59)
                elif d < f2:
                    f2 = d
    return f1, f2, cid


@njit(cache=True)
def cellular(x, y, z):
    """3D Worley: returns (F1, F2) distances in cell units."""
    ix, iy, iz = int(math.floor(x)), int(math.floor(y)), int(math.floor(z))
    f1, f2 = 9.0, 9.0
    for a in range(-1, 2):
        for b in range(-1, 2):
            for c in range(-1, 2):
                cx, cy, cz = ix + a, iy + b, iz + c
                px = cx + hash3(cx, cy, cz)
                py = cy + hash3(cx + 17, cy - 5, cz + 3)
                pz = cz + hash3(cx - 9, cy + 23, cz - 11)
                d = math.sqrt((px - x) ** 2 + (py - y) ** 2 + (pz - z) ** 2)
                if d < f1:
                    f2 = f1
                    f1 = d
                elif d < f2:
                    f2 = d
    return f1, f2


@njit(cache=True, inline="always")
def smoothstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


# ============================================================================ primitives
# row layout (float64[24]):
#  0 type (0 box, 1 cylinder, 2 ground, 3 rubble box)
#  1-3 centre, 4-6 half extents (cyl: radius, halflen, -), 7-15 rotation rows (local axes)
#  16 rounding, 17 flutes, 18 erosion amplitude, 19 seed,
#  20 break plane local-y (1e9 = none), 21 break roughness, 22 material, 23 relief panel (-1 none)
NP = 24


@njit(cache=True, inline="always")
def to_local(p, x, y, z):
    qx, qy, qz = x - p[1], y - p[2], z - p[3]
    return (p[7] * qx + p[8] * qy + p[9] * qz,
            p[10] * qx + p[11] * qy + p[12] * qz,
            p[13] * qx + p[14] * qy + p[15] * qz)


@njit(cache=True)
def ground_chips(x, z):
    """Angular stone fragments lying in the dirt: (height, mask)."""
    f1, f2, cid = cellular_id(x * 9.0, 0.3, z * 9.0)
    m = 0.0
    h = 0.0
    if cid > 0.84:
        m = smoothstep(0.0, 0.07, f2 - f1)
        h = (0.010 + 0.025 * hash3(int(cid * 1e6), 1, 2)) * m
    g1, g2, cid2 = cellular_id(x * 3.2 + 5.0, 1.3, z * 3.2)
    if cid2 > 0.92:
        m2 = smoothstep(0.0, 0.06, g2 - g1)
        h = max(h, (0.03 + 0.05 * hash3(int(cid2 * 1e6), 3, 4)) * m2)
        m = max(m, m2)
    return h, m


@njit(cache=True)
def ground_h(x, z):
    """Ground height: gentle undulation, ruts, stone chips; hollows hold standing water."""
    h = 0.10 * (fbm(x * 0.18, 0.5, z * 0.18, 4) - 0.5)
    h += 0.035 * (fbm(x * 0.9, 1.5, z * 0.9, 4) - 0.5)
    h += 0.008 * (fbm(x * 6.0, 2.5, z * 6.0, 3) - 0.5)
    # standing water: a long pool before the monument, a puddle beside the path
    q = ((x - 0.2) / 2.6) ** 2 + ((z - 12.35) / 0.48) ** 2 + 0.35 * (fbm(x * 1.4, 7.0, z * 1.4, 3) - 0.5)
    h -= 0.09 * smoothstep(1.0, 0.25, q)
    q2 = ((x - 1.05) / 0.95) ** 2 + ((z - 6.6) / 0.55) ** 2 + 0.45 * (fbm(x * 2.0, 3.0, z * 2.0, 3) - 0.5)
    h -= 0.07 * smoothstep(1.0, 0.3, q2)
    ch, cm = ground_chips(x, z)
    return h + ch * (1.0 - smoothstep(-0.01, -0.04, h))


@njit(cache=True)
def prim_sdf(p, x, y, z):
    t = int(p[0])
    if t == 2:
        return (y - ground_h(x, z)) * 0.85
    lx, ly, lz = to_local(p, x, y, z)
    seed = p[19]
    if t == 1:
        r, hl = p[4], p[5]
        rho = math.sqrt(lx * lx + lz * lz)
        fl = p[17]
        if fl > 0:
            ang = math.atan2(lz, lx)
            # concave flutes separated by narrow fillets
            c = math.cos(ang * fl)
            r = r - 0.022 * smoothstep(-0.55, 0.35, c) * (r / 0.38)
        dx = rho - r
        dy = abs(ly) - hl
        d = min(max(dx, dy), 0.0) + math.sqrt(max(dx, 0.0) ** 2 + max(dy, 0.0) ** 2)
    else:
        rr = p[16]
        qx = abs(lx) - p[4] + rr
        qy = abs(ly) - p[5] + rr
        qz = abs(lz) - p[6] + rr
        d = math.sqrt(max(qx, 0.0) ** 2 + max(qy, 0.0) ** 2 + max(qz, 0.0) ** 2) + min(max(qx, max(qy, qz)), 0.0) - rr
        if t == 3:
            # rubble core: mortar grooves between rough stones
            # rubble set in mortar: most cells hold a stone standing proud by its own amount, some are
            # empty sockets where the stone has fallen out; the mortar between is rough and irregular
            f1, f2, cid = cellular_id(x * 2.7 + seed, y * 3.6, z * 2.7)
            e1 = f2 - f1
            wob = 0.05 * (fbm(x * 9.0, y * 9.0, z * 9.0, 2) - 0.5)
            shape = smoothstep(0.02, 0.20, e1 + wob)
            if cid > 0.22:
                d -= (0.025 + 0.05 * hash3(int(cid * 1e5), 3, 7)) * shape ** 0.6
            else:
                d += 0.045 * shape
            g1, g2, cid2 = cellular_id(x * 8.0 - seed, y * 9.5, z * 8.0)
            d -= 0.012 * smoothstep(0.02, 0.14, g2 - g1) * (cid2 > 0.5) * (1.0 - shape)
            d += 0.02 * (fbm(x * 3.0, y * 3.0, z * 3.0, 3) - 0.5)
    # weathering: stronger near edges
    amp = p[18]
    if amp > 0.0 and d < 0.25:
        if t == 1:
            edge = abs(abs(ly) - p[5])
        else:
            ex = p[4] - abs(lx)
            ey = p[5] - abs(ly)
            ez = p[6] - abs(lz)
            # second-smallest of the three = distance to nearest edge
            m1 = min(ex, min(ey, ez))
            m3 = max(ex, max(ey, ez))
            edge = ex + ey + ez - m1 - m3
        w = 1.0 + 2.0 * math.exp(-max(edge, 0.0) / 0.05)
        n = fbm(x * 4.0 + seed, y * 4.0, z * 4.0, 5) - 0.5
        d += amp * w * n
        # chips: crisp bites taken out of edges (steep profile = sharp fracture rims)
        ch = fbm(x * 2.2 - seed, y * 2.2, z * 2.2, 4)
        d += 0.09 * smoothstep(0.55, 0.62, ch) * math.exp(-max(edge, 0.0) / 0.08)
        # pitting
        pit = fbm(x * 21.0, y * 21.0 + seed, z * 21.0, 2)
        d += 0.004 * smoothstep(0.62, 0.75, pit)
    # broken top
    if p[20] < 1e8:
        cut = ly - (p[20] + p[21] * (fbm(lx * 3.5 + seed, lz * 3.5, seed, 4) - 0.5) + 0.25 * p[21] * lx)
        d = max(d, cut)
    return d


@njit(cache=True)
def prim_bounds(p):
    """Axis-aligned bounds (minx,miny,minz,maxx,maxy,maxz) of a primitive."""
    t = int(p[0])
    if t == 1:
        hx, hy, hz = p[4], p[5], p[4]
    else:
        hx, hy, hz = p[4], p[5], p[6]
    ex = abs(p[7]) * hx + abs(p[10]) * hy + abs(p[13]) * hz
    ey = abs(p[8]) * hx + abs(p[11]) * hy + abs(p[14]) * hz
    ez = abs(p[9]) * hx + abs(p[12]) * hy + abs(p[15]) * hz
    return p[1] - ex, p[2] - ey, p[3] - ez, p[1] + ex, p[2] + ey, p[3] + ez


@njit(cache=True, parallel=True)
def bake(prims, dist, pid, ox, oy, oz, h, band):
    nx, ny, nz = dist.shape[0], dist.shape[1], dist.shape[2]
    for k in range(prims.shape[0]):
        p = prims[k]
        if int(p[0]) == 2:
            continue
        else:
            bx0, by0, bz0, bx1, by1, bz1 = prim_bounds(p)
            i0 = max(0, int((bx0 - band - ox) / h))
            i1 = min(nx, int((bx1 + band - ox) / h) + 2)
            j0 = max(0, int((by0 - band - oy) / h))
            j1 = min(ny, int((by1 + band - oy) / h) + 2)
            k0 = max(0, int((bz0 - band - oz) / h))
            k1 = min(nz, int((bz1 + band - oz) / h) + 2)
        for kk in prange(k0, k1):
            z = oz + kk * h
            for i in range(i0, i1):
                x = ox + i * h
                for j in range(j0, j1):
                    y = oy + j * h
                    d = prim_sdf(p, x, y, z)
                    dm = int(max(-band, min(band, d)) * 1000.0)
                    if dm < dist[i, j, kk]:
                        dist[i, j, kk] = dm
                        pid[i, j, kk] = k


@njit(cache=True, parallel=True)
def bake_coarse(dist, cs, out):
    """out[a,b,c] = min fine distance in its cs^3 block, minus a margin (conservative skip)."""
    for a in prange(out.shape[0]):
        for b in range(out.shape[1]):
            for c in range(out.shape[2]):
                m = 32000
                for i in range(a * cs, min((a + 1) * cs + 1, dist.shape[0])):
                    for j in range(b * cs, min((b + 1) * cs + 1, dist.shape[1])):
                        for k in range(c * cs, min((c + 1) * cs + 1, dist.shape[2])):
                            v = dist[i, j, k]
                            if v < m:
                                m = v
                out[a, b, c] = m


# ============================================================================ grid lookups
@njit(cache=True, inline="always")
def grid_d(dist, ox, oy, oz, inv_h, x, y, z):
    gx = (x - ox) * inv_h
    gy = (y - oy) * inv_h
    gz = (z - oz) * inv_h
    nx, ny, nz = dist.shape[0], dist.shape[1], dist.shape[2]
    if gx < 0 or gy < 0 or gz < 0 or gx >= nx - 1 or gy >= ny - 1 or gz >= nz - 1:
        return 1e9
    i, j, k = int(gx), int(gy), int(gz)
    fx, fy, fz = gx - i, gy - j, gz - k
    c000 = dist[i, j, k]
    c100 = dist[i + 1, j, k]
    c010 = dist[i, j + 1, k]
    c110 = dist[i + 1, j + 1, k]
    c001 = dist[i, j, k + 1]
    c101 = dist[i + 1, j, k + 1]
    c011 = dist[i, j + 1, k + 1]
    c111 = dist[i + 1, j + 1, k + 1]
    a = c000 + (c100 - c000) * fx
    b = c010 + (c110 - c010) * fx
    c = c001 + (c101 - c001) * fx
    d = c011 + (c111 - c011) * fx
    e = a + (b - a) * fy
    f = c + (d - c) * fy
    return (e + (f - e) * fz) * 0.001


@njit(cache=True, inline="always")
def coarse_d(coarse, ox, oy, oz, inv_ch, x, y, z):
    """Conservative distance to any surface from anywhere in this coarse cell (0 = near a surface)."""
    i = int((x - ox) * inv_ch)
    j = int((y - oy) * inv_ch)
    k = int((z - oz) * inv_ch)
    if i < 0 or j < 0 or k < 0 or i >= coarse.shape[0] or j >= coarse.shape[1] or k >= coarse.shape[2]:
        return 1e9
    return coarse[i, j, k]


@njit(cache=True)
def box_exit(x, y, z, dx, dy, dz, bmin, bmax):
    """Ray/AABB slab test: (tenter, texit); texit < tenter means miss."""
    t0, t1 = -1e30, 1e30
    for a in range(3):
        o = x if a == 0 else (y if a == 1 else z)
        d = dx if a == 0 else (dy if a == 1 else dz)
        if abs(d) < 1e-12:
            if o < bmin[a] or o > bmax[a]:
                return 1.0, -1.0
        else:
            ta = (bmin[a] - o) / d
            tb = (bmax[a] - o) / d
            if ta > tb:
                ta, tb = tb, ta
            t0 = max(t0, ta)
            t1 = min(t1, tb)
    return t0, t1


@njit(cache=True)
def scene_d(dist, coarse, G, x, y, z):
    """Distance at a point: grid inside, analytic ground estimate outside."""
    d = grid_d(dist, G[0], G[1], G[2], G[3], x, y, z)
    if d > 1e8:
        return y - 0.0
    return d


@njit(cache=True)
def march(dist, coarse, G, ox, oy, oz, dx, dy, dz, tmax):
    """Sphere-trace the baked scene. Returns t of hit or -1."""
    bmin = (G[0], G[1], G[2])
    bmax = (G[0] + (dist.shape[0] - 1) / G[3], G[1] + (dist.shape[1] - 1) / G[3], G[2] + (dist.shape[2] - 1) / G[3])
    t0, t1 = box_exit(ox, oy, oz, dx, dy, dz, bmin, bmax)
    if t1 < max(t0, 0.0):
        return -1.0
    t = max(t0, 0.0) + 1e-4
    tend = min(t1, tmax)
    band = G[5]
    for _ in range(400):
        if t > tend:
            return -1.0
        x, y, z = ox + t * dx, oy + t * dy, oz + t * dz
        dc = coarse_d(coarse, G[0], G[1], G[2], G[4], x, y, z)
        if dc > 0.0:
            t += dc
            continue
        d = grid_d(dist, G[0], G[1], G[2], G[3], x, y, z)
        if d >= band * 0.98:
            t += band * 0.8
            continue
        if d < 0.0008 * (1.0 + t * 0.5):
            return t
        t += d * 0.8
    return -1.0


@njit(cache=True)
def soft_shadow(dist, coarse, G, ox, oy, oz, dx, dy, dz, tmax, k):
    res = 1.0
    t = 0.02
    band = G[5]
    for _ in range(160):
        if t >= tmax:
            break
        x, y, z = ox + t * dx, oy + t * dy, oz + t * dz
        dc = coarse_d(coarse, G[0], G[1], G[2], G[4], x, y, z)
        if dc > 1e8:
            break
        if dc > 0.0:
            res = min(res, k * dc / t)
            t += dc
            continue
        d = grid_d(dist, G[0], G[1], G[2], G[3], x, y, z)
        if d > 1e8:
            break
        res = min(res, k * d / t)
        if res < 0.002:
            return 0.0
        t += max(min(d * 0.85, 0.25), 0.006)
    return smoothstep(0.0, 1.0, res)



# ============================================================================ the torchbearer
# fig: [x, z, heading, walk_phase, sway, active]; origin at the feet, facing local +z.
@njit(cache=True, inline="always")
def _smin(a, b, k):
    h = max(k - abs(a - b), 0.0) / k
    return min(a, b) - h * h * k * 0.25


@njit(cache=True)
def fig_sdf(fig, x, y, z):
    c, s = math.cos(fig[2]), math.sin(fig[2])
    qx, qz = x - fig[0], z - fig[1]
    lx = c * qx - s * qz
    lz = s * qx + c * qz
    ly = y - 0.012 * math.sin(fig[3] * 2.0)              # walking bob
    sway = fig[4]
    # cloak: a round cone from the hem (r 0.33) to the shoulders (r 0.19), swinging at the hem
    h = 1.36
    u = min(max(ly / h, 0.0), 1.0)
    cx = lx - sway * (1.0 - u) ** 2 - 0.035 * math.sin(fig[3]) * (1.0 - u) ** 2
    # a cloak is wider across the shoulders than it is deep
    cz = (lz + 0.03 * math.cos(fig[3]) * (1.0 - u) ** 2) * (1.15 + 0.25 * u)
    r1, r2 = 0.31, 0.215
    b = (r1 - r2) / h
    a = math.sqrt(1.0 - b * b)
    py = ly - 0.04
    qr = math.sqrt(cx * cx + cz * cz)
    k = -b * qr + a * py
    if k < 0.0:
        d = math.sqrt(qr * qr + py * py) - r1
    elif k > a * h:
        d = math.sqrt(qr * qr + (py - h) ** 2) - r2
    else:
        d = a * qr + b * py - r1
    # folds near the hem
    ang = math.atan2(cz, cx)
    d += 0.012 * math.sin(ang * 9.0 + ly * 3.0) * (1.0 - u) ** 1.5
    d *= 0.8   # the anisotropic squash above stretches distances; stay conservative
    # hooded head: the hood rises to a soft point at the back
    hx, hy, hz = lx, ly - 1.60, lz + 0.015
    d = _smin(d, math.sqrt(hx * hx + hy * hy * 0.85 + hz * hz) - 0.13, 0.07)
    px2, py2, pz2 = lx, ly - 1.70, lz + 0.07
    d = _smin(d, math.sqrt(px2 * px2 * 1.6 + py2 * py2 + pz2 * pz2 * 1.3) - 0.08, 0.05)
    # the torch arm, reaching forward and up on the right
    ax, ay, az = 0.16, 1.38, 0.02
    bx, by, bz = 0.25, 1.30, 0.34
    pax, pay, paz = lx - ax, ly - ay, lz - az
    bax, bay, baz = bx - ax, by - ay, bz - az
    t = min(max((pax * bax + pay * bay + paz * baz) / (bax * bax + bay * bay + baz * baz), 0.0), 1.0)
    ex, ey, ez = pax - bax * t, pay - bay * t, paz - baz * t
    d = _smin(d, math.sqrt(ex * ex + ey * ey + ez * ez) - 0.058, 0.04)
    return d


@njit(cache=True)
def fig_hit(fig, ox, oy, oz, dx, dy, dz, tmax):
    """Ray vs the figure: bounding cylinder, then sphere tracing. Returns t or -1."""
    if fig[5] <= 0.0:
        return -1.0
    # cylinder around the figure (radius 0.75, y 0..1.95)
    px, pz = ox - fig[0], oz - fig[1]
    A = dx * dx + dz * dz
    B = 2 * (px * dx + pz * dz)
    C = px * px + pz * pz - 0.75 * 0.75
    t0, t1 = 0.0, tmax
    if A > 1e-12:
        disc = B * B - 4 * A * C
        if disc < 0:
            return -1.0
        sq = math.sqrt(disc)
        t0 = max(t0, (-B - sq) / (2 * A))
        t1 = min(t1, (-B + sq) / (2 * A))
    elif C > 0:
        return -1.0
    if abs(dy) > 1e-9:
        ta, tb = (0.0 - oy) / dy, (1.95 - oy) / dy
        if ta > tb:
            ta, tb = tb, ta
        t0, t1 = max(t0, ta), min(t1, tb)
    elif oy < 0.0 or oy > 1.95:
        return -1.0
    if t1 <= t0:
        return -1.0
    t = t0
    for _ in range(80):
        if t > t1:
            return -1.0
        d = fig_sdf(fig, ox + t * dx, oy + t * dy, oz + t * dz)
        if d < 0.0008:
            return t
        t += max(d * 0.9, 0.001)
    return -1.0


@njit(cache=True)
def fig_shadow(fig, ox, oy, oz, dx, dy, dz, tmax, k):
    """Soft visibility through the figure along a shadow ray."""
    if fig[5] <= 0.0:
        return 1.0
    # quick reject: closest approach of the ray to the figure's axis
    px, pz = fig[0] - ox, fig[1] - oz
    hl = math.sqrt(dx * dx + dz * dz)
    if hl > 1e-6:
        tc = (px * dx + pz * dz) / (hl * hl)
        tc = min(max(tc, 0.0), tmax)
        cx, cz = ox + tc * dx - fig[0], oz + tc * dz - fig[1]
        if cx * cx + cz * cz > 0.9 * 0.9:
            return 1.0
    res = 1.0
    t = 0.02
    for _ in range(64):
        if t >= tmax:
            break
        y = oy + t * dy
        if y > 2.1 and dy > 0:
            break
        d = fig_sdf(fig, ox + t * dx, y, oz + t * dz)
        res = min(res, k * d / t)
        if res < 0.002:
            return 0.0
        t += max(d * 0.9, 0.01)
    return smoothstep(0.0, 1.0, res)


# ============================================================================ ground heightfield
# GH = [x0, z0, inv_h, hmax, nx, nz]; outside the baked area the ground is flat (y = 0).
@njit(cache=True, inline="always")
def hf(gh, GH, x, z):
    gx = (x - GH[0]) * GH[2]
    gz = (z - GH[1]) * GH[2]
    if gx < 0 or gz < 0 or gx >= gh.shape[1] - 1 or gz >= gh.shape[0] - 1:
        return 0.0
    i, k = int(gx), int(gz)
    fx, fz = gx - i, gz - k
    a = gh[k, i] + (gh[k, i + 1] - gh[k, i]) * fx
    b = gh[k + 1, i] + (gh[k + 1, i + 1] - gh[k + 1, i]) * fx
    return a + (b - a) * fz


@njit(cache=True)
def hf_hit(gh, GH, wl, ox, oy, oz, dx, dy, dz, tmax):
    """Intersect the ground (water fills hollows up to wl). Returns t or -1."""
    top = max(GH[3], wl) + 0.001
    if dy >= 0.0 and oy > top:
        return -1.0
    t = 0.0
    if oy > top:
        t = (top - oy) / dy
    hor = math.sqrt(max(1.0 - dy * dy, 0.0))
    tp = t
    dp = 1.0
    for _ in range(600):
        if t > tmax:
            return -1.0
        x, y, z = ox + t * dx, oy + t * dy, oz + t * dz
        h = max(hf(gh, GH, x, z), wl)
        dh = y - h
        if dh < 0.0:
            # bisection between tp (above) and t (below)
            lo, hi = tp, t
            for _ in range(10):
                m = 0.5 * (lo + hi)
                xm, ym, zm = ox + m * dx, oy + m * dy, oz + m * dz
                if ym - max(hf(gh, GH, xm, zm), wl) < 0.0:
                    hi = m
                else:
                    lo = m
            return 0.5 * (lo + hi)
        if dy >= 0.0 and y > top:
            return -1.0
        tp = t
        t += max(dh / (max(-dy, 0.0) + 0.35 * hor), 0.002 + 0.002 * t)
    return -1.0


@njit(cache=True)
def sky_color(rdx, rdy, rdz, moon, sky, frame):
    el = rdy
    az = math.atan2(rdx, rdz)
    ridge = 0.12 + 0.11 * fbm(az * 1.3 + 7.0, 0.0, 0.0, 6) + 0.03 * fbm(az * 8.0, 1.0, 0.0, 4)
    if el < ridge:
        # the Toçak Dağı: moonlit upper slopes, dark lower flanks, a few pale tomb facades
        cliff = fbm(az * 18.0, el * 18.0, 2.0, 5)
        shade = 0.004 + 0.010 * cliff + 0.012 * smoothstep(ridge - 0.10, ridge, el) * cliff
        hh = hash3(int(az * 90.0), int(el * 220.0), 5)
        if el > ridge * 0.40 and el < ridge * 0.80 and hh > 0.985:
            shade += 0.006
        sr, sg, sb = shade * 0.62, shade * 0.74, shade * 1.0
        hz = math.exp(-max(el, 0.0) * 12.0) * 0.7
        return (sr * (1 - hz) + sky[3] * hz, sg * (1 - hz) + sky[4] * hz, sb * (1 - hz) + sky[5] * hz)
    tt = smoothstep(0.0, 0.7, el)
    sr = sky[3] * (1 - tt) + sky[0] * tt
    sg = sky[4] * (1 - tt) + sky[1] * tt
    sb = sky[5] * (1 - tt) + sky[2] * tt
    md = rdx * moon[0] + rdy * moon[1] + rdz * moon[2]
    if md > 0.0:
        glow = math.exp((md - 1.0) * 600.0) * 0.35 + math.exp((md - 1.0) * 30.0) * 0.035
        sr += glow * 0.75
        sg += glow * 0.85
        sb += glow * 1.0
        if md > 0.99996:
            lim = 24.0 * (0.80 + 0.2 * fbm(rdx * 4000.0, rdy * 4000.0, rdz * 4000.0, 3))
            sr += lim
            sg += lim * 0.98
            sb += lim * 0.93
    cl = fbm(az * 2.6 + frame * 0.0005, el * 8.0, 4.0, 6)
    cl = smoothstep(0.50, 0.78, cl) * smoothstep(ridge, ridge + 0.3, el)
    lit = 1.0 + 3.0 * math.exp((md - 1.0) * 18.0) if md > 0.0 else 1.0
    sr = sr * (1 - 0.7 * cl) + 0.010 * cl * lit
    sg = sg * (1 - 0.7 * cl) + 0.012 * cl * lit
    sb = sb * (1 - 0.7 * cl) + 0.017 * cl * lit
    sxs = int((az + 4.0) * 1600.0)
    sys = int((el + 1.0) * 1600.0)
    hs = hash3(sxs, sys, 7)
    if hs > 0.9990:
        tw = 0.6 + 0.4 * math.sin(frame * 0.35 + hs * 7000.0)
        st = (hs - 0.9990) / 0.0010 * 0.6 * tw * (1 - cl)
        sr += st * 0.9
        sg += st * 0.95
        sb += st * 1.1
    return sr, sg, sb


# ============================================================================ the frame
@njit(cache=True, parallel=True, fastmath=True)
def render(W, H, cam, dist, pid, coarse, G, gh, GH, prims, mats, panels, torch, moon, sky, fog, frame, jitter, fig):
    """cam: [ox,oy,oz, fx,fy,fz, rx,ry,rz, ux,uy,uz, focal_px]
    torch: [x,y,z, r,g,b (radiant intensity), source radius, scatter, bounce]
    moon: [dx,dy,dz, r,g,b]; sky: [zenith rgb, horizon rgb]; fog: [density, height falloff, water level]
    Returns (rgb float32 HxWx3, depth float32 HxW)."""
    img = np.zeros((H, W, 3), np.float32)
    depth = np.full((H, W), 1e4, np.float32)
    ox, oy, oz = cam[0], cam[1], cam[2]
    wl = fog[2]
    for j in prange(H):
        for i in range(W):
            jx = jitter[0] + (hash3(i, j, frame) - 0.5) * jitter[2]
            jy = jitter[1] + (hash3(j, i, frame + 7) - 0.5) * jitter[2]
            sx = (i + 0.5 + jx - W * 0.5) / cam[12]
            sy = -(j + 0.5 + jy - H * 0.5) / cam[12]
            dx = cam[3] + sx * cam[6] + sy * cam[9]
            dy = cam[4] + sx * cam[7] + sy * cam[10]
            dz = cam[5] + sx * cam[8] + sy * cam[11]
            L = math.sqrt(dx * dx + dy * dy + dz * dz)
            dx, dy, dz = dx / L, dy / L, dz / L
            r = g = b = 0.0
            weight = 1.0
            rox, roy, roz, rdx, rdy, rdz = ox, oy, oz, dx, dy, dz
            tprim = 1e4
            for bounce in range(2):
                to = march(dist, coarse, G, rox, roy, roz, rdx, rdy, rdz, 300.0)
                tg = hf_hit(gh, GH, wl if bounce == 0 else -9.0, rox, roy, roz, rdx, rdy, rdz,
                            to if to > 0 else 400.0)
                tnear = 400.0
                if to > 0:
                    tnear = to
                if tg > 0 and tg < tnear:
                    tnear = tg
                tf = fig_hit(fig, rox, roy, roz, rdx, rdy, rdz, tnear)
                if tf > 0:
                    # ---- the cloaked torchbearer: dark wool, lit only by what reaches it
                    px, py, pz = rox + tf * rdx, roy + tf * rdy, roz + tf * rdz
                    if bounce == 0:
                        tprim = tf
                    e = 0.004
                    nx = fig_sdf(fig, px + e, py, pz) - fig_sdf(fig, px - e, py, pz)
                    ny = fig_sdf(fig, px, py + e, pz) - fig_sdf(fig, px, py - e, pz)
                    nz = fig_sdf(fig, px, py, pz + e) - fig_sdf(fig, px, py, pz - e)
                    nl = math.sqrt(nx * nx + ny * ny + nz * nz) + 1e-12
                    nx, ny, nz = nx / nl, ny / nl, nz / nl
                    wv = fbm(px * 40.0, py * 40.0, pz * 40.0, 3)
                    ar, ag, ab = 0.085 * (0.8 + 0.4 * wv), 0.070 * (0.8 + 0.4 * wv), 0.055 * (0.8 + 0.4 * wv)
                    lx_, ly_, lz_ = torch[0] - px, torch[1] - py, torch[2] - pz
                    d2 = lx_ * lx_ + ly_ * ly_ + lz_ * lz_
                    dl = math.sqrt(d2)
                    lx_, ly_, lz_ = lx_ / dl, ly_ / dl, lz_ / dl
                    ndl = nx * lx_ + ny * ly_ + nz * lz_
                    cr = cg = cb = 0.0
                    # wool scatters light around its edges: wrapped diffuse gives the rim its glow
                    wrap = (ndl + 0.35) / 1.35
                    if wrap > 0.0:
                        shf = fig_shadow(fig, px + nx * 0.01, py + ny * 0.01, pz + nz * 0.01, lx_, ly_, lz_,
                                         dl - torch[6], 6.0)
                        c_ = wrap * shf / (d2 + 0.02)
                        cr += ar * c_ * torch[3] * 1.6
                        cg += ag * c_ * torch[4] * 1.6
                        cb += ab * c_ * torch[5] * 1.6
                    mdl = nx * moon[0] + ny * moon[1] + nz * moon[2]
                    if mdl > 0:
                        cr += ar * mdl * moon[3]
                        cg += ag * mdl * moon[4]
                        cb += ab * mdl * moon[5]
                    amb = 0.55 + 0.45 * ny
                    cr += ar * sky[0] * amb
                    cg += ag * sky[1] * amb
                    cb += ab * sky[2] * amb
                    r += weight * cr
                    g += weight * cg
                    b += weight * cb
                    break
                if to < 0 and tg < 0:
                    sr, sg, sb = sky_color(rdx, rdy, rdz, moon, sky, frame)
                    r += weight * sr
                    g += weight * sg
                    b += weight * sb
                    break
                ground = tg > 0 and (to < 0 or tg < to)
                t = tg if ground else to
                px, py, pz = rox + t * rdx, roy + t * rdy, roz + t * rdz
                if bounce == 0:
                    tprim = t
                hgt = hf(gh, GH, px, pz)
                if ground and bounce == 0 and hgt < wl - 0.001:
                    # ---- water: rippled mirror over a dark bed
                    nv, ngx, ngy, ngz = fbm_d(px * 7.0 + frame * 0.01, frame * 0.03, pz * 7.0, 4, 0.5)
                    nx_, nz_ = -ngx * 0.010, -ngz * 0.010
                    nn = math.sqrt(nx_ * nx_ + 1.0 + nz_ * nz_)
                    nx_, ny_, nz_ = nx_ / nn, 1.0 / nn, nz_ / nn
                    cosi = -(rdx * nx_ + rdy * ny_ + rdz * nz_)
                    fres = 0.02 + 0.98 * (1.0 - cosi) ** 5
                    bed = 0.004 * (1.0 - fres)
                    r += bed * 0.5
                    g += bed * 0.6
                    b += bed * 0.5
                    weight = fres * 0.9
                    rox, roy, roz = px, wl + 1e-3, pz
                    rdx, rdy, rdz = rdx + 2 * cosi * nx_, rdy + 2 * cosi * ny_, rdz + 2 * cosi * nz_
                    continue
                # ---- normal
                if ground:
                    e = 0.012
                    nx = hf(gh, GH, px - e, pz) - hf(gh, GH, px + e, pz)
                    nz = hf(gh, GH, px, pz - e) - hf(gh, GH, px, pz + e)
                    ny = 2.0 * e
                    nl = math.sqrt(nx * nx + ny * ny + nz * nz)
                    nx, ny, nz = nx / nl, ny / nl, nz / nl
                    k = 0
                else:
                    e = 0.6 / G[3]
                    nx = grid_d(dist, G[0], G[1], G[2], G[3], px + e, py, pz) - grid_d(dist, G[0], G[1], G[2], G[3], px - e, py, pz)
                    ny = grid_d(dist, G[0], G[1], G[2], G[3], px, py + e, pz) - grid_d(dist, G[0], G[1], G[2], G[3], px, py - e, pz)
                    nz = grid_d(dist, G[0], G[1], G[2], G[3], px, py, pz + e) - grid_d(dist, G[0], G[1], G[2], G[3], px, py, pz - e)
                    nl = math.sqrt(nx * nx + ny * ny + nz * nz)
                    if nl > 1e6 or nl < 1e-9:
                        nx, ny, nz, nl = 0.0, 1.0, 0.0, 1.0
                    nx, ny, nz = nx / nl, ny / nl, nz / nl
                    gi = min(max(int((px - G[0]) * G[3] + 0.5), 0), dist.shape[0] - 1)
                    gj = min(max(int((py - G[1]) * G[3] + 0.5), 0), dist.shape[1] - 1)
                    gk = min(max(int((pz - G[2]) * G[3] + 0.5), 0), dist.shape[2] - 1)
                    k = pid[gi, gj, gk]
                pr = prims[k]
                mat = int(pr[22])
                cav = 1.0
                panel = int(pr[23])
                if panel >= 0 and not ground:
                    lx, ly, lz = to_local(pr, px, py, pz)
                    fnz = -(pr[13] * nx + pr[14] * ny + pr[15] * nz)
                    if fnz > 0.5 and abs(lx) < pr[4] * 0.96 and abs(ly) < pr[5] * 0.94:
                        u = (lx / pr[4]) * 0.5 + 0.5
                        v = 0.5 - (ly / pr[5]) * 0.5
                        PH, PW = panels.shape[1], panels.shape[2]
                        fx_ = min(max(u, 0.0), 1.0) * (PW - 2)
                        fy_ = min(max(v, 0.0), 1.0) * (PH - 2)
                        x0, y0 = int(fx_), int(fy_)
                        ax_, ay_ = fx_ - x0, fy_ - y0
                        h00 = panels[panel, y0, x0]
                        h10 = panels[panel, y0, x0 + 1]
                        h01 = panels[panel, y0 + 1, x0]
                        h11 = panels[panel, y0 + 1, x0 + 1]
                        hh = (h00 * (1 - ax_) + h10 * ax_) * (1 - ay_) + (h01 * (1 - ax_) + h11 * ax_) * ay_
                        du = ((h10 - h00) * (1 - ay_) + (h11 - h01) * ay_) * (PW - 2) / (2 * pr[4])
                        dv = ((h01 - h00) * (1 - ax_) + (h11 - h10) * ax_) * (PH - 2) / (2 * pr[5])
                        depth_m = 0.045
                        nx = nx - depth_m * (du * pr[7] - dv * pr[10])
                        ny = ny - depth_m * (du * pr[8] - dv * pr[11])
                        nz = nz - depth_m * (du * pr[9] - dv * pr[12])
                        nl = math.sqrt(nx * nx + ny * ny + nz * nz)
                        nx, ny, nz = nx / nl, ny / nl, nz / nl
                        cav = 0.45 + 0.55 * smoothstep(0.0, 0.6, hh)
                # ---- micro detail (analytic-gradient fbm)
                sc = mats[mat, 4]
                bv, bgx, bgy, bgz = fbm_d(px * sc * 9.0, py * sc * 9.0, pz * sc * 9.0, 5, 0.55)
                amt = mats[mat, 3] * 0.035 / sc
                dn = bgx * nx + bgy * ny + bgz * nz
                nx -= amt * (bgx - dn * nx)
                ny -= amt * (bgy - dn * ny)
                nz -= amt * (bgz - dn * nz)
                nl = math.sqrt(nx * nx + ny * ny + nz * nz)
                nx, ny, nz = nx / nl, ny / nl, nz / nl
                # ---- albedo
                ar, ag, ab = mats[mat, 0], mats[mat, 1], mats[mat, 2]
                n1 = fbm(px * sc, py * sc, pz * sc, 4)
                n2 = fbm(px * sc * 0.23 + 5.0, py * sc * 0.23, pz * sc * 0.23, 3)
                k_ = (0.78 + 0.40 * (n1 - 0.5) + 0.18 * (bv - 0.5)) * (0.85 + 0.3 * n2)
                ar *= k_
                ag *= k_ * (0.98 + 0.04 * n2)
                ab *= k_ * (0.95 + 0.08 * n2)
                if mat != 0:
                    st = fbm(px * 3.0, py * 0.30, pz * 3.0, 5)
                    sk = 1.0 - 0.38 * smoothstep(0.50, 0.80, st) * (0.6 + 0.4 * max(-ny, 0.0) + 0.4 * (1 - abs(ny)))
                    li = smoothstep(0.60, 0.78, fbm(px * 2.2 + 9.0, py * 2.2, pz * 2.2, 5)) * (0.25 + 0.75 * max(ny, 0.0))
                    li *= 0.55
                    ar = (ar * sk) * (1 - li) + ar * 0.62 * li
                    ag = (ag * sk) * (1 - li) + ag * 0.64 * li
                    ab = (ab * sk) * (1 - li) + ab * 0.48 * li
                else:
                    gr = smoothstep(0.45, 0.72, fbm(px * 0.8, 3.0, pz * 0.8, 5))
                    ar = ar * (1 - 0.35 * gr) + 0.26 * 0.35 * gr
                    ag = ag * (1 - 0.35 * gr) + 0.24 * 0.35 * gr
                    ab = ab * (1 - 0.35 * gr) + 0.13 * 0.35 * gr
                    chh, chm = ground_chips(px, pz)
                    ar = ar * (1 - chm) + 0.40 * chm * (0.8 + 0.4 * bv)
                    ag = ag * (1 - chm) + 0.38 * chm * (0.8 + 0.4 * bv)
                    ab = ab * (1 - chm) + 0.35 * chm * (0.8 + 0.4 * bv)
                    damp = smoothstep(wl + 0.025, wl, hgt)
                    ar *= 1 - 0.55 * damp
                    ag *= 1 - 0.50 * damp
                    ab *= 1 - 0.45 * damp
                ar *= cav
                ag *= cav
                ab *= cav
                # ---- ambient occlusion: objects grid + ground
                ao = 0.0
                sca = 1.0
                for s in range(5):
                    hs_ = 0.03 + 0.14 * s * s / 4.0
                    qx, qy, qz = px + nx * hs_, py + ny * hs_, pz + nz * hs_
                    dd = grid_d(dist, G[0], G[1], G[2], G[3], qx, qy, qz)
                    if not ground:
                        dd = min(dd, qy - hf(gh, GH, qx, qz))
                    if dd > 1e8:
                        dd = hs_
                    ao += max(hs_ - dd, 0.0) * sca
                    sca *= 0.72
                ao = min(max(1.0 - 2.4 * ao, 0.0), 1.0)
                # ---- torch
                lx_, ly_, lz_ = torch[0] - px, torch[1] - py, torch[2] - pz
                d2 = lx_ * lx_ + ly_ * ly_ + lz_ * lz_
                dl = math.sqrt(d2)
                lx_, ly_, lz_ = lx_ / dl, ly_ / dl, lz_ / dl
                ndl = nx * lx_ + ny * ly_ + nz * lz_
                cr = cg = cb = 0.0
                if ndl > 0.0:
                    sh = soft_shadow(dist, coarse, G, px + nx * 0.004, py + ny * 0.004, pz + nz * 0.004,
                                     lx_, ly_, lz_, dl - torch[6], 1.0 / max(torch[6], 0.01))
                    if sh > 0.0:
                        sh *= fig_shadow(fig, px + nx * 0.004, py + ny * 0.004, pz + nz * 0.004, lx_, ly_, lz_,
                                         dl - torch[6], 1.0 / max(torch[6], 0.01))
                    if sh > 0.0:
                        att = 1.0 / (d2 + 0.02)
                        hx, hy, hz = lx_ - rdx, ly_ - rdy, lz_ - rdz
                        hl_ = math.sqrt(hx * hx + hy * hy + hz * hz) + 1e-9
                        spec = mats[mat, 5] * math.pow(max(0.0, (nx * hx + ny * hy + nz * hz) / hl_), 30.0)
                        c_ = ndl * sh * att
                        cr += (ar + spec) * c_ * torch[3]
                        cg += (ag + spec) * c_ * torch[4]
                        cb += (ab + spec) * c_ * torch[5]
                fb = torch[8] / (d2 + 1.0) * ao
                cr += ar * fb * torch[3]
                cg += ag * fb * torch[4]
                cb += ab * fb * torch[5]
                # ---- moon
                mdl = nx * moon[0] + ny * moon[1] + nz * moon[2]
                if mdl > 0.0:
                    shm = soft_shadow(dist, coarse, G, px + nx * 0.004, py + ny * 0.004, pz + nz * 0.004,
                                      moon[0], moon[1], moon[2], 40.0, 30.0)
                    cr += ar * mdl * shm * moon[3]
                    cg += ag * mdl * shm * moon[4]
                    cb += ab * mdl * shm * moon[5]
                # ---- sky ambient
                amb = (0.55 + 0.45 * ny) * ao
                cr += ar * sky[0] * amb
                cg += ag * sky[1] * amb
                cb += ab * sky[2] * amb
                # ---- height fog
                fd = fog[0] * math.exp(-max(py, 0.0) * fog[1])
                tr = math.exp(-t * fd)
                cr = cr * tr + sky[3] * 0.45 * (1 - tr)
                cg = cg * tr + sky[4] * 0.45 * (1 - tr)
                cb = cb * tr + sky[5] * 0.55 * (1 - tr)
                r += weight * cr
                g += weight * cg
                b += weight * cb
                break
            # ---- torch in-scattering along the primary ray (single scattering, analytic)
            vx, vy, vz = torch[0] - ox, torch[1] - oy, torch[2] - oz
            s0 = vx * dx + vy * dy + vz * dz
            h2 = vx * vx + vy * vy + vz * vz - s0 * s0
            hh_ = math.sqrt(max(h2, 1e-6))
            T = min(tprim, 60.0)
            integ = (math.atan((T - s0) / hh_) - math.atan(-s0 / hh_)) / hh_
            sc_ = torch[7] * integ
            r += sc_ * torch[3]
            g += sc_ * torch[4]
            b += sc_ * torch[5]
            img[j, i, 0], img[j, i, 1], img[j, i, 2] = r, g, b
            depth[j, i] = tprim
    return img, depth


@njit(cache=True, parallel=True)
def bake_ground(gh, x0, z0, h):
    for k in prange(gh.shape[0]):
        for i in range(gh.shape[1]):
            x = x0 + i * h
            z = z0 + k * h
            # fade to flat at the borders so the far plane joins seamlessly
            fade = min(1.0, min(i, gh.shape[1] - 1 - i, k, gh.shape[0] - 1 - k) * h / 1.5)
            gh[k, i] = ground_h(x, z) * fade


# ============================================================================ python helpers
def rot(yaw=0.0, pitch=0.0, roll=0.0):
    """Rows are the local axes expressed in world space."""
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    Ry = np.array([[cy, 0, -sy], [0, 1, 0], [sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, sp], [0, -sp, cp]])
    Rz = np.array([[cr, sr, 0], [-sr, cr, 0], [0, 0, 1]])
    return Rz @ Rx @ Ry


def axis_frame(axis):
    """Rotation whose local y is `axis`."""
    a = np.asarray(axis, float)
    a /= np.linalg.norm(a)
    ref = np.array([1.0, 0, 0]) if abs(a[0]) < 0.9 else np.array([0, 0, 1.0])
    x = ref - a * (ref @ a)
    x /= np.linalg.norm(x)
    z = np.cross(x, a)
    return np.array([x, a, z])


def prim(kind, centre, half, R=None, rounding=0.01, flutes=0, erosion=0.012, seed=0.0,
         break_y=1e9, break_amp=0.0, mat=1, panel=-1):
    R = np.eye(3) if R is None else np.asarray(R, float)
    row = np.zeros(NP)
    row[0] = kind
    row[1:4] = centre
    row[4:7] = half
    row[7:16] = R.reshape(-1)
    row[16], row[17], row[18], row[19] = rounding, flutes, erosion, seed
    row[20], row[21], row[22], row[23] = break_y, break_amp, mat, panel
    return row


def look_at(pos, target, focal_px, roll=0.0):
    pos = np.asarray(pos, float)
    f = np.asarray(target, float) - pos
    f /= np.linalg.norm(f)
    up = np.array([0.0, 1.0, 0.0])
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    if roll:
        c, s = math.cos(roll), math.sin(roll)
        r, u = c * r + s * u, -s * r + c * u
    # rt convention: +x screen right = r
    return np.array([*pos, *f, *(-r), *u, focal_px], np.float64)


class Baked:
    def __init__(self, prims, lo, hi, h=0.02, band=0.3, coarse_cells=12, ground_res=0.01):
        self.prims = np.ascontiguousarray(prims, np.float64)
        lo, hi = np.asarray(lo, float), np.asarray(hi, float)
        n = np.ceil((hi - lo) / h).astype(int) + 1
        self.dist = np.full(tuple(n), int(band * 1000), np.int16)
        self.pid = np.zeros(tuple(n), np.uint8)
        bake(self.prims, self.dist, self.pid, lo[0], lo[1], lo[2], h, band)
        cs = coarse_cells
        nc = (n + cs - 1) // cs
        cmin = np.zeros(tuple(nc), np.int32)
        bake_coarse(self.dist, cs, cmin)
        ch = h * cs
        # cells whose voxels all sit at least ~band from any surface are empty; the distance
        # transform over cells gives a conservative skip distance for points inside them
        from scipy.ndimage import distance_transform_edt
        occupied = cmin < int(band * 1000 * 0.9)
        e = distance_transform_edt(~occupied)
        safe = np.where(occupied, 0.0, np.maximum((e - 1.75) * ch, 0.0) + band * 0.85)
        self.coarse = safe.astype(np.float32)
        ngx = int(round((hi[0] - lo[0]) / ground_res)) + 1
        ngz = int(round((hi[2] - lo[2]) / ground_res)) + 1
        self.gh = np.zeros((ngz, ngx), np.float32)
        bake_ground(self.gh, lo[0], lo[2], ground_res)
        self.GH = np.array([lo[0], lo[2], 1.0 / ground_res, float(self.gh.max()), ngx, ngz], np.float64)
        self.G = np.array([lo[0], lo[1], lo[2], 1.0 / h, 1.0 / ch, band], np.float64)
