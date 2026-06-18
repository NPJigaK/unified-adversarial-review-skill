# Historical Investigation Notes

Date recorded: 2026-06-18

This file preserves superseded assumptions, withdrawn findings, and prior
review results so they do not remain mixed with the current normative design.

Current normative decisions live in [DECISIONS.md](DECISIONS.md).
Detailed source analysis lives in [RESEARCH.md](RESEARCH.md).
Upstream provenance lives in [UPSTREAM.md](../UPSTREAM.md).
The latest design review is preserved in
[DESIGN_REVIEW_2026-06-18.md](reviews/DESIGN_REVIEW_2026-06-18.md).
The second design review is preserved in
[DESIGN_REVIEW_2026-06-18_ROUND2.md](reviews/DESIGN_REVIEW_2026-06-18_ROUND2.md).
The third design review is preserved in
[DESIGN_REVIEW_2026-06-18_ROUND3.md](reviews/DESIGN_REVIEW_2026-06-18_ROUND3.md).

## Initial Read-Only Review Result

An earlier read-only adversarial review used two temporary local agents:

- `pr_explorer`
- `adversarial_reviewer`

That review returned `needs_attention`.

Its high-level conclusion was:

- The direction that "Unified" means unifying review process, evidence bar,
  finding bar, and ship/no-ship judgment rather than merging every checklist was
  sound.
- Codex Skill progressive disclosure, `allow_implicit_invocation: false`,
  subagent token cost, and Codex Security staged workflow were consistent with
  official docs.
- The then-current research should not be converted directly into a Skill.

## Preserved Finding: Read-Only Boundary

Finding metadata:

- severity: medium
- blocking: true
- confidence: 0.82
- affected: first pasted research attachment, lines 471-482

Reason:

- The earlier research included a validation phase that could create a
  reproduction test if needed.
- The same research said review mode is read-only.
- Review mode writing tests or fixtures into the repository violates the
  read-only review boundary.

Recommended correction:

- In review mode, verification should be limited to read-only inspection, safe
  execution of existing tests or checks when authorized, code tracing, official
  documentation checks, scratch/temp external reproduction only when explicitly
  safe, and written verification recommendations.
- Writing tests into the repo belongs to a separate remediation or
  implementation task.

Status: still valid.

Current decision:

- Review mode must not edit repository files, add tests, add fixtures, apply
  patches, or commit changes.
- Running existing commands is an execution-safety question, not automatically
  safe merely because repository files are not patched.

## Withdrawn Finding: Local 2-Subagent Contract Regression

Finding metadata:

- severity: medium
- blocking: true
- confidence: 0.79
- affected: first pasted research attachment, lines 522-589

Original reason:

- The first research text said low-risk changes could default to no subagents.
- A temporary local `adversarial-review` skill required
  `pr_explorer -> adversarial_reviewer`.
- The review treated that local skill as a contract and called the
  optional-subagent design a regression.

User correction:

- The local skill was provisional and should not be treated as authoritative.

Status: withdrawn as a blocker.

Current decision:

- The base is OpenAI's `codex-plugin-cc` adversarial-review prompt and
  surrounding mechanism.
- Single-agent sequential execution is canonical for v1.
- Subagents are optional optimization or host-specific orchestration, not a
  semantic requirement.

## Preserved Finding: `hypothesized` Evidence In Final Findings

Finding metadata:

- severity: medium
- blocking: true
- confidence: 0.76
- affected: first pasted research attachment, lines 671-704

Reason:

- The earlier research said only validated/reachable counterexamples become
  findings.
- Its proposed output contract allowed
  `findings[].evidence_level = hypothesized`.
- That allowed unverified hypotheses to appear as final findings, confusing
  findings with residual uncertainty.

Recommended correction:

- Final findings should require traced evidence.
- `hypothesized` belongs in candidate state or residual uncertainty, not final
  findings.
- Schema validation should reject final findings with only hypothesized
  evidence.

Status: still valid in principle.

Current decision:

- v1 avoids an evidence-level enum in the canonical contract.
- Final findings must include evidence references, causal scenario,
  assumptions, verification performed, proof gaps, confidence, and
  recommendation.
- Candidates that do not survive verification become either `unresolved`
  uncertainty or are discarded; they do not become findings.

## Superseded Direction: Fully Independent Methodology

For one intermediate step, the design moved toward an independent
IV&V/FMEA/threat-modeling methodology and away from the OpenAI adversarial
review prompt.

Status: superseded.

Reason:

- The user clarified that "original OpenAI version" means
  `openai/codex-plugin-cc/plugins/codex/prompts/adversarial-review.md`.
- The final design should inherit the OpenAI adversarial review method and
  remove only the Claude Code runtime dependency.

Superseded direction:

