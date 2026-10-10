"""Historical geography for AD 1 and drawing of map overlays on the globe.

Boundaries are approximate reconstructions (see research/research.md for the
reasoning and uncertainties). Each outline is drawn generously into the sea and
then intersected with Natural Earth coastlines, so coasts are exact while land
frontiers carry the historical approximation.
"""
from __future__ import annotations

import json
import math
import pickle
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia
from shapely.geometry import LineString, Polygon, box, shape
from shapely.ops import unary_union

import gfx
from gfx import Canvas, paint
from globe import Camera, project

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "build" / "geo_cache.pkl"

# ----------------------------------------------------------------------------- outlines (lon, lat)
ROME_PROVINCES = [
    (-10.0, 44.0), (-5.0, 48.8), (1.5, 51.3), (4.2, 51.95), (6.1, 51.85), (6.6, 51.4), (6.95, 50.94),
    (7.6, 50.35), (8.27, 50.0), (8.4, 49.0), (7.6, 47.6), (8.6, 47.65), (9.9, 48.4), (11.4, 48.75),
    (12.1, 49.0), (13.4, 48.57), (14.3, 48.3), (16.37, 48.2), (17.0, 48.1), (18.7, 47.8), (19.05, 47.5),
    (18.7, 46.0), (19.0, 45.35), (19.85, 45.25), (20.46, 44.82), (21.5, 44.75), (22.5, 44.6), (22.9, 43.85),
    (24.6, 43.7), (25.95, 43.85), (27.3, 44.1), (28.0, 44.35), (28.7, 44.2),
    (30.5, 42.2), (35.0, 42.3), (39.5, 41.4), (40.3, 41.0), (39.6, 39.8), (38.8, 39.0), (38.4, 38.0),
    (38.3, 37.5), (37.9, 37.05), (38.3, 36.6), (38.2, 36.0), (37.5, 35.0), (37.0, 34.0), (36.8, 33.3),
    (36.6, 32.6), (35.9, 31.6), (35.4, 31.0), (34.25, 31.3), (32.6, 29.9), (35.0, 26.5), (35.7, 23.9),
    (35.6, 22.9), (32.5, 22.9), (28.5, 24.5), (25.3, 29.3), (25.1, 31.0), (24.5, 31.3), (21.0, 31.6),
    (20.0, 31.0), (19.0, 30.3), (17.0, 30.8), (15.0, 31.6), (12.0, 31.8), (10.3, 33.0), (9.5, 33.6),
    (7.8, 34.5), (6.5, 35.5), (6.4, 37.3), (2.0, 38.0), (-2.0, 36.5), (-5.45, 36.05), (-6.4, 36.0),
    (-9.8, 36.5),
]
ROME_CLIENTS = {
    "Mauretania": [(-6.2, 36.0), (-1.5, 35.6), (2.0, 36.8), (6.4, 37.2), (6.4, 35.5), (2.0, 34.0), (-2.0, 33.0),
                   (-6.0, 31.8), (-9.9, 31.0), (-9.9, 34.5)],
    "Thrace": [(24.0, 40.9), (24.0, 42.4), (25.5, 42.85), (28.0, 43.0), (28.3, 41.9), (29.15, 41.25), (26.6, 40.55),
               (25.0, 40.85)],
    "Cappadocia": [(33.5, 37.7), (33.3, 39.2), (35.0, 40.0), (37.5, 40.0), (38.8, 39.2), (38.4, 38.2), (36.6, 37.6),
                   (35.0, 37.3)],
    "Pontus": [(35.5, 41.8), (36.0, 40.4), (38.5, 40.3), (39.8, 40.5), (40.4, 41.0), (39.5, 41.4), (37.5, 41.3),
               (36.0, 41.9)],
    "Commagene": [(37.4, 37.4), (37.4, 38.1), (38.4, 38.2), (38.6, 37.4), (37.9, 37.0)],
    "Judaea": [(34.2, 31.3), (34.9, 32.9), (35.1, 33.3), (35.7, 33.4), (36.6, 33.05), (36.6, 32.4), (35.95, 31.6),
               (35.5, 31.0), (34.6, 31.0)],
    "Nabataea": [(34.3, 29.5), (34.6, 30.9), (35.45, 31.0), (35.95, 31.55), (36.6, 32.35), (37.6, 32.3),
                 (38.6, 31.0), (38.6, 28.0), (38.0, 26.5), (36.5, 25.9), (34.9, 28.0)],
    "Bosporus": [(33.5, 45.6), (36.8, 45.6), (38.2, 45.4), (37.6, 44.6), (36.0, 44.95), (34.0, 44.35)],
}
GERMANIA = [(6.2, 51.9), (6.8, 53.5), (8.8, 54.0), (10.0, 53.5), (11.6, 52.1), (11.5, 50.6), (9.5, 50.0),
            (8.3, 50.0), (7.6, 50.4), (6.95, 50.94), (6.6, 51.4)]
