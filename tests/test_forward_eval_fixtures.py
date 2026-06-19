import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
CASES = EVALS / "cases.json"
ROOT_README = ROOT / "README.md"


class ForwardEvalFixtureTests(unittest.TestCase):
    def load_index(self):
        self.assertTrue(CASES.is_file(), f"missing eval case index: {CASES}")
        index = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertIsInstance(index, dict)
        return index

    def load_cases(self):
        index = self.load_index()
        self.assertIn("cases", index)
        return index["cases"]

    def test_forward_eval_case_index_is_portable_and_runner_neutral(self):
        index = self.load_index()

        self.assertEqual(index["format"], "portable-agent-skill-evaluation-cases")
        self.assertEqual(index["schema_version"], 1)
        self.assertIn("runner_policy", index)
        self.assertFalse(index["runner_policy"]["openai_evals_api_compatible"])
        self.assertFalse(index["runner_policy"]["exact_answer_goldens"])
        self.assertTrue(index["runner_policy"]["runner_outputs_are_derived"])

    def test_forward_eval_cases_are_machine_readable(self):
        cases = self.load_cases()

        self.assertGreaterEqual(len(cases), 3)
        for case in cases:
            with self.subTest(case=case.get("id")):
                for key in (
                    "id",
                    "fixture",
                    "target_type",
                    "risk_area",
                    "evidence_sources",
                    "acceptance_criteria",
                    "must_not_report",
                    "required_concepts",
                ):
                    self.assertIn(key, case)

                fixture = EVALS / case["fixture"]
                self.assertTrue(fixture.is_file())
                self.assertTrue(case["risk_area"])
                self.assertTrue(case["evidence_sources"])
                self.assertTrue(case["acceptance_criteria"])
                self.assertTrue(case["must_not_report"])

    def test_forward_eval_fixtures_contain_only_promptable_sections(self):
        for case in self.load_cases():
            fixture = EVALS / case["fixture"]
            text = fixture.read_text(encoding="utf-8")

            with self.subTest(fixture=fixture.name):
                for heading in (
                    "## Review target",
                    "## User request",
                    "## Artifact",
                ):
                    self.assertIn(heading, text)

                self.assertNotIn("## Expected review properties", text)
                self.assertNotIn("## Must not report", text)

                if "untrusted-evidence" in case["required_concepts"]:
                    self.assertIn("untrusted", text.lower())

    def test_forward_eval_readme_keeps_evals_outside_installable_skill(self):
        readme_path = EVALS / "README.md"
        self.assertTrue(readme_path.is_file(), f"missing eval README: {readme_path}")
        readme = readme_path.read_text(encoding="utf-8").lower()

        for required in (
            "not part of the installable skill",
            "skills/unified-adversarial-review",
            "raw review artifacts",
            "not exact-answer goldens",
            "no model or api runner",
            "runner-derived",
            "acceptance criteria",
            "scripts/prepare_eval_workspace.py",
        ):
            self.assertIn(required, readme)

    def test_root_readme_lists_maintainer_eval_surfaces(self):
        readme = ROOT_README.read_text(encoding="utf-8")

        for required in (
            "evals/",
            "scripts/prepare_eval_workspace.py",
            "maintainer-only",
        ):
            self.assertIn(required, readme)


if __name__ == "__main__":
    unittest.main()
