"""Build the Limyra terrain: Copernicus GLO-30 DEM resampled onto the Sentinel-2 crop grid.

Output build/terrain/{height.npy (m, float32), albedo.npy (linear RGB, float16), meta.json}.
World frame used by the film: x = east, y = up, z = north, origin at Limyra, metres."""
import json
from pathlib import Path

import cv2
import numpy as np
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "plan" / "real_images"
OUT = ROOT / "build" / "terrain"
LIMYRA_LATLON = (36.3436, 30.1708)


def main(step=2):
    OUT.mkdir(parents=True, exist_ok=True)
    meta = json.load(open(REAL / "1_s2_limyra-finike-kumluca_2025-07-06_10m_7680x4320.json"))["crop"]
    s2 = cv2.imread(str(REAL / "1_s2_limyra-finike-kumluca_2025-07-06_10m_7680x4320.jpg"))
    dem = cv2.imread(str(REAL / "terrain" / "Copernicus_DSM_COG_10_N36_00_E030_00_DEM.tif"), cv2.IMREAD_UNCHANGED)
    px = meta["pixel_size_m"] * step
    H, W = s2.shape[0] // step, s2.shape[1] // step
    s2 = cv2.resize(s2, (W, H), interpolation=cv2.INTER_AREA)
    E = meta["ul_easting"] + (np.arange(W) + 0.5) * px
    N = meta["ul_northing"] - (np.arange(H) + 0.5) * px
    EE, NN = np.meshgrid(E, N)
    tr = Transformer.from_crs("EPSG:32636", "EPSG:4326", always_xy=True)
    lon, lat = tr.transform(EE, NN)
    # DEM pixel coords (top-left 37N 30E, 1 arcsec), pixel-is-area
    col = (lon - 30.0) * 3600 - 0.5
    row = (37.0 - lat) * 3600 - 0.5
    h = cv2.remap(dem, col.astype(np.float32), row.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    h = np.maximum(h, 0.0).astype(np.float32)
    # Limyra in the crop
    le, ln = Transformer.from_crs("EPSG:4326", "EPSG:32636", always_xy=True).transform(LIMYRA_LATLON[1], LIMYRA_LATLON[0])
    rgb = s2[..., ::-1].astype(np.float32) / 255
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    np.save(OUT / "height.npy", h)
    np.save(OUT / "albedo.npy", lin.astype(np.float16))
    json.dump(dict(texel=px, W=W, H=H, ul_e=meta["ul_easting"], ul_n=meta["ul_northing"],
                   limyra_e=le, limyra_n=ln, hmax=float(h.max())), open(OUT / "meta.json", "w"), indent=1)
    print("terrain", W, H, "texel", px, "hmax", h.max(), "limyra px", (le - meta["ul_easting"]) / px, (meta["ul_northing"] - ln) / px)


if __name__ == "__main__":
    main()
