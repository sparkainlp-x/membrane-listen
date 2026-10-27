# Results

SYNTHETIC. Every number below comes from committed scripts
(`experiments/`) run on a classical simulation of coupled phase
oscillators. Nothing here is a recording, a measurement of anything
real, a listening test or a clinical result. The protocol that fixed
the hypotheses, seeds and tests before any result existed is
`docs/PROTOCOL.md`.

Regenerate: `python -m experiments.run_all --set confirm --out
docs/results/confirm.json`, `python -m experiments.wav_checks --out
docs/results/wav_checks.json`, then `python -m experiments.render_results`.

## Confirmatory hypotheses (confirmation set, seeds 5000 to 5199, 200 replicates)

Holm correction over 23 hypotheses. 21 of 23 came out supported (or, for the two controls, retained).

| ID | Statement | Key | Mean [95 % CI] | Test vs null | Holm p | Outcome |
|---|---|---|---|---|---|---|
| H1 | at Omega 1 the pv pitch error is below 1 % | `A/om1/pv_relerr` | 0.0000 [0.0000, 0.0000] | less 0.01 | 0.0023 | supported |
| H2 | at Omega 32 (inside the Euler limit) the pv error is below 1 % | `A/om32/pv_relerr` | 0.0035 [0.0000, 0.0104] | less 0.01 | 0.0023 | supported |
| H3 | at Omega 48 (beyond the Euler limit, below Nyquist) the pv error exceeds 5 % | `A/om48/pv_relerr` | 0.9802 [0.9783, 0.9821] | greater 0.05 | 0.0023 | supported |
| H4 | at noise 1 the pv pitch error is below 5 % | `A/sig1/pv_relerr` | 0.0301 [0.0250, 0.0355] | less 0.05 | 0.0023 | supported |
| H5 | at noise 1 the pv estimator is more accurate than the fft estimator | `A/sig1/diff_fft_minus_pv` | -0.0270 [-0.0323, -0.0218] | greater 0 | 1.0000 | NOT supported |
| H6 | direction accuracy of the long-window estimator exceeds 0.99 without noise | `B/s0/win_acc` | 1.0000 [1.0000, 1.0000] | greater 0.99 | 0.0023 | supported |
| H7 | with noise 1 the single-reading direction accuracy is below 0.75 | `B/s1/last_acc` | 0.5700 [0.5475, 0.5950] | less 0.75 | 0.0023 | supported |
| H8 | with noise 1 the long-window estimator beats the single-reading one | `B/s1/diff_win_minus_last` | 0.3800 [0.3500, 0.4100] | greater 0 | 0.0023 | supported |
| H9 | with the drive weaker than its frequency (A 0.5) direction is not recovered reliably | `B/lockloss_a0.5/win_acc` | 0.5625 [0.5225, 0.6050] | less 0.99 | 0.0023 | supported |
| H10 | at d = n/2 the gap sign is at chance (equivalence rule) | `B/d32/sign_acc` | 0.4875 [0.4400, 0.5375] | two-sided 0.5 | 1.0000 | control retained (consistent with chance) |
| H11 | at d = 16 and no noise the mean gap error is below 0.01 rad | `B/d16/gap_err` | 0.0000 [0.0000, 0.0000] | less 0.01 | 0.0023 | supported |
| H12 | the undriven coupled ring still shows local coherence above 0.9 | `C/undriven_coupled/coherence` | 0.9680 [0.9625, 0.9733] | greater 0.9 | 0.0023 | supported |
| H13 | the undriven uncoupled ring has coherence below 0.6 | `C/undriven_uncoupled/coherence` | 0.3886 [0.3618, 0.4162] | less 0.6 | 0.0023 | supported |
| H14 | the undriven ring has wave-order below 0.3 | `C/undriven_coupled/wave_order` | 0.3427 [0.2992, 0.3860] | less 0.3 | 1.0000 | NOT supported |
| H15 | audio RMS tracks coherence across noise levels (Pearson above 0.9) | `C/corr_coh_rms` | 0.9994 [0.9993, 0.9994] | greater 0.9 | 0.0023 | supported |
| H16 | driven, no noise: coherence above 0.98 (the README says 0.990) | `C/s0/coherence` | 0.9904 [0.9904, 0.9904] | greater 0.98 | 0.0023 | supported |
| H17 | moving-sensor shift agrees with the derivation within 0.01 rad per time unit | `D1/low_speeds/abs_err` | 0.0000 [0.0000, 0.0000] | less 0.01 | 0.0023 | supported |
| H18 | at the frozen-phase speed the pitch is below 1 Hz | `D1/frozen/hz` | 0.0000 [0.0000, 0.0000] | less 1 | 0.0023 | supported |
| H19 | three sensors on the torus recover both wave-vector signs | `D2/sign_acc` | 1.0000 [1.0000, 1.0000] | greater 0.99 | 0.0023 | supported |
| H20 | the x pair's gap does not depend on ky (difference below 0.01 rad) | `D2/xpair_ky_leak` | 0.0000 [0.0000, 0.0000] | less 0.01 | 0.0023 | supported |
| H21 | a shuffled-phase sensor gives no direction (equivalence rule) | `F1/shuffle_acc` | 0.4956 [0.4881, 0.5032] | two-sided 0.5 | 1.0000 | control retained (consistent with chance) |
| H22 | the audio-only lag gets the direction right | `B/audio_lag/sign_acc` | 1.0000 [1.0000, 1.0000] | greater 0.99 | 0.0023 | supported |
| H23 | time-reversed audio gives the opposite lag sign, as the design says | `B/audio_lag_reversed/flip_acc` | 1.0000 [1.0000, 1.0000] | greater 0.99 | 0.0023 | supported |

