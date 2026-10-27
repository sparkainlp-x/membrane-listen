"""Ring, sensor and recording helpers (split from the supplied module).

Sections of the supplied module docstring are kept in README.md and
DESIGN.md.
"""

import cmath
import math
import random

from .stats import derive_seed

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
    """Kuramoto ring with a travelling drive.

    Equation (explicit Euler, synchronous update)::

        d theta_i = dt * ( coupling * mean_j sin(theta_j - theta_i)
                           + drive_amp * sin(phi_i(t) - theta_i)
                           + detune_i )  +  noise * sqrt(dt) * N(0, 1)
        phi_i(t) = drive_k * 2 pi i / n - drive_omega * t

    ``noise`` and ``detune_sd`` are additions for the pre-registered
    studies; both default to 0, which reproduces the supplied model
    exactly (the committed WAVs are byte-identical). Their random draws
    come from their own seeded streams, so the initial phases do not
    depend on them. A locked oscillator needs drive_amp > |drive_omega|
    (the Adler condition) and the Euler step needs roughly
    dt * sqrt(drive_amp**2 - drive_omega**2) < 2.
    """

    def __init__(self, n=64, coupling=2.0, drive_amp=1.5, drive_k=1,
                 drive_omega=1.0, dt=0.05, seed=42, noise=0.0,
                 detune_sd=0.0):
        if isinstance(n, bool) or not isinstance(n, int) or n < 3:
            raise ValueError("n must be an integer >= 3 (with n < 3 the two "
                             "neighbours of a node coincide)")
        for name, value in (("coupling", coupling), ("drive_amp", drive_amp),
                            ("drive_omega", drive_omega), ("dt", dt),
                            ("noise", noise), ("detune_sd", detune_sd)):
            if not math.isfinite(value):
                raise ValueError("%s must be finite" % name)
        if dt <= 0:
            raise ValueError("dt must be positive")
        if noise < 0 or detune_sd < 0:
            raise ValueError("noise and detune_sd must be non-negative")
        self.n = n
        self.noise = noise
        self.detune_sd = detune_sd
        self.coupling = coupling
        self.drive_amp = drive_amp
        self.drive_k = drive_k
        self.drive_omega = drive_omega
        self.dt = dt
        self.t = 0.0
        rng = random.Random(seed)
        self.theta = [rng.uniform(-math.pi, math.pi) for _ in range(n)]
        self._noise_rng = random.Random(derive_seed("ring-noise", seed))
        det_rng = random.Random(derive_seed("ring-detune", seed))
        self.detune = [det_rng.gauss(0.0, detune_sd) if detune_sd else 0.0
                       for _ in range(n)]

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
            rate = self.coupling * coupling_term + drive_term
            if self.detune_sd:
                rate += self.detune[i]
            value = self.theta[i] + dt * rate
            if self.noise:
                value += self.noise * math.sqrt(dt) * self._noise_rng.gauss(0.0, 1.0)
            new.append(value)
        self.theta = [wrap(th) for th in new]
        self.t += dt


# ---------------------------------------------------------------- sensor
class Sensor:
    """Passive, read-only vibration sensor.

    ``omega`` is the phase velocity between this reading and the previous
    one, wrapped into (-pi, pi] per step, so it is only meaningful while
    |omega| * dt < pi. It is NaN for the first reading (no history) and
    whenever no time has passed; the supplied code reported 0.0 there,
    which cannot be told apart from a measured zero.
    """

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
        self.speed = 0.0
        self._prev_phase = None
        self._prev_t = None

    def follow_probe(self, speed):
        """Move the sensor along the ring at ``speed`` nodes per time unit.

        The position advances by speed * elapsed time at each sample()
        after the first. Only the sensor's own position changes; the ring
        is never touched. (The supplied DESIGN.md said the sensor class
        had this method; the supplied code did not.)
        """
        if not math.isfinite(speed):
            raise ValueError("speed must be finite")
        self.speed = float(speed)

    def sample(self):
        if self.speed and self._prev_t is not None:
            self.position = (self.position
                             + self.speed * (self.ring.t - self._prev_t)) \
                % self.ring.n
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
            omega = float("nan")  # no history yet (supplied code said 0.0)
        else:
            dt = self.ring.t - self._prev_t
            omega = (wrap(phase - self._prev_phase) / dt if dt > 0
                     else float("nan"))
        reading = {"t": self.ring.t, "position": self.position, "phase": phase, "omega": omega,
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


