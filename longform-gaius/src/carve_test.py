import sys, time
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import numpy as np, cv2
import carve, hdr, sdf
W, H, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
t = time.time()
b = carve.slab(3600, 1500, 2.4, [("GAIUS CAESAR", "cinzel", 330, 700, 820, 0.08),
                                ("THE HEIR WHO NEVER CAME HOME", "cinzel", 92, 600, 1080, 0.22)], gold=1.0)
R = carve.relief_object(b)
print("build", round(time.time() - t, 1))
tc = np.array([1.0, 0.62, 0.32]); tc = tc / (0.2126 * tc[0] + 0.7152 * tc[1] + 0.0722 * tc[2])
cam = sdf.look_at((0.25, -0.05, -2.3), (0, 0, 0), W * 1.0)
for k, lx in enumerate((-1.4, 0.0, 1.2)):
    lights = [(lx, 0.55, -0.55, *(tc * 0.9), 0.06, 1)]
    t = time.time()
    img, dep, al = R.render(W, H, cam, lights, key=(0, 0, 0, 0, 0, 0), ambient=(0.002, 0.0025, 0.0035),
                            mat=[0.03, 12, 3.0, 40, 0, 0.1, 1.0, 0.74], seed=k,
                            env=[0.03, 0.025, 0.02, 0.0, 0.0, 0.0, lx * 0.5, 0.5, -0.7, 2.5, 1.7, 0.8, 4.0])
    print("render", round(time.time() - t, 2))
    cv2.imwrite(out.replace(".png", f"_{k}.png"), hdr.to_sdr8(img)[..., ::-1])
