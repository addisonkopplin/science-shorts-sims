"""Sound for the Galton board, generated directly from the simulation in galton.py (no samples, no music bed).

Every sound has a visible cause:
  * peg hit        -> a mallet note at the exact hit time. Pitch = the ball's horizontal position (pentatonic
                      scale degree 2j - r around C5: left is lower, right is higher), so each ball's path is a
                      little melody. Pan = peg x. Loudness follows the incoming speed. Dense phases are thinned
                      to about 30 hits per second so it stays a texture, not noise.
  * landing in bin -> pitch = a C-major chord tone for that bin (centre bin = C5). Loudness = landing speed,
                      so falls into empty bins ring out and landings on tall stacks are soft.
  * bell curve     -> a note as the curve is drawn across each bin, loudness = the curve's height there,
                      then a resolving C-major chord when it completes.
  * drain          -> a descending pentatonic run timed to the balls leaving the bins, ending as the loop restarts.
Usage: run galton.py (it calls score()). Standalone: python galton_sound.py [mallet|glass] -> out/galton.wav
"""
import json, os, sys
import numpy as np
from common import ease
import sound as S

def score(g, out_wav, variant="mallet"):
    DUR = g.DUR; SR = S.SR
    bus = S.Bus(DUR); rng = np.random.default_rng(11)
    ROOT = 523.25                                  # C5 = degree 0 (tonic) at the board's centre line
    def peg_note(d): return S.degree(int(np.clip(d, -7, 9)), ROOT)           # C4..E6, pentatonic
    TRIAD = [S.degree(k - 6, ROOT, S.MAJOR_TRIAD) for k in range(13)]       # bin k -> C-major chord tone
    if variant == "mallet":
        inst_peg = lambda f, v: S.marimba(f, v, 0.7)
        inst_land = lambda f, v: S.kalimba(f, v, 1.4)
        inst_arp = lambda f, v: S.marimba(f, v, 2.0)
    else:
        inst_peg = lambda f, v: S.glass(f, v, 0.9, 3.5, 1.2)
        inst_land = lambda f, v: S.glass(f, v, 1.8, 2.0, 1.0)
        inst_arp = lambda f, v: S.bell(f, v, 3.0)
    log = {"peg": [], "land": [], "arp": [], "drain": []}

    def speed(b, t, h=1e-3):
        p0, p1 = g.ball_pos(b, t - h), g.ball_pos(b, t + h)
        if p0 is None or p1 is None: return 0.0
        return float(np.hypot(p1[0] - p0[0], p1[1] - p0[1]) / (2 * h))

    # 1) peg hits
    hop_v = speed(0, g.emit[0] + g.ENTRY + 0.5 * g.T_HOP)
    emit_rate = lambda b: 1 / max(1e-3, np.median(np.diff(g.emit[max(0, b - 10):b + 1]))) if b > 0 else 1.0
    for b in range(g.N):
        early = b < 12
        keep_p = 1.0 if early else min(1.0, 30 / (emit_rate(b) * g.ROWS))
        for r in range(g.ROWS):
            if not early and rng.random() > keep_p: continue
            t = g.emit[b] + g.ENTRY + r * g.T_HOP
            j = int(g.steps[b, :r].sum()); x, _ = g.peg_xy(r, j)
            v = speed(b, t - 0.02) / hop_v
            vel = (0.9 if b == 0 else 0.35 if early else 0.07) * float(np.clip(v, 0.5, 1.3))
            bus.add(inst_peg(peg_note(2 * j - r), min(vel, 1.0)), t, 1.0, pan=(x - g.CX) / (6.5 * g.DX))
            if b == 0: log["peg"].append(round(t, 4))

    # 2) landings
    lands = []
    for b in np.argsort(g.land):
        t = g.land[b]
        if t > g.DRAIN0: continue
        k = g.k_final[b]; ys = g.Y0 + g.ROWS * g.DY - g.PEG_R - g.BALL_R; y1 = g.slot_xy(k, g.slot[b])[1]
        vland = np.sqrt(2 * g.G * (y1 - ys) + 260.0 ** 2)          # v0 + G*t at the landing
        lands.append((t, b, k, vland))
    vmax = max(l[3] for l in lands)
    for t, b, k, vl in lands:
        if b >= 30 and rng.random() > min(1.0, 18 / emit_rate(b)): continue
        vel = (0.8 if b < 30 else 0.22) * (vl / vmax) ** 0.8
        bus.add(inst_land(TRIAD[k], vel), t, 1.0, pan=(k - 6) / 7)
        if b < 30: log["land"].append(round(t, 4))

    # 3) bell curve reveal, same easing as the drawing in galton.py
    tt = np.linspace(19.2, 21.2, 4001); cp = np.array([ease((x - 19.2) / 2.0) for x in tt])
    for k in range(13):
        t = float(tt[np.searchsorted(cp, (k + 0.5) / 13)])
        h = np.exp(-(k - 6) ** 2 / (2 * 3.0))                # normal curve, variance 3 = 12 coin flips / 4
        bus.add(inst_arp(TRIAD[k] * (2 if TRIAD[k] < 400 else 1), 0.35 + 0.65 * h), t, 1.5, pan=(k - 6) / 7)
        log["arp"].append(round(t, 4))
    for f in (ROOT / 2, ROOT * 5 / 4 / 2, ROOT * 3 / 2 / 2, ROOT):   # resolving tonic chord
        bus.add(inst_arp(f, 0.6), 21.25, 1.1)

    # 4) drain: descending run at the quantiles of when balls actually leave the bins
    drain_t = np.array([g.DRAIN0 + (g.slot[b] / g.counts.max()) * 0.5 + abs(g.k_final[b] - 6) * 0.02 for b in range(g.N)])
    for i, t in enumerate(np.quantile(drain_t, np.linspace(0.02, 0.98, 14))):
        bus.add(inst_peg(S.degree(9 - i, ROOT), 0.45 - 0.015 * i), float(t), 1.0, pan=0.6 - 0.09 * i)
        log["drain"].append(round(float(t), 4))

    # master: reverb, fold the ring-out onto the start (seamless loop), -14 LUFS
    st = bus.stereo()
    st = S.wrap_tail(S.reverb(st, 0.16, 1.8), DUR)
    st = S.master(st, DUR, target=-14.1, wet=0.0, fade_ms=0)
    os.makedirs(os.path.dirname(out_wav) or ".", exist_ok=True)
    S.write_wav(out_wav, st)
    det = S.onsets(bus.stereo()[:int(SR * DUR)].mean(1), thresh=1.0)
    rep = dict(variant=variant, phone_energy_kept=round(S.phone_check(st), 3),
               sync_gold_ball=S.sync_report(np.array(log["peg"] + log["land"][:20]), det),
               events={k: len(v) for k, v in log.items()})
    print("  sound ->", out_wav, json.dumps(rep))
    return rep

if __name__ == "__main__":
    import galton as g
    g.setup(g.SEED)
    score(g, os.path.join("out", "galton.wav"), sys.argv[1] if len(sys.argv) > 1 else "mallet")
