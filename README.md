# Science Shorts simulations

The code behind two animated science Shorts: the simulations, the frame-by-frame animation, and
sound that is generated *from* the simulation (every note is caused by something you can see).

| Galton board | 1,000 double pendulums |
| --- | --- |
| ![Galton board forming a bell curve](docs/galton.gif) | ![1,000 double pendulums diverging into chaos](docs/pendulum.gif) |

*(The GIFs are silent previews; the rendered MP4s have the sound.)*

## Quick start

You need Python 3.9+, [ffmpeg](https://ffmpeg.org/download.html) on your PATH, and pycairo. On Windows
pip installs pycairo with cairo included. On macOS run `brew install cairo pkg-config` first, and on
Debian/Ubuntu `sudo apt install libcairo2-dev pkg-config python3-dev`.

```bash
pip install -r requirements.txt

python galton.py          # -> out/galton.mp4    (36 s, 1080x1920, with sound; about half a minute to render)
python pendulum.py        # -> out/pendulum.mp4  (34 s, with sound; a minute or two)
```

Useful options (both scripts):

```bash
python galton.py --preview 0,8,22     # just a few still frames as PNGs, in seconds
python galton.py --no-sound --gif     # video only, plus a small preview GIF
python galton.py --seed 42            # a different random run of the Galton board
python galton.py --variant glass      # glass/bell instruments instead of mallets
python pluck.py pluck-demo.wav        # demo of the string-pluck sounds used for the string art video
```

## What's simulated

**Galton board** (`galton.py`). 1,000 balls drop through 12 rows of pegs. At every peg a ball goes
left or right with probability 1/2, so the bin it lands in is the number of "rights": a binomial
distribution, which the central limit theorem says looks like a bell curve. The gold curve drawn
over the bins is the normal distribution with the same mean (6) and variance (12 × ¼ = 3), scaled to
1,000 balls. The board is idealised: fair coin flips, not bouncing-ball physics.

**Double pendulums** (`pendulum.py`, physics in `dp_sim.py`). 1,000 double pendulums with equal
masses and 1 m massless rods, no friction, integrated with 4th-order Runge-Kutta (40 substeps per
frame). The lower arms start at 2.4 rad with a total spread of one millionth of a radian (less than
0.0001°) across all 1,000. For about 9 seconds they move as one; then the tiny differences grow
exponentially and they fly apart. The total energy is printed as a check on the integrator (it drifts
by less than 1e-7). `python dp_sim.py` prints divergence times for a few starting angles and spreads.

## Sound

All sound is synthesized with numpy: no samples, no music, so no licensing questions.
`galton_sound.py` and `pendulum_sound.py` turn simulation events into notes:

- **Galton:** each peg hit plays a note whose pitch is the ball's left-right position (on a pentatonic
  scale), so every ball's path is a tiny melody; landings play chord tones by bin, louder for faster
  falls; the curve being drawn plays a rising arpeggio shaped like the bell curve, resolving on a chord.
- **Pendulums:** each time an arm turns around or swings over the top it plays a marimba note pitched
  by its speed. While all 1,000 are in sync they sound as single crisp notes; as chaos sets in the
  notes scatter.

The mixes are mastered to about −14 LUFS and loop seamlessly, like the videos. The design rules, the
research behind them and the exact mappings are in [docs/SOUND-DESIGN.md](docs/SOUND-DESIGN.md).
The reusable toolkit is the `sound/` package (scales, instruments, mixing and mastering) and
`pluck.py` (Karplus-Strong string plucks).

## Files

| File | What it is |
| --- | --- |
| `galton.py` | Galton board simulation and animation; renders the video and calls the sound |
| `galton_sound.py` | Sound for the Galton board, from the simulation events |
| `pendulum.py` | Double-pendulum animation; renders the video and calls the sound |
| `pendulum_sound.py` | Sound for the pendulums, from the simulation events |
| `dp_sim.py` | Double-pendulum equations of motion, RK4 integrator and energy |
| `common.py` | Video helpers: cairo frames into ffmpeg, easing, captions in the Shorts safe area |
| `sound/` | Sonification toolkit: `scales.py`, `instruments.py`, `mix.py` |
| `pluck.py` | String-pluck sound effects (pitch from line length) used for the string art video |
| `docs/` | Preview GIFs and the sound design notes |

Captions use the Inter font if it is installed (set `SIMS_FONT` to use another); otherwise cairo
falls back to a default sans-serif.

## License

[MIT](LICENSE).
