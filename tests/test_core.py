import copy
import math
import unittest

from membrane_listen import TWO_PI, Ring, Sensor, record_ring, wrap


class TestWrap(unittest.TestCase):
    def test_range_is_half_open_minus_pi_to_pi(self):
        for a in (0.0, 1.0, -1.0, math.pi, -math.pi, 3 * math.pi,
                  -3 * math.pi, 7.5, -7.5, 1e6, -1e6):
            w = wrap(a)
            self.assertGreater(w, -math.pi - 1e-15)
            self.assertLessEqual(w, math.pi)
            diff = (a - w) / TWO_PI
            self.assertAlmostEqual(diff, round(diff), places=6 if abs(a) > 1e5 else 9)
        self.assertEqual(wrap(-math.pi), math.pi)
        self.assertEqual(wrap(math.pi), math.pi)

    def test_matches_the_supplied_loop_for_ordinary_angles(self):
        def old(angle):
            while angle > math.pi:
                angle -= TWO_PI
            while angle <= -math.pi:
                angle += TWO_PI
            return angle
        for i in range(-2000, 2001):
            a = i * 0.0037
            self.assertEqual(wrap(a), old(a), a)

    def test_non_finite_raises_instead_of_looping_forever(self):
        for bad in (float("inf"), float("-inf"), float("nan")):
            with self.assertRaises(ValueError):
                wrap(bad)


class TestRingValidation(unittest.TestCase):
    def test_bad_arguments(self):
        for kwargs in ({"n": 2}, {"n": 0}, {"n": 1}, {"n": 8.0},
                       {"n": True}, {"dt": 0.0}, {"dt": -0.05},
                       {"dt": float("nan")}, {"coupling": float("inf")},
                       {"drive_amp": float("nan")},
                       {"drive_omega": float("inf")}):
            with self.assertRaises(ValueError, msg=str(kwargs)):
                Ring(**kwargs)

    def test_smallest_ring_works(self):
        ring = Ring(n=3)
        for _ in range(10):
            ring.step()
        self.assertTrue(all(math.isfinite(x) for x in ring.theta))

    def test_phases_stay_wrapped(self):
        ring = Ring()
        for _ in range(500):
            ring.step()
            self.assertTrue(all(-math.pi < x <= math.pi for x in ring.theta))

    def test_same_seed_same_trajectory(self):
        a, b = Ring(seed=7), Ring(seed=7)
        for _ in range(300):
            a.step()
            b.step()
        self.assertEqual(a.theta, b.theta)
        self.assertNotEqual(a.theta, Ring(seed=8).theta)

    def test_wave_order_is_a_proper_length(self):
        ring = Ring()
        for _ in range(2000):
            ring.step()
            self.assertLessEqual(ring.wave_order(), 1.0 + 1e-15)
        self.assertGreater(ring.wave_order(), 0.999)
        # The supplied plain sum() gave 1.0000000000000002 on Python 3.10;
        # exactly rounded sums make the value the same on every version.
        self.assertEqual(ring.wave_order(), 1.0)

    def test_lock_condition_adler(self):
        # drive strength below the drive frequency: no lock
        ring = Ring(drive_amp=0.5)
        for _ in range(3000):
            ring.step()
        self.assertLess(ring.wave_order(), 0.9)


