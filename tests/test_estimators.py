import math
import unittest

from membrane_listen import (SAMPLE_RATE, TWO_PI, Ring, Sensor, pulse_train,
                             record_ring, wrap)
from membrane_listen import estimators as est


def tone(hz, n=2048, rate=SAMPLE_RATE, phase=0.0):
    return [math.cos(TWO_PI * hz * i / rate + phase) for i in range(n)]


class TestUnits(unittest.TestCase):
    def test_pitch_of_unit_phase_velocity(self):
        # Hz = |omega| * dt * rate / (2 pi) with dt = 0.05 per sample:
        # 63.66 Hz. Without dt the arithmetic would give 1273 Hz.
        self.assertAlmostEqual(est.omega_to_hz(1.0), 63.66197723675813,
                               places=9)
        self.assertAlmostEqual(est.omega_to_hz(-1.0), est.omega_to_hz(1.0))
        self.assertAlmostEqual(1.0 / TWO_PI * SAMPLE_RATE, 1273.2395447351628)
        self.assertAlmostEqual(est.hz_to_omega(est.omega_to_hz(3.7)), 3.7)

    def test_nyquist_omega(self):
        w = est.nyquist_omega()
        self.assertAlmostEqual(w, math.pi / 0.05)
        self.assertAlmostEqual(est.omega_to_hz(w), SAMPLE_RATE / 2)

    def test_ring_tone_matches_the_formula(self):
        _, _, rd = record_ring(1, steps=4096)
        audio = [r["signal"] for r in rd]
        hz = est.peak_frequency_hz(audio)
        self.assertAlmostEqual(hz, est.omega_to_hz(1.0), delta=0.1)
        self.assertAlmostEqual(est.zero_crossing_hz(audio),
                               est.omega_to_hz(1.0), delta=0.1)


class TestPhaseVelocity(unittest.TestCase):
    def test_exact_ramp(self):
        phases = [wrap(-0.7 * 0.05 * i) for i in range(500)]
        self.assertAlmostEqual(est.phase_velocity(phases), -0.7, places=9)

    def test_too_few_phases_is_nan(self):
        self.assertTrue(math.isnan(est.phase_velocity([0.1])))
        self.assertTrue(math.isnan(est.phase_velocity([])))

    def test_aliasing_above_nyquist(self):
        # per-sample step 0.05 * 70 = 3.5 rad > pi: aliases to 3.5 - 2 pi
        phases = [wrap(70.0 * 0.05 * i) for i in range(200)]
        self.assertAlmostEqual(est.phase_velocity(phases),
                               (3.5 - TWO_PI) / 0.05, places=6)

    def test_matches_sensor_omega_on_a_locked_ring(self):
        _, _, rd = record_ring(1, steps=500)
        v = est.phase_velocity([r["phase"] for r in rd])
        self.assertAlmostEqual(v, -1.0, places=3)


class TestCircular(unittest.TestCase):
    def test_wraparound_mean(self):
        m, r = est.circular_mean([math.pi - 0.1, -math.pi + 0.1])
        self.assertAlmostEqual(abs(m), math.pi, places=9)
        self.assertGreater(r, 0.99)

    def test_opposite_angles_cancel(self):
        m, r = est.circular_mean([0.0, math.pi])
        self.assertAlmostEqual(r, 0.0, places=12)

    def test_empty(self):
        m, r = est.circular_mean([])
        self.assertTrue(math.isnan(m))
        self.assertEqual(r, 0.0)

    def test_window_k_recovers_wave_number(self):
        _, _, rd = record_ring(-1, steps=300)
        k, r = est.window_k([x["gradient"] for x in rd], 64)
        self.assertAlmostEqual(k, -1.0, places=2)
        self.assertGreater(r, 0.99)

    def test_phase_gap(self):
        gap, r = est.phase_gap([0.0, 0.1, 0.2], [1.0, 1.1, 1.2])
        self.assertAlmostEqual(gap, 1.0, places=12)
        self.assertAlmostEqual(r, 1.0, places=12)


