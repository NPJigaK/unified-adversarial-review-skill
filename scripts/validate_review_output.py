#!/usr/bin/env python3
"""Validate unified-adversarial-review machine output.

This validator is intentionally stricter than JSON Schema alone. It enforces
cross-field invariants that the OpenAI Structured Outputs subset cannot express.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


GIT_OID_RE = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ABS_PATH_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|/)")
URI_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
REDACTION_PLACEHOLDER_RE = re.compile(
    r"(?i)(\[redacted(?:_[a-z]+)?\]|<redacted>|\*{3,}|REDACTED)"
)
SECRET_RE = re.compile(
    r"(?i)("
    r"authorization:\s*(?:bearer|basic)\s+(?!\[?redacted\]?|<redacted>|\*{3,})\S+|"
    r"--token(?:=|\s+)(?!\[?redacted\]?|<redacted>|\*{3,})\S+|"
    r"(?:api[_-]?key|password|client_secret|secret|database_url)"
    r"(?:=|\s+)(?!\[?redacted\]?|<redacted>|\*{3,})\S+|"
    r"AWS_SECRET_ACCESS_KEY\s*=\s*(?!\[?redacted\]?|<redacted>|\*{3,})\S+|"
    r"AKIA[0-9A-Z]{16}|"
    r"gh[pousr]_[A-Za-z0-9_]{20,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r")"
)
PATH_KEYS = {"path", "paths", "supporting_paths"}
REMOTE_BASE_METHODS = {
    "host-review-base",
    "repository-review-base",
    "origin-head",
    "default-candidate",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def default_schema_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    candidates = [
        root / "assets" / "review-output.semantic.schema.json",
        root / "schemas" / "review-output.semantic.schema.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def jsonschema_validate(instance: Any, schema_path: Path, errors: list[str]) -> None:
    try:
        import jsonschema
    except ImportError:
        errors.append("jsonschema package is required for schema validation")
        return

    try:
        schema = load_json(schema_path)
    except FileNotFoundError:
        errors.append(f"semantic schema not found: {schema_path}")
        return
    except PermissionError:
        errors.append(f"semantic schema is not readable: {schema_path}")
        return
    except json.JSONDecodeError as exc:
        errors.append(f"semantic schema is invalid JSON: {exc}")
        return
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
    except jsonschema.SchemaError as exc:
        errors.append(f"semantic schema is invalid: {exc.message}")
        return

    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
        loc = ".".join(str(p) for p in err.path) or "<root>"
        errors.append(f"schema:{loc}: {err.message}")


def require_unique(values: list[str], label: str, errors: list[str]) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            errors.append(f"{label}: duplicate id {value!r}")
        seen.add(value)


def require_unique_items(values: list[Any], label: str, errors: list[str]) -> None:
    seen: set[Any] = set()
    for value in values:
        if value in seen:
            errors.append(f"{label}: duplicate value {value!r}")
        seen.add(value)


def get_locations(finding: dict[str, Any]) -> list[dict[str, Any]]:
    return [loc for loc in finding.get("locations", []) if isinstance(loc, dict)]


def check_scope_refs(
    label: str,
    refs: list[str],
    included_components: set[str],
    all_components: set[str],
    errors: list[str],
    require_included: bool,
) -> None:
    if not refs:
        errors.append(f"{label}: must reference at least one scope component")
        return
    for ref in refs:
        if ref not in all_components:
            errors.append(f"{label}: unknown scope component {ref!r}")
        elif require_included and ref not in included_components:
            errors.append(f"{label}: scope component {ref!r} is not included")


def check_path(path: str | None, label: str, errors: list[str]) -> None:
    if not path:
        return
    if path == "[REDACTED_PATH]":
        return
    normalized = path.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part not in {"", "."}]
    if (
        ABS_PATH_RE.search(path)
        or normalized.startswith("//")
        or normalized.startswith("~")
        or URI_RE.search(path)
        or ".." in parts
    ):
        errors.append(
            f"{label}: path must be repository-relative and must not escape the repository"
        )


def check_secret_text(value: str, label: str, errors: list[str]) -> None:
    # Heuristic lint only. Hosts must still redact tool output before it reaches the model.
    if SECRET_RE.search(value):
        errors.append(f"{label}: appears to contain an unredacted secret")


def scan_strings_and_paths(value: Any, label: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_label = f"{label}.{key}"
            if key in PATH_KEYS:
                if isinstance(child, list):
                    for idx, item in enumerate(child):
                        if isinstance(item, str):
                            check_path(item, f"{child_label}[{idx}]", errors)
                elif isinstance(child, str):
                    check_path(child, child_label, errors)
            scan_strings_and_paths(child, child_label, errors)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            scan_strings_and_paths(item, f"{label}[{idx}]", errors)
    elif isinstance(value, str):
        check_secret_text(value, label, errors)


def semantic_checks(doc: dict[str, Any], errors: list[str]) -> None:
    findings = doc.get("findings", [])
    uncertainties = doc.get("uncertainties", [])
    coverage = doc.get("coverage", {})
    scope = doc.get("scope", {})
    base = scope.get("base", {})
    components = scope.get("components", [])
    capability_modes = set(scope.get("capability_modes", []))

    if doc.get("finding_assessment") == "material-findings" and not findings:
        errors.append("finding_assessment=material-findings requires findings")
    if doc.get("finding_assessment") == "no-material-findings" and findings:
        errors.append("finding_assessment=no-material-findings forbids findings")

    component_ids = [
        c.get("id") for c in components if isinstance(c, dict) and c.get("id")
    ]
    require_unique(component_ids, "scope.components", errors)
    all_components = set(component_ids)
    included_components = {
        c.get("id")
        for c in components
        if isinstance(c, dict) and c.get("status") == "included" and c.get("id")
    }
    included_branch_components = {
        c.get("id")
        for c in components
        if isinstance(c, dict)
        and c.get("status") == "included"
        and c.get("kind") == "branch-diff"
        and c.get("id")
    }

    for component in components:
        if not isinstance(component, dict):
            continue
        cid = component.get("id", "<unknown>")
        if component.get("status") == "unavailable" and not component.get("reason"):
            errors.append(f"scope component {cid}: unavailable components require a reason")

    branch_available = base.get("branch_component_available")
    if included_branch_components:
        if branch_available is not True:
            errors.append("included branch-diff requires branch_component_available=true")
        if "git-aware" not in capability_modes:
            errors.append("included branch-diff requires git-aware capability mode")
    if base.get("branch_component_available") is True:
        if not included_branch_components:
            errors.append("branch_component_available=true requires an included branch-diff component")
        for key in ("base_ref", "base_commit_oid", "merge_base_oid"):
            if not base.get(key):
                errors.append(f"scope.base.{key}: required when branch component is available")
        if base.get("base_resolution_method") in {"unavailable", "not-applicable"}:
            errors.append("scope.base.base_resolution_method: invalid for available branch component")
    if base.get("branch_component_available") is False:
        if included_branch_components:
            errors.append("branch_component_available=false forbids included branch-diff components")
        for key in ("base_ref", "base_commit_oid", "merge_base_oid"):
            if base.get(key):
                errors.append(f"scope.base.{key}: must be null when branch component is unavailable")
        if base.get("base_resolution_method") not in {"unavailable", "not-applicable"}:
            errors.append(
                "scope.base.base_resolution_method must be unavailable or not-applicable "
                "when branch component is unavailable"
            )
    for key in ("base_commit_oid", "merge_base_oid"):
        value = base.get(key)
        if value and not GIT_OID_RE.fullmatch(value):
            errors.append(f"scope.base.{key}: must be 40- or 64-hex Git object id")
    if (
        base.get("base_resolution_method") in REMOTE_BASE_METHODS
        and base.get("remote_freshness") in {"local-only", "unknown"}
    ):
        has_stale_remote_limitation = any(
            isinstance(item, dict) and item.get("kind") == "stale-remote"
            for item in coverage.get("limitations", [])
        )
        if not has_stale_remote_limitation:
            errors.append("stale remote-derived base requires a stale-remote coverage limitation")
        if doc.get("coverage_status") == "sufficient":
            errors.append("coverage_status=sufficient forbids stale remote-derived base")

    if doc.get("coverage_status") == "sufficient":
        if uncertainties:
            errors.append("coverage_status=sufficient forbids unresolved uncertainties")
        if coverage.get("limitations"):
            errors.append("coverage_status=sufficient forbids coverage limitations")
        for component in components:
            if isinstance(component, dict) and component.get("status") == "unavailable":
                errors.append("coverage_status=sufficient forbids unavailable scope components")
    if not coverage.get("checks_performed"):
        errors.append("coverage.checks_performed must be non-empty")

    considered_list = coverage.get("lenses_considered", [])
    applied_list = coverage.get("lenses_applied", [])
    skipped_list = [
        item.get("lens")
        for item in coverage.get("lenses_skipped_with_reason", [])
        if isinstance(item, dict)
    ]
    require_unique_items(considered_list, "coverage.lenses_considered", errors)
    require_unique_items(applied_list, "coverage.lenses_applied", errors)
    require_unique_items(skipped_list, "coverage.lenses_skipped_with_reason", errors)
    considered = set(considered_list)
    applied = set(applied_list)
    skipped = set(skipped_list)
    if not applied.issubset(considered):
        errors.append("coverage.lenses_applied must be a subset of lenses_considered")
    if not skipped.issubset(considered):
        errors.append("coverage.lenses_skipped_with_reason must be a subset of lenses_considered")
    if considered != applied | skipped:
        errors.append("coverage.lenses_considered must equal applied lenses plus skipped lenses")
    overlap = applied & skipped
    if overlap:
        errors.append(f"coverage lenses cannot be both applied and skipped: {sorted(overlap)}")

    component_coverage = coverage.get("component_coverage", [])
    coverage_by_component: dict[str, list[dict[str, Any]]] = {}
    for idx, item in enumerate(component_coverage, start=1):
        if not isinstance(item, dict):
            continue
        refs = item.get("scope_components", [])
        check_scope_refs(
            f"component coverage {idx}",
            refs,
            included_components,
            all_components,
            errors,
            require_included=False,
        )
        if item.get("status") in {"skipped", "unavailable"} and not item.get("reason"):
            errors.append(f"component coverage {idx}: skipped/unavailable status requires a reason")
        if item.get("status") == "evaluated" and not item.get("checks_performed"):
            errors.append(f"component coverage {idx}: evaluated status requires checks_performed")
        for ref in refs:
            coverage_by_component.setdefault(ref, []).append(item)

    for component_id in included_components:
        evaluated = [
            item
            for item in coverage_by_component.get(component_id, [])
            if item.get("status") == "evaluated" and item.get("checks_performed")
        ]
        if not evaluated:
            errors.append(f"scope component {component_id!r}: missing evaluated component coverage")

    limitation_ids = [
        item.get("id")
        for item in coverage.get("limitations", [])
        if isinstance(item, dict) and item.get("id")
    ]
    require_unique(limitation_ids, "coverage.limitations", errors)

    require_unique(
        [f.get("id") for f in findings if isinstance(f, dict) and f.get("id")],
        "findings",
        errors,
    )

    for f in findings:
        if not isinstance(f, dict):
            continue
        fid = f.get("id", "<unknown>")
        check_scope_refs(
            f"finding {fid}",
            f.get("scope_components", []),
            included_components,
            all_components,
            errors,
            require_included=True,
        )
        risk_domains = f.get("risk_domains", [])
        require_unique_items(risk_domains, f"finding {fid}.risk_domains", errors)
        primary_lens = f.get("primary_lens")
        if primary_lens and primary_lens not in risk_domains:
            errors.append(f"finding {fid}: primary_lens must be included in risk_domains")
        if primary_lens and primary_lens not in applied:
            errors.append(f"finding {fid}: primary_lens must be listed in coverage.lenses_applied")

        locations = get_locations(f)
        location_ids = [loc.get("id") for loc in locations if loc.get("id")]
        require_unique(location_ids, f"finding {fid}.locations", errors)
        location_id_set = set(location_ids)

        for loc in locations:
            lid = loc.get("id", "<unknown>")
            if loc.get("kind") in {"source", "config", "test", "contract"}:
                check_path(loc.get("path"), f"finding {fid}.location {lid}", errors)
                start = loc.get("line_start")
                end = loc.get("line_end")
                if isinstance(start, int) and isinstance(end, int) and end < start:
                    errors.append(f"finding {fid}.location {lid}: line_end < line_start")
            if loc.get("kind") == "command":
                display_command = loc.get("display_command", "")
                check_secret_text(display_command, f"finding {fid}.location {lid}.display_command", errors)
                if loc.get("command_origin") == "reviewer-executed" and "safe-exec" not in capability_modes:
                    errors.append(
                        f"finding {fid}.location {lid}: reviewer-executed command requires safe-exec capability"
                    )
                digest_source = loc.get("digest_source")
                command_digest = loc.get("command_digest")
                output_digest = loc.get("output_digest")
                if digest_source in {"host-computed", "agent-reported"}:
                    if not isinstance(command_digest, str) or not SHA256_RE.fullmatch(command_digest):
                        errors.append(f"finding {fid}.location {lid}: command_digest must be 64 hex")
                    if not isinstance(output_digest, str) or not SHA256_RE.fullmatch(output_digest):
                        errors.append(f"finding {fid}.location {lid}: output_digest must be 64 hex")
                if digest_source == "not-available" and (command_digest or output_digest):
                    errors.append(f"finding {fid}.location {lid}: unavailable digests must be null")
                if loc.get("redaction_applied") is True:
                    combined = " ".join(
                        str(loc.get(key) or "")
                        for key in ("display_command", "relevant_excerpt", "redaction_note")
                    )
                    if not REDACTION_PLACEHOLDER_RE.search(combined):
                        errors.append(
                            f"finding {fid}.location {lid}: redaction_applied requires a placeholder or note"
                        )

        for item in f.get("delta_evidence", []) + f.get("evidence", []):
            if not isinstance(item, dict):
                continue
            ref = item.get("location_ref")
            if ref is not None and ref not in location_id_set:
                errors.append(f"finding {fid}: dangling location_ref {ref!r}")

        verification = f.get("verification", {})
        if not verification.get("checks_performed"):
            errors.append(f"finding {fid}: verification.checks_performed must be non-empty")
        if not verification.get("refutations_checked"):
            errors.append(f"finding {fid}: verification.refutations_checked must be non-empty")

    for idx, uncertainty in enumerate(uncertainties, start=1):
        if not isinstance(uncertainty, dict):
            continue
        check_scope_refs(
            f"uncertainty {idx}",
            uncertainty.get("scope_components", []),
            included_components,
            all_components,
            errors,
            require_included=True,
        )

    for idx, limitation in enumerate(coverage.get("limitations", []), start=1):
        if not isinstance(limitation, dict):
            continue
        check_scope_refs(
            f"coverage limitation {idx}",
            limitation.get("scope_components", []),
            included_components,
            all_components,
            errors,
            require_included=False,
        )

    for idx, artifact in enumerate(coverage.get("sensitive_artifacts", []), start=1):
        if isinstance(artifact, dict):
            check_path(artifact.get("path"), f"sensitive artifact {idx}", errors)

    for idx, step in enumerate(doc.get("next_steps", []), start=1):
        if not isinstance(step, dict):
            continue
        check_scope_refs(
            f"next step {idx}",
            step.get("scope_components", []),
            included_components,
            all_components,
            errors,
            require_included=False,
        )

    for component in components:
        if not isinstance(component, dict):
            continue
        cid = component.get("id")
        if component.get("status") == "unavailable":
            has_limitation = any(
                isinstance(item, dict) and cid in item.get("scope_components", [])
                for item in coverage.get("limitations", [])
            )
            if not has_limitation:
                errors.append(f"scope component {cid!r}: unavailable component requires a coverage limitation")

    scan_strings_and_paths(doc, "$", errors)


def validate_document(instance: Any, schema_path: Path | None = None) -> tuple[list[str], bool]:
    """Validate an already-parsed review document.

    Returns ``(errors, usage_error)``. ``usage_error`` is true when validation
    could not run because the schema or ``jsonschema`` dependency was missing or
    invalid; callers should map that condition to CLI exit code 2.
    """
    errors: list[str] = []
    resolved_schema = schema_path or default_schema_path()
    jsonschema_validate(instance, resolved_schema, errors)
    usage_error = any(
        err.startswith(("semantic schema", "jsonschema package"))
        for err in errors
    )
    if not usage_error:
        if isinstance(instance, dict):
            semantic_checks(instance, errors)
        else:
            errors.append("root document must be an object")
    return errors, usage_error


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, help="Review output JSON to validate")
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Semantic JSON Schema path",
    )
    args = parser.parse_args()
    schema_path = args.schema or default_schema_path()

    try:
        doc = load_json(args.output)
    except Exception as exc:  # noqa: BLE001 - command-line validator should report parse failures.
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 2

    errors, usage_error = validate_document(doc, schema_path)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 2 if usage_error else 1

    print("review output valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
