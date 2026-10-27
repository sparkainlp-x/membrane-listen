# DESIGN.md - membrane-listen

SYNTHETIC sonification of a classical phase-oscillator model. Nothing
here is a recording, an ECG, an EEG, a diagnosis or a medical device.
The first four sections are the supplied design notes, kept and
corrected; the later sections record what changed and why.

## Why two different sound models

The travelling wave is a real phase signal: cos(phase) is audible
directly, at about 64 Hz (phase velocity 1 rad per time unit, one
reading per audio sample at 8000 Hz). The heart and brain scenes are
not phase signals; they are pulse-arrival models, so they are
sonified as decaying thumps instead. Mixing the two without saying so
would have been dishonest: a thump is not a phase, and a tone is not
a beat. Each scene names its model in the README.

Correction to the arithmetic (the supplied text left out the time step).
The ring advances dt = 0.05 time units per audio sample, so a phase
velocity of omega rad per time unit is an audio frequency of
|omega| * dt * rate / (2 pi) Hz: 1 * 0.05 * 8000 / 6.2832 = 63.66 Hz.
The "about 64 Hz" claim is right; the formula 1/(2 pi) * rate = 1273 Hz
would only hold at dt = 1. The sign of omega is not audible, because
cos(phase) is an even function of phase.

## Why the two wave tones sound identical

A locked oscillator follows drive phase k * 2 pi i / N - Omega t, so at
fixed i its phase velocity is -Omega whatever k is. Pitch therefore
cannot carry direction in this model, and the demo does not pretend it
does. What carries direction is the spatial gradient: k_est = +1 vs -1,
and in the stereo files the phase gap between two sensors a quarter-ring
apart (+pi/2 vs -pi/2). If a future version wants direction audible in
mono, it needs a different mapping (for example gradient to stereo pan,
or gradient to a second tone), stated as a mapping, not as physics.

The two stereo files do carry direction in the audio itself: the second
channel is a copy of the first delayed by +31.4 samples (k = +1) or
-31.4 samples (k = -1), and reversing both channels in time flips the
sign. This is measured on the committed files in docs/RESULTS.md
(study E) and over 200 seeds (study B). Whether any listener can hear
31 samples (3.9 ms) of interchannel delay is a perception question; no
listening test was run, and none of this is a claim about perception.

## Test bugs found, not model bugs

- First heart test counted every sine zero-crossing as a thump
  (55 regions instead of 5). Fixed by counting arrival windows:
  loud in [arrival, arrival+1000], quiet in the gap before the next.
- Gap check ran past the end of the signal for the last thump
  (empty slice). Fixed by checking gaps only between thumps.
- (new) My first WAV header test unpacked the format chunk from bytes
  22 to 34, which is 12 bytes of a 14-byte structure. The offsets were
  wrong, not the writer; fixed to 22 to 36.
- (new) My first onset-count test used a 20000-sample pulse train and
  expected 4 onsets; the fourth arrival is at sample 21760, so only 3
  fit. Fixed by lengthening the train, not by changing the code.
- (new) My first stereo-lag test used lags up to 20 samples with a
  search range of +-60. A 100 Hz tone has an 80-sample period, so a lag
  of 20 and a lag of -60 are the same by correlation; the estimator
  returned -60. The estimator is documented to need a search range below
  half a period, and the tests and studies now respect that.
- (new) The first read-only test compared copies of the ring's whole
  attribute dictionary; adding a random-number generator to the ring
  made it fail because generators compare by identity. The test now
  compares generator states.

## Defects found in the supplied code (model code; fixed with tests)

1. Non-finite samples crashed the WAV writer with unhelpful errors
   (NaN: ValueError from int(); infinity: OverflowError). They now raise
   a clear ValueError and are never turned into numbers.
2. write_wav_stereo silently truncated the longer channel (zip). Unequal
   channel lengths now raise ValueError.
3. Out-of-range samples were silently clipped. Clipping is still the
   default for compatibility, but scenes are built with clip="error", so
   a scene that would clip fails to build. None of the six clips (peaks
   0.99 for the waves and 0.95 for the heart and brain).
4. pulse_train looped forever for period <= 0, wrote to the END of the
   buffer for a negative delay (negative list indices), and returned
   silence for tau <= 0. All raise ValueError now.
5. Ring accepted n < 3 (with n = 2 the two neighbours of a node are the
   same node; n = 0 built an empty ring), and dt <= 0 or non-finite
   parameters. Argument checks added.
6. Sensor accepted a NaN or infinite position (crash), a negative
   window (negative coherence) and a window wider than the ring (nodes
   counted several times). Argument checks added.
7. wrap() subtracted 2 pi in a loop, which never ends for an infinite
   angle. It now uses the exact IEEE remainder and raises ValueError for
   non-finite input; for ordinary angles it returns the same floats
   (tested against the supplied loop on 4001 angles).
8. The first reading's omega was 0.0, indistinguishable from a measured
   zero; it is NaN now, as is omega when no time has elapsed.
9. Ring.wave_order used built-in sum(), whose float rounding changed in
   Python 3.12: on Python 3.10 the supplied code returned
   1.0000000000000002 (a "length" above 1) and 1.0 on 3.12. It now uses
   exactly rounded sums (math.fsum) and returns 1.0 on every version.
   The committed WAV bytes were already identical on 3.10 to 3.13; the
   fix matters for the reported numbers.
10. DESIGN.md said the sensor class has follow_probe(); the supplied code
    had no such method. It now exists (it moves only the sensor, never
    the ring), and the Doppler question below is answered with it.

## Inconsistencies kept, not hidden

- The brain scene's right-sensor delay is 4720 samples (0.59 s). The
  label arithmetic in the supplied docstring (32 nodes to the end of the
  left chain at 0.01 s, a 0.12 s cross delay, 16 nodes into the right
  chain) gives 0.32 + 0.12 + 0.16 = 0.60 s = 4800 samples, so the
  stated "spread delay 0.43 s" would be 0.44 s. The supplied constant is
  kept so that brain_stereo.wav stays byte-identical to the supplied
  file; tests pin both numbers and the 80-sample difference.
- The heart and brain scenes are not simulated chains. A chain is
  reduced to one arrival delay per sensor; only the arrival time is
  modelled.
- The supplied README "Measured numbers" for the stereo waves said only
  "sensors 10 and 26". The phase gap is now measured in the build (+1.5708
  and -1.5708 rad, pi/2 to four decimals) instead of being asserted "by
  construction".

## Additions for the studies (defaults reproduce the supplied model)

- Ring noise (Euler-Maruyama, noise * sqrt(dt) * N(0,1) per node per
  step) and static detuning, both off by default. With both off the
  trajectory is bit-identical to the supplied model (test).
- Sensor.follow_probe(speed): nodes per time unit.
- membrane_listen.experimental.Torus: a 2D membrane, labelled EXPERIMENTAL.
- membrane_listen.estimators: pitch (phase velocity and FFT), direction
  (window mean), stereo phase gap and audio lag, onset and decay fits.

## Open questions (now answered by labelled experiments)

- Does a sensor riding the probe (moving position) hear a Doppler-like
  shift in this toy? Derived (omega_obs = -Omega + 2 pi k v / n) and
  measured in study D1; see docs/RESULTS.md for the agreement and its
  limits. It is a kinematic effect of the sensor's motion through a
  locked phase pattern.
- Would a 2D membrane give a richer stereo image (two sensor axes)?
  Study D2 asks it of a 12 x 12 torus with three sensors; see
  docs/RESULTS.md. This is an experiment, not a scene.
