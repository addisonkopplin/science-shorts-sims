"""science-03: Galton board, long build -> the 1 in 4,096 ball drops into a 10x slot.
Random phase: 1,000 balls, p=1/2 per peg (seed 241: no ball reaches either edge; 12 land one bounce from it).
Final ball: staged, it is sent down the all-left path (1 of 4,096 equally likely paths) to show the edge."""
import math, numpy as np, cairo, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))  # repo root: common.py
from common import *

OUT = "science-03"
SEED = 241
DUR = 65.5
N, ROWS = 1000, 12
DX, DY, Y0 = 62, 40, 600
PEG_R, BALL_R = 5.0, 4.2
BIN_TOP = Y0 + ROWS * DY - 10
BIN_BOT = 1425
PER_ROW_E, PER_ROW_O, SPX, ROWH = 6, 5, 9.4, 8.2
T_HOP, G = 0.13, 3200.0
ORANGE = (1.0, 0.55, 0.22)
BLUE = (0.80, 0.86, 1.0)
rng = np.random.default_rng(SEED)

# ---- emission: slow start, steady stream, ends ~44 s ----
emit, t = [], 0.3
while len(emit) < N:
    rate = 2.2 if t < 6 else (2.2 + (28 - 2.2) * min(1, (t - 6) / 6))
    emit.append(t); t += 1 / rate
emit = np.array(emit)
steps = rng.integers(0, 2, size=(N, ROWS))          # 1 = right
k_final = steps.sum(1)
counts = np.bincount(k_final, minlength=ROWS + 1)
assert counts[0] == 0 and counts[ROWS] == 0
RUN = np.array([(np.argmax(r != r[0]) if (r != r[0]).any() else ROWS) for r in steps])  # initial same-way run
slot = np.zeros(N, int); seen = np.zeros(ROWS + 1, int)
for b in range(N):
    slot[b] = seen[k_final[b]]; seen[k_final[b]] += 1

def slot_xy(k, n):
    pair, rem = divmod(n, PER_ROW_E + PER_ROW_O)
    row = pair * 2 + (0 if rem < PER_ROW_E else 1)
    col = rem if rem < PER_ROW_E else rem - PER_ROW_E
    left = CX + (k - 6) * DX - DX / 2 + 3 + BALL_R + 1.2
    x = left + col * SPX + (SPX / 2 if row % 2 else 0)
    return x, BIN_BOT - BALL_R - 1 - row * ROWH

def peg_xy(r, j): return CX + (j - r / 2) * DX, Y0 + r * DY
ENTRY = 0.28
YS = Y0 + ROWS * DY - PEG_R - BALL_R

def hop_xy(r, j, dirn, s):
    x0, y0 = peg_xy(r, j)
    return x0 + dirn * DX / 2 * ease(s), y0 + DY * (0.35 * s + 0.65 * s * s) - 16 * math.sin(math.pi * s) - PEG_R - BALL_R

def fall_time(y1, v0=260.0, g=G): return (-v0 + math.sqrt(v0 * v0 + 2 * g * (y1 - YS))) / g

