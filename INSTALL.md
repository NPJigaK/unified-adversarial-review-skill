# Installation

The installable Skill directory is:

```text
skills/unified-adversarial-review/
```

Install that directory as a whole. Do not install the repository root as a
Skill.

## Universal Installer

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review
```

## Codex Project Install

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review \
  --agent codex
```

Manual project install:

```text
copy or symlink:
  skills/unified-adversarial-review/

to:
  <repo>/.agents/skills/unified-adversarial-review/
```

Invoke explicitly:

```text
$unified-adversarial-review Review the current branch against main.
Focus especially on rollback safety, data integrity, and retry behavior.
Do not modify repository files.
```

Codex official docs describe repository skills under `.agents/skills`.
Third-party installers may use different global paths for Codex user installs;
verify global installs in your local Codex build before relying on them.

## Codex Natural-Language Install

```text
Use $skill-installer to install the unified-adversarial-review skill from:

https://github.com/NPJigaK/unified-adversarial-review-skill/tree/main/skills/unified-adversarial-review

Install it for my user account. Inspect the skill contents before installing it,
and do not modify the source repository.
```

## Use Without Installing

```bash
npx skills use \
  NPJigaK/unified-adversarial-review-skill@unified-adversarial-review \
  --agent codex
```

## Other Agent Skills Clients

Copy or link the whole directory:

```text
skills/unified-adversarial-review/
```

into the target agent's project-scoped skills directory.

Claude Code users may install the same Agent Skill into:

```text
.claude/skills/unified-adversarial-review/
```

or use:

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review \
  --agent claude-code
```

This is compatibility only. Claude Code is not a runtime dependency.
