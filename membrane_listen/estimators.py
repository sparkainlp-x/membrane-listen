"""Estimators applied to sensor readings and to rendered audio.

All standard library. These are measurement tools for the SYNTHETIC
membrane, not claims about any real signal.

Units. The ring advances ``DT`` time units per audio sample, so a phase
velocity of omega radians per time unit is an audio frequency of
``|omega| * DT * SAMPLE_RATE / (2 * pi)`` Hz. With omega = 1, DT = 0.05
and 8000 samples per second that is 63.66 Hz (the supplied "about 64 Hz";
the supplied DESIGN.md left DT out of the arithmetic). The sign of omega
is not audible: cos(phase) is an even function of phase.
"""

import cmath
import math

from .core import SAMPLE_RATE, TWO_PI, wrap

DT = 0.05  # Ring default time step, time units per audio sample


def omega_to_hz(omega, dt=DT, rate=SAMPLE_RATE):
    """Audio frequency (Hz) of cos(phase) for phase velocity omega."""
    return abs(omega) * dt * rate / TWO_PI


def hz_to_omega(hz, dt=DT, rate=SAMPLE_RATE):
    """Phase velocity magnitude (rad per time unit) for an audio frequency."""
    return hz * TWO_PI / (dt * rate)


def nyquist_omega(dt=DT):
    """Largest |omega| whose per-sample phase step is below pi."""
    return math.pi / dt


def circular_mean(angles):
    """(mean angle, resultant length) of angles; (nan, 0.0) if empty."""
    angles = list(angles)
    if not angles:
        return float("nan"), 0.0
    c = math.fsum(math.cos(a) for a in angles)
    s = math.fsum(math.sin(a) for a in angles)
    r = math.hypot(c, s) / len(angles)
    return (math.atan2(s, c) if r > 0 else float("nan")), r


def phase_velocity(phases, dt=DT):
    """Mean phase velocity from successive wrapped phase differences.

    The wrapped differences are summed (exactly rounded) and divided by
    the elapsed time. It is unbiased while |omega| * dt < pi; faster
    phase motion aliases to a smaller (possibly sign-flipped) value.
    NaN for fewer than two phases.
    """
    phases = list(phases)
    if len(phases) < 2:
        return float("nan")
    steps = [wrap(b - a) for a, b in zip(phases, phases[1:])]
    return math.fsum(steps) / (dt * len(steps))


def window_k(gradients, n):
    """Wave number from the circular mean of per-sample gradients."""
    mean, r = circular_mean(gradients)
    return mean * n / TWO_PI, r


def phase_gap(phases_a, phases_b):
    """Circular mean of wrap(b - a) over time: (gap, resultant length)."""
    return circular_mean([wrap(b - a) for a, b in zip(phases_a, phases_b)])


# ----------------------------------------------------------------- FFT
def fft(x):
    """Radix-2 FFT of a sequence of complex numbers (length 2**m)."""
    n = len(x)
    if n == 0 or n & (n - 1):
        raise ValueError("length must be a power of two")
    a = [complex(v) for v in x]
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            a[i], a[j] = a[j], a[i]
    length = 2
    while length <= n:
        w_len = cmath.exp(-2j * math.pi / length)
        half = length // 2
        for start in range(0, n, length):
            w = 1.0 + 0.0j
            for k in range(half):
                u = a[start + k]
                v = a[start + k + half] * w
                a[start + k] = u + v
                a[start + k + half] = u - v
                w *= w_len
        length <<= 1
    return a


