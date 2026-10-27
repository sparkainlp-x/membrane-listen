"""Ring, sensor and recording helpers (split from the supplied module).

Sections of the supplied module docstring are kept in README.md and
DESIGN.md.
"""

import cmath
import math
import random

TWO_PI = 2.0 * math.pi
SAMPLE_RATE = 8000


def wrap(angle):
    """Wrap an angle into (-pi, pi].

    The supplied version subtracted 2*pi in a loop, which never ends
    for an infinite angle and is slow for a huge one; this version uses
    the exact IEEE remainder and raises ValueError for non-finite input.
    For |angle| of order pi it returns the same floats as before.
    """
    if not math.isfinite(angle):
        raise ValueError("cannot wrap a non-finite angle")
    r = math.remainder(angle, TWO_PI)
    if r <= -math.pi:
        r += TWO_PI
    return r


# ---------------------------------------------------------------- ring
class Ring:
    """Kuramoto ring with a travelling drive (propulsion dynamics)."""

    def __init__(self, n=64, coupling=2.0, drive_amp=1.5, drive_k=1,
                 drive_omega=1.0, dt=0.05, seed=42):
        if isinstance(n, bool) or not isinstance(n, int) or n < 3:
            raise ValueError("n must be an integer >= 3 (with n < 3 the two "
                             "neighbours of a node coincide)")
        for name, value in (("coupling", coupling), ("drive_amp", drive_amp),
                            ("drive_omega", drive_omega), ("dt", dt)):
            if not math.isfinite(value):
                raise ValueError("%s must be finite" % name)
        if dt <= 0:
            raise ValueError("dt must be positive")
        self.n = n
        self.coupling = coupling
        self.drive_amp = drive_amp
        self.drive_k = drive_k
        self.drive_omega = drive_omega
        self.dt = dt
        self.t = 0.0
        rng = random.Random(seed)
        self.theta = [rng.uniform(-math.pi, math.pi) for _ in range(n)]

    def _drive_phase(self, i):
        return self.drive_k * TWO_PI * i / self.n - self.drive_omega * self.t

    def wave_order(self):
        """Length of the mean of exp(i * (theta - drive phase)).

        Sums are exactly rounded (math.fsum): the built-in sum() changed
        its float rounding in Python 3.12, so plain sums are not
        identical across Python versions.
        """
        d = [self.theta[i] - self._drive_phase(i) for i in range(self.n)]
        re = math.fsum(math.cos(x) for x in d) / self.n
        im = math.fsum(math.sin(x) for x in d) / self.n
        return math.hypot(re, im)

    def step(self):
        n, dt = self.n, self.dt
        new = []
        for i in range(n):
            coupling_term = (math.sin(self.theta[(i - 1) % n] - self.theta[i])
                             + math.sin(self.theta[(i + 1) % n] - self.theta[i])) / 2.0
            drive_term = self.drive_amp * math.sin(self._drive_phase(i) - self.theta[i])
            new.append(self.theta[i] + dt * (self.coupling * coupling_term + drive_term))
        self.theta = [wrap(th) for th in new]
        self.t += dt


# ---------------------------------------------------------------- sensor
class Sensor:
    """Passive, read-only vibration sensor (propulsion v0.2.0 logic)."""

    def __init__(self, ring, position=0.0, window=2):
        if not math.isfinite(position):
            raise ValueError("position must be finite")
        if (isinstance(window, bool) or not isinstance(window, int)
                or window < 0 or 2 * window + 1 > ring.n):
            raise ValueError("window must be an integer with 0 <= window and "
                             "2 * window + 1 <= n (nodes are not counted "
                             "twice)")
        self.ring = ring
        self.position = position % ring.n
        self.window = window
        self._prev_phase = None
        self._prev_t = None

    def sample(self):
        n = self.ring.n
        i = int(self.position) % n
        j = (i + 1) % n
        f = self.position - int(self.position)
        z = (1.0 - f) * cmath.exp(1j * self.ring.theta[i]) \
            + f * cmath.exp(1j * self.ring.theta[j])
        phase = cmath.phase(z)
        gradient = wrap(self.ring.theta[j] - self.ring.theta[i])
        local = [self.ring.theta[(i + d) % n]
                 for d in range(-self.window, self.window + 1)]
        coherence = math.hypot(math.fsum(math.cos(x) for x in local),
                               math.fsum(math.sin(x) for x in local)) \
            / (2 * self.window + 1)
        if self._prev_phase is None:
            omega = 0.0
        else:
            dt = self.ring.t - self._prev_t
            omega = wrap(phase - self._prev_phase) / dt if dt else 0.0
        reading = {"t": self.ring.t, "phase": phase, "omega": omega,
                   "gradient": gradient, "k_est": gradient * n / TWO_PI,
                   "coherence": coherence,
                   "signal": math.cos(phase) * coherence}
        self._prev_phase = phase
        self._prev_t = self.ring.t
        return reading


def record_ring(drive_k, warmup=200, steps=16000, position=10.0, seed=42):
    """Warm up, then record sensor readings, one per step."""
    ring = Ring(drive_k=drive_k, seed=seed)
    for _ in range(warmup):
        ring.step()
    sensor = Sensor(ring, position=position)
    readings = []
    for _ in range(steps):
        ring.step()
        readings.append(sensor.sample())
    return ring, sensor, readings


