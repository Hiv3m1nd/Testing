import sys, time
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import numpy as np, cv2
import sdf, hdr, scene_limyra as S
W, H, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
h = float(sys.argv[4]) if len(sys.argv) > 4 else 0.02
t = time.time(); B = S.baked(h); print("bake", round(time.time() - t, 1), "s", B.dist.shape, B.dist.nbytes / 1e6, "MB")
panels = S.relief_panels()
tc = np.array([1.0, 0.50, 0.19]); tc = tc / (0.2126 * tc[0] + 0.7152 * tc[1] + 0.0722 * tc[2])
torch = np.array([-0.9, 1.6, 6.5, *(tc * 5.0), 0.05, 0.0006, 0.035])
md = np.array([-0.55, 0.45, 0.70]); md /= np.linalg.norm(md)
moon = np.array([*md, 0.016, 0.024, 0.042])
sky = np.array([0.0025, 0.0040, 0.0080, 0.010, 0.013, 0.022])
fog = np.array([0.03, 0.6, -0.012])
cam = sdf.look_at((0.6, 1.25, -2.4), (-0.3, 1.25, 12.0), W * 0.95)
jit = np.array([0.0, 0.0, 1.0])
for f in range(2):
    t = time.time()
    img, dep = sdf.render(W, H, cam, B.dist, B.pid, B.coarse, B.G, B.gh, B.GH, B.prims, S.MATS, panels, torch, moon, sky, fog, f, jit)
    print("render", f, round(time.time() - t, 2))
np.save(out.replace(".png", ".npy"), img)
cv2.imwrite(out, hdr.to_sdr8(img)[..., ::-1])
