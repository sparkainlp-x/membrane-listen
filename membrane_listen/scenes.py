"""The six committed scenes: deterministic WAV bytes plus the numbers.

Every scene is built from a fixed seed (42) and fixed parameters, so
regeneration is byte-identical (checked by tests and by ``--check``).
"""

import math

from .core import SAMPLE_RATE, TWO_PI, Ring, Sensor, record_ring, wrap
from .pulses import (BRAIN_LEFT_DELAY, BRAIN_RIGHT_DELAY, brain_signals,
                     heart_signal)
from .wavio import wav_bytes

SEED = 42
WARMUP = 200
STEPS = 16000
SENSOR_A = 10.0
SENSOR_B = 26.0

SCENE_FILES = ("wave_forward.wav", "wave_reverse.wav",
               "wave_stereo_forward.wav", "wave_stereo_reverse.wav",
               "heart.wav", "brain_stereo.wav")


def _mono_wave(k):
    ring, _, readings = record_ring(drive_k=k, warmup=WARMUP, steps=STEPS,
                                    position=SENSOR_A, seed=SEED)
    last = readings[-1]
    signal = [r["signal"] for r in readings]
    data, n = wav_bytes([signal], SAMPLE_RATE, clip="error")
    info = {"k": k, "k_est": last["k_est"], "omega": last["omega"],
            "coherence": last["coherence"], "wave_order": ring.wave_order(),
            "frames": n, "seconds": n / SAMPLE_RATE,
            "peak": max(abs(x) for x in signal)}
    return data, info


def _stereo_wave(k):
    ring = Ring(drive_k=k, seed=SEED)
    for _ in range(WARMUP):
        ring.step()
    sa = Sensor(ring, position=SENSOR_A)
    sb = Sensor(ring, position=SENSOR_B)
    left, right, gaps = [], [], []
    for _ in range(STEPS):
        ring.step()
        ra, rb = sa.sample(), sb.sample()
        left.append(ra["signal"])
        right.append(rb["signal"])
        gaps.append(wrap(rb["phase"] - ra["phase"]))
    data, n = wav_bytes([left, right], SAMPLE_RATE, clip="error")
    mean_gap = math.atan2(math.fsum(math.sin(g) for g in gaps),
                          math.fsum(math.cos(g) for g in gaps))
    info = {"k": k, "sensors": (SENSOR_A, SENSOR_B), "frames": n,
            "gap_last": gaps[-1], "gap_mean": mean_gap,
            "gap_expected": TWO_PI * k * (SENSOR_B - SENSOR_A) / ring.n,
            "peak": max(max(abs(x) for x in left),
                        max(abs(x) for x in right))}
    return data, info


def build_scenes():
    """{filename: (wav bytes, info dict)} for all six scenes."""
    scenes = {}
    scenes["wave_forward.wav"] = _mono_wave(1)
    scenes["wave_reverse.wav"] = _mono_wave(-1)
    scenes["wave_stereo_forward.wav"] = _stereo_wave(1)
    scenes["wave_stereo_reverse.wav"] = _stereo_wave(-1)
    heart = heart_signal()
    data, n = wav_bytes([heart], SAMPLE_RATE, clip="error")
    scenes["heart.wav"] = (data, {
        "frames": n, "seconds": n / SAMPLE_RATE,
        "thumps": len(range(2560, n, 6400)),
        "period_s": 0.80, "delay_s": 0.32, "peak": max(map(abs, heart))})
    left, right = brain_signals()
    data, n = wav_bytes([left, right], SAMPLE_RATE, clip="error")
    scenes["brain_stereo.wav"] = (data, {
        "frames": n, "seconds": n / SAMPLE_RATE,
        "left_delay_s": BRAIN_LEFT_DELAY / SAMPLE_RATE,
        "right_delay_s": BRAIN_RIGHT_DELAY / SAMPLE_RATE,
        "spread_s": (BRAIN_RIGHT_DELAY - BRAIN_LEFT_DELAY) / SAMPLE_RATE,
        "peak": max(max(map(abs, left)), max(map(abs, right)))})
    assert tuple(scenes) == SCENE_FILES
    return scenes
