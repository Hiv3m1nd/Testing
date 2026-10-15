#!/usr/bin/env python3
"""HDR10 pipeline smoke test for the long-form film (3840x2160, 30 fps).

Renders a short synthetic scene in LINEAR light (BT.709 primaries, 1.0 = diffuse
white), with a flickering flame whose core peaks at 10x diffuse white over a dim
masonry wall, then produces:

  * <out>/hdr10_test.mp4      HEVC Main10, BT.2020 / SMPTE ST 2084 (PQ), HDR10 SEI
                              (mastering display P3-D65 1000 nit + MaxCLL/MaxFALL)
  * <out>/sdr_test.mp4        H.264 BT.709 preview, graded from the same linear frames
  * <out>/sdr_from_hdr.mp4    H.264 BT.709 made by ffmpeg zscale+tonemap from the HDR
                              file (checks the filter chain YouTube-style down-conversion)
  * <out>/stats.json          MaxCLL/MaxFALL pre-pass, timings, commands

HDR mapping (ITU-R BT.2408): scene 1.0 -> 203 cd/m2 (HDR reference white).
Highlights above a 500-nit knee roll off smoothly (C1 continuous) toward a
1000-nit peak, applied to max(R,G,B) so hue is preserved.

Usage:  python make_hdr_test.py [--frames 48] [--out DIR] [--preset medium] [--crf 16]
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

FPS = 30
REF_WHITE = 203.0      # cd/m2 for scene-linear 1.0 (BT.2408 HDR reference white)
PEAK = 1000.0          # mastering / target peak, cd/m2
KNEE = 500.0           # roll-off starts here, cd/m2

# Linear BT.709 RGB -> linear BT.2020 RGB (ITU-R BT.2087, same D65 white)
M709_TO_2020 = np.array([
    [0.627403895934699, 0.329283038377884, 0.043313065687417],
    [0.069097289358232, 0.919540395075459, 0.011362315566309],
    [0.016391438875150, 0.088013307877226, 0.895595253247624]], np.float32)

# SMPTE ST 2084 constants
PQ_M1 = 2610.0 / 16384.0
PQ_M2 = 2523.0 / 4096.0 * 128.0
PQ_C1 = 3424.0 / 4096.0
PQ_C2 = 2413.0 / 4096.0 * 32.0
PQ_C3 = 2392.0 / 4096.0 * 32.0

# HDR10 static metadata. Mastering display = P3-D65 primaries, 1000 / 0.0001 nit.
# x265 units: chromaticity in 0.00002, luminance in 0.0001 cd/m2.
MASTER_DISPLAY = "G(13250,34500)B(7500,3000)R(34000,16000)WP(15635,16450)L(10000000,1)"


# ----------------------------------------------------------------------------- colour

def pq_inverse_eotf(nits):
    """Absolute luminance (cd/m2) -> PQ signal in [0,1]. float32, in-place friendly."""
    y = np.clip(nits, 0.0, 10000.0) * np.float32(1.0 / 10000.0)
    ym = np.power(y, np.float32(PQ_M1), dtype=np.float32)
    num = np.float32(PQ_C1) + np.float32(PQ_C2) * ym
    den = np.float32(1.0) + np.float32(PQ_C3) * ym
    return np.power(num / den, np.float32(PQ_M2), dtype=np.float32)


def pq_eotf(e):
    """PQ signal [0,1] -> cd/m2 (used for verification)."""
    e = np.clip(np.asarray(e, np.float64), 0, 1)
    p = e ** (1 / PQ_M2)
    return 10000.0 * (np.maximum(p - PQ_C1, 0) / (PQ_C2 - PQ_C3 * p)) ** (1 / PQ_M1)


def rolloff(L, knee=KNEE, peak=PEAK):
    """Identity below knee; exponential shoulder above, slope 1 at knee, asymptote = peak."""
    span = peak - knee
    out = np.where(L > knee, knee + span * (1.0 - np.exp(-(L - knee) / span)), L)
    return out.astype(np.float32)


def scene_to_pq(lin709):
    """Scene-linear BT.709 (1.0 = diffuse white) -> PQ BT.2020 RGB float32 [0,1] + nits maxRGB."""
    h, w, _ = lin709.shape
    rgb2020 = cv2.transform(lin709, M709_TO_2020)          # per-pixel 3x3 matrix
    np.maximum(rgb2020, 0, out=rgb2020)
    nits = rgb2020 * np.float32(REF_WHITE)
    m = nits.max(axis=2)
    m_out = rolloff(m)
    scale = np.where(m > 1e-6, m_out / np.maximum(m, 1e-6), 1.0).astype(np.float32)
    nits *= scale[..., None]
    return pq_inverse_eotf(nits), m_out


def srgb_oetf(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055).astype(np.float32)


def scene_to_sdr(lin709):
    """SDR grade of the same scene: diffuse white -> ~0.79 linear, soft shoulder to 1.0,
    hot highlights desaturate toward white (mix of hue-preserving and per-channel curves)."""
    a = np.float32(0.85)
    k = np.float32(0.6)

    def f(v):
        return np.where(v > k, k + (1 - k) * (1 - np.exp(-(v - k) / (1 - k))), v).astype(np.float32)

    x = lin709 * a
    m = x.max(axis=2)
    hue = x * (f(m) / np.maximum(m, 1e-6))[..., None]
    per = f(x)
    out = hue * 0.45 + per * 0.55
    return srgb_oetf(out)


# ----------------------------------------------------------------------------- scene

def _noise(h, w, grid, seed):
    """Smooth value noise upsampled from a fixed grid (resolution independent)."""
    rng = np.random.default_rng(seed)
    g = rng.random((grid[1], grid[0])).astype(np.float32)
    return cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)


class Scene:
    """Procedural test scene; identical framing at any resolution."""

    def __init__(self, w, h, grain=0.012):
        self.w, self.h, self.grain = w, h, grain
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        self.u = xx / w            # 0..1
        self.v = yy / h            # 0..1
        # masonry albedo: ashlar courses with offset joints + multi-octave noise
        tex = (0.5 * _noise(h, w, (24, 14), 1) + 0.3 * _noise(h, w, (96, 54), 2)
               + 0.2 * _noise(h, w, (384, 216), 3))
        rows = 9
        ry = self.v * rows
        row_i = np.floor(ry)
        bx = self.u * 6 + (row_i % 2) * 0.5
        jy = np.abs(ry - np.round(ry)) * (h / rows)       # px distance to bed joint
        jx = np.abs(bx - np.round(bx)) * (w / 6)          # px distance to head joint
        joint = np.clip(np.minimum(jx, jy) / (0.004 * h), 0, 1)
        alb = (0.30 + 0.35 * tex) * (0.35 + 0.65 * joint)
        self.albedo = alb[..., None] * np.array([0.62, 0.55, 0.45], np.float32) / 0.62
        # dim stone gradient: darker top, faint cold ambient
        self.ambient = (0.015 + 0.05 * self.v)[..., None] * np.array([0.6, 0.7, 1.0], np.float32)
        self.fx, self.fy = 0.5, 0.70                     # flame base (normalised)
        d2 = ((self.u - self.fx) * w / h) ** 2 + (self.v - (self.fy - 0.12)) ** 2
        self.falloff = (1.0 / (1.0 + d2 / 0.02))[..., None]
        # grain tile (precomputed once, shifted per frame)
        rng = np.random.default_rng(7)
        self.grain_tile = rng.standard_normal((h, w)).astype(np.float32)
        # small-res grid for the flame field
        self.fh, self.fw = max(64, h // 4), max(64, w // 4)
        fy_, fx_ = np.mgrid[0:self.fh, 0:self.fw].astype(np.float32)
        self.fu = (fx_ / self.fw - self.fx) * (w / h)
        self.fv = (self.fy - fy_ / self.fh)              # height above flame base
        self.turb = [_noise(self.fh, self.fw, (16, 9), 10 + i) for i in range(3)]

    def flame(self, t):
        """Flame emission field (scene-linear, peak ~10.0 at the core)."""
        v = self.fv
        u = self.fu.copy()
        # turbulence: horizontal displacement grows with height, scrolls upward
        sh = int(t * 0.9 * self.fh) % self.fh
        tb = np.roll(self.turb[0], -sh, axis=0) - 0.5
        tb2 = np.roll(self.turb[1], -(2 * sh) % self.fh, axis=0) - 0.5
        u = u + (tb * 0.10 + tb2 * 0.04) * np.clip(v, 0, None) * 2.2
        width = 0.055 * np.clip(1.0 - v / 0.30, 0.0, 1.0) ** 0.8 + 1e-4
        body = np.exp(-(u / width) ** 2) * np.exp(-((v - 0.07) / 0.11) ** 2)
        body *= np.clip((v + 0.035) / 0.035, 0, 1)   # soft base
        flick = 1.0 + 0.10 * np.sin(2 * np.pi * 1.7 * t) + 0.05 * np.sin(2 * np.pi * 4.3 * t + 1.0)
        T = np.clip(body * flick, 0, 1.2)                    # "temperature"
        # blackbody-ish ramp (BT.709 linear), intensity ~ T^2.2, core peaks near 10
        c_hot = np.array([1.00, 0.93, 0.78], np.float32)
        c_mid = np.array([1.00, 0.52, 0.12], np.float32)
        c_cool = np.array([0.90, 0.16, 0.03], np.float32)
        a = np.clip((T - 0.55) / 0.45, 0, 1)[..., None]
        b = np.clip(T / 0.55, 0, 1)[..., None]
        col = c_cool * (1 - b) + c_mid * b
        col = col * (1 - a) + c_hot * a
        emis = col * (10.0 * np.clip(T, 0, 1) ** 2.2)[..., None]
        # glow halo (atmospheric scatter) done at low res
        glow = cv2.GaussianBlur(emis, (0, 0), self.fh * 0.05) * 0.35
        glow += cv2.GaussianBlur(emis, (0, 0), self.fh * 0.18) * 0.25
        out = emis + glow
        return cv2.resize(out, (self.w, self.h), interpolation=cv2.INTER_CUBIC), flick

    def frame(self, i):
        t = i / FPS
        emis, flick = self.flame(t)
        light = np.array([1.0, 0.55, 0.22], np.float32) * (1.6 * flick)
        img = self.albedo * (self.ambient + self.falloff * light)
        img += np.maximum(emis, 0)
        # embers: a few rising sparks at ~4x diffuse white
        rng = np.random.default_rng(100)
        for k in range(10):
            x0, sp, ph = rng.random(), 0.04 + 0.05 * rng.random(), rng.random()
            yy = self.fy - 0.08 - ((t * sp * 4 + ph) % 1.0) * 0.6
            xx = self.fx + (x0 - 0.5) * 0.12 + 0.02 * np.sin(6 * t + k)
            r = max(1.5, 0.0018 * self.h)
            cx, cy = int(xx * self.w), int(yy * self.h)
            x0_, x1_ = max(0, cx - int(4 * r)), min(self.w, cx + int(4 * r) + 1)
            y0_, y1_ = max(0, cy - int(4 * r)), min(self.h, cy + int(4 * r) + 1)
            if x1_ <= x0_ or y1_ <= y0_:
                continue
            gy, gx = np.mgrid[y0_:y1_, x0_:x1_].astype(np.float32)
            s = np.exp(-((gx - cx) ** 2 + (gy - cy) ** 2) / (2 * r * r))[..., None]
            img[y0_:y1_, x0_:x1_] += s * np.array([4.0, 2.2, 0.7], np.float32)
        # film grain (multiplicative, shifted tile so it moves frame to frame)
        if self.grain > 0:
            g = np.roll(self.grain_tile, ((i * 97) % self.h, (i * 211) % self.w), axis=(0, 1))
            img *= (1.0 + self.grain * g)[..., None]
        # reference patches (bottom-left, grain-free): scene-linear neutral steps
        self.patches = [0.01, 0.05, 0.18, 0.5, 1.0, 2.0, 4.0, 10.0]
        for x0, y0, ps, val in self._patch_rects():
            img[y0:y0 + ps, x0:x0 + ps] = val
        return img.astype(np.float32)

    def _patch_rects(self):
        ps = int(0.05 * self.h)
        y0 = self.h - int(0.04 * self.h) - ps
        return [(int(0.03 * self.w) + j * int(ps * 1.15), y0, ps, v) for j, v in enumerate(self.patches)]

    def patch_centers(self):
        return [(x0 + ps // 2, y0 + ps // 2, v) for x0, y0, ps, v in self._patch_rects()]


# ----------------------------------------------------------------------------- encode

def hdr_cmd(w, h, out, max_cll, max_fall, preset, crf):
    x265 = ":".join([
        "colorprim=bt2020", "transfer=smpte2084", "colormatrix=bt2020nc", "range=limited",
        "chromaloc=2", f"master-display={MASTER_DISPLAY}", f"max-cll={max_cll},{max_fall}",
        "hdr10=1", "hdr10-opt=1", "repeat-headers=1", "aq-mode=3", "log-level=error",
    ])
    return [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb48le", "-s", f"{w}x{h}", "-r", str(FPS),
        "-color_primaries", "bt2020", "-color_trc", "smpte2084", "-colorspace", "rgb", "-color_range", "pc",
        "-i", "-",
        "-vf", ("zscale=pin=2020:tin=smpte2084:min=gbr:rin=full:"
                "p=2020:t=smpte2084:m=2020_ncl:r=limited:c=topleft:d=error_diffusion,"
                "format=yuv420p10le"),
        "-c:v", "libx265", "-preset", preset, "-crf", str(crf), "-profile:v", "main10",
        "-x265-params", x265,
        "-color_primaries", "bt2020", "-color_trc", "smpte2084", "-colorspace", "bt2020nc",
        "-color_range", "tv", "-chroma_sample_location", "topleft",
        "-g", str(FPS * 2), "-tag:v", "hvc1", "-movflags", "+faststart", str(out)]


def sdr_cmd(w, h, out):
    return [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS),
        "-color_primaries", "bt709", "-color_trc", "iec61966-2-1", "-colorspace", "rgb", "-i", "-",
        "-vf", "zscale=min=gbr:rin=full:m=709:r=limited:c=left,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
        "-g", str(FPS * 2), "-movflags", "+faststart", str(out)]


def tonemap_cmd(src, out):
    # HDR10 -> SDR BT.709 via zimg + ffmpeg tonemap (CPU). npl=203 makes 1.0 = HDR ref white.
    return [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
        "-vf", ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,"
                "tonemap=tonemap=hable:desat=0:peak=4.93,"
                "zscale=t=bt709:m=bt709:r=limited,format=yuv420p"),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
        str(out)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=48)
    ap.add_argument("--w", type=int, default=3840)
    ap.add_argument("--h", type=int, default=2160)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "out"))
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--crf", type=int, default=16)
    ap.add_argument("--grain", type=float, default=0.012)
    ap.add_argument("--dump-raw", default="", help="also write raw rgb48le PQ frames here (encoder benchmarks)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stats = {"frames": a.frames, "size": [a.w, a.h], "fps": FPS}

    # ---- pre-pass at 1/4 res: MaxCLL / MaxFALL must be known before x265 starts
    t0 = time.time()
    small = Scene(a.w // 4, a.h // 4, grain=0.0)
    cll, fall = 0.0, 0.0
    for i in range(a.frames):
        _, m = scene_to_pq(small.frame(i))
        cll = max(cll, float(m.max()))
        fall = max(fall, float(m.mean()))
    max_cll, max_fall = int(np.ceil(min(cll * 1.02, PEAK))), int(np.ceil(fall * 1.05))
    stats["prepass"] = {"seconds": round(time.time() - t0, 2), "maxcll_est": cll, "maxfall_est": fall,
                        "signalled_max_cll": max_cll, "signalled_max_fall": max_fall}
    print(f"pre-pass: MaxCLL~{cll:.0f}  MaxFALL~{fall:.1f}  -> max-cll={max_cll},{max_fall}", flush=True)

    # ---- full-res render, piped to two encoders
    t0 = time.time()
    scene = Scene(a.w, a.h, grain=a.grain)
    stats["scene_init_s"] = round(time.time() - t0, 2)
    hdr_path, sdr_path = out / "hdr10_test.mp4", out / "sdr_test.mp4"
    hc, sc = hdr_cmd(a.w, a.h, hdr_path, max_cll, max_fall, a.preset, a.crf), sdr_cmd(a.w, a.h, sdr_path)
    stats["hdr_cmd"] = shlex.join(hc)
    stats["sdr_cmd"] = shlex.join(sc)
    ph = subprocess.Popen(hc, stdin=subprocess.PIPE)
    ps = subprocess.Popen(sc, stdin=subprocess.PIPE)
    raw = open(a.dump_raw, "wb") if a.dump_raw else None
    t_scene = t_conv = t_io = 0.0
    real_cll, real_fall = 0.0, 0.0
    t_all = time.time()
    for i in range(a.frames):
        t1 = time.time()
        lin = scene.frame(i)
        t2 = time.time()
        pq, m = scene_to_pq(lin)
        real_cll, real_fall = max(real_cll, float(m.max())), max(real_fall, float(m.mean()))
        buf16 = (pq * np.float32(65535.0) + np.float32(0.5)).astype(np.uint16)
        sdr8 = (scene_to_sdr(lin) * np.float32(255.0) + np.float32(0.5)).astype(np.uint8)
        t3 = time.time()
        b = buf16.tobytes()
        ph.stdin.write(b)
        ps.stdin.write(sdr8.tobytes())
        if raw:
            raw.write(b)
        t4 = time.time()
        t_scene += t2 - t1
        t_conv += t3 - t2
        t_io += t4 - t3
        if i in (0, a.frames // 2):
            cv2.imwrite(str(out / f"still_sdr_{i:03d}.png"), cv2.cvtColor(sdr8, cv2.COLOR_RGB2BGR))
        if i % 8 == 0:
            print(f"frame {i}/{a.frames}  {time.time() - t_all:.1f}s", flush=True)
    for p in (ph, ps):
        p.stdin.close()
    if raw:
        raw.close()
    t_wait = time.time()
    rc = [ph.wait(), ps.wait()]
    stats["render"] = {
        "wall_s": round(time.time() - t_all, 2), "encoder_drain_s": round(time.time() - t_wait, 2),
        "scene_s_per_frame": round(t_scene / a.frames, 3), "convert_s_per_frame": round(t_conv / a.frames, 3),
        "pipe_write_s_per_frame": round(t_io / a.frames, 3), "returncodes": rc,
        "actual_maxcll": real_cll, "actual_maxfall": real_fall}
    print(json.dumps(stats["render"], indent=1), flush=True)
    if any(rc):
        sys.exit("encoder failed")

    # ---- SDR down-conversion of the HDR master by ffmpeg (filter-chain check)
    t0 = time.time()
    tc = tonemap_cmd(hdr_path, out / "sdr_from_hdr.mp4")
    stats["tonemap_cmd"] = shlex.join(tc)
    subprocess.run(tc, check=True)
    stats["tonemap_s"] = round(time.time() - t0, 2)
    stats["patch_centers"] = scene.patch_centers()
    (out / "stats.json").write_text(json.dumps(stats, indent=1))
    print("done", out)


if __name__ == "__main__":
    main()
