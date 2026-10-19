"""Phobos numbers used in FACTS.md (stdlib only). Run: python3 calc.py  -> calc_output.txt
Inputs: JPL SSD Planetary Satellite Physical Parameters (S8): Phobos GM 0.0007087 km^3/s^2, mean radius 11.08 km;
Mars GM 42828.37362 km^3/s^2. Phobos orbital radius 9,376 km (S5)."""
import math
GM = 0.0007087e9; R = 11.08e3                       # m^3/s^2, m
v = math.sqrt(2 * GM / R); g = GM / R**2
print('v_esc', v, 'm/s', v * 3.6, 'km/h')
print('g', g, 'Idefix 25kg weighs like', 25 * g / 9.80665 * 1000, 'g')
mu = 0.0007087 / 42828.37362; a = 9376
print('mu', mu, 'rH', a * (mu / 3) ** (1 / 3))
print('rH NAOJ', 9376 * (1.66e-8 / 3) ** (1 / 3))
