# Unified Adversarial Review Skill Research

Date: 2026-06-18

Normative status: historical research and source analysis. Current v1 decisions
live in [DECISIONS.md](DECISIONS.md). Superseded assumptions and withdrawn
findings are separated in [HISTORY.md](HISTORY.md). Upstream provenance is in
[UPSTREAM.md](../UPSTREAM.md).

This document preserves the investigation that informed the implemented
`unified-adversarial-review` Skill. It is historical and non-normative.

The current requirement is:

- Treat the "original OpenAI version" as:
  <https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/prompts/adversarial-review.md>
- Check the original prompt and its surrounding mechanism before using it as the base.
- Do not use Claude Code as the runtime.
- Preserve the full investigation history, including superseded assumptions and withdrawn findings.

## Current Repository State

At the time of investigation:

- Working directory: this repository root
- Git state: no commits yet on `main`; `origin/main` was gone from local status.
- `rg --files` returned no tracked or untracked project files.
- The repository contained `.git` only before this document was added.
- Remote: `git@github.com:NPJigaK/unified-adversarial-review-skill.git`
- `git ls-remote --heads origin` returned no remote heads.

This means all conclusions below are design and source-analysis conclusions. They are not findings
against an implemented skill in this repository.

## Corrected Definition Of "Original OpenAI Version"

The original OpenAI version is not the temporary local provisional
`adversarial-review` skill.

The original OpenAI version is:

- Repository: `https://github.com/openai/codex-plugin-cc`
- Commit inspected locally: `807e03ac9d5aa23bc395fdec8c3767500a86b3cf`
- Prompt path: `plugins/codex/prompts/adversarial-review.md`
- Command path: `plugins/codex/commands/adversarial-review.md`
- Runtime script: `plugins/codex/scripts/codex-companion.mjs`
- Git context collection: `plugins/codex/scripts/lib/git.mjs`
- Codex app-server wrapper: `plugins/codex/scripts/lib/codex.mjs`
- Prompt interpolation: `plugins/codex/scripts/lib/prompts.mjs`
- Output schema: `plugins/codex/schemas/review-output.schema.json`
- Rendering: `plugins/codex/scripts/lib/render.mjs`
- Claude stop gate prompt/hook:
  - `plugins/codex/prompts/stop-review-gate.md`
  - `plugins/codex/scripts/stop-review-gate-hook.mjs`

Important correction:

- The previous statement saying that "OpenAI version" was not externally confirmed is superseded.
- The temporary local `adversarial-review` skill should not be treated as the method source of truth.
- The GitHub OpenAI prompt and surrounding plugin mechanism must be used as the base reference.

## What The OpenAI Original Actually Is

The inspected OpenAI source is a Claude Code plugin that delegates work to Codex.

The plugin itself is for Claude Code users, but it uses the local Codex CLI and Codex app server as
the actual review runtime. For this repository, Claude Code-specific command wrapping is not used.
Only the review method, prompt contract, schema contract, and target/context collection ideas are
base material.

The plugin README describes:

- `/codex:review` as a normal read-only Codex review.
- `/codex:adversarial-review` as a steerable review that questions implementation direction,
  design choices, assumptions, tradeoffs, and failure modes.
- `/codex:adversarial-review` uses the same review target selection as `/codex:review`.
- It supports `--base <ref>`, `--wait`, and `--background`.
- Unlike `/codex:review`, it accepts extra focus text after flags.
- The command is read-only and does not fix code.
- The plugin wraps the Codex app server and uses the user's local `codex` binary, local auth, local
  checkout, machine-local environment, and Codex config.

## OpenAI Prompt Structure

The OpenAI prompt is organized as tagged sections. Its method should be treated as the core base.
The prompt is documented here section by section rather than copied verbatim. The source of truth is
the linked OpenAI repository file; this document records all observed responsibilities,
constraints, and contracts that informed the implemented Skill.

### Role

The reviewer is Codex performing an adversarial software review.

The central role is to break confidence in the change rather than validate it.

### Task

The reviewer receives:

- a target label
- user focus text
- repository context

It reviews the provided repository context to find the strongest reasons the change should not ship
yet.

### Operating Stance

The stance is skeptical by default.

It assumes the change may fail in subtle, high-cost, or user-visible ways until evidence says
otherwise.

It does not give credit for:

