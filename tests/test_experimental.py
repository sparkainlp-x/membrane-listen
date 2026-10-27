import math
import unittest

from membrane_listen import wrap
from membrane_listen.experimental import Torus


def settle(t, steps=500):
    for _ in range(steps):
        t.step()


class TestTorus(unittest.TestCase):
    def test_locks_to_the_plane_wave(self):
        for kx, ky in ((1, 0), (0, 1), (1, 1), (-1, 1)):
            t = Torus(kx=kx, ky=ky)
            settle(t)
            self.assertGreater(t.wave_order(), 0.99, (kx, ky))

    def test_gaps_follow_the_wave_vector(self):
        t = Torus(size=12, kx=1, ky=-1)
        settle(t)
        gx = wrap(t.phase_at(4, 0) - t.phase_at(0, 0))
        gy = wrap(t.phase_at(0, 4) - t.phase_at(0, 0))
        self.assertAlmostEqual(gx, 2 * math.pi * 4 / 12, places=2)
        self.assertAlmostEqual(gy, -2 * math.pi * 4 / 12, places=2)

    def test_an_x_pair_does_not_see_ky(self):
        gaps = []
        for ky in (1, -1):
            t = Torus(kx=1, ky=ky, seed=11)
            settle(t)
            gaps.append(wrap(t.phase_at(3, 5) - t.phase_at(0, 5)))
        self.assertAlmostEqual(gaps[0], gaps[1], places=2)

    def test_deterministic_and_validated(self):
        a, b = Torus(seed=2, noise=0.3), Torus(seed=2, noise=0.3)
        settle(a, 20)
        settle(b, 20)
        self.assertEqual(a.theta, b.theta)
        for kw in ({"size": 2}, {"dt": 0.0}, {"noise": -1.0},
                   {"coupling": float("nan")}):
            with self.assertRaises(ValueError):
                Torus(**kw)

    def test_phase_at_does_not_modify_state(self):
        t = Torus()
        settle(t, 10)
        snap = [row[:] for row in t.theta]
        for x in range(-3, 15):
            t.phase_at(x, x)
        self.assertEqual(t.theta, snap)


if __name__ == "__main__":
    unittest.main()
