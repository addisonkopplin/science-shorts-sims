"""Just-intonation scales and quantizers, so mapped data never produces clashing intervals."""
import numpy as np
SR = 44100
# ratios within one octave
MAJOR_PENTA = [1, 9/8, 5/4, 3/2, 5/3]                 # C D E G A
MINOR_PENTA = [1, 6/5, 4/3, 3/2, 9/5]                 # A C D E G
MAJOR = [1, 9/8, 5/4, 4/3, 3/2, 5/3, 15/8]
MAJOR_TRIAD = [1, 5/4, 3/2]                           # C E G
C4 = 261.63

def degree(d, root=C4, scale=MAJOR_PENTA):
    """frequency of scale degree d (int, may be negative) above root"""
    n = len(scale); o, i = divmod(int(d), n)
    return root * (2.0 ** o) * scale[i]

def degree_cont(x, root=C4, scale=MAJOR_PENTA):
    """continuous degree -> frequency, interpolating geometrically between neighbouring scale steps"""
    lo = np.floor(x); fr = x - lo
    f0 = np.vectorize(lambda d: degree(d, root, scale))(lo); f1 = np.vectorize(lambda d: degree(d, root, scale))(lo + 1)
    return f0 * (f1 / f0) ** fr

def snap_glide(x, smooth_s=0.06, fps=None, sr=SR, snap=0.85):
    """soft quantisation of a continuous degree track: pull toward nearest integer (snap 0..1),
    then one-pole smoothing (portamento). x sampled at sr."""
    q = np.round(x); y = x + snap * (q - x)
    a = np.exp(-1.0 / (smooth_s * sr)); out = np.empty_like(y); acc = y[0]
    # vectorised one-pole via lfilter-like recursion in blocks
    for i in range(len(y)):
        acc = a * acc + (1 - a) * y[i]; out[i] = acc
    return out
