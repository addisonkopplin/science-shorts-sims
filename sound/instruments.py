"""Instruments. All return mono float arrays at SR (peak ~1 at vel=1). Soft attacks (>=2 ms), warm partials,
and energy kept mostly below ~4 kHz (ear is most sensitive 2-5 kHz; harsh there)."""
import numpy as np
SR = 44100
_cache = {}

def _t(dur): return np.arange(int(SR * dur)) / SR

def _attack(n, ms):
    a = int(SR * ms / 1000); e = np.ones(n)
    if a > 1: e[:a] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))
    return e

def modal(freq, ratios, amps, decays, dur, vel=1.0, attack_ms=2.0, bright_vel=True):
    """sum of exponentially decaying sinusoids (modal synthesis). Velocity also brightens (harder mallet)."""
    key = ("m", round(freq, 2), tuple(ratios), tuple(amps), tuple(decays), dur, round(vel, 2), attack_ms)
    if key in _cache: return _cache[key]
    t = _t(dur); s = np.zeros_like(t)
    for k, (r, a, d) in enumerate(zip(ratios, amps, decays)):
        f = freq * r
        if f > 9000: continue
        ak = a * (vel ** (0.5 * k) if bright_vel else 1.0)
        ak *= 1.0 if f < 3000 else (3000 / f) ** 1.5        # tame 3-9 kHz
        s += ak * np.sin(2 * np.pi * f * t) * np.exp(-t * d)
    s *= _attack(len(t), attack_ms) * vel
    s /= max(1.0, np.abs(s).max() / max(vel, 1e-3))
    _cache[key] = s
    return s

def marimba(freq, vel=1.0, dur=1.2):
    # tuned marimba bar: 2nd mode tuned 2 octaves up (4:1), 3rd near 10:1 (Rossing, Science of Percussion Instruments)
    return modal(freq, [1, 4.0, 9.9], [1, 0.25, 0.06], [3.2 + freq / 400, 14, 30], dur, vel, attack_ms=2.5)

def kalimba(freq, vel=1.0, dur=1.6):
    # cantilever tine: inharmonic overtone near 6.27x (clamped-free beam), short-lived; plus a soft 2x
    return modal(freq, [1, 2.0, 6.27], [1, 0.12, 0.10], [2.2, 6, 22], dur, vel, attack_ms=3)

def glass(freq, vel=1.0, dur=2.0, ratio=3.5, index=1.6):
    """FM glass/crystal (Chowning 1973): carrier f, modulator ratio*f, decaying index -> bright start, pure tail"""
    key = ("g", round(freq, 2), round(vel, 2), dur, ratio, index)
    if key in _cache: return _cache[key]
    t = _t(dur); I = index * vel * np.exp(-t * 6)
    s = np.sin(2 * np.pi * freq * t + I * np.sin(2 * np.pi * freq * ratio * t)) * np.exp(-t * 1.6)
    s += 0.3 * np.sin(2 * np.pi * 2 * freq * t) * np.exp(-t * 3)
    s *= _attack(len(t), 3) * vel / 1.3
    _cache[key] = s
    return s

def bell(freq, vel=1.0, dur=3.0):
    """FM bell with irrational (golden) ratio -> inharmonic, Chowning-style; long decay"""
    return glass(freq, vel, dur, ratio=1.618, index=2.2)

def ks_pluck(freq, vel=1.0, dur=1.5, damp=0.5, decay=0.996):
    """refined Karplus-Strong: lowpassed excitation, fractional delay (linear interp) for accurate tuning"""
    key = ("ks", round(freq, 2), round(vel, 2), dur, damp, decay)
    if key in _cache: return _cache[key]
    rng = np.random.default_rng(int(freq * 10))
    n = int(SR * dur); P = SR / freq; p = int(P); frac = P - p
    exc = rng.uniform(-1, 1, p + 2)
    for _ in range(int(2 + damp * 6)): exc = 0.5 * (exc + np.roll(exc, 1))
    y = np.zeros(n + p + 2); y[:p + 2] = exc
    for i in range(p + 2, n + p + 2):
        a = y[i - p - 1] * frac + y[i - p] * (1 - frac)
        b = y[i - p - 2] * frac + y[i - p - 1] * (1 - frac)
        y[i] = decay * 0.5 * (a + b)
    s = y[p + 2:]; s = s / max(1e-9, np.abs(s).max()) * vel * _attack(n, 2)
    _cache[key] = s
    return s

def soft_tick(freq=1200, vel=1.0, dur=0.06):
    """woody tick: two damped partials, 1.5 ms attack, no broadband noise"""
    return modal(freq, [1, 2.76], [1, 0.3], [70, 120], dur, vel, attack_ms=1.5, bright_vel=False)

def voice(freq_track, amp_track, bright_track, kind="warm", nh=8, phase=None):
    """continuous voice following per-sample frequency/amp/brightness arrays.
    warm: additive harmonics with weights bright^k (k>=1), hard-capped at 4.5 kHz.
    glass: FM with modulator 2x carrier (harmonic), index = 2*bright -> brightness tracks energy."""
    ph = 2 * np.pi * np.cumsum(freq_track) / SR if phase is None else phase
    if kind == "glass":
        s = np.sin(ph + 2.0 * bright_track * np.sin(2 * ph)) * 0.8 + 0.2 * np.sin(0.5 * ph + 0.3)
    else:
        s = np.sin(ph)
        for k in range(2, nh + 1):
            w = bright_track ** (k - 1) / k * (freq_track * k < 4500)
            s += w * np.sin(k * ph)
        s *= 0.7
    return s * amp_track

def pad(freqs, dur, amp=1.0, attack=1.5, release=1.5, bright=0.25):
    t = _t(dur); env = np.minimum(1, t / attack) * np.minimum(1, (dur - t) / release)
    s = np.zeros_like(t)
    for i, f in enumerate(freqs):
        for det in (0.999, 1.0015):
            ph = 2 * np.pi * f * det * t + i
            s += np.sin(ph) + bright * np.sin(2 * ph) + bright ** 2 * np.sin(3 * ph)
    return amp * env * s / (2 * len(freqs))
