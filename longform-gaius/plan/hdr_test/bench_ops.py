#!/usr/bin/env python3
"""Per-frame cost of 4K (3840x2160) float32 compositing on this CPU box.

  python bench_ops.py micro              # single-op timings (1 thread and all threads)
  python bench_ops.py heavy  [--src IMG] # one 'heavy' compositing frame, stage by stage
  python bench_ops.py pool   [--src IMG] [--workers 4] [--frames 8]
  python bench_ops.py e2e1   [--src IMG] [--workers 4] [--frames 96]   # N renderers -> ONE x265
  python bench_ops.py e2e    [--src IMG] [--workers 4] [--frames 48] [--preset medium] [--out F]
        e2e = real chunked pipeline: N worker processes each render heavy frames and pipe
        rgb48le into their own x265 HDR10 encoder; chunks concatenated with -c copy.

The heavy frame models a 2.5D 'living photograph' shot: a real photo pushed in with a
depth-driven parallax remap, a foreground layer warped separately and alpha-composited,
depth-of-field blur, 3-level bloom, atmospheric haze, colour grade, vignette, grain,
then linear BT.709 -> BT.2020 -> roll-off -> PQ -> uint16 (fused numba kernel).
"""
import argparse
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

if "--threads1" in sys.argv:
    os.environ["NUMBA_NUM_THREADS"] = "1"
import cv2  # noqa: E402
import numba  # noqa: E402
import numpy as np  # noqa: E402
from numba import njit, prange  # noqa: E402

W, H = 3840, 2160
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from make_hdr_test import (FPS, KNEE, M709_TO_2020, MASTER_DISPLAY, PEAK, PQ_C1, PQ_C2,  # noqa: E402
                           PQ_C3, PQ_M1, PQ_M2, REF_WHITE, pq_inverse_eotf)

DEFAULT_SRC = HERE.parent / "real_images" / "1_s2_limyra-finike-kumluca_2025-07-06_10m_7680x4320.jpg"
M = M709_TO_2020.astype(np.float32)


# ----------------------------------------------------------------------------- fused kernels

@njit(parallel=True, fastmath=True, cache=True)
def lin709_to_pq16_pow(img, out, ref_white, knee, peak):
    h, w, _ = img.shape
    span = peak - knee
    for y in prange(h):
        for x in range(w):
            r, g, b = img[y, x, 0], img[y, x, 1], img[y, x, 2]
            R = max((0.627403895934699 * r + 0.329283038377884 * g + 0.043313065687417 * b) * ref_white, 0.0)
            G = max((0.069097289358232 * r + 0.919540395075459 * g + 0.011362315566309 * b) * ref_white, 0.0)
            B = max((0.016391438875150 * r + 0.088013307877226 * g + 0.895595253247624 * b) * ref_white, 0.0)
            m = max(R, max(G, B))
            if m > knee:
                s = (knee + span * (1.0 - math.exp(-(m - knee) / span))) / m
                R *= s
                G *= s
                B *= s
            for c, v in ((0, R), (1, G), (2, B)):
                ym = (v * 1e-4) ** 0.1593017578125
                e = ((0.8359375 + 18.8515625 * ym) / (1.0 + 18.6875 * ym)) ** 78.84375
                out[y, x, c] = np.uint16(min(e, 1.0) * 65535.0 + 0.5)


def make_pq_lut(n=65536):
    """LUT indexed by q = (nits/10000)^(1/4) * (n-1): fine steps near black where PQ is steep."""
    q = np.linspace(0, 1, n, dtype=np.float64)
    nits = (q ** 4) * 10000.0
    return np.clip(np.round(pq_inverse_eotf(nits.astype(np.float32)).astype(np.float64) * 65535), 0,
                   65535).astype(np.uint16)


