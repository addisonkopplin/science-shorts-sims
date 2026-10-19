"""Generates the cat silhouette path used in the Short (our own drawing, made in code, no third-party image).
A hand-placed closed polygon (sitting cat seen from the front, tail curled to the right), softened with
2 rounds of Chaikin corner-cutting except at the two ear tips, which stay sharp.
Writes cat_path.npy (complex points, resampled uniformly by arc length) and cat_path.png.
Run: python3 cat_path.py"""
import numpy as np
P = [(30,0),(50,-1),(72,0),(88,2),(97,10),(99,21),(95,30),(92.5,22),(90,13),(84,7.5),(78,9),
     (80,20),(77,35),(70,47),(64,54),(68,60),(70,68),(69,77),(72,92),(61,83),
     (50,84.5),(39,83),(28,92),(31,77),(30,68),(32,60),(36,54),(30,47),(23,35),(20,20),(22,8)]
SHARP = {18, 22}  # ear tips
def chaikin(pts, sharp, rounds=2):
    pts = list(pts); sharp = set(sharp)
    for _ in range(rounds):
        out, ns = [], set()
        n = len(pts)
        for i in range(n):
            a, b = np.array(pts[i]), np.array(pts[(i+1) % n])
            if i in sharp:
                ns.add(len(out)); out.append(tuple(a))
            if i in sharp or (i+1) % n in sharp:
                # keep the corner: cut only on the far side
                out.append(tuple(0.75*a+0.25*b) if i in sharp else tuple(0.25*a+0.75*b))
            else:
                out += [tuple(0.75*a+0.25*b), tuple(0.25*a+0.75*b)]
        pts, sharp = out, ns
    return pts
pts = np.array(chaikin(P, SHARP))
z = pts[:,0] + 1j*pts[:,1]
def resample(z, M=4096):
    zc = np.append(z, z[0]); seg = np.abs(np.diff(zc)); cum = np.concatenate([[0], np.cumsum(seg)])
    s = np.arange(M)/M*cum[-1]; k = np.searchsorted(cum, s, side='right')-1
    return zc[k] + (zc[k+1]-zc[k])*(s-cum[k])/seg[k]
zz = resample(z)
zz = zz - zz.mean()
np.save('cat_path.npy', zz)
if __name__ == '__main__':
    from PIL import Image, ImageDraw
    W=600; im=Image.new('L',(W,W),0); d=ImageDraw.Draw(im)
    x=(zz.real-zz.real.min()); y=(zz.imag-zz.imag.min()); s=520/max(np.ptp(zz.real),np.ptp(zz.imag))
    xy=[(40+a*s, W-40-b*s) for a,b in zip(x,y)]; d.line(xy+[xy[0]], fill=255, width=3)
    im.save('cat_path.png'); print('points', len(pts), '-> resampled', len(zz))
