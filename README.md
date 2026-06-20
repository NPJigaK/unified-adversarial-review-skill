# Unified Adversarial Review Agent Skill

[![Latest release](https://img.shields.io/github/v/release/NPJigaK/unified-adversarial-review-skill?label=release)](https://github.com/NPJigaK/unified-adversarial-review-skill/releases/latest)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](skills/unified-adversarial-review/LICENSE)

A portable, read-only Agent Skill for adversarially reviewing code changes,
implementation plans, and pre-ship decisions.

This repository ships one installable Skill:

```text
skills/unified-adversarial-review/
```

## Quick Start

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review \
  --agent codex
```

```text
$unified-adversarial-review Review the current branch against main.
```

Works with Codex, Claude Code, Cursor, and other Agent Skills clients.

## Why This Skill Exists

### #1: Agent reviews stop too early

The problem: ordinary agent review often skims the diff, finds one plausible
issue, or accepts the happy path when nothing obvious breaks.

The fix: deep review is the default. The Skill requires scope mapping,
risk-lens routing, candidate tracking, refutation, and coverage justification
before reporting.

### #2: Noisy findings hide the real blocker

The problem: style issues, cleanup suggestions, and speculative concerns make a
review look busy while weakening the ship/no-ship signal.

The fix: final findings must be material, grounded, causally tied to the target,
actionable, and not refuted by an existing guard or guarantee.

### #3: "No findings" is easy to overread

The problem: a clean review can be mistaken for proof that a change is safe.

The fix: finding assessment and coverage status are separate. A report can say
there are no supported material findings while still naming coverage gaps and
unresolved material uncertainty.

## Usage

```text
$unified-adversarial-review Review the current branch against main.
Focus especially on rollback safety, data integrity, and retry behavior.
Do not modify repository files.
```

Plan/design review:

```text
$unified-adversarial-review Review this implementation plan before coding.
Look for missing controls, unsafe state transitions, migration hazards, and
operability gaps.
```

## What It Optimizes For

- material, release-relevant failures;
- rejection of weak or refuted candidates;
- concrete causal paths and evidence;
- deep default review with explicit role-pass and candidate/refutation records;
- separation of finding assessment from coverage completeness;
- read-only review and sensitive-data protection.

## How It Works

The Skill turns adversarial review into a falsification workflow rather than a
general checklist. A review follows this shape:

```text
Frame -> Inspect -> Discovery -> Model -> Challenge -> Trace -> Refute -> Adjudicate -> Report
```

In practice, that means the reviewer first defines the target, scope, available
capabilities, and coverage gaps. It then maps entry points, data flows, trust
boundaries, lifecycle transitions, and high-value assets before generating
failure candidates.

Every candidate must include realistic preconditions, a trigger, a reachable or
proposed path, the missing guard or unsafe transition, the violated invariant,
material impact, and the relation to the reviewed change or plan. Candidates
are then actively refuted against guards, contracts, tests, configuration,
rollout behavior, and platform guarantees before anything becomes a final
finding.

The final report separates:

- supported material findings;
- unresolved material uncertainty;
- discarded candidates, which are not reported as findings;
- reviewed scope and coverage limitations.

This structure is designed to make the output useful for ship/no-ship decisions
without padding the report with style issues, generic cleanup, or speculative
concerns.

## Design Rationale And Provenance

This repository combines a few established review ideas into a portable Agent
Skill. The method is intentionally grounded in quoted upstream guidance and in
the installable Skill contract, not just in a high-level summary.

This is not an OpenAI or Microsoft product, endorsement, certification, or
official security process.

### OpenAI Codex Influence

The starting point is OpenAI's Apache-2.0
[`codex-plugin-cc`](https://github.com/openai/codex-plugin-cc) adversarial
review prompt:

> "break confidence in the change, not to validate it"

> "Report only material findings."

Source:
[`plugins/codex/prompts/adversarial-review.md`](https://github.com/openai/codex-plugin-cc/blob/807e03ac9d5aa23bc395fdec8c3767500a86b3cf/plugins/codex/prompts/adversarial-review.md)
at pinned commit `807e03ac9d5aa23bc395fdec8c3767500a86b3cf`.

This Skill adapts that stance and material-finding bar while removing the
Claude Code plugin runtime dependency. The upstream prompt pin, SHA-256, Git
blob hash, and adaptation boundary are recorded in
[skills/unified-adversarial-review/UPSTREAM.md](skills/unified-adversarial-review/UPSTREAM.md).

In this Skill, that becomes a read-only review contract: falsify confidence,
trace concrete failure paths, refute candidates before reporting, and omit
style, naming, cleanup, and unsupported speculation.

### Microsoft SDL And Threat Modeling Influence

The methodology also borrows from public Microsoft Security Development
Lifecycle and threat modeling guidance:

> "starts with clearly defined security and privacy requirements"

> "review all threat models for accuracy and completeness"

Source:
[Microsoft Security Development Lifecycle](https://learn.microsoft.com/en-us/compliance/assurance/assurance-microsoft-security-development-lifecycle).

Microsoft's threat modeling guidance also lists:

> "Validating that threats have been mitigated."

Source:
[Microsoft Threat Modeling](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling).

The
[Threat Modeling Tool overview](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool)
is another useful public reference for modeling components, data flows, and
security boundaries.

### Skill-Specific Adaptation

This repository narrows those sources for agentic code and plan review:

| Source idea | Skill implementation |
| --- | --- |
| Challenge the change rather than validate intent | read-only falsification workflow |
| Identify concrete threats before judging safety | discovery map before candidate generation |
| Validate mitigations | candidate ledger and refutation records |
| Review completeness before release | separate coverage status and finalization gates |
| Agent inputs can be hostile or misleading | repository text and command output are treated as untrusted evidence |

That adaptation is implemented in the Skill files themselves:

- [SKILL.md](skills/unified-adversarial-review/SKILL.md) defines the top-level
  contract, non-negotiables, and report shape;
- [methodology.md](skills/unified-adversarial-review/references/methodology.md)
  defines the full workflow, scope rules, role-pass protocol, candidate ledger,
  refutation pass, and finalization gates;
- [finding-calibration.md](skills/unified-adversarial-review/references/finding-calibration.md)
  defines materiality, severity, confidence, uncertainty, and coverage
  calibration;
- [lenses.md](skills/unified-adversarial-review/references/lenses.md) defines
  conditional risk lenses without turning the review into broad checklist
  theater.

## Install Options

The Skill content is the same across clients; only install location and
invocation syntax vary. Detailed paths, user/global installs, and `npx skills
use` examples are in [INSTALL.md](INSTALL.md).

### Codex

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review \
  --agent codex
```

```text
$unified-adversarial-review Review the current branch against main.
```

### Claude Code

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review \
  --agent claude-code
```

```text
/unified-adversarial-review Review the current branch against main.
```

### Cursor

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review \
  --agent cursor
```

```text
/unified-adversarial-review Review the current branch against main.
```

### Agent Skills CLI

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review
```

## Repository Layout

```text
README.md
INSTALL.md
skills/unified-adversarial-review/
```

This repository is intentionally distribution-focused. Design notes, schemas,
validators, and eval infrastructure are not bundled here because they are not
installed with the Skill.

## License And Provenance

Apache-2.0. See
[skills/unified-adversarial-review/LICENSE](skills/unified-adversarial-review/LICENSE),
[skills/unified-adversarial-review/NOTICE](skills/unified-adversarial-review/NOTICE),
and
[skills/unified-adversarial-review/UPSTREAM.md](skills/unified-adversarial-review/UPSTREAM.md).
This is a separate adaptation and is not an OpenAI product or endorsement.
License and provenance files are included inside the installable Skill
directory so the distributed artifact is self-contained.