## Agreement with the development set (seeds 1000 to 1199)

| ID | Development set | Confirmation set | Agreement |
|---|---|---|---|
| H1 | supported | supported | same |
| H2 | supported | supported | same |
| H3 | supported | supported | same |
| H4 | supported | supported | same |
| H5 | NOT supported | NOT supported | same |
| H6 | supported | supported | same |
| H7 | supported | supported | same |
| H8 | supported | supported | same |
| H9 | supported | supported | same |
| H10 | control retained (consistent with chance) | control retained (consistent with chance) | same |
| H11 | supported | supported | same |
| H12 | supported | supported | same |
| H13 | supported | supported | same |
| H14 | NOT supported | NOT supported | same |
| H15 | supported | supported | same |
| H16 | supported | supported | same |
| H17 | supported | supported | same |
| H18 | supported | supported | same |
| H19 | supported | supported | same |
| H20 | supported | supported | same |
| H21 | control retained (consistent with chance) | control retained (consistent with chance) | same |
| H22 | supported | supported | same |
| H23 | supported | supported | same |

## All studies (confirmation set; mean [95 % bootstrap CI] over replicates)

### Study A: pitch accuracy

Drive frequency sweep (n = 64, A = 1.5 max(1, Omega), no noise):

| Omega | True Hz | pv rel. error | fft rel. error | pv aided rel. error (diagnostic) | wave-order |
|---|---|---|---|---|---|
| 0.25 | 15.92 | 0.0000 [0.0000, 0.0000] | 0.0002 [0.0002, 0.0002] | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 0.5 | 31.83 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 1 | 63.66 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 2 | 127.32 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 4 | 254.65 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 8 | 509.30 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 16 | 1018.59 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 32 | 2037.18 | 0.0035 [0.0000, 0.0104] | 0.0035 [0.0000, 0.0104] | 0.0000 [0.0000, 0.0000] | 0.984 [0.981, 0.987] |
| 48 | 3055.77 | 0.9802 [0.9783, 0.9821] | 0.0000 [0.0000, 0.0000] | 0.0001 [0.0001, 0.0001] | 0.846 [0.844, 0.848] |

