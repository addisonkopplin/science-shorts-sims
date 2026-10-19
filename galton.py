"""Galton board -> bell curve. 1,000 balls fall through 12 rows of pegs; at every peg a ball goes left or
right with probability 1/2 (an idealised board: no bouncing physics, just fair coin flips).

    python galton.py                  # render out/galton.mp4 (video + synced sound), about a minute or two
    python galton.py --preview 0,8,22 # just a few still frames -> out/galton_*.png
    python galton.py --no-sound       # video only
    python galton.py --seed 3         # another random run (some seeds overflow the bins and are rejected)
    python galton.py --gif            # also a small preview GIF
"""
import argparse, math, os, subprocess, sys
import numpy as np, cairo
from common import *

DUR = 36.0
N, ROWS = 1000, 12
DX, DY, Y0 = 62, 40, 600
PEG_R, BALL_R = 5.0, 4.2
BIN_TOP = Y0 + ROWS * DY - 10   # 1070
BIN_BOT = 1425
PER_ROW_E, PER_ROW_O, SPX, ROWH = 6, 5, 9.4, 8.2
T_HOP, G = 0.13, 3200.0
SEED = 7
ENTRY = 0.28   # fall from funnel to first peg
DRAIN0 = 33.4  # the floor opens and the balls drain (then the video loops)

def setup(seed=SEED):
    """run the random part of the simulation: every ball's left/right choices and when it is released"""
    global rng, emit, steps, k_final, counts, slot, land
    rng = np.random.default_rng(seed)
    # emission schedule: slow at first so you can follow one ball, then a stream
    emit, t = [], 0.05
    while len(emit) < N:
        rate = 3.5 if t < 3 else (3.5 + (90 - 3.5) * min(1, (t - 3) / 5))
        emit.append(t); t += 1 / rate
    emit = np.array(emit)
    steps = rng.integers(0, 2, size=(N, ROWS))          # 1 = right, 0 = left, p = 1/2 each
    k_final = steps.sum(1)                              # bin = number of rights
    counts = np.bincount(k_final, minlength=ROWS + 1)
    slot = np.zeros(N, int); seen = np.zeros(ROWS + 1, int)
    for b in range(N):
        slot[b] = seen[k_final[b]]; seen[k_final[b]] += 1
    top_y = slot_xy(6, counts.max() - 1)[1]
    print("seed", seed, "balls per bin", counts.tolist())
    if top_y <= BIN_TOP + 10:
        sys.exit(f"seed {seed}: the tallest stack overflows the bins; try another --seed")
    land = np.array([landed_time(b) for b in range(N)])

def slot_xy(k, n):
    pair, rem = divmod(n, PER_ROW_E + PER_ROW_O)
    row = pair * 2 + (0 if rem < PER_ROW_E else 1)
    col = rem if rem < PER_ROW_E else rem - PER_ROW_E
    left = CX + (k - 6) * DX - DX / 2 + 3 + BALL_R + 1.2
    x = left + col * SPX + (SPX / 2 if row % 2 else 0)
    y = BIN_BOT - BALL_R - 1 - row * ROWH
    return x, y

def peg_xy(r, j): return CX + (j - r / 2) * DX, Y0 + r * DY