def peak_frequency_hz(samples, rate=SAMPLE_RATE, pad_factor=4):
    """Frequency of the largest spectral peak (Hann window, zero padding,
    parabolic interpolation on the log magnitude). NaN for silence."""
    n = len(samples)
    if n < 8:
        raise ValueError("need at least 8 samples")
    m = sum(samples) / n
    win = [0.5 - 0.5 * math.cos(TWO_PI * i / (n - 1)) for i in range(n)]
    x = [(s - m) * w for s, w in zip(samples, win)]
    size = 1
    while size < n * pad_factor:
        size <<= 1
    x += [0.0] * (size - n)
    spec = fft(x)
    mag = [abs(spec[k]) for k in range(size // 2 + 1)]
    mag[0] = 0.0
    k = max(range(len(mag)), key=mag.__getitem__)
    if mag[k] <= 1e-12:
        return float("nan")
    if 0 < k < len(mag) - 1 and mag[k - 1] > 0 and mag[k + 1] > 0:
        a, b, c = (math.log(mag[k - 1]), math.log(mag[k]),
                   math.log(mag[k + 1]))
        denom = a - 2 * b + c
        shift = 0.5 * (a - c) / denom if denom != 0 else 0.0
    else:
        shift = 0.0
    return (k + shift) * rate / size


def zero_crossing_hz(samples, rate=SAMPLE_RATE):
    """Frequency from linearly interpolated rising zero crossings."""
    times = []
    for i in range(1, len(samples)):
        a, b = samples[i - 1], samples[i]
        if a < 0.0 <= b and b > a:
            times.append(i - 1 + (-a) / (b - a))
    if len(times) < 2:
        return float("nan")
    return (len(times) - 1) * rate / (times[-1] - times[0])


def stereo_lag(left, right, max_lag):
    """Lag (samples, fractional) at which right best matches left.

    Positive: right is a delayed copy of left, right[t + lag] ~ left[t].
    Normalised cross-correlation over the overlap, parabolic refinement.
    NaN if either channel is silent. For a periodic signal the lag is
    only defined modulo the period, so ``max_lag`` must stay below half a
    period or the result can land one period away.
    """
    n = len(left)
    if n != len(right) or n <= 2 * max_lag + 2:
        raise ValueError("channels must match and exceed 2 * max_lag + 2")
    ml = sum(left) / n
    mr = sum(right) / n
    a = [v - ml for v in left]
    b = [v - mr for v in right]
    if math.fsum(v * v for v in a) == 0.0 or math.fsum(v * v for v in b) == 0.0:
        return float("nan")
    scores = []
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            xs, ys = a[:n - lag], b[lag:]
        else:
            xs, ys = a[-lag:], b[:n + lag]
        num = math.fsum(p * q for p, q in zip(xs, ys))
        den = math.sqrt(math.fsum(p * p for p in xs)
                        * math.fsum(q * q for q in ys))
        scores.append(num / den if den else 0.0)
    k = max(range(len(scores)), key=scores.__getitem__)
    shift = 0.0
    if 0 < k < len(scores) - 1:
        y0, y1, y2 = scores[k - 1], scores[k], scores[k + 1]
        denom = y0 - 2 * y1 + y2
        shift = 0.5 * (y0 - y2) / denom if denom != 0 else 0.0
    return k - max_lag + shift


# ----------------------------------------------------------- pulse audio
def onsets(samples, threshold=0.3, min_gap=2000):
    """Indices where |sample| first exceeds threshold after >= min_gap
    samples of quiet (or at the start)."""
    out = []
    last = None
    for i, s in enumerate(samples):
        if abs(s) > threshold:
            if last is None or i - last >= min_gap:
                out.append(i)
            last = i
    return out


def fit_decay_tau(samples, start, length, half_cycle):
    """Decay time constant (samples) of a thump from per-half-cycle peaks.

    Takes the largest |sample| in consecutive windows of ``half_cycle``
    samples inside [start, start + length), then fits ln(peak) against
    the peak position by least squares. Returns (tau, n_peaks).
    """
    pts = []
    for lo in range(start, start + length - half_cycle + 1, half_cycle):
        seg = range(lo, lo + half_cycle)
        i = max(seg, key=lambda j: abs(samples[j]))
        if abs(samples[i]) > 1e-9:
            pts.append((i, math.log(abs(samples[i]))))
    if len(pts) < 3:
        return float("nan"), len(pts)
    mx = math.fsum(p[0] for p in pts) / len(pts)
    my = math.fsum(p[1] for p in pts) / len(pts)
    sxx = math.fsum((p[0] - mx) ** 2 for p in pts)
    slope = math.fsum((p[0] - mx) * (p[1] - my) for p in pts) / sxx
    return (-1.0 / slope if slope < 0 else float("inf")), len(pts)
