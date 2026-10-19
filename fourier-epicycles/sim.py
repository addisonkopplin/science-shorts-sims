"""How many epicycles does a drawing need? Complex DFT of a closed path; keep the K biggest circles
(sorted by radius, as epicycle animations do) and measure the worst-case distance between the
reconstruction and the true path, as a % of the drawing's width.
Paths: (1) the classic heart curve (a trig polynomial, so exact with few circles);
(2) a five-pointed star (polygon with sharp corners); (3) THE SHORT'S DRAWING: the cat silhouette from
cat_path.py (cat_path.npy, 4,096 points uniform by arc length). Run: python3 cat_path.py && python3 sim.py"""
import numpy as np

M = 4096  # samples along the path (uniform in parameter / arc length)
t = np.arange(M) / M * 2 * np.pi

heart = 16 * np.sin(t)**3 + 1j * (13*np.cos(t) - 5*np.cos(2*t) - 2*np.cos(3*t) - np.cos(4*t))

def polygon(verts, M):
    verts = np.asarray(verts); segs = np.roll(verts, -1) - verts
    L = np.abs(segs); s = np.arange(M) / M * L.sum(); cum = np.concatenate([[0], np.cumsum(L)])
    k = np.searchsorted(cum, s, side="right") - 1
    return verts[k] + segs[k] * (s - cum[k]) / L[k]

ang = np.pi/2 + np.arange(10) * np.pi / 5
r = np.where(np.arange(10) % 2 == 0, 1.0, 0.382)
star = polygon(r * np.exp(1j * ang), M)

def report(name, z):
    c = np.fft.fft(z) / M
    order = np.argsort(-np.abs(c))
    width = np.ptp(z.real)
    nonzero = int((np.abs(c) > 1e-9 * np.abs(c).max()).sum())
    out = []
    for K in (1, 2, 3, 5, 10, 20, 30, 50, 100, 200, 500):
        keep = np.zeros_like(c); keep[order[:K]] = c[order[:K]]
        err = np.abs(np.fft.ifft(keep) * M - z).max() / width
        out.append((K, err))
    print(f"{name}: non-zero circles = {nonzero} (of {M})")
    for K, e in out:
        print(f"   {K:4d} circles: worst error = {e:.2%} of width")
    for thr in (0.10, 0.05, 0.02, 0.01, 0.005):
        for K in range(1, M + 1):
            keep = np.zeros_like(c); keep[order[:K]] = c[order[:K]]
            if np.abs(np.fft.ifft(keep) * M - z).max() / width < thr:
                print(f"   fewest circles for worst error < {thr:.1%}: {K}"); break

report("heart curve", heart)
report("five-pointed star", star)

cat = np.load("cat_path.npy")
report("cat silhouette (the Short's drawing)", cat)
c = np.fft.fft(cat) / M; order = np.argsort(-np.abs(c))
print(f"cat: biggest circle radius = {np.abs(c[order[0]]):.2f}, 20th = {np.abs(c[order[19]]):.3f}, "
      f"100th = {np.abs(c[order[99]]):.4f} (units: drawing width = {np.ptp(cat.real):.1f})")
