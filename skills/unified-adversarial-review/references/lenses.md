# Risk Lenses

Use only lenses triggered by the target change. The point is depth on relevant
risks, not broad checklist coverage.

## Security / Trust

Trigger when the change touches auth, permissions, tenants, roles, sessions,
external input, secrets, sandboxing, file paths, tool calls, or data exposure.

Ask:

- Can an unauthorized caller reach the new path?
- Did the change move validation after a side effect?
- Are tenant, user, org, or environment boundaries preserved?
- Are secrets, tokens, keys, or PII read, logged, returned, or sent to tools?
- Does repository or user-controlled text influence commands, prompts, paths, or
  policy?

## Data / Migration

Trigger when the change writes, deletes, transforms, migrates, backfills, bills,
deduplicates, or changes persistence.

Ask:

- Can partial success be retried as a duplicate side effect?
- Is idempotency preserved across retries, restarts, and timeouts?
- Can migration order, default values, nullability, or old rows corrupt data?
- Is rollback safe after partial migration?
- Are read and write paths compatible during rollout?

## Concurrency / Retry / Distributed

Trigger when the change touches async work, queues, locks, caches, events,
ordering, retry, timers, or distributed state.

Ask:

- Can two workers process the same item?
- Can retry happen after a side effect but before state is recorded?
- Can cache invalidation race with reads or writes?
- Does ordering matter across events, commits, or messages?
- Are locks scoped, timed, and released correctly?

## Compatibility / Contract

Trigger when the change touches APIs, schemas, protocol, config, CLI flags,
public behavior, serialized data, old clients, or external integrations.

Ask:

- Do existing clients still work?
- Are old configs, old rows, old messages, or old serialized objects accepted?
- Is the rollout order safe across mixed versions?
- Does the change silently reinterpret an existing field or default?
- Are errors and status codes still compatible with callers?

## Resilience / Operability

Trigger when the change touches deploy, rollback, flags, startup, shutdown,
timeouts, observability, alerts, background jobs, or incident response.

Ask:

- Can the change fail closed or degrade safely?
- Is rollback safe after the new code has written state?
- Will operators see the failure quickly enough?
- Are metrics/logs/traces sufficient without leaking sensitive values?
- Can a stuck job, timeout, or dependency failure block recovery?

## Resource Safety

Trigger when the change touches loops, batching, fan-out, recursion, large input,
memory, disk, network, quotas, cost, model calls, or unbounded queues.

Ask:

- Can attacker/user input cause unbounded CPU, memory, disk, or cost?
- Can fan-out multiply unexpectedly?
- Are batch sizes, pagination, and timeouts bounded?
- Can retries amplify load during an outage?
- Is backpressure or rate limiting preserved?

## LLM / Agent

Trigger when the change touches prompts, RAG, MCP, tool calls, agent memory,
retrieved text, model output parsing, or autonomous actions.

Ask:

- Can untrusted text become an instruction?
- Can model output trigger unsafe tools or writes without validation?
- Are tool arguments constrained and checked?
- Can memory or retrieval leak private data across users or tasks?
- Does the agent preserve review/system instructions over repository text?

## Lens Selection Record

In the final coverage section, briefly state:

- lenses used;
- important lenses intentionally skipped and why;
- coverage gaps that could affect the assessment.
