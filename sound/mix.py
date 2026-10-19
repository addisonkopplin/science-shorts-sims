"""Stereo bus, equal-power panning, convolution reverb, spectral EQ, limiter, mastering, checks."""
import numpy as np, subprocess, json, wave, tempfile, os
SR = 44100

def pan_gains(p):
    """equal-power pan, p in [-1, 1]"""
    a = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.cos(a), np.sin(a)

class Bus:
    def __init__(self, dur): self.L = np.zeros(int(SR * dur) + SR * 4); self.R = np.zeros_like(self.L); self.dur = dur
    def add(self, sig, at, gain=1.0, pan=0.0):
        n = int(round(at * SR))
        if n < 0 or n >= len(self.L): return
        m = min(len(sig), len(self.L) - n); gl, gr = pan_gains(pan)
        self.L[n:n + m] += gain * gl * sig[:m]; self.R[n:n + m] += gain * gr * sig[:m]
    def add_track(self, sig, pan_track=None, gain=1.0):
        """continuous signal starting at 0 with optional per-sample pan"""
        m = min(len(sig), len(self.L))
        gl, gr = pan_gains(pan_track[:m] if pan_track is not None else 0.0)
        self.L[:m] += gain * gl * sig[:m]; self.R[:m] += gain * gr * sig[:m]
    def stereo(self): return np.stack([self.L, self.R], 1)

def _fftconv(x, h):
    n = len(x) + len(h) - 1; N = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(h, N), N)[:len(x)]

def synth_ir(rt60=2.0, predelay=0.012, damp_hz=5000, seed=5):
    """synthetic stereo room IR: decorrelated noise, exponential decay, HF damping that increases over time"""
    rng = np.random.default_rng(seed); n = int(SR * rt60 * 1.2); t = np.arange(n) / SR
    irs = []
    for ch in range(2):
        x = rng.standard_normal(n) * np.exp(-6.91 * t / rt60)
        # time-varying lowpass approximated by blending with a smoothed copy
        k = max(1, int(SR / damp_hz)); sm = np.convolve(x, np.ones(k * 3) / (k * 3), "same")
        w = np.clip(t / (rt60 * 0.5), 0, 1); x = (1 - w) * x + w * sm
        x = np.concatenate([np.zeros(int(predelay * SR)), x]); irs.append(x / np.sqrt((x ** 2).sum()))
    return irs

def reverb(st, wet=0.18, rt60=2.0):
    irs = synth_ir(rt60)
    out = st.copy()
    for ch in range(2):
        out[:, ch] = st[:, ch] + wet * _fftconv(st[:, ch], irs[ch]) * 3.0
    return out

def eq(st, hp=60.0, dip_hz=3500, dip_db=-3.0, dip_q=1.0, lp=12000):
    """zero-phase spectral EQ on the whole buffer: highpass, gentle presence dip (2-5 kHz), soft top lowpass"""
    out = np.empty_like(st)
    for ch in range(2):
        X = np.fft.rfft(st[:, ch]); f = np.fft.rfftfreq(len(st), 1 / SR)
        g = 1 / np.sqrt(1 + (hp / np.maximum(f, 1e-3)) ** 4)
        g *= 10 ** (dip_db / 20 * np.exp(-0.5 * (np.log2(np.maximum(f, 1) / dip_hz) / (dip_q * 0.7)) ** 2))
        g *= 1 / np.sqrt(1 + (f / lp) ** 4)
        out[:, ch] = np.fft.irfft(X * g, len(st))
    return out

def highpass(st, fc):
    out = np.empty_like(st)
    for ch in range(st.shape[1]):
        X = np.fft.rfft(st[:, ch]); f = np.fft.rfftfreq(len(st), 1 / SR)
        out[:, ch] = np.fft.irfft(X / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** 8), len(st))
    return out

def limit(st, ceiling=0.7, look=0.005, release=0.1):
    from numpy.lib.stride_tricks import sliding_window_view as swv
    peak = np.abs(st).max(1)
    need = np.minimum(1.0, ceiling / np.maximum(peak, 1e-9))
    L = int(look * SR); p = np.pad(need, (L, L), constant_values=1.0); g = swv(p, 2 * L + 1).min(1)
    c = np.cumsum(np.pad(g, (L, 0), constant_values=g[0])); g = (c[L:] - c[:-L]) / L
    a = np.exp(-1 / (release * SR)); out = np.empty_like(g); cur = 1.0
    for i in range(len(g)):
        cur = g[i] if g[i] < cur else a * cur + (1 - a) * g[i]; out[i] = cur
    return np.clip(st * out[:, None], -ceiling, ceiling)

def write_wav(path, st):
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())

def read_wav(path):
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, w.getnchannels()) / 32767.0
    return x

def ebur(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    tail = r[r.rindex("Summary"):]
    I = float(tail.split("I:")[1].split("LUFS")[0]); TP = float(tail.split("Peak:")[1].split("dBFS")[0])
    return I, TP

def _lufs(st):
    fd, tmp = tempfile.mkstemp(suffix=".wav"); os.close(fd); write_wav(tmp, st)
    I, _ = ebur(tmp); os.remove(tmp); return I

def master(st, dur, target=-14.0, ceiling=0.72, wet=0.18, rt60=2.0, fade_ms=4):
    st = reverb(st, wet, rt60)
    st = eq(st)
    st = st[:int(SR * dur)]
    g = 1.0
    for _ in range(4):
        y = limit(st * g, ceiling); I = _lufs(y); g *= 10 ** ((target - I) / 20)
    y = limit(st * g, ceiling)
    f = int(fade_ms / 1000 * SR)
    if f > 0: y[:f] *= np.linspace(0, 1, f)[:, None]
    if f > 0: y[-f:] *= np.linspace(1, 0, f)[:, None]
    return y

def wrap_tail(st, dur):
    """fold audio that rings past the loop point back onto the start, so the loop seam is continuous"""
    n = int(SR * dur); head = st[:n].copy(); tail = st[n:]
    m = min(len(tail), n); head[:m] += tail[:m]
    return head

def mux(video, wav, out):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "aresample=48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out], check=True)

def phone_check(st):
    """simulate a phone speaker (200 Hz highpass): fraction of energy kept"""
    hp = highpass(st, 200.0)
    return float((hp ** 2).sum() / max(1e-12, (st ** 2).sum()))

def onsets(mono, hop=256, thresh=None):
    """spectral-flux onset times (s) for sync verification"""
    win = 1024; n = (len(mono) - win) // hop
    frames = np.lib.stride_tricks.sliding_window_view(mono, win)[::hop][:n] * np.hanning(win)
    S = np.abs(np.fft.rfft(frames, axis=1)); S = np.log1p(100 * S)
    flux = np.maximum(0, np.diff(S, axis=0)).sum(1)
    flux = (flux - np.median(flux)) / (flux.std() + 1e-9)
    th = 1.5 if thresh is None else thresh
    pk = [i for i in range(1, len(flux) - 1) if flux[i] > th and flux[i] >= flux[i - 1] and flux[i] > flux[i + 1]]
    return (np.array(pk) + 1) * hop / SR + win / 2 / SR * 0  # frame start convention

def sync_report(expected, detected, tol=0.03):
    """median |error| of each expected onset to its nearest detected onset; fraction within tol"""
    if len(detected) == 0: return dict(n=len(expected), hit=0.0)
    d = np.array([np.min(np.abs(detected - e)) for e in expected])
    return dict(n=len(expected), median_ms=float(np.median(d) * 1000), within_tol=float((d < tol).mean()))
