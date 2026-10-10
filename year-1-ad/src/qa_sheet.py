"""QA helper: render one shot function at several times into a contact sheet.

Usage (from src/):
  python qa_sheet.py scenes_b s_rome 63.0,66.5,68.8,72.5 rome.jpg
Writes build/qa/<name>. Each tile is 360x640 with its time stamped; frames go
through gfx.finish() so they match the final grade. Use this after every scene
edit, before committing to a full render.

For a rendered video, the equivalent is:
  ffmpeg -i video.mp4 -vf "fps=0.5,scale=180:320,tile=8x6" build/qa/sheet_%02d.jpg
"""
import importlib
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import gfx  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "build" / "qa"


def main():
    mod = importlib.import_module(sys.argv[1])
    fn = getattr(mod, sys.argv[2])
    times = [float(x) for x in sys.argv[3].split(",")]
    OUT.mkdir(parents=True, exist_ok=True)
    ims = []
    for t in times:
        t0 = time.time()
        img = gfx.finish(fn(t), int(t * gfx.FPS))
        print(f"t={t} {time.time() - t0:.2f}s", flush=True)
        im = (np.clip(img, 0, 1)[:, :, ::-1] * 255).astype(np.uint8)
        im = cv2.resize(im, (360, 640), interpolation=cv2.INTER_AREA)
        cv2.putText(im, f"{t:.1f}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        ims.append(im)
    while len(ims) % 4:
        ims.append(np.zeros_like(ims[0]))
    rows = [np.hstack(ims[i:i + 4]) for i in range(0, len(ims), 4)]
    cv2.imwrite(str(OUT / sys.argv[4]), np.vstack(rows))
    print("wrote", OUT / sys.argv[4])


if __name__ == "__main__":
    main()
