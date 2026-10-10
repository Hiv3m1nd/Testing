"""Fetch open terrain tiles (AWS Terrain Tiles / Mapzen "terrarium" encoding).

Terrain Tiles are open data on AWS (s3://elevation-tiles-prod), compiled from
SRTM, GMTED2010, ETOPO1 and other sources - see research/sources.md for the
attribution line used in the video description.

Usage: python fetch_data.py   (idempotent; skips tiles already on disk)
"""
import math
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CACHE = Path(os.environ.get("TILE_CACHE", Path(__file__).resolve().parents[1] / "build" / "tiles"))
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"


def tile_range(z, lon0, lon1, lat0, lat1):
    n = 2 ** z
    def tx(lon):
        return int((lon + 180) / 360 * n)
    def ty(lat):
        r = math.radians(lat)
        return int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n)
    xs = range(max(0, tx(lon0)), min(n - 1, tx(lon1)) + 1)
    ys = range(max(0, ty(lat1)), min(n - 1, ty(lat0)) + 1)
    return [(z, x, y) for x in xs for y in ys]


def fetch(t):
    z, x, y = t
    p = CACHE / str(z) / str(x) / f"{y}.png"
    if p.exists() and p.stat().st_size > 0:
        return 0
    p.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(URL.format(z=z, x=x, y=y), timeout=60) as r:
                data = r.read()
            p.write_bytes(data)
            return len(data)
        except Exception as e:  # network hiccup: retry
            err = e
    print("failed", t, err, file=sys.stderr)
    return 0


REGIONS = [
    (4, -180, 180, -85, 85),      # whole globe, coarse
    (6, -20, 136, -6, 62),        # Old World: Atlantic to Korea, Sahara to Baltic
    (6, -112, -78, 8, 28),        # Mesoamerica
]

if __name__ == "__main__":
    tiles = [t for reg in REGIONS for t in tile_range(*reg)]
    print(len(tiles), "tiles")
    with ThreadPoolExecutor(16) as ex:
        total = sum(ex.map(fetch, tiles))
    print(f"downloaded {total/1e6:.1f} MB")
