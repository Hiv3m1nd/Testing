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
    m = loudnorm(Path(a.audio), norm)
    print("measured", m["input_i"], "LUFS ->", -14)
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
