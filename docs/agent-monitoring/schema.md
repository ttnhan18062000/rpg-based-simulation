---
status: active
layer: observability
authority: P1
audience: developer
tags: [agent-monitoring, schema]
---

# Agent Monitoring — Schema Reference

Two append-only JSONL files, joined by `run_id`.

---

## Derived SQLite Index (Read Path Only)

`tools/agent-monitoring/build_index.py` builds a gitignored, full-rebuild-only SQLite index
(`agent-monitoring-index/monitoring.db`) from all 3 JSONL files below — `runs`, `events`, and
`tools` tables, each column-for-column derived from the corresponding JSONL shape, plus a
materialized `resolved_status`/`is_complete` pair on `runs` computed by importing
`generate_retro.py::_resolve_status()` and `validate.py::_record_is_complete()` directly rather
than reimplementing that normalization in SQL. It mirrors this repo's `knowledge-index/knowledge.db`
precedent: derived, gitignored, rebuildable, **never** the source of truth — the JSONL files below
remain the sole write-path/append-only ground truth, untouched by the index or its build step.

Run `make agent-monitoring-index` to (re)build it. `query.py` and `validate.py` **hard-require**
the index to exist (exiting with an actionable "run `make agent-monitoring-index` first" error if
it's missing) — a deliberate choice, since neither is meant to run without its data source.
`generate_retro.py` is the one exception: it builds the index on demand if missing, and falls back
to reading the raw JSONL directly if that on-demand build itself fails, so the weekly retro report
never becomes hard-blocked on the index's presence. `events`/`tools` tables use non-unique
`(run_id, seq)` indexes, not a `UNIQUE` constraint — historical pause/resume seq-collision
duplicates (see the Known Limitations section below) exist in the live corpus and would crash a
naive unique-key rebuild. `tools.jsonl` rows missing a `tool` field (a handful of confirmed
off-schema records) are excluded from the `tools` table with a stderr warning, never coerced.

See `docs/plans/archive/agent_infrastructure/idea_agent_monitoring_derived_index.md` (archived —
shipped) for the full design rationale, and `docs/parity_ledger/infrastructure.yaml` entries
INFRA-289 through INFRA-291 for the per-consumer migration evidence and any documented output
divergences.

---

## `agent-monitoring/runs.jsonl`

One record per workflow invocation.

```json
{
  "run_id": "TCK-20260607-COMBAT-RELATION",
  "start_ts": "2026-06-07T10:00:00Z",
  "end_ts": "2026-06-07T10:48:30Z",
  "workflow": "implement-ticket",
  "tier": "standard",
  "final_status": "DONE",
  "agent_count": 9,
  "duration_s": 2910
}
```

### Fields

| Field | Type | Nullable | Description |
|---|---|---|---|
| `run_id` | string | No | Unique run identifier. For `implement-ticket`: the ticket ID. For `implement-epic`: `EPIC-{id}` or `FOLDER-{path}`. For `create-tickets`: `CREATE-TICKETS-{sanitized source path}` — no single ticket_id exists at run start since this workflow creates N tickets. |
| `start_ts` | ISO 8601 | No | UTC timestamp when the workflow started (captured at Scope / Discover / Comprehend phase via `date -u`). |
| `end_ts` | ISO 8601 | Yes | UTC timestamp when the workflow finished. `null` if the workflow crashed before writing the end record. |
| `workflow` | string | No | Name of the workflow that produced this run: `implement-ticket` \| `implement-epic` \| `create-tickets` \| `simq-audit`. |
| `tier` | string | No | Ticket tier: `hotfix` \| `standard` \| `epic`. For `create-tickets`: always `n/a` — this workflow doesn't operate on a single ticket's tier (each generated ticket gets its own tier, decided during the Structure phase). |
| `final_status` | string | No | Outcome of the run. See values below. |
| `agent_count` | int | No | Total number of agent calls that produced events. |
| `duration_s` | int | Yes | Wall-clock seconds from start to end. `null` for crashed runs. |

### What is not recorded

**Token counts** are not recorded. The workflow `agent()` call returns the agent's structured output only; API usage metadata (`input_tokens`, `output_tokens`) is consumed internally by the Claude Code runtime and is not forwarded to the workflow script. There is no field for it and no workaround within the current platform.

**Tool call counts** per agent are also not recorded. They could be self-reported (each agent counts its own tool calls and includes the total in its return value), but this is not currently implemented. Use `agent_count` as a coarse proxy for run complexity.

### `final_status` values

| Value | Meaning |
|---|---|
| `IN_PROGRESS` | Run-start record written; end record not yet written. Should not appear in completed runs. |
| `DONE` | Workflow completed successfully. |
| `EPIC_SCOPED` | Epic tier — ticket scoped, no implementation. |
| `CONFLICTS_DETECTED` | Duplicate or conflicting ticket found at Scope gate. |
| `TAGS_NOT_REGISTERED` | A ticket's tag isn't in `docs/guidelines/tag_registry.jsonl` — caught at Scope, before the rest of the pipeline runs (`TCK-20260706-SCOPE-TAG-REGISTRY-CHECK`). |
| `SCOPE_AGENT_FAILED` | The Scope-phase `ticket-scoper` agent call returned null or malformed output with no `ticket_id` — caught before any other phase runs (`TCK-20260720-MONITORING-PIPELINE-BUGFIXES`). |
| `NEEDS_HUMAN_INPUT` | Plan had unresolved questions; paused for human. |
| `NEEDS_CHANGES` | Architecture review returned violations. |
| `BLOCKED` | Architecture review found fundamental conflict. |
| `DOC_STALENESS_BLOCKED` | A behavior-changing `src/` or `.claude/workflows/*.js` diff has no `docs/` path in `files_changed` — caught right after Implement, before Architecture-Verify/Test/Parity/Verify (`TCK-20260720-GATE-CHECK-WIRING-DECISIONS`, wiring `tools/gate_checks/doc_staleness_check.py`). |
| `TESTS_FAILED` | Tests failed after implementation. |
| `DATA_RUNS_CLEAN_FAILED` | Post-Test auto-clean of `data/runs/*`/`reports/release_proof/*` failed (permissions/lock issue) — resolved manually, then re-run. |
| `PARITY_INCOMPLETE` | A committed `src/` path mapped to a parity-ledger subsystem was not cross-referenced in the Parity phase's ledger update. |
| `SECURITY_BLOCKED` | Security review rejected the change (fires only for tickets whose tags include `security`, or whose derived `suggested_skills` includes `/security-review`). |
| `DOD_BLOCKED` | Definition-of-Done conditions not met. |
| `FINALIZE_INCOMPLETE` | Finalize's self-check (`run_finalize_selfcheck`) found the migration/move/log-append/registry-regen steps did not fully land, or its own output was unparseable. |
| `NOTHING_TO_CREATE` | `create-tickets` only — no actionable concerns, all concerns were duplicates of existing tickets, or no tasks survived structuring. |
| `CRASHED` | Synthetic status set by `validate.py` for runs with `start_ts` but no `end_ts`. |

### Historical Corrections

`runs.jsonl` is append-only for all *new* writes (see the file's opening line above) — every writer
(`record_run.py`) only ever `open(RUNS_FILE, "a")`s, never rewrites an existing line. The one
documented exception: **TCK-20260718-STATUS-DRIFT-REPAIR** (2026-07-18) corrected the `final_status`
casing on 7 pre-existing records (`"done"`/`"success"` → `"DONE"`, predating this doc's all-uppercase
enum convention) via an atomic, audited, line-scoped string substitution — not a bulk parse/
re-serialize — so every other byte of every other line was left untouched. This was a one-time
historical data correction, not a change to the write contract; the file remains append-only for
all writes going forward.

---

## `agent-monitoring/events.jsonl`

One record per agent call within a workflow run. FK: `run_id → runs.run_id`.

```json
{
  "run_id": "TCK-20260607-COMBAT-RELATION",
  "seq": 3,
  "ts": "2026-06-07T10:12:00Z",
  "phase": "Investigate",
  "agent": "investigator",
  "summary": "Found incomplete projection fallback in resolver.py:214; parity gap in combat_movement entry CM-031",
  "status": "ok"
}
```

### Fields

| Field | Type | Nullable | Description |
|---|---|---|---|
| `run_id` | string | No | FK to runs.jsonl. |
| `seq` | int | No | 1-based call order within the run. Monotonically increasing. |
| `ts` | ISO 8601 | No | UTC timestamp when this event was recorded. Captured by the orchestrator (`bash('date -u +%Y-%m-%dT%H:%M:%SZ')`) immediately before the paired `agent()` call, not self-reported by the agent — see TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH. |
| `phase` | string | No | Workflow phase this agent call belongs to. |
| `agent` | string | No | Agent identifier (matches `.claude/agents/{agent}.md` filename). |
| `summary` | string | No | One sentence describing what the agent did and the key finding. Empty string = agent did not provide a summary (prompt quality signal). Max 200 chars. |
| `status` | string | No | `ok` \| `failed` \| `blocked` \| `skipped` |
| `tool_call_count` | int | Yes | Total number of tool calls made by this agent. Computed deterministically by `record_events.py` at write time from `tools.jsonl` (counts entries matching `run_id` + `seq`) for `implement-ticket` workflow records only — see below. `null` for runs produced before this field was added, and for workflows that never register a `.claude/current_run` sidecar (`create-tickets`, `implement-epic`). |
| `reason_code` | string | Yes | Machine-parseable sub-cause code. Populated for `Scope`/`ticket-scoper` and `Verify`/`done-checker` `failed` events; `null` everywhere else, and `null` for all records predating `TCK-20260706-MONITORING-REASON-CODE`/`TCK-20260706-SCOPE-TAG-REGISTRY-CHECK`. See below for why only those two phases get one. |
| `cost_proxy_score` | float | Yes | Monotonic, unitless spend-proxy score computed deterministically by `record_events.py` at write time from `tools.jsonl`, for `implement-ticket` workflow records only. `null`/absent for all records predating `TCK-20260708-AGENT-COST-OBSERVABILITY` (no backfill). See below for the formula. |

### `status` values

| Value | Meaning |
|---|---|
| `ok` | Agent completed its task successfully. |
| `failed` | Agent returned an error or could not complete. |
| `blocked` | Agent was blocked by a gate condition (e.g. architecture violation). |
| `skipped` | Phase was skipped (e.g. Investigate/Plan/Review for hotfix tier). |

### `reason_code` values

Populated wherever a gate status collapses more than one distinct cause into a single value.
`NEEDS_HUMAN_INPUT` → Plan, `NEEDS_CHANGES`/`BLOCKED` → Review or Architecture-Verify,
`TESTS_FAILED` → Test, and `SECURITY_BLOCKED` → Security-Review each still disambiguate 1:1 via
`phase`/`final_status` alone — no code needed there. Three phases, across both workflows that
write to this file, don't:

- **`Verify`** (`done-checker`, `implement-ticket`) — its 13-condition checklist collapses many
  distinct DoD failure reasons into one `DOD_BLOCKED` status (`TCK-20260706-MONITORING-REASON-CODE`).
- **`Scope`** (`ticket-scoper`, `implement-ticket`) — used to have exactly one failure cause
  (conflicts), so `phase=Scope + status=failed` alone was enough; adding a second cause
  (unregistered tags, `TCK-20260706-SCOPE-TAG-REGISTRY-CHECK`) reopened the same collapsed-cause
  problem, so it now gets a code too.
- **`Structure`** (`create-tickets`, `create-tickets` workflow) — the same unregistered-tag cause
  can also surface here, since this workflow computes tags for a whole batch of tickets before any
  of `implement-ticket`'s gates ever run (`TCK-20260706-CREATE-TICKETS-TAG-CHECK`).

| Value | Meaning | Phase(s) |
|---|---|---|
| `conflicts_detected` | Duplicate or conflicting ticket found. | Scope |
| `tag_registry_rejection` | A tag isn't in `docs/guidelines/tag_registry.jsonl` (see `docs/guidelines/tag_taxonomy.md`'s Tag Registry section) — same root cause regardless of which phase/workflow caught it. | Scope, Structure, Verify |
| `dod_condition_failed` | Any other DoD condition failed at Verify — a deliberately coarse fallback, not a full taxonomy of every possible DoD failure reason (that would be speculative rather than evidence-driven; see `tools/gate_checks/done_checker_static.py`'s `classify_checklist_failure`). | Verify |

Not a closed enum — a future phase found to have its own catch-all-status problem could add its
own value, but none is added speculatively ahead of evidence. `generate_retro.py`'s reason-code
aggregation is workflow-agnostic (iterates every event regardless of source) — no code change was
needed there when `Structure` started emitting this field.

### `cost_proxy_score` — proxy formula and interpretation

`cost_proxy_score` is a **monotonic, unitless proxy for relative comparison** (e.g. "agent A costs
3x agent B this week"), **not a dollar-denominated cost figure** — no reader should subtract two
scores and interpret the delta as real currency.

Formula (computed deterministically by `record_events.py::compute_tool_stats()` at write time,
one group per `(run_id, seq)` — moved out of `writeMonitoring`'s own LLM-executed prompt by
`TCK-20260719-COST-PROXY-WRITE-PATH`, since an agent-transcribed compute step is exactly the kind
of non-deterministic bookkeeping this repo's other monitoring fields already moved away from; see
`record_run.py`'s `compute_duration_s` for the precedent this mirrors):

```
cost_proxy_score = w_bash  * Σ(Bash duration_ms)
                  + w_agent * count(Agent-tool spawns)
                  + w_edit  * count(Read/Edit/Write/MultiEdit calls)
```

Current starting weights: `w_bash=0.001, w_agent=50, w_edit=1`. These are calibratable, not
precision-load-bearing — `tools/agent-monitoring/cost_proxy.py` is the single source of truth for
the live values (same pattern as this doc deferring to `vocabulary.py` for phase/agent vocabulary).

Why `count(Agent)` and never `Σ duration_ms where tool=Agent`: the `Agent` tool's own `duration_ms`
is SDK call-dispatch overhead, not the spawned subagent's real cost — a sampled ticket showed the
`Agent` tool averaging ~97ms regardless of the spawned agent's actual runtime, and a
background/async spawn's real cost is invisible to the parent's own tool-call duration entirely.
Summing would silently undercount fan-out cost, so the formula counts spawns instead.

Known limitations:

- The raw linear formula is **unclamped and outlier-sensitive** — a single very-long Bash call can
  dominate a spend breakdown. This is an accepted characteristic of Tier 1, not a bug; a future
  ticket may revisit capping if real retro data shows distortion.
- `null`/absent for every event recorded before `TCK-20260708-AGENT-COST-OBSERVABILITY` landed (no
  backfill) — a retro breakdown over a period spanning the cutover will show partial coverage, by
  design.

Canonical phase/agent values for all four workflows are enforced from `tools/agent-monitoring/vocabulary.py` — the tables below are illustrative documentation, not the source of truth; if they disagree with `vocabulary.py`, the module wins.

### `phase` values (implement-ticket workflow)

`Scope`, `Investigate`, `Plan`, `Review`, `Implement`, `Architecture-Verify`, `Test`, `Parity`, `Security-Review`, `Verify`, `Finalize`

`Architecture-Verify` and `Security-Review` are both conditional. `Architecture-Verify` is skipped
for hotfix tier. `Security-Review` only appears in `events.jsonl` for tickets whose tags include
`security`, or whose derived `suggested_skills` includes `/security-review`; it is absent entirely
(not even a `skipped` event) for every other ticket.

### `phase` values (create-tickets workflow)

`Comprehend`, `Investigate` (one event per concern), `Structure`, `Write` (one event per ticket), `Link` (only when `epic_id` is provided). Neither `create-tickets` nor `implement-epic` registers a `.claude/current_run` sidecar per agent call (neither ever has), so `tool_call_count` is always absent on their events — `record_events.py::compute_tool_stats()` only computes it for `implement-ticket` run_ids (see "How tool calls are attributed to agent events" above), and leaves every other workflow's records untouched.

### `phase` values (implement-epic workflow)

`Implement` — one event per child ticket, recording that child ticket's own overall status. No
Discover/Report phase-tagged events are emitted today (see `.claude/workflows/implement-epic.js`).

### `phase` values (simq-audit workflow)

`Recalibrate`, `Classify Drift`, `Update Anchors`, `Sync Docs`, `Parity Check`, `Verify`, `Report`.

### Retrieval-event field family (additive)

Introduced by `TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT`. `tools/retrieval_events.py` is the
single source of truth for the field list (`RETRIEVAL_EVENT_FIELDS`) — the table below is
illustrative documentation, same convention as `vocabulary.py` above. All fields are optional
additions on top of the 7 base fields already documented above; they never replace or narrow the
base REQUIRED set enforced by `record_events.py::validate_record()`.

| Field | Type | Description |
|---|---|---|
| `retrieval_event_schema_version` | int | Version of this additive field family itself, starting at `1`. Distinct from `retrieval_version` below — the two are unrelated and must not be conflated. |
| `retrieval_version` | int | The retrieval/cache-key logic's own version number, sourced from `tools/retrieval_cache.py`'s `RETRIEVAL_VERSION` constant (manually bumped on breaking changes to the cache's key/invalidation logic) or a `ContextPacket`'s own `retrieval_version` field. Not to be confused with `retrieval_event_schema_version` above, which versions this monitoring-event shape itself, not the retrieval logic. |
| `corpus_generation` | string | Which corpus/index generation this retrieval ran against. |
| `cache_level` | string | `index` \| `query` \| `packet` — which of the 3 cache levels (`docs/observability/retrieval_retention_redaction_policy.md`) this event concerns, if any. |
| `cache_status` | string | `hit` \| `miss` \| `stale-rejected`, taken verbatim from `tools/retrieval_cache.py`'s own status constants. |
| `latency_ms` | float | Wall-clock time of the wrapped call, measured by the wrapper via `time.perf_counter()`. |
| `candidate_count` | int | Upper-bound approximation of the pre-fusion/pre-selection candidate pool size. |
| `selected_count` | int | Number of results actually selected/returned. |
| `source_kind_counts` | object | Counts of selected results by `kind` (`doc`, `ticket`, `code_symbol`, etc.). |
| `authority_counts` | object | Counts of selected results by `authority` value (including the `unrated` sentinel from `tools/hybrid_retrieval.py`). |
| `freshness_counts` | object | Counts of selected results by `freshness` value (including `unrated`). |
| `exclusion_reason_counts` | object | Counts of excluded candidates by reason. |
| `cited_source_hashes` | array of string | Content hashes of cited sources — never raw content, per the retention/redaction policy's PROHIBITED list. |
| `adequacy_verdict` | string | `sufficient` \| `insufficient` \| `noisy` — a deliberately simple, documented-placeholder heuristic (`tools/retrieval_events.py::compute_adequacy_verdict()`), not a claim of real quality assessment. |
| `expansion_reason` / `expansion_count` | string / int | Present only if a follow-up expansion occurred. |
| `scenario` / `risk_tier` | string | Optional, caller-supplied classification fields. |

**Provenance (`run_id`/`seq`/`phase`/`agent`) for standalone invocations:** retrieval events are
emitted from test/manual invocations of the Phase 3 retrieval modules
(`tools/hybrid_retrieval.py`, `tools/retrieval_cache.py`, `tools/context_packet_assembler.py`),
none of which are wired into any `.claude/workflows/*.js` file — there is no tracked
`implement-ticket`/`implement-epic`/`create-tickets`/`simq-audit` run to attach to. Rather than
reusing a real ticket ID (which would misclassify these synthetic events into that ticket's own
event stream under `infer_workflow()`) or inventing a synthesized `run-{code}-{timestamp}` value
(explicitly forbidden — see "Manual/ad hoc run_id convention" below), these events mint a new,
self-describing `run_id` prefix: `RETRIEVAL-EVENT-<slug>`. This prefix matches none of
`infer_workflow()`'s 4 known prefixes (`SIMQ-AUDIT-`, `EPIC-`/`FOLDER-`, `CREATE-TICKETS-`,
`TCK-`), so `infer_workflow()` returns `None` for it — sanctioned by that function's own
documented "future 5th workflow" contract — and `warn_vocabulary_drift()` is consequently a
genuine no-op for these events' `phase`/`agent` literals (`Retrieval` /
`hybrid-retrieval-wrapper`, `retrieval-cache-wrapper`, `context-packet-wrapper`), not a
suppressed real warning. `seq` is a small caller-supplied literal, never a timestamp/hash.
Because these `run_id`s have no matching `runs.jsonl` row, they are naturally excluded from every
existing run-scoped retro/dashboard view (`generate_retro.py` filters events to `run_id in
{r["run_id"] for r in runs}`) — they do not corrupt or interleave into any real ticket's event
stream.

---

## `agent-monitoring/tools.jsonl`

One record per tool call, written by `PreToolUse` and `PostToolUse` hooks. Joined to events by `run_id` + `seq`.

```json
{
  "session_id": "abc123",
  "run_id": "TCK-20260614-TOOL-TRACKING",
  "seq": 5,
  "phase": "Implement",
  "agent": "implementer",
  "ts": "2026-06-14T10:12:01Z",
  "tool": "Bash",
  "input_summary": "pytest tests/engine/ -x",
  "status": "ok",
  "duration_ms": 4210
}
```

### Fields

| Field | Type | Nullable | Description |
|---|---|---|---|
| `session_id` | string | No | Claude Code session ID from the hook payload. Groups all tool calls within one session. |
| `run_id` | string | Yes | FK → runs.jsonl. `null` when the tool call occurred outside an active workflow run (interactive session use). |
| `seq` | int | Yes | FK → events.seq. Identifies which agent event this tool call belongs to. Written by the orchestrating workflow (`implement-ticket.js`'s `writeSidecar(seq)` helper) via a `bash()` call immediately before the paired `agent()` call; `null` if the sidecar was not yet written at hook time. |
| `phase` | string | Yes | Workflow phase this tool call occurred during, matching the `phase` literal at the corresponding `writeSidecar` call site (or the Scope-phase inline write). `null` when the tool call occurred outside an active workflow run, or for records predating `TCK-20260719-LIVE-PHASE-AGENT-LABEL` (no backfill). |
| `agent` | string | Yes | Agent identifier active during this tool call, matching the `agent` literal at the corresponding call site. Same nullability rules as `phase`. |
| `ts` | ISO 8601 | No | UTC timestamp of the tool call (captured at PostToolUse). |
| `tool` | string | No | Tool name: `Read`, `Edit`, `Write`, `Bash`, `Agent`, `MultiEdit`, etc. |
| `input_summary` | string | No | Extracted key identifier from tool input. Per-tool: file path for Read/Edit/Write/MultiEdit; first 80 chars of command for Bash; description/prompt for Agent. Max 120 chars. |
| `status` | string | No | `ok` \| `failed`. Derived from the tool response's error flag. |
| `duration_ms` | int | Yes | Wall-clock milliseconds from PreToolUse to PostToolUse. `null` if the pre-hook temp file was missing. |

### Write locking

The `PostToolUse` hook (`post_tool_hook.py`) wraps its open+write block in `fcntl.flock(f, fcntl.LOCK_EX)` (released via `fcntl.flock(f, fcntl.LOCK_UN)` after the write) so concurrent hook invocations from different Claude Code sessions/processes serialize their appends instead of racing — without this, two processes' `write()` calls to the same append-mode file handle can interleave mid-line, producing an unparseable record (observed and hand-repaired once, `TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK`). This is a POSIX-only guarantee (`fcntl` has no Windows equivalent); the hook has no platform fallback, consistent with this repo's `tools/` convention of not supporting non-POSIX environments. The lock is advisory and only serializes writers going through this same hook script — it does not protect against a non-Python process writing to the file directly (none is known to). Any locking failure (unsupported platform, OS-level error) is swallowed by the hook's existing fail-silent `try/except Exception: pass` wrapper exactly like every other exception in this hook — it never blocks or fails the tool call the hook fires after.

### How tool calls are attributed to agent events

The orchestrating workflow (`implement-ticket.js`) writes `{"run_id": "...", "seq": N}` to `.claude/current_run` itself via a `bash()` call (the shared `writeSidecar(seq)` helper), immediately before dispatching each corresponding `agent()` call — agent prompts no longer contain a sidecar-write instruction. The PostToolUse hook reads this file on every tool call and tags the record with `run_id` + `seq`. `record_events.py::compute_tool_stats()` — called at write time inside `record_events.py`'s own `main()`, not by `writeMonitoring`'s prompt — counts records per `(run_id, seq)` to produce `tool_call_count`/`cost_proxy_score` in `events.jsonl`, always overriding any value the caller passed in (`TCK-20260719-COST-PROXY-WRITE-PATH`; mirrors `record_run.py`'s `compute_duration_s`).

Since `TCK-20260719-LIVE-PHASE-AGENT-LABEL`, the sidecar (and thus each `tools.jsonl` record) also carries `phase`/`agent`, threaded through the same `writeSidecar(seq, phase, agent)` call as `run_id`/`seq` — this lets a live-run consumer show which phase/agent is currently producing tool calls without waiting for the run's `events.jsonl` entries to be written at exit.

Scope (`ticket-scoper`) also registers a sidecar value now (net-new coverage, `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`) — it can't reuse `writeSidecar(seq)` itself (that helper closes over `tid`, not yet known when creating a brand-new ticket), so it inlines two bash() branches: the real `{run_id: ticketId, seq: seqOffset + 1}` when resuming an existing ticket, or an explicit clear-to-`{}` when creating a new one (the ticket_id genuinely doesn't exist yet at that point — clearing at least prevents a stale value from a crashed prior run bleeding into this run's Scope-phase tool calls, even though Scope's own tool calls during ticket *creation* specifically stay correctly unattributed/null rather than attributed to the not-yet-known new ticket).

A third mechanism, `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`: when a ticket's run is
paused mid-pipeline and resumed later as a separate session sharing the same `run_id`, the
resumed session's own `seq` numbering (both `pushEvent`'s and every `writeSidecar` call site's
`events.length + 1` expression, and the Scope-phase resume branch's own sidecar write) would
previously restart at `1`, silently aliasing the new session's tool-call attribution onto
whatever `(run_id, seq)` buckets the pre-pause session already wrote in `tools.jsonl`. Fixed by a
`seqOffset` computed once at Scope-phase resume — `tools/agent-monitoring/seq_offset.py`'s
`compute_seq_offset(run_id, events)` looks up the max `seq` this `run_id` already has in
`agent-monitoring/events.jsonl` (`0` for a brand-new ticket) — added into every `seq`-producing
expression so a resumed session's numbering continues past the prior session's instead of
restarting. `tools/agent-monitoring/validate.py`'s `compute_multi_invocation_collision_report()`
detects this mechanism's historical signature (a `run_id` with more than one `phase="Scope",
seq=1` event) so a future recurrence surfaces automatically.

`writeMonitoring`'s own `agent()` call still never gets its own tracked `(run_id, seq)` by design, but its internal Step 5 "clear the sidecar" instruction was moved to Step 0 (run first, not last) by the same ticket. Previously, Steps 1-4's own Bash/python calls executed *before* the clear, so they were silently attributed to whatever phase's sidecar was still active — inflating that phase's true `tools.jsonl` row count beyond what Step 2's own snapshot had already recorded. This was confirmed empirically: a direct cross-check of `tool_call_count` against `tools.jsonl` ground truth found ~35% of historical events had a wrong count, concentrated (though not exclusively) at whichever phase immediately preceded a `writeMonitoring` call. Clearing first makes every one of writeMonitoring's own calls correctly unattributed (`run_id: null`) instead.

Tool calls made outside a workflow (interactive Claude Code session) are still recorded with `run_id: null, seq: null` — useful for auditing overall tool usage. Historical `tool_call_count`/`cost_proxy_score` values recorded before this fix are not backfilled (append-only precedent) — they may still be wrong; only events recorded after this fix are expected to be reliable.

### `status` values

| Value | Meaning |
|---|---|
| `ok` | Tool completed without error. |
| `failed` | Tool response contained an error flag or `"ERROR"` prefix. |

---

## Join Example

```python
import json
from pathlib import Path
from collections import defaultdict

runs = {json.loads(l)['run_id']: json.loads(l)
        for l in Path('agent-monitoring/runs.jsonl').read_text().splitlines() if l}

events_by_run = defaultdict(list)
for line in Path('agent-monitoring/events.jsonl').read_text().splitlines():
    if line:
        e = json.loads(line)
        events_by_run[e['run_id']].append(e)

tools_by_event = defaultdict(list)
for line in Path('agent-monitoring/tools.jsonl').read_text().splitlines():
    if line:
        t = json.loads(line)
        if t.get('run_id') and t.get('seq') is not None:
            tools_by_event[(t['run_id'], t['seq'])].append(t)

# Full run with events and per-event tool calls:
run = runs['TCK-20260607-...']
events = sorted(events_by_run[run['run_id']], key=lambda e: e['seq'])
for event in events:
    tools = tools_by_event[(run['run_id'], event['seq'])]
    print(f"  {event['phase']} ({event['agent']}): {len(tools)} tool calls")
```

---

## Known Limitations

### Legacy schema generations without `end_ts`

At least five historical monitoring-write generations coexist with the current schema in `runs.jsonl`:

1. `started_at`/`finished_at`/`status`/`phases_completed`/`notes`
2. `final_status` present but `end_ts` key absent
3. `ts_start`/`ts_end`/`result`/`agent`
4. `completed_at`/`status`
5. `FOLDER-*`/`EPIC-*` batch wrappers using a bare `status` field

`validate.py`'s incomplete-run check now recognizes all of these as valid completion signals (not just the current schema's `end_ts`), via the `LEGACY_COMPLETION_FIELDS` (`end_ts`, `finished_at`, `completed_at`, `ts_end`) and `LEGACY_TERMINAL_STATUS_VALUES` (the enumerated union of every terminal `final_status`/`status` value observed in the data — `DONE`, `done`, `complete`, `completed`, `success`, `EPIC_SCOPED`, `ALL_SCOPED`, `DOD_BLOCKED`, `NEEDS_HUMAN_INPUT`, `GATE_FAIL`, `STOPPED_BY_USER`) allowlists in `tools/agent-monitoring/validate.py`. The check also dedupes by `run_id` first — a `run_id`'s group of records is only flagged if none of its records satisfy the completion check.

This was a deliberate decision: an exhaustive audit (not a sample) of the 2026-07-05 investigation (`TCK-20260705-MONITORING-RUNID-JOIN`) found **107/107** of the previously-residual "Incomplete run (CRASHED?)" warnings were genuinely completed work — 98/107 via direct `tickets/done/` file match, the other 9 via explicit terminal-status fields plus independently-DONE child tickets. Zero genuine crashes or abandoned work were found.

**Final residual after the fix: exactly 1** — `TCK-20260623-TYPE-CHECKER`, a 6th legacy shape (`"outcome":"success"`, `"phase":"implement"`, no `end_ts`/`final_status`/`status` field at all) confirmed genuinely complete via a direct `tickets/done/TCK-20260623-TYPE-CHECKER.md` match. It is not added to the allowlist (a single-record shape is not worth a speculative code addition) — it is accepted as a permanently-documented, individually-verified exception.

Do not "fix" any of this by backfilling `runs.jsonl` (Out of Scope, append-only precedent) — the fix lives entirely in `validate.py`'s read-side interpretation.

### Manual/ad hoc run_id convention

The `run-{code}-{unix_ts}` run_id convention and ad hoc `-REDESIGN`-style suffixes found in historical data are pre-refactor/manual-session artifacts (confirmed via `.claude/workflows/implement-ticket.js`'s single-capture `tid` pattern, which cannot produce either shape) — not reproducible by current `.claude/workflows/*.js` code. If hand-writing monitoring records outside the JS workflows (e.g. an `audit-maintenance`-style direct invocation), always reuse the exact ticket ID as `run_id` verbatim — never invent a suffix or a synthesized `run-{code}-{timestamp}` ID; doing so breaks the events/run-record join for that record permanently.

### Full evidence

Full classification evidence for the 2026-07-05 audit of 126 incomplete-run / 5 zero-event records (corrected: 16 true dedup-resolved, 107 true residual, 107/107 confirmed genuinely completed): `stored_artifacts/TCK-20260705-MONITORING-RUNID-JOIN/investigation.md`.
