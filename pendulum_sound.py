"""Sound for the double pendulums: ONLY discrete event sounds from the motion (no drones, pads or held tones).
Events, for all 1,000 pendulums:
  * upper arm turns around (its angular velocity changes sign) -> marimba note
  * lower bob swings over the top (its angle crosses pi)        -> marimba chime an octave higher
Pitch = the lower bob's speed at that instant, mapped to a pentatonic degree. Pan = the bob's x position.
Pendulums that fire the same event at (nearly) the same time and pitch merge into one note whose loudness
grows with how many fired: at the start all 1,000 are in sync, so you hear single crisp notes; as chaos
takes over the notes scatter. Notes are thinned by importance (at most 5 per half second).
Usage: run pendulum.py (it calls score()). Standalone: python pendulum_sound.py -> out/pendulum.wav
"""
import json, os
import numpy as np
from common import FPS
import sound as S

def score(p, out_wav):
    SR = S.SR; DUR = p.DUR; N = p.N
    t1, t2, w1, w2 = (p.tr[:, i, :] for i in range(4))
    vx = np.cos(t1) * w1 + np.cos(t2) * w2; vy = -(np.sin(t1) * w1 + np.sin(t2) * w2)
    speed = np.hypot(vx, vy); VMAX = np.quantile(speed, 0.995)
    xpos = np.sin(t1) + np.sin(t2)
    CLUSTER = 0.015       # s: events closer than this with the same pitch merge (well under the 30 ms sync budget)
    CAP = 5               # max notes per 0.5 s window (keep the biggest clusters)

    def crossings(kind):
        """per-pendulum sub-frame event times. returns arrays (t, idx_pendulum, frame)"""
        T, I, F = [], [], []
        if kind == "rev":
            a, b = w1[:-1], w1[1:]
            m = (np.sign(a) != np.sign(b)) & (a != 0)
            f, i = np.nonzero(m)
            frac = a[f, i] / (a[f, i] - b[f, i])
        else:  # over the top: theta2 crosses pi (mod 2pi)
            k = np.floor((t2 + np.pi) / (2 * np.pi))
            m = np.diff(k, axis=0) != 0
            f, i = np.nonzero(m)
            # fraction where (theta2 - pi) hits a multiple of 2pi
            a = t2[f, i]; b = t2[f + 1, i]
            tgt = np.where(b > a, np.ceil((a - np.pi) / (2 * np.pi)) * 2 * np.pi + np.pi, np.floor((a - np.pi) / (2 * np.pi)) * 2 * np.pi + np.pi)
            frac = np.clip((tgt - a) / (b - a), 0, 1)
        return (f + frac) / FPS, i, f

    notes = []
    for kind in ("rev", "flip"):
        t, idx, f = crossings(kind)
        keep = t < p.XF0
        t, idx, f = t[keep], idx[keep], f[keep]
        deg = np.round(np.clip(speed[f, idx] / VMAX, 0, 1) * 7).astype(int)    # 0..7 pentatonic steps
        order = np.argsort(t); t, idx, f, deg = t[order], idx[order], f[order], deg[order]
        used = np.zeros(len(t), bool)
        for a in range(len(t)):
            if used[a]: continue
            m = (~used[a:]) & (t[a:] - t[a] < CLUSTER) & (deg[a:] == deg[a])
            sel = np.nonzero(m)[0] + a; used[sel] = True
            notes.append(dict(kind=kind, t=float(np.mean(t[sel])), n=int(len(sel)), deg=int(deg[a]),
                              x=float(np.mean(xpos[f[sel], idx[sel]]))))
    print("raw clusters", len(notes))
    # thin by importance: per 0.5 s window keep the CAP largest clusters (flips favoured slightly)
    kept = []
    for w0 in np.arange(0, DUR, 0.5):
        win = [n_ for n_ in notes if w0 <= n_["t"] < w0 + 0.5]
        win.sort(key=lambda n_: -(n_["n"] * (1.5 if n_["kind"] == "flip" else 1.0)))
        kept += win[:CAP]
    kept.sort(key=lambda n_: n_["t"])
    print("kept notes", len(kept), " in-sync notes (n>900):", sum(n_["n"] > 900 for n_ in kept))

    bus = S.Bus(DUR)
    for n_ in kept:
        imp = np.sqrt(n_["n"] / N)                       # 1,000 in sync -> 1.0; a lone pendulum -> 0.03
        vel = 0.30 + 0.70 * imp
        if n_["kind"] == "rev":
            f0 = S.degree(n_["deg"])                     # C4..C6 range
            sig = S.marimba(f0, min(1.0, vel), 1.2)
            g = 0.9
        else:
            f0 = S.degree(n_["deg"] + 5)                 # an octave up: chime
            sig = S.marimba(f0, min(1.0, vel), 1.6)
            g = 0.75
        bus.add(sig, n_["t"], g * (0.55 + 0.45 * imp), pan=float(np.clip(n_["x"] / 2, -1, 1)) * 0.8)

    st = bus.stereo()
    st = S.wrap_tail(S.reverb(st, 0.16, 1.8), DUR)          # loop: the ring-out folds onto the start
    st = S.master(st, DUR, target=-14.1, wet=0.0, fade_ms=0)
    os.makedirs(os.path.dirname(out_wav) or ".", exist_ok=True)
    S.write_wav(out_wav, st)
    det = S.onsets(bus.stereo()[:int(SR * DUR)].mean(1), thresh=1.0)
    allt = np.array([n_["t"] for n_ in kept])
    rep = dict(notes=len(kept), phone_energy_kept=round(S.phone_check(st), 3), sync=S.sync_report(allt, det))
    print("  sound ->", out_wav, json.dumps(rep))
    return rep

if __name__ == "__main__":
    import pendulum as p
    score(p, os.path.join("out", "pendulum.wav"))
