"""Tests for membrane-listen. Run: python -m unittest"""

import math
import os
import tempfile
import unittest

from membrane_listen import (Ring, Sensor, brain_signals, heart_signal,
                             pulse_train, read_wav, record_ring,
                             write_wav_mono, write_wav_stereo)


def _first_above(samples, threshold=0.3):
    for i, s in enumerate(samples):
        if abs(s) > threshold:
            return i
    return None


class TestListen(unittest.TestCase):
    def _tmp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        return d.name

    def test_sensor_read_only(self):
        ring = Ring(drive_k=1)
        for _ in range(200):
            ring.step()
        before = list(ring.theta)
        Sensor(ring, position=10.0).sample()
        self.assertEqual(ring.theta, before)

    def test_forward_reverse_gradient_sign(self):
        _, _, fwd = record_ring(drive_k=1, steps=200)
        _, _, rev = record_ring(drive_k=-1, steps=200)
        self.assertAlmostEqual(fwd[-1]["k_est"], 1.0, places=1)
        self.assertAlmostEqual(rev[-1]["k_est"], -1.0, places=1)
        # Same pitch in both directions: omega is -drive_omega.
        self.assertAlmostEqual(fwd[-1]["omega"], -1.0, places=1)
        self.assertAlmostEqual(rev[-1]["omega"], -1.0, places=1)
        self.assertGreater(fwd[-1]["coherence"], 0.9)

    def test_wave_wav_round_trip(self):
        _, _, readings = record_ring(drive_k=1, steps=8000)
        path = os.path.join(self._tmp(), "listen_test.wav")
        n = write_wav_mono(path, [r["signal"] for r in readings])
        ch, rate, frames = read_wav(path)
        self.assertEqual((ch, rate, frames), (1, 8000, 8000))
        self.assertEqual(n, 8000)
        self.assertGreater(max(abs(r["signal"]) for r in readings), 0.5)

    def test_heart_period_and_delay(self):
        sig = heart_signal()
        # First thump starts at the sensor delay, 2560 samples.
        self.assertIsNotNone(_first_above(sig, 0.3))
        first = _first_above(sig, 0.3)
        self.assertTrue(2560 <= first <= 2560 + 200)
        # Five thumps: each arrival window is loud, each gap is quiet
        # (thump decays with tau=640, period is 6400).
        for k in range(5):
            arrival = 2560 + k * 6400
            self.assertGreater(max(abs(s) for s in sig[arrival:arrival + 1000]), 0.5)
        for k in range(4):  # gap before the next thump, not past the end
            arrival = 2560 + k * 6400
            self.assertLess(max(abs(s) for s in sig[arrival + 5000:arrival + 6400]), 0.05)

    def test_brain_spread_delay(self):
        left, right = brain_signals()
        fl, fr = _first_above(left, 0.3), _first_above(right, 0.3)
        self.assertIsNotNone(fl)
        self.assertIsNotNone(fr)
        # Right hears it 3440 samples (0.43 s) after left.
        self.assertAlmostEqual(fr - fl, 3440, delta=200)
        path = os.path.join(self._tmp(), "listen_brain_test.wav")
        n = write_wav_stereo(path, left, right)
        ch, rate, frames = read_wav(path)
        self.assertEqual((ch, rate, frames), (2, 8000, n))

    def test_pulse_train_is_deterministic(self):
        a = pulse_train(8000, 6400, 2560)
        b = pulse_train(8000, 6400, 2560)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main(verbosity=2)
