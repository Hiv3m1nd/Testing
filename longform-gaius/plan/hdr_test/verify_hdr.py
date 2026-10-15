#!/usr/bin/env python3
"""Verify an HDR10 master (and optional SDR files) produced by make_hdr_test.py.

Checks: stream colour tags, Main10 / yuv420p10le, HDR10 SEI side data on every
keyframe, clean full decode (frame count, no errors), and round-trip luminance of
the neutral reference patches (decode -> RGB PQ -> cd/m2) against the intended
mapping (scene 1.0 -> 203 nit, roll-off to 1000 nit).

Usage: python verify_hdr.py OUT_DIR
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_hdr_test import REF_WHITE, pq_eotf, rolloff  # noqa: E402


def probe(path, *args):
    r = subprocess.run(["ffprobe", "-v", "error", *args, "-of", "json", str(path)],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def full_decode(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-map", "0:v:0",
                        "-f", "null", "-"], capture_output=True, text=True)
    n = int(probe(path, "-count_frames", "-select_streams", "v:0",
                  "-show_entries", "stream=nb_read_frames")["streams"][0]["nb_read_frames"])
    return r.returncode == 0 and not r.stderr.strip(), n, r.stderr.strip()


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent / "out")
    stats = json.loads((out / "stats.json").read_text())
    W, H = stats["size"]
    hdr = out / "hdr10_test.mp4"
    res = {"ok": True, "checks": {}}

    def check(name, cond, info=None):
        res["checks"][name] = {"pass": bool(cond), "info": info}
        res["ok"] &= bool(cond)

    s = probe(hdr, "-select_streams", "v:0", "-show_entries", "stream")["streams"][0]
    want = {"codec_name": "hevc", "profile": "Main 10", "pix_fmt": "yuv420p10le", "color_range": "tv",
            "color_space": "bt2020nc", "color_transfer": "smpte2084", "color_primaries": "bt2020",
            "width": W, "height": H}
    got = {k: s.get(k) for k in want}
    check("stream_tags", got == want, got)

    fr = probe(hdr, "-select_streams", "v:0", "-show_entries",
               "frame=key_frame,pict_type:frame_side_data")["frames"]
    keys = [f for f in fr if f.get("key_frame") == 1]
    sd_ok = []
    for f in keys:
        types = {d.get("side_data_type") for d in f.get("side_data_list", [])}
        sd_ok.append({"Mastering display metadata", "Content light level metadata"} <= types)
    md = next(d for d in keys[0]["side_data_list"] if d["side_data_type"] == "Mastering display metadata")
    cl = next(d for d in keys[0]["side_data_list"] if d["side_data_type"] == "Content light level metadata")
    check("hdr10_sei_on_every_keyframe", all(sd_ok) and len(keys) > 0,
          {"keyframes": len(keys), "mastering": {k: md[k] for k in md if k != "side_data_type"},
           "cll": {"max_content": cl["max_content"], "max_average": cl["max_average"]}})

    ok, n, err = full_decode(hdr)
    check("hdr_decodes_cleanly", ok and n == stats["frames"], {"frames": n, "stderr": err[:400]})
    for name in ("sdr_test.mp4", "sdr_from_hdr.mp4"):
        p = out / name
        if p.exists():
            ok, n, err = full_decode(p)
            ss = probe(p, "-select_streams", "v:0", "-show_entries",
                       "stream=codec_name,pix_fmt,color_space,color_transfer,color_primaries")["streams"][0]
            check(f"{name}_decodes_cleanly", ok and n == stats["frames"]
                  and ss["color_transfer"] == "bt709", {"frames": n, **ss})

    # round-trip patch luminance: decode middle frame back to full-range 16-bit RGB (still PQ / BT.2020)
    mid = stats["frames"] // 2
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(hdr), "-vf",
         f"select=eq(n\\,{mid}),zscale=min=2020_ncl:rin=limited:m=gbr:r=full:"
         "pin=2020:tin=smpte2084:p=2020:t=smpte2084,format=gbrp16le",
         "-frames:v", "1", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    g, b, r_ = np.frombuffer(raw, np.uint16).reshape(3, H, W)          # planar G,B,R
    img = np.stack([r_, g, b], axis=-1).astype(np.float64) / 65535.0
    rows = []
    worst = 0.0
    r = max(2, int(0.01 * H))
    for cx, cy, val in stats["patch_centers"]:
        e = img[cy - r:cy + r, cx - r:cx + r].mean(axis=(0, 1))
        nits = pq_eotf(e)
        target = float(rolloff(np.float32(val * REF_WHITE)))
        err = abs(nits.mean() - target) / max(target, 1e-3)
        worst = max(worst, err if target > 1 else 0.0)
        rows.append({"scene": val, "target_nits": round(target, 2), "decoded_nits": round(float(nits.mean()), 2),
                     "pq_code10": round(float(e.mean() * 1023), 1)})
    check("patch_luminance_roundtrip_within_3pct", worst < 0.03, rows)
    print(json.dumps(res, indent=1))
    (out / "verify.json").write_text(json.dumps(res, indent=1))
    sys.exit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main()