Ring size (Omega 1):

| Ring size n | pv rel. error | fft rel. error | wave-order |
|---|---|---|---|
| 16 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 32 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 128 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |

Noise (Omega 1, n = 64):

| Noise sigma | pv rel. error | fft rel. error | fft minus pv | pv aided rel. error (diagnostic) | wave-order |
|---|---|---|---|---|---|
| 0.5 | 0.0026 [0.0023, 0.0029] | 0.0012 [0.0011, 0.0013] | -0.0014 [-0.0017, -0.0011] | 0.0026 [0.0023, 0.0029] | 0.972 [0.971, 0.973] |
| 1 | 0.0301 [0.0250, 0.0355] | 0.0031 [0.0028, 0.0034] | -0.0270 [-0.0323, -0.0218] | 0.0301 [0.0249, 0.0356] | 0.847 [0.841, 0.852] |
| 2 | 0.6493 [0.6248, 0.6734] | 0.0137 [0.0072, 0.0238] | -0.6356 [-0.6606, -0.6097] | 0.6493 [0.6252, 0.6738] | 0.412 [0.399, 0.425] |

### Study B: direction recovery and stereo gap

Direction accuracy (fraction of k = +1 and k = -1 runs with the right sign):

| Noise sigma | single-reading accuracy | long-window accuracy | window minus single | wave-order |
|---|---|---|---|---|
| 0 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 1.000 [1.000, 1.000] |
| 0.1 | 0.963 [0.943, 0.980] | 1.000 [1.000, 1.000] | 0.037 [0.020, 0.058] | 0.999 [0.999, 0.999] |
| 0.25 | 0.785 [0.750, 0.820] | 1.000 [1.000, 1.000] | 0.215 [0.180, 0.247] | 0.993 [0.993, 0.993] |
| 0.5 | 0.650 [0.620, 0.682] | 1.000 [1.000, 1.000] | 0.350 [0.318, 0.383] | 0.972 [0.971, 0.973] |
| 1 | 0.570 [0.547, 0.595] | 0.950 [0.927, 0.970] | 0.380 [0.350, 0.410] | 0.847 [0.841, 0.853] |
| 2 | 0.522 [0.495, 0.550] | 0.627 [0.595, 0.660] | 0.105 [0.065, 0.145] | 0.412 [0.399, 0.425] |

Other conditions:

| Condition | single-reading accuracy | long-window accuracy | wave-order |
|---|---|---|---|
| coupling 0, noise 0.5 | 0.560 [0.537, 0.583] | 0.892 [0.863, 0.920] | 0.925 [0.923, 0.928] |
| lock loss, A = 0.5 (Omega 1) | 0.555 [0.512, 0.598] | 0.562 [0.522, 0.605] | 0.438 [0.409, 0.467] |
| lock loss, A = 1 (Omega 1) | 0.938 [0.912, 0.960] | 0.815 [0.780, 0.848] | 0.961 [0.956, 0.966] |
| lock loss, A = 1.25 (Omega 1) | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] |

Stereo phase gap, noise 0:

| Separation d (nodes) | expected gap (rad) | gap error (rad) | gap sign accuracy |
|---|---|---|---|
| 1 | 0.0982 | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 2 | 0.1963 | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 4 | 0.3927 | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 8 | 0.7854 | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 16 | 1.5708 | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 24 | 2.3562 | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 31 | 3.0434 | 0.0000 [0.0000, 0.0000] | 1.000 [1.000, 1.000] |
| 32 | 3.1416 | 0.0000 [0.0000, 0.0000] | 0.487 [0.440, 0.537] |

Stereo phase gap, noise 0.5:

| Separation d (nodes) | expected gap (rad) | gap error (rad) | gap sign accuracy |
|---|---|---|---|
| 1 | 0.0982 | 0.0177 [0.0159, 0.0195] | 1.000 [1.000, 1.000] |
| 2 | 0.1963 | 0.0226 [0.0202, 0.0251] | 1.000 [1.000, 1.000] |
| 4 | 0.3927 | 0.0282 [0.0254, 0.0312] | 1.000 [1.000, 1.000] |
| 8 | 0.7854 | 0.0298 [0.0265, 0.0330] | 1.000 [1.000, 1.000] |
| 16 | 1.5708 | 0.0273 [0.0246, 0.0300] | 1.000 [1.000, 1.000] |
| 24 | 2.3562 | 0.0285 [0.0256, 0.0314] | 1.000 [1.000, 1.000] |
| 31 | 3.0434 | 0.0296 [0.0266, 0.0327] | 0.998 [0.993, 1.000] |
| 32 | 3.1416 | 0.0279 [0.0251, 0.0310] | 0.500 [0.500, 0.500] |

Audio-only direction (two audio channels from sensors 10 and 26, no access to phases):

| Measure | Mean [95 % CI] |
|---|---|
| lag sign accuracy | 1.000 [1.000, 1.000] |
| lag error against +-31.42 samples | 0.0004 [0.0004, 0.0004] |
| time-reversed audio flips the lag sign | 1.000 [1.000, 1.000] |

### Study C: coherence, loudness and null controls

| Noise sigma | coherence | audio RMS | wave-order |
|---|---|---|---|
| 0 | 0.990 [0.990, 0.990] | 0.703 [0.703, 0.703] | 1.000 [1.000, 1.000] |
| 0.25 | 0.986 [0.986, 0.986] | 0.699 [0.699, 0.700] | 0.993 [0.993, 0.993] |
| 0.5 | 0.972 [0.971, 0.972] | 0.689 [0.688, 0.690] | 0.972 [0.971, 0.973] |
| 1 | 0.890 [0.888, 0.892] | 0.633 [0.631, 0.635] | 0.847 [0.841, 0.853] |
| 2 | 0.579 [0.576, 0.581] | 0.438 [0.435, 0.440] | 0.412 [0.399, 0.425] |
| 4 | 0.422 [0.421, 0.423] | 0.331 [0.330, 0.332] | 0.135 [0.125, 0.145] |

Controls:

| Case | coherence | audio RMS | wave-order |
|---|---|---|---|
| driven, no noise (reference) | 0.990 [0.990, 0.990] | 0.703 [0.703, 0.703] | 1.000 [1.000, 1.000] |
| undriven, coupled (A = 0) | 0.968 [0.962, 0.973] | 0.660 [0.627, 0.692] | 0.343 [0.299, 0.386] |
| undriven, uncoupled (A = 0, coupling 0) | 0.389 [0.362, 0.416] | 0.241 [0.215, 0.268] | 0.107 [0.099, 0.115] |
| drive weaker than its frequency (A = 0.5) | 0.969 [0.963, 0.974] | 0.686 [0.682, 0.690] | 0.419 [0.379, 0.457] |

| Per-replicate correlation across the six noise levels | Mean [95 % CI] |
|---|---|
| Pearson(coherence, audio RMS) | 0.999 [0.999, 0.999] |
| Pearson(coherence, wave-order) | 0.992 [0.990, 0.993] |

Winding numbers (amendment A1, diagnostic):

| Winding number of the final undriven coupled ring | Fraction of replicates [95 % CI] |
|---|---|
| 0 | 0.245 [0.190, 0.305] |
| +1 | 0.225 [0.170, 0.280] |
| any other | 0.530 [0.460, 0.600] |

### Study D: the two open questions

D1, a moving sensor (Doppler-like shift); a kinematic effect of the sensor's motion, not a wave in a medium:

