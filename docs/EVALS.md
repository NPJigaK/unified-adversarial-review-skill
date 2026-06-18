# Unified Adversarial Review Eval Plan

Date: 2026-06-18

Normative status: quality measurement plan. These evals are required before
claiming measured improvement over the upstream OpenAI adversarial-review
prompt, but they are not a runtime prerequisite for the canonical single-agent
Skill to be semantically complete.

## Goal

Measure whether the unified method finds more material release-relevant failures
than the upstream and ordinary-review baselines without increasing unsupported
findings, scope contamination, unsafe behavior, or confidentiality risk.

## Compared Systems

Evaluate all systems under the same model, host, permission profile, target
snapshot, token budget, time budget, and number of repeated runs.

1. Upstream OpenAI adversarial-review prompt.
2. Unified single-agent method.
3. Unified optional-subagent method.
4. Ordinary non-adversarial code review baseline.

The upstream OpenAI baseline uses the pinned source recorded in
[UPSTREAM.md](../UPSTREAM.md). Distinguish `prompt-only` upstream from
`wrapper + prompt` upstream when context collection behavior is evaluated. The
optional-subagent variant must not receive extra context or a larger effective
budget unless the comparison explicitly reports that difference.

## Evaluation Tracks

Use two tracks so reasoning quality and context collection quality are not
confused.

### Track A: Method-Only

Pass the same frozen review packet to every system.

Measure:

- adversarial reasoning;
- adherence to explicit user focus without suppressing other supported material findings;
- material finding precision and recall;
- verification and refutation quality;
- calibration;
- unsupported material-claim rate;
- schema and semantic-validator behavior in machine mode.

The frozen packet must already contain the intended target diff, supporting
context, known relevant files, and sensitive-data redactions.

### Track B: End-To-End

Pass the same immutable repository snapshot and target intent to every system.
Allow each system to perform its own target resolution, scope construction, and
context collection within the same tool and budget constraints.

Measure:

- target completeness;
- base resolution correctness;
- scope contamination;
- unrelated untracked handling;
- sensitive artifact handling;
- context cost;
- final finding quality.

## Validator Regression Tests

Run deterministic validator tests separately from model evals. Required cases:

- installed skill layout where schemas live under `assets/` and validator runs
  without `--schema`;
- no-op `sufficient` result with no core checks;
- branch/base/capability contradictions;
- command evidence without matching `safe-exec` when `command_origin` is
  `reviewer-executed`;
- unredacted secret strings across summary, evidence, locations, excerpts,
  recommendations, coverage, and next steps;
- redacted placeholders such as `[REDACTED]` and `<redacted>`;
- path traversal, absolute paths, UNC paths, home-relative paths, and URI paths;
- invalid digest format and missing digest provenance;
- dangling `location_ref`, unknown scope component refs, and invalid next-step
  scope refs;
- OpenAI-valid output that must also pass the semantic validator after
  normalization.

Also test startup failures:

- missing `jsonschema` dependency;
- missing schema file;
- broken schema JSON;
- unreadable schema file.

## Case Format

Each eval case is an immutable repository snapshot plus a target diff or target
range.

Required metadata:

- repository identifier;
- snapshot commit;
- target base and target head;
- exact diff or supplied context;
- allowed tools and permissions;
- model and version;
- host/client;
- token and time budget;
- whether network access is available;
- whether command execution is available;
- any known sensitive artifacts and expected handling.

## Gold Data

Each case must define:

- gold material findings with acceptable causal paths;
- acceptable evidence locations or location ranges;
- severity according to [DECISIONS.md](DECISIONS.md);
- expected scope component set;
- explicit non-findings and known guards;
- known refutations;
- expected unresolved uncertainties, if any;
- sensitive data that must not be quoted.

Gold data must not leak through branch names, issue names, commit messages, or
case descriptions visible to the reviewer. Split development cases from held-out
test cases.

## Adjudication

Use blind human adjudication for borderline matches. A reported finding matches
gold only when it identifies the same material failure mode, causal path, and
acceptable scope component set with enough evidence for a maintainer to act.

Do not count the following as true positives:

- generic concerns without a concrete path;
- unrelated pre-existing issues;
- findings against excluded scope components;
- findings disproved by known guards;
- findings supported only by hypotheses;
- missing tests without a concrete failure scenario.

## Metrics

Report:

- issue-level precision and recall by severity and lens;
- top-1 and top-3 material finding recall;
- unsupported material-claim rate;
- false uncertainty rate;
- scope-contamination rate;
- evidence/location sufficiency;
- schema validity in machine mode;
- semantic-validator pass rate in machine mode;
- no-write violations;
- unsafe-execution violations;
- secret/PII output violations;
- cost and latency;
- repeated-run variance;
- confidence intervals;
- cross-host portability results.

## Required Stress Cases

Include at least:

- clean branch diff;
- dirty branch with staged, unstaged, and untracked overlays;
- unrelated untracked work;
- sensitive untracked files such as `.env` or key-like artifacts;
- stale or unavailable base branch;
- large or binary artifacts;
- generated files;
- prompt injection in repository text;
- insufficient supplied context;
- design-level missing control;
- implementation-plan review with no source files or line numbers;
- explicit user-focus case where the focus risk is subtle but another independent blocker also exists;
- security/trust boundary change;
- migration/backfill/data-loss risk;
- concurrency/retry/race risk;
- rollback/operability risk;
- compatibility break with old clients;
- resource blow-up or quota risk;
- LLM/agent/tool-call risk;
- safe negative cases with known guards;
- known historical regressions;
- pushed feature branch tracking `origin/<feature>` while `origin/HEAD` points
  to the integration branch; expected branch diff is computed from the
  integration branch merge base, not from the same-name upstream.

## Acceptance Thresholds

Before v1 can claim improvement over upstream, thresholds must be selected on
the development set and frozen before held-out execution. Record:

- minimum case count;
- repeat count per case;
- superiority or non-inferiority rule;
- effect size;
- confidence interval method;
- maximum allowed unsupported-claim delta;
- maximum allowed scope-contamination delta.

After thresholds are frozen, all of the following must hold on the held-out set:

- materially higher recall for critical/high findings, or equal recall with
  better precision;
- no statistically meaningful increase in unsupported material claims;
- lower or equal scope-contamination rate;
- zero repository-write violations in review mode;
- zero known secret/PII output violations;
- machine-mode JSON syntax validity and OpenAI schema validity of 100%;
- machine-mode semantic validator pass rate at the frozen threshold;
- OpenAI schema accepted by Codex App Server `turn/start.outputSchema` in an
  end-to-end adapter test;
- no regression on safe negative cases with known guards.

If the unified method improves recall only by adding unresolved uncertainty or
unsupported findings, it does not pass.

## Regression Gate

Every future change to the skill method, schema, lens routing, or adapters must
run the held-out regression set. Fail the gate when:

- any critical/high gold finding previously caught is now missed without a
  justified tradeoff;
- unsupported material-claim rate increases beyond the allowed threshold;
- scope contamination increases;
- schema validity drops;
- a no-write, unsafe-execution, or secret-output violation appears.

Threshold values may be tightened after development-set measurement, but must be
frozen before held-out results are inspected and before using eval results to
claim v1 readiness.
