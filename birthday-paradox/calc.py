"""Birthday problem: exact probabilities (365 equally likely days, Feb 29 ignored) + a seeded simulation.
Run: python3 calc.py"""
from fractions import Fraction
from math import comb
import random

def p_shared(n, days=365):
    q = Fraction(1)
    for k in range(n):
        q *= Fraction(days - k, days)
    return 1 - q

for n in (10, 20, 22, 23, 30, 40, 50, 57, 60, 70, 75, 100):
    p = p_shared(n)
    print(f"n={n:3d}: P(at least one shared birthday) = {float(p):.6f}  ({float(p):.1%})")
first50 = next(n for n in range(1, 366) if p_shared(n) > Fraction(1, 2))
first99 = next(n for n in range(1, 366) if p_shared(n) > Fraction(99, 100))
print(f"smallest n with P > 50%: {first50};  smallest n with P > 99%: {first99}")
print(f"pairs among 23 people: C(23,2) = {comb(23,2)}")
print(f"P(someone shares YOUR birthday) with 22 others: {1-(364/365)**22:.4f}")
print(f"people needed for >50% that someone shares YOUR birthday: "
      f"{next(n for n in range(1,2000) if 1-(364/365)**n > 0.5)}")

SEED = 20261019; rng = random.Random(SEED); R = 1000
hits = sum(len(set(rng.randrange(365) for _ in range(23))) < 23 for _ in range(R))
print(f"simulation seed={SEED}: {R} rooms of 23 -> {hits} rooms had a shared birthday ({hits/R:.1%})")

# --- added after writers' room r1 -------------------------------------------------------------
from math import exp, log, sqrt, factorial
import json
print("\n# why 23: pairs grow like n^2/2")
for n in (5, 10, 15, 20, 23, 30, 40, 50, 70):
    print(f"  n={n:3d}: pairs={comb(n,2):5d}")
print(f"if the 253 pairs were independent 1-in-365 chances: 1-(364/365)^253 = {1-(364/365)**253:.4f}")
print(f"naive (wrong) multiplication 253/365 = {253/365:.4f}")
print(f"P(no shared birthday | 23) exact = {float(1-p_shared(23)):.6f}  (just below one half)")
print(f"approximation 1-exp(-n(n-1)/730) at 23 = {1-exp(-23*22/730):.4f}")
print(f"365*ln2 = {365*log(2):.1f}  (why ~253 single chances give ~50%: same number behind #6 and #7)")
print(f"50% point estimate sqrt(2 ln2 * 365) = {sqrt(2*log(2)*365):.2f}")

# Feb 29: 365 days with weight 4, Feb 29 weight 1 (out of 1461). P(no match) via e_k of the weights is heavy;
# use the exact product formula for distinct-day assignments with a DP over 'used Feb29 or not'.
def p_shared_leap(n):
    w = Fraction(4, 1461); wl = Fraction(1, 1461)
    # P(all distinct) = sum over (Feb29 unused) + (Feb29 used by exactly one person)
    a = Fraction(1)
    for k in range(n): a *= (365 - k) * w           # all on ordinary days, distinct
    b = Fraction(0)
    if n >= 1:
        c = Fraction(1)
        for k in range(n - 1): c *= (365 - k) * w
        b = n * wl * c
    return 1 - (a + b)
print(f"with Feb 29 at weight 1/1461: P(23) = {float(p_shared_leap(23)):.6f} vs 365-day {float(p_shared(23)):.6f}")

# at least THREE people sharing a day: P(no day has >=3) = sum_k n!/(2^k k! (n-2k)!) * 365!/(365-n+k)! / 365^n
def p_no_triple(n, d=365):
    tot = Fraction(0)
    for k in range(0, n // 2 + 1):
        singles = n - 2 * k
        if k + singles > d: continue
        ways_people = Fraction(factorial(n), (2 ** k) * factorial(k) * factorial(singles))
        ways_days = Fraction(factorial(d), factorial(d - k - singles))
        tot += ways_people * ways_days
    return tot / Fraction(d) ** n
n3 = next(n for n in range(3, 200) if 1 - p_no_triple(n) > Fraction(1, 2))
print(f"smallest n with P(some day has >=3 people) > 50%: {n3} ({float(1-p_no_triple(n3)):.4f})")

# per-room flags for the animation, same RNG order as the 1,000-room sim above
rng = random.Random(SEED); flags = []; rooms = []
for _ in range(R):
    b = [rng.randrange(365) for _ in range(23)]
    flags.append(len(set(b)) < 23); rooms.append(b)
json.dump(dict(seed=SEED, flags=flags, room0=rooms[0]), open("rooms.json", "w"))
r0 = rooms[0]; dup = sorted({d for d in r0 if r0.count(d) > 1})
print(f"rooms.json written: {sum(flags)} of {R} flagged (matches the sim above); featured room 0 shared days: {dup}")

# spread of the 1,000-room run: 2,000 more runs (seeds 1..2000)
def run(seed):
    r = random.Random(seed); return sum(len(set(r.randrange(365) for _ in range(23))) < 23 for _ in range(1000))
ws = sorted(run(s) for s in range(1, 2001))
print(f"2,000 runs of 1,000 rooms: median {ws[1000]}, middle 95% {ws[50]}-{ws[1949]}")