| Sensor speed v (nodes per time unit) | expected omega (-1 + 2 pi k v / 64) | abs. error (rad per time unit) |
|---|---|---|
| -2 | -1 + -0.1963 k | 0.00000 [0.00000, 0.00000] |
| -1 | -1 + -0.0982 k | 0.00000 [0.00000, 0.00000] |
| -0.5 | -1 + -0.0491 k | 0.00000 [0.00000, 0.00000] |
| 0 | -1 + +0.0000 k | 0.00000 [0.00000, 0.00000] |
| 0.5 | -1 + +0.0491 k | 0.00000 [0.00000, 0.00000] |
| 1 | -1 + +0.0982 k | 0.00000 [0.00000, 0.00000] |
| 2 | -1 + +0.1963 k | 0.00000 [0.00000, 0.00000] |
| frozen-phase speed 10.186 k | 0 | 0.00000 [0.00000, 0.00000] |
| 20 k | -1 + 1.9635 k | 0.00000 [0.00000, 0.00000] |

| Measure | Mean [95 % CI] |
|---|---|
| low speeds, mean abs. error (rad per time unit) | 0.00000 [0.00000, 0.00000] |
| pitch at the frozen-phase speed (Hz) | 0.0000 [0.0000, 0.0000] |
| pitch at speed 20 (Hz), measured | 61.338 [61.338, 61.338] |
| pitch at speed 20 (Hz), expected | 61.338 [61.338, 61.338] |

D1 repeated with noise:

| Measure at noise 0.5 (amendment A1, exploratory) | Mean [95 % CI] |
|---|---|
| low speeds, mean abs. error (rad per time unit) | 0.00243 [0.00228, 0.00260] |
| pitch at the frozen-phase speed (Hz) | 0.1546 [0.1417, 0.1686] |
| pitch at speed 20 (Hz), measured | 61.326 [61.300, 61.352] |
| pitch at speed 20 (Hz), expected | 61.338 [61.338, 61.338] |

D2, a 12 x 12 torus as a second spatial axis (EXPERIMENTAL):

| Measure | Mean [95 % CI] |
|---|---|
| both wave-vector signs recovered from 3 sensors (4 quadrants) | 1.000 [1.000, 1.000] |
| x-pair gap difference between ky = +1 and ky = -1 (rad) | 0.00000 [0.00000, 0.00000] |

### Study E: checks on the committed WAV files

Deterministic, no seeds; pass or fail against the stated tolerance. 20 checks, all pass: yes.


brain:

| Check | Measured | Expected | Tolerance | Unit | Pass |
|---|---|---|---|---|---|
| brain left thump count | 4 | 4 | 0 | thumps | yes |
| brain right thump count | 4 | 4 | 0 | thumps | yes |
| brain left-to-right spread (first onsets) | 3440 | 3440.0 | 30.0 | samples | yes |
| brain left-to-right spread | 0.43 | 0.43 | 0.005 | s | yes |
| brain left period | 9600.0 | 9600.0 | 1.0 | samples | yes |

heart:

| Check | Measured | Expected | Tolerance | Unit | Pass |
|---|---|---|---|---|---|
| heart thump count | 5 | 5 | 0 | thumps | yes |
| heart inter-onset interval (mean) | 6400.0 | 6400.0 | 1.0 | samples | yes |
| heart first onset minus nominal arrival (2560) | 8 | 0.0 | 30.0 | samples | yes |
| heart thump decay constant | 639.963342 | 640.0 | 19.2 | samples | yes |
| heart thump fundamental (fft of first thump) | 55.000057 | 55.0 | 2.0 | Hz | yes |
| heart pacemaker period | 0.8 | 0.8 | 0.001 | s | yes |

mono waves:

