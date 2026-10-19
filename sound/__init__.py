"""Sonification toolkit for science Shorts (numpy only; everything synthesized, no samples).
Modules: scales (just-intonation quantizer), instruments (modal marimba/kalimba, FM glass/bell, Karplus-Strong,
soft tick, continuous additive/FM voices, pad), mix (stereo bus, equal-power pan, convolution reverb,
spectral EQ, lookahead limiter, LUFS/true-peak mastering, phone-speaker check, onset detection)."""
SR = 44100
from .scales import *
from .instruments import *
from .mix import *
