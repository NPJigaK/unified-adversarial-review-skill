# Installation

The installable Skill directory is:

```text
skills/unified-adversarial-review/
```

Install that directory as a whole. Do not install the repository root as a
Skill.

## Install Options

### Codex with `$skill-installer`

```text
Use $skill-installer to install the unified-adversarial-review skill from:

https://github.com/NPJigaK/unified-adversarial-review-skill/tree/main/skills/unified-adversarial-review

Install it for my user account. Inspect the skill contents before installing it,
and do not modify the source repository.
```

### Manual copy

Copy or symlink:

```text
skills/unified-adversarial-review/
```

to:

```text
<repo>/.agents/skills/unified-adversarial-review/
```

For Codex user/global installs, Codex official docs describe user skills under:

```text
$HOME/.agents/skills/
```

Third-party installers may use different global paths for Codex user installs;
verify global installs in your local Codex build before relying on them.

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

## Invoke

Invoke the Skill explicitly:

```text
$unified-adversarial-review Review the current branch against main.
Focus especially on rollback safety, data integrity, and retry behavior.
Do not modify repository files.
```

## Use Without Installing

```bash
npx skills use \
  NPJigaK/unified-adversarial-review-skill@unified-adversarial-review \
  --agent codex
```

## Other Agent Skills Clients

This Skill follows the portable Agent Skills `SKILL.md` directory layout. For
compatible clients, copy or link the whole directory:

```text
skills/unified-adversarial-review/
```

into the target agent's skills directory. Do not copy only `SKILL.md`; the
`references/` directory is part of the runtime instructions.

### Claude Code

Project-scoped install:

```text
.claude/skills/unified-adversarial-review/
```

User/global install:

```text
~/.claude/skills/unified-adversarial-review/
```

Invoke with:

```text
/unified-adversarial-review Review the current branch against main.
```

Claude Code may also be used through compatible installers, for example:

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review \
  --agent claude-code
```

### Cursor

Project-scoped install:

```text
.cursor/skills/unified-adversarial-review/
```

User/global install when supported by your Cursor version:

```text
~/.cursor/skills/unified-adversarial-review/
```

Invoke through Cursor's skill or slash-command UI, typically:

```text
/unified-adversarial-review Review the current branch against main.
```

Compatible installers may also support Cursor, for example:

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review \
  --agent cursor
```

### Generic `.agents` layout

Clients that follow the shared Agent Skills directory convention may also load:

```text
.agents/skills/unified-adversarial-review/
```

or:

```text
~/.agents/skills/unified-adversarial-review/
```

## Compatibility Notes

- Codex is the primary target for this repository.
- Claude Code and Cursor compatibility is based on the portable `SKILL.md`
  layout, not on any Claude- or Cursor-specific runtime dependency.
- `agents/openai.yaml` is Codex UI metadata. Other clients may ignore it without
  changing the Skill semantics.
- Invocation syntax is client-specific: Codex uses `$unified-adversarial-review`;
  Claude Code and Cursor commonly use `/unified-adversarial-review` or a skill
  menu.
