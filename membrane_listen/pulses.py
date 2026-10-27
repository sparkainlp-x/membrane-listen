"""Pulse-arrival models sonified as decaying thumps (toy labels)."""

import math

from .core import SAMPLE_RATE, TWO_PI

def pulse_train(duration, period, delay, tau=640, freq_hz=55.0,
                sample_rate=SAMPLE_RATE):
    """Decaying thump train: pacemaker fires every `period` samples,
    the pulse reaches the sensor `delay` samples after each firing.
    All units are audio samples unless named otherwise."""
    out = [0.0] * duration
    arrival = delay
    while arrival < duration:
        for s in range(arrival, min(duration, arrival + 6 * tau)):
            age = s - arrival
            out[s] += math.exp(-age / tau) * math.sin(
                TWO_PI * freq_hz * age / sample_rate)
        arrival += period
    return out


def heart_signal(duration=32000, period=6400, delay=2560):
    """Pacemaker every 0.80 s, sensor hears it 0.32 s later."""
    return pulse_train(duration, period, delay)


def brain_signals(duration=38400, period=9600):
    """Left sensor delay 0.16 s, right sensor delay 0.59 s.
    Returns (left, right); the 0.43 s gap is the spread delay."""
    left = pulse_train(duration, period, delay=1280)
    right = pulse_train(duration, period, delay=4720)
    return left, right


