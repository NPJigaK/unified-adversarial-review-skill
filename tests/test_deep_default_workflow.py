from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "unified-adversarial-review" / "SKILL.md"
METHODOLOGY = (
    ROOT / "skills" / "unified-adversarial-review" / "references" / "methodology.md"
)


class DeepDefaultWorkflowTests(unittest.TestCase):
    def test_skill_makes_deep_review_the_default(self):
        text = SKILL.read_text(encoding="utf-8").lower()

        self.assertIn("deep review is the default", text)
        self.assertIn("do not offer or choose a quick review mode", text)
        self.assertIn("do not finalize after a single skim", text)
        self.assertIn("candidate ledger", text)
        self.assertIn("refutation record", text)

    def test_methodology_requires_role_passes_even_without_subagents(self):
        text = METHODOLOGY.read_text(encoding="utf-8").lower()

        for role in ("mapper", "challenger", "validator"):
            self.assertRegex(text, rf"\b{role}\b")

        self.assertIn("role-pass protocol", text)
        self.assertIn("run the same roles sequentially yourself", text)
        self.assertIn("preferred when available", text)
        self.assertIn("not required for semantic completeness", text)

    def test_methodology_has_hard_finalization_gates(self):
        text = METHODOLOGY.read_text(encoding="utf-8").lower()

        required_gates = [
            "scope map",
            "risk lens routing record",
            "candidate ledger",
            "refutation record",
            "coverage justification",
            "multi-agent usage record",
        ]
        for gate in required_gates:
            self.assertIn(gate, text)

    def test_report_template_exposes_depth_and_orchestration(self):
        text = SKILL.read_text(encoding="utf-8").lower()

        self.assertIn("depth and orchestration", text)
        self.assertRegex(text, r"role passes:\s*\n-")
        self.assertRegex(text, r"candidate ledger:\s*\n-")
        self.assertRegex(text, r"multi-agent usage:\s*\n-")


if __name__ == "__main__":
    unittest.main()
