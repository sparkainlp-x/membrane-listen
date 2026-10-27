# membrane-listen

SYNTHETIC sonification of a phase-oscillator membrane: tones and pulse
sounds from simulated phase. Classical, standard-library-only Python,
seeded and reproducible. Version 0.1.0, released on GitHub on 2026-10-27
and archived on Zenodo; the DOIs are listed under "How to cite" once the
archive record exists.

Copyright (C) 2026 Jean-François Brisson (Spark AI NLP). Licensed under
AGPL-3.0-only; the full text is in `LICENSE`.

## How to cite

See `CITATION.cff`. Cite the repository URL, version 0.1.0 and the
release tag v0.1.0 (a DOI is listed here once the Zenodo record exists).
Jean-François Brisson, membrane-listen, version 0.1.0 (2026),
https://github.com/sparkainlp-x/membrane-listen. SYNTHETIC software, not
a recording and not a medical model.

## Honest limits (read these first)

- This is a SYNTHETIC simulation. The sound is a sonification of
  simulated phase, not a recording of anything. No sound pressure exists
  in any of these models.
- Not a heart, not a brain, not an ECG, not an EEG, not a diagnosis, not
  a medical model and not a medical device. The heart and brain scenes
  are pulse-arrival toys with toy labels (a pulse chain is reduced to
  one arrival delay per sensor), not anatomy and not electrophysiology.
- No listening test was run. Nothing here says what anyone hears, finds
  clear or can tell apart. "Pitch" means the frequency of the rendered
  signal, "loudness" its RMS level, "clarity" the sensor's local
  coherence.
- "Clarity = locked" is not what the measurements show: the sensor
  coherence stays at 0.97 when the ring is no longer locked to its drive
  and when nothing drives it at all (see Findings). Loud means locally
  ordered, not locked.
- The two stereo files carry direction in the audio (a +-31.4 sample
  delay between channels); the mono files do not. Whether a listener can
  use that is untested.
- Two of the 23 pre-registered hypotheses were not supported, and the
  supplied design notes needed corrections (see DESIGN.md).

## Quickstart

```
python -m membrane_listen            # builds the six WAV files in ./wav
python -m membrane_listen --check    # regenerates in memory and compares
                                     # byte for byte with ./wav
python -m unittest                   # the test suite (also runs under pytest)
python demo.py                       # shim for the supplied entry point
```

No installation or network access is needed; Python 3.10 to 3.13.

## The mapping (a choice, stated plainly)

- audio sample = cos(sensor phase) x local coherence
- pitch = local phase velocity (omega), measured from the sensor's own
  phase history, not set by hand. The audio frequency is
  |omega| dt rate / (2 pi) Hz, with dt = 0.05 time units per sample and
  rate 8000 Hz: omega = 1 gives 63.66 Hz. The sign of omega is not
  audible.
- direction = phase-gradient sign (k_est), reported numerically, and, in
  the stereo files, the phase gap (and the audio delay) between two
  sensors a quarter-ring apart
- clarity = local coherence of five neighbouring oscillators (locked
  0.99; falls with noise)

## Scenes (seed 42, 8000 Hz, all committed in `wav/`)

| File | Model | What it contains | Measured numbers |
|---|---|---|---|
| `wave_forward.wav` | ring, k = +1, seed 42, sensor at node 10 | 2.0 s tone | k_est +1.00, omega -1.000, coherence 0.990, wave-order 1.000, peak 63.66 Hz |
| `wave_reverse.wav` | ring, k = -1, seed 42, sensor at node 10 | 2.0 s tone, same pitch | k_est -1.00, omega -1.000, coherence 0.990, wave-order 1.000, peak 63.66 Hz |
| `wave_stereo_forward.wav` | ring, k = +1, sensors 10 (left) and 26 (right) | 2.0 s, two channels | phase gap +1.5708 rad (+pi/2); right channel lags left by 31.4 samples |
| `wave_stereo_reverse.wav` | ring, k = -1, sensors 10 and 26 | 2.0 s, two channels | phase gap -1.5708 rad (-pi/2); right channel leads left by 31.4 samples |
| `heart.wav` | pulse train (toy label), no seed | 5 thumps in 4.0 s | arrival every 0.80 s, first at 0.32 s, 55 Hz thump with 80 ms decay |
| `brain_stereo.wav` | two pulse trains (toy label), no seed | 4 thumps per channel, 4.8 s stereo | left 0.16 s, right 0.59 s (label arithmetic gives 0.60 s, see DESIGN.md), spread 0.43 s |

