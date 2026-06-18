# Installation

The installable Skill directory is:

```text
skills/unified-adversarial-review/
```

Install that directory as a whole. Do not install the repository root as a
Skill.

## Install Options

The same Skill directory is installed for every Agent Skills client:

```text
skills/unified-adversarial-review/
```

Install the whole directory. Do not copy only `SKILL.md`; the `references/`
directory is part of the runtime instructions.

License and provenance files are maintained at the repository root:
`LICENSE`, `NOTICE`, and `UPSTREAM.md`.

Only the install path and invocation syntax vary by client.

### Codex

```text
Use $skill-installer to install the unified-adversarial-review skill from:

https://github.com/NPJigaK/unified-adversarial-review-skill/tree/main/skills/unified-adversarial-review

Install it for my user account. Inspect the skill contents before installing it,
and do not modify the source repository.
```

Project-scoped install:

```text
.agents/skills/unified-adversarial-review/
```

User/global install:

```text
$HOME/.agents/skills/unified-adversarial-review/
```

CLI install:

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review \
  --agent codex
```

Invoke:

```text
$unified-adversarial-review Review the current branch against main.
```

Use without installing:

```bash
npx skills use \
  NPJigaK/unified-adversarial-review-skill@unified-adversarial-review \
  --agent codex
```

### Claude Code

Project-scoped install:

```text
.claude/skills/unified-adversarial-review/
```

User/global install:

```text
~/.claude/skills/unified-adversarial-review/
```

CLI install:

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review \
  --agent claude-code
```

Invoke:

```text
/unified-adversarial-review Review the current branch against main.
```

Use without installing:

```bash
npx skills use \
  NPJigaK/unified-adversarial-review-skill@unified-adversarial-review \
  --agent claude-code
```

### Cursor

Project-scoped install:

```text
.cursor/skills/unified-adversarial-review/
```

User/global install:

```text
~/.cursor/skills/unified-adversarial-review/
```

CLI install:

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review \
  --agent cursor
```

Invoke:

```text
/unified-adversarial-review Review the current branch against main.
```

Use without installing:

```bash
npx skills use \
  NPJigaK/unified-adversarial-review-skill@unified-adversarial-review \
  --agent cursor
```

### Shared `.agents` layout

Some Agent Skills clients also load the shared project-scoped path:

```text
.agents/skills/unified-adversarial-review/
```

or user/global path:

```text
~/.agents/skills/unified-adversarial-review/
```

### Agent Skills CLI

```bash
npx skills add NPJigaK/unified-adversarial-review-skill \
  --skill unified-adversarial-review
```

## Notes

- The Skill content and review method are the same across Codex, Claude Code,
  Cursor, and other Agent Skills clients.
- `agents/openai.yaml` is OpenAI/Codex UI metadata. Clients that do not read it
  can ignore it without changing the Skill semantics.
- Invocation syntax is client-specific: Codex uses `$unified-adversarial-review`;
  Claude Code and Cursor commonly use `/unified-adversarial-review` or a skill
  menu.
