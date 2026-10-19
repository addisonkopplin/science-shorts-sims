"""Independent reproduction of the NIST P-256 seed (Quill, 2026-10-19).
Written from the POSIX drand48 spec (a=0x5DEECE66D, c=0xB, m=2^48; srand48(t) sets state = t<<16 | 0x330E),
NOT copied from the Anthropic snippet. Each lrand48/drand48 step yields one byte = top 8 bits of the 48-bit state.
Then checks the ANSI X9.62 / FIPS 186-2 SHA-1 procedure: seed -> c, and b^2*c == -27 (mod p) for the published b.
Run: python3 reproduce.py   (stdlib only)"""
import hashlib, datetime
A, C, M = 0x5DEECE66D, 0xB, 1 << 48
def stream(t):
    x = ((t & 0xFFFFFFFF) << 16) | 0x330E
    while True:
        x = (A * x + C) % M
        yield x >> 40                       # top byte (same as lrand48() >> 23, or int(drand48()*256))
def candidate(t, n):
    g = stream(t); b = bytes(next(g) for _ in range(20 * n)); return b[-20:]
# Published values, FIPS 186-2 (change notice 1), Appendix 6, Curve P-256 (fips.txt lines 1134-1146)
p = 115792089210356248762697446949407573530086143415290314195533631308867097853951
s_pub = bytes.fromhex("c49d360886e704936a6678e1139d26b7819f7e90")
c_pub = int("7efba1662985be9403cb055c75d4f7e0ce8d84a9c5114abcaf3177680104fa0d", 16)
b_pub = int("5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b", 16)
assert p == 2**256 - 2**224 + 2**192 + 2**96 - 1
t = 871696354
print("timestamp", t, "=", datetime.datetime.fromtimestamp(t, datetime.timezone.utc).isoformat())
seed = candidate(t, 1842)
print("candidate 1842:", seed.hex(), "matches FIPS 186-2 seed:", seed == s_pub)
# How many candidates is that? bytes consumed:
print("bytes drawn up to and including candidate 1842:", 20 * 1842)
# X9.62 / FIPS 186-2 App. 6: t=256 bits, s=floor((t-1)/160)=1, h=t-160*s=96
def x962_c(seed, bits=256):
    sc = (bits - 1) // 160; h = bits - 160 * sc
    H = hashlib.sha1(seed).digest(); c0 = int.from_bytes(H, "big") & ((1 << h) - 1)
    W = c0 & ~(1 << (h - 1))                # clear the leftmost bit of the h-bit string
    g = len(seed) * 8; z = int.from_bytes(seed, "big")
    for i in range(1, sc + 1):
        si = ((z + i) % (1 << g)).to_bytes(len(seed), "big")
        W = (W << 160) | int.from_bytes(hashlib.sha1(si).digest(), "big")
    return W
c = x962_c(seed)
print("SHA-1 procedure gives c == published c:", c == c_pub)
print("published b satisfies b^2*c == -27 mod p:", (b_pub * b_pub * c) % p == (-27) % p)
# Also check the other runs listed by Valsorda/Anthropic against values we can read in fips.txt
others = {"P-192": (863966734, 139), "P-224": (891607927, 7026), "P-384": (872952608, 2688), "P-521": (871002724, 1136)}
for k, (tt, n) in others.items():
    print(k, datetime.datetime.fromtimestamp(tt, datetime.timezone.utc).isoformat(), n, candidate(tt, n).hex())
print("candidate 876 (same run, reported as valid-but-unused):", candidate(t, 876).hex())
