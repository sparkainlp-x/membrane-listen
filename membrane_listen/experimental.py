"""EXPERIMENTAL: a 2D membrane for the second open question in DESIGN.md.

Labelled experiment, not part of the six scenes. A square torus of
L x L phase oscillators with a plane-wave drive of wave vector
(kx, ky); same SYNTHETIC classical model as the ring, one more axis.
"""

import math
import random

from .core import TWO_PI, wrap
from .stats import derive_seed


class Torus:
    """Kuramoto torus with a travelling plane-wave drive.

        d theta = dt * ( coupling * mean_{4 nbrs} sin(theta_j - theta)
                         + drive_amp * sin(phi - theta) )
                  + noise * sqrt(dt) * N(0, 1)
        phi(x, y, t) = 2 pi (kx x + ky y) / L - drive_omega * t
    """

    def __init__(self, size=12, coupling=2.0, drive_amp=1.5, kx=1, ky=0,
                 drive_omega=1.0, dt=0.05, seed=42, noise=0.0):
        if isinstance(size, bool) or not isinstance(size, int) or size < 3:
            raise ValueError("size must be an integer >= 3")
        for name, value in (("coupling", coupling), ("drive_amp", drive_amp),
                            ("drive_omega", drive_omega), ("dt", dt),
                            ("noise", noise)):
            if not math.isfinite(value):
                raise ValueError("%s must be finite" % name)
        if dt <= 0 or noise < 0:
            raise ValueError("dt must be positive and noise non-negative")
        self.size = size
        self.coupling = coupling
        self.drive_amp = drive_amp
        self.kx, self.ky = kx, ky
        self.drive_omega = drive_omega
        self.dt = dt
        self.noise = noise
        self.t = 0.0
        rng = random.Random(seed)
        self.theta = [[rng.uniform(-math.pi, math.pi) for _ in range(size)]
                      for _ in range(size)]
        self._noise_rng = random.Random(derive_seed("torus-noise", seed))

    def drive_phase(self, x, y):
        return (TWO_PI * (self.kx * x + self.ky * y) / self.size
                - self.drive_omega * self.t)

    def wave_order(self):
        d = [self.theta[y][x] - self.drive_phase(x, y)
             for y in range(self.size) for x in range(self.size)]
        re = math.fsum(math.cos(v) for v in d) / len(d)
        im = math.fsum(math.sin(v) for v in d) / len(d)
        return math.hypot(re, im)

    def step(self):
        n, dt, th = self.size, self.dt, self.theta
        new = []
        for y in range(n):
            row = []
            for x in range(n):
                c = th[y][x]
                coupling_term = (math.sin(th[y][(x - 1) % n] - c)
                                 + math.sin(th[y][(x + 1) % n] - c)
                                 + math.sin(th[(y - 1) % n][x] - c)
                                 + math.sin(th[(y + 1) % n][x] - c)) / 4.0
                drive_term = self.drive_amp * math.sin(self.drive_phase(x, y) - c)
                v = c + dt * (self.coupling * coupling_term + drive_term)
                if self.noise:
                    v += self.noise * math.sqrt(dt) * self._noise_rng.gauss(0.0, 1.0)
                row.append(wrap(v))
            new.append(row)
        self.theta = new
        self.t += dt

    def phase_at(self, x, y):
        """Read-only phase of one node."""
        return self.theta[y % self.size][x % self.size]
