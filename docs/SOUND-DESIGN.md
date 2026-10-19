# Sound design for science Shorts: research and rules

Goal: the sound should feel *caused by* the math on screen (intentional), be pleasant (satisfying, never harsh), and survive phone speakers. All audio is synthesized in code from the simulation state (`sound/`), so there are no samples and no licensing questions.

## 1. Sonification: map data to sound on purpose
- **Parameter-mapping sonification.** Each data variable drives one sound parameter (pitch, loudness, timbre, pan, onset). Design choices are *polarity* (does more data mean higher or lower?), *scaling* (fit the data range into a useful perceptual range), and *context* (reference sounds). Grond & Berger, "Parameter Mapping Sonification", ch. 15 of *The Sonification Handbook* (Hermann, Hunt, Neuhoff eds., 2011): https://sonification.de/handbook/chapters/chapter15/
- **Pitch is the most used and most readable dimension.** Musical intervals are perceptually "privileged", so mapping data onto **scale degrees** makes the changes meaningful. The Handbook's own example maps temperature to a **C-D-E-G-A pentatonic** scale. (Same chapter, example S15.5; also ch. 4, Walker & Nees, "Theory of Sonification": https://sonification.de/handbook/download/TheSonificationHandbook-chapter2.pdf)
- Our polarity choices follow common mental models: **faster/higher energy → higher pitch and brighter tone**, **position left/right → stereo pan**, **discrete event (collision, crossing) → note onset**, and **amount (how many) → loudness**.

