"""Numba CPU ray tracer for the torch-lit ruins (linear-light HDR output).

Scene: analytic primitives (oriented boxes, capped cylinders, a bumpy ground
plane) with procedural weathered limestone, fluted column drums and carved
relief panels sampled from height maps. Lighting: a flickering torch (point
light, true shadow rays, soft via jitter), moonlight (directional, shadows),
dim sky ambient, an analytic single-scattering glow around the flame, height
fog. Units: metres; y up; 1.0 radiance = diffuse white (203 nits in the PQ
master).
"""
from __future__ import annotations

import math

import numpy as np
from numba import njit, prange

# ----------------------------------------------------------------------------- noise


@njit(cache=True, inline="always")
def _hash(ix, iy, iz):
    h = (ix * 374761393 + iy * 668265263 + iz * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF) / 16777215.0


@njit(cache=True, inline="always")
def _fade(t):
    return t * t * (3.0 - 2.0 * t)


@njit(cache=True)
def vnoise(x, y, z):
    ix, iy, iz = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = _fade(x - ix), _fade(y - iy), _fade(z - iz)
    ix, iy, iz = int(ix), int(iy), int(iz)
    c000 = _hash(ix, iy, iz)
    c100 = _hash(ix + 1, iy, iz)
    c010 = _hash(ix, iy + 1, iz)
    c110 = _hash(ix + 1, iy + 1, iz)
    c001 = _hash(ix, iy, iz + 1)
    c101 = _hash(ix + 1, iy, iz + 1)
    c011 = _hash(ix, iy + 1, iz + 1)
    c111 = _hash(ix + 1, iy + 1, iz + 1)
    x00 = c000 + (c100 - c000) * fx
    x10 = c010 + (c110 - c010) * fx
    x01 = c001 + (c101 - c001) * fx
    x11 = c011 + (c111 - c011) * fx
    y0 = x00 + (x10 - x00) * fy
    y1 = x01 + (x11 - x01) * fy
    return y0 + (y1 - y0) * fz


@njit(cache=True)
def fbm(x, y, z, octaves):
    a, s, tot = 0.5, 0.0, 0.0
    for _ in range(octaves):
        s += a * vnoise(x, y, z)
        tot += a
        x *= 2.03
        y *= 2.03
        z *= 2.03
        a *= 0.5
    return s / tot


# ----------------------------------------------------------------------------- intersections
# boxes:  [cx, cy, cz, hx, hy, hz, r00..r22 (rows = local axes), material, panel_id]  -> 17 floats
# cyls:   [cx, cy, cz, ax, ay, az, radius, halflen, material, flutes]               -> 10 floats
INF = 1e30


@njit(cache=True)
def hit_box(ox, oy, oz, dx, dy, dz, b):
    px, py, pz = ox - b[0], oy - b[1], oz - b[2]
    lox = b[6] * px + b[7] * py + b[8] * pz
    loy = b[9] * px + b[10] * py + b[11] * pz
    loz = b[12] * px + b[13] * py + b[14] * pz
    ldx = b[6] * dx + b[7] * dy + b[8] * dz
    ldy = b[9] * dx + b[10] * dy + b[11] * dz
    ldz = b[12] * dx + b[13] * dy + b[14] * dz
    tmin, tmax, axis, sgn = -INF, INF, -1, 0.0
    for k in range(3):
        o = lox if k == 0 else (loy if k == 1 else loz)
        d = ldx if k == 0 else (ldy if k == 1 else ldz)
        h = b[3 + k]
        if abs(d) < 1e-9:
            if o < -h or o > h:
                return INF, -1, 0.0
        else:
            t1 = (-h - o) / d
            t2 = (h - o) / d
            s = -1.0
            if t1 > t2:
                t1, t2 = t2, t1
                s = 1.0
            if t1 > tmin:
                tmin, axis, sgn = t1, k, s
            if t2 < tmax:
                tmax = t2
            if tmin > tmax:
                return INF, -1, 0.0
    if tmax < 1e-4:
        return INF, -1, 0.0
    if tmin < 1e-4:
        return INF, -1, 0.0  # camera inside: ignore
    return tmin, axis, sgn


