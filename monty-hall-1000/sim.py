"""Monty Hall: 1,000 simulated games, both strategies on the same games.
Rules (vos Savant's stated conditions): car placed uniformly at random; contestant picks uniformly
at random; host KNOWS where the car is, ALWAYS opens a goat door the contestant didn't pick
(choosing at random if he has two), and ALWAYS offers the switch.
Run: python3 sim.py   (numpy not needed; Python's random with fixed seed)"""
import random
from fractions import Fraction
from itertools import product

SEED = 20261019
rng = random.Random(SEED)

def play(rng):
    car = rng.randrange(3); pick = rng.randrange(3)
    goats = [d for d in range(3) if d != pick and d != car]
    opened = rng.choice(goats)
    switch_to = next(d for d in range(3) if d != pick and d != opened)
    return car == pick, car == switch_to

N = 1000
stay = sw = 0
checkpoints = {}
for g in range(1, N + 1):
    s, w = play(rng)
    stay += s; sw += w
    if g in (10, 30, 100, 300, 1000):
        checkpoints[g] = (stay, sw)
print(f"seed={SEED}, games={N}")
for g, (s, w) in checkpoints.items():
    print(f"  after {g:4d} games: stay won {s:4d} ({s/g:.1%}), switch won {w:4d} ({w/g:.1%})")
assert stay + sw == N  # in every game exactly one strategy wins

# reference run, 1,000,000 games, separate seed
rng2 = random.Random(SEED + 1); M = 1_000_000; sw2 = sum(play(rng2)[1] for _ in range(M))
print(f"reference: {M:,} games, switch won {sw2/M:.4%}, stay won {(M-sw2)/M:.4%}")

# exact enumeration over car x pick (host's coin flip doesn't change who wins)
wins = sum(Fraction(1, 9) for car, pick in product(range(3), repeat=2) if car != pick)
print(f"exact: P(switch wins) = {wins}, P(stay wins) = {1 - wins}")

# 100-door variant (host opens 98 goat doors): switch wins unless first pick was the car
print(f"exact, 100 doors: P(switch wins) = {Fraction(99,100)}")

# --- added after writers' room r1 -------------------------------------------------------------
# (a) The host's KNOWLEDGE is the whole trick: "Monty Fall" host opens one of the two unpicked doors
#     at random; games where he reveals the car are thrown out. Then switching wins only about 1/2.
rng3 = random.Random(SEED + 2); kept = sw3 = 0
for _ in range(1_000_000):
    car = rng3.randrange(3); pick = rng3.randrange(3)
    opened = rng3.choice([d for d in range(3) if d != pick])
    if opened == car: continue            # he showed the car: not the situation we're asking about
    kept += 1; sw3 += (car != pick)        # the other closed door has the car iff first pick was wrong
print(f"ignorant host (random door, car-reveals discarded): {kept:,} games kept, switch won {sw3/kept:.4%}")
# exact: P(switch wins | goat revealed by an ignorant host) = (2/3 * 1/2) / (1/3 + 2/3 * 1/2) = 1/2
print(f"exact, ignorant host: P(switch wins | goat shown) = {Fraction(2,3)*Fraction(1,2) / (Fraction(1,3) + Fraction(2,3)*Fraction(1,2))}")

# (b) How much does one 1,000-game run wobble? 2,000 independent runs (seeds 1..2000).
def run1000(seed):
    r = random.Random(seed)
    return sum(play(r)[1] for _ in range(1000))
wins = sorted(run1000(s) for s in range(1, 2001))
lo, hi = wins[int(0.025 * len(wins))], wins[int(0.975 * len(wins)) - 1]
print(f"2,000 runs of 1,000 games: switch wins median {wins[len(wins)//2]}, middle 95% {lo}-{hi}, "
      f"min {wins[0]}, max {wins[-1]}; runs where staying beat switching: {sum(w < 500 for w in wins)}")
# note on the seed: 20261019 is the date the sim was written; it was the first and only seed run for #3.
