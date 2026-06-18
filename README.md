# Unified Adversarial Review Agent Skill

A portable, read-only Agent Skill for adversarially reviewing code changes,
implementation plans, and pre-ship decisions.

The installable Skill is:

```text
skills/unified-adversarial-review/
```

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