@njit(cache=True)
def hit_cyl(ox, oy, oz, dx, dy, dz, c):
    # cylinder centred at c[0:3], axis c[3:6], radius c[6], half-length c[7]
    ax, ay, az = c[3], c[4], c[5]
    px, py, pz = ox - c[0], oy - c[1], oz - c[2]
    pd = px * ax + py * ay + pz * az
    dd = dx * ax + dy * ay + dz * az
    qx, qy, qz = px - pd * ax, py - pd * ay, pz - pd * az
    ex, ey, ez = dx - dd * ax, dy - dd * ay, dz - dd * az
    A = ex * ex + ey * ey + ez * ez
    B = 2.0 * (qx * ex + qy * ey + qz * ez)
    C = qx * qx + qy * qy + qz * qz - c[6] * c[6]
    best, part = INF, -1
    if A > 1e-12:
        disc = B * B - 4 * A * C
        if disc >= 0:
            sq = math.sqrt(disc)
            t = (-B - sq) / (2 * A)
            if t > 1e-4:
                h = pd + t * dd
                if abs(h) <= c[7]:
                    best, part = t, 0
    if abs(dd) > 1e-9:  # caps
        for s in (-1.0, 1.0):
            t = (s * c[7] - pd) / dd
            if 1e-4 < t < best:
                hx, hy, hz = qx + t * ex, qy + t * ey, qz + t * ez
                if hx * hx + hy * hy + hz * hz <= c[6] * c[6]:
                    best, part = t, (1 if s > 0 else 2)
    return best, part


@njit(cache=True)
def occluded(ox, oy, oz, dx, dy, dz, tmax, boxes, cyls):
    for i in range(boxes.shape[0]):
        t, a, s = hit_box(ox, oy, oz, dx, dy, dz, boxes[i])
        if t < tmax:
            return True
    for i in range(cyls.shape[0]):
        t, p = hit_cyl(ox, oy, oz, dx, dy, dz, cyls[i])
        if t < tmax:
            return True
    return False


# ----------------------------------------------------------------------------- materials
# material table rows: [r, g, b, bump, noise_scale, spec]
@njit(cache=True)
def stone_albedo(px, py, pz, mat, mats):
    base_r, base_g, base_b = mats[mat, 0], mats[mat, 1], mats[mat, 2]
    sc = mats[mat, 4]
    n1 = fbm(px * sc, py * sc, pz * sc, 4)
    n2 = fbm(px * sc * 7.0 + 3.1, py * sc * 7.0, pz * sc * 7.0, 3)
    stain = fbm(px * 0.8 + 11.0, py * 1.6, pz * 0.8, 3)
    k = 0.72 + 0.45 * n1 + 0.12 * (n2 - 0.5)
    dark = 1.0 - 0.45 * max(0.0, (stain - 0.55) * 2.2)  # weathering streaks
    lich = max(0.0, (fbm(px * 2.3, py * 2.3 + 5.0, pz * 2.3, 3) - 0.62) * 3.0)  # lichen patches
    r = base_r * k * dark
    g = base_g * k * dark
    b = base_b * k * dark
    r = r * (1 - lich) + 0.38 * lich
    g = g * (1 - lich) + 0.37 * lich
    b = b * (1 - lich) + 0.26 * lich
    return r, g, b


