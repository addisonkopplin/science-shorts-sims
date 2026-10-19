"""Reproduces gaia_calc_output.txt. Inputs from SIMBAD (queried 2026-10-19) for SDSS J133001.13+643523.7 = WD J1330+6435 = Gaia DR3 1666074615061406336:
parallax 11.5812 +/- 0.7812 mas and G = 20.644728 (both Gaia EDR3, 2020yCat.1350....0G)."""
plx, e = 11.5812, 0.7812
pc = 1000/plx; ly_per_pc = 3.26156
print(f"d = 1000/{plx} = {pc:.1f} pc = {pc*ly_per_pc:.0f} ly; 1-sigma range {1000/(plx+e)*ly_per_pc:.0f}-{1000/(plx-e)*ly_per_pc:.0f} ly")
G = 20.644728; lim = 6.0
print(f"Gaia G = {G:.2f}; vs naked-eye limit ~{lim}: {10**((G-lim)/2.5):,.0f} times fainter")
print(f"Teff 4240 K = {4240-273.15:.0f} C")
