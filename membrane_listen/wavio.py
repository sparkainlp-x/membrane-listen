"""WAV input and output (standard library wave and struct).

Samples are floats in [-1, 1] and are written as 16-bit PCM, scaled by
32767 and rounded half to even (Python's round). The value -32768 is
never produced, so the range is symmetric.
"""

import io
import math
import struct
import wave

from .core import SAMPLE_RATE

INT16_MAX = 32767


def _check_rate(sample_rate):
    if (isinstance(sample_rate, bool) or not isinstance(sample_rate, int)
            or sample_rate <= 0):
        raise ValueError("sample_rate must be a positive integer")


def _to_int16(samples, clip="clip"):
    """Float samples to symmetric int16.

    ``clip="clip"`` limits out-of-range samples to +-32767 (the
    default, as supplied); ``clip="error"`` raises ValueError instead,
    so a scene can prove it never clipped. Non-finite samples always
    raise ValueError; they are never silently turned into numbers.
    """
    if clip not in ("clip", "error"):
        raise ValueError("clip must be 'clip' or 'error'")
    out = []
    for s in samples:
        if not math.isfinite(s):
            raise ValueError("non-finite sample cannot be written to a WAV file")
        v = int(round(s * INT16_MAX))
        if v > INT16_MAX or v < -INT16_MAX:
            if clip == "error":
                raise ValueError("sample %r is outside [-1, 1]" % (s,))
            v = max(-INT16_MAX, min(INT16_MAX, v))
        out.append(v)
    return out


def wav_bytes(channels, sample_rate=SAMPLE_RATE, clip="clip"):
    """Encode one list of samples per channel as WAV bytes.

    All channels must have the same length (the supplied stereo writer
    silently truncated the longer one).
    """
    _check_rate(sample_rate)
    if not channels:
        raise ValueError("at least one channel is required")
    lengths = {len(c) for c in channels}
    if len(lengths) != 1:
        raise ValueError("channels differ in length: %s" % sorted(lengths))
    ints = [_to_int16(c, clip) for c in channels]
    n = len(ints[0])
    frames = [v for frame in zip(*ints) for v in frame]
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(len(ints))
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(struct.pack("<%dh" % len(frames), *frames))
    return buf.getvalue(), n


def write_wav_mono(path, samples, sample_rate=SAMPLE_RATE, clip="clip"):
    data, n = wav_bytes([samples], sample_rate, clip)
    with open(path, "wb") as fh:
        fh.write(data)
    return n


def write_wav_stereo(path, left, right, sample_rate=SAMPLE_RATE, clip="clip"):
    data, n = wav_bytes([left, right], sample_rate, clip)
    with open(path, "wb") as fh:
        fh.write(data)
    return n


def read_wav(path):
    """(channels, sample_rate, frames), as supplied."""
    with wave.open(path, "rb") as w:
        return w.getnchannels(), w.getframerate(), w.getnframes()


def read_wav_samples(path):
    """(sample_rate, [channel lists of floats in [-1, 1]]) from 16-bit PCM."""
    with wave.open(path, "rb") as w:
        if w.getsampwidth() != 2:
            raise ValueError("only 16-bit PCM is supported")
        ch, rate, n = w.getnchannels(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    vals = struct.unpack("<%dh" % (n * ch), raw)
    return rate, [[v / INT16_MAX for v in vals[c::ch]] for c in range(ch)]
