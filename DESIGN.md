# DESIGN.md — membrane-listen

## Why two different sound models

The travelling wave is a real phase signal: cos(phase) is audible
directly, at about 64 Hz (phase velocity 1 rad per time unit, one
reading per audio sample at 8000 Hz). The heart and brain scenes are
not phase signals — they are pulse-arrival models, so they are
sonified as decaying thumps instead. Mixing the two without saying so
would have been dishonest: a thump is not a phase, and a tone is not
a beat. Each scene names its model in the README.

## Why the two wave tones sound identical

A locked oscillator follows drive phase k·2πi/N − Ωt, so at fixed i
its phase velocity is −Ω whatever k is. Pitch therefore cannot carry
direction in this model, and the demo does not pretend it does. What
carries direction is the spatial gradient: k_est = +1 vs −1, and in
the stereo files the phase gap between two sensors a quarter-ring
apart (+π/2 vs −π/2). If a future version wants direction audible in
mono, it needs a different mapping (e.g. gradient → stereo pan, or
gradient → a second tone), stated as a mapping, not as physics.

## Test bugs found, not model bugs

- First heart test counted every sine zero-crossing as a thump
  (55 regions instead of 5). Fixed by counting arrival windows:
  loud in [arrival, arrival+1000], quiet in the gap before the next.
- Gap check ran past the end of the signal for the last thump
  (empty slice). Fixed by checking gaps only between thumps.

## Open questions

- Does a sensor riding the probe (moving position) hear a Doppler-like
  shift in this toy? The sensor class has follow_probe(); untested.
- Would a 2D membrane give a richer stereo image (two sensor axes)?
  Untested; the ring gives one spatial axis only.