@njit(cache=True)
def bump_normal(px, py, pz, nx, ny, nz, amount, sc):
    if amount <= 0.0:
        return nx, ny, nz
    e = 0.02 / sc
    f0 = fbm(px * sc, py * sc, pz * sc, 4)
    gx = (fbm((px + e) * sc, py * sc, pz * sc, 4) - f0) / e
    gy = (fbm(px * sc, (py + e) * sc, pz * sc, 4) - f0) / e
    gz = (fbm(px * sc, py * sc, (pz + e) * sc, 4) - f0) / e
    # remove the component along n, perturb
    dot = gx * nx + gy * ny + gz * nz
    gx -= dot * nx
    gy -= dot * ny
    gz -= dot * nz
    nx2, ny2, nz2 = nx - amount * gx / sc, ny - amount * gy / sc, nz - amount * gz / sc
    L = math.sqrt(nx2 * nx2 + ny2 * ny2 + nz2 * nz2) + 1e-9
    return nx2 / L, ny2 / L, nz2 / L


@njit(cache=True)
def sample_panel(panels, pid, u, v):
    """Bilinear height sample from relief panel `pid` at u,v in [0,1]."""
    H = panels.shape[1]
    W = panels.shape[2]
    x = min(max(u, 0.0), 1.0) * (W - 1)
    y = min(max(v, 0.0), 1.0) * (H - 1)
    x0, y0 = int(x), int(y)
    x1, y1 = min(x0 + 1, W - 1), min(y0 + 1, H - 1)
    fx, fy = x - x0, y - y0
    a = panels[pid, y0, x0] + (panels[pid, y0, x1] - panels[pid, y0, x0]) * fx
    b = panels[pid, y1, x0] + (panels[pid, y1, x1] - panels[pid, y1, x0]) * fx
    return a + (b - a) * fy