- good intent
- partial fixes
- likely follow-up work

If something only works on the happy path, the prompt treats that as a real weakness.

### Attack Surface

The prompt prioritizes failures that are expensive, dangerous, or hard to detect:

- auth
- permissions
- tenant isolation
- trust boundaries
- data loss
- data corruption
- duplication
- irreversible state changes
- rollback safety
- retries
- partial failure
- idempotency gaps
- race conditions
- ordering assumptions
- stale state
- re-entrancy
- empty state
- null behavior
- timeout behavior
- degraded dependency behavior
- version skew
- schema drift
- migration hazards
- compatibility regressions
- observability gaps that hide failure or make recovery harder

### Review Method

The prompt actively tries to disprove the change.

It looks for:

- violated invariants
- missing guards
- unhandled failure paths
- assumptions that fail under stress

It traces how bad inputs, retries, concurrent actions, and partial operations move through code.

User focus is weighted heavily, but other defensible material issues may still be reported.

The prompt includes `REVIEW_COLLECTION_GUIDANCE`, which changes depending on whether the diff is
fully inlined or whether the reviewer must self-collect context with read-only git commands.

### Finding Bar

Only material findings are reported.

The prompt excludes:

- style feedback
- naming feedback
- low-value cleanup
- speculative concerns without evidence

Every finding must answer:

- what can go wrong
- why the code path is vulnerable
- likely impact
- concrete risk-reducing change

### Structured Output Contract

The OpenAI original requires valid JSON matching the provided schema.

It uses:

- `needs-attention` when there is material risk worth blocking on
- `approve` when no substantive adversarial finding can be supported from provided context

Every finding must include:

- affected file
- `line_start`
- `line_end`
- confidence score from `0` to `1`
- concrete recommendation

The summary should be a terse ship/no-ship assessment rather than a neutral recap.

### Grounding Rules

The prompt is aggressive but grounded.

Every finding must be defensible from repository context or tool output.

The prompt forbids inventing:

- files
- lines
- code paths
- incidents
- attack chains
- runtime behavior

If a conclusion depends on inference, that inference must be stated and confidence must stay honest.

### Calibration Rules

The prompt prefers one strong finding over several weak findings.

It tells the reviewer not to dilute serious issues with filler.

If the change looks safe, the reviewer should return no findings directly.

### Final Check

Before finalizing, every finding must be:

- adversarial rather than stylistic
- tied to a concrete code location
- plausible under a real failure scenario
- actionable for an engineer fixing it

## OpenAI Output Schema

The schema file is `plugins/codex/schemas/review-output.schema.json`.

Top-level object:

- `additionalProperties: false`
- required:
  - `verdict`
  - `summary`
  - `findings`
  - `next_steps`

`verdict` enum:

- `approve`
- `needs-attention`

`summary`:

- string
- minimum length 1

`findings`:

- array of objects
- each finding has `additionalProperties: false`
- required:
  - `severity`
  - `title`
  - `body`
  - `file`
  - `line_start`
  - `line_end`
  - `confidence`
  - `recommendation`

Finding fields:

- `severity`: enum `critical`, `high`, `medium`, `low`
- `title`: non-empty string
- `body`: non-empty string
- `file`: non-empty string
- `line_start`: integer, minimum 1
- `line_end`: integer, minimum 1
- `confidence`: number from 0 to 1
- `recommendation`: string

`next_steps`:

- array of non-empty strings

Schema tension observed:

- The prompt says to report only material findings.
- The schema permits `low` severity.
- If this repository wants a stricter material-only skill, either remove `low` from the final schema
  or define that `low` is allowed only for compatibility but should not normally appear.

## OpenAI Companion Runtime Mechanism

The Claude Code command is not used here, but its surrounding mechanism matters because it shows how
the OpenAI prompt receives context and how Codex is constrained.

### Command Layer

`plugins/codex/commands/adversarial-review.md`:

- describes the command as a Codex review that challenges implementation approach and design choices
- is review-only
- forbids fixing issues or applying patches
- returns Codex output verbatim in the Claude Code command flow
- preserves raw arguments exactly
- supports `--wait`, `--background`, `--base <ref>`, `--scope auto|working-tree|branch`, and focus text
- uses the same review target selection as `/codex:review`
- does not support `--scope staged` or `--scope unstaged`
- can take extra focus text after flags

