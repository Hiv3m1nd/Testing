import sys, time, math
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import numpy as np, cv2
import coin, hdr, sdf
W, H, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
t = time.time()
tc = np.array([1.0, 0.70, 0.45]); tc = tc / (0.2126 * tc[0] + 0.7152 * tc[1] + 0.0722 * tc[2])
for k, yaw in enumerate((-0.5, -0.15, 0.25)):
    R = coin.relief_object(yaw=yaw, pitch=0.10)
    if k == 0: print("build", round(time.time() - t, 1))
    cam = sdf.look_at((0.004, 0.003, -0.055), (0, 0, 0), W * 1.3)
    lights = [(-0.05 + 0.05 * k, 0.04, -0.05, *(tc * 0.0045), 0.004, 1)]
    t = time.time()
    img, dep, al = R.render(W, H, cam, lights, key=(0.5, 0.6, 0.6, 0.02, 0.03, 0.05), ambient=(0.004, 0.005, 0.007),
                            mat=[0.0, 30, 1.6, 120, 0, 0.0, 0.92, 0.95], seed=k,
                            env=[0.05, 0.06, 0.08, 0.004, 0.004, 0.005, -0.4, 0.7, -0.6, 0.6, 0.7, 0.85, 12.0])
    print("render", round(time.time() - t, 2))
    cv2.imwrite(out.replace(".png", f"_{k}.png"), hdr.to_sdr8(img)[..., ::-1])