# ----------------------------------------------------------------------------- the kernel
@njit(cache=True, parallel=True, fastmath=True)
def render(W, H, cam, boxes, cyls, mats, panels, torch, moon, sky, fog, seed):
    """cam: [ox,oy,oz, fx,fy,fz, rx,ry,rz, ux,uy,uz, focal_px]
    torch: [x,y,z, r,g,b intensity-scaled, radius_jitter, scatter]
    moon: [dx,dy,dz, r,g,b]; sky: [r,g,b ambient, horizon r,g,b]; fog: [density, height_falloff]
    Returns rgb (H,W,3) float32 linear and depth (H,W)."""
    img = np.zeros((H, W, 3), np.float32)
    depth = np.full((H, W), 1e9, np.float32)
    ox, oy, oz = cam[0], cam[1], cam[2]
    for j in prange(H):
        for i in range(W):
            sx = (i + 0.5 - W * 0.5) / cam[12]
            sy = -(j + 0.5 - H * 0.5) / cam[12]
            dx = cam[3] + sx * cam[6] + sy * cam[9]
            dy = cam[4] + sx * cam[7] + sy * cam[10]
            dz = cam[5] + sx * cam[8] + sy * cam[11]
            L = math.sqrt(dx * dx + dy * dy + dz * dz)
            dx, dy, dz = dx / L, dy / L, dz / L
            # nearest hit
            tbest, kind, idx, aux, sgn = INF, -1, -1, -1, 0.0
            for b in range(boxes.shape[0]):
                t, a, s = hit_box(ox, oy, oz, dx, dy, dz, boxes[b])
                if t < tbest:
                    tbest, kind, idx, aux, sgn = t, 0, b, a, s
            for c in range(cyls.shape[0]):
                t, p = hit_cyl(ox, oy, oz, dx, dy, dz, cyls[c])
                if t < tbest:
                    tbest, kind, idx, aux = t, 1, c, p
            if dy < -1e-6:
                tg = -oy / dy
                if 1e-4 < tg < tbest:
                    tbest, kind = tg, 2
            r = g = b_ = 0.0
            if kind < 0:
                # ---- sky: gradient, moon glow, stars, the Taurus ridge
                el = dy
                az = math.atan2(dx, dz)
                ridge = 0.035 + 0.07 * fbm(az * 2.2 + 7.0, 0.0, 0.0, 5) + 0.05 * fbm(az * 9.0, 1.0, 0.0, 3)
                if el < ridge:
                    shade = 0.012 + 0.018 * fbm(az * 30.0, el * 30.0, 2.0, 3)
                    # rock-cut tombs: small pale facades on the cliff
                    tb = fbm(az * 60.0, el * 140.0, 5.0, 2)
                    if el > ridge * 0.35 and el < ridge * 0.8 and tb > 0.68:
                        shade += 0.03
                    r, g, b_ = shade * 0.6, shade * 0.75, shade * 1.0
                else:
                    t_ = min(max((el - ridge) * 2.2, 0.0), 1.0)
                    r = sky[3] * (1 - t_) + sky[0] * t_
                    g = sky[4] * (1 - t_) + sky[1] * t_
                    b_ = sky[5] * (1 - t_) + sky[2] * t_
                    md = dx * moon[0] + dy * moon[1] + dz * moon[2]
                    if md > 0.0:
                        glow = math.exp((md - 1.0) * 140.0) * 0.6 + math.exp((md - 1.0) * 12.0) * 0.06
                        disc = 1.0 if md > 0.99996 else 0.0
                        r += glow * 0.8 + disc * 18.0
                        g += glow * 0.85 + disc * 18.0
                        b_ += glow * 1.0 + disc * 17.0
                    # stars
                    sxs = int((az + 4.0) * 900.0)
                    sys = int((el + 1.0) * 900.0)
                    hs = _hash(sxs, sys, 7)
                    if hs > 0.9985:
                        tw = 0.5 + 0.5 * math.sin(seed * 0.7 + hs * 1000.0)
                        st = (hs - 0.9985) / 0.0015 * 0.25 * tw * min(1.0, (el - ridge) * 8.0)
                        r += st
                        g += st
                        b_ += st * 1.1
                img[j, i, 0], img[j, i, 1], img[j, i, 2] = r, g, b_
                tbest = 1e5
            else:
                px, py, pz = ox + tbest * dx, oy + tbest * dy, oz + tbest * dz
                depth[j, i] = tbest
                # ---- surface normal + material
                if kind == 0:
                    bb = boxes[idx]
                    a = aux
                    nx, ny, nz = bb[6 + a * 3] * sgn, bb[7 + a * 3] * sgn, bb[8 + a * 3] * sgn
                    mat = int(bb[15])
                    pid = int(bb[16])
                    if pid >= 0 and a == 2 and sgn < 0:  # carved panel on the -Z local face
                        qx, qy, qz = px - bb[0], py - bb[1], pz - bb[2]
                        lx = bb[6] * qx + bb[7] * qy + bb[8] * qz
                        ly = bb[9] * qx + bb[10] * qy + bb[11] * qz
                        u = (lx / bb[3]) * 0.5 + 0.5
                        v = 0.5 - (ly / bb[4]) * 0.5
                        e = 1.0 / panels.shape[2]
                        h0 = sample_panel(panels, pid, u, v)
                        hu = sample_panel(panels, pid, u + e, v) - h0
                        hv = sample_panel(panels, pid, u, v + e) - h0
                        depth_scale = 0.035  # relief depth (m) per unit height
                        du = hu * depth_scale / (2 * bb[3] * e)
                        dv = hv * depth_scale / (2 * bb[4] * e)
                        # tangent frame: local x (row0), local -y for v
                        nx = nx - du * bb[6] + dv * bb[9]
                        ny = ny - du * bb[7] + dv * bb[10]
                        nz = nz - du * bb[8] + dv * bb[11]
                        Ln = math.sqrt(nx * nx + ny * ny + nz * nz)
                        nx, ny, nz = nx / Ln, ny / Ln, nz / Ln
                        cav = 0.55 + 0.45 * h0
                    else:
                        cav = 1.0
                elif kind == 1:
                    cc = cyls[idx]
                    mat = int(cc[8])
                    ax, ay, az_ = cc[3], cc[4], cc[5]
                    if aux == 0:
                        qx, qy, qz = px - cc[0], py - cc[1], pz - cc[2]
                        hh = qx * ax + qy * ay + qz * az_
                        nx, ny, nz = qx - hh * ax, qy - hh * ay, qz - hh * az_
                        Ln = math.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
                        nx, ny, nz = nx / Ln, ny / Ln, nz / Ln
                        fl = cc[9]
                        if fl > 0:
                            # tangent around the axis
                            tx, ty, tz = ay * nz - az_ * ny, az_ * nx - ax * nz, ax * ny - ay * nx
                            # angle: use a reference perpendicular
                            rx, ry, rz = (1.0, 0.0, 0.0) if abs(ax) < 0.9 else (0.0, 1.0, 0.0)
                            dpr = rx * ax + ry * ay + rz * az_
                            rx, ry, rz = rx - dpr * ax, ry - dpr * ay, rz - dpr * az_
                            Lr = math.sqrt(rx * rx + ry * ry + rz * rz)
                            rx, ry, rz = rx / Lr, ry / Lr, rz / Lr
                            sx_, sy_, sz_ = ay * rz - az_ * ry, az_ * rx - ax * rz, ax * ry - ay * rx
                            ang = math.atan2(nx * sx_ + ny * sy_ + nz * sz_, nx * rx + ny * ry + nz * rz)
                            k = math.sin(ang * fl) * 0.55
                            nx, ny, nz = nx + k * tx, ny + k * ty, nz + k * tz
                            Ln = math.sqrt(nx * nx + ny * ny + nz * nz)
                            nx, ny, nz = nx / Ln, ny / Ln, nz / Ln
                            cav = 0.82 + 0.18 * math.cos(ang * fl)
                        else:
                            cav = 1.0
                    else:
                        s_ = 1.0 if aux == 1 else -1.0
                        nx, ny, nz = ax * s_, ay * s_, az_ * s_
                        cav = 0.9
                else:
                    nx, ny, nz = 0.0, 1.0, 0.0
                    mat = 0
                    cav = 1.0
                sc = mats[mat, 4]
                nx, ny, nz = bump_normal(px, py, pz, nx, ny, nz, mats[mat, 3], sc * 3.0)
                ar, ag, ab = stone_albedo(px, py, pz, mat, mats)
                if kind == 2:  # ground: dirt, pebbles, dry grass tint
                    pb = fbm(px * 6.0, 0.0, pz * 6.0, 3)
                    gr = fbm(px * 0.7, 3.0, pz * 0.7, 3)
                    ar = ar * (0.7 + 0.5 * pb) * (1 - 0.3 * gr) + 0.06 * gr
                    ag = ag * (0.7 + 0.5 * pb) * (1 - 0.2 * gr) + 0.05 * gr
                    ab = ab * (0.7 + 0.5 * pb) * (1 - 0.35 * gr)
                ar *= cav
                ag *= cav
                ab *= cav
                # ---- torch (point light, soft shadow via jittered position)
                jx = torch[0] + (_hash(i, j, seed) - 0.5) * torch[6]
                jy = torch[1] + (_hash(j, i, seed + 1) - 0.5) * torch[6]
                jz = torch[2] + (_hash(i + j, seed, 3) - 0.5) * torch[6]
                lx, ly, lz = jx - px, jy - py, jz - pz
                d2 = lx * lx + ly * ly + lz * lz
                dl = math.sqrt(d2)
                lx, ly, lz = lx / dl, ly / dl, lz / dl
                ndl = nx * lx + ny * ly + nz * lz
                if ndl > 0:
                    if not occluded(px + nx * 2e-3, py + ny * 2e-3, pz + nz * 2e-3, lx, ly, lz, dl, boxes, cyls):
                        att = 1.0 / (d2 + 0.05)
                        # soft wrap + a touch of spec for wet-looking stone
                        hx, hy, hz = lx - dx, ly - dy, lz - dz
                        Lh = math.sqrt(hx * hx + hy * hy + hz * hz) + 1e-9
                        spec = mats[mat, 5] * math.pow(max(0.0, (nx * hx + ny * hy + nz * hz) / Lh), 40.0)
                        r += (ar * ndl + spec) * torch[3] * att
                        g += (ag * ndl + spec) * torch[4] * att
                        b_ += (ab * ndl + spec) * torch[5] * att
                # ---- moon
                mdl = nx * moon[0] + ny * moon[1] + nz * moon[2]
                if mdl > 0:
                    if not occluded(px + nx * 2e-3, py + ny * 2e-3, pz + nz * 2e-3, moon[0], moon[1], moon[2], 1e4, boxes, cyls):
                        r += ar * mdl * moon[3]
                        g += ag * mdl * moon[4]
                        b_ += ab * mdl * moon[5]
                # ---- ambient sky (hemisphere)
                amb = 0.5 + 0.5 * ny
                r += ar * sky[0] * amb * 0.6
                g += ag * sky[1] * amb * 0.6
                b_ += ab * sky[2] * amb * 0.6
                # ---- height fog (moonlit)
                fd = fog[0] * math.exp(-max(py, 0.0) * fog[1])
                tr = math.exp(-tbest * fd)
                fr, fg, fb = sky[3] * 0.6, sky[4] * 0.6, sky[5] * 0.7
                r = r * tr + fr * (1 - tr)
                g = g * tr + fg * (1 - tr)
                b_ = b_ * tr + fb * (1 - tr)
                img[j, i, 0], img[j, i, 1], img[j, i, 2] = r, g, b_
            # ---- analytic in-scattering around the torch along the primary ray
            vx, vy, vz = torch[0] - ox, torch[1] - oy, torch[2] - oz
            s0 = vx * dx + vy * dy + vz * dz
            h2 = vx * vx + vy * vy + vz * vz - s0 * s0
            h = math.sqrt(max(h2, 1e-6))
            T = min(tbest, 400.0)
            integ = (math.atan((T - s0) / h) - math.atan(-s0 / h)) / h
            sc_ = torch[7] * integ
            img[j, i, 0] += sc_ * torch[3]
            img[j, i, 1] += sc_ * torch[4]
            img[j, i, 2] += sc_ * torch[5]
    return img, depth