## 2. Pleasantness (psychoacoustics)
- **Harmonicity drives consonance.** Across more than 250 listeners, a preference for harmonic spectra (not the absence of beating) predicted a preference for consonant chords. McDermott, Lehr & Oxenham (2010), *Current Biology* 20:1035, https://doi.org/10.1016/j.cub.2010.04.019. → We use **just-intonation ratios** (1, 9/8, 5/4, 3/2, 5/3) so simultaneous notes are as harmonic as possible.
- **Pentatonic / chord-tone quantization.** A pentatonic scale has no semitone steps, so random combinations never form the harshest clashes. This is why viral polyrhythm and pendulum sonifications use it (a marimba in D pentatonic for Mermikides' pendulum-wave sonification; commenters on r/oddlysatisfying point it out). Sources: http://circlingcrows.blogspot.com/2016/03/theme-and-experimentation.html ; https://www.reddit.com/r/oddlysatisfying/comments/101b2p4/
- **Avoid harsh 2–5 kHz energy.** The ear is most sensitive between 2 and 5 kHz (ear-canal resonance, peak around 3–4 kHz; equal-loudness contours, ISO 226). https://en.wikipedia.org/wiki/Equal-loudness_contours ; ISO 226:2023 https://www.iso.org/standard/83117.html → Instruments roll off partials above 3 kHz, the master has a gentle −3 dB dip around 3.5 kHz, and continuous voices are hard-capped at 4.5 kHz.
- **Soft attacks, warm timbres.** Raised-cosine attacks of 1.5–3 ms (no clicks); modal mallets (marimba bar tuned 1 : 4 : ~10, Rossing, *Science of Percussion Instruments*, 2000), kalimba (clamped-free beam overtone around 6.3×), and FM glass and bells (Chowning 1973: a decaying modulation index gives a bright strike and a pure tail, and irrational ratios give bell-like inharmonicity). https://ccrma.stanford.edu/sites/default/files/user/jc/fm_synthesis_paper.pdf
- **Gentle reverb** (synthetic stereo room IR, RT60 about 2 s, wet ~16–18 %) gives space and glue without washing out the onsets.

## 3. What makes "satisfying" content sound good
- **Crisp sounds are a top ASMR trigger** (64 % of 475 respondents), along with slow movements. Barratt & Davis (2015), *PeerJ* 3:e851, https://doi.org/10.7717/peerj.851. ASMR viewers show calmer heart rates. Poerio et al. (2018), *PLOS ONE*, https://doi.org/10.1371/journal.pone.0196645 → crisp but *soft* transients: mallet and glass strikes with short attacks, no noise bursts.
- **Order emerging from apparent chaos, and a return to order.** The pendulum wave (15 pendulums with 51…65 swings per 60 s, which realign every 60 s; Harvard Natural Sciences Lecture Demonstrations, via https://jessegalef.com/2011/05/04/simple-beautiful-physics-video/) and Project.JDM's polyrhythm circles (each contact triggers a note, and integer loop counts make everything re-align; Hyperplexed's rebuild: https://www.klinke.studio/notes/audio/digital_musicianship/unravelling-the-magic-behind-polyrhythms ; interview with Jairo Mora, *J. Popular Music Studies* 2024, https://doi.org/10.1525/jpms.2024.36.3.39). The appeal: every sound visibly comes from an event, the notes are consonant, rhythm creates anticipation, and the resolution back to unison pays it off.
- → Our structure: a clear single voice or melody first, a texture that grows as complexity grows, a **resolving tonic chord** at the reveal, and a **seamless audio loop** that matches the visual loop.

## 4. Phones
- Most Shorts are heard on phone speakers, which roll off the low frequencies (often around 100–500 Hz). The brain reconstructs the "missing fundamental" from harmonics. Aarts, "Perceiving low pitch through small loudspeakers": https://www.sps.tue.nl/rmaarts/RMA_papers/aar00c.pdf ; FFmpeg virtualbass defaults to a 250 Hz cutoff.
- → Melodic fundamentals are kept at or above about 196 Hz (G3). The few lower notes (rare outer Galton bins) carry strong 2× and 4× partials. Check: a 200 Hz highpass keeps about 99 % of the energy in both mixes (`phone_check()` in `sound/mix.py`).
- **Loudness.** YouTube turns loud uploads down, so there's nothing to gain beyond about −14 LUFS. Masters land at about −14 LUFS integrated with a true peak of −2.4 to −2.7 dBTP (lookahead limiter, measured after AAC encoding).

## 5. Rules for every new video
1. Every sound has a visible cause, and every recurring visual event has a sound.
2. Pitch comes from a quantized scale (major pentatonic in just intonation, or chord tones). Continuous pitch glides between scale steps with portamento (snap about 0.8, 50 ms glide).
3. Mapping polarity: up/fast/energetic = higher and brighter; left/right = pan; count = loudness.
4. Thin dense events to about 20–30 per second so it's a texture, not noise. Scale per-event gain by speed or impact.
5. Build up to the reveal, resolve on the tonic, and make the audio loop seamless: the reverb tail is folded onto the start, the loop tone is phase-aligned, and level and pan match at the seam.
6. Keep partials under about 4.5 kHz, attacks at 1.5 ms or longer, fundamentals at or above about 196 Hz, −14 LUFS, true peak ≤ −1 dBTP.

## Toolkit (`sound/`)
`scales.py` (just-intonation pentatonic, major, triad; degree → Hz; soft snap + glide) · `instruments.py` (modal marimba and kalimba, FM glass and bell, fractional-delay Karplus-Strong, soft tick, continuous additive/FM voice, pad) · `mix.py` (stereo bus with equal-power pan, convolution reverb with a synthetic room, spectral EQ, lookahead limiter, LUFS mastering via ffmpeg, loop-tail wrap, phone check, spectral-flux onset detector and sync report).

## Exact mappings
### Galton board (`galton_sound.py`)
| Simulation quantity | Sound |
|---|---|
| Peg hit (row r, after j rights) | mallet note at the exact hit time; **pitch = horizontal position** (pentatonic degree 2j − r around C5), so each ball's path is a little melody; **pan = peg x**; loudness ∝ incoming speed; the dense phase is thinned to about 30 hits/s |
| Landing in bin k | **pitch = C-major chord tone for that bin** (centre bin = C5); **loudness ∝ (landing speed)^0.8**, so falls into empty bins ring out and landings on tall stacks are soft; pan = bin |
| Bell curve being drawn | a note as the drawing crosses each bin, **velocity = normal-curve height** there, then a resolving C-major chord |
| Floor opens (drain) | 14-note descending pentatonic run timed to when the balls actually leave the bins, ending as the loop restarts |

### Double pendulums (`pendulum_sound.py`)
| Simulation quantity | Sound |
|---|---|
| Upper arm turns around (ω₁ changes sign) | marimba note |
| Lower bob swings over the top (θ₂ crosses π) | marimba chime an octave higher |
| Lower bob speed at that instant | **pitch**: pentatonic degree 0–7 |
| Lower bob x position | **pan** |
| How many of the 1,000 pendulums fire together (within 15 ms, same pitch) | one merged note whose **loudness grows with the count**: all 1,000 in sync at the start give single crisp notes; as chaos sets in they scatter into many quiet ones |
| Density | at most 5 notes per half second, the biggest clusters win |

There is deliberately no background music, drone or pad: every sound is an event you can see.
