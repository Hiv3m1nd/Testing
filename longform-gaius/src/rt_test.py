import sys, time
import numpy as np
import cv2
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import rt, scene_ruins

W, H = int(sys.argv[1]), int(sys.argv[2])
boxes, cyls = scene_ruins.layout()
panels = np.zeros((2, 256, 512), np.float32)
yy, xx = np.mgrid[0:256, 0:512] / 256.0
panels[0] = 0.5 + 0.5 * np.sin(xx * 20) * np.sin(yy * 10)
panels[1] = 0.5
tc = rt.torch_color(1850) * 60.0
torch = np.array([0.6, 1.7, 2.0, *tc, 0.12, 0.004])
moon = np.array([*(np.array([-0.4, 0.55, 0.75]) / np.linalg.norm([-0.4, 0.55, 0.75])), 0.035, 0.045, 0.075])
sky = np.array([0.010, 0.016, 0.034, 0.020, 0.026, 0.045])
fog = np.array([0.02, 0.6])
cam = rt.look_at((0.3, 1.5, -3.0), (0.0, 1.2, 10.0), W * 0.9)
t = time.time()
img, dep = rt.render(W, H, cam, boxes, cyls, rt.MATS if hasattr(rt, 'MATS') else scene_ruins.MATS, panels, torch, moon, sky, fog, 1)
print("first (compile+render)", time.time() - t)
t = time.time()
img, dep = rt.render(W, H, cam, boxes, cyls, scene_ruins.MATS, panels, torch, moon, sky, fog, 2)
print("render", time.time() - t)
x = img / (1 + img)  # reinhard preview
x = np.clip(x, 0, 1) ** (1 / 2.2)
cv2.imwrite(sys.argv[3], (x[..., ::-1] * 255).astype(np.uint8))