- do not use OpenAI adversarial-review as the method parent;
- use Codex Skill specs only as execution format;
- use an independent
  `Frame/Scope -> Model -> Challenge -> Trace/Verify -> Adjudicate -> Decide/Report`
  method;
- make subagents optional for high-risk or large changes.

Current position:

- Preserve the OpenAI adversarial stance, no-ship focus, high-cost failure
  prioritization, material-finding-only calibration, grounded findings, compact
  output, read-only review mode, user-focus weighting, and large-diff
  self-collection lessons.
- Extend the method with explicit modeling, lens routing, candidate
  verification, unresolved uncertainty, coverage limits, confidentiality
  boundaries, scope components, and evals.

## Corrected Claim: App-Server Review Customization

An earlier note said the built-in app-server review path could not be
customized.

Status: narrowed.

Current decision:

- The upstream plugin uses `turn/start` with a custom prompt and `outputSchema`;
  that is an implementation fact.
- Current Codex app-server docs list `review/start` with a `custom` free-form
  target, so "cannot customize" is too broad.
- Future adapters should decide based on current app-server behavior rather than
  assuming the old wrapper path is the only possible integration.

## Local Investigation Artifacts

The investigation read local pasted attachments, the provisional local
`adversarial-review` skill, provisional local `pr_explorer` and
`adversarial_reviewer` agent configs, and a temporary clone of
`openai/codex-plugin-cc`.

Exact local absolute paths are intentionally omitted from repository
documentation because they are environment-specific and not normative.

## Second Design Review Result

The second design review returned `needs-attention` but confirmed that the
previous major issues were largely resolved.

Remaining implementation-contract risks it identified:

- the Draft 2020-12 schema could not be used directly as Codex/OpenAI
  Structured Outputs `outputSchema`;
- the current branch's configured upstream is not a safe default review base;
- schema-valid output could still be semantically invalid without deterministic
  validation;
- fail-closed coverage policy conflicted with `accepted limited` adapter
  language;
- evals needed separate method-only and end-to-end tracks;
- findings and uncertainties needed multiple scope component support;
- command evidence needed command/path redaction, not output redaction only.

Current decision:

- Keep separate semantic and OpenAI-compatible schemas.
- Require a semantic validator for machine mode, CI gates, and Codex adapters.
- Resolve branch bases from user/host/repository review base, then `origin/HEAD`
  and default integration branch candidates; do not default to same-name branch
  upstream.
- Keep coverage waivers outside the portable core.
- Split evals into method-only and end-to-end tracks.

## Third Design Review Result

The third design review returned `needs-attention` but judged the Round 2
issues mostly closed. It focused on validator and machine-mode execution
contract gaps.

Remaining implementation-contract risks it identified:

- installed skill layout put schemas under `assets/`, while the validator
  default searched `schemas/`;
- a no-op review could still return `no-material-findings + sufficient`;
- base, scope, and capability fields could contradict each other;
- confidentiality checks scanned too little output and rejected redacted
  placeholders;
- digests were self-reported strings without provenance;
- semantic and OpenAI schemas could drift;
- eval lens metrics could not be computed cleanly without explicit finding lens
  fields;
- validator dependency on `jsonschema` needed a portability contract.

Current decision:

- Default validator schema discovery prefers installed `assets/` and falls back
  to repository `schemas/`.
- Add `component_coverage`, stronger coverage checks, base/scope/capability
  cross-field validation, command provenance, digest source, broader secret/path
  lint, and validator regression tests.
- Treat validator secret detection as heuristic only; host adapters should
  redact tool output before it reaches the model.
- Record Python and `jsonschema` requirements for machine validation.

## Quality Objective Correction: Focused, Not Small

After Round 3, the priority was corrected again. The objective is not to make a
small Skill. The objective is to make the best focused adversarial-review Skill:
one that a single capable agent can run completely, while finding more material
release-relevant failures and producing fewer unsupported or immaterial
findings.

Schema, validator, App Server adapters, CI gates, optional subagents, and
benchmark infrastructure are not deleted from the design merely because they are
complex. They remain when they improve review quality, machine reliability, or
measurement. They are separated from the core only when making them mandatory
would add dependency or ceremony without improving the review.

Current decision:

- v1 core is `SKILL.md` plus `references/methodology.md`,
  `references/finding-calibration.md`, and `references/lenses.md`.
- v1 must preserve OpenAI adversarial stance, material finding bar, read-only
  investigation, minimal modeling, conditional lens routing, candidate
  refutation, supported/unresolved/refuted separation, delta evidence, coverage
  limits, prompt-injection resistance, and sensitive-data caution.
- Machine tooling, optional orchestration, and evals remain in the repository
  as quality infrastructure, but the core review method must stay semantically
  complete with one agent and Markdown output.
