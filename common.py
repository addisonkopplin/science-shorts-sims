"""Shared video helpers: cairo frames piped to ffmpeg (H.264, yuv420p, 30 fps, 1080x1920 vertical),
easing, and captions kept inside the YouTube Shorts safe area. Sound lives in the sound/ package."""
import cairo, math, os, subprocess, numpy as np

W, H, FPS = 1080, 1920, 30
# Shorts safe area: keep key text out of top ~150px, bottom 25% (y>1440) and right ~140px (action buttons)
SAFE = dict(left=70, right=W - 150, top=170, bottom=1440)
CX = (SAFE['left'] + SAFE['right']) / 2  # 500
FONT = os.environ.get("SIMS_FONT", "Inter")   # any installed font works; cairo falls back if Inter is missing
BG = (0.043, 0.043, 0.063)
WHITE = (1, 1, 1)
ACCENT = (0.36, 0.52, 1.0)  # lighter variant of #1f3fbf so it reads on dark bg
GOLD = (1.0, 0.78, 0.25)

def ease(t):  # smoothstep 0..1
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)

def fade(t, a, b, d=0.35):
    """opacity of an element visible between a and b seconds with d-second fades"""
    if t < a or t > b: return 0.0
    return min(1.0, (t - a) / d, (b - t) / d)

class Writer:
    """Pipe raw BGRA frames into ffmpeg. Use: w = Writer("out.mp4"); c = w.ctx(); ...draw...; w.push(); w.close()"""
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
            "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
        self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    def ctx(self):
        c = cairo.Context(self.surf)
        c.set_source_rgb(*BG); c.paint()
        return c
    def push(self):
        self.surf.flush()
        self.p.stdin.write(bytes(self.surf.get_data()))
    def close(self):
        self.p.stdin.close(); self.p.wait()
        assert self.p.returncode == 0

def wrap(c, text, size, maxw, weight=cairo.FONT_WEIGHT_BOLD):
    c.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, weight); c.set_font_size(size)
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if c.text_extents(t).x_advance > maxw and cur:
                lines.append(cur); cur = w
            else: cur = t
        lines.append(cur)
    return lines

def text(c, s, y, size=72, alpha=1.0, color=WHITE, weight=cairo.FONT_WEIGHT_BOLD, x=None, maxw=None,
         align="center", lh=1.18, shadow=True):
    """draw wrapped text with top at y; returns bottom y"""
    if alpha <= 0: return y
    maxw = maxw or (SAFE['right'] - SAFE['left'])
    x = CX if x is None else x
    lines = wrap(c, s, size, maxw, weight)
    asc = c.font_extents()[0]
    for i, ln in enumerate(lines):
        ext = c.text_extents(ln)
        lx = x - ext.x_advance / 2 if align == "center" else x
        ly = y + asc + i * size * lh
        if shadow:
            c.set_source_rgba(0, 0, 0, 0.6 * alpha)
            for dx, dy in ((3, 3), (0, 3), (3, 0)):
                c.move_to(lx + dx, ly + dy); c.show_text(ln)
        c.set_source_rgba(*color, alpha); c.move_to(lx, ly); c.show_text(ln)
    return y + len(lines) * size * lh

def still(frame_fn, t, path):
    """render one frame at time t (seconds) to a PNG, for previews"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
    c.set_source_rgb(*BG); c.paint(); frame_fn(c, t); s.write_to_png(path)

def render_video(frame_fn, dur, path):
    """render frames 0..dur*FPS through frame_fn(ctx, t) into an H.264 file"""
    wr = Writer(path); n = int(dur * FPS)
    for f in range(n):
        frame_fn(wr.ctx(), f / FPS); wr.push()
        if f % FPS == 0: print(f"\r  video {f / FPS:4.0f} / {dur:.0f} s", end="", flush=True)
    wr.close(); print(f"\r  video {dur:.0f} / {dur:.0f} s -> {path}")