class TestSensorValidation(unittest.TestCase):
    def test_bad_arguments(self):
        ring = Ring()
        for pos in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaises(ValueError):
                Sensor(ring, position=pos)
        for w in (-1, 32, 1.5, True):
            with self.assertRaises(ValueError, msg=str(w)):
                Sensor(ring, window=w)
        Sensor(ring, window=31)  # 63 nodes, fewer than n = 64

    def test_negative_and_large_positions_wrap(self):
        ring = Ring()
        for _ in range(300):
            ring.step()
        a = Sensor(ring, position=-3.5).sample()
        b = Sensor(ring, position=60.5).sample()
        c = Sensor(ring, position=60.5 + 64 * 3).sample()
        self.assertEqual(a["phase"], b["phase"])
        self.assertAlmostEqual(b["phase"], c["phase"], places=12)

    def test_coherence_is_between_zero_and_one(self):
        ring = Ring()
        for _ in range(50):
            ring.step()
            for pos in (0.0, 10.0, 63.5):
                c = Sensor(ring, position=pos).sample()["coherence"]
                self.assertGreaterEqual(c, 0.0)
                self.assertLessEqual(c, 1.0 + 1e-15)

    def test_window_zero_has_unit_coherence(self):
        ring = Ring()
        s = Sensor(ring, position=5.0, window=0).sample()
        self.assertAlmostEqual(s["coherence"], 1.0, places=12)

    def test_phase_unwrapping_across_the_branch_cut(self):
        ring = Ring()
        sensor = Sensor(ring, position=0.0)
        ring.theta = [3.0] * ring.n
        ring.t = 0.0
        sensor.sample()
        ring.theta = [-3.0] * ring.n  # true step is +0.2832 rad, not -6
        ring.t = 0.05
        r = sensor.sample()
        self.assertAlmostEqual(r["omega"], (TWO_PI - 6.0) / 0.05, places=9)


class TestReadOnlySensor(unittest.TestCase):
    def snapshot(self, ring):
        return (copy.deepcopy(ring.__dict__), ring.theta[:], ring.t)

    def test_sampling_changes_no_ring_state(self):
        ring = Ring(drive_k=1)
        for _ in range(200):
            ring.step()
        before = self.snapshot(ring)
        sensors = [Sensor(ring, position=p) for p in (0.0, 10.0, 26.5, 63.9)]
        for _ in range(50):
            for s in sensors:
                s.sample()
        self.assertEqual(self.snapshot(ring), before)

    def test_attached_sensors_do_not_change_the_trajectory(self):
        a, b = Ring(seed=3), Ring(seed=3)
        sensors = [Sensor(b, position=p) for p in (1.0, 20.25, 40.0)]
        for _ in range(1500):
            a.step()
            b.step()
            for s in sensors:
                s.sample()
        self.assertEqual(a.theta, b.theta)
        self.assertEqual(a.t, b.t)

    def test_the_read_only_test_catches_a_mutating_sensor(self):
        class Bad(Sensor):
            def sample(self):
                r = super().sample()
                self.ring.theta[0] += 1e-9
                return r
        a, b = Ring(seed=3), Ring(seed=3)
        bad = Bad(b, position=1.0)
        for _ in range(100):
            a.step()
            b.step()
            bad.sample()
        self.assertNotEqual(a.theta, b.theta)


class TestRecordRing(unittest.TestCase):
    def test_sample_counts_and_times(self):
        ring, sensor, readings = record_ring(1, warmup=10, steps=25)
        self.assertEqual(len(readings), 25)
        self.assertAlmostEqual(readings[0]["t"], 11 * 0.05, places=12)
        self.assertAlmostEqual(readings[-1]["t"], 35 * 0.05, places=12)

    def test_zero_steps_is_empty(self):
        _, _, readings = record_ring(1, warmup=0, steps=0)
        self.assertEqual(readings, [])


class TestOmegaHistory(unittest.TestCase):
    def test_first_reading_has_no_omega(self):
        ring = Ring()
        s = Sensor(ring, position=3.0)
        self.assertTrue(math.isnan(s.sample()["omega"]))
        ring.step()
        self.assertTrue(math.isfinite(s.sample()["omega"]))

    def test_no_elapsed_time_gives_nan_not_zero(self):
        ring = Ring()
        s = Sensor(ring, position=3.0)
        s.sample()
        self.assertTrue(math.isnan(s.sample()["omega"]))

    def test_locked_omega_is_minus_the_drive_frequency(self):
        for k in (1, -1, 2):
            _, _, rd = record_ring(k, steps=300)
            self.assertAlmostEqual(rd[-1]["omega"], -1.0, places=3)
        _, _, rd = record_ring(1, steps=300)
        self.assertTrue(math.isnan(rd[0]["omega"]))


if __name__ == "__main__":
    unittest.main()
