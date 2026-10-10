"""Loudness-normalise the mix and mux the final MP4.

Two-pass ffmpeg loudnorm to -14 LUFS integrated / -1 dBTP (the reference level
YouTube, Instagram and TikTok normalise to), then H.264 High + AAC-LC 48 kHz with
the moov atom up front for streaming.

Usage: python master.py VIDEO_IN OUT.mp4 [--crf 18] [--maxrate 16M]
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def loudnorm(src: Path, dst: Path, I=-14.0, TP=-1.0, LRA=11.0):
    first = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af",
                            f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", first, re.S).group(0))
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
          f"linear=true:print_format=summary")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-af", af, "-ar", "48000",
                    str(dst)], check=True)
    return m


def measure_i(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f",
                          "null", "-"], capture_output=True, text=True).stderr
    summ = out[out.rfind("Summary:"):]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1)), float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ).group(1))


def measure_tp(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
                          "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    summ = out[out.rfind("Summary:"):]
    i = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1))
    tp = float(re.search(r"True peak:\s+Peak:\s+(-?[\d.]+) dBFS", summ, re.S).group(1))
    return i, tp


def pre_limit(src: Path, dst: Path, target=-14.0):
    """Gain up to the target loudness, catching peaks with a look-ahead limiter (ceiling -2 dBFS)."""
    i, _ = measure_i(src)
    gain = target - i + 0.4
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-af",
                    f"volume={gain:.2f}dB,alimiter=limit=0.79:attack=4:release=60:level=false:latency=true",
                    "-c:a", "pcm_f32le", str(dst)], check=True)
    return gain


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--audio", default=str(ROOT / "build" / "mix_premaster.wav"))
    ap.add_argument("--crf", type=float, default=18)
    ap.add_argument("--maxrate", default="16M")
    ap.add_argument("--bitrate", default=None, help="two-pass target video bitrate instead of CRF")
    a = ap.parse_args()
    norm = ROOT / "build" / "mix_final.wav"
    limited = ROOT / "build" / "mix_limited.wav"
    g = pre_limit(Path(a.audio), limited)
    print(f"pre-gain {g:+.1f} dB through look-ahead limiter")
    i, _ = measure_i(limited)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(limited), "-af",
                    f"volume={-14.0 - i:.2f}dB", "-c:a", "pcm_f32le", str(norm)], check=True)
    i2, tp = measure_tp(norm)
    print(f"final {i2} LUFS, true peak {tp} dBTP")
    assert tp <= -1.0 and abs(i2 + 14) <= 0.3, "loudness/true-peak target missed"
    common = ["-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "slow", "-profile:v", "high",
              "-level", "4.2", "-pix_fmt", "yuv420p", "-r", "30", "-g", "60", "-c:a", "aac", "-b:a", "320k", "-ar",
              "48000", "-movflags", "+faststart", "-shortest"]
    if a.bitrate:
        for p in (1, 2):
            cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.video, "-i", str(norm), *common,
                   "-b:v", a.bitrate, "-maxrate", a.maxrate, "-bufsize", "20M", "-pass", str(p),
                   "-passlogfile", str(ROOT / "build" / "x264pass")]
            cmd += (["-an", "-f", "mp4", "/dev/null"] if p == 1 else [a.out])
            if p == 1:
                cmd = [c for c in cmd if c not in ("-map", "1:a:0")]
            subprocess.run(cmd, check=True)
    else:
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.video, "-i", str(norm), *common,
                        "-crf", str(a.crf), "-maxrate", a.maxrate, "-bufsize", "32M", a.out], check=True)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