PARTHIA = [
    (38.0, 37.1), (38.3, 36.5), (39.0, 36.0), (40.1, 35.3), (40.75, 34.6), (41.9, 34.4), (43.3, 33.4),
    (44.3, 32.0), (46.0, 31.0), (47.6, 30.3), (48.5, 29.4), (51.5, 27.4), (54.5, 25.9), (56.4, 26.6),
    (57.5, 25.4), (61.5, 24.9), (60.8, 27.5), (61.2, 30.5), (61.6, 33.0), (62.4, 35.0), (62.6, 37.0),
    (62.8, 38.2), (61.0, 38.6), (58.0, 38.4), (55.0, 37.8), (54.0, 37.35), (53.5, 37.6), (50.0, 37.7),
    (48.8, 38.4), (47.5, 39.0), (46.0, 38.7), (44.8, 38.0), (44.2, 37.2), (42.5, 37.3), (40.5, 37.4),
    (38.8, 37.4),
]
ARMENIA = [(38.8, 39.2), (40.5, 40.9), (43.5, 41.25), (46.0, 41.05), (47.5, 39.5), (46.0, 38.7), (44.8, 38.0),
           (44.2, 37.45), (42.5, 37.45), (40.5, 37.6), (39.0, 38.3)]
HAN = [
    (93.6, 40.3), (94.7, 40.6), (97.5, 40.3), (99.5, 40.0), (100.5, 41.9), (101.5, 42.0), (101.5, 40.3),
    (102.5, 39.3), (103.5, 39.0), (105.5, 38.5), (106.5, 40.9), (108.0, 41.4), (110.0, 41.4), (112.0, 41.3),
    (114.0, 41.5), (116.0, 41.3), (117.5, 41.5), (119.5, 42.0), (121.0, 42.4), (122.5, 42.6), (124.0, 42.5),
    (125.0, 41.8), (126.2, 41.2), (127.0, 40.0), (127.4, 39.0), (127.0, 38.0), (126.0, 37.4), (125.0, 37.0),
    (123.5, 33.0), (122.5, 30.0), (121.0, 26.0), (117.5, 22.5), (114.0, 21.6), (111.5, 20.5), (109.0, 19.9),
    (108.6, 17.5), (108.6, 16.0), (107.5, 15.8), (106.5, 16.3), (105.5, 17.8), (104.2, 19.5), (103.5, 21.0),
    (102.6, 22.4), (101.9, 23.2), (101.0, 24.5), (100.2, 25.5), (100.5, 26.8), (101.5, 27.5), (102.0, 29.0),
    (102.6, 30.5), (103.0, 31.5), (103.6, 32.8), (103.5, 34.0), (102.0, 35.6), (101.0, 36.5), (101.4, 37.5),
    (100.0, 38.3), (98.5, 39.2), (96.0, 39.6), (93.6, 39.9),
]
HAINAN = [(108.4, 17.9), (111.4, 17.9), (111.4, 20.17), (108.4, 20.17)]
TARIM = [(75.3, 39.5), (76.0, 40.9), (79.0, 41.6), (82.0, 42.1), (85.5, 42.5), (88.0, 43.2), (89.5, 43.1),
         (91.5, 42.8), (93.0, 42.5), (93.6, 40.4), (91.0, 39.1), (88.0, 38.5), (85.0, 37.5), (82.0, 36.8),
         (79.5, 36.7), (77.0, 37.1), (75.3, 38.4)]
