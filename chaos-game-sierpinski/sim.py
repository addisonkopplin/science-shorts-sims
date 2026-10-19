"""Chaos game on a triangle -> Sierpinski triangle, with convergence measurements.
Coordinates: affine triangle with corners (0,0), (1,0), (0,1); any triangle is an affine image of it,
and the jump-halfway rule commutes with affine maps, so counts are the same for an equilateral triangle.
A level-k cell is the sub-triangle with grid index (i, j) = floor(2^k * (x, y)) where i & j == 0
and i + j < 2^k (there are 3^k of them; their union is the level-k Sierpinski approximation).
Run: python3 sim.py"""
import numpy as np, math

SEED = 20261019
rng = np.random.default_rng(SEED)
V = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
N = 200_000
p = np.array([0.0, 0.0])  # r1: start ON a corner, which is on the pattern, so every dot is on it (r0 started at (0.3,0.3), inside the centre hole)
pts = np.empty((N, 2)); corners = rng.integers(0, 3, N)
for n in range(N):
    p = (p + V[corners[n]]) / 2.0
    pts[n] = p

def in_level(pt, k):
    i = np.floor(pt[:, 0] * 2**k).astype(np.int64); j = np.floor(pt[:, 1] * 2**k).astype(np.int64)
    i = np.minimum(i, 2**k - 1); j = np.minimum(j, 2**k - 1)
    return (i & j) == 0, i, j

print(f"seed={SEED}, points={N:,}, start=corner (0,0)")
# 1) every point after the k-th jump is inside the level-k pattern
for k in (1, 5, 10, 20):
    ok, _, _ = in_level(pts, k)
    print(f"level {k}: share of ALL {N:,} dots (from the very first) inside the level-{k} pattern: {ok.mean():.6f}")
# distance from attractor halves each jump: start error bound
print("(a start OFF the pattern would only get within 2^-k of it after k jumps; from a corner it never leaves)")

# 2) coverage of level-k cells versus number of points (ignoring the first 20 jumps)
for k in (6, 7):
    ok, i, j = in_level(pts, k)
    cells = 3**k; seen = set(); marks = {}
    for n, (a, b) in enumerate(zip(i, j), start=1):
        seen.add((a, b))
        for frac in (0.5, 0.9, 0.99, 1.0):
            if frac not in marks and len(seen) >= math.ceil(frac * cells):
                marks[frac] = n
        if len(seen) == cells: break
    print(f"level {k} ({cells} cells): points to cover 50%={marks[0.5]:,}, 90%={marks[0.9]:,}, "
          f"99%={marks[0.99]:,}, 100%={marks.get(1.0)}")

# 3) area left and dimension
for k in (1, 5, 10, 20):
    print(f"after {k} removal steps, area left = (3/4)^{k} = {0.75**k:.6f}")
print(f"similarity dimension = log 3 / log 2 = {math.log(3)/math.log(2):.4f}")

# 4) save a preview to check the picture
try:
    import PIL.Image as Image
    img = np.zeros((600, 600), np.uint8)
    for n_show, name in ((1000, "1k"), (10000, "10k"), (50000, "50k")):
        img[:] = 0
        q = pts[:n_show]
        x = (q[:, 0] + 0.5 * q[:, 1]); y = q[:, 1] * math.sqrt(3) / 2  # to equilateral
        img[(599 - y * 599).astype(int), (x * 599).astype(int)] = 255
        Image.fromarray(img).save(f"preview_{name}.png")
    print("previews: preview_1k.png preview_10k.png preview_50k.png")
except ImportError:
    pass

# 5) Pascal's triangle link: C(i+j, i) is odd exactly when i & j == 0 (Lucas's theorem),
#    i.e. odd entries of Pascal's triangle sit on the same cells as the Sierpinski pattern. Check rows 0-127.
from math import comb
bad = sum((comb(i + j, i) % 2 == 1) != ((i & j) == 0) for i in range(128) for j in range(128 - i))
odd = sum(comb(n, r) % 2 for n in range(64) for r in range(n + 1))
print(f"Pascal check, rows 0-127: mismatches between 'odd' and 'i&j==0' = {bad}; odd entries in first 64 rows = {odd} (= 3^6 = {3**6})")

# --- added after writers' room r1 -------------------------------------------------------------
print("\n# r1 checks")
# (a) exactness: from a corner, after n jumps x*2^n and y*2^n are integers with no shared 1-bits (on the attractor).
r = np.random.default_rng(SEED); X = Y = 0; okx = True
for n, c in enumerate(r.integers(0, 3, 60), start=1):
    X, Y = X + (2**(n-1) if c == 1 else 0), Y + (2**(n-1) if c == 2 else 0)
    # position = (X/2^n, Y/2^n) with the newest jump as the top bit; check i & j == 0 at full resolution
    okx &= (X & Y) == 0
print(f"exact integer check, 60 jumps from corner (0,0): every dot has x,y binary digits with no shared 1s: {okx}")

# (b) robustness across seeds: at 1,000 dots, how many of the 81 level-4 triangles and 243 level-5 triangles are hit
h4, h5 = [], []
for sd in range(1, 21):
    rr = np.random.default_rng(sd); q = np.zeros(2); P = np.empty((1000, 2))
    for n, c in enumerate(rr.integers(0, 3, 1000)): q = (q + V[c]) / 2; P[n] = q
    for k, store in ((4, h4), (5, h5)):
        _, i, j = in_level(P, k); store.append(len(set(zip(i.tolist(), j.tolist()))))
print(f"20 seeds, 1,000 dots each: level-4 triangles hit min {min(h4)}/81 max {max(h4)}/81; level-5 min {min(h5)}/243 max {max(h5)}/243")

# (c) a square with the same rule fills uniformly: 4 corners, jump halfway, 200,000 dots, 64x64 grid
rs = np.random.default_rng(SEED); S4 = np.array([[0,0],[1,0],[1,1],[0,1]], float); q = np.zeros(2); hit = np.zeros((64, 64), int)
for c in rs.integers(0, 4, 200_000):
    q = (q + S4[c]) / 2; hit[min(int(q[0]*64), 63), min(int(q[1]*64), 63)] += 1
print(f"square, 4 corners, ratio 1/2, 200,000 dots: 64x64 cells hit {np.count_nonzero(hit)}/4096, min {hit.min()} max {hit.max()} per cell (mean {hit.mean():.1f})")

# (d) the rule without randomness: corners in a fixed cycle 0,1,2,0,1,2... -> dots settle onto just 3 points
q = np.zeros(2); seen = set()
for n in range(3000):
    q = (q + V[n % 3]) / 2
    if n > 100: seen.add((round(q[0], 9), round(q[1], 9)))
print(f"fixed cycle of corners: after 100 jumps the dots sit on {len(seen)} distinct points: {sorted(seen)}")

# (e) zoom fairness: share of dots inside the lower-left half-size copy
inside = (pts[:, 0] < 0.5) & (pts[:, 1] < 0.5) & (pts[:, 0] + pts[:, 1] < 0.5)
print(f"share of the {N:,} dots in the lower-left half-size copy: {inside.mean():.4f} (about 1/3, so the 2x zoom needs ~3x the dots to look as dense)")

# (f) Pascal rows 0-15 vs level-4 cells, cell for cell
bad16 = sum((comb(i + j, i) % 2 == 1) != ((i & j) == 0) for i in range(16) for j in range(16 - i))
print(f"Pascal rows 0-15 vs the 81 level-4 triangles: mismatches = {bad16}; odd entries = {sum(comb(n, r) % 2 for n in range(16) for r in range(n+1))} (= 3^4 = 81)")
