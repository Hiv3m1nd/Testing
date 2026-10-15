"""Master the audio, join the rendered segments and write the deliverables.

  python finalize.py --tag draft1                 # SDR draft with sound (build/out/<tag>_sdr.mp4)
  python finalize.py --tag master --hdr           # + HDR10 master, SDR fallback, phone preview, captions

Audio: look-ahead limiter, then an exact gain to -14 LUFS integrated, true peak <= -1 dBTP.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
OUT = BUILD / "out"
sys.path.insert(0, str(ROOT.parent / "year-1-ad" / "src"))
import master as m1  # noqa: E402  (pre_limit, measure_i, measure_tp from the 1 AD pipeline)

TITLE = "Gaius_Caesar_ColdOpen"


def master_audio():
    pre = BUILD / "mix_premaster.wav"
    limited = BUILD / "mix_limited.wav"
    final = BUILD / "mix_final.wav"
    g = m1.pre_limit(pre, limited)
    i, _ = m1.measure_i(limited)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(limited), "-af",
                    f"volume={-14.0 - i:.2f}dB", "-c:a", "pcm_f32le", str(final)], check=True)
    i2, tp = m1.measure_tp(final)
    print(f"audio: pre-gain {g:+.1f} dB, final {i2} LUFS, true peak {tp} dBTP")
    assert tp <= -1.0 and abs(i2 + 14) <= 0.3, "loudness/true-peak target missed"
    return final, i2, tp


def concat(tag, kind):
    segd = BUILD / "seg" / tag
    segs = sorted(segd.glob(f"{kind}_*.mp4"))
    lst = segd / f"{kind}_list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in segs))
    out = segd / f"{kind}_joined.mp4"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(out)], check=True)
    return out, len(segs)


def srt():
    tl = json.load(open(BUILD / "timeline.json"))

    def ts(t):
        h, r = divmod(t, 3600)
        mnt, s = divmod(r, 60)
        return f"{int(h):02d}:{int(mnt):02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}"

    def plain(s):
        return re.sub(r"\[([^\]]+)\]\(/[^)]*/\)", r"\1", s)

    cues = []
    for line in tl["lines"]:
        words = line["words"]
        text = plain(line["text"])
        # split long lines at punctuation into cues of <= ~84 characters (two lines of 42)
        chunks, cur = [], []
        for wd in text.split():
            cur.append(wd)
            if len(" ".join(cur)) > 60 and wd[-1] in ",:;." or len(" ".join(cur)) > 80:
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
        k = 0
        for ch in chunks:
            a = words[min(k, len(words) - 1)]["s"]
            k2 = min(k + len(ch), len(words)) - 1
            b = words[k2]["e"] + 0.25
            k += len(ch)
            s = " ".join(ch)
            if len(s) > 42:
                cut = s.rfind(" ", 0, len(s) // 2 + 8)
                s = s[:cut] + "\n" + s[cut + 1:]
            cues.append((a, b, s))
    out = OUT / "captions_en.srt"
    out.write_text("".join(f"{i + 1}\n{ts(a)} --> {ts(b)}\n{s}\n\n" for i, (a, b, s) in enumerate(cues)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="draft1")
    ap.add_argument("--hdr", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    audio, lufs, tp = master_audio()
    sdr, n = concat(a.tag, "sdr")
    print(f"joined {n} SDR segments")
    sdr_out = OUT / f"{TITLE}_{a.tag}_SDR.mp4"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(sdr), "-i", str(audio),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", str(sdr_out)], check=True)
    print("wrote", sdr_out)
    # phone preview under 30 MB: 1080p H.264 two-pass at a fixed bitrate
    prev = OUT / f"{TITLE}_{a.tag}_preview_1080p.mp4"
    common = ["-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264", "-preset", "slow", "-profile:v", "high",
              "-pix_fmt", "yuv420p", "-b:v", "4000k", "-maxrate", "6000k", "-bufsize", "8000k",
              "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
    for p in (1, 2):
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(sdr_out), *common, "-pass", str(p),
               "-passlogfile", str(BUILD / "x264prev")]
        cmd += (["-an", "-f", "mp4", "/dev/null"] if p == 1 else ["-c:a", "aac", "-b:a", "160k", "-movflags",
                                                                  "+faststart", str(prev)])
        subprocess.run(cmd, check=True)
    print("wrote", prev, prev.stat().st_size / 2 ** 20, "MiB")
    if a.hdr:
        hdr, n = concat(a.tag, "hdr")
        hdr_out = OUT / f"{TITLE}_4K_HDR10.mp4"
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(hdr), "-i", str(audio),
                        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-tag:v", "hvc1", "-c:a", "aac", "-b:a",
                        "320k", "-ar", "48000", "-movflags", "+faststart", "-shortest", str(hdr_out)], check=True)
        print("wrote", hdr_out, hdr_out.stat().st_size / 2 ** 20, "MiB")
    print("captions", srt())
    json.dump(dict(lufs=lufs, true_peak=tp), open(OUT / f"{a.tag}_audio.json", "w"))


if __name__ == "__main__":
    main()
