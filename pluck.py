"""Synthesized sound design for the string art video (one pluck per thread line): Karplus-Strong plucks, a density shimmer, ticks and whooshes.
Everything is generated here from noise and sine waves (no samples), so there are no licensing questions.

Usage:
    from pluck import render_events, duck, master
    ev = [dict(t=1.20, v=0.4, pan=-0.3), dict(t=2.0, kind="tick"), dict(t=5.0, kind="whoosh")]
    sfx = render_events(ev, total_s=10)            # (N, 2) float32 at 48 kHz
    sfx = duck(sfx, voice_mono)                     # lower the effects while the voice speaks
Event fields: t (s), kind ("pluck" default, "tick", "whoosh"), v (0..1: pitch, 0 = low; e.g. a line's length mapped so
long lines are low), pan (-1..1), gain (linear, default 1).
When plucks come faster than max_rate per second, only some are kept (evenly) and the rest become a soft shimmer
whose level follows the rate, so very fast builds sound like a rising wash instead of noise.
CLI demo: python pluck.py out.wav   (12 slow plucks, then a very fast run that turns into a shimmer)
In the string art explainer, each line's pluck pitch follows its length: v = 1 - length / longest, so long
lines are low and short lines high.
"""
import numpy as np

SR = 48000
# A minor pentatonic over ~2.5 octaves (Hz): plucks always sound consonant together
SCALE = [110 * 2 ** (s / 12) for s in (0, 3, 5, 7, 10, 12, 15, 17, 19, 22, 24, 27, 29, 31)]
_cache = {}

def ks_pluck(freq, dur=1.6, sr=SR, decay=0.996, bright=0.5, seed=0):
    """Karplus-Strong string: a burst of filtered noise fed through a delay line with a lowpass average."""
    key = (round(freq, 2), dur, sr, decay, bright, seed)
    if key in _cache: return _cache[key]
    rng = np.random.default_rng(seed)
    N = max(2, int(round(sr / freq))); total = int(dur * sr)
    burst = rng.uniform(-1, 1, N)
    # soften the excitation: lower 'bright' = more lowpass = rounder, softer pluck
    for _ in range(int(1 + (1 - bright) * 4)): burst = 0.5 * (burst + np.roll(burst, 1))
    out = np.zeros(total + N + 1); out[:N] = burst
    i = N
    while i < total:  # process one period at a time (vectorized inside the period)
        j = min(i + N, total)
        seg = out[i - N:j - N + 1]
        out[i:j] = decay * 0.5 * (seg[:-1] + seg[1:]) if len(seg) > 1 else 0
        i = j
    y = out[:total]
    env = np.minimum(1, np.arange(total) / (0.002 * sr))         # 2 ms attack, no click
    y = y * env * np.exp(-np.arange(total) / (sr * dur * 0.35))   # extra fade so tails stay short
    y /= (np.abs(y).max() + 1e-9)
    _cache[key] = y.astype(np.float32); return _cache[key]

def tick(sr=SR):
    t = np.arange(int(0.05 * sr)) / sr
    return (np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 90) * 0.6).astype(np.float32)

def whoosh(dur=0.7, sr=SR, seed=1):
    rng = np.random.default_rng(seed); n = int(dur * sr)
    x = rng.standard_normal(n)
    # sweep a one-pole lowpass from dark to bright and back
    t = np.linspace(0, 1, n); fc = 300 + 3500 * np.sin(np.pi * t) ** 2
    a = np.exp(-2 * np.pi * fc / sr); y = np.zeros(n); s = 0.0
    for k in range(n): s = a[k] * s + (1 - a[k]) * x[k]; y[k] = s
    y *= np.sin(np.pi * t) ** 2
    return (y / (np.abs(y).max() + 1e-9) * 0.5).astype(np.float32)