Claude Code-specific parts to exclude from this Codex Skill:

- `disable-model-invocation`
- `allowed-tools`
- `AskUserQuestion`
- Claude background tasks
- returning command stdout verbatim as a Claude command wrapper
- `CLAUDE_PLUGIN_ROOT`

Concepts to keep:

- review-only boundary
- wait/background is a runtime concern, not a review-method concern
- preserve user focus text
- do not weaken adversarial framing
- use the same target-selection semantics as ordinary review where possible

### Normal Review Versus Adversarial Review

`/codex:review`:

- maps to the built-in Codex reviewer via app-server `review/start`
- is not steerable
- does not accept extra focus text

`/codex:adversarial-review`:

- does not use the native `review/start` path
- builds a custom prompt from `prompts/adversarial-review.md`
- sends it through app-server `turn/start`
- passes `review-output.schema.json` as `outputSchema`
- runs in a read-only sandbox

This distinction matters for this repository:

- The implemented Skill is based on the adversarial prompt and review contract.
- It should not assume that built-in `/review` behavior can be customized into this method.

### Argument Handling

`scripts/lib/args.mjs` provides:

- long options with `--key value` and `--key=value`
- boolean options where `--flag=false` maps to false
- short aliases
- `--` passthrough for positionals
- quoted string splitting for raw argument strings

For review commands, `codex-companion.mjs` parses:

- value options: `base`, `scope`, `model`, `cwd`
- boolean options: `json`, `background`, `wait`
- alias: `-m` maps to `--model`
- remaining positionals become focus text

### Target Resolution

`resolveReviewTarget(cwd, options)`:

- first ensures the directory is inside a Git repository
- supports scopes:
  - `auto`
  - `working-tree`
  - `branch`
- if `--base <ref>` is passed, target mode is `branch` against that base
- if `--scope working-tree` is passed, target mode is working tree
- unsupported scopes produce an error
- if `--scope branch` is passed, it detects a default branch
- in `auto` mode:
  - dirty working tree means working-tree review
  - otherwise review branch diff against detected default branch

Default branch detection:

- first tries `refs/remotes/origin/HEAD`
- then tries candidates:
  - `main`
  - `master`
  - `trunk`
- checks both local branches and `origin/<candidate>`
- if none is found, it errors and asks for `--base <ref>` or `--scope working-tree`

Working-tree state includes:

- staged files from `git diff --cached --name-only`
- unstaged files from `git diff --name-only`
- untracked files from `git ls-files --others --exclude-standard`
- dirty state if any of those are non-empty

### Working Tree Context Collection

For working-tree review, context can include:

- `git status --short --untracked-files=all`
- staged diff
- unstaged diff
- untracked files

Untracked file handling:

- directories are skipped
- broken symlinks or unreadable files are skipped
- binary files are skipped
- files larger than 24 KiB are skipped
- text files under the limit are embedded

Inline diff thresholds:

- default max inline files: 2
- default max inline diff bytes: 256 KiB

If the working tree is too large:

- the script includes status, diff stats, changed files, and eligible untracked file content
- it does not inline the full diff
- it tells the adversarial reviewer to inspect the target diff with read-only git commands before
  finalizing findings

### Branch Context Collection

For branch review:

- it computes merge base using `git merge-base HEAD <baseRef>`
- `commitRange` is `<mergeBase>..HEAD`
- `reviewRange` is `<baseRef>...HEAD`
- changed files come from `git diff --name-only <commitRange>`
- commit log comes from `git log --oneline --decorate <commitRange>`
- diff stat comes from `git diff --stat <commitRange>`
- inline branch diff uses `git diff --binary --no-ext-diff --submodule=diff <commitRange>`

Nuance:

- `reviewRange` is computed but the collected diff/log use `commitRange`.
- The implementation deliberately avoids inheriting this wrapper transport behavior; future adapters may decide whether to use explicit
  three-dot diff semantics consistently.

### Prompt Construction

`buildAdversarialReviewPrompt(context, focusText)` loads `prompts/adversarial-review.md` and
interpolates:

- `TARGET_LABEL`
- `USER_FOCUS`
- `REVIEW_COLLECTION_GUIDANCE`
- `REVIEW_INPUT`

The interpolation implementation replaces `{{UPPERCASE_KEY}}` placeholders and uses an empty string
for missing values.

