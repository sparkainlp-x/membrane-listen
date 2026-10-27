# Study protocol (pre-registration note)

Status: committed before any study result existed in this repository.
Everything below concerns a SYNTHETIC sonification of a classical
phase-oscillator model. Nothing here is a statement about real hearts,
brains, sound, perception or any clinical quantity, and none of the
studies can support such a statement. No listening test was run and none
is planned in this protocol: claims about what anyone hears are out of
scope.

## What was already known before this note

- The supplied package, its README numbers (seed 42: k_est +1.00 and
  -1.00, omega -1.000, coherence 0.990, wave-order 1.000) and its six
  tests were seen and reproduced before this protocol was written; the
  six WAV files regenerate byte for byte (see CHANGELOG).
- While adding code, unit tests at the default seed (42) were run for the
  Doppler-like shift (the derivation below matched within 0.01 rad per
  time unit for k = +1 and -1 and speeds -2 to 2 nodes per time unit),
  for the 2D torus (it locks to plane waves, and gap signs match), for
  noise (wave-order falls as noise rises) and for the estimators on
  analytic signals. Hypotheses H17 to H20 are therefore confirmations of
  small-sample observations on new seeds, not blind predictions.
- No multi-seed output of any study below had been run or seen. The
  thresholds come from physical reasoning written out in the
  "Derivations" section, not from data.

## Units of analysis and seeds

- A replicate is one seed s. Seed s sets the ring's initial phases and
  its noise and detuning streams, so replicates differ in everything
  random. Every study below is computed within each replicate; the
  summary is the mean over replicates with a percentile bootstrap 95 %
  confidence interval (5000 resamples; 10000 for hypothesis tests).
- Development set DEV: seeds 1000 to 1199 (200 replicates). Used to debug
  the pipeline and to look at behaviour. Not used for any confirmatory
  claim.
- Confirmation set CONFIRM: seeds 5000 to 5199 (200 replicates), disjoint
  from DEV. Every confirmatory number in `docs/RESULTS.md` comes from
  CONFIRM, which is run once after the code is frozen. A smoke set (seeds
  9001 to 9005) is used only in CI. Seed 42 is reserved for the committed
  WAV scenes and is in none of these sets.
- Random streams: the ring draws initial phases from `random.Random(seed)`
  as supplied; noise, detuning, and the shuffle control use separate
  streams from `membrane_listen.stats.derive_seed(role, ...)` (SHA-256 of
  a role label and the seed), roles `ring-noise`, `ring-detune`,
  `torus-noise`, `shuffle`, `boot`.
- Stopping rule: there is none beyond the fixed 200 replicates per set;
  nothing is added or dropped after seeing results. If the confirmation
  script must change after it has been run, those results are void; the
  change is logged as an amendment and the study is rerun once on a fresh
  disjoint set (seeds 7000 to 7199) which is declared before it is run.
- Amendments are committed before the confirmation run and are numbered
  A1, A2, ... at the end of this file.

## Fixed setup (unless a study varies it)

Ring of n = 64 oscillators, coupling 2.0 (mean of the two neighbours),
drive amplitude A = 1.5, drive frequency Omega = 1.0, wave number k = +1,
dt = 0.05 time units per audio sample, noise 0, no detuning, sample rate
8000 Hz (so 1 rad per time unit is 63.66 Hz). Warm-up 400 steps, then
record 2048 steps (0.256 s of audio, 102.4 time units). Sensors read
interpolated phase at node position 10 with window 2 (5 nodes) unless
stated. The audio is cos(phase) x local coherence.

## Estimators (all in `membrane_listen/estimators.py`)

- `pv`: pitch from the sum of wrapped successive phase differences of the
  sensor phase, divided by elapsed time (rad per time unit), converted to
  Hz as |omega| dt rate / (2 pi).
- `fft`: pitch from the largest peak of the Hann-windowed, zero-padded
  (x4) FFT of the audio, parabolic interpolation.
- `last`: direction from the sign of k_est of the final single reading
  (as in the supplied README).
- `win`: direction from the sign of the circular mean of the per-sample
  gradients over the 2048 recorded readings.
- Stereo phase gap: circular mean over time of wrap(phase_b - phase_a).
- Audio lag: `stereo_lag` of the two audio channels, search range +-39
  samples (below half the 125.7-sample period, so no period ambiguity).

## Derivations (written before any multi-seed run)

