import math
import os
import struct
import tempfile
import unittest
import wave

from membrane_listen import (_to_int16, read_wav, read_wav_samples,
                             wav_bytes, write_wav_mono, write_wav_stereo)


class TestWavIO(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "x.wav")

    def test_header_mono(self):
        write_wav_mono(self.path, [0.0, 0.5, -0.5, 1.0])
        with wave.open(self.path, "rb") as w:
            self.assertEqual((w.getnchannels(), w.getsampwidth(),
                              w.getframerate(), w.getnframes()),
                             (1, 2, 8000, 4))
            self.assertEqual(struct.unpack("<4h", w.readframes(4)),
                             (0, 16384, -16384, 32767))

    def test_header_stereo_interleaving_and_block_align(self):
        write_wav_stereo(self.path, [0.1, 0.2, 0.3], [-0.1, -0.2, -0.3])
        with open(self.path, "rb") as fh:
            head = fh.read(44)
        self.assertEqual(head[:4], b"RIFF")
        self.assertEqual(head[8:16], b"WAVEfmt ")
        channels, rate, byte_rate, block, bits = struct.unpack(
            "<HIIHH", head[22:36])
        self.assertEqual((channels, rate, byte_rate, block, bits),
                         (2, 8000, 8000 * 4, 4, 16))
        self.assertEqual(struct.unpack("<I", head[40:44])[0], 3 * 4)
        self.assertEqual(struct.unpack("<I", head[4:8])[0], 36 + 3 * 4)
        ch, rate, frames = read_wav(self.path)
        self.assertEqual((ch, rate, frames), (2, 8000, 3))
        rate, (left, right) = read_wav_samples(self.path)
        self.assertAlmostEqual(left[1], 0.2, places=4)
        self.assertAlmostEqual(right[1], -0.2, places=4)

    def test_stereo_channel_order_is_left_then_right(self):
        write_wav_stereo(self.path, [0.5], [-0.5])
        with wave.open(self.path, "rb") as w:
            self.assertEqual(struct.unpack("<2h", w.readframes(1)),
                             (16384, -16384))

    def test_unequal_channels_rejected(self):
        with self.assertRaises(ValueError):
            write_wav_stereo(self.path, [0.1] * 5, [0.1] * 3)
        self.assertFalse(os.path.exists(self.path))

    def test_non_finite_samples_rejected(self):
        for bad in (float("nan"), float("inf"), float("-inf")):
            with self.assertRaises(ValueError):
                write_wav_mono(self.path, [0.1, bad])

    def test_clipping_is_symmetric_and_can_be_made_an_error(self):
        self.assertEqual(_to_int16([2.0, -2.0, 1.0, -1.0]),
                         [32767, -32767, 32767, -32767])
        with self.assertRaises(ValueError):
            _to_int16([1.01], clip="error")
        self.assertEqual(_to_int16([1.0, -1.0], clip="error"),
                         [32767, -32767])
        with self.assertRaises(ValueError):
            _to_int16([0.0], clip="maybe")

    def test_silent_and_empty_signals(self):
        n = write_wav_mono(self.path, [0.0] * 100)
        self.assertEqual(n, 100)
        _, (ch,) = read_wav_samples(self.path)
        self.assertEqual(ch, [0.0] * 100)
        self.assertEqual(write_wav_mono(self.path, []), 0)
        self.assertEqual(read_wav(self.path), (1, 8000, 0))

    def test_bad_sample_rate_rejected(self):
        for bad in (0, -8000, 8000.0, True, None):
            with self.assertRaises(ValueError):
                wav_bytes([[0.0]], sample_rate=bad)

    def test_round_trip_within_one_quantisation_step(self):
        sig = [math.sin(0.01 * i) for i in range(1000)]
        write_wav_mono(self.path, sig)
        _, (back,) = read_wav_samples(self.path)
        self.assertLess(max(abs(a - b) for a, b in zip(sig, back)),
                        0.5 / 32767 + 1e-12)

    def test_bytes_equal_file_contents(self):
        data, n = wav_bytes([[0.1, 0.2]])
        write_wav_mono(self.path, [0.1, 0.2])
        with open(self.path, "rb") as fh:
            self.assertEqual(fh.read(), data)
        self.assertEqual(n, 2)

    def test_no_channels_rejected(self):
        with self.assertRaises(ValueError):
            wav_bytes([])


if __name__ == "__main__":
    unittest.main()