### Codex App Server Execution

The plugin checks that:

- `codex --version` is available
- `codex app-server --help` is available

For adversarial review, it uses `runAppServerTurn`:

- starts a Codex app-server connection
- starts a fresh thread unless resuming
- uses sandbox `read-only`
- uses approval policy `never`
- uses an ephemeral thread by default
- sends the generated prompt to `turn/start`
- passes the JSON schema as `outputSchema`
- captures the final assistant message
- parses it as JSON

`runAppServerTurn` returns:

- status
- thread ID
- turn ID
- final message
- reasoning summary
- final turn
- error
- cleaned stderr
- file changes
- touched files
- command executions

For normal review, it instead uses `runAppServerReview`:

- starts a read-only ephemeral thread
- calls app-server `review/start`
- captures `enteredReviewMode` and `exitedReviewMode` items
- returns the built-in review text

### App Server Event Capture

The plugin tracks app-server notifications including:

- thread started
- turn started
- item started
- item completed
- errors
- turn completed

It captures:

- final assistant message
- review text from `exitedReviewMode`
- reasoning summaries
- command executions
- file changes
- subagent/collaboration activity

It infers completion after the final answer when subagent work has drained.

This matters because:

- an adversarial review Skill should not rely on hidden intermediate reasoning
- final output must be derived from the final structured result and evidence surfaced in context
- if subagents are used, parent synthesis must wait for their completion

### Rendering

`renderReviewResult`:

- fails visibly if Codex does not return valid JSON
- validates top-level shape before rendering
- normalizes findings
- sorts findings by severity: critical, high, medium, low
- renders target, verdict, summary, findings, recommendations, and next steps
- includes reasoning summary if available

Important nuance:

- Rendering normalizes missing finding fields for display, but the app-server run passes an
  `outputSchema`, so the intended contract is schema-constrained JSON.
- The Skill and optional adapters must not rely on renderer normalization as a substitute for schema correctness.

### Stop Review Gate

The plugin also includes a Claude Code Stop hook review gate.

Mechanism:

- It runs only when enabled by plugin config.
- It reviews only the previous Claude turn.
- If the previous turn did not make code changes, it returns allow immediately.
- It outputs a compact first line with allow/block semantics.
- It runs a Codex task with a stop-gate prompt and blocks ending the Claude session if the review
  returns block.

This is Claude Code-specific and should not be used directly in this repository.

Concepts that may still be relevant:

- gate output must have strict machine-readable semantics
- review should verify that actual code changes happened before blocking
- gate reviews must avoid blocking on older unrelated work

## Codex Skill And Codex Platform Facts Verified

OpenAI Codex Skill docs support these facts:

- A skill packages instructions, resources, and optional scripts.
- A skill directory has required `SKILL.md` and optional `scripts/`, `references/`, `assets/`, and
  `agents/openai.yaml`.
- Skills use progressive disclosure: Codex initially sees name, description, and file path, then
  reads full `SKILL.md` only when the skill is selected.
- Skills can be explicitly invoked or implicitly invoked by matching the description.
- `allow_implicit_invocation: false` in `agents/openai.yaml` disables implicit invocation but still
  permits explicit invocation.
- Codex reads repo-scoped skills from `.agents/skills` along the current working directory path up to
  repo root.
- Direct skill folders are for authoring and local discovery; plugins are the distribution unit when
  reusable installation or app/MCP integration is needed.
- Best practice: keep each skill focused on one job, prefer instructions over scripts unless
  deterministic behavior or external tooling is needed, and test prompts against the description.

OpenAI Codex Subagents docs support these facts:

- Codex can spawn specialized subagents in parallel and collect results.
- Subagents are useful for complex parallel exploration, tests, triage, summarization, and other
  bounded tasks.
- Codex only spawns subagents when explicitly asked to do so.
- Subagent workflows consume more tokens than comparable single-agent runs.
- Subagents inherit current sandbox policy, but custom agents can override sandbox configuration.
- Custom agents are standalone TOML files under `~/.codex/agents/` or `.codex/agents/`.
- Each custom agent file must define:
  - `name`
  - `description`
  - `developer_instructions`
- Optional custom agent fields include:
  - `nickname_candidates`
  - `model`
  - `model_reasoning_effort`
  - `sandbox_mode`
  - `mcp_servers`
  - `skills.config`