def ball_pos(b, t):
    te = t - emit[b]
    if te < 0: return None
    py = Y0 - PEG_R - BALL_R
    if te < ENTRY:
        s = te / ENTRY; return CX, (Y0 - 90) + (py - (Y0 - 90)) * s * s
    te -= ENTRY
    if te < ROWS * T_HOP:
        r = int(te // T_HOP); s = (te - r * T_HOP) / T_HOP
        return hop_xy(r, steps[b, :r].sum(), 1 if steps[b, r] else -1, s)
    te -= ROWS * T_HOP
    k = k_final[b]; x1, y1 = slot_xy(k, slot[b]); xs = CX + (k - 6) * DX
    tf = fall_time(y1)
    if te < tf:
        return xs + (x1 - xs) * ease(te / tf), YS + 260 * te + G * te * te / 2
    return x1, y1

land = np.array([emit[b] + ENTRY + ROWS * T_HOP + fall_time(slot_xy(k_final[b], slot[b])[1]) for b in range(N)])
NEAR = [b for b in np.argsort(land) if k_final[b] in (1, ROWS - 1)]
print("counts", counts.tolist(), "near", len(NEAR), "runs>=7", int((RUN >= 7).sum()), "last landing", round(land.max(), 2))

def streak_state(b, t):
    """(current streak length, alive) while ball b is among the pegs"""
    te = t - emit[b] - ENTRY
    if te < 0 or te >= ROWS * T_HOP: return 0, False
    made = int(te // T_HOP) + 1
    return min(made, RUN[b]), made <= RUN[b]

# ---- final staged ball ----
FB0 = 52.0
FB_HOP = [0.36 + 0.26 * (r / 11) ** 2 for r in range(ROWS)]
FB_PEG = [FB0 + ENTRY * 2 + sum(FB_HOP[:r]) for r in range(ROWS)]   # time it touches peg row r
FB_EXIT = FB_PEG[-1] + FB_HOP[-1]
FB_BIN_Y = slot_xy(0, 0)[1]
FB_LAND = FB_EXIT + fall_time(FB_BIN_Y)
DOOR = FB_LAND + 1.0
G2 = 1500.0
BOX_X, BOX_TOP, BOX_BOT, BOX_W = CX, 1790, 1960, 300
FB_REST = BOX_BOT - 6 - BALL_R - 3
X0B = CX - 6 * DX
def _bez(p0, p1, p2, p3, n=80):
    u = np.linspace(0, 1, n)[:, None]
    return (1-u)**3*np.array(p0) + 3*(1-u)**2*u*np.array(p1) + 3*(1-u)*u*u*np.array(p2) + u**3*np.array(p3)
CHUTE = np.vstack([np.array([[X0B, FB_BIN_Y], [X0B, 1540]]),
                   _bez((X0B, 1540), (X0B, 1680), (BOX_X, 1600), (BOX_X, 1745))[1:],
                   np.array([[BOX_X, FB_REST]])])
_seg = np.hypot(*np.diff(CHUTE, axis=0).T); CUM = np.concatenate([[0], np.cumsum(_seg)]); PATH_LEN = CUM[-1]
FB_HIT = DOOR + 0.12 + math.sqrt(2 * PATH_LEN / G2)
CAM_MAX = 560
print("final: pegs", round(FB_PEG[0], 2), "-", round(FB_PEG[-1], 2), "bin", round(FB_LAND, 2), "door", round(DOOR, 2), "hit", round(FB_HIT, 2))

def fb_pos(t):
    te = t - FB0
    if te < 0: return None
    py = Y0 - PEG_R - BALL_R
    if te < 2 * ENTRY:
        s = te / (2 * ENTRY); return CX, (Y0 - 90) + (py - (Y0 - 90)) * s * s
    if t < FB_EXIT:
        r = max(i for i in range(ROWS) if FB_PEG[i] <= t); s = (t - FB_PEG[r]) / FB_HOP[r]
        return hop_xy(r, 0, -1, s)
    if t < FB_LAND:
        te = t - FB_EXIT; return X0B, YS + 260 * te + G * te * te / 2
    if t < DOOR + 0.12: return X0B, FB_BIN_Y
    d = min(PATH_LEN, 0.5 * G2 * (t - DOOR - 0.12) ** 2)
    return float(np.interp(d, CUM, CHUTE[:, 0])), float(np.interp(d, CUM, CHUTE[:, 1]))

def cam(t):
    if t < DOOR: return 0.0
    return CAM_MAX * ease((t - DOOR) / (FB_HIT - DOOR + 0.2))

def fb_streak(t):
    return sum(1 for p in FB_PEG if p + 0.02 <= t) if t >= FB_PEG[0] else 0

def normal_curve_pts():
    mu, var = ROWS / 2, ROWS / 4; pts = []
    for i in range(241):
        kx = -0.5 + (ROWS + 1) * i / 240
        dens = N * math.exp(-(kx - mu) ** 2 / (2 * var)) / math.sqrt(2 * math.pi * var)
        pts.append((CX + (kx - 6) * DX, BIN_BOT - dens / (PER_ROW_E + PER_ROW_O) * 2 * ROWH))
    return pts
CURVE = normal_curve_pts()
CURVE_T = 34.6

def bin_x(k): return CX + (k - 6.5) * DX

def board(c, t):
    peg_a = 1 - 0.75 * ease((t - DOOR) / 1.0)
    c.set_source_rgba(0.42, 0.44, 0.52, peg_a)
    for r in range(ROWS):
        for j in range(r + 1):
            x, y = peg_xy(r, j); c.arc(x, y, PEG_R, 0, 2 * math.pi); c.fill()
    # pegs on the final ball's path light up as it touches them
    for r in range(ROWS):
        if t >= FB_PEG[r]:
            a = 0.35 + 0.65 * max(0, 1 - (t - FB_PEG[r]) / 0.5)
            x, y = peg_xy(r, 0); c.set_source_rgba(*GOLD, a * peg_a); c.arc(x, y, PEG_R + 1.5, 0, 2 * math.pi); c.fill()
    c.set_source_rgb(0.42, 0.44, 0.52)
    c.set_line_width(4); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(CX - 70, Y0 - 120); c.line_to(CX - 14, Y0 - 70); c.move_to(CX + 70, Y0 - 120); c.line_to(CX + 14, Y0 - 70); c.stroke()
    # edge bins tinted once the odds are explained
    ea = ease((t - 16.3) / 0.6)
    if ea > 0:
        for k in (0, ROWS):
            c.set_source_rgba(*GOLD, 0.10 * ea + (0.12 * ea if 16.3 < t < 25 else 0) * (0.5 + 0.5 * math.sin(t * 5)))
            c.rectangle(bin_x(k) + 2, BIN_TOP, DX - 4, BIN_BOT - BIN_TOP); c.fill()
    # near-miss flash
    for b in NEAR:
        dt = t - land[b]
        if 0 <= dt < 0.9:
            k = k_final[b]; c.set_source_rgba(*ORANGE, 0.35 * (1 - dt / 0.9))
            c.rectangle(bin_x(k) + 2, BIN_TOP, DX - 4, BIN_BOT - BIN_TOP); c.fill()
    c.set_source_rgb(0.42, 0.44, 0.52); c.set_line_width(3)
    for k in range(ROWS + 2):
        x = CX + (k - 6.5) * DX; c.move_to(x, BIN_TOP); c.line_to(x, BIN_BOT); c.stroke()
    # floor; bin 0 segment is a trapdoor hinged at its left end
    c.move_to(bin_x(1), BIN_BOT); c.line_to(CX + 6.5 * DX, BIN_BOT); c.stroke()
    ang = (math.pi / 2) * min(1, ((t - DOOR) / 0.18) ** 2) if t > DOOR else 0
    hx = bin_x(0)
    if t <= DOOR + 0.4: c.move_to(hx, BIN_BOT); c.line_to(hx + DX * math.cos(ang), BIN_BOT + DX * math.sin(ang)); c.stroke()
    # chute + 10x cup (below the screen until the camera moves)
    if t > DOOR:
        ia = ease((t - DOOR) / 0.4)
        c.set_line_cap(cairo.LINE_CAP_BUTT); c.set_line_join(cairo.LINE_JOIN_ROUND)
        for w, col in ((DX - 4 + 6, (0.42, 0.44, 0.52, ia)), (DX - 4, (*BG, 1))):
            c.set_source_rgba(*col); c.set_line_width(w)
            c.move_to(*CHUTE[0]); [c.line_to(*q) for q in CHUTE[1:-1]]; c.line_to(BOX_X, BOX_TOP + 2); c.stroke()
        hit = t >= FB_HIT; glow = max(0, 1 - (t - FB_HIT) / 1.2) if hit else 0
        x0 = BOX_X - BOX_W / 2
        if hit:
            c.set_source_rgba(*GOLD, 0.18 + 0.5 * glow); c.rectangle(x0, BOX_TOP, BOX_W, BOX_BOT - BOX_TOP); c.fill()
        c.set_source_rgb(*(GOLD if hit else (0.6, 0.62, 0.7))); c.set_line_width(5); c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.move_to(x0, BOX_TOP); c.line_to(x0, BOX_BOT); c.line_to(x0 + BOX_W, BOX_BOT); c.line_to(x0 + BOX_W, BOX_TOP); c.stroke()
        sc = 1.0 if not hit else 1 + 0.35 * math.exp(-(t - FB_HIT) * 5) * math.cos((t - FB_HIT) * 9)
        c.save(); c.translate(BOX_X, BOX_TOP + 85); c.scale(sc, sc)
        text(c, "10x", -50, 104, 1.0, color=(WHITE if hit else (0.75, 0.77, 0.85)), x=0)
        c.restore()
        if hit:  # sparks
            srng = np.random.default_rng(3); dt = t - FB_HIT
            if dt < 1.4:
                for i in range(28):
                    a = -math.pi * srng.uniform(0.05, 0.95); v = srng.uniform(250, 700)
                    x = BOX_X + math.cos(a) * v * dt; y = BOX_TOP + math.sin(a) * v * dt + 900 * dt * dt
                    c.set_source_rgba(*GOLD, max(0, 1 - dt / 1.4)); c.arc(x, y, 3.2, 0, 2 * math.pi); c.fill()

def frame(c, t):
    cy = cam(t)
    c.save(); c.translate(0, -cy)
    board(c, t)
    nl = 0
    for b in range(N):
        if emit[b] > t: break
        x, y = ball_pos(b, t)
        if t >= land[b]: nl += 1
        L, alive = streak_state(b, t)
        col = BLUE; rr = BALL_R
        if b == 0: col = GOLD; rr = BALL_R + 2.5
        elif alive and L >= 7: col = ORANGE; rr = BALL_R + 1.5
        elif RUN[b] >= 7 and t - emit[b] - ENTRY > 0:   # streak broke: fade back to blue
            br = emit[b] + ENTRY + RUN[b] * T_HOP; f = max(0, 1 - (t - br) / 0.5)
            col = tuple(BLUE[i] + (ORANGE[i] - BLUE[i]) * f for i in range(3)); rr = BALL_R + 1.5 * f
        c.set_source_rgb(*col); c.arc(x, y, rr, 0, 2 * math.pi); c.fill()
    p = fb_pos(t)
    if p:
        if FB_PEG[0] <= t:   # trail
            c.set_source_rgba(*GOLD, 0.5); c.set_line_width(3); first = True
            for s in np.linspace(FB_PEG[0], min(t, FB_LAND), 160):
                q = fb_pos(s); (c.move_to if first else c.line_to)(*q); first = False
            c.stroke()
        c.set_source_rgb(*GOLD); c.arc(*p, BALL_R + 3.5, 0, 2 * math.pi); c.fill()
    # bell curve
    cp = ease((t - CURVE_T) / 2.0) * (1 - ease((t - 50.8) / 0.6))
    if cp > 0:
        c.set_source_rgba(*GOLD, 0.9 * (1 - ease((t - 50.8) / 0.6))); c.set_line_width(6); c.set_line_join(cairo.LINE_JOIN_ROUND)
        n = max(2, int(len(CURVE) * cp)); c.move_to(*CURVE[0])
        for q in CURVE[1:n]: c.line_to(*q)
        c.stroke()
    # counters (world space so they scroll away with the board)
    ca = 1 - ease((t - 51.2) / 0.5)
    text(c, f"{nl:,}", 640, size=54, alpha=ca, color=(0.85, 0.88, 0.96), x=SAFE['left'] + 10, align="left")
    text(c, f"of {N:,} balls", 706, size=34, alpha=ca * 0.8, color=(0.7, 0.73, 0.83), x=SAFE['left'] + 10, align="left", weight=cairo.FONT_WEIGHT_NORMAL)
    nn = sum(1 for b in NEAR if land[b] <= t)
    na = ca * ease((t - 7.5) / 0.6)
    pulse = max([0] + [1 - (t - land[b]) / 0.6 for b in NEAR if 0 <= t - land[b] < 0.6])
    text(c, "One bounce from the edge:", 780, size=28, alpha=na * 0.8, color=(0.7, 0.73, 0.83), x=SAFE['left'] + 10, align="left", weight=cairo.FONT_WEIGHT_NORMAL, maxw=300)
    text(c, f"{nn}", 852, size=46 + 12 * pulse, alpha=na, color=ORANGE, x=SAFE['left'] + 10, align="left")
    text(c, "On the edge:", 930, size=28, alpha=na * 0.8, color=(0.7, 0.73, 0.83), x=SAFE['left'] + 10, align="left", weight=cairo.FONT_WEIGHT_NORMAL)
    text(c, "0", 968, size=46, alpha=na, color=GOLD, x=SAFE['left'] + 10, align="left")
    c.restore()
    # captions (screen space)
    y = text(c, "Every bounce is a coin flip", 205, 82, fade(t, -1, 7.2))
    text(c, "left or right, 50/50", y + 12, 46, fade(t, -1, 7.2) * 0.9, color=GOLD, weight=cairo.FONT_WEIGHT_NORMAL)
    text(c, "To land on an edge, a ball has to bounce the same way all 12 times", 205, 70, fade(t, 7.5, 16.0))
    a = fade(t, 16.3, 25.0); y = text(c, "1 in 4,096", 205, 110, a, color=GOLD)
    text(c, "chance for each edge", y + 6, 52, a, weight=cairo.FONT_WEIGHT_NORMAL)
    a = fade(t, 25.3, 34.2); y = text(c, "Orange = 7 or more bounces the same way", 205, 66, a, color=ORANGE)
    text(c, "most streaks break before the bottom", y + 10, 46, a, weight=cairo.FONT_WEIGHT_NORMAL)
    a = fade(t, 34.5, 43.0); y = text(c, "Most land in the middle", 205, 76, a)
    text(c, "the bell curve", y + 8, 52, a, color=GOLD, weight=cairo.FONT_WEIGHT_NORMAL)
    a = fade(t, 43.3, 47.6); text(c, "Close calls, but nothing on the edge", 205, 72, a)
    a = fade(t, 47.9, 51.3); y = text(c, "1,000 balls", 205, 96, a)
    text(c, "and none on the edge", y + 6, 60, a, weight=cairo.FONT_WEIGHT_NORMAL)
    a = fade(t, 51.5, FB_PEG[0] + 0.1, 0.25); text(c, "One more", 215, 96, a, color=GOLD)
    a = fade(t, FB_PEG[0] - 0.05, FB_HIT - 0.1, 0.2)
    if a > 0:
        n = fb_streak(t)
        y = text(c, "Lefts in a row", 205, 58, a, weight=cairo.FONT_WEIGHT_NORMAL)
        lp = max([0] + [1 - (t - p) / 0.3 for p in FB_PEG if 0 <= t - p < 0.3])
        text(c, f"{n}", y + 4, 120 + 30 * lp, a, color=GOLD)
    a = ease((t - FB_HIT - 0.25) / 0.4)
    y = text(c, "The 1 in 4,096 ball", 205, 96, a, color=GOLD)
    text(c, "12 lefts in a row", y + 10, 52, a * ease((t - FB_HIT - 0.8) / 0.4), weight=cairo.FONT_WEIGHT_NORMAL)

if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    if only:
        for tt in map(float, only.split(",")):
            s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s); c.set_source_rgb(*BG); c.paint()
            frame(c, tt); os.makedirs("prev", exist_ok=True); s.write_to_png(f"prev/x_{tt:05.1f}.png")
        sys.exit()
    wr = Writer(f"build/{OUT}.video.mp4")
    for f in range(int(DUR * FPS)):
        frame(wr.ctx(), f / FPS); wr.push()
    wr.close(); print("video done")
