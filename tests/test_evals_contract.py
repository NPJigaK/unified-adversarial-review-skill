from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
CASES = EVALS / "cases"
README = EVALS / "README.md"
RUBRIC = EVALS / "rubric.md"
SCHEMA = EVALS / "review-output.schema.json"
SKILL_DIR = ROOT / "skills" / "unified-adversarial-review"


def read_text(path):
    return path.read_text(encoding="utf-8")


def load_cases():
    case_paths = sorted(CASES.glob("*.json"))
    cases = []
    for path in case_paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            cases.extend(data)
        else:
            cases.append(data)
    return cases


class EvalsContractTests(unittest.TestCase):
    def test_decision_is_backed_by_local_and_primary_evidence(self):
        text = read_text(README)

        self.assertIn("Decision: add evals", text)

        for local_anchor in (
            "skills/unified-adversarial-review/SKILL.md",
            "skills/unified-adversarial-review/references/methodology.md",
            "tests/test_deep_default_workflow.py",
        ):
            self.assertIn(local_anchor, text)

        for primary_source in (
            "https://developers.openai.com/blog/eval-skills",
            "https://developers.openai.com/api/docs/guides/evaluation-best-practices",
            "https://developers.openai.com/api/docs/guides/agent-evals",
            "https://developers.openai.com/codex/skills",
        ):
            self.assertIn(primary_source, text)

        self.assertIn("Local evidence", text)
        self.assertIn("Primary-source evidence", text)

    def test_evals_live_outside_the_installable_skill(self):
        text = read_text(README)

        self.assertIn("not installed with the Skill", text)
        self.assertFalse((SKILL_DIR / "evals").exists())

    def test_eval_cases_cover_core_behavioral_risks(self):
        cases = load_cases()
        categories = {case["category"] for case in cases}

        self.assertGreaterEqual(len(cases), 6)
        self.assertSetEqual(
            categories,
            {
                "true_positive",
                "false_positive_refutation",
                "scope_control",
                "limited_coverage",
                "prompt_injection",
                "plan_review",
            },
        )

    def test_eval_cases_require_trusted_evidence_for_expected_outcomes(self):
        cases = load_cases()
        valid_source_types = {
            "target",
            "supporting_context",
            "local_repo",
            "primary_source",
        }

        for case in cases:
            with self.subTest(case=case["id"]):
                for key in (
                    "id",
                    "title",
                    "category",
                    "task_mode",
                    "objective",
                    "prompt",
                    "target",
                    "expected",
                    "trusted_evidence",
                ):
                    self.assertIn(key, case)

                self.assertIn("kind", case["target"])
                self.assertIn("content", case["target"])
                self.assertIn(
                    case["expected"]["finding_assessment"],
                    ("material-findings", "no-material-findings"),
                )
                self.assertIn(
                    case["expected"]["coverage_status"],
                    ("sufficient", "limited", "insufficient"),
                )

                evidence = case["trusted_evidence"]
                self.assertIsInstance(evidence, list)
                self.assertGreaterEqual(len(evidence), 1)
                for item in evidence:
                    self.assertIn(item["source_type"], valid_source_types)
                    self.assertTrue(item["anchor"])
                    self.assertTrue(item["why_trusted"])

                for expectation_key in ("must_include", "must_not_include"):
                    self.assertIn(expectation_key, case["expected"])
                    for item in case["expected"][expectation_key]:
                        self.assertTrue(item["claim"])
                        self.assertTrue(item["evidence_anchor"])
                        self.assertTrue(item["reason"])

    def test_rubric_makes_evidence_refutation_and_coverage_mandatory(self):
        text = read_text(RUBRIC)
        normalized = " ".join(text.lower().split())

        for required in (
            "trusted evidence gate",
            "affected evidence",
            "causal path",
            "refutation",
            "coverage",
            "candidate ledger",
            "unsupported finding",
        ):
            self.assertIn(required, normalized)

    def test_review_output_schema_requires_grounding_fields(self):
        schema = json.loads(read_text(SCHEMA))

        self.assertEqual(schema["type"], "object")
        self.assertIn("findings", schema["required"])
        self.assertIn("coverage", schema["required"])
        self.assertIn("evidence_audit", schema["required"])

        finding_schema = schema["properties"]["findings"]["items"]
        for required in (
            "affected_evidence",
            "causal_path",
            "change_relation",
            "refutation",
            "impact",
            "recommendation",
            "confidence",
            "trusted_evidence_used",
        ):
            self.assertIn(required, finding_schema["required"])

        coverage_schema = schema["properties"]["coverage"]
        self.assertIn("status", coverage_schema["required"])
        self.assertIn("not_verified", coverage_schema["required"])


if __name__ == "__main__":
    unittest.main()
