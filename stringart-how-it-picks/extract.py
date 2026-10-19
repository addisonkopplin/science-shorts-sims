"""Numbers for the 'how it picks' Short (fact-check fix: LoC scan, public repo at commit 209877c).
Input: solve/trace-loc.json, written by solve/solve_loc.js, which runs the UNMODIFIED public String Art Maker
core.js at commit 209877cbecb0a351b38da0a4d9dd42d4c57df96d (md5-checked) on the worker input the Maker page sent
for the Library of Congress Einstein scan, checks the order against the page's own result, then re-runs it with
read-only hooks (order asserted identical) to record per-line RMS, candidate scores and a scan at the stop.
Candidate score d = the solver's linearised change in its own weighted error if that line were added
(negative = helps by its own score). The score includes the highlight weight, the detail term and a crowding charge.
Step 0 is skipped: the first line is chosen by bestAnywhere() over every nail.
Every number below is computed here from the trace; nothing is typed in. Run: python3 extract.py"""
import json, math, os
from collections import Counter
here = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(here, 'solve', 'trace-loc.json')))
order, rms, cand, D = T['order'], T['rms'], T['cand'], T['dead']
n, skip, lines = T['n'], T['skip'], len(order) - 1
print(f"core.js commit {T['commit']} (md5 {T['coreMd5']}); photo {T['photo']}")
print(f"Maker page status: {T['pageStatus']}")
print(f"pristine re-run order identical to the Maker page's order: {T['hashMatch']}; solver-only time {T['solverMs']:.0f} ms (node, setup excluded)")
print(f"nails={n}, skip={skip} (pair usable if > {skip} apart => {n - 1 - 2 * skip} usable partners per nail), grid={T['w']}x{T['h']}, max lines {T['maxLines']}")
print(f"nail sequence length={len(order)} (=> {lines} lines); first 11 nails: {order[:11]}; last nail: {order[-1]}")
print(f"RMS lightness gap (L*, inside the nail circle): start {rms[0]:.2f}, end {rms[-1]:.2f}")
for k in (1, 10, 100, 500, 800, 1000, 2000, lines):
    print(f"  after line {k}: RMS {rms[k]:.2f}")
ups = [i for i in range(1, len(rms)) if rms[i] > rms[i - 1] + 1e-9]
print(f"lines where the RMS gap rose: {len(ups)} of {lines}" + (f" (first few: {ups[:10]})" if ups else ""))

def used_at(step):
    cur = order[step]; used = set()
    for a, b in zip(order[:step], order[1:step + 1]):
        if cur in (a, b): used.add(b if a == cur else a)
    return cur, used, order[step - 1]
print("\n# candidates per step (by the solver's own score)")
helpers = {}
for s in sorted(int(k) for k in cand if k != '0' and int(k) < lines):
    c = cand[str(s)]; d = c['d']; m = len(d); neg = sum(v < 0 for v in d.values())
    cur, used, prev = used_at(s); expect = (n - 1 - 2 * skip) - len(used) - (0 if prev in used else 1)
    assert c['from'] == cur and m == expect, (s, c['from'], cur, m, expect)
    best = min(d, key=d.get); assert int(best) == order[s + 1], (s, best, order[s + 1])
    helpers[s] = (cur, m, neg)
    if s <= 11 or s % 100 == 0:
        print(f"step {s:4d}: from nail {cur:3d}, partners already used {len(used):2d}, candidates {m} (expected {expect}), help {neg}, hurt {m - neg}, best -> nail {best}")
allhelp = [s for s, (_, m, neg) in helpers.items() if neg == m]
print(f"steps where every candidate helped: {len(allhelp)} of {len(helpers)}; last such step: {max(allhelp)}")
lo = min(m for _, m, _ in helpers.values()); hi = max(m for _, m, _ in helpers.values())
print(f"candidates per step ranged {lo}-{hi} over {len(helpers)} steps")

print("\n# the stop (scan at the moment the loop breaks, same state the solver saw)")
print(f"stopped after line {lines} of a {T['maxLines']} limit, on nail {D['cur']} (came from nail {D['prev']}); last nail in order = {order[-1]}: {D['cur'] == order[-1]}")
print(f"unused lines from nail {D['cur']}: {D['linesFromCur']}; helping by its own score: {D['helpFromCurByScore']}; "
      f"lowering the plain lightness error (no weights, no crowding charge): {D['helpFromCurByPlainLightness']}")
print(f"unused lines on the whole board: {D['unused']}; helping by its own score elsewhere: {D['helpElsewhereByScore']}; "
      f"lowering plain lightness error anywhere: {D['helpAnywhereByPlainLightness']}; best score anywhere {D['bestScoreAnywhere']:.1f}")

print("\n# first ten lines")
arcs = sorted(set(order[:11])); print(f"nails touched by lines 1-10: {arcs}")
u, v, F = T['layout']['u'], T['layout']['v'], T['frameMM']
L = sum(math.hypot((u[a] - u[b]) * F, (v[a] - v[b]) * F) for a, b in zip(order, order[1:])) / 1000
print(f"\n# thread: sum of the {lines} chord lengths on a {F / 10:.0f} cm frame = {L:.1f} m; with the Maker's +10% = {L * 1.1:.1f} m")
cnt = Counter(order); print(f"distinct nails used: {len(cnt)} of {n}; most-used nail appears {cnt.most_common(1)[0][1]} times")

# build stages (solve/render_stages.js, the Maker's SA.render) -> build_stages.png, first10.png
try:
    import numpy as np; from PIL import Image, ImageDraw
    S = json.load(open(os.path.join(here, 'solve', 'stages.json'))); s = S['S']; at = S['at']
    a = np.fromfile(os.path.join(here, 'solve', 'stages.raw'), np.uint8).reshape(len(at), s, s)
    if at[-1] != lines: print(f"WARNING: stages rendered to {at[-1]}, order has {lines}")
    strip = Image.new('L', (s * len(at), s + 40), 255); dr = ImageDraw.Draw(strip)
    for i, k in enumerate(at): strip.paste(Image.fromarray(a[i]), (i * s, 40)); dr.text((i * s + 10, 12), f"{k} lines", fill=0)
    strip.save(os.path.join(here, 'build_stages.png')); Image.fromarray(a[0]).save(os.path.join(here, 'first10.png'))
    print(f"wrote build_stages.png ({', '.join(map(str, at))} lines) and first10.png")
except FileNotFoundError:
    print("stages not rendered (run node solve/render_stages.js)")