print("cat: speeds (turns per loop) of the 10 biggest circles:",
      [int(k if k < M//2 else k - M) for k in order[:10]])
try:
    from PIL import Image, ImageDraw
    Ks = (3, 5, 10, 20, 50, 100); W = 300
    sheet = Image.new("L", (W * len(Ks), W + 30), 0); d = ImageDraw.Draw(sheet)
    lo = min(cat.real.min(), cat.imag.min()); sc = (W - 40) / max(np.ptp(cat.real), np.ptp(cat.imag))
    for n, K in enumerate(Ks):
        keep = np.zeros_like(c); keep[order[:K]] = c[order[:K]]; r = np.fft.ifft(keep) * M
        pts = [(n*W + 20 + (p.real - cat.real.min())*sc, W - 20 - (p.imag - cat.imag.min())*sc) for p in r]
        d.line(pts + [pts[0]], fill=255, width=2); d.text((n*W + 10, W + 8), f"{K} circles", fill=255)
    sheet.save("cat_circles.png"); print("contact sheet: cat_circles.png", Ks)
except ImportError:
    pass

# --- added after writers' room r1 -------------------------------------------------------------
print("\n# r1 checks (cat)")
W = np.ptp(cat.real)
def recon(K):
    keep = np.zeros_like(c); keep[order[:K]] = c[order[:K]]; return np.fft.ifft(keep) * M
def hausdorff(a, b):
    def directed(p, q):
        best = np.full(len(p), np.inf)
        for s in range(0, len(q), 512):
            best = np.minimum(best, np.abs(p[:, None] - q[None, s:s+512]).min(axis=1))
        return best.max()
    return max(directed(a, b), directed(b, a))
print(f"k=0 (centre) coefficient |c0| = {abs(c[0]):.2e} (path is mean-centred, so no non-spinning term in the chain)")
for K in (3, 10, 20, 50, 100):
    r = recon(K)
    print(f"  {K:4d} circles: timing-matched worst gap {np.abs(r - cat).max()/W:.2%}, shape gap (Hausdorff) {hausdorff(r, cat)/W:.2%}, "
          f"RMS gap {np.sqrt(np.mean(np.abs(r - cat)**2))/W:.3%}")
# greedy-by-radius vs the K lowest speeds (|k| small): mean-square error comparison (Parseval says biggest-first is best in RMS)
ks = np.fft.fftfreq(M, 1/M).astype(int)
for K in (20, 100):
    low = np.argsort(np.abs(ks) + 1e-6*np.arange(M))[:K]; keep = np.zeros_like(c); keep[low] = c[low]
    rl = np.fft.ifft(keep) * M
    print(f"  {K} lowest speeds: RMS {np.sqrt(np.mean(np.abs(rl-cat)**2))/W:.3%}, worst {np.abs(rl-cat).max()/W:.2%}; "
          f"top-{K}-by-radius max speed |k| = {np.abs(ks[order[:K]]).max()}")
# decay of the coefficients: largest |c_k| in speed bands
for lo_, hi_ in ((1, 10), (11, 30), (31, 100), (101, 300), (301, 1000)):
    band = (np.abs(ks) >= lo_) & (np.abs(ks) <= hi_)
    print(f"  speeds {lo_:4d}-{hi_:4d}: biggest radius {np.abs(c[band]).max():.4f}")
sel = (np.abs(ks) >= 10) & (np.abs(ks) <= 500)
kk = np.abs(ks[sel]); cc = np.abs(c[sel])
# fit the upper envelope: max |c| in log-spaced bins
bins = np.unique(np.logspace(1, np.log10(500), 15).astype(int)); xs = []; ys = []
for a, b in zip(bins[:-1], bins[1:]):
    m = (kk >= a) & (kk < b)
    if m.any(): xs.append(np.log((a+b)/2)); ys.append(np.log(cc[m].max()))
slope = np.polyfit(xs, ys, 1)[0]
print(f"  envelope of |c_k| for speeds 10-500 falls like k^{slope:.2f} (corner-type decay is k^-2)")
# ear tips: how close does the redrawn curve get to the true tip point? (rounded tips shrink but never vanish)
tips = {"ear 1": int(0.559 * M), "ear 2": int(0.697 * M)}
for name, i0 in tips.items():
    # refine: true tip = sharpest turn near i0
    seg = np.arange(i0 - 40, i0 + 40) % M
    d1 = np.roll(cat, -1)[seg] - cat[seg]; d0 = cat[seg] - np.roll(cat, 1)[seg]
    turn = np.abs(np.angle(d1 / d0)); it = seg[np.argmax(turn)]
    row = []
    for K in (20, 50, 100, 500):
        r = recon(K); row.append(f"{K}: {np.abs(r - cat[it]).min()/W:.2%}")
    print(f"  {name} tip (index {it}, turn {np.degrees(turn.max()):.0f} deg per step): closest approach of the redrawn curve " + ", ".join(row))
# are small circles 'local'? displacement added by circles 21-100 along the whole loop
add = recon(100) - recon(20); mag = np.abs(add) / W
ear_idx = np.r_[int(0.559*M)-60:int(0.559*M)+60, int(0.697*M)-60:int(0.697*M)+60]
print(f"  circles 21-100 move the pen by median {np.median(mag):.2%} of width along the whole loop, max {mag.max():.2%}; "
      f"median near the ears {np.median(mag[ear_idx]):.2%} (they act everywhere; at the ears many line up)")
try:
    from PIL import Image, ImageDraw
    Ks = (10, 20, 50, 100, 500); Z = 260; sheet = Image.new("L", (Z*len(Ks), Z+24), 0)
    e1, e2 = cat[int(0.559*M)], cat[int(0.697*M)]; ctr = (e1 + e2) / 2; half = 0.75 * abs(e1 - e2)
    for n, K in enumerate(Ks):
        r = recon(K); tile = Image.new("L", (Z, Z), 0); dt = ImageDraw.Draw(tile)
        px = lambda p: ((p.real - ctr.real + half)/(2*half)*Z, Z*0.35 - (p.imag - ctr.imag)/(2*half)*Z)
        dt.line([px(p) for p in cat] + [px(cat[0])], fill=90, width=1)
        dt.line([px(p) for p in r] + [px(r[0])], fill=255, width=2)
        sheet.paste(tile, (n*Z, 0)); ImageDraw.Draw(sheet).text((n*Z + 8, Z + 6), f"{K} circles", fill=255)
    sheet.save("ears_zoom.png"); print("  ears zoom sheet: ears_zoom.png", Ks)
except ImportError:
    pass
