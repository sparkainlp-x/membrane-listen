"""Shared constants and helpers for the studies."""

import math

from membrane_listen import Ring, Sensor

SEED_SETS = {
    "dev": list(range(1000, 1200)),
    "confirm": list(range(5000, 5200)),
    "smoke": list(range(9001, 9006)),
}

WARMUP = 400
RECORD = 2048
SENSOR_POS = 10.0

OMEGAS = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 48.0)
RING_SIZES = (16, 32, 128)
PITCH_SIGMAS = (0.5, 1.0, 2.0)
DIR_SIGMAS = (0.0, 0.1, 0.25, 0.5, 1.0, 2.0)
LOCK_AMPS = (0.5, 1.0, 1.25)
SEPARATIONS = (1, 2, 4, 8, 16, 24, 31, 32)
GAP_SIGMAS = (0.0, 0.5)
COH_SIGMAS = (0.0, 0.25, 0.5, 1.0, 2.0, 4.0)
SPEEDS = (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0)
FAST_SPEED = 20.0
SHUFFLES = 40


def tok(x):
    """Stable short token for a number in result keys (0.5 -> '0.5')."""
    return f"{x:g}"


def record(ring, sensors, steps=RECORD, warmup=WARMUP):
    """Warm the ring up, then collect one reading per step per sensor."""
    for _ in range(warmup):
        ring.step()
    out = [[] for _ in sensors]
    for _ in range(steps):
        ring.step()
        for bucket, sensor in zip(out, sensors):
            bucket.append(sensor.sample())
    return out


def sign_ok(value, k):
    """True when value has the same strict sign as k."""
    return value * k > 0


def mean(values):
    values = list(values)
    return math.fsum(values) / len(values)


def finite_or(value, fallback):
    return value if math.isfinite(value) else fallback
