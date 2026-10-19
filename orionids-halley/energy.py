"""Orionid numbers (stdlib only). Run: python3 energy.py > energy_output.txt"""
import math
v = 66_000.0                      # m/s, NASA Orionids page (O1)
m = 1e-6                          # kg = 1 milligram (a chosen example mass, not a 'typical' Orionid)
KE = 0.5 * m * v**2
print(f"1 mg at 66 km/s: KE = 0.5 * {m} kg * ({v:.0f} m/s)^2 = {KE:.0f} J")
# Baseball: MLB Official Baseball Rules 3.01: 5 to 5 1/4 oz avoirdupois -> use 5.125 oz
oz = 0.028349523125; mb = 5.125 * oz; vb = 90 * 0.44704
KEb = 0.5 * mb * vb**2
print(f"baseball {mb*1000:.1f} g at 90 mph ({vb:.2f} m/s): KE = {KEb:.1f} J; ratio = {KE/KEb:.1f}")
for lo, hi in [(5, 5.25)]:
    print(f"  ratio range for 5-5.25 oz at 90 mph: {KE/(0.5*hi*oz*vb**2):.1f}-{KE/(0.5*lo*oz*vb**2):.1f}")
print(f"  at 95 mph: {KE/(0.5*mb*(95*0.44704)**2):.1f}")
# Gram for gram vs TNT (4.184 kJ/g by definition)
print(f"specific KE at 66 km/s = {0.5*v**2/1e6:.2f} MJ/kg = {0.5*v**2/1e6/4.184:.2f} x TNT (4.184 MJ/kg)")
# Why so fast: heliocentric speed of a Halley-orbit particle at 1 AU vs Earth's orbital speed
GMsun = 1.32712440018e20; AU = 1.495978707e11
a = 17.9 * AU                      # JPL SBDB 1P/Halley (O5)
vp = math.sqrt(GMsun * (2 / AU - 1 / a)); ve = math.sqrt(GMsun / AU)
vesc_sun = math.sqrt(2 * GMsun / AU)
print(f"particle speed at 1 AU on Halley's orbit ~ {vp/1e3:.1f} km/s; Earth ~ {ve/1e3:.1f} km/s; solar escape at 1 AU {vesc_sun/1e3:.1f} km/s")
vesc_earth = 11.19e3
vmax = math.sqrt((vesc_sun + ve)**2 + vesc_earth**2)
print(f"max possible entry speed (head-on, parabolic, + Earth's pull) ~ {vmax/1e3:.1f} km/s  (AMS: 72 km/s)")
vg = math.sqrt(v**2 - vesc_earth**2)
cos = (vp**2 + ve**2 - vg**2) / (2 * vp * ve)
print(f"Orionid: entry 66 -> geocentric {vg/1e3:.1f} km/s -> angle between particle and Earth velocity ~ {math.degrees(math.acos(cos)):.0f} deg (180 = exactly head-on)")
print(f"if they had moved the same way as Earth (prograde, same angle mirrored): geocentric ~ {math.sqrt(vp**2+ve**2-2*vp*ve*math.cos(math.radians(180-math.degrees(math.acos(cos)))))/1e3:.1f} km/s")
# --- r1 additions (2026-10-19) ---
# Expert r1 Q1: how much of the speed is the retrograde direction vs the near-escape heliocentric speed?
ang = math.acos(cos)
for label, vpp in [("Halley-orbit dust (a=17.9 au)", vp), ("retrograde but circular orbit at 1 AU", ve)]:
    vg2 = math.sqrt(vpp**2 + ve**2 - 2*vpp*ve*math.cos(ang))
    print(f"{label}: heliocentric {vpp/1e3:.1f} km/s, same {math.degrees(ang):.0f} deg geometry -> geocentric {vg2/1e3:.1f} km/s -> entry {math.sqrt(vg2**2+vesc_earth**2)/1e3:.1f} km/s")
print(f"Halley-orbit speed at 1 AU as a share of solar escape speed there: {100*vp/vesc_sun:.1f}%")
# Skeptic r1 Q5: modern fastballs ~94 mph
print(f"ratio at 94 mph: {KE/(0.5*mb*(94*0.44704)**2):.1f}")
# JPL SBDB (read 2026-10-19): Earth MOID 0.0745 au; aphelion 35.3 au (Neptune ~30.07 au)
print(f"Halley's current orbit passes {0.0745*AU/1e9:.1f} million km from Earth's orbit at closest (JPL MOID 0.0745 au)")
