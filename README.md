# Unified Adversarial Review

A portable, read-only Agent Skill for adversarially reviewing code changes,
implementation plans, and pre-ship decisions. It adapts the core stance of
OpenAI's Apache-2.0 `codex-plugin-cc` adversarial-review prompt while removing
Claude Code as a runtime dependency.

The canonical workflow runs in one capable agent. Subagents are optional and
may improve exploration or validation for large and high-risk reviews, but they
are never required for a complete review.

## What it optimizes for

- finding material, release-relevant failures;
- rejecting weak or refuted candidates before reporting them;
- grounding findings in a concrete causal path and evidence;
- preserving explicit scope and coverage limits;
- staying read-only and protecting sensitive repository data.

## Install

### Codex user skill

Copy or symlink the runtime directory:

```text
unified-adversarial-review/
```

into:

```text
$HOME/.agents/skills/unified-adversarial-review/
```

Then invoke it explicitly:

```text
$unified-adversarial-review review the current branch against main
```

For a repository-scoped install, place the same directory under:

```text
<repo>/.agents/skills/unified-adversarial-review/
```

Other Agent Skills clients can install the same runtime directory according to
their own skill-location rules.

## Runtime package

```text
unified-adversarial-review/
├── SKILL.md
├── agents/openai.yaml          # optional Codex UX/invocation metadata
├── references/
│   ├── methodology.md
│   ├── finding-calibration.md
│   └── lenses.md
├── LICENSE
├── NOTICE
└── UPSTREAM.md
```

The default output is findings-first Markdown. The root-level schemas,
validator, and tests are optional quality tooling and are not runtime
dependencies of the Skill.

## Development and validation

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

The optional machine-output validator is:

```bash
python scripts/validate_review_output.py path/to/review-output.json
```

## Repository layout

- `unified-adversarial-review/`: installable runtime Skill.
- `schemas/`, `scripts/`, `tests/`: optional machine-output quality tooling.
- `docs/DECISIONS.md`: current normative design decisions.
- `docs/EVALS.md`: comparison and regression-evaluation plan.
- `docs/RESEARCH.md`: source analysis and rationale.
- `docs/HISTORY.md`: superseded decisions and review history.
- `docs/reviews/`: archived verbatim design-review snapshots.
- `UPSTREAM.md`: pinned upstream provenance.

## License and provenance

Apache-2.0. See `LICENSE`, `NOTICE`, and `UPSTREAM.md`. This is a separate
adaptation and is not an OpenAI product or endorsement.
