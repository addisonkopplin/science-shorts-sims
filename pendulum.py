"""1,000 double pendulums whose starting angles differ by less than 0.0001 degrees -> chaos.
Equal point masses, equal massless rods (L = 1 m, g = 9.81 m/s^2), RK4 integration, no friction
(the physics is in dp_sim.py; energy drift is printed as a check). The video ends by crossfading back
to the first frame, so it loops.

    python pendulum.py                    # render out/pendulum.mp4 (video + synced sound)
    python pendulum.py --preview 0,12,22  # still frames -> out/pendulum_*.png
    python pendulum.py --no-sound --gif
"""
import argparse, math, os, sys, colorsys
import numpy as np, cairo
from common import *
from dp_sim import simulate, energy

DUR, N = 34.0, 1000
TH0, SPREAD, TSCALE = 2.4, 1e-6, 0.75     # rad, total spread of theta2 across all pendulums (rad), slow-motion factor
PX, PY, ARM = CX, 840, 225
XF0, XF1 = DUR - 1.6, DUR - 0.2           # crossfade back to the opening frame (loop)

tr = simulate(TH0, SPREAD, N, DUR, sub=40, tscale=TSCALE)   # (frames+1, 4, N)
E = np.array([energy(tr[:, :, i].T) for i in (0, N - 1)])
print("energy drift (J/kg-ish):", float(np.abs(E - E[:, :1]).max()), "spread deg:", math.degrees(SPREAD))
tip = lambda f: (PX + ARM * (np.sin(tr[f, 0]) + np.sin(tr[f, 1])), PY + ARM * (np.cos(tr[f, 0]) + np.cos(tr[f, 1])))
xs = np.array([tip(f)[0] for f in range(len(tr))]); ys = np.array([tip(f)[1] for f in range(len(tr))])
spread_px = np.hypot(xs.std(1), ys.std(1))
t_div = next(i / FPS for i, v in enumerate(spread_px) if v > 20)
print("visible divergence at", t_div, "s")
COLORS = [colorsys.hsv_to_rgb(0.85 * i / (N - 1), 0.75, 1.0) for i in range(N)]

def draw_state(c, f, alpha, trail=True):
    t1, t2 = tr[f, 0], tr[f, 1]
    x1 = PX + ARM * np.sin(t1); y1 = PY + ARM * np.cos(t1)
    x2 = x1 + ARM * np.sin(t2); y2 = y1 + ARM * np.cos(t2)
    if trail:
        for back in range(1, 10):
            fb = f - back * 2
            if fb < 0: break
            bx, by = xs[fb], ys[fb]
            for i in range(0, N, 2):
                c.set_source_rgba(*COLORS[i], alpha * 0.10 * (1 - back / 10))
                c.rectangle(bx[i] - 1.5, by[i] - 1.5, 3, 3)
                c.fill()
    c.set_line_width(2.2); c.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(N):
        c.set_source_rgba(*COLORS[i], alpha * 0.22)
        c.move_to(PX, PY); c.line_to(x1[i], y1[i]); c.line_to(x2[i], y2[i]); c.stroke()
    for i in range(N):
        c.set_source_rgba(*COLORS[i], alpha * 0.8)
        c.arc(x2[i], y2[i], 4, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(1, 1, 1, alpha); c.arc(PX, PY, 7, 0, 2 * math.pi); c.fill()

def frame(c, t):
    f = int(round(t * FPS))
    u = ease((t - XF0) / (XF1 - XF0)) if t > XF0 else 0.0
    draw_state(c, f, 1 - u)
    if u > 0: draw_state(c, 0, u, trail=False)
    hook = 1.0 if t < 4.5 else fade(t, 0, 4.9)
    if t > XF0: hook = u
    y = text(c, "This is 1,000 pendulums", 200, 84, hook)
    text(c, "not one", y + 8, 54, hook, color=GOLD, weight=cairo.FONT_WEIGHT_NORMAL)
    text(c, "Their starting angles differ by less than 0.0001°", 200, 72, fade(t, 5.1, 10.4))
    text(c, "Then chaos takes over", 200, 84, fade(t, 10.7, 17.6), color=GOLD)
    text(c, "Tiny differences grow exponentially until no two agree", 200, 70, fade(t, 17.9, 24.8))
    text(c, "It's why weather forecasts break down after about two weeks", 200, 66, fade(t, 25.1, XF0))

def main():
    ap = argparse.ArgumentParser(description="Double pendulum Short: render video and synced sound")
    ap.add_argument("--preview", help="comma-separated times in seconds: write still PNGs instead of a video")
    ap.add_argument("--no-sound", action="store_true", help="skip the sound (video only)")
    ap.add_argument("--gif", action="store_true", help="also write a small looping preview GIF")
    ap.add_argument("--out", default="out", help="output folder")
    a = ap.parse_args()
    if a.preview:
        for tt in map(float, a.preview.split(",")):
            p = os.path.join(a.out, f"pendulum_{tt:05.1f}.png"); still(frame, tt, p); print("wrote", p)
        return
    video = os.path.join(a.out, "pendulum.video.mp4")
    render_video(frame, DUR, video)
    final = video
    if not a.no_sound:
        import pendulum_sound, sound as S
        wav = os.path.join(a.out, "pendulum.wav")
        pendulum_sound.score(sys.modules[__name__], wav)
        final = os.path.join(a.out, "pendulum.mp4")
        S.mux(video, wav, final); print("wrote", final)
    if a.gif:
        from galton import make_gif
        make_gif(final, os.path.join(a.out, "pendulum.gif"))

if __name__ == "__main__":
    main()
