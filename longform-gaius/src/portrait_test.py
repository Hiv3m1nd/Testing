import sys, time
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import numpy as np, cv2
import portrait, hdr, sdf
W, H, name, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
t = time.time()
R, b = portrait.relief(name)
print("build", round(time.time() - t, 1), b["size"], "texel", b["texel"])
tc = np.array([1.0, 0.60, 0.30]); tc = tc / (0.2126 * tc[0] + 0.7152 * tc[1] + 0.0722 * tc[2])
cam = sdf.look_at((0.05, 0.02, -0.80), (-0.06, 0.01, 0.0), W * 1.6)
for k, lx in enumerate((-0.35, 0.05, 0.35)):
    lights = [(lx, 0.10, -0.40, *(tc * 0.10), 0.05, 1)]
    key = (0.6, 0.3, 0.75, 0.010, 0.016, 0.03)   # cool rim from behind-right
    t = time.time()
    img, dep, al = R.render(W, H, cam, lights, key=key, ambient=(0.002, 0.003, 0.005), mat=[0.10, 30, 0, 60, 0, 0.35, 1, 0.8], seed=k)
    print("render", round(time.time() - t, 2))
    cv2.imwrite(out.replace(".png", f"_{k}.png"), hdr.to_sdr8(img)[..., ::-1])
