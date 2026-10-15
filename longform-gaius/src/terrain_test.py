import sys, time
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import numpy as np, cv2
import terrain_night as TN, hdr, sdf
W, H, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
T = TN.Terrain()
md = np.array([0.35, 0.42, -0.84]); md /= np.linalg.norm(md)
moon = np.array([*md, 0.24, 0.29, 0.42])
glow = np.array([0.0, 30.0, 0.0, 6.0, 3.2, 1.2, 0.0012])
for k, (pos, tgt) in enumerate((((-2500, 3400, -15000), (0, 300, 1000)), ((-1500, 2300, -7500), (0, 150, 0)))):
    cam = sdf.look_at(pos, tgt, W * 0.85)
    t = time.time()
    img, dep = T.render(W, H, cam, moon, glow, k)
    print("render", k, round(time.time() - t, 2))
    cv2.imwrite(out.replace(".png", f"_{k}.png"), hdr.to_sdr8(img)[..., ::-1])
