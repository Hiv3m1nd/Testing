"""Ray-cast perspective globe: terrain textures, sunlight, atmosphere, glint.

Earth is the unit sphere. x -> (0N,0E), y -> (0N,90E), z -> North pole.
A Camera looks at a surface point (lat, lon) from `dist` Earth radii away, with
`tilt` (0 = straight down) and `heading` (0 = looking north). Every frame each
of the ~2M pixels is intersected with the sphere and textured with cv2.remap,
so camera moves are continuous flights rather than zooms on a flat picture.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from gfx import W, H

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "build" / "tex"


def ll2v(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)


@dataclass
class Camera:
    lat: float
    lon: float
    dist: float          # distance from target point, Earth radii
    tilt: float = 0.0    # degrees from vertical
    heading: float = 0.0  # degrees clockwise from north
    fov: float = 34.0    # vertical field of view, degrees
    roll: float = 0.0
    shift_y: float = 0.0  # vertical lens shift (fraction of height), keeps target off-centre

    def basis(self):
        P = ll2v(self.lat, self.lon)
        up = P
        east = np.array([-math.sin(math.radians(self.lon)), math.cos(math.radians(self.lon)), 0.0])
        north = np.cross(up, east)
        h, t = math.radians(self.heading), math.radians(self.tilt)
        fwd_h = math.cos(h) * north + math.sin(h) * east  # horizontal look direction
        C = P + self.dist * (math.cos(t) * up - math.sin(t) * fwd_h)
        F = P - C
        F /= np.linalg.norm(F)
        U = up - np.dot(up, F) * F
        if np.linalg.norm(U) < 1e-6:
            U = fwd_h.copy()
        U /= np.linalg.norm(U)
        R = np.cross(F, U)
        if self.roll:
            r = math.radians(self.roll)
            R, U = math.cos(r) * R + math.sin(r) * U, -math.sin(r) * R + math.cos(r) * U
        f = (H / 2) / math.tan(math.radians(self.fov) / 2)
        return C, F, R, U, f

    def lerp(self, other: "Camera", t: float) -> "Camera":
        def L(a, b):
            return a + (b - a) * t
        dlon = ((other.lon - self.lon + 180) % 360) - 180
        # interpolate distance in log space for natural zooms
        d = math.exp(L(math.log(self.dist), math.log(other.dist)))
        return Camera(L(self.lat, other.lat), self.lon + dlon * t, d, L(self.tilt, other.tilt),
                      L(self.heading, other.heading), L(self.fov, other.fov), L(self.roll, other.roll),
                      L(self.shift_y, other.shift_y))


def fly(a: Camera, b: Camera, t: float, arc: float = 0.6) -> Camera:
    """Great-circle flight: interpolate, then lift the camera mid-way (pull back)."""
    c = a.lerp(b, t)
    span = math.degrees(math.acos(np.clip(np.dot(ll2v(a.lat, a.lon), ll2v(b.lat, b.lon)), -1, 1)))
    c.dist *= 1 + arc * (span / 30.0) * math.sin(math.pi * t) * 1.2
    return c


# ----------------------------------------------------------------------------- textures
@lru_cache(maxsize=None)
def texture(name, level=0):
    meta = json.load(open(TEX / f"{name}.json"))
    img = cv2.imread(str(TEX / f"{name}.png"), cv2.IMREAD_COLOR)[:, :, ::-1]
    land = np.load(TEX / f"{name}_land.npy")
    img = np.dstack([img, land])  # RGBA, A = land fraction
    ppd = meta["ppd"]
    for _ in range(level):
        img = cv2.pyrDown(img)
        ppd /= 2
    return np.ascontiguousarray(img), meta["lon0"], meta["lat1"], ppd


@lru_cache(maxsize=4)
def pixel_grid(shift_y=0.0):
    xs = (np.arange(W, dtype=np.float32) + 0.5) - W / 2
    ys = (np.arange(H, dtype=np.float32) + 0.5) - H / 2 - shift_y * H
    return np.meshgrid(xs, ys)


def _sample(name, level, lat, lon, valid):
    img, lon0, lat1, ppd = texture(name, level)
    mx = ((lon - lon0) * ppd - 0.5).astype(np.float32)
    my = ((lat1 - lat) * ppd - 0.5).astype(np.float32)
    mx[~valid] = -10
    my[~valid] = -10
    out = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return out.astype(np.float32) / 255.0


def _region_weight(name, lat, lon, feather=1.5):
    img, lon0, lat1, ppd = texture(name, 0)
    lon1 = lon0 + img.shape[1] / ppd
    lat0 = lat1 - img.shape[0] / ppd
    w = np.minimum.reduce([lon - lon0, lon1 - lon, lat - lat0, lat1 - lat]) / feather
    return np.clip(w, 0, 1)


SUN_COLOR = np.array([1.0, 0.96, 0.9], np.float32)
ATM_DAY = np.array([0.32, 0.55, 0.95], np.float32)
ATM_DUSK = np.array([1.0, 0.55, 0.28], np.float32)


def render(cam: Camera, sun=(30.0, 20.0), exposure=1.0, night_lights=None, atmosphere=1.0,
           glint=0.6, haze=1.0):
    """Return (rgb float32 HxWx3, coverage HxW, lat, lon, hit mask)."""
    C, F, R, U, f = cam.basis()
    gx, gy = pixel_grid(round(cam.shift_y, 3))
    d = (F[None, None, :] * f + gx[..., None] * R[None, None, :] - gy[..., None] * U[None, None, :]).astype(np.float32)
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    b = d @ C.astype(np.float32)
    c = float(C @ C) - 1.0
    disc = b * b - c
    hit = disc > 0
    sq = np.sqrt(np.maximum(disc, 0))
    t = -b - sq
    hit &= t > 0
    P = C[None, None, :].astype(np.float32) + t[..., None] * d
    P /= np.linalg.norm(P, axis=-1, keepdims=True) + 1e-9
    lat = np.degrees(np.arcsin(np.clip(P[..., 2], -1, 1)))
    lon = np.degrees(np.arctan2(P[..., 1], P[..., 0]))

    # pick texture resolution from the footprint of one pixel at the target
    h_alt = max(float(np.linalg.norm(C)) - 1.0, 1e-4)
    deg_px = math.degrees(min(cam.dist, h_alt * 1.2 + 0.02) / f)
    lvl = 0 if deg_px < 1 / 30 else 1 if deg_px < 1 / 15 else 2 if deg_px < 1 / 7 else 3
    tex = _sample("global", max(0, lvl - 2), lat, lon, hit)
    for name in ("oldworld", "mesoamerica"):
        w = _region_weight(name, lat, lon) * hit
        if w.max() > 0:
            reg = _sample(name, lvl, lat, lon, w > 0)
            tex = tex * (1 - w[..., None]) + reg * w[..., None]
    rgb, landf = tex[..., :3], tex[..., 3]
    # sRGB -> linear for lighting
    rgb = rgb ** 2.2

    S = ll2v(*sun).astype(np.float32)
    ndl = P @ S
    day = np.clip((ndl + 0.08) / 0.3, 0, 1)
    day = day * day * (3 - 2 * day)
    diffuse = np.clip(ndl, 0, 1) ** 0.6
    mu = np.clip(-(P * d).sum(-1), 0, 1)  # cos view angle at surface
    surf = rgb * (0.08 + 1.25 * diffuse)[..., None] * day[..., None] * SUN_COLOR
    night = rgb * 0.035 + np.array([0.004, 0.007, 0.014], np.float32)
    surf = surf + night * (1 - day[..., None])
    # sun glint on water
    if glint:
        refl = d - 2 * (d * P).sum(-1, keepdims=True) * P
        g = np.clip(refl @ S, 0, 1) ** 300 * (1 - landf) * day
        surf += (glint * 0.9 * g)[..., None] * SUN_COLOR
    # aerial perspective / limb haze
    dusk = np.clip(1 - np.abs(ndl) / 0.35, 0, 1)
    atm_col = ATM_DAY * (1 - dusk[..., None]) + ATM_DUSK * dusk[..., None]
    hz = haze * (1 - mu) ** 3 * np.clip(ndl + 0.25, 0, 1)
    surf = surf * (1 - 0.55 * hz[..., None]) + atm_col * hz[..., None] * 0.55
    surf = surf * hit[..., None]

    # outer atmosphere for rays that miss (or graze) the planet
    if atmosphere:
        closest = np.sqrt(np.maximum(c - b * b + 1.0, 0))  # distance of ray from centre
        alt = closest - 1.0
        Q = C[None, None, :] - b[..., None] * d
        Q /= np.linalg.norm(Q, axis=-1, keepdims=True) + 1e-9
        qs = Q @ S
        lit = np.clip((qs + 0.25) / 0.6, 0, 1)
        qdusk = np.clip(1 - np.abs(qs) / 0.4, 0, 1)
        acol = ATM_DAY * (1 - qdusk[..., None]) + ATM_DUSK * qdusk[..., None]
        scale = 0.022
        glow = np.exp(-np.maximum(alt, 0) / scale) * (~hit) * (b < 0)
        surf = surf + atmosphere * (glow * lit)[..., None] * acol * 1.1

    if night_lights is not None:
        surf = surf + night_lights(lat, lon, hit) * (1 - day[..., None])

    # antialias the limb: soft coverage from ray/limb distance
    edge = np.clip(disc * f * 0.5, 0, 1) * (t > 0)
    out = np.clip(surf * exposure, 0, None) ** (1 / 2.2)
    return out.astype(np.float32), edge.astype(np.float32), lat, lon, hit


def project(cam: Camera, lat, lon, alt=0.0):
    """Lat/lon arrays -> screen x, y and a visibility mask (front side, in front of camera)."""
    C, F, R, U, f = cam.basis()
    P = ll2v(np.asarray(lat, float), np.asarray(lon, float)) * (1 + alt)
    v = P - C
    z = v @ F
    x = W / 2 + (v @ R) / np.maximum(z, 1e-6) * f
    y = H / 2 + cam.shift_y * H - (v @ U) / np.maximum(z, 1e-6) * f
    front = (P @ C) > 1.0 + 1e-4
    return x, y, front & (z > 0)


def surface_scale(cam: Camera, lat, lon):
    """Pixels per degree of latitude at a point (for sizing labels/markers)."""
    x0, y0, _ = project(cam, lat, lon)
    x1, y1, _ = project(cam, lat + 0.5, lon)
    return float(np.hypot(x1 - x0, y1 - y0) * 2)
