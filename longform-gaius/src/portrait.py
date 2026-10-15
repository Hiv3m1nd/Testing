"""Real photographs of sculpture lifted into 2.5D and relit by a moving torch.

The photograph supplies colour and fine detail; Depth Anything V2 (Small) supplies the
shape. The studio light baked into the photo is divided out (partially) so the new
light can model the face. The background becomes empty space."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

import hfr

ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "plan" / "real_images"
DEPTH = ROOT / "build" / "depth"


PARAMS = {
    "3_met_possibly-gaius-caesar_head_three-quarter-dark": dict(dome_w=0.55, blur_px=14.0, depth_m=0.13),
    "3_met_possibly-gaius-caesar_head_front-dark": dict(dome_w=0.35, blur_px=8.0, depth_m=0.15),
    "3_met_augustus_marble-portrait_07-286-115_dark": dict(dome_w=0.25, blur_px=4.0),
}


def srgb_to_lin(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def build(name, scale=0.55, head_width_m=0.24, depth_m=0.16, detail=0.0025, old_light=(-0.25, -0.35, 0.90),
          delight=0.65, thresh=None, crop=None, dome_w=0.0, blur_px=0.1):
    img = cv2.imread(str(REAL / f"{name}.jpg"))
    dep = np.load(DEPTH / f"{name}.npy")
    if crop is not None:
        y0, y1, x0, x1 = crop
        img, dep = img[y0:y1, x0:x1], dep[y0:y1, x0:x1]
    h, w = img.shape[:2]
    W2, H2 = int(w * scale), int(h * scale)
    img = cv2.resize(img, (W2, H2), interpolation=cv2.INTER_AREA)
    dep = cv2.resize(dep, (W2, H2), interpolation=cv2.INTER_AREA)
    rgb = srgb_to_lin(img[..., ::-1].astype(np.float32) / 255.0)
    # --- object mask from depth (Otsu) refined by colour distance from the backdrop
    d8 = (np.clip(dep, 0, 1) * 255).astype(np.uint8)
    t, _ = cv2.threshold(d8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if thresh is not None:
        t = thresh * 255
    m = (d8 > t).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    keep = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    m = (lab == keep).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    # smooth the outline: blur the binary mask and re-threshold
    m = (cv2.GaussianBlur(m.astype(np.float32), (0, 0), 4.0) > 0.5).astype(np.uint8)
    m = cv2.erode(m, np.ones((5, 5), np.uint8))
    mask = m.astype(bool)
    # --- object width in pixels sets the texel size
    xs = np.where(mask.any(0))[0]
    obj_w = xs.max() - xs.min()
    texel = head_width_m / obj_w
    # --- height: smooth depth inside the mask, stretched to a plausible head depth
    dv = dep[mask]
    lo, hi = np.percentile(dv, 1), np.percentile(dv, 99.5)
    base = np.clip((dep - lo) / (hi - lo), 0, 1)
    base = cv2.GaussianBlur(base, (0, 0), 7.0)
    # round the silhouette off so the edge falls away like a real head, not a cardboard cut-out
    dist = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    edge = np.clip(dist / (obj_w * 0.10), 0, 1)
    edge = np.sqrt(1 - (1 - edge) ** 2)
    # a smooth convex "dome" prior from the outline, blended with the estimated depth: keeps the
    # features the model sees but removes the cliffs it sometimes invents at temples and hairlines
    dome = np.sqrt(np.clip(dist / (dist.max() + 1e-6), 0, 1))
    dome = cv2.GaussianBlur(dome, (0, 0), obj_w * 0.03)
    base = dome_w * dome + (1 - dome_w) * cv2.GaussianBlur(base, (0, 0), blur_px)
    height = (0.25 + 0.75 * base) * edge * depth_m
    # fine carving detail from the photograph's local contrast (hair, eyelids, lips)
    lum = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    hp = lum - cv2.GaussianBlur(lum, (0, 0), 5.0)
    hp2 = lum - cv2.GaussianBlur(lum, (0, 0), 1.5)
    smooth_h = np.where(mask, height, hfr.HOLE).astype(np.float32)
    height = height + (hp * 0.7 + hp2 * 0.3) * detail
    height = np.where(mask, height, hfr.HOLE).astype(np.float32)
    # --- de-light: divide out an estimate of the studio light
    gy, gx = np.gradient(cv2.GaussianBlur(np.where(mask, height, 0).astype(np.float32), (0, 0), 3.0))
    nrm = np.dstack([-gx / texel, -gy / texel, np.ones_like(gx)])
    nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
    lo_ = np.asarray(old_light, np.float32)
    lo_ /= np.linalg.norm(lo_)
    sh_old = np.clip(nrm @ lo_, 0, 1) * 0.65 + 0.35
    alb = rgb / (sh_old[..., None] ** delight)
    alb = alb / np.percentile(alb[mask].mean(1), 70) * 0.62
    # temper the photo's warm cast so the torch, not the print, sets the colour
    grey = alb.mean(2, keepdims=True)
    alb = grey + (alb - grey) * 0.7
    alb = np.clip(alb, 0, 0.95).astype(np.float32)
    # height units = metres; hscale 1
    return dict(hm=height, hm_shadow=smooth_h, albedo=alb, texel=texel, size=(W2, H2), mask=mask)


def relief(name, centre=(0.0, 0.0, 0.0), crop=None, **kw):
    kw = {**PARAMS.get(name, {}), **kw}
    """Place the photo in the world facing -z (toward a camera on the -z side), centred at `centre`."""
    b = build(name, crop=crop, **kw)
    W2, H2 = b["size"]
    tx = b["texel"]
    # local frame: U = +x (image right), V = -y (image down), N = -z (out toward the camera)
    u, v, n = np.array([1.0, 0, 0]), np.array([0, -1.0, 0]), np.array([0, 0, -1.0])
    o = np.asarray(centre) - u * (W2 / 2) * tx - v * (H2 / 2) * tx
    return hfr.Relief(b["hm"], b["albedo"], o, u, v, n, tx, 1.0, hm_shadow=b["hm_shadow"]), b
