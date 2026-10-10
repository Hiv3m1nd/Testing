"""Render the film: shot list -> frames -> parallel x264 segments -> concat.

Usage:
  python render.py                 # full render to build/video.mp4 (no audio)
  python render.py --from 60 --to 75 --out build/test.mp4   # a test range
  python render.py --frames 10,45.5,120 --stills build/stills  # PNG stills
"""
from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import captions  # noqa: E402
import gfx  # noqa: E402
import scenes_a as A  # noqa: E402
import scenes_b as B  # noqa: E402
from gfx import FPS, H, W  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
END = 173.6

# (renderer, start, end). Neighbouring shots overlap; the overlap is a dissolve.
SHOTS = [
    (A.s_open, 0.0, 5.3),
    (A.s_calendar, 4.5, 27.6),
    (A.s_inscription, 27.0, 36.5),
    (A.s_yuanshi, 35.9, 44.4),
    (A.s_empires, 43.6, 62.9),
    (B.s_rome, 62.5, 74.9),
    (B.s_journey, 74.1, 119.6),
    (B.s_changan, 118.9, 129.4),
    (B.s_pheasant, 128.8, 149.7),
    (B.s_close, 149.1, 160.9),
    (B.s_next, 160.3, 169.7),
    (B.s_end, 169.0, END),
]


def frame(t: float, idx: int) -> np.ndarray:
    active = [(fn, a, b) for fn, a, b in SHOTS if a <= t < b]
    if len(active) == 1:
        img = active[0][0](t)
    else:
        (f1, a1, b1), (f2, a2, b2) = active[:2]
        w = gfx.smoother(gfx.seg(t, a2, b1))
        img = f1(t) * (1 - w) + f2(t) * w if 0 < w < 1 else (f2(t) if w >= 1 else f1(t))
    warm = 0.35
    img = gfx.finish(img, idx, warm=warm)
    img = img * (1 - gfx.smooth(gfx.seg(t, END - 0.7, END)))  # fade out
    cv = gfx.Canvas.from_float(img)
    captions.draw(cv, t)
    return cv.arr[..., :3]


def encode_chunk(args):
    k, f0, f1, path = args
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-pix_fmt", "yuv420p",
           "-g", str(FPS * 2), str(path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(f0, f1):
        p.stdin.write(np.ascontiguousarray(frame(i / FPS, i)).tobytes())
        if (i - f0) % 60 == 0:
            el = time.time() - t0
            print(f"[chunk {k}] {i - f0}/{f1 - f0} frames, {el:.0f}s", flush=True)
    p.stdin.close()
    p.wait()
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="t0", type=float, default=0.0)
    ap.add_argument("--to", dest="t1", type=float, default=END)
    ap.add_argument("--out", default=str(ROOT / "build" / "video.mp4"))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--chunks", type=int, default=16)
    ap.add_argument("--frames", default=None)
    ap.add_argument("--only", default=None, help="comma-separated chunk indices to re-render, then re-concat all")
    ap.add_argument("--stills", default=str(ROOT / "build" / "stills"))
    a = ap.parse_args()
    if a.frames:
        out = Path(a.stills)
        out.mkdir(parents=True, exist_ok=True)
        for tt in [float(x) for x in a.frames.split(",")]:
            img = frame(tt, int(tt * FPS))
            cv2.imwrite(str(out / f"t{tt:07.2f}.png"), img[..., ::-1])
            print("wrote", tt)
        return
    f0, f1 = int(round(a.t0 * FPS)), int(math.ceil(a.t1 * FPS))
    segdir = ROOT / "build" / "segments"
    segdir.mkdir(parents=True, exist_ok=True)
    n = max(1, a.chunks)
    bounds = np.linspace(f0, f1, n + 1).astype(int)
    jobs = [(k, int(bounds[k]), int(bounds[k + 1]), segdir / f"seg_{k:03d}.mp4") for k in range(n)
            if bounds[k + 1] > bounds[k]]
    t0 = time.time()
    todo = jobs
    if a.only:
        keep = {int(x) for x in a.only.split(",")}
        todo = [j for j in jobs if j[0] in keep]
    with Pool(a.workers) as pool:
        pool.map(encode_chunk, todo, chunksize=1)
    paths = [j[3] for j in jobs]
    lst = segdir / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in paths))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    a.out], check=True)
    print(f"done {a.out} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