KUSH = [(31.0, 22.6), (32.7, 22.9), (34.5, 20.5), (36.0, 18.0), (36.5, 15.0), (35.0, 13.0), (33.0, 12.8),
        (32.0, 15.0), (31.5, 18.0), (30.0, 20.0)]

# ----------------------------------------------------------------------------- places (lat, lon)
CITIES = {
    "Rome": (41.89, 12.49), "Alexandria": (31.20, 29.92), "Antioch": (36.20, 36.16), "Carthage": (36.85, 10.32),
    "Athens": (37.97, 23.72), "Jerusalem": (31.78, 35.23), "Ctesiphon": (33.09, 44.58), "Merv": (37.66, 62.19),
    "Chang'an": (34.31, 108.86), "Luoyang": (34.68, 112.45), "Dunhuang": (40.14, 94.66), "Kashgar": (39.47, 75.99),
    "Myos Hormos": (26.16, 34.24), "Berenice": (23.91, 35.48), "Muziris": (10.16, 76.21), "Barygaza": (21.70, 72.98),
    "Meroë": (16.94, 33.75), "Teotihuacan": (19.69, -98.84), "El Mirador": (17.75, -89.92),
    "Pandateria": (40.80, 13.43), "Rhodes": (36.43, 28.22), "Lugdunum": (45.76, 4.83), "Massilia": (43.30, 5.37),
    "Palmyra": (34.55, 38.27), "Zeugma": (37.06, 37.87), "Artaxata": (39.95, 44.55), "Petra": (30.33, 35.44),
    "Samos": (37.70, 26.95), "Ecbatana": (34.80, 48.52), "Pataliputra": (25.61, 85.14), "Seleucia": (33.10, 44.52),
}

SILK_ROAD = [(34.31, 108.86), (36.06, 103.8), (37.93, 102.64), (38.93, 100.45), (39.73, 98.5), (40.14, 94.66),
             (40.5, 89.9), (41.73, 86.15), (41.72, 82.96), (41.17, 80.26), (39.47, 75.99), (39.7, 73.6),
             (40.4, 71.0), (39.65, 66.96), (39.77, 64.42), (37.66, 62.19), (36.6, 58.0), (36.13, 54.13),
             (35.59, 51.43), (34.80, 48.52), (33.09, 44.58), (34.75, 40.73), (34.55, 38.27), (36.20, 36.16)]
SEA_ROUTE = [(26.16, 34.24), (23.91, 35.9), (20.5, 38.2), (16.5, 40.6), (13.6, 42.6), (12.6, 43.45), (12.2, 45.5),
             (12.0, 50.0), (11.4, 56.0), (10.8, 63.0), (10.3, 70.0), (10.16, 76.21)]
SEA_ROUTE_N = [(12.2, 45.5), (13.5, 52.0), (16.5, 60.0), (19.5, 67.0), (21.70, 72.98)]
YELLOW_RIVER_HAN = [(34.9, 113.6), (35.55, 114.5), (35.75, 115.0), (36.6, 115.3), (37.45, 116.3), (38.3, 116.85),
                    (38.45, 117.6)]  # lower course before the AD 11 shift (approximate)
RIVER_NAMES = ["Nile", "Tigris", "Euphrates", "Indus", "Ganges", "Danube", "Rhine", "Chang Jiang", "Yangtze",
               "Huang", "Wei", "Amu  Darya", "Syr  Darya", "Jordan", "Tarim"]


def _poly(pts):
    return Polygon(pts)


@lru_cache(maxsize=1)
def _land():
    d = json.load(open(ROOT / "assets/geo/ne_50m_land.geojson"))
    return unary_union([shape(f["geometry"]) for f in d["features"]])