@njit(parallel=True, fastmath=True, cache=True)
def lin709_to_pq16_lut(img, out, lut, ref_white, knee, peak):
    h, w, _ = img.shape
    span = peak - knee
    n1 = lut.shape[0] - 1
    for y in prange(h):
        for x in range(w):
            r, g, b = img[y, x, 0], img[y, x, 1], img[y, x, 2]
            R = max((0.627403895934699 * r + 0.329283038377884 * g + 0.043313065687417 * b) * ref_white, 0.0)
            G = max((0.069097289358232 * r + 0.919540395075459 * g + 0.011362315566309 * b) * ref_white, 0.0)
            B = max((0.016391438875150 * r + 0.088013307877226 * g + 0.895595253247624 * b) * ref_white, 0.0)
            m = max(R, max(G, B))
            if m > knee:
                s = (knee + span * (1.0 - math.exp(-(m - knee) / span))) / m
                R *= s
                G *= s
                B *= s
            for c, v in ((0, R), (1, G), (2, B)):
                q = math.sqrt(math.sqrt(min(v * 1e-4, 1.0))) * n1
                i = int(q)
                if i >= n1:
                    out[y, x, c] = lut[n1]
                else:
                    f = q - i
                    out[y, x, c] = np.uint16(lut[i] + (np.float32(lut[i + 1]) - lut[i]) * f + 0.5)


@njit(parallel=True, fastmath=True, cache=True)
def madd3(a, gain, lift, out):
    h, w, _ = a.shape
    for y in prange(h):
        for x in range(w):
            for c in range(3):
                out[y, x, c] = a[y, x, c] * gain[c] + lift[c]


# ----------------------------------------------------------------------------- timing helpers

def timeit(fn, n=5, warm=1):
    for _ in range(warm):
        fn()
    ts = []
    for _ in range(n):
        t = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t)
    return float(np.median(ts))


def micro():
    rng = np.random.default_rng(0)
    img = rng.random((H, W, 3), dtype=np.float32) * 4
    img2 = rng.random((H, W, 3), dtype=np.float32)
    a1 = rng.random((H, W), dtype=np.float32)
    out = np.empty_like(img)
    o16 = np.empty((H, W, 3), np.uint16)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    mx = (xx + 3.3 * np.sin(yy / 50)).astype(np.float32)
    my = (yy + 2.1 * np.cos(xx / 70)).astype(np.float32)
    m1, m2 = cv2.convertMaps(mx, my, cv2.CV_16SC2)
    lut = make_pq_lut()
    gain = np.array([1.05, 1.0, 0.92], np.float32)
    lift = np.array([0.004, 0.003, 0.006], np.float32)
    A = np.float32(2.0)
    small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)

    ops = {
        "alloc+zero float32 4K RGB (np.zeros)": lambda: np.zeros((H, W, 3), np.float32),
        "copy float32 4K RGB": lambda: img.copy(),
        "GaussianBlur sigma=2": lambda: cv2.GaussianBlur(img, (0, 0), 2),
        "GaussianBlur sigma=8": lambda: cv2.GaussianBlur(img, (0, 0), 8),
        "GaussianBlur sigma=32": lambda: cv2.GaussianBlur(img, (0, 0), 32),
        "GaussianBlur sigma=32 via 1/4-res (resize down+blur 8+resize up)": lambda: cv2.resize(
            cv2.GaussianBlur(cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 8),
            (W, H), interpolation=cv2.INTER_LINEAR),
        "stackBlur ksize=65 (approx gaussian)": lambda: cv2.stackBlur(img, (65, 65)),
        "resize 1/4 -> 4K INTER_CUBIC": lambda: cv2.resize(small, (W, H), interpolation=cv2.INTER_CUBIC),
        "remap float maps INTER_LINEAR": lambda: cv2.remap(img, mx, my, cv2.INTER_LINEAR,
                                                           borderMode=cv2.BORDER_REFLECT),
        "remap fixed-point maps (CV_16SC2) INTER_LINEAR": lambda: cv2.remap(img, m1, m2, cv2.INTER_LINEAR,
                                                                            borderMode=cv2.BORDER_REFLECT),
        "remap float maps INTER_CUBIC": lambda: cv2.remap(img, mx, my, cv2.INTER_CUBIC,
                                                          borderMode=cv2.BORDER_REFLECT),
        "warpAffine INTER_LINEAR": lambda: cv2.warpAffine(img, np.float32([[1.01, 0.002, -5], [0, 1.01, -3]]),
                                                          (W, H), flags=cv2.INTER_LINEAR),
        "multiply-add numpy a*g+l (allocating)": lambda: img * gain + lift,
        "multiply-add numpy in-place (out=)": lambda: (np.multiply(img, gain, out=out), np.add(out, lift, out=out)),
        "multiply-add cv2.multiply+cv2.add (Scalar)": lambda: cv2.add(cv2.multiply(img, (1.05, 1.0, 0.92, 0)),
                                                                      (0.004, 0.003, 0.006, 0)),
        "multiply-add numba fused (parallel)": lambda: madd3(img, gain, lift, out),
        "alpha over numpy fg*a+bg*(1-a)": lambda: img * a1[..., None] + img2 * (1 - a1[..., None]),
        "alpha over cv2.blendLinear": lambda: cv2.blendLinear(img, img2, a1, 1 - a1),
        "3x3 colour matrix cv2.transform": lambda: cv2.transform(img, M),
        "3x3 colour matrix numpy img @ M.T": lambda: img @ M.T,
        "PQ numpy (2 pow, float32) on 3ch": lambda: pq_inverse_eotf(img * A),
        "PQ+709->2020+rolloff+pack numba pow (fused)": lambda: lin709_to_pq16_pow(img, o16, 203.0, 500.0, 1000.0),
        "PQ+709->2020+rolloff+pack numba LUT (fused)": lambda: lin709_to_pq16_lut(img, o16, lut, 203.0, 500.0,
                                                                                  1000.0),
        "uint16 pack numpy (clip*65535+0.5).astype": lambda: (np.clip(img2, 0, 1) * np.float32(65535)
                                                              + np.float32(0.5)).astype(np.uint16),
        "tobytes uint16 4K RGB (49.8 MB)": lambda: o16.tobytes(),
        "random normal 4K 1ch (fresh grain)": lambda: rng.standard_normal((H, W), dtype=np.float32),
    }
    res = {}
    for nthreads in (1, 4):
        cv2.setNumThreads(nthreads)
        numba.set_num_threads(min(nthreads, numba.config.NUMBA_NUM_THREADS))
        col = {}
        for name, fn in ops.items():
            col[name] = round(timeit(fn, n=3) * 1000, 1)
            print(f"[{nthreads}t] {name:62s} {col[name]:8.1f} ms", flush=True)
        res[f"{nthreads}_thread_ms"] = col
    # accuracy of LUT path vs pow path
    lin709_to_pq16_pow(img, o16, 203.0, 500.0, 1000.0)
    a = o16.astype(np.int32)
    lin709_to_pq16_lut(img, o16, lut, 203.0, 500.0, 1000.0)
    res["lut_vs_pow_max_abs_diff_16bit_codes"] = int(np.abs(a - o16.astype(np.int32)).max())
    print("LUT vs pow max |diff| (16-bit codes):", res["lut_vs_pow_max_abs_diff_16bit_codes"])
    return res


