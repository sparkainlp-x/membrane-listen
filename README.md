# membrane-listen v0.1.0

**SYNTHETIC sonification: a sensor inside a phase-oscillator membrane
reads the local vibration, and that reading is turned into sound.
Classical simulation only. Not a recording, not a heart, not a brain,
not an ECG, not a diagnosis, not a medical device.**

## The mapping (a choice, stated plainly)

- audio sample = cos(sensor phase) × local coherence
- pitch = local phase velocity (omega), measured from the sensor's
  own phase history, not set by hand
- direction = phase gradient sign (k_est), reported numerically
- clarity = local coherence (locked ~0.99 = loud, noisy = quiet)

## Scenes (seed 42, 8000 Hz)

| File | What you hear | Measured numbers |
|---|---|---|
| `wav/wave_forward.wav` | 2.0 s tone, k=+1 | k_est +1.00, omega −1.000, coherence 0.990, wave-order 1.000 |
| `wav/wave_reverse.wav` | 2.0 s tone, k=−1, same pitch | k_est −1.00, omega −1.000, coherence 0.990, wave-order 1.000 |
| `wav/wave_stereo_forward.wav` | Two sensors a quarter-ring apart, phase gap +π/2 | sensors 10 and 26 |
| `wav/wave_stereo_reverse.wav` | Same, phase gap −π/2 | sensors 10 and 26 |
| `wav/heart.wav` | 5 thumps in 4.0 s | pacemaker every 0.80 s, sensor delay 0.32 s, 55 Hz decaying thump |
| `wav/brain_stereo.wav` | Left thump, then right thump, stereo | left 0.16 s, right 0.59 s, spread delay 0.43 s, 4.8 s |

Listen in that order: the two wave tones sound the same pitch on
purpose — direction lives in the gradient, not the pitch. The heart
is a pulse chain (pacemaker → travelling pulse → sensor), the brain
is two pulse chains with a cross delay, heard left then right.

## Run

```
python demo.py   # builds all WAV files in wav/
python tests.py  # 6/6 tests
```

## Files

- `membrane_listen.py` — ring, sensor, pulse trains, WAV I/O (stdlib only)
- `demo.py`, `tests.py`, `DESIGN.md`, `README.md`, `LICENSE` (AGPL-3.0-only)

## Honest limits

No sound pressure exists in any of these models. The audio is a
sonification of phase, not a recording of anything real. The heart
and brain scenes are pulse chains with toy labels, not anatomy, not
electrophysiology, not neuroscience. The sensor is read-only: sampling
changes no model state (test-pinned).
