#!/usr/bin/env python3
"""Prepare prompt/rubric files from portable adversarial-review eval cases."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


FORMAT = "portable-agent-skill-evaluation-cases"
WORKSPACE_FORMAT = "prepared-adversarial-review-eval-workspace"
REQUIRED_CASE_KEYS = {
    "id",
    "fixture",
    "target_type",
    "risk_area",
    "evidence_sources",
    "acceptance_criteria",
    "must_not_report",
    "required_concepts",
}
REQUIRED_PROMPT_SECTIONS = (
    "## Review target",
    "## User request",
    "## Artifact",
)
EVALUATOR_ONLY_SECTIONS = (
    "## Expected review properties",
    "## Must not report",
)
CASE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class EvalConfigError(ValueError):
    pass


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvalConfigError(f"{path}: invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise EvalConfigError(f"{path}: top-level value must be an object")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvalConfigError(message)


def validate_index(index: dict, cases_path: Path) -> list[dict]:
    require(
        index.get("format") == FORMAT,
        f"{cases_path}: format must be {FORMAT!r}",
    )
    require(index.get("schema_version") == 1, f"{cases_path}: schema_version must be 1")

    runner_policy = index.get("runner_policy")
    require(isinstance(runner_policy, dict), f"{cases_path}: runner_policy must be an object")
    require(
        runner_policy.get("openai_evals_api_compatible") is False,
        f"{cases_path}: runner_policy.openai_evals_api_compatible must be false",
    )
    require(
        runner_policy.get("exact_answer_goldens") is False,
        f"{cases_path}: runner_policy.exact_answer_goldens must be false",
    )
    require(
        runner_policy.get("runner_outputs_are_derived") is True,
        f"{cases_path}: runner_policy.runner_outputs_are_derived must be true",
    )

    cases = index.get("cases")
    require(isinstance(cases, list) and cases, f"{cases_path}: cases must be a non-empty list")
    return cases


def validate_case(case: dict, eval_root: Path, seen_ids: set[str]) -> tuple[Path, str]:
    require(isinstance(case, dict), "case entry must be an object")
    missing = sorted(REQUIRED_CASE_KEYS - set(case))
    require(not missing, f"{case.get('id', '<unknown>')}: missing keys: {', '.join(missing)}")

    case_id = case["id"]
    require(isinstance(case_id, str) and case_id, "case id must be a non-empty string")
    require(
        CASE_ID_PATTERN.fullmatch(case_id) is not None,
        f"{case_id}: case id must use lowercase letters, digits, and hyphens only",
    )
    require(case_id not in seen_ids, f"{case_id}: duplicate case id")
    seen_ids.add(case_id)

    require(
        isinstance(case["target_type"], str) and case["target_type"],
        f"{case_id}: target_type must be a non-empty string",
    )

    for key in (
        "risk_area",
        "evidence_sources",
        "acceptance_criteria",
        "must_not_report",
        "required_concepts",
    ):
        require(
            isinstance(case[key], list) and all(isinstance(item, str) and item for item in case[key]),
            f"{case_id}: {key} must be a non-empty list of strings",
        )

    fixture_rel = case["fixture"]
    require(isinstance(fixture_rel, str) and fixture_rel, f"{case_id}: fixture must be a string")

    fixture_path = (eval_root / fixture_rel).resolve()
    require(fixture_path.is_file(), f"{case_id}: missing fixture: {fixture_path}")
    require(
        fixture_path.is_relative_to(eval_root.resolve()),
        f"{case_id}: fixture path escapes eval root: {fixture_rel}",
    )

    prompt = fixture_path.read_text(encoding="utf-8")
    for section in REQUIRED_PROMPT_SECTIONS:
        require(section in prompt, f"{case_id}: missing prompt section {section!r}")
    for section in EVALUATOR_ONLY_SECTIONS:
        require(
            section not in prompt,
            f"{case_id}: evaluator-only section must stay out of fixture: {section}",
        )

    return fixture_path, prompt


def write_workspace(cases_path: Path, out_dir: Path) -> dict:
    cases_path = cases_path.resolve()
    eval_root = cases_path.parent
    index = load_json(cases_path)
    cases = validate_index(index, cases_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_cases = []
    seen_ids: set[str] = set()

    for case in cases:
        _fixture_path, prompt = validate_case(case, eval_root, seen_ids)
        case_dir = out_dir / case["id"]
        case_dir.mkdir(parents=True, exist_ok=True)

        prompt_path = case_dir / "prompt.md"
        rubric_path = case_dir / "rubric.json"
        prompt_path.write_text(prompt, encoding="utf-8", newline="\n")

        rubric = {
            "id": case["id"],
            "target_type": case["target_type"],
            "risk_area": case["risk_area"],
            "evidence_sources": case["evidence_sources"],
            "acceptance_criteria": case["acceptance_criteria"],
            "must_not_report": case["must_not_report"],
            "required_concepts": case["required_concepts"],
        }
        rubric_path.write_text(
            json.dumps(rubric, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

        manifest_cases.append(
            {
                "id": case["id"],
                "target_type": case["target_type"],
                "prompt": str(prompt_path.relative_to(out_dir)).replace("\\", "/"),
                "rubric": str(rubric_path.relative_to(out_dir)).replace("\\", "/"),
            }
        )

    manifest = {
        "format": WORKSPACE_FORMAT,
        "source_format": FORMAT,
        "source_schema_version": index["schema_version"],
        "cases": manifest_cases,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare prompt-only and rubric-only files from eval cases."
    )
    parser.add_argument("--cases", type=Path, default=Path("evals/cases.json"))
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        manifest = write_workspace(args.cases, args.out)
    except EvalConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"prepared_cases": len(manifest["cases"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
