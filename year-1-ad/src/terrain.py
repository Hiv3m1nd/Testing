"""Build equirectangular colour + elevation textures for the globe renderer.

Pipeline: terrarium tiles -> elevation mosaic (Web Mercator) -> equirectangular
reprojection -> land/water mask from Natural Earth (minus modern reservoirs,
plus the pre-1960 Aral Sea and the ancient Lake Texcoco) -> hillshade +
hypsometric palette + hand-drawn aridity masks -> textures in build/tex/.

The palette is deliberately "natural, pre-modern": no cities, roads, farmland or
reservoirs, just relief, water and vegetation zones.
"""
import json
import math
from pathlib import Path

import cv2
import numpy as np
import skia
from shapely.geometry import shape, Polygon

ROOT = Path(__file__).resolve().parents[1]
TILES = ROOT / "build" / "tiles"
OUT = ROOT / "build" / "tex"

# (name, zoom, lon0, lon1, lat0, lat1, px_per_degree)
REGIONS = {
    "global": (4, -180.0, 180.0, -90.0, 90.0, 11.0),
    "oldworld": (6, -20.0, 136.0, -6.0, 62.0, 42.0),
    "mesoamerica": (6, -112.0, -78.0, 8.0, 28.0, 42.0),
}


def merc_y(lat, n):
    r = np.radians(np.clip(lat, -85.05, 85.05))
    return (1 - np.log(np.tan(r) + 1 / np.cos(r)) / math.pi) / 2 * n * 256


