import json
import math
import os
import re
import unittest
from unittest import mock

from experiments import render_results, run_all, studies, wav_checks
from experiments.common import SEED_SETS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_CACHE = {}


def smoke_replicate():
    if "r" not in _CACHE:
        _CACHE["r"] = studies.replicate(9001)
    return _CACHE["r"]


class TestSeedSets(unittest.TestCase):
    def test_sets_are_disjoint_and_sized(self):
        dev, conf, smoke = (set(SEED_SETS[k]) for k in ("dev", "confirm", "smoke"))
        self.assertEqual((len(dev), len(conf), len(smoke)), (200, 200, 5))
        self.assertFalse(dev & conf or dev & smoke or conf & smoke)
        for s in dev | conf | smoke:
            self.assertNotEqual(s, 42)  # seed 42 is reserved for the scenes
        self.assertEqual((min(dev), max(dev)), (1000, 1199))
        self.assertEqual((min(conf), max(conf)), (5000, 5199))


class TestReplicate(unittest.TestCase):
    def test_every_hypothesis_key_is_produced(self):
        rep = smoke_replicate()
        for hid, key, *_ in run_all.HYPOTHESES:
            self.assertIn(key, rep, hid)

    def test_values_are_finite_floats(self):
        for key, value in smoke_replicate().items():
            self.assertTrue(math.isfinite(value), key)

    def test_deterministic(self):
        again = studies.study_f(9001)
        base = smoke_replicate()
        for key, value in again.items():
            self.assertEqual(base[key], value, key)

    def test_platform_stable_expectations_on_the_smoke_seed(self):
        rep = smoke_replicate()
        self.assertLess(rep["A/om1/pv_relerr"], 1e-6)
        self.assertEqual(rep["B/s0/win_acc"], 1.0)
        self.assertEqual(rep["B/audio_lag/sign_acc"], 1.0)
        self.assertEqual(rep["F2/readonly_identical"], 1.0)
        self.assertEqual(rep["F2/mutant_detected"], 1.0)
        self.assertAlmostEqual(rep["C/s0/coherence"], 0.990388, places=5)
        self.assertEqual(rep["D2/sign_acc"], 1.0)

    def test_mutant_sensor_class_really_mutates(self):
        from membrane_listen import Ring
        r1, r2 = Ring(seed=1), Ring(seed=1)
        m = studies._Mutant(r2, position=0.0)
        r1.step()
        r2.step()
        m.sample()
        self.assertNotEqual(r1.theta, r2.theta)


class TestProtocolMatchesCode(unittest.TestCase):
    def test_hypothesis_table_in_protocol_equals_the_code(self):
        with open(os.path.join(ROOT, "docs", "PROTOCOL.md"), encoding="utf-8") as fh:
            text = fh.read()
        rows = re.findall(r"^\| (H\d+) \| ([^ |]+) \| ([^ |]+) \| ([^ |]+) \|",
                          text, re.M)
        self.assertEqual(len(rows), 23)
        code = {h[0]: h for h in run_all.HYPOTHESES}
        for hid, key, null, alt in rows:
            c = code[hid]
            self.assertEqual((key, float(null), alt), (c[1], c[2], c[3]), hid)

    def test_protocol_precedes_results_in_history_note(self):
        with open(os.path.join(ROOT, "docs", "PROTOCOL.md"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("committed before any study result existed", text)
        self.assertIn("A1", text)


class TestRunAll(unittest.TestCase):
    def test_supported_rule(self):
        row = {"lo": 0.43, "hi": 0.52}
        self.assertTrue(run_all.supported("H10", 0.9, row))
        self.assertFalse(run_all.supported("H10", 0.01, row))
        self.assertFalse(run_all.supported("H10", 0.9, {"lo": 0.30, "hi": 0.52}))
        self.assertTrue(run_all.supported("H21", 0.5, {"lo": 0.47, "hi": 0.52}))
        self.assertFalse(run_all.supported("H21", 0.5, {"lo": 0.40, "hi": 0.52}))
        self.assertTrue(run_all.supported("H1", 0.049, row))
        self.assertFalse(run_all.supported("H1", 0.05, row))

    def test_tiny_run_has_the_documented_structure(self):
        with mock.patch.dict(run_all.SEED_SETS, {"tiny": [9001, 9002]}):
            res = run_all.run("tiny", 1, 50, 100)
        self.assertEqual(res["meta"]["replicates"], 2)
        self.assertTrue(res["meta"]["synthetic"])
        self.assertEqual([h["id"] for h in res["hypotheses"]],
                         [f"H{i}" for i in range(1, 24)])
        for h in res["hypotheses"]:
            self.assertTrue(0 < h["p"] <= 1 and h["p"] <= h["p_holm"] <= 1)
        for row in res["rows"].values():
            self.assertLessEqual(row["lo"], row["hi"])
        _CACHE["tiny"] = res

    def test_renderer_on_a_tiny_run(self):
        if "tiny" not in _CACHE:
            self.test_tiny_run_has_the_documented_structure()
        res = _CACHE["tiny"]
        text = render_results.render(res, res, wav_checks.run(),
                                     "## Interpretation\n\ntext\n")
        for needle in ("# Results", "SYNTHETIC", "## Limitations",
                       "Study A", "Study B", "Study C", "Study D",
                       "Study E", "Study F", "H23", "No listening test was run"):
            self.assertIn(needle, text)
        self.assertEqual(text, render_results.render(res, res, wav_checks.run(),
                                                     "## Interpretation\n\ntext\n"))


class TestWavChecks(unittest.TestCase):
    def test_all_checks_pass_on_the_committed_files(self):
        res = wav_checks.run()
        self.assertTrue(res["all_pass"], json.dumps(res["checks"], indent=1))
        self.assertGreaterEqual(res["n_checks"], 20)

    def test_aliasing_tables(self):
        res = wav_checks.run()
        for row in res["aliasing_tones"]:
            self.assertAlmostEqual(row["measured_hz"], row["expected_hz"],
                                   delta=0.5)
        for row in res["aliasing_phase"]:
            self.assertAlmostEqual(row["measured_omega"],
                                   row["expected_omega"], places=5)

    def test_committed_json_matches_a_fresh_run(self):
        path = os.path.join(ROOT, "docs", "results", "wav_checks.json")
        if not os.path.exists(path):
            self.skipTest("wav_checks.json not generated yet")
        with open(path, encoding="utf-8") as fh:
            committed = json.load(fh)
        self.assertEqual(committed, json.loads(json.dumps(wav_checks.run())))


if __name__ == "__main__":
    unittest.main()