1. Locked state. With drive phase phi_i = 2 pi k i / n - Omega t and
   uniform lag delta, theta_i = phi_i - delta. The coupling term cancels
   for a linear phase profile, and d theta / dt = -Omega requires
   sin(delta) = Omega / A (Adler condition A > Omega). The sensor's phase
   velocity is therefore -Omega whatever k is, and the audio frequency is
   Omega dt rate / (2 pi) Hz: 63.66 Hz for Omega = 1.
2. Euler limit. The per-step map for the lag has slope
   1 - dt A cos(delta) with cos(delta) = sqrt(1 - (Omega/A)^2). It is
   stable only if dt sqrt(A^2 - Omega^2) < 2. With A = 1.5 Omega that is
   Omega < about 35.8; the Nyquist limit |omega| dt < pi is Omega < 62.8.
   So the stability limit of the integrator, not Nyquist, is expected to
   be what breaks high pitches. Aliasing itself (a phase step beyond pi)
   is checked on analytic signals, not on the ring.
3. Direction. The per-node gradient of a unit wave is 2 pi / 64 = 0.098
   rad. Phase noise of a few tenths of a radian per node is enough to
   hide it in one reading, so the single-reading estimator is expected to
   fail at noise levels where a long-window mean still works.
4. Stereo. Two sensors d nodes apart see a phase gap 2 pi k d / n. At
   d = n / 2 the gap is +-pi and its sign is ambiguous.
5. Audio lag. With gap delta between channels, the second channel is a
   delayed copy of the first by delta / (Omega dt) samples when
   delta > 0: +31.4 samples for d = 16, k = +1 and -31.4 for k = -1.
   Reversing both channels in time flips the sign of the lag. The mono
   audio cos(phase) is even in phase, so pitch carries no direction.
6. Doppler-like shift. A sensor moving at v nodes per time unit sees
   omega_obs = -Omega + 2 pi k v / n. At v = Omega n / (2 pi k) the
   observed phase is frozen (zero pitch). This is kinematics of the
   sensor, not a statement about waves in a medium.
7. Undriven controls. Without drive (A = 0) but with coupling, diffusive
   coupling is expected to align neighbours, so the local coherence is
   expected to be HIGH even though nothing is driving the ring (clarity
   is local alignment, not locking to a drive); wave-order is the quantity
   that separates driven from undriven. Without coupling or drive, the
   five random phases in the sensor window give a coherence near 0.4.

## Studies and hypotheses

Study A, pitch: Omega in {0.25, 0.5, 1, 2, 4, 8, 16, 32, 48} with
A = 1.5 max(1, Omega); ring sizes n in {16, 32, 128} at Omega = 1; noise
sigma in {0.5, 1, 2} at Omega = 1. Metric: relative error of the pitch
estimate against Omega dt rate / (2 pi).

Study B, direction and stereo: noise sigma in {0, 0.1, 0.25, 0.5, 1, 2},
k = +1 and -1; coupling 0 and 2 at sigma 0.5; lock loss with A in {0.5,
1.0, 1.25} at sigma 0; sensors at 10 and 10 + d for d in {1, 2, 4, 8, 16,
24, 31, 32} at sigma 0 and 0.5; the audio-lag direction estimator on the
d = 16 pair and on its time-reversed audio.

Study C, coherence and loudness: noise sigma in {0, 0.25, 0.5, 1, 2, 4};
null controls: undriven coupled ring (A = 0), undriven uncoupled ring
(A = 0, coupling 0); lock loss A = 0.5.

Study D, open questions from DESIGN.md. D1: a moving sensor
(`follow_probe`) at speeds {-2, -1, -0.5, 0, 0.5, 1, 2} and at the
frozen-phase speed and at 20 nodes per time unit, k = +1 and -1. D2: a
12 x 12 torus with wave vectors (+-1, +-1) and sensors at (0,0), (3,0),
(0,3); warm-up 300 steps, record 300.

Study E, WAV checks (no seeds; computed from the committed files by
`experiments/wav_checks.py`): FFT peak of the two mono waves against
63.66 Hz; forward-minus-reverse peak difference; thump decay constant
against 640 samples (80 ms); inter-onset intervals against 6400 samples
(0.80 s); stereo lag of the two stereo files against +-31.4 samples and
their time-reversed versions; the brain spread of 3440 samples; peak
level below full scale; and the analytic aliasing table. These check that
the implementation does what its labels say; they are deterministic and
are reported as pass or fail against stated tolerances, outside the
Holm family.

Study F, negative controls: F1, shuffled-phase sensor (random permutation
of the node phases of the final state, 40 shuffles per k) gives no
direction; F2, a sensor attached to a ring never changes its trajectory
(fraction of replicates with an identical trajectory), and a deliberately
mutating sensor is always detected.