The two wave tones have the same pitch on purpose: direction lives in
the gradient, not the pitch. The files are small (about 400 kB in
total) and regenerate byte for byte; a test compares them with the
committed bytes. Floating-point caveat: sums use exact rounding
(`math.fsum`) so that Python 3.10 to 3.13 agree; a different C math
library could in principle change the last bit of a sample, and that
test would show it first.

## Findings (SYNTHETIC; 200 confirmation seeds, 95 % bootstrap CIs)

Full tables, the development-set comparison and the limitations are in
`docs/RESULTS.md`; the protocol that fixed everything before any result
is `docs/PROTOCOL.md`. Each study ran once on seeds 5000 to 5199.

| Question | Result |
|---|---|
| Is the sensor's pitch right? (study A) | Exact without noise at every drive frequency up to 16 (0.0 relative error); 0.35 % at 32 (CI [0, 1.0 %]); at 48 the phase-based estimate is 98 % wrong because single steps alias, while the audio's spectral peak is still right (0.0008 %). |
| Under noise 1, which pitch estimate is better? (H5) | Not what I expected: the audio spectrum (0.31 % error) beats the sensor's phase history (3.0 %, CI [2.5, 3.5]). H5 was NOT supported; at noise 2 the phase-based error is 65 %. |
| Is direction recovered? (study B) | The long-window estimate is right in 100 % of runs up to noise 0.5 and 95 % at noise 1 (CI [93, 97]); the single reading in the supplied README is right 65 % at noise 0.5 and 57 % at noise 1. With the drive weaker than its frequency it is at chance (0.56, CI [0.52, 0.61]). |
| Does the stereo audio carry direction? | Yes, in the lag between channels: sign right in 200 of 200 replicates, flips under time reversal in 200 of 200, error 0.0004 samples. Mono audio carries none (forward and reverse tones differ by 0.0 Hz). |
| Does "clarity" track locking? (study C) | No. Coherence is 0.990 locked, 0.969 when the drive is too weak to lock (CI [0.963, 0.974]), 0.968 with no drive at all (CI [0.962, 0.973]), and 0.389 only with no coupling either. Loudness follows coherence by construction (Pearson 0.9994). Undriven wave-order was 0.34, not near 0 (H14 NOT supported): undriven rings relax into twisted states. |
| Doppler-like shift for a moving sensor? (D1) | Matches omega_obs = -Omega + 2 pi k v / n to rounding without noise; mean error 0.0024 rad per time unit at noise 0.5. A kinematic effect of the sensor's motion. |
| Does a 2D membrane give a second axis? (D2) | The membrane does (three sensors recover both wave-vector signs, 200 of 200), but a two-channel stereo pair is blind to the second axis. EXPERIMENTAL; no scene was built. |
| Controls | Shuffled-phase sensor at chance (0.496, CI [0.488, 0.503]); an attached sensor never changed a trajectory (200 of 200); a deliberately mutating sensor was caught (200 of 200). 20 of 20 WAV checks pass (decay constant 639.96 samples against the label 640, 55.00 Hz thump, 0.80 s intervals). |

These are results about a simulation. They say nothing about perception,
physiology, real hearts or real brains.

## Reproduce the studies

```
python -m experiments.run_all --set dev     --out docs/results/dev.json
python -m experiments.run_all --set confirm --out docs/results/confirm.json
python -m experiments.wav_checks            --out docs/results/wav_checks.json
python -m experiments.render_results        # writes docs/RESULTS.md
```

Seed sets: development 1000 to 1199, confirmation 5000 to 5199, smoke
(CI) 9001 to 9005; seed 42 is reserved for the scenes. Each full run
takes a few minutes on 8 cores.

## Layout

- `membrane_listen/`: `core.py` (ring, sensor), `pulses.py` (thump
  trains), `wavio.py` (WAV input and output), `scenes.py` (the six
  scenes), `estimators.py` (pitch, direction, stereo lag, decay fits),
  `stats.py` (seeded bootstrap, Holm, correlations), `experimental.py`
  (2D torus, labelled experiment), `__main__.py` (command line)
- `experiments/`: studies, runner, WAV checks, results renderer
- `docs/`: `PROTOCOL.md`, `RESULTS.md` (generated), `interpretation.md`
  (hand-written), `results/*.json`
- `tests/`, `scripts/check_text.py` (the wording and emoji checker run in
  CI), `DESIGN.md`, `CHANGELOG.md`, `CITATION.cff`, `.zenodo.json`

## Lineage

The oscillator dynamics follow the sparkainlp-x membrane lineage;
nothing outside this repository is needed to run it. This repository starts from
the supplied membrane-listen package, committed unchanged as its first
commit, and DESIGN.md lists every change.
