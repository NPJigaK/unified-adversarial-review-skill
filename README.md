# Unified Adversarial Review Agent Skill

[![Latest release](https://img.shields.io/github/v/release/NPJigaK/unified-adversarial-review-skill?label=release)](https://github.com/NPJigaK/unified-adversarial-review-skill/releases/latest)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](skills/unified-adversarial-review/LICENSE)

A portable, read-only Agent Skill for adversarially reviewing code changes,
implementation plans, and pre-ship decisions.

The installable Skill is:

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

It adapts the core stance of OpenAI's Apache-2.0 `codex-plugin-cc`
adversarial-review prompt while removing Claude Code as a runtime dependency.
Deep review is the default: the Skill requires scope mapping, risk-lens
routing, candidate tracking, refutation, and coverage justification before
reporting. The canonical workflow remains complete in one capable agent, while
multi-agent mapper/challenger/validator separation is preferred when the host
and active policy permit it.

## Install Options

### Codex

```text
Use $skill-installer to install the unified-adversarial-review skill from:

https://github.com/NPJigaK/unified-adversarial-review-skill/tree/main/skills/unified-adversarial-review

Install it for my user account. Inspect the skill contents before installing it,
and do not modify the source repository.
```

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review \
  --agent codex
```

Invoke with:

```text
$unified-adversarial-review Review the current branch against main.
```

### Claude Code

Copy `skills/unified-adversarial-review/` to:

```text
.claude/skills/unified-adversarial-review/
```

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review \
  --agent claude-code
```

Invoke with:

```text
/unified-adversarial-review Review the current branch against main.
```

### Cursor

Copy `skills/unified-adversarial-review/` to:

```text
.cursor/skills/unified-adversarial-review/
```

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review \
  --agent cursor
```

Invoke with:

```text
/unified-adversarial-review Review the current branch against main.
```

### Agent Skills CLI

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review
```

More install options are in [INSTALL.md](INSTALL.md).

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
- refuted or immaterial candidates, which are not reported as findings;
- reviewed scope and coverage limitations.

This structure is designed to make the output useful for ship/no-ship decisions
without padding the report with style issues, generic cleanup, or speculative
concerns.

## Design Rationale And Provenance

This repository combines a few established review ideas into a portable Agent
Skill. It is not an OpenAI or Microsoft product, endorsement, certification, or
official security process.

### OpenAI Codex Influence

The starting point is OpenAI's Apache-2.0
[`codex-plugin-cc`](https://github.com/openai/codex-plugin-cc) adversarial
review workflow. That plugin describes `/codex:adversarial-review` as a
read-only, steerable review that challenges implementation and design choices,
pressure-tests assumptions, and focuses on risk areas such as authorization,
data loss, rollback, race conditions, and reliability.

This Skill adapts that stance and material-finding bar while removing the
Claude Code plugin runtime dependency. The pinned upstream source, hash, and
adaptation boundary are recorded in
[skills/unified-adversarial-review/UPSTREAM.md](skills/unified-adversarial-review/UPSTREAM.md).

### Microsoft SDL And Threat Modeling Influence

The methodology also borrows from public Microsoft Security Development
Lifecycle and threat modeling guidance:

- define the review target and security-relevant requirements before judging
  implementation;
- model components, data flows, trust boundaries, and important state
  transitions;
- identify concrete threats or failure modes;
- verify whether mitigations, guards, and guarantees actually close the risk;
- review accuracy, completeness, and unacceptable residual risk before release.

Those ideas are reflected in the Skill's discovery map, risk-lens routing,
candidate ledger, refutation records, and explicit coverage status. Useful
public references include
[Microsoft SDL](https://learn.microsoft.com/en-us/compliance/assurance/assurance-microsoft-security-development-lifecycle),
[Microsoft Threat Modeling](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling),
and the
[Threat Modeling Tool overview](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool).

### Skill-Specific Adaptation

This Skill narrows the method for agentic code and plan review:

- mapper, challenger, and validator role passes keep scope discovery,
  candidate generation, and refutation distinct;
- risk lenses are selected only when triggered by the target, avoiding broad
  checklist theater;
- a candidate ledger prevents weak, duplicate, unrelated, or refuted concerns
  from leaking into the final report;
- coverage status is separate from finding assessment, so "no material
  findings" is never presented as proof of safety;
- repository text and command output are treated as untrusted evidence, which
  reduces prompt-injection and review-steering risk;
- the review is read-only and secret-aware by default.

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