def _lakes():
    d = json.load(open(ROOT / "assets/geo/ne_50m_lakes.geojson"))
    return unary_union([shape(f["geometry"]) for f in d["features"]
                        if f["properties"].get("featurecla") != "Reservoir"])


@lru_cache(maxsize=1)
def regions():
    """Clip outlines to land. Cached to disk (shapely work takes a few seconds)."""
    if CACHE.exists():
        return pickle.load(open(CACHE, "rb"))
    land = _land().difference(_lakes())

    def tidy(g, min_area=0.03, min_hole=0.25):
        polys = [g] if g.geom_type == "Polygon" else [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]
        keep = [Polygon(p.exterior, [r for r in p.interiors if Polygon(r).area > min_hole])
                for p in polys if p.area > min_area]
        return unary_union(keep)

    def clip(pts):
        return tidy(_poly(pts).buffer(0).intersection(land))
    clients = {k: clip(v) for k, v in ROME_CLIENTS.items()}
    client_union = unary_union(list(clients.values()))
    out = {
        "rome": tidy(clip(ROME_PROVINCES).difference(client_union)),
        "rome_clients": client_union,
        "germania": clip(GERMANIA),
        "parthia": tidy(clip(PARTHIA).difference(_poly(ARMENIA))),
        "armenia": clip(ARMENIA),
        "han": tidy(clip(HAN).difference(_poly(HAINAN))),
        "tarim": clip(TARIM),
        "kush": clip(KUSH),
    }
    rivers = json.load(open(ROOT / "assets/geo/ne_50m_rivers_lake_centerlines.geojson"))
    lines = []
    for f in rivers["features"]:
        name = f["properties"].get("name") or ""
        if name not in RIVER_NAMES:
            continue
        g = shape(f["geometry"])
        if name == "Huang":  # cut the modern lower course; the Han-era course is drawn separately
            g = g.intersection(box(-180, -90, 114.2, 90))
        for ln in ([g] if g.geom_type == "LineString" else list(getattr(g, "geoms", []))):
            if ln.geom_type == "LineString" and len(ln.coords) > 1:
                lines.append((name, np.asarray(ln.coords)[:, :2]))
    lines.append(("Huang", np.array([(lo, la) for la, lo in YELLOW_RIVER_HAN])))
    out["rivers"] = lines
    pickle.dump(out, open(CACHE, "wb"))
    return out


