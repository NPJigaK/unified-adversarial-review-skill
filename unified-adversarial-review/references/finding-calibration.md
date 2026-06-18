# Finding calibration

Use this file to decide whether a candidate becomes a final finding and how to
qualify the review result.

## Materiality

A material finding is a concrete in-scope failure that can plausibly affect:

- security or authorization;
- user data or money;
- data correctness, migration safety, or durability;
- reliability, availability, rollback, or operations;
- compatibility with existing users, clients, schemas, or configs;
- bounded CPU, memory, disk, queues, rate limits, external calls, or cost;
- LLM/agent tool safety, memory, prompt injection, or data exposure.

Do not report:

- style, naming, formatting, or cosmetic concerns;
- broad maintainability preferences;
- missing tests without a concrete failure scenario;
- speculative concerns without a reachable or proposed path;
- generic security advice;
- unrelated pre-existing defects.

## Severity

Severity describes impact if the finding is real. Keep evidence strength in
confidence, not severity.

### Critical

Use for broad or severe impact such as:

- cross-tenant or privilege-boundary break;
- meaningful-scale credential, secret, or sensitive-data exposure;
- irreversible or broad data loss/corruption;
- high-value financial/billing corruption;
- failure likely to require incident response or emergency rollback.

### High

Use for material impact with meaningful blast radius, difficult recovery, poor
detectability, or serious user-visible security/data/reliability consequences.

### Medium

Use for bounded but still material impact with a narrower blast radius, clearer
recovery, or stronger containment. It must still be important enough to affect
a ship decision.

Do not emit `low` severity findings in adversarial-review output.

## Confidence

### High

The path or proposal is traced, realistic preconditions are established,
obvious refutations were checked, and concrete evidence supports the impact.

### Medium

The path is traced and material, with bounded assumptions or one non-critical
verification gap.

### Low

Do not emit a low-confidence final finding. Keep it internal or, only when the
risk is concrete and material, report it as unresolved uncertainty.

## Finding versus uncertainty

Report a finding only when supported.

Report unresolved uncertainty only when:

- the risk is concrete and material if true;
- the path is plausible and in scope;
- one specific missing fact blocks support or refutation;
- a concrete check can resolve it.

Do not list refuted candidates, generic worries, or low-value unknowns under
`Unresolved`.

## Required finding content

Every final finding includes:

- affected source/config/contract/test/plan anchor, or documented missing
  control;
- preconditions and trigger;
- reachable changed, proposed, or supporting path;
- missing guard or unsafe transition;
- violated invariant;
- material impact;
- checked refutations;
- how the target introduced, worsened, exposed, or proposes the risk;
- minimum concrete recommendation;
- confidence.

If these cannot be stated, the candidate is not ready as a finding.

## Finding assessment

Use:

- `material-findings` when at least one supported material finding exists;
- `no-material-findings` when none survives within the reviewed scope.

## Coverage status

Use:

- `sufficient`: release-relevant included scope was evaluated and no material
  unresolved uncertainty remains;
- `limited`: the assessment is usable, but explicit non-decisive gaps remain;
- `insufficient`: missing context or capability makes the finding/no-finding
  judgment unreliable.

A no-finding assessment with limited or insufficient coverage is not approval.
Always state reviewed scope, capability mode, and important gaps.
