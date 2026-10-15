"""Monocular depth for the real photographs (Depth Anything V2 Small, Apache-2.0, ONNX on CPU).

Writes build/depth/<name>.npy: relative depth (near = larger), full image resolution,
upsampled with an edge-aware joint filter guided by the photo."""
import sys
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

MODEL = __import__("os").environ.get("DEPTH_MODEL", "depth_anything_v2_vits.onnx")
OUT = Path(__file__).resolve().parents[1] / "build" / "depth"


def infer(img_bgr, size=518):
    """The exported graph takes a fixed 518x518 input: pad the photo to a square, infer, crop back."""
    sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
    inp = sess.get_inputs()[0]
    h, w = img_bgr.shape[:2]
    n = max(h, w)
    pad = np.zeros((n, n, 3), np.uint8)
    pad[:] = np.median(img_bgr[:20, :20].reshape(-1, 3), axis=0)
    y0, x0 = (n - h) // 2, (n - w) // 2
    pad[y0:y0 + h, x0:x0 + w] = img_bgr
    x = cv2.resize(pad, (size, size), interpolation=cv2.INTER_AREA)[..., ::-1].astype(np.float32) / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    x = x.transpose(2, 0, 1)[None].astype(np.float32)
    d = np.squeeze(sess.run(None, {inp.name: x})[0]).astype(np.float32)
    d = cv2.resize(d, (n, n), interpolation=cv2.INTER_CUBIC)[y0:y0 + h, x0:x0 + w]
    return d


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for p in sys.argv[1:]:
        img = cv2.imread(p)
        d = infer(img)
        d = (d - d.min()) / (d.max() - d.min() + 1e-9)
        full = d
        try:
            full = cv2.ximgproc.guidedFilter(img, full, 8, 1e-4)
        except AttributeError:
            full = cv2.bilateralFilter(full, 9, 0.05, 6)
        np.save(OUT / (Path(p).stem + ".npy"), full.astype(np.float32))
        vis = (np.clip(full, 0, 1) * 255).astype(np.uint8)
        cv2.imwrite(str(OUT / (Path(p).stem + "_depth.png")), cv2.resize(vis, (vis.shape[1] // 4, vis.shape[0] // 4)))
        print(p, d.shape, full.shape)


if __name__ == "__main__":
    main()
