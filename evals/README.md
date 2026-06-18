# Unified Adversarial Review Evals

## Decision: add evals

Add repo-local evals for this skill.

The strongest evidence says this repository should include evals, but they
should live outside `skills/unified-adversarial-review/` so the installable Skill
stays lean. The current repository already has useful static tests, but those
tests only prove that important instruction text is present. They do not test
whether an agent using the skill actually distinguishes material findings from
refuted candidates, reports trusted evidence, respects scope, resists prompt
injection in target text, or marks limited coverage honestly.

## Local evidence

- `skills/unified-adversarial-review/SKILL.md` defines a high-variance agentic
  workflow: map scope, build a discovery map, keep a candidate ledger, refute
  candidates, and report coverage.
- `skills/unified-adversarial-review/references/methodology.md` makes behavioral
  promises that cannot be validated by text presence alone: role passes, target
  relation, refutation records, finalization gates, and prompt-injection
  handling.
- `tests/test_deep_default_workflow.py` is intentionally static. It checks for
  required phrases and sections, but it does not run representative review
  tasks or grade review outputs.
- `README.md` identifies this as a distribution-focused repository. Eval
  infrastructure should stay at the repository root, not installed with the Skill.

## Primary-source evidence

- OpenAI's Codex skill docs describe skills as reusable workflow packages and
  document progressive disclosure: Codex starts with metadata, then loads
  `SKILL.md`, then reads references or runs scripts only as needed. That supports
  keeping heavyweight eval artifacts outside the installable Skill:
  https://developers.openai.com/codex/skills
- OpenAI's skill-eval guide recommends measuring skill behavior with concrete
  prompts, captured runs, deterministic checks, and structured rubric output.
  It also recommends starting small and adding deeper checks only when they
  reduce risk: https://developers.openai.com/blog/eval-skills
- OpenAI's general evaluation guidance says generative AI is variable, traditional
  software tests are insufficient by themselves, evals should be task-specific,
  and "vibe-based evals" are an anti-pattern:
  https://developers.openai.com/api/docs/guides/evaluation-best-practices
- OpenAI's agent evaluation guide says to move to datasets and eval runs when
  repeatability is needed for benchmarking changes over time:
  https://developers.openai.com/api/docs/guides/agent-evals

## Best-fit approach

Use a staged eval suite:

1. Keep static contract tests in `tests/` for instruction structure and eval
   fixture integrity.
2. Keep behavioral eval inputs in `evals/cases/` as a small, curated dataset.
3. Grade outputs with `evals/review-output.schema.json` and `evals/rubric.md`.
4. Run model-assisted grading manually or in CI only when a runner is available;
   do not make hosted Evals API usage a hard dependency.

This is the best fit because it follows the official skill-eval pattern while
avoiding unnecessary dependencies. It also matches the risk profile of this
skill: the hardest regressions are not missing files, but false positives,
unsupported findings, weak refutation, scope drift, and dishonest coverage.

## How to use the eval cases

For each case in `evals/cases/`, run the current skill against the `prompt` and
`target.content`. Then ask a read-only grader to emit JSON conforming to
`evals/review-output.schema.json` and score it with `evals/rubric.md`.

Example manual command shape:

```bash
codex exec \
  '$unified-adversarial-review Review eval case <case-id> using the supplied target.' \
  --output-schema ./evals/review-output.schema.json
```

Do not treat these fixtures as full proof of safety. They are regression probes
for the behaviors this skill most needs to keep getting right.
