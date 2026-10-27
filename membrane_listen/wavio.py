"""WAV input and output (standard library wave and struct)."""

import struct
import wave

from .core import SAMPLE_RATE

def _to_int16(samples):
    return [max(-32767, min(32767, int(round(s * 32767)))) for s in samples]


def write_wav_mono(path, samples, sample_rate=SAMPLE_RATE):
    frames = _to_int16(samples)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(struct.pack("<%dh" % len(frames), *frames))
    return len(frames)


def write_wav_stereo(path, left, right, sample_rate=SAMPLE_RATE):
    li, ri = _to_int16(left), _to_int16(right)
    frames = [v for pair in zip(li, ri) for v in pair]
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(struct.pack("<%dh" % len(frames), *frames))
    return len(li)


def read_wav(path):
    with wave.open(path, "rb") as w:
        return w.getnchannels(), w.getframerate(), w.getnframes()
