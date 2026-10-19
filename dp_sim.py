import numpy as np
g, L = 9.81, 1.0
def deriv(s):
    t1, t2, w1, w2 = s
    d = t1 - t2
    den = 3 - np.cos(2 * d)   # (2m1+m2 - m2 cos(2d)), m1=m2=1
    a1 = (-3 * g * np.sin(t1) - g * np.sin(t1 - 2 * t2) - 2 * np.sin(d) * (w2**2 * L + w1**2 * L * np.cos(d))) / (L * den)
    a2 = (2 * np.sin(d) * (2 * w1**2 * L + 2 * g * np.cos(t1) + w2**2 * L * np.cos(d))) / (L * den)
    return np.array([w1, w2, a1, a2])
def energy(s):
    t1, t2, w1, w2 = s  # m=1, L=1
    T = 0.5 * (2 * w1**2 + w2**2 + 2 * w1 * w2 * np.cos(t1 - t2))
    V = -g * (2 * np.cos(t1) + np.cos(t2))
    return T + V
def simulate(th0, eps_total, n, dur, fps=30, sub=40, tscale=1.0):
    off = np.linspace(0, eps_total, n)
    s = np.array([np.full(n, th0), th0 + off, np.zeros(n), np.zeros(n)])
    dt = tscale / fps / sub
    out = [s.copy()]
    for f in range(int(dur * fps)):
        for _ in range(sub):
            k1 = deriv(s); k2 = deriv(s + dt / 2 * k1); k3 = deriv(s + dt / 2 * k2); k4 = deriv(s + dt * k3)
            s = s + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        out.append(s.copy())
    return np.array(out)  # frames x 4 x n
if __name__ == "__main__":
    import sys
    for th0 in (2.0, 2.4):
        for eps in (1e-6, 1e-5, 1e-4):
            tr = simulate(th0, eps, 200, 32, sub=20)
            # spread of tip positions
            x = np.sin(tr[:, 0]) + np.sin(tr[:, 1]); y = -np.cos(tr[:, 0]) - np.cos(tr[:, 1])
            spread = np.hypot(x.std(1), y.std(1))
            t_div = [next((i / 30 for i, v in enumerate(spread) if v > thr), None) for thr in (0.05, 0.3, 0.8)]
            E = energy(tr[:, :, 0].T); print(th0, eps, "div times", t_div, "energy drift", float(E.max() - E.min()))