- `agents.max_threads` defaults to 6.
- `agents.max_depth` defaults to 1.

Custom agent placement conclusion:

- The runtime Skill includes optional `agents/openai.yaml` for UI metadata,
  invocation policy, and tool dependencies.
- Actual Codex custom agent TOML files for roles such as mapper/challenger/validator belong in
  `.codex/agents/` or `~/.codex/agents/`, not as ordinary files inside the skill directory.
- If the skill wants to be self-contained, it should either avoid requiring custom TOML agents or
  document a setup step that installs project-scoped `.codex/agents/*.toml`.

OpenAI Codex Security plugin docs support these facts:

- Codex Security uses staged workflows:
  - threat modeling
  - finding discovery
  - validation
  - attack-path analysis
  - reporting
- Threat modeling identifies entry points, trust boundaries, sensitive actions, and risky
  components.
- Finding discovery looks for concrete source-to-sink paths or broken controls.
- Validation tests or otherwise verifies plausible findings and records evidence or proof gaps.
- Attack-path analysis traces exploitable paths and rates severity for findings that survive
  validation.
- Security diff scan is scoped to pull request, commit, branch diff, or working-tree patch.
- First scans should stay read-only unless the user explicitly asks Codex to prepare a fix.

Codex app-server docs support these facts:

- A client starts `codex app-server`, initializes, starts or resumes a thread, starts a turn, and
  streams events.
- `turn/start` can accept optional overrides including model, sandbox policy, and output schema.
- `review/start` runs the Codex reviewer and supports targets such as uncommitted changes, base
  branch, commit, and custom instructions.

Codex approvals and security docs support these facts:

- Prompt injection can cause an agent to fetch and follow untrusted instructions.
- Web results and fetched external content should be treated as untrusted.
- Read-only and approval controls matter for safe review workflows.

OpenAI eval guidance supports these facts:

- Use eval-driven development.
- Make evaluations task-specific and representative of real-world distributions.
- Include typical, edge, and adversarial cases.
- Use human expert labels where needed.
- Evaluation is continuous.
- Multi-agent architectures introduce additional nondeterminism and need evaluation at the points
  where nondeterminism enters.

## External Methodology Sources Checked

These sources support the broader methodology but do not prove that any particular Codex Skill
implementation will be accurate. The final skill must be evaluated.

### NASA IV&V

NASA IV&V material supports:

- independent verification and validation as a risk-reduction practice
- managerial, technical, and financial independence as true IV&V properties
- independent selection of what to analyze, which techniques to use, schedules, and issues to act on
- increased likelihood of finding high-risk errors early

Codex implication:

- Same-model subagents are not true NASA IV&V independence.
- They can only be described as separation of duties or bias reduction.
- Claims of real independence must be avoided unless separate organizations, methods, or reviewers
  are actually involved.

### Microsoft Threat Modeling / Secure By Design

Microsoft sources support:

- threat modeling as structured security design analysis
- thinking like an attacker
- identifying threats before shipping
- modeling software design, data flow, and trust boundaries
- STRIDE as a useful categorization method, not the entire review method

Codex implication:

- Security review should start from system model, data flow, and trust boundaries.
- STRIDE and OWASP should be conditional security lenses, not the parent framework for the whole
  skill.

### FMEA

FMEA sources support:

- identifying potential failure modes
- identifying causes and effects
- prioritizing and limiting failures
- using failure analysis for prevention and forecasting

Codex implication:

- FMEA is a good source for state, data, reliability, and operational failure analysis.
- It should be used as a conditional lens or reference, not as the sole skill structure.

### OWASP Code Review Guide

OWASP supports:

- manual code review as a security activity
- review guidance tied to how vulnerability classes are identified in code

Codex implication:

- OWASP belongs mainly in the `Security / Trust` lens.
- It should not dominate non-security review domains such as migration, concurrency, rollback, or
  observability.

### NIST SSDF

NIST SSDF supports:

- secure development practices as a high-level framework that can integrate into SDLCs
- evidence/artifacts as records of secure development practices
- outcome-oriented practices rather than one prescribed development method

Codex implication:

- The Skill should produce review artifacts that can be integrated into a repeatable workflow.
- It should not be a one-off checklist dump.

### AWS Formal Methods / TLA+

