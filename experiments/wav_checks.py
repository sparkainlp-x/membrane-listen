"""Study E: deterministic checks on the committed WAV files.

    python -m experiments.wav_checks --out docs/results/wav_checks.json

No seeds. Each check compares a number measured from the WAV audio with
the number the scene's own labels or derivation give, and records pass
or fail against a stated tolerance. These check that the implementation
does what its labels say; they say nothing about hearing or perception.
"""

import argparse
import json
import math
import os
import sys

from membrane_listen import SAMPLE_RATE, TWO_PI, wrap
from membrane_listen import estimators as est
from membrane_listen.wavio import read_wav_samples

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WAV = os.path.join(ROOT, "wav")
TAU = 640.0
THUMP_HZ = 55.0


def load(name):
    rate, chans = read_wav_samples(os.path.join(WAV, name))
    assert rate == SAMPLE_RATE
    return chans


def check(name, measured, expected, tol, unit):
    return {"name": name, "measured": round(measured, 6),
            "expected": round(expected, 6), "tolerance": tol, "unit": unit,
            "pass": bool(abs(measured - expected) <= tol)}


def mono_waves():
    out = []
    want = est.omega_to_hz(1.0)
    peaks = {}
    for name in ("wave_forward.wav", "wave_reverse.wav"):
        (x,) = load(name)
        peaks[name] = est.peak_frequency_hz(x)
        out.append(check(f"{name} fft peak", peaks[name], want, 0.1, "Hz"))
        out.append(check(f"{name} zero-crossing rate",
                         est.zero_crossing_hz(x), want, 0.1, "Hz"))
    out.append(check("forward minus reverse peak (pitch carries no direction)",
                     peaks["wave_forward.wav"] - peaks["wave_reverse.wav"],
                     0.0, 0.1, "Hz"))
    return out


def stereo_waves():
    out = []
    lag_expected = (TWO_PI / 4) / (1.0 * 0.05)
    for name, k in (("wave_stereo_forward.wav", 1),
                    ("wave_stereo_reverse.wav", -1)):
        left, right = load(name)
        lag = est.stereo_lag(left, right, 39)
        lag_rev = est.stereo_lag(left[::-1], right[::-1], 39)
        out.append(check(f"{name} audio lag", lag, k * lag_expected, 1.0,
                         "samples"))
        out.append(check(f"{name} time-reversed audio lag", lag_rev,
                         -k * lag_expected, 1.0, "samples"))
    return out


def heart():
    (x,) = load("heart.wav")
    on = est.onsets(x, 0.3, 2000)
    out = [check("heart thump count", len(on), 5, 0, "thumps")]
    ioi = [b - a for a, b in zip(on, on[1:])]
    out.append(check("heart inter-onset interval (mean)",
                     math.fsum(ioi) / len(ioi), 6400.0, 1.0, "samples"))
    out.append(check("heart first onset minus nominal arrival (2560)",
                     on[0] - 2560, 0.0, 30.0, "samples"))
    tau, n = est.fit_decay_tau(x, 2560 + 73, int(3 * TAU), 73)
    out.append(check("heart thump decay constant", tau, TAU, TAU * 0.03,
                     "samples"))
    seg = x[2560:2560 + 2560]
    out.append(check("heart thump fundamental (fft of first thump)",
                     est.peak_frequency_hz(seg), THUMP_HZ, 2.0, "Hz"))
    out.append(check("heart pacemaker period", math.fsum(ioi) / len(ioi)
                     / SAMPLE_RATE, 0.80, 0.001, "s"))
    return out


def brain():
    left, right = load("brain_stereo.wav")
    ol = est.onsets(left, 0.3, 2000)
    orr = est.onsets(right, 0.3, 2000)
    out = [check("brain left thump count", len(ol), 4, 0, "thumps"),
           check("brain right thump count", len(orr), 4, 0, "thumps")]
    out.append(check("brain left-to-right spread (first onsets)",
                     orr[0] - ol[0], 3440.0, 30.0, "samples"))
    out.append(check("brain left-to-right spread", (orr[0] - ol[0]) /
                     SAMPLE_RATE, 0.43, 0.005, "s"))
    out.append(check("brain left period", (ol[-1] - ol[0]) / (len(ol) - 1),
                     9600.0, 1.0, "samples"))
    return out


def aliasing_table():
    """Pure tones through the FFT estimator: fold at Nyquist."""
    rows = []
    for hz in (100.0, 1000.0, 3900.0, 4100.0, 5000.0, 7900.0, 8100.0):
        x = [math.cos(TWO_PI * hz * i / SAMPLE_RATE) for i in range(2048)]
        folded = abs(((hz + SAMPLE_RATE / 2) % SAMPLE_RATE) - SAMPLE_RATE / 2)
        rows.append({"true_hz": hz, "expected_hz": folded,
                     "measured_hz": round(est.peak_frequency_hz(x), 3)})
    return rows


def phase_aliasing_table():
    """Phase ramps through the pv estimator: per-sample step beyond pi."""
    rows = []
    for omega in (1.0, 30.0, 60.0, 62.0, 64.0, 70.0, 100.0):
        phases = [wrap(omega * 0.05 * i) for i in range(400)]
        got = est.phase_velocity(phases)
        want = wrap(omega * 0.05) / 0.05
        rows.append({"omega": omega, "per_sample_step": round(omega * 0.05, 4),
                     "expected_omega": round(want, 6),
                     "measured_omega": round(got, 6)})
    return rows


def run():
    sections = {"mono waves": mono_waves(), "stereo waves": stereo_waves(),
                "heart": heart(), "brain": brain()}
    flat = [c for rows in sections.values() for c in rows]
    return {"checks": sections,
            "all_pass": all(c["pass"] for c in flat),
            "n_checks": len(flat),
            "aliasing_tones": aliasing_table(),
            "aliasing_phase": phase_aliasing_table(),
            "synthetic": True}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    result = run()
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"wrote {args.out}: {result['n_checks']} checks, "
          f"all pass: {result['all_pass']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