def load_mosaic(z):
    n = 2 ** z
    xs = sorted(int(p.name) for p in (TILES / str(z)).iterdir())
    ys = sorted({int(p.stem) for x in xs for p in (TILES / str(z) / str(x)).iterdir()})
    x0, y0 = xs[0], ys[0]
    mos = np.zeros(((ys[-1] - y0 + 1) * 256, (xs[-1] - x0 + 1) * 256), np.float32)
    for x in xs:
        for y in ys:
            p = TILES / str(z) / str(x) / f"{y}.png"
            if not p.exists():
                continue
            im = cv2.imread(str(p), cv2.IMREAD_COLOR)[:, :, ::-1].astype(np.float32)
            e = im[:, :, 0] * 256 + im[:, :, 1] + im[:, :, 2] / 256 - 32768
            mos[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = e
    return mos, x0 * 256, y0 * 256, n


def equirect_elevation(name):
    z, lon0, lon1, lat0, lat1, ppd = REGIONS[name]
    mos, ox, oy, n = load_mosaic(z)
    W = int((lon1 - lon0) * ppd)
    H = int((lat1 - lat0) * ppd)
    lon = lon0 + (np.arange(W) + 0.5) / ppd
    lat = lat1 - (np.arange(H) + 0.5) / ppd
    mx = ((lon + 180) / 360 * n * 256 - ox).astype(np.float32)
    my = (merc_y(lat, n) - oy).astype(np.float32)
    mapx = np.broadcast_to(mx[None, :], (H, W)).copy()
    mapy = np.broadcast_to(my[:, None], (H, W)).copy()
    elev = cv2.remap(mos, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return elev, lon, lat


def rasterize(geoms, lon0, lat1, ppd, W, H):
    """Fill shapely geometries into a float mask using skia (antialiased)."""
    arr = np.zeros((H, W, 4), np.uint8)
    surf = skia.Surface(arr, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
    c = surf.getCanvas()
    paint = skia.Paint(AntiAlias=True, Color=skia.ColorWHITE)
    for g in geoms:
        polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
        for poly in polys:
            path = skia.Path()
            path.setFillType(skia.PathFillType.kEvenOdd)
            for ring in [poly.exterior, *poly.interiors]:
                pts = np.asarray(ring.coords)
                xs = (pts[:, 0] - lon0) * ppd
                ys = (lat1 - pts[:, 1]) * ppd
                path.moveTo(xs[0], ys[0])
                for x, y in zip(xs[1:], ys[1:]):
                    path.lineTo(x, y)
                path.close()
            c.drawPath(path, paint)
    return arr[:, :, 0].astype(np.float32) / 255.0


def land_mask(lon, lat, ppd, elev):
    W, H = len(lon), len(lat)
    lon0, lat1 = lon[0] - 0.5 / ppd, lat[0] + 0.5 / ppd
    bbox = Polygon([(lon0, lat1), (lon[-1] + 1, lat1), (lon[-1] + 1, lat[-1] - 1), (lon0, lat[-1] - 1)])
    land = json.load(open(ROOT / "assets/geo/ne_10m_land.geojson"))
    geoms = [shape(f["geometry"]).intersection(bbox) for f in land["features"]]
    m = rasterize([g for g in geoms if not g.is_empty], lon0, lat1, ppd, W, H)
    lakes = json.load(open(ROOT / "assets/geo/ne_10m_lakes.geojson"))
    lk = []
    for f in lakes["features"]:
        pr = f["properties"]
        if pr.get("featurecla") == "Reservoir" or "Aral" in (pr.get("name") or ""):
            continue
        g = shape(f["geometry"])
        if g.intersects(bbox):
            lk.append(g.intersection(bbox))
    m = np.clip(m - rasterize([g for g in lk if not g.is_empty], lon0, lat1, ppd, W, H), 0, 1)
    LON, LAT = np.meshgrid(lon, lat)
    # Aral Sea at its pre-1960 level (~53 m), Lake Texcoco (valley floor ~2240 m)
    aral = (LON > 58.0) & (LON < 61.9) & (LAT > 43.4) & (LAT < 46.9) & (elev < 53.0)
    texcoco = (LON > -99.25) & (LON < -98.85) & (LAT > 19.25) & (LAT < 19.75) & (elev < 2238.0)
    m[aral | texcoco] = 0.0
    return m


# Hand-drawn aridity: (lon, lat) polygons, heavily blurred. 1 = hyper-arid.
DESERTS = [
    [(-17, 21), (-10, 30.5), (0, 32), (10, 32.5), (20, 30.5), (26, 31.5), (32, 30.4), (34.6, 29),
     (38, 17), (34, 15.5), (24, 15.5), (15, 16), (5, 17), (-5, 18), (-16.5, 18)],  # Sahara
    [(34.8, 29.5), (37, 33.5), (41, 35.5), (46, 31.5), (48.5, 29), (51, 25), (56, 24), (59.5, 22),
     (55, 17), (48, 16.5), (43, 18), (38, 24)],  # Arabia + Syrian desert
    [(51, 35.7), (56, 36.6), (61, 34), (62, 29), (58, 27), (53, 29.5)],  # Iranian deserts
    [(55, 37.5), (60, 39), (64, 44), (61, 45.5), (56, 43), (53, 41)],  # Karakum
    [(64, 40), (68, 41), (66.5, 44.5), (62, 43)],  # Kyzylkum
    [(69, 24), (74, 26.5), (75.5, 29.5), (71, 30), (68.5, 27)],  # Thar
    [(76.5, 38.5), (80, 41.2), (88, 41.2), (90.5, 40), (88, 37.6), (82, 37), (77.5, 37.5)],  # Taklamakan
    [(91, 40.5), (96, 42.5), (104, 44.5), (112, 45.5), (114, 43), (108, 41.6), (100, 39.5), (95, 39.8)],  # Gobi/Alashan
    [(-114, 26), (-110, 31), (-104, 30), (-103.5, 25)],  # Sonoran/Chihuahuan edge
]
STEPPE = [
    [(30, 45.5), (40, 47), (50, 46.5), (60, 47.5), (75, 48.5), (85, 49), (85, 45.5), (78, 44), (62, 45.5),
     (52, 44.5), (45, 44), (38, 44.5)],  # Pontic-Kazakh steppe
    [(30.5, 37.5), (35, 39.5), (40, 39.5), (38, 37.2), (33, 37.3)],  # central Anatolia
    [(45, 33), (50, 37), (57, 37.5), (62, 36), (64, 31), (61, 27), (55, 27), (50, 30)],  # Iranian plateau
    [(105, 43.5), (115, 46.5), (120, 48), (118, 43), (110, 41.2)],  # Mongolian steppe
    [(80, 30), (90, 33.5), (100, 34), (97, 31), (88, 29.5)],  # Tibetan plateau (cold steppe)
    [(-6.5, 37.5), (-4, 41.5), (-1, 41.6), (-2.5, 38)],  # Iberian meseta
    [(-10, 15.5), (5, 16), (20, 15), (36, 13), (38, 9), (30, 11), (15, 12.5), (0, 13.5), (-15, 13.5)],  # Sahel
]


def blurred_poly_mask(polys, lon, lat, ppd, sigma_deg):
    W, H = len(lon), len(lat)
    lon0, lat1 = lon[0] - 0.5 / ppd, lat[0] + 0.5 / ppd
    m = rasterize([Polygon(p) for p in polys], lon0, lat1, ppd, W, H)
    k = max(3, int(sigma_deg * ppd * 3) | 1)
    return cv2.GaussianBlur(m, (k, k), sigma_deg * ppd)


def value_noise(H, W, scale, seed, octaves=4):
    rng = np.random.default_rng(seed)
    acc = np.zeros((H, W), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = max(2, int(H / scale * 2 ** o)), max(2, int(W / scale * 2 ** o))
        g = rng.random((gh, gw)).astype(np.float32)
        acc += amp * cv2.resize(g, (W, H), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= 0.5
    return acc / tot


def hillshade(elev, lat, ppd, exaggeration=2.2):
    dy_m = 111_320.0 / ppd
    dx_m = dy_m * np.cos(np.radians(lat))[:, None]
    gy, gx = np.gradient(elev)
    gx = gx / dx_m * exaggeration
    gy = -gy / dy_m * exaggeration
    nz = 1.0 / np.sqrt(1 + gx ** 2 + gy ** 2)
    nx, ny = -gx * nz, -gy * nz
    out = 0.0
    # multi-directional light (NW dominant) avoids the flat look of a single sun
    for az, alt, w in [(315, 40, 0.6), (270, 45, 0.2), (0, 50, 0.2)]:
        a, b = math.radians(az), math.radians(alt)
        lx, ly, lz = math.sin(a) * math.cos(b), math.cos(a) * math.cos(b), math.sin(b)
        out = out + w * np.clip(nx * lx + ny * ly + nz * lz, 0, 1)
    flat = math.sin(math.radians(45))
    return out / flat  # 1.0 on flat ground


def lerp(a, b, t):
    return a + (b - a) * t[..., None]


def C(hexs):
    return np.array([int(hexs[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


FERTILE = [
    [(29.9, 30.9), (30.4, 31.55), (31.0, 31.6), (31.9, 31.5), (32.3, 31.1), (31.3, 30.1), (31.2, 29.9)],  # Nile Delta
    [(43.6, 33.9), (44.6, 33.6), (45.6, 32.6), (46.9, 31.6), (47.6, 30.6), (46.6, 30.4), (45.2, 31.4),
     (44.0, 32.4), (43.4, 33.4)],  # Mesopotamian alluvium
    [(30.6, 29.6), (31.0, 29.6), (31.0, 29.1), (30.5, 29.1)],  # Fayum
]
OASIS_RIVERS = {"Nile", "Tigris", "Euphrates", "Indus", "Amu  Darya", "Syr  Darya", "Tarim", "Helmand",
                "Harirud", "Jordan", "Niger", "Huang"}


def river_mask(lon, lat, ppd, width_deg=0.35):
    """Green corridors along desert rivers (the Nile valley above all)."""
    W, H = len(lon), len(lat)
    lon0, lat1 = lon[0] - 0.5 / ppd, lat[0] + 0.5 / ppd
    arr = np.zeros((H, W, 4), np.uint8)
    surf = skia.Surface(arr, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
    c = surf.getCanvas()
    paint = skia.Paint(AntiAlias=True, Color=skia.ColorWHITE, Style=skia.Paint.kStroke_Style,
                       StrokeWidth=width_deg * ppd, StrokeCap=skia.Paint.kRound_Cap)
    d = json.load(open(ROOT / "assets/geo/ne_10m_rivers_lake_centerlines.geojson"))
    for f in d["features"]:
        if (f["properties"].get("name") or "") not in OASIS_RIVERS:
            continue
        g = shape(f["geometry"])
        for line in ([g] if g.geom_type == "LineString" else list(g.geoms)):
            pts = np.asarray(line.coords)
            path = skia.Path()
            path.moveTo((pts[0, 0] - lon0) * ppd, (lat1 - pts[0, 1]) * ppd)
            for x, y in pts[1:, :2]:
                path.lineTo((x - lon0) * ppd, (lat1 - y) * ppd)
            c.drawPath(path, paint)
    m = arr[:, :, 0].astype(np.float32) / 255
    k = max(3, int(0.25 * ppd * 3) | 1)
    return cv2.GaussianBlur(m, (k, k), 0.2 * ppd)


def warp(mask, ppd, seed, amp_deg=1.2):
    H, W = mask.shape
    nx = value_noise(H, W, ppd * 4, seed, 4) - 0.5
    ny = value_noise(H, W, ppd * 4, seed + 1, 4) - 0.5
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    return cv2.remap(mask, gx + nx * 2 * amp_deg * ppd, gy + ny * 2 * amp_deg * ppd, cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_REFLECT)


def colorize(elev, land, arid, steppe, shade, lat, noise, detail, rivers):
    t = np.clip
    shp = elev.shape + (3,)

    def col(h):
        return np.broadcast_to(C(h), shp)
    # ocean: smooth depth ramp, faint shelf
    depth = t(-elev / 5000.0, 0, 1) ** 0.5
    ocean = lerp(col("#1d3f4c"), col("#07121c"), depth)
    shelf = t(1 - (-elev) / 60.0, 0, 1) * (elev < 0)
    ocean = lerp(ocean, col("#2c5a63"), shelf * 0.35)
    # land
    e = t(elev, 0, 6500)
    absl = np.abs(lat)[:, None] * np.ones_like(elev)
    forest = lerp(col("#4b5c33"), col("#37492c"), t(detail * 1.4 - 0.2, 0, 1))
    grass = lerp(col("#66703f"), col("#7a7a4a"), noise)
    veg = lerp(forest, grass, t(noise * 1.3 - 0.15, 0, 1) * 0.6)
    veg = lerp(veg, col("#2c3f26"), t((absl - 50) / 12, 0, 1) * 0.7)   # boreal
    veg = lerp(veg, col("#2a4623"), t(1 - absl / 16.0, 0, 1) * 0.8)    # tropical
    dry = lerp(col("#857a50"), col("#9a8a5c"), detail)
    base = lerp(veg, dry, t(steppe, 0, 1) * 0.8)
    # deserts: sandy lowlands vs. darker rocky plateaus, by relief
    sand = lerp(col("#b8955f"), col("#cdab73"), noise)
    sand = lerp(sand, col("#a8774a"), t((detail - 0.45) * 2.2, 0, 1) * 0.8)
    sand = lerp(sand, col("#8c7457"), t((0.5 - noise) * 2.5, 0, 1) * 0.5)
    rocky = lerp(col("#86705a"), col("#655446"), detail)
    rough = t((e - 300) / 900, 0, 1) * 0.7 + t((1 - shade) * 3, 0, 1) * 0.3
    desert = lerp(sand, rocky, t(rough, 0, 1))
    base = lerp(base, desert, t(arid, 0, 1))
    base = lerp(base, col("#47582c"), t(rivers * 1.6, 0, 1) * t(arid + steppe, 0, 1))
    hi = t((e - 1500) / 2200, 0, 1)
    base = lerp(base, col("#76695a"), hi * 0.7)
    rock = t((e - 4000) / 1400, 0, 1)
    base = lerp(base, col("#9a948a"), rock * 0.55)
    snow = t((e - 5300) / 800, 0, 1) * t((1 - shade) * 0 + 1, 0, 1) + t((absl - 66) / 6, 0, 1) * t(e / 300, 0, 1)
    base = lerp(base, col("#e4e7ea"), t(snow, 0, 1) * 0.85)
    base = base * (0.92 + 0.16 * detail[..., None])
    lit = base * t(shade, 0.2, 1.7)[..., None]
    rgb = lerp(ocean, lit, land)
    # documentary grade: slight desaturation
    g = rgb.mean(-1, keepdims=True)
    rgb = g + (rgb - g) * 0.85
    return t(rgb, 0, 1)


def build(name):
    z, lon0, lon1, lat0, lat1, ppd = REGIONS[name]
    elev, lon, lat = equirect_elevation(name)
    land = land_mask(lon, lat, ppd, elev)
    shade = hillshade(np.maximum(elev, 0) * (land > 0.5) + elev * (land <= 0.5) * 0.15, lat, ppd)
    H, W = elev.shape
    arid = warp(blurred_poly_mask(DESERTS, lon, lat, ppd, 0.7), ppd, 21)
    steppe = warp(blurred_poly_mask(STEPPE, lon, lat, ppd, 1.0), ppd, 23)
    noise = value_noise(H, W, ppd * 6, 7)
    detail = value_noise(H, W, ppd * 0.7, 11, 4)
    edge = value_noise(H, W, ppd * 1.5, 31, 5) - 0.5
    arid = np.clip((arid + edge * 0.5 - 0.3) / 0.42, 0, 1)
    arid = arid * arid * (3 - 2 * arid)
    arid = arid * np.clip(1.25 - np.maximum(elev, 0) / 3500, 0, 1)
    steppe = np.clip((steppe + edge * 0.5 - 0.25) / 0.5, 0, 1) * 0.7
    rivers = np.maximum(river_mask(lon, lat, ppd, 0.16), blurred_poly_mask(FERTILE, lon, lat, ppd, 0.15))
    rgb = colorize(elev, land, arid, steppe, shade, lat, noise, detail, rivers)
    OUT.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUT / f"{name}.png"), (rgb[:, :, ::-1] * 255).astype(np.uint8))
    np.save(OUT / f"{name}_land.npy", (land * 255).astype(np.uint8))
    np.save(OUT / f"{name}_elev.npy", elev.astype(np.float16))
    json.dump({"lon0": float(lon[0] - 0.5 / ppd), "lat1": float(lat[0] + 0.5 / ppd), "ppd": ppd, "W": W, "H": H},
              open(OUT / f"{name}.json", "w"))
    print(name, rgb.shape)


if __name__ == "__main__":
    import sys
    for n in (sys.argv[1:] or REGIONS):
        build(n)