def ball_pos(b, t):
    """position of ball b at time t, or None if not yet emitted"""
    te = t - emit[b]
    if te < 0: return None
    # entry
    px, py = peg_xy(0, 0); py -= PEG_R + BALL_R
    if te < ENTRY:
        s = te / ENTRY; return CX, (Y0 - 90) + (py - (Y0 - 90)) * s * s
    te -= ENTRY
    if te < ROWS * T_HOP:
        r = int(te // T_HOP); s = (te - r * T_HOP) / T_HOP
        j = steps[b, :r].sum()
        x0, y0 = peg_xy(r, j)
        dirn = 1 if steps[b, r] else -1
        x = x0 + dirn * DX / 2 * ease(s)
        y = y0 + DY * (0.35 * s + 0.65 * s * s) - 16 * math.sin(math.pi * s) - PEG_R - BALL_R
        return x, y
    te -= ROWS * T_HOP
    k = k_final[b]
    x1, y1 = slot_xy(k, slot[b])
    xs = CX + (k - 6) * DX
    ys = Y0 + ROWS * DY - PEG_R - BALL_R
    v0 = 260.0
    # y = ys + v0 t + G t^2/2 until y1
    tf = (-v0 + math.sqrt(v0 * v0 + 2 * G * (y1 - ys))) / G
    if te < tf:
        s = te / tf
        return xs + (x1 - xs) * ease(s), ys + v0 * te + G * te * te / 2
    return x1, y1

def landed_time(b):
    k = k_final[b]; x1, y1 = slot_xy(k, slot[b]); ys = Y0 + ROWS * DY - PEG_R - BALL_R; v0 = 260.0
    return emit[b] + ENTRY + ROWS * T_HOP + (-v0 + math.sqrt(v0 * v0 + 2 * G * (y1 - ys))) / G
def drain_offset(b, t):
    """after DRAIN0 the floor opens; balls fall out, lower ones first"""
    if t < DRAIN0: return 0.0
    k = k_final[b]; delay = (slot[b] / max(counts)) * 0.5 + abs(k - 6) * 0.02
    tt = t - DRAIN0 - delay
    return 0.0 if tt < 0 else 0.5 * 4000 * tt * tt

def normal_curve_pts():
    mu, var = ROWS / 2, ROWS / 4
    pts = []
    for i in range(241):
        kx = -0.5 + (ROWS + 1) * i / 240
        dens = N * math.exp(-(kx - mu) ** 2 / (2 * var)) / math.sqrt(2 * math.pi * var)  # expected balls per bin
        # height of a stack of `dens` balls
        h = dens / (PER_ROW_E + PER_ROW_O) * 2 * ROWH
        pts.append((CX + (kx - 6) * DX, BIN_BOT - h))
    return pts
CURVE = normal_curve_pts()

def board(c, t):
    floor_open = ease((t - DRAIN0) / 0.25) if t > DRAIN0 else 0
    c.set_source_rgb(0.42, 0.44, 0.52)
    for r in range(ROWS):
        for j in range(r + 1):
            x, y = peg_xy(r, j); c.arc(x, y, PEG_R, 0, 2 * math.pi); c.fill()
    # funnel
    c.set_line_width(4); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(CX - 70, Y0 - 120); c.line_to(CX - 14, Y0 - 70); c.move_to(CX + 70, Y0 - 120); c.line_to(CX + 14, Y0 - 70); c.stroke()
    # bins
    c.set_line_width(3)
    for k in range(ROWS + 2):
        x = CX + (k - 6.5) * DX
        c.move_to(x, BIN_TOP); c.line_to(x, BIN_BOT); c.stroke()
    c.set_source_rgba(0.42, 0.44, 0.52, 1 - floor_open)
    c.move_to(CX - 6.5 * DX, BIN_BOT); c.line_to(CX + 6.5 * DX, BIN_BOT); c.stroke()

def frame(c, t):
    board(c, t)
    # balls
    nlanded = 0
    for b in range(N):
        if emit[b] > t: break
        p = ball_pos(b, t)
        if t >= land[b]: nlanded += 1
        x, y = p; y += drain_offset(b, t)
        if y > H + 10: continue
        if b == 0: c.set_source_rgb(*GOLD); rr = BALL_R + 2.5
        else: c.set_source_rgb(0.80, 0.86, 1.0); rr = BALL_R
        c.arc(x, y, rr, 0, 2 * math.pi); c.fill()
    # gold ball trail (path so far) during first seconds
    a = fade(t, 0.0, 5.0, 0.5)
    if a > 0 and t > emit[0]:
        c.set_source_rgba(*GOLD, 0.55 * a); c.set_line_width(3)
        tt = min(t, land[0]); first = True
        for s in np.linspace(emit[0], tt, 120):
            x, y = ball_pos(0, s)
            (c.move_to if first else c.line_to)(x, y); first = False
        c.stroke()
    # bell curve overlay
    cp = ease((t - 19.2) / 2.0) * (1 - ease((t - DRAIN0) / 0.4))
    if cp > 0:
        c.set_source_rgba(*GOLD, 0.95 if t < DRAIN0 else (1 - ease((t - DRAIN0) / 0.4)))
        c.set_line_width(6); c.set_line_join(cairo.LINE_JOIN_ROUND)
        n = max(2, int(len(CURVE) * cp))
        c.move_to(*CURVE[0])
        for p in CURVE[1:n]: c.line_to(*p)
        c.stroke()
    # counter
    ca = fade(t, 0.0, DRAIN0, 0.3) if t > 0.4 else 1
    text(c, f"{nlanded:,}", 640, size=54, alpha=ca, color=(0.85, 0.88, 0.96), x=SAFE['left'] + 10, align="left")
    text(c, f"of {N:,} balls", 706, size=34, alpha=ca * 0.8, color=(0.7, 0.73, 0.83), x=SAFE['left'] + 10,
         align="left", weight=cairo.FONT_WEIGHT_NORMAL)
    # captions
    hook_a = 1.0 if t < 4.6 else fade(t, 0, 5.0)
    if t > DUR - 0.7: hook_a = ease((t - (DUR - 0.7)) / 0.6)
    y = text(c, "Every bounce is a coin flip", 205, 82, hook_a)
    text(c, "left or right, 50/50", y + 12, 46, hook_a * 0.9, color=GOLD, weight=cairo.FONT_WEIGHT_NORMAL)
    text(c, "So no one can predict where a single ball lands", 205, 74, fade(t, 5.2, 11.0))
    text(c, "But 1,000 of them pile into a shape you can predict", 205, 74, fade(t, 11.3, 19.0))
    a = fade(t, 19.3, 28.6)
    y = text(c, "The bell curve", 215, 100, a, color=GOLD)
    text(c, "a.k.a. the normal distribution", y + 10, 48, a, weight=cairo.FONT_WEIGHT_NORMAL)
    text(c, "Add up lots of random coin flips and this shape appears. That's the central limit theorem.",
         195, 60, fade(t, 28.9, 33.6))

def main():
    ap = argparse.ArgumentParser(description="Galton board Short: render video and synced sound")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--preview", help="comma-separated times in seconds: write still PNGs instead of a video")
    ap.add_argument("--no-sound", action="store_true", help="skip the sound (video only)")
    ap.add_argument("--variant", default="mallet", choices=["mallet", "glass"], help="instrument set for the sound")
    ap.add_argument("--gif", action="store_true", help="also write a small looping preview GIF")
    ap.add_argument("--out", default="out", help="output folder")
    a = ap.parse_args()
    setup(a.seed)
    if a.preview:
        for tt in map(float, a.preview.split(",")):
            p = os.path.join(a.out, f"galton_{tt:05.1f}.png"); still(frame, tt, p); print("wrote", p)
        return
    video = os.path.join(a.out, "galton.video.mp4")
    render_video(frame, DUR, video)
    final = video
    if not a.no_sound:
        import galton_sound
        wav = os.path.join(a.out, "galton.wav")
        galton_sound.score(sys.modules[__name__], wav, a.variant)
        final = os.path.join(a.out, "galton.mp4")
        import sound as S
        S.mux(video, wav, final)
        print("wrote", final)
    if a.gif:
        gif = os.path.join(a.out, "galton.gif")
        make_gif(final, gif)

def make_gif(video, gif, width=270, fps=12):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-vf",
                    f"fps={fps},scale={width}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                    "-loop", "0", gif], check=True)
    print("wrote", gif)

if __name__ == "__main__":
    main()