### Confirmatory hypotheses (Holm correction over all 23)

Each is a test of the replicate-level mean against a null value, with
the alternative shown. A hypothesis is "supported" when its Holm-adjusted
p is below 0.05, except H10 and H21, which are equivalence-type controls
(see the rule below). Keys are the names in the result files.

| ID | Key | Null | Alt | Statement |
|---|---|---|---|---|
| H1 | A/om1/pv_relerr | 0.01 | less | at Omega 1 the pv pitch error is below 1 % |
| H2 | A/om32/pv_relerr | 0.01 | less | at Omega 32 (inside the Euler limit) the pv error is below 1 % |
| H3 | A/om48/pv_relerr | 0.05 | greater | at Omega 48 (beyond the Euler limit, below Nyquist) the pv error exceeds 5 % |
| H4 | A/sig1/pv_relerr | 0.05 | less | at noise 1 the pv pitch error is below 5 % |
| H5 | A/sig1/diff_fft_minus_pv | 0.0 | greater | at noise 1 the pv estimator is more accurate than the fft estimator |
| H6 | B/s0/win_acc | 0.99 | greater | direction accuracy with the long-window estimator exceeds 0.99 without noise |
| H7 | B/s1/last_acc | 0.75 | less | with noise 1 the single-reading direction accuracy is below 0.75 |
| H8 | B/s1/diff_win_minus_last | 0.0 | greater | with noise 1 the long-window estimator beats the single-reading one |
| H9 | B/lockloss_a0.5/win_acc | 0.99 | less | with the drive weaker than its frequency (A 0.5) direction is not recovered reliably |
| H10 | B/d32/sign_acc | 0.5 | two-sided | at d = n/2 the gap sign is at chance (equivalence rule) |
| H11 | B/d16/gap_err | 0.01 | less | at d = 16 and no noise the mean gap error is below 0.01 rad |
| H12 | C/undriven_coupled/coherence | 0.9 | greater | the undriven coupled ring still shows local coherence above 0.9 |
| H13 | C/undriven_uncoupled/coherence | 0.6 | less | the undriven uncoupled ring has coherence below 0.6 |
| H14 | C/undriven_coupled/wave_order | 0.3 | less | the undriven ring has wave-order below 0.3 |
| H15 | C/corr_coh_rms | 0.9 | greater | audio RMS tracks coherence across noise levels (Pearson above 0.9) |
| H16 | C/s0/coherence | 0.98 | greater | driven, no noise: coherence above 0.98 (the README says 0.990) |
| H17 | D1/low_speeds/abs_err | 0.01 | less | moving-sensor shift agrees with the derivation within 0.01 rad per time unit |
| H18 | D1/frozen/hz | 1.0 | less | at the frozen-phase speed the pitch is below 1 Hz |
| H19 | D2/sign_acc | 0.99 | greater | three sensors on the torus recover both wave-vector signs |
| H20 | D2/xpair_ky_leak | 0.01 | less | the x pair's gap does not depend on ky (difference below 0.01 rad) |
| H21 | F1/shuffle_acc | 0.5 | two-sided | a shuffled-phase sensor gives no direction (equivalence rule) |
| H22 | B/audio_lag/sign_acc | 0.99 | greater | the audio-only lag gets the direction right |
| H23 | B/audio_lag_reversed/flip_acc | 0.99 | greater | time-reversed audio gives the opposite lag sign, as the design says |

Equivalence rule (H10 and H21 only): "supported" means Holm-adjusted p
is at least 0.05 and the 95 % bootstrap CI of the mean lies inside
[0.40, 0.60] for H10 and [0.45, 0.55] for H21. This is a retention rule
for a control, not evidence that the true value is exactly 0.5.

Everything else in `docs/RESULTS.md` (all other keys, ring-size and
coupling variants, the Omega sweep outside H1 to H3, the lock-loss
sweep, per-separation gap tables, speed tables) is exploratory:
reported with CIs, no p-values.

### Reporting rules

- Every table is generated by a committed script from a committed JSON
  file; no number in RESULTS.md is typed by hand.
- Failures and null results are reported on the same footing as the
  rest; a hypothesis that is not supported is written up as not supported.
- RESULTS.md carries a limitations section: SYNTHETIC; classical
  simulation; no listening test; no claim about hearing, perception or
  physiology; the pulse scenes (heart and brain) are labelled
  pulse-arrival toys and are checked only for internal consistency.
- Tie, rounding and platform: values are rounded to 6 decimals; results
  are expected to agree across machines to that precision except where
  stated.

## Amendments

(none yet)
