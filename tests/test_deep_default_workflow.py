from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "unified-adversarial-review" / "SKILL.md"
METHODOLOGY = (
    ROOT / "skills" / "unified-adversarial-review" / "references" / "methodology.md"
)


def section_between(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


def normalized_whitespace(text):
    return re.sub(r"\s+", " ", text)


def word_count(text):
    return len(re.findall(r"\S+", text))


class DeepDefaultWorkflowTests(unittest.TestCase):
    def test_top_level_skill_stays_compact_and_delegates_details(self):
        text = SKILL.read_text(encoding="utf-8")
        lower_text = text.lower()

        self.assertLessEqual(word_count(text), 1000)
        self.assertIn("methodology.md", lower_text)
        self.assertIn("finding-calibration.md", lower_text)
        self.assertIn("lenses.md", lower_text)
        self.assertNotIn("### 1. frame", lower_text)
        self.assertNotIn("### 9. report", lower_text)

        methodology_text = METHODOLOGY.read_text(encoding="utf-8").lower()
        for detailed_section in (
            "## target and scope",
            "## inspect",
            "## model",
            "## candidate generation",
            "## refutation pass",
            "## finalization gates",
        ):
            self.assertIn(detailed_section, methodology_text)

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
            "discovery map",
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
        self.assertRegex(text, r"discovery map:\s*\n-")
        self.assertRegex(text, r"candidate ledger:\s*\n-")
        self.assertRegex(text, r"multi-agent usage:\s*\n-")

    def test_methodology_defines_role_pass_output_contract(self):
        text = METHODOLOGY.read_text(encoding="utf-8").lower()

        self.assertIn("role-pass output contract", text)
        for required_field in (
            "objective",
            "search/read targets",
            "exclusions",
            "output expected",
            "stop condition",
            "handoff to the next pass",
        ):
            self.assertIn(required_field, text)

    def test_methodology_prevents_role_pass_duplication_and_gaps(self):
        text = METHODOLOGY.read_text(encoding="utf-8").lower()
        normalized_text = re.sub(r"\s+", " ", text)

        for required_instruction in (
            "divide the target",
            "do not duplicate the same search",
            "intentionally not covering because another pass owns it",
            "mapper starts broad",
            "identifies coverage gaps",
            "challenger uses the map",
            "rather than re-reading everything",
            "validator focuses on refutation checks",
            "must not add new speculative findings",
            "handed back through the candidate ledger",
        ):
            self.assertIn(required_instruction, normalized_text)

    def test_methodology_requires_discovery_pass_before_candidates(self):
        text = METHODOLOGY.read_text(encoding="utf-8").lower()

        self.assertIn("discovery pass", text)
        self.assertIn("before candidate generation", text)
        self.assertIn("source -> transform -> sink", text)
        self.assertIn("trust boundaries", text)
        self.assertIn("state/lifecycle transitions", text)
        self.assertIn("high-value assets", text)
        self.assertIn("seed candidates", text)
        self.assertIn("not as reportable evidence by itself", text)

    def test_discovery_map_is_part_of_top_level_review_contract(self):
        text = SKILL.read_text(encoding="utf-8").lower()

        self.assertIn("discovery map", text)
        self.assertIn(
            "frame -> inspect -> discovery -> model -> challenge -> trace -> refute -> adjudicate -> report",
            text,
        )
        depth_controls = section_between(
            text,
            "before finalizing, verify that the final answer can show the depth controls:",
            "## reporting",
        )
        self.assertIn("discovery map", depth_controls)

    def test_methodology_connects_discovery_to_mapper_and_finalization_gate(self):
        text = METHODOLOGY.read_text(encoding="utf-8").lower()

        role_pass_protocol = section_between(
            text,
            "### role-pass protocol",
            "## user focus",
        )
        normalized_role_pass = normalized_whitespace(role_pass_protocol)
        self.assertRegex(normalized_role_pass, r"mapper:.*discovery map")
        self.assertIn("entry points", normalized_role_pass)
        self.assertIn("source-to-sink", normalized_role_pass)
        self.assertIn("trust boundaries", normalized_role_pass)
        self.assertIn("lifecycle transitions", normalized_role_pass)
        self.assertIn("high-value assets", normalized_role_pass)

        finalization_gates = section_between(
            text,
            "## finalization gates",
            "## prompt injection",
        )
        normalized_gates = normalized_whitespace(finalization_gates)
        self.assertIn("- discovery map:", normalized_gates)
        self.assertIn("entry points", normalized_gates)
        self.assertIn("source-to-sink", normalized_gates)
        self.assertIn("trust boundaries", normalized_gates)
        self.assertIn("lifecycle transitions", normalized_gates)
        self.assertIn("high-value assets", normalized_gates)

    def test_methodology_identifies_external_contracts_during_inspect(self):
        text = METHODOLOGY.read_text(encoding="utf-8").lower()
        inspect = section_between(text, "## inspect", "## model")

        self.assertIn("load-bearing external contracts", inspect)
        self.assertIn("during inspect, not only during refute", inspect)
        for contract_type in (
            "framework",
            "protocol",
            "database",
            "queue",
            "cloud",
            "model",
            "tool",
        ):
            self.assertIn(contract_type, text)

        self.assertLess(
            text.index("load-bearing external contracts"),
            text.index("## candidate generation"),
        )

    def test_external_contracts_are_recorded_for_candidate_generation(self):
        text = METHODOLOGY.read_text(encoding="utf-8").lower()
        inspect = section_between(text, "## inspect", "## model")
        normalized_inspect = normalized_whitespace(inspect)
        candidate_generation = section_between(
            text, "## candidate generation", "## delta evidence"
        )
        normalized_candidate_generation = normalized_whitespace(candidate_generation)
        finalization_gates = section_between(
            text, "## finalization gates", "## prompt injection"
        )

        for required in (
            "record",
            "external contract or guarantee",
            "source used",
            "candidate class",
            "coverage",
            "scope map",
        ):
            self.assertIn(required, normalized_inspect)

        self.assertIn("external contract evidence", normalized_candidate_generation)
        self.assertIn("evidence searched", normalized_candidate_generation)
        self.assertIn("external-contract coverage", finalization_gates)

    def test_methodology_bounds_external_contract_discovery(self):
        text = METHODOLOGY.read_text(encoding="utf-8").lower()
        inspect = section_between(text, "## inspect", "## model")
        normalized_inspect = normalized_whitespace(inspect)

        self.assertIn(
            "do not expand this into a broad dependency audit", normalized_inspect
        )
        self.assertIn("non-load-bearing semantics", normalized_inspect)


if __name__ == "__main__":
    unittest.main()
