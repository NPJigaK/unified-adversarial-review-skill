# Unified Adversarial Review

A portable, read-only Agent Skill for adversarially reviewing code changes,
implementation plans, and pre-ship decisions.

The installable Skill is:

```text
skills/unified-adversarial-review/
```

It adapts the core stance of OpenAI's Apache-2.0 `codex-plugin-cc`
adversarial-review prompt while removing Claude Code as a runtime dependency.
The canonical workflow runs in one capable agent; subagents are optional and
never required for a complete review.

## Install Options

### Codex with `$skill-installer`

```text
Use $skill-installer to install the unified-adversarial-review skill from:

https://github.com/NPJigaK/unified-adversarial-review-skill/tree/main/skills/unified-adversarial-review

Install it for my user account. Inspect the skill contents before installing it,
and do not modify the source repository.
```

### Manual copy

```text
copy skills/unified-adversarial-review/
to   <repo>/.agents/skills/unified-adversarial-review/
```

### Universal CLI

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review
```

Codex-specific CLI install:

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review \
  --agent codex
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
- separation of finding assessment from coverage completeness;
- read-only review and sensitive-data protection.

## Repository Layout

```text
README.md
INSTALL.md
LICENSE
NOTICE
UPSTREAM.md
skills/unified-adversarial-review/
```

This repository is intentionally distribution-focused. Design notes, schemas,
validators, and eval infrastructure are not bundled here because they are not
installed with the Skill.

## License And Provenance

Apache-2.0. See [LICENSE](LICENSE), [NOTICE](NOTICE), and
[UPSTREAM.md](UPSTREAM.md). This is a separate adaptation and is not an OpenAI
product or endorsement.
