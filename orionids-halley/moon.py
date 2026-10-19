import ephem, math
cities={'Denver 39.74N 104.99W (UTC-6 MDT)':('39.74','-104.99',-6),'New York 40.71N 74.01W (UTC-4 EDT)':('40.71','-74.01',-4),'London 51.51N 0.13W (UTC+1 BST)':('51.51','-0.13',1),'Tokyo 35.68N 139.69E (UTC+9)':('35.68','139.69',9),'Sydney 33.87S 151.21E (UTC+11 AEDT)':('-33.87','151.21',11)}
# Orionid radiant J2000 RA 95 deg, Dec +16 (IMO). 
rad=ephem.FixedBody(); rad._ra=math.radians(95); rad._dec=math.radians(16); rad._epoch=ephem.J2000
for name,(la,lo,tz) in cities.items():
    o=ephem.Observer(); o.lat=la; o.lon=lo; o.elevation=0; o.pressure=0; o.horizon='-0:34'
    # local evening of Oct 21 18:00 local
    start=ephem.Date('2026/10/21 18:00')-tz*ephem.hour
    o.date=start
    m=ephem.Moon(); s=ephem.Sun()
    ms=o.next_setting(m); 
    o.horizon='-18'; dawn=o.next_rising(s,use_center=True)
    o.horizon='-0:34'
    o.date=ms; rad.compute(o); ralt=math.degrees(rad.alt)
    m.compute(ephem.Date('2026/10/22 06:00')-tz*ephem.hour)
    loc=lambda d: ephem.Date(d+tz*ephem.hour)
    print(f"{name}: moonset {loc(ms)} local; astro dawn {loc(dawn)} local; dark window {(dawn-ms)*24:.2f} h; radiant alt at moonset {ralt:.0f} deg; moon illum {m.phase:.0f}%")
for d in ['2026/10/21 00:00','2026/10/22 00:00','2026/10/22 06:00']:
    m=ephem.Moon(d); print(d,'UTC illum',round(m.phase,1))
print('prev first quarter',ephem.previous_first_quarter_moon('2026/10/22'),'next full',ephem.next_full_moon('2026/10/22'))
