## Interpretation (hand-written, SYNTHETIC)

Numbers quoted here are from the confirmation set unless stated. Of the
23 pre-registered hypotheses, 21 came out as written (19 supported, 2
controls retained) and 2 did not (H5 and H14). Both failures also failed
in the development set, and neither was edited away.

### What held

- The supplied README numbers reproduce at seed 42 (k_est +1.00 and
  -1.00, omega -1.000, coherence 0.990, wave-order 1.000), the six WAV
  files regenerate byte for byte on Python 3.10 to 3.13, and the audio
  of the two mono waves has its spectral peak at 63.662 Hz, matching
  |omega| dt rate / (2 pi) = 63.662 Hz (study E). The pitch of the tone is
  set by the drive frequency alone: forward and reverse waves differ by
  0.0 Hz, so pitch carries no direction.
- Direction is carried by the spatial gradient, and survives into the
  stereo audio: the lag between the two channels has the right sign in
  all 200 replicates (H22), the lag of the time-reversed audio flips sign
  in all 200 (H23), and the lag error is 0.0004 samples without noise.
  This is the one mapping in the repository where direction is present in
  the audio signal itself. Whether a listener can use a 31-sample (3.9 ms)
  interchannel delay is a perception question; no listening test was run.
- Without noise the sensor pitch is exact at every drive frequency from
  0.25 to 16 (0.0 relative error, H1), and also at 32 on average (0.35 %,
  CI [0, 1.0 %]; H2). The CI upper end (1.04 %) is just above the 1 % threshold
  while the mean is 0.35 %, so the error is not uniformly tiny at 32; the
  test against 1 % is supported, but "exact at 32" would be an
  overstatement.
- The moving sensor (Doppler-like shift) agrees with
  omega_obs = -Omega + 2 pi k v / n to rounding in the noise-free ring
  (H17), and the frozen-phase speed gives silence (H18). The agreement is
  that tight because the locked state is exactly linear in space; the
  study checks that the code implements the derivation, it does not
  discover anything. At noise 0.5 the mean absolute error is 0.0024 rad
  per time unit (CI [0.0023, 0.0026]) and the "frozen" pitch is 0.15 Hz
  (CI [0.14, 0.17]) rather than 0. It is a kinematic effect of the
  sensor's motion through a standing pattern of phase, not a wave
  phenomenon in a medium. Because the audio is cos(phase), the sign of
  the shift is not audible: a sensor at speed 20 hears 61.3 Hz, the
  mirror of -1 + 1.96.
- A second spatial axis exists in a 2D membrane: three sensors on a
  12 x 12 torus recovered the sign of both wave-vector components in
  every replicate (H19), and a pair along x is blind to ky (H20, 0.0 rad
  difference). The implication for sound is a limit, not a feature: a
  stereo pair is two channels and carries one gap, so it renders one
  axis. A second axis needs a third channel or another mapping, and no
  such mapping was built or tested.
- Controls behaved: a shuffled-phase sensor is at chance (0.496, CI
  [0.488, 0.503]; H21 retained); a sensor attached to a ring never
  changed its trajectory (200 of 200) and a deliberately mutating sensor
  was caught in 200 of 200 (study F).

### What did not hold, and what was surprising

- H5 (pv more accurate than fft under noise) failed in the opposite
  direction. At noise 1 the spectral estimate of the audio is off by
  0.31 % but the estimate from the sensor's phase history is off by
  3.0 % (CI [2.5, 3.5]); at noise 2 the spectral estimate is off by 1.4 %
  and the phase-history estimate by 65 % (CI [62.5, 67.3]). The aided
  diagnostic (amendment A1) gives the same 65 %, so at noise 2 this is
  real phase slipping, not a measurement artefact: the sensor's phase
  drifts away from the drive while the audio still has its strongest
  spectral line at the drive frequency. The honest reading is that the
  phase-based pitch is the less robust one in this model.
- H3 was supported as written (at Omega 48 the pv error is 98 %, CI
  [97.8, 98.2]) but my explanation was only half right. The protocol
  expected the Euler stability limit to break high pitches. What
  actually breaks is the sensor's phase-velocity estimate: the lag
  between ring and drive oscillates beyond the stability limit and
  pushes single steps past pi, so the wrapped steps alias. The audio
  pitch is still right (spectral error 0.0008 %) and the aided
  estimator, which removes step aliasing, is off by only 0.012 %
  (CI [0.011, 0.014]). So at Omega 48 the tone is correct and the
  ring is only partly locked (wave-order 0.846); the number that
  fails is the sensor's own pitch reading.
- H14 failed. I expected an undriven ring to show wave-order near
  zero (below 0.3). It is 0.343 (CI [0.299, 0.386]). Diffusive coupling
  relaxes random initial phases into a twisted state with a winding
  number; 22.5 % of rings (CI [17, 28]) end with winding +1, which
  matches the k = +1 profile in space and gives wave-order near 1, 24.5 %
  end at 0 and 53 % at other windings. Wave-order measures agreement with
  a spatial profile, so it is not a pure indicator of being driven in an
  undriven ring either. This explanation fits the winding fractions but
  was not tested beyond them.
- "Clarity tracks locking" is not what the sensor coherence measures.
  The audio RMS follows coherence almost perfectly (Pearson 0.9994, H15),
  but that is built in: the audio is cos(phase) times coherence. The
  substantive finding is that coherence is a local-alignment measure.
  With the drive weaker than its frequency (A = 0.5, locking lost) the
  coherence is 0.969 (CI [0.963, 0.974]) against 0.990 when locked, while
  wave-order drops to 0.42; an undriven coupled ring has coherence 0.968
  (H12, CI [0.962, 0.973]); only the uncoupled undriven ring is low,
  0.389 (H13; the analytic value for five random phases is about 0.4).
  Coherence does fall with noise (0.99 at noise 0 to 0.42 at noise 4),
  so "loud = locally ordered, quiet = noisy" holds, but "loud = locked to
  a drive" does not.
- Direction from a single reading is fragile. The supplied README reports
  k_est from the last sample; with noise it is right 0.65 of the time at
  noise 0.5 and 0.57 at noise 1 (H7), where the long-window estimator
  is right 1.00 and 0.95 (H8). The long-window estimator still fails at
  noise 2 (0.63) and, without noise, when the drive is weaker than its
  frequency (0.56, near chance; H9): direction recovery needs locking.
  Coupling matters: at noise 0.5 with no coupling the window estimator is
  right 0.89 of the time (CI [0.86, 0.92]) against 1.00 with the default
  coupling.
- The stereo gap is at its limit at d = n/2: the gap is +-pi, its sign
  is ambiguous, and the sign accuracy is 0.49 (CI [0.44, 0.54], H10,
  determined by floating-point noise rather than physics). Separation
  31 with noise still gets the sign 0.9975 of the time. With noise 0.5
  the gap error is about 0.027 rad (CI [0.025, 0.030]) at d = 16.

### Reading the WAV checks (study E)

All 20 deterministic checks pass: the heart's thump decays with a time
constant of 639.96 samples (label 640), its fundamental is 55.00 Hz, the
five thumps are 6400 samples (0.80 s) apart, the brain's right thump
follows the left by 3440 samples (0.43 s), and the stereo lag of the wave
files is +-31.416 samples. These show that the implementation matches its
own labels. They say nothing about whether the labels describe anything,
and the heart and brain scenes remain pulse-arrival toys.
