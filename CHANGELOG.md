# Changelog

## 0.1.0 (2026-10-27)

First release, archived on Zenodo.

Starts from the supplied membrane-listen package (committed unchanged as
the first commit). The six committed WAV files are byte-identical to the
supplied ones, and regenerate identically on Python 3.10 to 3.13.

Verified as supplied: the six supplied tests pass; the README numbers
reproduce at seed 42 (k_est +1.00 and -1.00, omega -1.000, coherence
0.990, wave-order 1.000, five thumps 0.80 s apart, left 0.16 s, right
0.59 s, spread 0.43 s). Mismatches found: the brain right-sensor delay
(0.59 s) differs from the label arithmetic (0.60 s) by 0.01 s, and the
DESIGN.md pitch arithmetic left the time step out (63.66 Hz is right).
Both are documented, neither is hidden.

Changed (defects, each with tests; see DESIGN.md):
- WAV writer rejects non-finite samples and unequal stereo channels;
  clipping can be made an error and scenes use that.
- pulse_train rejects period <= 0 (it looped forever), negative delay
  (it wrote to the end of the buffer) and tau <= 0.
- Ring and Sensor validate their arguments; wrap() no longer loops.
- omega is NaN, not 0.0, when there is no history.
- Exactly rounded sums, so wave_order is 1.0 on every Python version (the
  supplied code returned 1.0000000000000002 on 3.10).
- Sensor.follow_probe() now exists.

Added:
- Package layout, `python -m membrane_listen` with a byte-for-byte
  `--check`, pyproject, CI on Python 3.10 to 3.13, wording checker.
- Optional ring noise and detuning (off by default), a labelled 2D torus
  experiment, estimators for pitch, direction, stereo lag and decay.
- docs/PROTOCOL.md (pre-registration, committed before any result and
  amended once, A1, before the confirmation run), experiments/,
  docs/RESULTS.md, and 154 tests.

Findings: see README and docs/RESULTS.md. Two of 23 pre-registered
hypotheses were not supported (H5, H14).