AWS formal methods sources support:

- modeling safety and liveness properties for complex systems
- using TLA+ or PlusCal to find subtle bugs in distributed systems
- reported AWS cases including DynamoDB issues requiring traces of 35 steps

Codex implication:

- Modeling invariants before generating scary scenarios is a sound design choice.
- Formal methods should be treated as an optional verification technique for high-risk cases, not
  something the Skill always executes.

### OSS-Fuzz

OSS-Fuzz sources support:

- continuous fuzzing as a practical method for finding vulnerabilities and bugs
- reported May 2025 result: over 13,000 vulnerabilities and 50,000 bugs across 1,000 projects

Codex implication:

- Fuzzing is a verification technique for input-handling hypotheses.
- It is not itself a review lens and should not always run.

### Chaos Engineering

Chaos Engineering principles support:

- defining steady state
- forming hypotheses
- varying real-world events
- minimizing blast radius
- treating production experiments carefully

Codex implication:

- Chaos belongs as an optional validation/experiment recommendation for resilience and operations
  risks.
- Review mode should not run destructive or production-impacting chaos experiments.

### Premortem

HBR premortem material supports:

- assuming a project has failed and generating plausible reasons for failure
- surfacing concerns earlier

Codex implication:

- Premortem is useful for hypothesis generation.
- It is not evidence.
- Premortem-generated risks must go through trace and verification before becoming findings.

## Historical Review Notes

Historical findings, withdrawn conclusions, and intermediate design positions
are preserved in [HISTORY.md](HISTORY.md). The latest design review is preserved
verbatim in [DESIGN_REVIEW_2026-06-18.md](reviews/DESIGN_REVIEW_2026-06-18.md).

This research file now keeps source analysis and rationale only. Current
normative requirements live in [DECISIONS.md](DECISIONS.md).

## Claude Code Elements Not To Use

Do not use:

- Claude Code slash command files as the runtime
- Claude background task flow
- `AskUserQuestion`
- Claude Stop hook
- Claude-specific review gate
- `CLAUDE_PLUGIN_ROOT`
- Claude command `allowed-tools`
- Claude command `disable-model-invocation`
- returning Codex stdout verbatim as a Claude command behavior

Use instead:

- Codex Skill `SKILL.md`
- optional `references/`
- optional deterministic validation scripts
- optional `agents/openai.yaml` for Codex app metadata and invocation policy
- optional project-scoped `.codex/agents/*.toml` if custom subagents are required

## Recommended Skill Structure

Historical repository-local skill location considered during research:

```text
.agents/skills/unified-adversarial-review/
├── SKILL.md
├── references/
│   ├── openai-original-analysis.md
│   ├── methodology.md
│   ├── evidence-and-severity.md
│   ├── lens-security-trust.md
│   ├── lens-data-state.md
│   ├── lens-concurrency-distributed.md
│   ├── lens-migration-compatibility.md
│   ├── lens-resilience-operability.md
│   ├── lens-resource-performance.md
│   └── lens-llm-agent.md
├── scripts/
│   └── validate-output.py
└── agents/
    └── openai.yaml
```

Current distribution layout is recorded in `docs/DECISIONS.md` and
`README.md`. The repository now keeps the installable runtime skill at
`skills/unified-adversarial-review/` so common installers can discover
`skills/<name>/SKILL.md`, while Codex project installs still place the copied or
linked runtime directory under `.agents/skills/unified-adversarial-review/`.

If using custom subagents:

```text
.codex/agents/
├── uar-mapper.toml
├── uar-challenger.toml
└── uar-validator.toml
```

Reason:

- Codex custom agent TOML files are loaded from `.codex/agents/` or `~/.codex/agents/`.
- Skill-local `agents/openai.yaml` is metadata and policy, not the standalone custom agent TOML
  mechanism.

## Recommended Core Workflow

The workflow should be OpenAI-base plus explicit modeling:

```text
Frame
  Define review target, base, scope, user focus, and risk tolerance.

Collect
  Gather working-tree or branch context with read-only git commands.

Model
  Reconstruct intended behavior, execution paths, state transitions, data flow,
  trust boundaries, invariants, side effects, rollout, rollback, and external assumptions.

Challenge
  Try to disprove the release-safety case using bad input, empty/null state,
  retries, timeouts, partial failures, concurrency, stale state, version skew,
  permission/tenant violations, degraded dependencies, and observability gaps.

Trace
  Follow candidate failures through concrete repository paths.

Verify
  Try to disprove each candidate by checking guards, callers, config, defaults,
  framework guarantees, tests, and documented contracts.

Adjudicate
  Keep only material, grounded, actionable findings.

Report
  Return structured ship/no-ship output, findings, next steps, uncertainty, and review limits.
```

