import math
import unittest

from membrane_listen import Ring, Sensor, record_ring, wrap
from membrane_listen import estimators as est


def settle(ring, steps=400):
    for _ in range(steps):
        ring.step()


class TestNoiseAndDetuning(unittest.TestCase):
    def test_zero_noise_matches_the_supplied_model_exactly(self):
        a, b = Ring(seed=5), Ring(seed=5, noise=0.0, detune_sd=0.0)
        for _ in range(500):
            a.step()
            b.step()
        self.assertEqual(a.theta, b.theta)

    def test_initial_phases_do_not_depend_on_noise_settings(self):
        self.assertEqual(Ring(seed=9).theta,
                         Ring(seed=9, noise=1.0, detune_sd=0.5).theta)

    def test_noise_is_deterministic_per_seed_and_differs_across_seeds(self):
        a, b, c = (Ring(seed=s, noise=0.5) for s in (4, 4, 5))
        for _ in range(100):
            a.step()
            b.step()
            c.step()
        self.assertEqual(a.theta, b.theta)
        self.assertNotEqual(a.theta, c.theta)

    def test_noise_lowers_the_wave_order(self):
        orders = []
        for noise in (0.0, 1.0, 4.0):
            r = Ring(seed=3, noise=noise)
            settle(r, 600)
            orders.append(r.wave_order())
        self.assertGreater(orders[0], orders[1])
        self.assertGreater(orders[1], orders[2])

    def test_noise_scales_with_sqrt_dt(self):
        # one step of a free (no drive, no coupling) oscillator: the
        # variance of the increment is noise^2 * dt
        incs = []
        for seed in range(400):
            r = Ring(seed=seed, coupling=0.0, drive_amp=0.0, noise=1.0, dt=0.04)
            before = list(r.theta)
            r.step()
            incs += [wrap(x - y) for x, y in zip(r.theta, before)]
        var = sum(x * x for x in incs) / len(incs)
        self.assertAlmostEqual(var, 0.04, delta=0.003)

    def test_detuning_is_static_and_zero_mean_scale(self):
        r = Ring(seed=2, detune_sd=0.3)
        d = list(r.detune)
        settle(r, 50)
        self.assertEqual(r.detune, d)
        sd = math.sqrt(sum(x * x for x in d) / len(d))
        self.assertGreater(sd, 0.15)
        self.assertLess(sd, 0.45)
        self.assertEqual(Ring(seed=2).detune, [0.0] * 64)

    def test_invalid_noise(self):
        for kw in ({"noise": -0.1}, {"detune_sd": -1.0},
                   {"noise": float("nan")}):
            with self.assertRaises(ValueError):
                Ring(**kw)


class TestFollowProbe(unittest.TestCase):
    def test_doppler_like_shift_matches_the_derivation(self):
        # expected: omega_obs = -drive_omega + 2 pi k v / n
        for k in (1, -1):
            for v in (-2.0, -0.5, 0.0, 0.5, 2.0):
                ring = Ring(drive_k=k)
                settle(ring, 400)
                s = Sensor(ring, position=10.0)
                s.follow_probe(v)
                phases = []
                for _ in range(600):
                    ring.step()
                    phases.append(s.sample()["phase"])
                got = est.phase_velocity(phases)
                want = -1.0 + 2 * math.pi * k * v / 64
                self.assertAlmostEqual(got, want, delta=0.01, msg=(k, v))

    def test_moving_sensor_wraps_around_the_ring(self):
        ring = Ring()
        s = Sensor(ring, position=60.0)
        s.follow_probe(10.0)
        s.sample()
        for _ in range(100):
            ring.step()
            r = s.sample()
            self.assertTrue(0.0 <= r["position"] < 64.0)

    def test_moving_sensor_is_still_read_only(self):
        a, b = Ring(seed=6), Ring(seed=6)
        s = Sensor(b, position=3.0)
        s.follow_probe(3.0)
        for _ in range(400):
            a.step()
            b.step()
            s.sample()
        self.assertEqual(a.theta, b.theta)

    def test_speed_must_be_finite_and_stationary_default(self):
        s = Sensor(Ring())
        self.assertEqual(s.speed, 0.0)
        with self.assertRaises(ValueError):
            s.follow_probe(float("inf"))

    def test_position_reported_in_every_reading(self):
        _, _, rd = record_ring(1, steps=3)
        self.assertEqual([r["position"] for r in rd], [10.0] * 3)


if __name__ == "__main__":
    unittest.main()
