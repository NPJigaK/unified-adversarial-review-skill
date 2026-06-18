import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import validate_review_output as validator_module


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_review_output.py"
SEMANTIC_SCHEMA = ROOT / "schemas" / "review-output.semantic.schema.json"
OPENAI_SCHEMA = ROOT / "schemas" / "review-output.openai.schema.json"


def valid_output():
    return {
        "schema_version": "1.0",
        "method_version": "1.0",
        "finding_assessment": "no-material-findings",
        "coverage_status": "sufficient",
        "summary": "No material findings within supplied context.",
        "scope": {
            "target": "supplied diff",
            "capability_modes": ["supplied-context"],
            "base": {
                "branch_component_available": False,
                "base_ref": None,
                "base_commit_oid": None,
                "merge_base_oid": None,
                "base_resolution_method": "not-applicable",
                "remote_freshness": "not-applicable",
                "notes": None,
            },
            "components": [
                {
                    "id": "supplied-context",
                    "kind": "supplied-context",
                    "status": "included",
                    "description": "User supplied diff",
                    "paths": [],
                    "reason": None,
                }
            ],
            "intent_sources": [],
        },
        "findings": [],
        "uncertainties": [],
        "coverage": {
            "lenses_considered": [],
            "lenses_applied": [],
            "lenses_skipped_with_reason": [],
            "checks_performed": ["target resolved", "review packet inspected"],
            "component_coverage": [
                {
                    "scope_components": ["supplied-context"],
                    "status": "evaluated",
                    "checks_performed": ["supplied diff inspected"],
                    "reason": None,
                }
            ],
            "limitations": [],
            "sensitive_artifacts": [],
        },
        "next_steps": [],
    }


def run_validator(doc, schema=None):
    errors, usage_error = validator_module.validate_document(
        doc, schema or SEMANTIC_SCHEMA
    )
    return subprocess.CompletedProcess(
        args=[],
        returncode=2 if usage_error else (1 if errors else 0),
        stdout="review output valid\n" if not errors else "",
        stderr="\n".join(errors),
    )


def run_validator_cli(doc, validator=VALIDATOR, schema=None):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(doc, f)
        output_path = Path(f.name)
    try:
        cmd = [sys.executable, str(validator), str(output_path)]
        if schema is not None:
            cmd.extend(["--schema", str(schema)])
        return subprocess.run(cmd, text=True, capture_output=True)
    finally:
        output_path.unlink(missing_ok=True)


