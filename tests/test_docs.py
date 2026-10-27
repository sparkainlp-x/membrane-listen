import hashlib
import json
import os
import re
import unittest

import membrane_listen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


class TestLicense(unittest.TestCase):
    def test_full_official_agpl_text(self):
        with open(os.path.join(ROOT, "LICENSE"), "rb") as fh:
            data = fh.read()
        self.assertEqual(len(data), 34523)
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         "0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0")
        text = data.decode("utf-8")
        self.assertIn("GNU AFFERO GENERAL PUBLIC LICENSE", text)
        self.assertIn("Version 3, 19 November 2007", text)


class TestMetadata(unittest.TestCase):
    def test_versions_agree_and_no_release_is_claimed(self):
        self.assertEqual(membrane_listen.__version__, "0.1.0")
        self.assertIn('version = "0.1.0"', read("pyproject.toml"))
        self.assertIn("version: 0.1.0", read("CITATION.cff"))
        self.assertEqual(json.loads(read(".zenodo.json"))["version"], "0.1.0")
        self.assertIn("## 0.1.0 (2026-10-27)", read("CHANGELOG.md"))
        self.assertIn("released on GitHub on 2026-10-27",
                      read("README.md").replace("\n", " "))
        cff = read("CITATION.cff")
        self.assertIn("date-released: 2026-10-27", cff)
        self.assertEqual(json.loads(read(".zenodo.json"))["publication_date"],
                         "2026-10-27")

    def test_zenodo_dois_are_recorded_in_the_citation_files(self):
        version_doi = "10.5281/zenodo.23687758"
        concept_doi = "10.5281/zenodo.23687757"
        cff = read("CITATION.cff")
        self.assertIn("doi: " + version_doi, cff)
        self.assertIn("value: " + concept_doi, cff)
        for name in ("README.md", "CHANGELOG.md"):
            text = read(name)
            self.assertIn(version_doi, text)
            self.assertIn(concept_doi, text)
        # the archive metadata is deliberately left without DOIs
        self.assertNotIn("doi", read(".zenodo.json").lower())

    def test_sole_author_with_orcid_and_licence(self):
        z = json.loads(read(".zenodo.json"))
        self.assertEqual(len(z["creators"]), 1)
        self.assertEqual(z["creators"][0]["name"], "Brisson, Jean-François")
        self.assertEqual(z["creators"][0]["orcid"], "0009-0000-9778-5374")
        self.assertEqual(z["license"], "AGPL-3.0-only")
        cff = read("CITATION.cff")
        self.assertEqual(cff.count("family-names:"), 1)
        self.assertIn("orcid: https://orcid.org/0009-0000-9778-5374", cff)
        self.assertIn("license: AGPL-3.0-only", cff)
        self.assertIn('license = "AGPL-3.0-only"', read("pyproject.toml"))

    def test_runtime_is_standard_library_only(self):
        self.assertIn("dependencies = []", read("pyproject.toml"))
        self.assertIn('requires-python = ">=3.10"', read("pyproject.toml"))
        std = {"cmath", "math", "random", "struct", "wave", "io", "hashlib",
               "argparse", "os", "sys", "json", "platform", "multiprocessing",
               "re", "subprocess", "copy", "unittest", "tempfile"}
        for base, _, names in os.walk(os.path.join(ROOT, "membrane_listen")):
            for name in names:
                if not name.endswith(".py"):
                    continue
                for line in read(os.path.relpath(os.path.join(base, name),
                                                 ROOT)).splitlines():
                    m = re.match(r"\s*(?:import|from)\s+([A-Za-z_][\w]*)", line)
                    if m and not line.lstrip().startswith("from ."):
                        self.assertIn(m.group(1), std | {"membrane_listen"},
                                      (name, line))

    def test_no_network_in_ci_and_matrix(self):
        ci = read(".github", "workflows", "ci.yml")
        for v in ("3.10", "3.11", "3.12", "3.13"):
            self.assertIn(f'"{v}"', ci)
        self.assertNotIn("pip install", ci)
        self.assertNotIn("curl", ci)


class TestReadme(unittest.TestCase):
    def test_honest_limits_come_before_the_quickstart(self):
        text = read("README.md")
        self.assertLess(text.index("## Honest limits"),
                        text.index("## Quickstart"))
        for needle in ("SYNTHETIC", "No listening test was run",
                       "not an ECG", "Not a heart, not a brain"):
            self.assertIn(needle, text.replace("\n", " "))

    def test_scene_table_lists_all_six_files_and_seeds(self):
        text = read("README.md")
        for name in ("wave_forward.wav", "wave_reverse.wav",
                     "wave_stereo_forward.wav", "wave_stereo_reverse.wav",
                     "heart.wav", "brain_stereo.wav"):
            self.assertIn(f"`{name}`", text)
            self.assertTrue(os.path.exists(os.path.join(ROOT, "wav", name)))
        self.assertIn("seed 42", text)

    def test_readme_numbers_match_the_results_files(self):
        res = json.loads(read("docs", "results", "confirm.json"))
        rows = res["rows"]
        self.assertAlmostEqual(rows["C/undriven_coupled/coherence"]["mean"],
                               0.968, places=3)
        self.assertAlmostEqual(rows["B/s1/win_acc"]["mean"], 0.95, places=2)
        self.assertAlmostEqual(rows["C/undriven_coupled/wave_order"]["mean"],
                               0.34, places=2)
        text = read("README.md")
        for needle in ("0.968", "0.389", "0.9994", "0.496", "0.34"):
            self.assertIn(needle, text)
        not_supported = [h["id"] for h in res["hypotheses"]
                         if not h["supported"]]
        self.assertEqual(not_supported, ["H5", "H14"])


class TestDesign(unittest.TestCase):
    def test_supplied_test_bug_notes_are_kept(self):
        text = read("DESIGN.md").replace("\n", " ")
        self.assertIn("counted every sine zero-crossing as a thump", text)
        self.assertIn("Gap check ran past the end of the signal", text)

    def test_inconsistencies_are_documented(self):
        text = read("DESIGN.md").replace("\n", " ")
        self.assertIn("0.60 s = 4800 samples", text)
        self.assertIn("1273 Hz", text)
        self.assertIn("follow_probe", text)

    def test_protocol_and_results_exist(self):
        for path in (("docs", "PROTOCOL.md"), ("docs", "RESULTS.md"),
                     ("docs", "interpretation.md"),
                     ("docs", "results", "dev.json"),
                     ("docs", "results", "confirm.json"),
                     ("docs", "results", "wav_checks.json"),
                     ("CONTRIBUTING.md",), ("SECURITY.md",)):
            self.assertTrue(os.path.exists(os.path.join(ROOT, *path)), path)

    def test_results_state_the_limitations(self):
        text = read("docs", "RESULTS.md")
        self.assertIn("## Limitations", text)
        self.assertIn("No listening test was run", text)


if __name__ == "__main__":
    unittest.main()