This is compatible with the OpenAI original because it keeps the original stance and finding bar,
but makes model and verification steps explicit.

## Review Mode Boundaries

Review mode must be read-only.

Allowed:

- read files
- inspect diffs
- run safe read-only git commands
- inspect existing tests
- run existing tests if user/environment policy allows and the command is not destructive
- verify external platform contracts from official or primary sources
- use temporary scratch space only if it does not modify the repository and does not hide evidence
- recommend tests or reproductions

Not allowed in review mode:

- edit repository files
- add tests to the repository
- add fixtures to the repository
- apply patches
- run destructive commands
- run unknown project scripts without considering side effects
- run production-impacting chaos experiments
- perform remediation unless the user explicitly switches tasks

## Output Contract Design Options

### Option A: Stay Close To OpenAI Original

Use:

- `approve`
- `needs-attention`

Pros:

- closest to original
- simple
- easier schema validation

Cons:

- no explicit inconclusive state
- no explicit conditional release state
- needs separate fields for review limits and missing evidence

### Option B: Unified Expanded Verdicts

Use:

- `block`
- `conditional`
- `clear-within-scope`
- `inconclusive`

Required gate semantics:

- `block`: fail release gate
- `conditional`: fail until listed conditions are completed
- `inconclusive`: fail or require human review
- `clear-within-scope`: pass only within the reviewed scope

Pros:

- clearer release semantics
- avoids treating "no findings" as proof of safety

Cons:

- diverges from OpenAI original schema
- needs adapters if compatible with original review tooling

### Evidence Levels

If evidence levels are included, use:

- `traced`
- `reproduced`
- `tool-confirmed`
- `formally-checked`

Do not allow final findings to use:

- `hypothesized`

Use `hypothesized` only for internal candidates or residual uncertainties.

## Subagent Position

OpenAI `codex-plugin-cc` adversarial review does not define custom mapper/challenger/validator
subagents. It runs a single Codex turn with a structured prompt and schema.

Codex docs say subagents are explicit and cost more.

Therefore:

- subagents should not be mandatory unless the user explicitly asks for a multi-agent review or the
  Skill defines a high-risk mode that asks the parent Codex to spawn them
- subagents are best treated as optional separation of duties
- if used, they must be read-only in review mode
- if used, parent synthesis must not become a majority vote
- if used, roles should be narrow:
  - mapper: facts, paths, invariants, trust boundaries
  - challenger: counterexample candidates
  - validator: disprove candidates, check guards and evidence
  - parent: adjudication and final output

Subagent limitation:

- Same-model subagents are not true independent verification and validation.
- They reduce some prompt-local bias but can share correlated mistakes.

## Lens Routing

Do not run every checklist every time.

Use conditional lenses based on changed code and modeled risk:

- Security / Trust:
  - auth
  - permissions
  - tenant boundaries
  - secrets
  - external input
  - injection
  - prompt injection
  - tool authority
- State / Data Integrity:
  - schema changes
  - migrations
  - destructive writes
  - deletion
  - billing
  - duplication
  - irreversible state
- Concurrency / Distributed Behavior:
  - retry
  - idempotency
  - queue semantics
  - locks
  - cache
  - events
  - ordering
  - stale reads
  - re-entrancy
- Compatibility / Migration:
  - public API
  - protocol
  - serialization
  - config
  - old clients
  - old workers
  - mixed deployments
  - rollback
- Resilience / Operations:
  - dependency failure
  - timeout
  - feature flags
  - monitoring
  - alerting
  - recovery
  - runbooks
- Resource / Performance Safety:
  - unbounded work
  - memory
  - disk
  - fan-out
  - quotas
  - rate limits
- LLM / Agent:
  - untrusted context
  - prompt injection
  - tool misuse
  - confused deputy
  - data exfiltration
  - secret leakage
  - unsafe autonomous action

## Evaluation Requirements

The Skill itself needs evals.