class ValidateReviewOutputTests(unittest.TestCase):
    def test_valid_output_passes(self):
        cp = run_validator(valid_output())
        self.assertEqual(cp.returncode, 0, cp.stderr)

    def test_installed_layout_default_validation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "unified-adversarial-review"
            (root / "scripts").mkdir(parents=True)
            (root / "assets").mkdir()
            shutil.copy2(VALIDATOR, root / "scripts" / "validate_review_output.py")
            shutil.copy2(SEMANTIC_SCHEMA, root / "assets" / "review-output.semantic.schema.json")
            cp = run_validator_cli(valid_output(), validator=root / "scripts" / "validate_review_output.py")
            self.assertEqual(cp.returncode, 0, cp.stderr)

    def test_noop_sufficient_is_rejected(self):
        doc = valid_output()
        doc["coverage"]["checks_performed"] = []
        doc["coverage"]["component_coverage"] = []
        cp = run_validator(doc)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("coverage.checks_performed", cp.stderr)

    def test_branch_diff_requires_git_base(self):
        doc = valid_output()
        doc["scope"]["components"] = [
            {
                "id": "branch-diff",
                "kind": "branch-diff",
                "status": "included",
                "description": "branch diff",
                "paths": [],
                "reason": None,
            }
        ]
        doc["coverage"]["component_coverage"][0]["scope_components"] = ["branch-diff"]
        cp = run_validator(doc)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("included branch-diff requires", cp.stderr)

    def test_reviewer_executed_command_requires_safe_exec(self):
        doc = valid_output()
        doc["finding_assessment"] = "material-findings"
        doc["coverage_status"] = "limited"
        doc["coverage"]["lenses_considered"] = ["security-trust"]
        doc["coverage"]["lenses_applied"] = ["security-trust"]
        doc["findings"] = [
            {
                "id": "F-1",
                "scope_components": ["supplied-context"],
                "severity": "high",
                "confidence": "high",
                "finding_level": "implementation",
                "risk_domains": ["security-trust"],
                "primary_lens": "security-trust",
                "title": "Command evidence needs safe exec",
                "type": "implementation",
                "change_relation": "introduced",
                "delta_evidence": [
                    {"kind": "new-reachable-path", "detail": "changed path", "location_ref": "L-1"}
                ],
                "causal_trace": {
                    "preconditions": ["input reaches changed code"],
                    "trigger": "request",
                    "reachable_path": ["handler"],
                    "failed_guard_or_transition": "guard missing",
                    "violated_invariant": "only safe commands are run",
                    "impact": "unsafe command execution",
                },
                "body": "Concrete scenario.",
                "locations": [
                    {
                        "id": "L-1",
                        "kind": "command",
                        "display_command": "pytest tests/example.py",
                        "command_digest": "a" * 64,
                        "digest_algorithm": "sha256",
                        "digest_source": "agent-reported",
                        "command_origin": "reviewer-executed",
                        "exit_code": 0,
                        "output_digest": "b" * 64,
                        "relevant_excerpt": "",
                        "redaction_applied": False,
                        "redaction_note": None,
                    }
                ],
                "evidence": [{"kind": "command", "detail": "command ran", "location_ref": "L-1"}],
                "assumptions": [],
                "verification": {
                    "checks_performed": ["command result inspected"],
                    "refutations_checked": ["checked for existing guard"],
                    "remaining_gaps": [],
                },
                "recommendation": "Use safe execution policy.",
            }
        ]
        cp = run_validator(doc)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("requires safe-exec", cp.stderr)

    def test_redacted_bearer_placeholder_is_allowed_but_real_token_is_rejected(self):
        doc = valid_output()
        doc["coverage"]["checks_performed"] = ["Authorization: Bearer [REDACTED] checked"]
        cp = run_validator(doc)
        self.assertEqual(cp.returncode, 0, cp.stderr)

        doc["summary"] = "Authorization: Basic abc123"
        cp = run_validator(doc)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("unredacted secret", cp.stderr)

    def test_path_traversal_is_rejected(self):
        doc = valid_output()
        doc["scope"]["components"][0]["paths"] = ["../outside/secret.py"]
        cp = run_validator(doc)
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("must not escape", cp.stderr)

    def test_openai_schema_shape_validates_then_semantic_validator_accepts(self):
        import jsonschema

        doc = valid_output()
        schema = json.loads(OPENAI_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.validate(instance=doc, schema=schema)
        cp = run_validator(doc)
        self.assertEqual(cp.returncode, 0, cp.stderr)

    def test_openai_schema_fields_exist_in_semantic_schema(self):
        semantic = json.loads(SEMANTIC_SCHEMA.read_text(encoding="utf-8"))
        openai = json.loads(OPENAI_SCHEMA.read_text(encoding="utf-8"))

        def collect_object_fields(schema, prefix="$"):
            fields = set()
            if isinstance(schema, dict):
                props = schema.get("properties")
                if isinstance(props, dict):
                    for key, value in props.items():
                        child = f"{prefix}.{key}"
                        fields.add(child)
                        fields |= collect_object_fields(value, child)
                for key in ("$defs", "items", "anyOf", "oneOf", "allOf"):
                    value = schema.get(key)
                    if isinstance(value, dict):
                        for child_key, child_value in value.items():
                            fields |= collect_object_fields(child_value, f"#/$defs/{child_key}")
                    elif isinstance(value, list):
                        for item in value:
                            fields |= collect_object_fields(item, prefix)
            return fields

        semantic_fields = collect_object_fields(semantic)
        openai_fields = collect_object_fields(openai)
        missing = sorted(openai_fields - semantic_fields)
        self.assertFalse(missing, missing)

    def test_plan_review_relations_are_supported_by_both_schemas(self):
        for schema_path in (SEMANTIC_SCHEMA, OPENAI_SCHEMA):
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            self.assertIn(
                "proposed",
                schema["$defs"]["finding"]["properties"]["change_relation"]["enum"],
            )
            self.assertIn(
                "proposed-failure-path",
                schema["$defs"]["delta_evidence"]["properties"]["kind"]["enum"],
            )

    def test_missing_schema_returns_usage_error(self):
        cp = run_validator_cli(valid_output(), schema=ROOT / "does-not-exist.schema.json")
        self.assertEqual(cp.returncode, 2)
        self.assertIn("semantic schema not found", cp.stderr)

    def test_broken_schema_returns_usage_error(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write("{")
            schema_path = Path(f.name)
        try:
            cp = run_validator_cli(valid_output(), schema=schema_path)
        finally:
            schema_path.unlink(missing_ok=True)
        self.assertEqual(cp.returncode, 2)
        self.assertIn("semantic schema is invalid JSON", cp.stderr)


if __name__ == "__main__":
    unittest.main()
