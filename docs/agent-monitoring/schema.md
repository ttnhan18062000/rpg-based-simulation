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
| `workflow` | string | No | Name of the workflow that produced this run: `implement-ticket` \| `implement-epic` \| `create-tickets`. |
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
| `NEEDS_HUMAN_INPUT` | Plan had unresolved questions; paused for human. |
| `NEEDS_CHANGES` | Architecture review returned violations. |
| `BLOCKED` | Architecture review found fundamental conflict. |
| `TESTS_FAILED` | Tests failed after implementation. |
| `SECURITY_BLOCKED` | Security review rejected the change (fires only for tickets whose tags include `security`, or whose derived `suggested_skills` includes `/security-review`). |
| `DOD_BLOCKED` | Definition-of-Done conditions not met. |
| `NOTHING_TO_CREATE` | `create-tickets` only — no actionable concerns, all concerns were duplicates of existing tickets, or no tasks survived structuring. |
| `CRASHED` | Synthetic status set by `validate.py` for runs with `start_ts` but no `end_ts`. |

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
| `ts` | ISO 8601 | No | UTC timestamp when this event was recorded. |
| `phase` | string | No | Workflow phase this agent call belongs to. |
| `agent` | string | No | Agent identifier (matches `.claude/agents/{agent}.md` filename). |
| `summary` | string | No | One sentence describing what the agent did and the key finding. Empty string = agent did not provide a summary (prompt quality signal). Max 200 chars. |
| `status` | string | No | `ok` \| `failed` \| `blocked` \| `skipped` |
| `tool_call_count` | int | Yes | Total number of tool calls made by this agent. Computed by `writeMonitoring` from `tools.jsonl` (counts entries matching `run_id` + `seq`). `null` for runs produced before this field was added. |
| `reason_code` | string | Yes | Machine-parseable sub-cause code. Populated for `Scope`/`ticket-scoper` and `Verify`/`done-checker` `failed` events; `null` everywhere else, and `null` for all records predating `TCK-20260706-MONITORING-REASON-CODE`/`TCK-20260706-SCOPE-TAG-REGISTRY-CHECK`. See below for why only those two phases get one. |
| `cost_proxy_score` | float | Yes | Monotonic, unitless spend-proxy score computed by `writeMonitoring` from `tools.jsonl`. `null`/absent for all records predating `TCK-20260708-AGENT-COST-OBSERVABILITY` (no backfill). See below for the formula. |

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

Formula (computed by `writeMonitoring`, one group per `(run_id, seq)`):

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

`Scope`, `Investigate`, `Plan`, `Review`, `Implement`, `Test`, `Parity`, `Security-Review`, `Verify`, `Finalize`

`Security-Review` is conditional — it only appears in `events.jsonl` for tickets whose tags include
`security`, or whose derived `suggested_skills` includes `/security-review`; it is absent entirely
(not even a `skipped` event) for every other ticket.

### `phase` values (create-tickets workflow)

`Comprehend`, `Investigate` (one event per concern), `Structure`, `Write` (one event per ticket), `Link` (only when `epic_id` is provided). `create-tickets` does not register a `.claude/current_run` sidecar per agent call, so `tool_call_count` is always `null` on its events — not computed the way it is for `implement-ticket`/`implement-epic`.

---

## `agent-monitoring/tools.jsonl`

One record per tool call, written by `PreToolUse` and `PostToolUse` hooks. Joined to events by `run_id` + `seq`.

```json
{
  "session_id": "abc123",
  "run_id": "TCK-20260614-TOOL-TRACKING",
  "seq": 5,
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
| `seq` | int | Yes | FK → events.seq. Identifies which agent event this tool call belongs to. Written by the agent to `.claude/current_run` as its first Bash step; `null` if the sidecar was not yet written at hook time. |
| `ts` | ISO 8601 | No | UTC timestamp of the tool call (captured at PostToolUse). |
| `tool` | string | No | Tool name: `Read`, `Edit`, `Write`, `Bash`, `Agent`, `MultiEdit`, etc. |
| `input_summary` | string | No | Extracted key identifier from tool input. Per-tool: file path for Read/Edit/Write/MultiEdit; first 80 chars of command for Bash; description/prompt for Agent. Max 120 chars. |
| `status` | string | No | `ok` \| `failed`. Derived from the tool response's error flag. |
| `duration_ms` | int | Yes | Wall-clock milliseconds from PreToolUse to PostToolUse. `null` if the pre-hook temp file was missing. |

### How tool calls are attributed to agent events

Each agent prompt includes an early Bash step that writes `{"run_id": "...", "seq": N}` to `.claude/current_run`. The PostToolUse hook reads this file on every tool call and tags the record with `run_id` + `seq`. The `writeMonitoring` step at the end of the workflow counts records per seq to produce `tool_call_count` in events.jsonl.

Tool calls made outside a workflow (interactive Claude Code session) are still recorded with `run_id: null, seq: null` — useful for auditing overall tool usage.

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
