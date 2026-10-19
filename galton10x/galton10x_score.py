"""science-03 score: discrete event sounds driven by galton10x.py (no music bed, no sustained tones)."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))  # repo root: common.py, sound/
import galton10x as g
from common import ease
import sound as S

DUR = g.DUR; bus = S.Bus(DUR); rng = np.random.default_rng(11)
ROOT = 523.25
def peg_note(d): return S.degree(int(np.clip(d, -7, 9)), ROOT)
TRIAD = [S.degree(k - 6, ROOT, S.MAJOR_TRIAD) for k in range(13)]
log = {k: [] for k in ("peg", "land", "streak", "near", "arp", "final_peg", "final", "hit")}
emit_rate = lambda b: 1 / max(1e-3, np.median(np.diff(g.emit[max(0, b - 10):b + 1]))) if b > 0 else 1.0

# 1) random balls: peg hits (pitch = horizontal position), thinned to ~30 hits/s in the dense phase
for b in range(g.N):
    early = b < 14
    keep = 1.0 if early else min(1.0, 30 / (emit_rate(b) * g.ROWS))
    for r in range(g.ROWS):
        if not early and rng.random() > keep: continue
        t = g.emit[b] + g.ENTRY + r * g.T_HOP; j = int(g.steps[b, :r].sum()); x, _ = g.peg_xy(r, j)
        vel = 0.75 if b == 0 else 0.32 if early else 0.07
        bus.add(S.marimba(peg_note(2 * j - r), vel, 0.7), t, 1.0, pan=(x - g.CX) / (6.5 * g.DX))
        if early: log["peg"].append(round(t, 3))
# 2) landings (pitch = bin)
for b in np.argsort(g.land):
    if b >= 30 and rng.random() > min(1.0, 16 / emit_rate(b)): continue
    k = g.k_final[b]; vel = 0.7 if b < 30 else 0.2
    bus.add(S.kalimba(TRIAD[k], vel, 1.4), g.land[b], 1.0, pan=(k - 6) / 7)
    if b < 30: log["land"].append(round(float(g.land[b]), 3))
# 3) streaks: once a ball has gone the same way 7+ times, each further same-way bounce gets a rising glass note
for b in np.where(g.RUN >= 7)[0]:
    side = -1 if g.steps[b, 0] == 0 else 1
    for L in range(7, g.RUN[b] + 1):
        t = g.emit[b] + g.ENTRY + (L - 1) * g.T_HOP
        bus.add(S.glass(S.degree(L - 2, ROOT), 0.22 + 0.04 * (L - 7), 0.9), t, 1.0, pan=0.7 * side)
        log["streak"].append(round(float(t), 3))
# 4) near misses (landed one bin from the edge): soft falling two-note figure
for b in g.NEAR:
    t = float(g.land[b]); side = -0.8 if g.k_final[b] == 1 else 0.8
    bus.add(S.marimba(S.degree(3, ROOT), 0.5, 0.8), t, 1.0, pan=side)
    bus.add(S.marimba(S.degree(1, ROOT), 0.42, 1.0), t + 0.16, 1.0, pan=side)
    log["near"].append(round(t, 3))
# 5) bell-curve reveal (as v3)
tt = np.linspace(g.CURVE_T, g.CURVE_T + 2, 4001); cp = np.array([ease((x - g.CURVE_T) / 2.0) for x in tt])
for k in range(13):
    t = float(tt[np.searchsorted(cp, (k + 0.5) / 13)]); h = np.exp(-(k - 6) ** 2 / 6.0)
    bus.add(S.marimba(TRIAD[k] * (2 if TRIAD[k] < 400 else 1), 0.3 + 0.55 * h, 2.0), t, 1.0, pan=(k - 6) / 7)
    log["arp"].append(round(t, 3))
# 6) final ball: each peg = marimba at its position + a kalimba note that climbs with the streak count
for r, t in enumerate(g.FB_PEG):
    x, _ = g.peg_xy(r, 0); pan = (x - g.CX) / (6.5 * g.DX)
    bus.add(S.marimba(peg_note(-r), 0.6 + 0.03 * r, 1.0), t, 1.0, pan=pan)
    bus.add(S.kalimba(S.degree(r, ROOT / 2), 0.35 + 0.04 * r, 1.4), t, 1.0, pan=pan)
    log["final_peg"].append(round(t, 3))
bus.add(S.kalimba(TRIAD[0], 0.8, 1.6), g.FB_LAND, 1.0, pan=-0.8); log["final"].append(round(g.FB_LAND, 3))
bus.add(S.soft_tick(520, 0.9, 0.08), g.DOOR, 1.0, pan=-0.8); log["final"].append(round(g.DOOR, 3))
# chute: soft wooden ticks where the ball meets the bends of the tube
for frac in (0.25, 0.55, 0.8):
    d = frac * g.PATH_LEN; t = g.DOOR + 0.12 + np.sqrt(2 * d / g.G2)
    bus.add(S.soft_tick(700 + 300 * frac, 0.5, 0.06), float(t), 1.0, pan=-0.5 + 0.6 * frac); log["final"].append(round(float(t), 3))
# caption beats in the quiet stretch: '0 on the edge' (both edge bins), then the last ball is let go
for p in (-0.85, 0.85): bus.add(S.glass(S.degree(0, ROOT), 0.3, 1.2), 47.95, 1.0, pan=p)
bus.add(S.kalimba(S.degree(4, ROOT), 0.45, 1.4), g.FB0, 1.0)
# 7) 10x hit: one strike (bell + C-major tine chord + low marimba), then a quick sparkle run as the sparks fly
H = g.FB_HIT
bus.add(S.bell(ROOT, 0.8, 3.0), H, 1.0)
for f in (ROOT / 2, ROOT * 5 / 8, ROOT * 3 / 4, ROOT):
    bus.add(S.kalimba(f, 0.75, 2.0), H, 1.0)
bus.add(S.marimba(ROOT / 4, 0.9, 1.5), H, 1.0)
for i in range(8):
    bus.add(S.glass(S.degree(5 + i, ROOT), 0.4 - 0.035 * i, 1.0), H + 0.06 + 0.055 * i, 1.0, pan=-0.6 + 0.17 * i)
log["hit"].append(round(H, 3))

st = bus.stereo()
st = S.reverb(st, 0.16, 1.8)
st = S.master(st, DUR, target=-14.1, wet=0.0, fade_ms=30)
out = "build/science-03"; os.makedirs("out", exist_ok=True)
S.write_wav(out + ".wav", st)
S.mux("build/science-03.video.mp4", out + ".wav", "out/science-03.mp4")
I, TP = S.ebur("out/science-03.mp4")
rep = dict(LUFS=I, true_peak_dBTP=TP, phone_energy_kept=round(S.phone_check(st), 3), events={k: len(v) for k, v in log.items()})
json.dump(dict(rep, log=log), open(out + ".sync.json", "w"), indent=1)
print(json.dumps(rep, indent=1))
