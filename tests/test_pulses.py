import math
import unittest

from membrane_listen import (SAMPLE_RATE, brain_signals, heart_signal,
                             hop_delay_samples, pulse_train)
from membrane_listen.pulses import BRAIN_LEFT_DELAY, BRAIN_RIGHT_DELAY


class TestPulses(unittest.TestCase):
    def test_sample_counts(self):
        self.assertEqual(len(heart_signal()), 32000)
        left, right = brain_signals()
        self.assertEqual((len(left), len(right)), (38400, 38400))
        self.assertEqual(pulse_train(0, 5, 0), [])

    def test_silent_before_first_arrival(self):
        sig = pulse_train(1000, 400, 300)
        self.assertEqual(sig[:300], [0.0] * 300)
        self.assertEqual(sig[300], 0.0)  # sine starts at zero
        self.assertNotEqual(sig[301], 0.0)

    def test_delay_beyond_duration_is_silence(self):
        self.assertEqual(pulse_train(100, 50, 500), [0.0] * 100)

    def test_invalid_arguments_raise_instead_of_hanging_or_wrapping(self):
        for kwargs in ({"period": 0}, {"period": -5}, {"delay": -10},
                       {"tau": 0}, {"tau": -1}, {"tau": float("nan")},
                       {"duration": -1}, {"freq_hz": -1.0},
                       {"period": 2.5}, {"sample_rate": 0}):
            args = {"duration": 100, "period": 50, "delay": 10}
            args.update(kwargs)
            with self.assertRaises(ValueError, msg=str(kwargs)):
                pulse_train(**args)

    def test_negative_delay_does_not_write_to_the_end_of_the_buffer(self):
        with self.assertRaises(ValueError):
            pulse_train(100, 50, -10)

    def test_peak_amplitude_below_one_and_no_clipping(self):
        for sig in (heart_signal(),) + brain_signals():
            self.assertLess(max(abs(s) for s in sig), 1.0)

    def test_thumps_do_not_overlap_in_the_shipped_scenes(self):
        # 6 * tau = 3840 samples < period 6400 and < 9600.
        sig = heart_signal()
        for k in range(4):
            a = 2560 + k * 6400
            self.assertLess(abs(sig[a + 3840 + 100]), 1e-12)

    def test_five_heart_arrivals_and_four_per_brain_channel(self):
        arrivals = [a for a in range(2560, 32000, 6400)]
        self.assertEqual(len(arrivals), 5)
        for delay in (BRAIN_LEFT_DELAY, BRAIN_RIGHT_DELAY):
            self.assertEqual(len(range(delay, 38400, 9600)), 4)

    def test_brain_gap_is_0_43_seconds_but_label_arithmetic_gives_0_44(self):
        gap = BRAIN_RIGHT_DELAY - BRAIN_LEFT_DELAY
        self.assertEqual(gap, 3440)
        self.assertAlmostEqual(gap / SAMPLE_RATE, 0.43, places=9)
        self.assertEqual(BRAIN_LEFT_DELAY, hop_delay_samples(16))
        label_right = hop_delay_samples(32, 0.12) + hop_delay_samples(16)
        self.assertEqual(label_right, 4800)
        self.assertEqual(label_right - BRAIN_RIGHT_DELAY, 80)  # 0.01 s

    def test_frequency_and_decay_parameters(self):
        sig = pulse_train(4000, 4000, 0, tau=640, freq_hz=55.0)
        # first quarter cycle peak near age = SAMPLE_RATE / (4 * 55)
        quarter = int(round(SAMPLE_RATE / (4 * 55.0)))
        self.assertAlmostEqual(sig[quarter],
                               math.exp(-quarter / 640.0), delta=0.01)


if __name__ == "__main__":
    unittest.main()