# ----------------------------------------------------------------------------- heavy frame

class HeavyShot:
    """A 2.5D 'living photograph' shot. All buffers preallocated; frame(i) -> uint16 PQ RGB."""

    def __init__(self, src_path):
        t = time.perf_counter()
        bgr = cv2.imread(str(src_path), cv2.IMREAD_COLOR)
        if bgr is None:
            raise SystemExit(f"cannot read {src_path}")
        # plate at 1.25x output for push-in headroom, sRGB decode -> linear (LUT on uint8)
        ph, pw = int(H * 1.25), int(W * 1.25)
        s = max(pw / bgr.shape[1], ph / bgr.shape[0])
        bgr = cv2.resize(bgr, (int(bgr.shape[1] * s) + 1, int(bgr.shape[0] * s) + 1), interpolation=cv2.INTER_AREA)
        y0, x0 = (bgr.shape[0] - ph) // 2, (bgr.shape[1] - pw) // 2
        rgb8 = cv2.cvtColor(bgr[y0:y0 + ph, x0:x0 + pw], cv2.COLOR_BGR2RGB)
        v = np.arange(256, dtype=np.float32) / 255
        lut = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4).astype(np.float32)
        self.plate = lut[rgb8]                                     # linear, (ph, pw, 3)
        self.pw, self.ph = pw, ph
        # synthetic depth (in production: MiDaS/Depth-Anything output) -> smooth, 0 far .. 1 near
        yy, xx = np.mgrid[0:ph, 0:pw].astype(np.float32)
        depth = np.clip(yy / ph * 0.9 + 0.1 * np.sin(xx / pw * 6.0), 0, 1)
        self.depth = cv2.GaussianBlur(depth, (0, 0), 25)
        del xx, yy, depth
        # foreground cut-out layer (in production: segmented subject), here a soft elliptical matte
        self.fg = cv2.GaussianBlur(self.plate[:H, :W] * np.float32(1.3), (0, 0), 1.0)
        oy, ox = np.mgrid[0:H, 0:W].astype(np.float32)
        self.fg_a = np.clip(1.2 - (((ox - W * 0.68) / (W * 0.18)) ** 2 + ((oy - H * 0.6) / (H * 0.32)) ** 2), 0,
                            1).astype(np.float32)
        r2 = ((ox - W / 2) / (W * 0.62)) ** 2 + ((oy - H / 2) / (H * 0.62)) ** 2
        self.vign = np.clip(1.0 - 0.55 * r2, 0.25, 1.0).astype(np.float32)[..., None].copy()
        self.haze = np.clip((1.0 - oy / H) * 0.06, 0, 1).astype(np.float32)[..., None] * np.array(
            [0.55, 0.62, 0.75], np.float32)
        rng = np.random.default_rng(3)
        self.grain = rng.standard_normal((H + 64, W + 64)).astype(np.float32) * np.float32(0.015)
        self.mapx = np.empty((H, W), np.float32)
        self.mapy = np.empty((H, W), np.float32)
        self.ox, self.oy = ox, oy
        self.dsmall = cv2.resize(self.depth, (W, H), interpolation=cv2.INTER_AREA)
        self.lut = make_pq_lut()
        self.out16 = np.empty((H, W, 3), np.uint16)
        self.gain = np.array([1.06, 1.0, 0.9], np.float32)
        self.lift = np.array([0.002, 0.0015, 0.003], np.float32)
        self.timings = {}
        self.init_s = time.perf_counter() - t

    def _t(self, k, t0):
        t1 = time.perf_counter()
        self.timings[k] = self.timings.get(k, 0.0) + (t1 - t0)
        return t1

    def frame(self, i):
        t = time.perf_counter()
        p = i / (FPS * 6.0)                                         # 6 s push-in
        z = 1.0 + 0.2 * p
        cam_x, cam_y = 0.02 * p, -0.01 * p
        # 1) depth-driven parallax remap of the plate (near pixels move more)
        par = (self.dsmall - 0.5) * np.float32(60.0 * p)
        np.multiply(self.ox - W / 2, np.float32(1.0 / (1.25 * z)), out=self.mapx)
        self.mapx += self.pw / 2 + cam_x * self.pw
        self.mapx -= par
        np.multiply(self.oy - H / 2, np.float32(1.0 / (1.25 * z)), out=self.mapy)
        self.mapy += self.ph / 2 + cam_y * self.ph
        self.mapy -= par * np.float32(0.3)
        bg = cv2.remap(self.plate, self.mapx, self.mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        t = self._t("parallax_remap", t)
        # 2) depth of field: blurred copy mixed by (1 - depth)
        blur = cv2.resize(cv2.GaussianBlur(cv2.resize(bg, (W // 2, H // 2), interpolation=cv2.INTER_AREA),
                                           (0, 0), 3.0), (W, H), interpolation=cv2.INTER_LINEAR)
        k = (1.0 - self.dsmall) ** 2
        bg = cv2.blendLinear(blur, bg, k, 1.0 - k)
        t = self._t("dof_blur_mix", t)
        # 3) foreground layer, own affine move, alpha over
        A = np.float32([[1.0 + 0.04 * p, 0, -W * 0.02 * p], [0, 1.0 + 0.04 * p, -H * 0.03 * p]])
        fg = cv2.warpAffine(self.fg, A, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        fa = cv2.warpAffine(self.fg_a, A, (W, H), flags=cv2.INTER_LINEAR)
        img = cv2.blendLinear(fg, bg, fa, 1.0 - fa)
        t = self._t("fg_warp_composite", t)
        # 4) bloom: 3 octaves from a thresholded copy
        hi = cv2.resize(img, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
        cv2.threshold(hi, 0.7, 0, cv2.THRESH_TOZERO, dst=hi)
        b1 = cv2.GaussianBlur(hi, (0, 0), 4)
        b2 = cv2.GaussianBlur(cv2.resize(b1, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 8)
        b3 = cv2.GaussianBlur(cv2.resize(b2, (W // 8, H // 8), interpolation=cv2.INTER_AREA), (0, 0), 16)
        b2 += cv2.resize(b3, (W // 4, H // 4), interpolation=cv2.INTER_LINEAR)
        b1 += cv2.resize(b2, (W // 2, H // 2), interpolation=cv2.INTER_LINEAR)
        cv2.scaleAdd(cv2.resize(b1, (W, H), interpolation=cv2.INTER_LINEAR), 0.25, img, dst=img)
        t = self._t("bloom_3oct", t)
        # 5) haze + grade + vignette + light flicker
        img += self.haze
        madd3(img, self.gain * np.float32(1.0 + 0.03 * math.sin(i * 0.7)), self.lift, img)
        np.multiply(img, self.vign, out=img)
        t = self._t("grade_haze_vignette", t)
        # 6) grain (shifted crop of a precomputed tile, luminance-weighted-ish)
        gy, gx = (i * 37) % 64, (i * 53) % 64
        g = self.grain[gy:gy + H, gx:gx + W]
        img += (g[..., None] * img)
        t = self._t("grain", t)
        # 7) linear 709 -> 2020 -> roll-off -> PQ -> uint16
        lin709_to_pq16_lut(img, self.out16, self.lut, REF_WHITE, KNEE, PEAK)
        t = self._t("pq_pack_numba", t)
        b = self.out16.tobytes()
        self._t("tobytes", t)
        return b


def heavy(src, n=4):
    cv2.setNumThreads(1)
    numba.set_num_threads(1)
    shot = HeavyShot(src)
    shot.frame(0)                     # warm (numba compile from cache, page-in)
    shot.timings = {}
    t = time.perf_counter()
    for i in range(1, n + 1):
        shot.frame(i)
    tot = (time.perf_counter() - t) / n
    res = {"init_s": round(shot.init_s, 2), "single_thread_s_per_frame": round(tot, 3),
           "stages_ms": {k: round(v / n * 1000, 1) for k, v in shot.timings.items()}}
    # same with all threads in one process
    cv2.setNumThreads(4)
    numba.set_num_threads(min(4, numba.config.NUMBA_NUM_THREADS))
    t = time.perf_counter()
    for i in range(1, n + 1):
        shot.frame(i)
    res["4_thread_one_process_s_per_frame"] = round((time.perf_counter() - t) / n, 3)
    print(json.dumps(res, indent=1))
    return res


# ----------------------------------------------------------------------------- pool / e2e

def _worker_init(src=None):
    global _SHOT
    cv2.setNumThreads(1)
    numba.set_num_threads(1)
    if src is not None:
        _SHOT = HeavyShot(src)
        _SHOT.frame(0)


_SHOT = None


def _pool_job(args):
    src, f0, f1 = args
    t = time.perf_counter()
    for i in range(f0, f1):
        _SHOT.frame(i)
    return time.perf_counter() - t


def pool(src, workers, frames):
    from multiprocessing import get_context
    jobs = [(src, k * frames, (k + 1) * frames) for k in range(workers)]
    with get_context("fork").Pool(workers, initializer=_worker_init, initargs=(src,)) as p:
        p.map(_pool_job, [(src, 0, 0)] * workers, chunksize=1)        # wait until all workers are up
        time.sleep(2)
        t = time.perf_counter()
        per = p.map(_pool_job, jobs, chunksize=1)
        wall = time.perf_counter() - t
    res = {"workers": workers, "frames_total": workers * frames, "wall_s": round(wall, 2),
           "frames_per_s": round(workers * frames / wall, 3),
           "worker_s_per_frame": [round(x / frames, 3) for x in per],
           "frames_per_hour_render_only": int(3600 * workers * frames / wall)}
    print(json.dumps(res, indent=1))
    return res


def x265_hdr_args(preset, crf, max_cll=1000, max_fall=400, extra=""):
    params = ("colorprim=bt2020:transfer=smpte2084:colormatrix=bt2020nc:range=limited:chromaloc=2:"
              f"master-display={MASTER_DISPLAY}:max-cll={max_cll},{max_fall}:hdr10=1:hdr10-opt=1:"
              f"repeat-headers=1:aq-mode=3:log-level=error{extra}")
    return ["-vf", ("zscale=pin=2020:tin=smpte2084:min=gbr:rin=full:p=2020:t=smpte2084:m=2020_ncl:"
                    "r=limited:c=topleft:d=error_diffusion,format=yuv420p10le"),
            "-c:v", "libx265", "-preset", preset, "-crf", str(crf), "-profile:v", "main10",
            "-x265-params", params, "-color_primaries", "bt2020", "-color_trc", "smpte2084",
            "-colorspace", "bt2020nc", "-color_range", "tv", "-chroma_sample_location", "topleft"]


def _e2e_job(args):
    src, k, f0, f1, path, preset, crf, xparams = args
    _worker_init()
    shot = HeavyShot(src)
    cmd = (["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb48le",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"] + x265_hdr_args(preset, crf, extra=xparams)
           + ["-g", str(FPS * 2), "-tag:v", "hvc1", str(path)])
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t = time.perf_counter()
    for i in range(f0, f1):
        p.stdin.write(shot.frame(i))
    p.stdin.close()
    rc = p.wait()
    return rc, time.perf_counter() - t


def e2e(src, workers, frames, preset, crf, out, xparams):
    from multiprocessing import get_context
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    segs = [out.parent / f"_seg{k:02d}.mp4" for k in range(workers)]
    b = np.linspace(0, frames, workers + 1).astype(int)
    jobs = [(src, k, int(b[k]), int(b[k + 1]), segs[k], preset, crf, xparams) for k in range(workers)]
    t = time.perf_counter()
    with get_context("spawn").Pool(workers) as p:
        r = p.map(_e2e_job, jobs, chunksize=1)
    lst = out.parent / "_segs.txt"
    lst.write_text("".join(f"file '{s}'\n" for s in segs))
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i",
                    str(lst), "-c", "copy", "-tag:v", "hvc1", "-movflags", "+faststart", str(out)], check=True)
    wall = time.perf_counter() - t
    for s in segs:
        s.unlink()
    lst.unlink()
    res = {"workers": workers, "frames": frames, "preset": preset, "crf": crf, "x265_extra": xparams,
           "wall_s_incl_init": round(wall, 2), "chunk_render+encode_s": [round(x[1], 1) for x in r],
           "returncodes": [x[0] for x in r], "s_per_frame_wall": round(wall / frames, 3),
           "frames_per_hour": int(3600 * frames / wall), "out": str(out)}
    print(json.dumps(res, indent=1))
    return res


def _render_one(i):
    return _SHOT.frame(i)


def e2e_single(src, workers, frames, preset, crf, out, xparams):
    """Topology B: N render workers (ordered imap) -> ONE x265 process. Lower RAM than N encoders."""
    from multiprocessing import get_context
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = (["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb48le",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"] + x265_hdr_args(preset, crf, extra=xparams)
           + ["-g", str(FPS * 2), "-tag:v", "hvc1", "-movflags", "+faststart", str(out)])
    t = time.perf_counter()
    with get_context("fork").Pool(workers, initializer=_worker_init, initargs=(src,)) as pool:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        # bounded in-flight window: plain imap has no back-pressure and would queue every
        # rendered 50 MB frame in RAM whenever the encoder is the bottleneck
        from collections import deque
        q, nxt, window = deque(), 0, workers * 2
        while nxt < frames or q:
            while nxt < frames and len(q) < window:
                q.append(pool.apply_async(_render_one, (nxt,)))
                nxt += 1
            p.stdin.write(q.popleft().get())
        p.stdin.close()
        rc = p.wait()
    wall = time.perf_counter() - t
    res = {"topology": "N renderers -> 1 encoder", "workers": workers, "frames": frames, "preset": preset,
           "crf": crf, "x265_extra": xparams, "wall_s_incl_init": round(wall, 2), "returncode": rc,
           "s_per_frame_wall": round(wall / frames, 3), "frames_per_hour": int(3600 * frames / wall),
           "out": str(out)}
    print(json.dumps(res, indent=1))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["micro", "heavy", "pool", "e2e", "e2e1"])
    ap.add_argument("--src", default=str(DEFAULT_SRC))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--crf", type=int, default=16)
    ap.add_argument("--x265-extra", default="", help="extra ':key=val' x265 params, e.g. ':pools=1:frame-threads=1'")
    ap.add_argument("--out", default=str(HERE / "out" / "e2e_heavy.mp4"))
    ap.add_argument("--json", default="")
    ap.add_argument("--threads1", action="store_true")
    a = ap.parse_args()
    if a.mode == "micro":
        r = micro()
    elif a.mode == "heavy":
        r = heavy(a.src)
    elif a.mode == "pool":
        r = pool(a.src, a.workers, a.frames)
    elif a.mode == "e2e1":
        r = e2e_single(a.src, a.workers, a.frames, a.preset, a.crf, a.out, a.x265_extra)
    else:
        r = e2e(a.src, a.workers, a.frames, a.preset, a.crf, a.out, a.x265_extra)
    if a.json:
        Path(a.json).write_text(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