def _place(buf, x, at, gain, pan):
    i = int(at * SR)
    if i >= len(buf): return
    x = x[:len(buf) - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * gain * l; buf[i:i + len(x), 1] += x * gain * r

def render_events(events, total_s, max_rate=9.0, pluck_gain=0.35, shimmer_gain=0.10, window=0.5):
    buf = np.zeros((int(total_s * SR) + SR, 2), np.float32)
    pl = sorted([e for e in events if e.get("kind", "pluck") == "pluck"], key=lambda e: e["t"])
    ts = np.array([e["t"] for e in pl]) if pl else np.zeros(0)
    # local rate (plucks per second) around each pluck
    rate = np.array([((ts > t - window / 2) & (ts <= t + window / 2)).sum() / window for t in ts]) if len(ts) else ts
    acc = 0.0
    for e, r in zip(pl, rate):
        keep = 1.0 if r <= max_rate else max_rate / r
        acc += keep
        if acc < 1.0: continue   # evenly thin out dense passages
        acc -= 1.0
        v = float(np.clip(e.get("v", 0.5), 0, 1)); f = SCALE[int(round(v * (len(SCALE) - 1)))]
        g = pluck_gain * e.get("gain", 1.0) * (1.0 if r <= max_rate else 0.6)
        _place(buf, ks_pluck(f, bright=0.35 + 0.3 * v, seed=int(e["t"] * 1000) % 7), e["t"], g, e.get("pan", 0.0))
    # shimmer bed: level follows the pluck rate above max_rate; pitch of its partials rises slowly with density
    if len(ts):
        n = len(buf); tt = np.arange(n) / SR
        dens = np.zeros(n); idx = (ts * SR).astype(int); idx = idx[idx < n]
        np.add.at(dens, idx, 1.0)
        k = int(window * SR); dens = np.convolve(dens, np.ones(k) / window, mode="same")
        lvl = np.clip((dens - max_rate) / (8 * max_rate), 0, 1) ** 0.6
        sm = int(0.15 * SR); lvl = np.convolve(lvl, np.ones(sm) / sm, mode="same")
        if lvl.max() > 0:
            rise = 1 + 0.5 * lvl
            sh = np.zeros(n)
            for m, f in enumerate((880, 1318.5, 1760, 2637)):
                ph = 2 * np.pi * np.cumsum(f * rise) / SR
                sh += np.sin(ph + m) * (0.6 ** m) * (0.75 + 0.25 * np.sin(2 * np.pi * (5 + m) * tt))
            sh = sh / 2.2 * lvl * shimmer_gain
            buf[:, 0] += sh.astype(np.float32); buf[:, 1] += np.roll(sh, 240).astype(np.float32)
    for e in events:
        if e.get("kind") == "tick": _place(buf, tick(), e["t"], 0.25 * e.get("gain", 1.0), e.get("pan", 0.0))
        elif e.get("kind") == "whoosh": _place(buf, whoosh(e.get("dur", 0.7)), e["t"] - e.get("dur", 0.7) / 2, 0.22 * e.get("gain", 1.0), 0.0)
    return buf[:int(total_s * SR)]

def duck(sfx, voice, depth_db=10.0, attack=0.05, release=0.35, thresh=0.01):
    """Lower sfx by depth_db while the (mono, same rate) voice is active."""
    v = np.abs(voice[:len(sfx)]); v = np.pad(v, (0, len(sfx) - len(v)))
    w = int(0.02 * SR); env = np.sqrt(np.convolve(v ** 2, np.ones(w) / w, mode="same"))
    act = (env > thresh).astype(np.float32)
    g = np.empty_like(act); a = np.exp(-1 / (attack * SR)); r = np.exp(-1 / (release * SR)); s = 0.0
    for i in range(len(act)):  # smooth gate
        c = a if act[i] > s else r; s = c * s + (1 - c) * act[i]; g[i] = s
    gain = 10 ** (-depth_db * g / 20)
    return sfx * gain[:, None]

def write_wav(path, st):
    """16-bit stereo WAV with the standard library"""
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    import sys
    ev = [dict(t=0.3 + 0.35 * i, v=i / 12, pan=np.sin(i)) for i in range(12)]
    ev += [dict(t=5 + i * 0.01, v=(i * 37 % 100) / 100) for i in range(400)]  # very fast run -> thinned + shimmer
    ev += [dict(t=4.6, kind="whoosh"), dict(t=10, kind="tick")]
    out = sys.argv[1] if len(sys.argv) > 1 else "pluck-demo.wav"
    write_wav(out, render_events(ev, 11)); print("wrote", out)
