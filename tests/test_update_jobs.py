import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "src" / "update_jobs.py"
SPEC = importlib.util.spec_from_file_location("update_jobs", MODULE_PATH)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class AuthorizationClassificationTests(unittest.TestCase):
    def test_explicit_cpt_acceptance(self):
        self.assertEqual(module.classify_authorization("We accept CPT candidates for this internship.")[0], "explicit_cpt_yes")

    def test_explicit_cpt_rejection(self):
        self.assertEqual(module.classify_authorization("Candidates using CPT are not eligible.")[0], "explicit_cpt_no")

    def test_generic_no_sponsorship_is_not_mislabeled_as_cpt_rejection(self):
        status, wording, _ = module.classify_authorization("We are unable to provide visa sponsorship now or in the future.")
        self.assertEqual(status, "possible_restriction")
        self.assertEqual(wording, "generic_no_sponsorship_wording")

    def test_silence_means_unknown(self):
        self.assertEqual(module.classify_authorization("Strong communication skills and teamwork.")[0], "unknown")


class PostingFilterTests(unittest.TestCase):
    def test_keeps_us_data_internship(self):
        source = {"company": "Example", "platform": "greenhouse", "careers_url": "https://example.com"}
        raw = {"title": "Data Analyst Intern - Summer 2027", "content": "SQL and dashboard work.", "location": {"name": "New York, NY"}, "absolute_url": "https://example.com/job/1"}
        self.assertIsNotNone(module.normalize(source, raw, "2026-10-15T00:00:00+00:00"))

    def test_excludes_non_internship(self):
        source = {"company": "Example", "platform": "greenhouse", "careers_url": "https://example.com"}
        raw = {"title": "Data Analyst II", "content": "Data analytics role.", "location": {"name": "Atlanta, GA"}, "absolute_url": "https://example.com/job/2"}
        self.assertIsNone(module.normalize(source, raw, "2026-10-15T00:00:00+00:00"))


if __name__ == "__main__":
    unittest.main()
