import io
import os
import subprocess
import sys
import tempfile
import unittest
import wave

from membrane_listen import __main__ as cli
from membrane_listen.scenes import SCENE_FILES, build_scenes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WAV = os.path.join(ROOT, "wav")


class TestScenes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenes = build_scenes()

    def test_six_scenes_in_order(self):
        self.assertEqual(tuple(self.scenes), SCENE_FILES)
        self.assertEqual(len(SCENE_FILES), 6)

    def test_regeneration_matches_committed_wavs_byte_for_byte(self):
        # Platform note: values use exactly rounded sums and standard
        # libm functions; the committed files were checked identical on
        # Python 3.10 to 3.13 (Linux). A different libm could in
        # principle differ in the last bit of a sample, which would show
        # up here first.
        for name in SCENE_FILES:
            with open(os.path.join(WAV, name), "rb") as fh:
                self.assertEqual(fh.read(), self.scenes[name][0], name)

    def test_regeneration_is_deterministic(self):
        again = build_scenes()
        for name in SCENE_FILES:
            self.assertEqual(again[name][0], self.scenes[name][0], name)

    def test_committed_files_are_small(self):
        total = sum(os.path.getsize(os.path.join(WAV, n)) for n in SCENE_FILES)
        self.assertLess(total, 500_000)

    def test_headers(self):
        expect = {"wave_forward.wav": (1, 16000), "wave_reverse.wav": (1, 16000),
                  "wave_stereo_forward.wav": (2, 16000),
                  "wave_stereo_reverse.wav": (2, 16000),
                  "heart.wav": (1, 32000), "brain_stereo.wav": (2, 38400)}
        for name, (ch, frames) in expect.items():
            with wave.open(io.BytesIO(self.scenes[name][0]), "rb") as w:
                self.assertEqual((w.getnchannels(), w.getnframes(),
                                  w.getframerate(), w.getsampwidth()),
                                 (ch, frames, 8000, 2), name)

    def test_nothing_clips(self):
        for name in SCENE_FILES:
            self.assertLess(self.scenes[name][1]["peak"], 1.0, name)

    def test_readme_numbers_reproduce(self):
        f = self.scenes["wave_forward.wav"][1]
        r = self.scenes["wave_reverse.wav"][1]
        self.assertAlmostEqual(f["k_est"], 1.0, places=2)
        self.assertAlmostEqual(r["k_est"], -1.0, places=2)
        for x in (f, r):
            self.assertAlmostEqual(x["omega"], -1.0, places=3)
            self.assertAlmostEqual(x["coherence"], 0.990, places=3)
            self.assertAlmostEqual(x["wave_order"], 1.0, places=3)
        sf = self.scenes["wave_stereo_forward.wav"][1]
        sr = self.scenes["wave_stereo_reverse.wav"][1]
        self.assertAlmostEqual(sf["gap_mean"], 3.141592653589793 / 2, places=3)
        self.assertAlmostEqual(sr["gap_mean"], -3.141592653589793 / 2, places=3)
        self.assertEqual(self.scenes["heart.wav"][1]["thumps"], 5)
        b = self.scenes["brain_stereo.wav"][1]
        self.assertAlmostEqual(b["spread_s"], 0.43, places=9)

    def test_forward_and_reverse_mono_files_are_different_files(self):
        self.assertNotEqual(self.scenes["wave_forward.wav"][0],
                            self.scenes["wave_reverse.wav"][0])


class TestCLI(unittest.TestCase):
    def test_writes_and_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "w")
            buf = io.StringIO()
            old, sys.stdout = sys.stdout, buf
            try:
                self.assertEqual(cli.main(["--out", out]), 0)
                self.assertEqual(cli.main(["--out", out, "--check"]), 0)
            finally:
                sys.stdout = old
            self.assertEqual(sorted(os.listdir(out)), sorted(SCENE_FILES))
            with open(os.path.join(out, "heart.wav"), "ab") as fh:
                fh.write(b"x")
            sys.stdout = io.StringIO()
            try:
                self.assertEqual(cli.main(["--out", out, "--check"]), 1)
            finally:
                sys.stdout = old
            self.assertIn("SYNTHETIC", buf.getvalue())

    def test_check_with_missing_files_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, sys.stdout = sys.stdout, io.StringIO()
            try:
                self.assertEqual(cli.main(["--out", tmp, "--check"]), 1)
            finally:
                sys.stdout = old

    def test_module_entry_point_and_shim(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([sys.executable, "-W", "error", "-m",
                                "membrane_listen", "--out", tmp],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("not a recording", r.stdout)
        r = subprocess.run([sys.executable, "-W", "error", "-m",
                            "membrane_listen", "--check", "--out", WAV],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
