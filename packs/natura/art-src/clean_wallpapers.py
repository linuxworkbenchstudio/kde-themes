"""Natura wallpapers: take out the "NATURATECH ZEN" text, the dot grid and the line-and-square
mark (top right), and crop the Dark picture's light strip; both stay 3840 x 2160."""
import sys
import numpy as np, cv2
from PIL import Image


def terms(x, y, deg=3):
    return np.stack([x ** i * y ** j for i in range(deg + 1) for j in range(deg + 1 - i)], -1)


def clean(a, region, seed=7):
    x0, y0, x1, y1 = region
    reg = a[y0:y1, x0:x1].astype(float)
    grey = cv2.cvtColor(a[y0:y1, x0:x1], cv2.COLOR_RGB2GRAY)
    smooth = cv2.medianBlur(grey, 61).astype(float)
    marks = (np.abs(grey - smooth) > 5).astype(np.uint8)
    marks[-40:] = 0                    # the hills start just below: leave them alone
    marks = cv2.dilate(marks, np.ones((25, 25), np.uint8))
    yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0]
    nx, ny = xx / (x1 - x0), yy / (y1 - y0)
    keep = marks == 0
    T = terms(nx[keep], ny[keep])
    fit = np.empty_like(reg)
    resid = []
    for c in range(3):
        coef, *_ = np.linalg.lstsq(T, reg[..., c][keep], rcond=None)
        fit[..., c] = terms(nx, ny) @ coef
        resid.append(reg[..., c][keep] - (T @ coef))
    # the sky's own fine grain, sampled from clean pixels and shuffled into the filled area
    rng = np.random.default_rng(seed)
    grain = np.stack(resid, -1)
    grain = grain[rng.integers(0, len(grain), fit.shape[:2])]
    grain = cv2.GaussianBlur(grain.astype(np.float32), (3, 3), 0)
    fill = fit + np.clip(grain, -6, 6)
    # replace where the marks are, fading out over 30 px so no edge shows
    w = cv2.GaussianBlur(cv2.dilate(marks, np.ones((31, 31), np.uint8)).astype(np.float32), (61, 61), 0)
    taper = np.ones_like(w)
    ramp = np.linspace(0, 1, 30)
    taper[-30:] *= ramp[::-1, None]                       # fade out above the bottom of the area
    taper[:, :30] *= ramp[None, :]                        # and at its left side
    w = (w * taper)[..., None]
    out = reg * (1 - w) + fill * w
    a = a.copy()
    a[y0:y1, x0:x1] = np.clip(out + 0.5, 0, 255).astype(np.uint8)
    return a


src, out, which = sys.argv[1], sys.argv[2], sys.argv[3]
a = np.asarray(Image.open(src).convert("RGB"))
if which == "light":
    a = clean(a, (3120, 60, 3840, 880))
else:
    a = clean(a, (3190, 60, 3840, 880))
    a = a[14:14 + 2124, 64:64 + 3776]      # the light strip on the left (and the thin line along the top)
    a = cv2.resize(a, (3840, 2160), interpolation=cv2.INTER_LANCZOS4)
Image.fromarray(a).save(out, optimize=True)
