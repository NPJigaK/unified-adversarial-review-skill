# Upstream Provenance

Date recorded: 2026-06-18

This repository is intended to adapt the adversarial review method from
OpenAI's `codex-plugin-cc` while not using Claude Code as the runtime.

## Pinned Upstream Source

- Repository: <https://github.com/openai/codex-plugin-cc>
- Base repository commit: `807e03ac9d5aa23bc395fdec8c3767500a86b3cf`
- Snapshot commit date: 2026-04-18
- Snapshot commit subject: `fix: bump plugin version to 1.0.4 (#244)`
- Primary prompt path: `plugins/codex/prompts/adversarial-review.md`
- Base prompt SHA-256:
  `6D32771BBC061648082EA27EC3A8B57B36E2EDC3DD8F0BD9DFE5FD6C8AD654AC`
- Base prompt Git blob hash:
  `78668af6e0ca89d11b48bea8d01904210a750d17`

These four values are the v1 pin. Earlier commits that touched the prompt are
history, not the implementation pin.

## Relevant Upstream Files

- `plugins/codex/prompts/adversarial-review.md`
- `plugins/codex/commands/adversarial-review.md`
- `plugins/codex/commands/review.md`
- `plugins/codex/schemas/review-output.schema.json`
- `plugins/codex/scripts/codex-companion.mjs`
- `plugins/codex/scripts/lib/git.mjs`
- `plugins/codex/scripts/lib/prompts.mjs`
- `plugins/codex/scripts/lib/codex.mjs`
- `plugins/codex/scripts/lib/render.mjs`
- `plugins/codex/prompts/stop-review-gate.md`
- `plugins/codex/scripts/stop-review-gate-hook.mjs`
- `LICENSE`
- `NOTICE`

## Prompt History Observed

The local full-history fetch showed these commits touching
`plugins/codex/prompts/adversarial-review.md`:

- `c69527eb18d0bdab92080487708381f95cf4c291` (2026-03-30): `Initial commit`
- `bc8fa661a50998ead1c1164a94339fc9cab1d742` (2026-04-07):
  `fix: avoid embedding large adversarial review diffs (#179)`

The base repository commit `807e03ac9d5aa23bc395fdec8c3767500a86b3cf` did not
itself modify the prompt; it is the repository snapshot used during this
investigation. The prompt content at that snapshot includes the later
large-diff fix from `bc8fa661a50998ead1c1164a94339fc9cab1d742`.

## Verification Requirement

Future vendored excerpts or adapted reference files should include a local hash
check against the pinned prompt content. If the upstream prompt is deliberately
updated, update this file and record the diff rationale rather than following
`main` implicitly.

## License

- Upstream license: Apache-2.0
- Upstream notice: `Copyright 2026 OpenAI`
- This repository includes `LICENSE` and `NOTICE` to retain the upstream
  license and notice while marking this repository as a separate adaptation.

## Adaptation Boundary

Use as base:

- adversarial stance
- material-finding bar
- grounding rules
- calibration rules
- structured review contract concepts
- target/context collection lessons

Do not use as runtime dependency:

- Claude Code slash commands
- Claude Code background task flow
- Claude Code Stop hook
- `CLAUDE_PLUGIN_ROOT`
- Claude command `allowed-tools`
- Claude command `disable-model-invocation`

This repository implements the method as a portable Codex/Agent Skill.