# ----------------------------------------------------------------------------- drawing
def _densify(coords, step=0.3):
    pts = [coords[0]]
    for a, b in zip(coords[:-1], coords[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        for i in range(1, n + 1):
            pts.append((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n))
    return np.asarray(pts)


def geom_path(cam: Camera, geom, step=0.3):
    """Shapely (multi)polygon in lon/lat -> skia path in screen space."""
    path = skia.Path()
    path.setFillType(skia.PathFillType.kEvenOdd)
    polys = [geom] if geom.geom_type == "Polygon" else [g for g in getattr(geom, "geoms", []) if g.geom_type == "Polygon"]
    for poly in polys:
        for ring in [poly.exterior, *poly.interiors]:
            c = _densify(np.asarray(ring.coords), step)
            x, y, vis = project(cam, c[:, 1], c[:, 0])
            if not vis.any():
                continue
            path.moveTo(float(x[0]), float(y[0]))
            for xi, yi in zip(x[1:], y[1:]):
                path.lineTo(float(xi), float(yi))
            path.close()
    return path


def line_path(cam: Camera, latlon, step=0.25, upto=1.0):
    """Polyline of (lat, lon) points, optionally only the first `upto` fraction of its length."""
    ll = np.asarray(latlon, float)
    c = _densify(ll[:, ::-1], step)  # lon, lat
    if upto < 1.0:
        seglen = np.hypot(np.diff(c[:, 0]), np.diff(c[:, 1]))
        cum = np.concatenate([[0], np.cumsum(seglen)])
        n = int(np.searchsorted(cum, cum[-1] * max(upto, 0.0)))
        c = c[:max(2, n + 1)]
    x, y, vis = project(cam, c[:, 1], c[:, 0])
    path = skia.Path()
    started = False
    for xi, yi, v in zip(x, y, vis):
        if not v:
            started = False
            continue
        if not started:
            path.moveTo(float(xi), float(yi))
            started = True
        else:
            path.lineTo(float(xi), float(yi))
    return path, (x[-1], y[-1], bool(vis[-1]))


def fill_region(cv: Canvas, cam: Camera, geom, rgb, alpha=0.35, edge=2.5, glow=10.0, edge_alpha=0.9,
                hatch=False):
    if alpha <= 0.003 and edge_alpha <= 0.003:
        return
    path = geom_path(cam, geom)
    c = cv.c
    if hatch:
        c.save()
        c.clipPath(path, skia.ClipOp.kIntersect, True)
        p = paint(rgb, alpha * 1.6, stroke=2.0)
        for k in range(-40, 80):
            x0 = k * 22.0
            c.drawLine(x0, 0, x0 + gfx.H * 0.6, gfx.H, p)
        c.restore()
    else:
        c.drawPath(path, paint(rgb, alpha))
    if edge_alpha > 0:
        if glow:
            c.drawPath(path, paint(rgb, edge_alpha * 0.5, stroke=edge * 3, blur=glow))
        c.drawPath(path, paint(tuple(min(1, v * 1.25 + 0.1) for v in rgb), edge_alpha, stroke=edge))


def draw_rivers(cv: Canvas, cam: Camera, alpha=0.5, width=1.6, names=None):
    if alpha <= 0.003:
        return
    p = paint((0.55, 0.75, 0.85), alpha, stroke=width)
    for name, coords in regions()["rivers"]:
        if names and name not in names:
            continue
        ll = coords[:, ::-1]
        path, _ = line_path(cam, ll, step=0.2)
        cv.c.drawPath(path, p)


def city_marker(cv: Canvas, cam: Camera, name, a=1.0, label=None, rgb=gfx.PALE_GOLD, size=40, dx=24, dy=12,
                align="left", r=7, pulse=0.0, sub=None, sub_size=None, font_name="cinzel", weight=600):
    if a <= 0.003:
        return None
    lat, lon = CITIES[name]
    x, y, vis = project(cam, [lat], [lon])
    if not vis[0]:
        return None
    x, y = float(x[0]), float(y[0])
    c = cv.c
    if pulse:
        rr = r + 26 * pulse
        c.drawCircle(x, y, rr, paint(rgb, a * (1 - pulse) * 0.8, stroke=2.5))
    c.drawCircle(x, y, r * 2.4, paint(rgb, a * 0.35, blur=r * 1.2))
    c.drawCircle(x, y, r, paint(rgb, a))
    c.drawCircle(x, y, r * 0.45, paint((1, 1, 1), a))
    if label is not False:
        f = gfx.font(font_name, size, weight)
        tx = x + dx if align == "left" else (x - dx if align == "right" else x)
        gfx.draw_text(cv, label or name.upper(), tx, y + dy, f, gfx.IVORY, a, tracking=0.12, align=align,
                      shadow=0.9)
        if sub:
            fs = gfx.font("garamond-italic", sub_size or size * 0.8, 500)
            gfx.draw_text(cv, sub, tx, y + dy + (sub_size or size * 0.8) * 1.15, fs, gfx.PALE_GOLD, a * 0.95,
                          align=align, shadow=0.9)
    return x, y


def region_label(cv: Canvas, cam: Camera, lat, lon, text, a=1.0, size=48, rgb=gfx.IVORY, tracking=0.35,
                 weight=600, sub=None):
    if a <= 0.003:
        return
    x, y, vis = project(cam, [lat], [lon])
    if not vis[0]:
        return
    f = gfx.font("cinzel", size, weight)
    gfx.draw_text(cv, text, float(x[0]), float(y[0]), f, rgb, a, tracking=tracking, shadow=1.0)
    if sub:
        fs = gfx.font("garamond-italic", size * 0.62, 500)
        gfx.draw_text(cv, sub, float(x[0]), float(y[0]) + size * 0.95, fs, gfx.PALE_GOLD, a * 0.95, shadow=1.0)