# ----------------------------------------------------------------------------- helpers
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
    return np.array([*pos, *f, *r, *u, focal_px], np.float64)


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])


def rot(yaw=0.0, pitch=0.0, rollz=0.0):
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(rollz), math.sin(rollz)
    Ry = np.array([[cy, 0, -sy], [0, 1, 0], [sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, sp], [0, -sp, cp]])
    Rz = np.array([[cr, sr, 0], [-sr, cr, 0], [0, 0, 1]])
    return Rz @ Rx @ Ry


def box(center, half, R=None, mat=1, panel=-1):
    R = np.eye(3) if R is None else np.asarray(R)
    return [*center, *half, *R.reshape(-1), mat, panel]


def cyl(center, axis, radius, halflen, mat=1, flutes=0):
    a = np.asarray(axis, float)
    a /= np.linalg.norm(a)
    return [*center, *a, radius, halflen, mat, flutes]


def torch_color(kelvin=1850.0):
    """Approximate blackbody colour (linear BT.709) normalised to luminance 1."""
    t = kelvin / 100.0
    r = 1.0
    g = 0.39008157876901960784 * math.log(t) - 0.63184144378862745098
    b = 0.0 if t <= 19 else 0.54320678911019607843 * math.log(t - 10) - 1.19625408914
    rgb = np.clip(np.array([r, g, b]), 0, 1) ** 2.2
    return rgb / (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2])