class TestFFT(unittest.TestCase):
    def test_matches_naive_dft(self):
        x = [math.sin(0.3 * i) + 0.1 * i % 3 for i in range(16)]
        got = est.fft(x)
        for k in range(16):
            want = sum(x[n] * complex(math.cos(TWO_PI * k * n / 16),
                                      -math.sin(TWO_PI * k * n / 16))
                       for n in range(16))
            self.assertAlmostEqual(abs(got[k] - want), 0.0, places=9)

    def test_rejects_non_power_of_two(self):
        for n in (0, 3, 12):
            with self.assertRaises(ValueError):
                est.fft([0.0] * n)


class TestPeakFrequency(unittest.TestCase):
    def test_pure_tones(self):
        for hz in (50.0, 63.66, 440.0, 1234.5, 3900.0):
            self.assertAlmostEqual(est.peak_frequency_hz(tone(hz)), hz,
                                   delta=0.3, msg=str(hz))

    def test_above_nyquist_aliases(self):
        # 4100 Hz sampled at 8000 Hz is indistinguishable from 3900 Hz
        self.assertAlmostEqual(est.peak_frequency_hz(tone(4100.0)), 3900.0,
                               delta=0.5)
        self.assertAlmostEqual(est.peak_frequency_hz(tone(8050.0)), 50.0,
                               delta=0.5)

    def test_silence_is_nan_and_short_input_raises(self):
        self.assertTrue(math.isnan(est.peak_frequency_hz([0.0] * 256)))
        with self.assertRaises(ValueError):
            est.peak_frequency_hz([0.0] * 4)

    def test_dc_offset_is_ignored(self):
        x = [v + 5.0 for v in tone(300.0)]
        self.assertAlmostEqual(est.peak_frequency_hz(x), 300.0, delta=0.3)

    def test_zero_crossing(self):
        self.assertAlmostEqual(est.zero_crossing_hz(tone(123.4, 4000)),
                               123.4, delta=0.05)
        self.assertTrue(math.isnan(est.zero_crossing_hz([0.0] * 50)))
        self.assertTrue(math.isnan(est.zero_crossing_hz([1.0] * 50)))


class TestStereoLag(unittest.TestCase):
    def test_known_lag_both_signs(self):
        a = tone(100.0, 2000)
        for lag in (-9.5, -3.0, 0.0, 4.25, 20.0, -30.0):
            b = [math.cos(TWO_PI * 100.0 * (i - lag) / SAMPLE_RATE)
                 for i in range(2000)]
            self.assertAlmostEqual(est.stereo_lag(a, b, 39), lag, delta=0.05)

    def test_silence_is_nan(self):
        self.assertTrue(math.isnan(est.stereo_lag([0.0] * 500, tone(50, 500), 10)))

    def test_bad_lengths(self):
        with self.assertRaises(ValueError):
            est.stereo_lag([0.0] * 10, [0.0] * 11, 2)
        with self.assertRaises(ValueError):
            est.stereo_lag(tone(50, 20), tone(50, 20), 10)

    def test_time_reversal_flips_the_lag_sign(self):
        a = tone(100.0, 2000)
        b = [math.cos(TWO_PI * 100.0 * (i - 6.0) / SAMPLE_RATE)
             for i in range(2000)]
        fwd = est.stereo_lag(a, b, 60)
        rev = est.stereo_lag(a[::-1], b[::-1], 60)
        self.assertAlmostEqual(fwd, -rev, delta=0.05)
        self.assertGreater(abs(fwd), 5.0)


class TestPulseAudio(unittest.TestCase):
    def test_onsets_and_decay(self):
        sig = pulse_train(24000, 6400, 2560)
        on = est.onsets(sig, 0.3, 2000)
        self.assertEqual(len(on), 4)
        self.assertEqual([b - a for a, b in zip(on, on[1:])], [6400] * 3)
        tau, n = est.fit_decay_tau(sig, 2560 + 73, 3 * 640, 73)
        self.assertAlmostEqual(tau, 640.0, delta=640 * 0.02)
        self.assertGreater(n, 20)

    def test_decay_fit_on_silence_is_nan(self):
        tau, n = est.fit_decay_tau([0.0] * 1000, 0, 900, 73)
        self.assertTrue(math.isnan(tau))
        self.assertEqual(n, 0)

    def test_onsets_empty_and_quiet(self):
        self.assertEqual(est.onsets([0.0] * 100), [])
        self.assertEqual(est.onsets([0.2] * 100, 0.3), [])


if __name__ == "__main__":
    unittest.main()
