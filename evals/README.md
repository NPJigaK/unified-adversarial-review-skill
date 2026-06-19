# Forward Eval Fixtures

These evals are maintainer-only checks for the unified adversarial review
workflow. They are not part of the installable Skill under
`skills/unified-adversarial-review`.

`evals/cases.json` is the canonical, portable case index. It records the schema
version, runner policy, evidence sources, risk area, acceptance criteria, and
negative assertions for each fixture. Runner-specific outputs should be
runner-derived artifacts, not edits to the canonical cases.

The fixtures contain raw review artifacts only. When running a case manually or
through a future runner, prompt the reviewer with the fixture content. Use the
case index `acceptance_criteria` and `must_not_report` fields as the evaluator
rubric.

Use `scripts/prepare_eval_workspace.py` to materialize separate `prompt.md` and
`rubric.json` files for each case. This prevents evaluator-only acceptance
criteria from leaking into the prompt sent to an agent.

The cases are not exact-answer goldens. A valid review may use different
wording, but it should preserve the material decisions described in
`evals/cases.json`.

There is intentionally no model or API runner here. The first layer is a small,
stable fixture corpus that can later be connected to any runner without changing
the installable Skill artifact.
