"""Pulse-arrival models sonified as decaying thumps (toy labels).

Nothing here is simulated physics: a pulse chain is reduced to one
arrival delay per sensor, and each arrival is sonified as a decaying
sine ("thump"). The labels heart and brain are toy labels, not anatomy
and not electrophysiology.
"""

import math

from .core import SAMPLE_RATE, TWO_PI

HOP_SECONDS = 0.01  # time for the pulse to move one node, as labelled


def _nonneg_int(name, value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("%s must be a non-negative integer" % name)


def pulse_train(duration, period, delay, tau=640, freq_hz=55.0,
                sample_rate=SAMPLE_RATE):
    """Decaying thump train: pacemaker fires every `period` samples,
    the pulse reaches the sensor `delay` samples after each firing.
    All units are audio samples unless named otherwise.

    The supplied version looped forever for period <= 0, silently wrote
    to the END of the buffer for a negative delay (negative list
    indices), and returned silence for tau <= 0; those inputs now raise
    ValueError.
    """
    _nonneg_int("duration", duration)
    _nonneg_int("delay", delay)
    if isinstance(period, bool) or not isinstance(period, int) or period < 1:
        raise ValueError("period must be a positive integer")
    if not (math.isfinite(tau) and tau > 0):
        raise ValueError("tau must be positive and finite")
    if not (math.isfinite(freq_hz) and freq_hz >= 0):
        raise ValueError("freq_hz must be non-negative and finite")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    span = int(math.ceil(6 * tau))
    out = [0.0] * duration
    arrival = delay
    while arrival < duration:
        for s in range(arrival, min(duration, arrival + span)):
            age = s - arrival
            out[s] += math.exp(-age / tau) * math.sin(
                TWO_PI * freq_hz * age / sample_rate)
        arrival += period
    return out


def hop_delay_samples(hops, extra_seconds=0.0, sample_rate=SAMPLE_RATE):
    """Arrival delay in samples for ``hops`` nodes plus a fixed extra."""
    return int(round((hops * HOP_SECONDS + extra_seconds) * sample_rate))


def heart_signal(duration=32000, period=6400, delay=2560):
    """Pacemaker every 0.80 s, sensor hears it 0.32 s later."""
    return pulse_train(duration, period, delay)


# The supplied right-sensor delay. The label arithmetic (32 nodes to the
# end of the left chain, 0.12 s cross delay, 16 nodes into the right
# chain) gives 0.32 + 0.12 + 0.16 = 0.60 s = 4800 samples; the supplied
# constant is 4720 samples = 0.59 s. It is kept so that the shipped WAV
# stays byte-identical; the 0.01 s difference is documented, not hidden.
BRAIN_LEFT_DELAY = 1280
BRAIN_RIGHT_DELAY = 4720


def brain_signals(duration=38400, period=9600):
    """Left sensor delay 0.16 s, right sensor delay 0.59 s.
    Returns (left, right); the 0.43 s gap is the spread delay."""
    left = pulse_train(duration, period, delay=BRAIN_LEFT_DELAY)
    right = pulse_train(duration, period, delay=BRAIN_RIGHT_DELAY)
    return left, right