Positive cases:

- known production incidents
- security regressions
- race conditions
- unsafe migrations
- rollback failures
- tenant isolation breaks
- data loss bugs
- intentionally inserted mutations

Negative cases:

- safe changes
- unreachable scary code
- already-guarded paths
- intentional behavior
- style-only concerns
- tests that already cover the risk

Metrics:

- material finding recall
- precision
- false positives per review
- top-1 and top-3 detection
- location accuracy
- evidence completeness
- duplicate finding rate
- unsupported claim rate
- token cost
- wall-clock cost

The eval set should include typical, edge, and adversarial cases, with human calibration where
needed.

## Historical Open Questions (Resolved In DECISIONS.md)

1. Should the final output stay fully compatible with OpenAI's original `approve` /
   `needs-attention` schema, or should it use expanded `block` / `conditional` /
   `clear-within-scope` / `inconclusive` verdicts?
2. If expanded verdicts are used, should a compatibility renderer produce the original schema for
   tools that expect it?
3. Should `low` severity be removed from final findings, despite being present in the OpenAI
   original schema?
4. Should custom subagents be optional documentation only, or should this repository include
   project-scoped `.codex/agents/*.toml` files?
5. Should the Skill include a deterministic `validate-output.py` script and JSON schema from v1?
6. Should large-diff self-collection preserve the `codex-plugin-cc` thresholds exactly:
   - max inline files 2
   - max inline diff bytes 256 KiB
   - max untracked file bytes 24 KiB
7. Should branch review preserve `commitRange = mergeBase..HEAD`, or use explicit three-dot diff
   semantics throughout?

## Source List

Primary OpenAI source for the original prompt:

- <https://github.com/openai/codex-plugin-cc/blob/main/plugins/codex/prompts/adversarial-review.md>
- <https://github.com/openai/codex-plugin-cc>

OpenAI Codex docs:

- Agent Skills: <https://developers.openai.com/codex/skills>
- Subagents: <https://developers.openai.com/codex/subagents>
- Codex Security plugin: <https://developers.openai.com/codex/security/plugin>
- Codex App Server: <https://developers.openai.com/codex/app-server>
- Agent approvals and security: <https://developers.openai.com/codex/agent-approvals-security>
- Evaluation best practices: <https://developers.openai.com/api/docs/guides/evaluation-best-practices>
- Structured Outputs: <https://developers.openai.com/api/docs/guides/structured-outputs>

Agent Skills specification:

- <https://agentskills.io/specification>

Git source:

- git-branch upstream tracking behavior: <https://git-scm.com/docs/git-branch>

External methodology sources:

- NASA IV&V overview: <https://www.nasa.gov/ivv-overview/>
- NASA IV&V program PDF: <https://ntrs.nasa.gov/api/citations/20140016847/downloads/20140016847.pdf>
- Microsoft Threat Modeling Tool overview:
  <https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool>
- Microsoft Secure by Design:
  <https://www.microsoft.com/en-us/securityengineering/sdl/practices/secure-by-design>
- ASQ FMEA: <https://asq.org/quality-resources/fmea>
- AHRQ FMEA: <https://digital.ahrq.gov/health-it-tools-and-resources/evaluation-resources/workflow-assessment-health-it-toolkit/all-workflow-tools/fmea-analysis>
- OWASP Code Review Guide: <https://owasp.org/www-project-code-review-guide/>
- NIST SSDF SP 800-218: <https://csrc.nist.gov/pubs/sp/800/218/final>
- AWS formal methods / TLA+ PDF:
  <https://lamport.azurewebsites.net/tla/formal-methods-amazon.pdf>
- OSS-Fuzz: <https://github.com/google/oss-fuzz>
- Principles of Chaos Engineering: <https://principlesofchaos.org/>
- HBR Project Premortem: <https://hbr.org/2007/09/performing-a-project-premortem>

Local artifacts read during investigation:

- pasted research attachments;
- the provisional local `adversarial-review` skill;
- provisional local `pr_explorer` and `adversarial_reviewer` agent configs;
- a temporary clone of `openai/codex-plugin-cc`.

Exact local absolute paths are intentionally omitted because they are
environment-specific and not normative. The temporary local skill and local
agents are recorded for investigation completeness only. They are not
authoritative for the final Skill unless explicitly adopted later.
