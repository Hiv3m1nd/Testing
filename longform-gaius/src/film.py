"""Assemble the cold open: shots -> dissolves -> global finish -> letterbox -> HDR10 / SDR.

  python film.py --stills 3,8,13 --width 960          # SDR PNG stills for QA (build/stills)
  python film.py --from 0 --to 48.2 --width 1920 --sdr-only --tag draft   # draft segments
  python film.py --from 0 --to 48.2 --width 3840 --tag master             # HDR10 + SDR segments
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

import hdr
import post
import shots

FPS = 24
ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
ASPECT = 2.39
MASTER_DISPLAY = "G(13250,34500)B(7500,3000)R(34000,16000)WP(15635,16450)L(10000000,1)"


def active_h(W):
    return int(round(W / ASPECT / 2)) * 2


def render_frame(t, W, frame):
    H = int(round(W * 9 / 16))
    AH = active_h(W)
    act = [(fn, a, b) for (fn, a, b) in shots.EDIT if a <= t < b]
    out = None
    if len(act) == 1:
        out = act[0][0](t, W, AH, frame)[0]
    elif len(act) >= 2:
        (f1, a1, b1), (f2, a2, b2) = act[0], act[1]
        w = post.ease_io((t - a2) / (b1 - a2))
        i1 = f1(t, W, AH, frame)[0]
        i2 = f2(t, W, AH, frame)[0]
        out = i1 * (1 - w) + i2 * w
    else:
        out = np.zeros((AH, W, 3), np.float32)
    img = out.astype(np.float32)
    img = post.bloom(img, 0.06)
    img = post.glare(img, threshold=3.5, amount=0.03, length_frac=0.12)
    img = post.vignette(img, 0.30)
    img = post.grain(img, frame, 0.010)
    # global fades: in from black, out to black
    k = post.ease(t / 1.4) * post.ease((shots.DURATION - t) / 1.2)
    img *= k
    full = np.zeros((H, W, 3), np.float32)
    y0 = (H - AH) // 2
    full[y0:y0 + AH] = img
    return full


def to_pq16(lin):
    x = np.maximum(lin.astype(np.float32), 0)
    m = x.max(axis=2, keepdims=True) * hdr.REF_WHITE
    scale = np.where(m > 1e-6, hdr.rolloff_nits(m) / np.maximum(m, 1e-6), 1.0)
    nits = x * hdr.REF_WHITE * scale
    nits2020 = np.maximum(nits @ hdr.M709_2020.T, 0)
    e = hdr.pq_oetf(nits2020)
    return np.round(e * 65535).astype(np.uint16), float(nits2020.max()), float(nits2020.mean())


def hdr_cmd(W, H, out, crf=14, preset="slow", max_cll=1000, max_fall=60):
    x265 = ":".join(["colorprim=bt2020", "transfer=smpte2084", "colormatrix=bt2020nc", "range=limited",
                     "chromaloc=2", f"master-display={MASTER_DISPLAY}", f"max-cll={max_cll},{max_fall}",
                     "hdr10=1", "hdr10-opt=1", "repeat-headers=1", "aq-mode=3", "log-level=error",
                     f"keyint={FPS * 2}", "open-gop=0"])
    return ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb48le", "-s", f"{W}x{H}", "-r", str(FPS),
            "-color_primaries", "bt2020", "-color_trc", "smpte2084", "-colorspace", "rgb", "-color_range", "pc",
            "-i", "-",
            "-vf", ("zscale=pin=2020:tin=smpte2084:min=gbr:rin=full:"
                    "p=2020:t=smpte2084:m=2020_ncl:r=limited:c=topleft:d=error_diffusion,format=yuv420p10le"),
            "-c:v", "libx265", "-preset", preset, "-crf", str(crf), "-profile:v", "main10", "-x265-params", x265,
            "-color_primaries", "bt2020", "-color_trc", "smpte2084", "-colorspace", "bt2020nc",
            "-color_range", "tv", "-chroma_sample_location", "topleft", "-tag:v", "hvc1", str(out)]


def sdr_cmd(W, H, out, crf=14):
    return ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "rgb", "-i", "-",
            "-vf", "zscale=min=gbr:rin=full:m=709:r=limited:c=left:d=error_diffusion,format=yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-profile:v", "high", "-g", str(FPS * 2),
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv", str(out)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", default="")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--from", dest="t0", type=float, default=0.0)
    ap.add_argument("--to", dest="t1", type=float, default=shots.DURATION)
    ap.add_argument("--chunk", type=int, default=48)
    ap.add_argument("--sdr-only", action="store_true")
    ap.add_argument("--tag", default="draft")
    ap.add_argument("--max-fall", type=int, default=60)
    a = ap.parse_args()
    W = a.width
    H = int(round(W * 9 / 16))
    if a.stills:
        d = BUILD / "stills"
        d.mkdir(parents=True, exist_ok=True)
        for s in a.stills.split(","):
            t = float(s)
            t0 = time.time()
            img = render_frame(t, W, int(round(t * FPS)))
            cv2.imwrite(str(d / f"t{t:06.2f}_w{W}.png"), hdr.to_sdr8(img)[..., ::-1])
            print(f"still t={t:.2f} {time.time() - t0:.1f}s", flush=True)
        return
    segd = BUILD / "seg" / a.tag
    segd.mkdir(parents=True, exist_ok=True)
    f0, f1 = int(round(a.t0 * FPS)), int(round(a.t1 * FPS))
    stats = []
    for c0 in range(f0 - f0 % a.chunk, f1, a.chunk):
        c1 = min(c0 + a.chunk, int(round(shots.DURATION * FPS)))
        sdr_p = segd / f"sdr_{c0:05d}.mp4"
        hdr_p = segd / f"hdr_{c0:05d}.mp4"
        if sdr_p.exists() and (a.sdr_only or hdr_p.exists()):
            continue
        ps = subprocess.Popen(sdr_cmd(W, H, str(sdr_p) + ".tmp.mp4"), stdin=subprocess.PIPE)
        ph = None if a.sdr_only else subprocess.Popen(hdr_cmd(W, H, str(hdr_p) + ".tmp.mp4", max_fall=a.max_fall),
                                                       stdin=subprocess.PIPE)
        tc = time.time()
        for fr in range(c0, c1):
            t = fr / FPS
            img = render_frame(t, W, fr)
            ps.stdin.write(hdr.to_sdr8(img).tobytes())
            if ph:
                pq, mx, avg = to_pq16(img)
                ph.stdin.write(pq.tobytes())
                stats.append((fr, mx, avg))
        ps.stdin.close()
        ps.wait()
        os.replace(str(sdr_p) + ".tmp.mp4", sdr_p)
        if ph:
            ph.stdin.close()
            ph.wait()
            os.replace(str(hdr_p) + ".tmp.mp4", hdr_p)
        print(f"chunk {c0}-{c1} done in {time.time() - tc:.0f}s ({(time.time() - tc) / (c1 - c0):.1f}s/frame)", flush=True)
    if stats:
        with open(segd / f"stats_{f0:05d}.json", "w") as fh:
            json.dump(stats, fh)


if __name__ == "__main__":
    main()