| Check | Measured | Expected | Tolerance | Unit | Pass |
|---|---|---|---|---|---|
| wave_forward.wav fft peak | 63.66196 | 63.661977 | 0.1 | Hz | yes |
| wave_forward.wav zero-crossing rate | 63.661977 | 63.661977 | 0.1 | Hz | yes |
| wave_reverse.wav fft peak | 63.66196 | 63.661977 | 0.1 | Hz | yes |
| wave_reverse.wav zero-crossing rate | 63.661978 | 63.661977 | 0.1 | Hz | yes |
| forward minus reverse peak (pitch carries no direction) | 0.0 | 0.0 | 0.1 | Hz | yes |

stereo waves:

| Check | Measured | Expected | Tolerance | Unit | Pass |
|---|---|---|---|---|---|
| wave_stereo_forward.wav audio lag | 31.415866 | 31.415927 | 1.0 | samples | yes |
| wave_stereo_forward.wav time-reversed audio lag | -31.415866 | -31.415927 | 1.0 | samples | yes |
| wave_stereo_reverse.wav audio lag | -31.41587 | -31.415927 | 1.0 | samples | yes |
| wave_stereo_reverse.wav time-reversed audio lag | 31.41587 | 31.415927 | 1.0 | samples | yes |

Aliasing of audio tones through the FFT pitch estimator (8000 Hz sampling, Nyquist 4000 Hz):

| True Hz | Expected Hz (folded) | Measured Hz |
|---|---|---|
| 100.0 | 100.0 | 100.001 |
| 1000.0 | 1000.0 | 1000.0 |
| 3900.0 | 3900.0 | 3899.999 |
| 4100.0 | 3900.0 | 3899.999 |
| 5000.0 | 3000.0 | 3000.0 |
| 7900.0 | 100.0 | 100.001 |
| 8100.0 | 100.0 | 100.001 |

Aliasing of a phase ramp through the pv estimator (per-sample step beyond pi folds):

| omega | Per-sample step (rad) | Expected omega | Measured omega |
|---|---|---|---|
| 1.0 | 0.05 | 1.0 | 1.0 |
| 30.0 | 1.5 | 30.0 | 30.0 |
| 60.0 | 3.0 | 60.0 | 60.0 |
| 62.0 | 3.1 | 62.0 | 62.0 |
| 64.0 | 3.2 | -61.663706 | -61.663706 |
| 70.0 | 3.5 | -55.663706 | -55.663706 |
| 100.0 | 5.0 | -25.663706 | -25.663706 |

### Study F: negative controls

| Control | Mean [95 % CI] |
|---|---|
| shuffled-phase sensor, direction accuracy (chance 0.5) | 0.496 [0.488, 0.503] |
| unshuffled sensor, direction accuracy | 1.000 [1.000, 1.000] |
| attached sensors leave the trajectory identical (fraction of replicates) | 1.000 [1.000, 1.000] |
| deliberately mutating sensor is detected (fraction of replicates) | 1.000 [1.000, 1.000] |

## Limitations

- SYNTHETIC classical simulation of a ring (and one torus) of phase
  oscillators with an explicit Euler integrator. Conclusions about the
  integrator (for example the stability limit) are conclusions about this
  code at dt = 0.05.
- No listening test was run. Nothing here says what anyone hears, finds
  clear, or can tell apart. "Pitch" means the frequency of the rendered
  audio signal, "loudness" means its RMS level, "clarity" means the
  sensor's local coherence; these are properties of numbers.
- The heart and brain scenes are pulse-arrival toys sonified as decaying
  thumps. They are checked in Study E only for internal consistency with
  their own labels. They are not anatomy, not electrophysiology, not an
  ECG or EEG, and not a medical device.
- Confidence intervals are percentile bootstrap intervals over 200
  replicate seeds. They describe seed-to-seed variation of this
  simulation, not uncertainty about any physical system.
- The brain scene's right-sensor delay is 0.59 s as supplied while its
  own label arithmetic gives 0.60 s; this is documented in DESIGN.md and
  left unchanged so the committed WAV is byte-identical to the supplied
  one.
- The development set was used for debugging and was looked at; the
  confirmation set was run once after the code was frozen.

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
