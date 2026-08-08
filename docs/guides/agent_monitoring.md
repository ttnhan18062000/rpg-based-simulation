---
status: active
layer: observability
authority: P1
audience: developer
tags: [agent-monitoring, retro]
---

# Agent Monitoring Retro Guide

The retro process transforms raw `runs.jsonl` + `events.jsonl` into a structured improvement cycle. Run it weekly or after a batch of tickets.

---

## When to Run

- After every 5+ completed tickets
- Every Friday (or the start of the next sprint)
- Before changing any agent prompt, workflow phase, or tier routing rule

This is no longer pure human discipline: a `PostToolUse` hook
(`tools/agent-monitoring/retro_nudge_hook.py`, wired in `.claude/settings.json`)
counts `implement-ticket` runs with `final_status`/`status` `DONE` in
`agent-monitoring/runs.jsonl` whose `start_ts`/`started_at` is later than the
mtime of the most recent dated `agent-monitoring/retro/RETRO-<week>.md` report
(`RETRO-ALL.md` is a static all-time snapshot and is excluded from this check).
Once that count reaches 5, it injects an `additionalContext` reminder to run
`/agent-monitoring-retro` — advisory only, it never blocks a tool call, and it
fires at most once per session. Run `/agent-monitoring-retro` to invoke the
skill directly instead of waiting for the nudge.

---

## How to Generate a Report

```bash
# Current ISO week (default)
python3 tools/agent-monitoring/generate_retro.py

# Specific week
python3 tools/agent-monitoring/generate_retro.py --week 2026-W23

# Last 30 days
python3 tools/agent-monitoring/generate_retro.py --days 30

# All time
python3 tools/agent-monitoring/generate_retro.py --all
```

Reports are written to `agent-monitoring/retro/RETRO-<label>.md`.  
The index at `agent-monitoring/retro/index.md` is updated automatically.

---

## Report Sections

| Section | What to Look For |
|---|---|
| **Run Summary** | DONE rate < 80%? Average duration > 20 min? |
| **Gate Failure Breakdown** | Which gates block most runs? Repeated TESTS_FAILED or PARITY_FAIL suggests systemic issues. |
| **Reason Codes** | Only shown when at least one event carries a `reason_code` (see `docs/agent-monitoring/schema.md`). Disambiguates gate statuses that collapse multiple causes into one value — e.g. a run of `DOD_BLOCKED` or Scope/Structure `failed`/`blocked` counts alone can't tell you whether the cause was an unregistered tag, a duplicate ticket, or an unrelated DoD condition; this section can. A rising `tag_registry_rejection` count suggests agents need better registry-awareness before Scope, not just a Verify-time catch. |
| **Tag Breakdown — Subsystem/Topic** | Only shown when at least one run resolves to a registered Subsystem/Topic tag. Tags are resolved live at report-generation time from ticket frontmatter under `tickets/done/` and `tickets/inprogress/`, keyed by `run_id` — a ticket file that has been moved, renamed, or deleted since its run completed becomes unresolvable and is silently excluded from this table (a known limitation of live resolution, not a bug). Use this to spot which subsystem/topic areas have the lowest DONE rate or the most gate failures. |
| **Tag Breakdown — Process/Skill-signal** | Only shown when at least one run resolves to a registered Process/Skill-signal tag. Deliberately asymmetric: only the `security` tag has a real gate to cross-reference today (`Security-Review` phase event or `SECURITY_BLOCKED` final_status, built by `TCK-20260705-WORKFLOW-SECURITY-GATE`) — its row shows a computed gate-hit count. `api-design`, `debugging`, and `performance` show `N/A — no gate implemented` in the same column, because no such gate exists in the orchestration code today, not because of a data gap. This is not a promise that symmetric gates are planned. |
| **Tier Distribution** | Are hotfix tickets actually taking a fast path? High hotfix gate-fail rate = wrong tier. A tier's DONE rate is computed excluding EPIC_SCOPED runs (shown in a separate Scoped column) — EPIC_SCOPED is a correct terminal state for scope-only epics, not a failure, and inflating the denominator with it previously understated epic tier health (44% vs. the real 79%). |
| **Agent Status Distribution** | High `failed` or `blocked` on specific agents → prompt problem. |
| **Phase Status Distribution** | A per-phase `ok`/`failed`/`blocked`/`skipped` breakdown, computed after folding casing variants (`Verify`/`verify`/`VERIFY` etc.) into one canonical bucket per phase (`TCK-20260719-PHASE-AGENT-CASE-FOLD`) — the accurate per-phase failure rate this table shows was previously undercounted when casing fragmentation split one logical phase across 2-3 separate buckets. `tools/agent-monitoring/validate.py`'s drift report deliberately still reports casing variants as separate entries — that's a data-integrity check, distinct from this table's read-time normalization for aggregation. |
| **Summary Quality** | Empty-summary count is scoped to current-schema events only (agent field set); pre-normalization legacy events (agent is null) never had a summary field and are reported separately as "Legacy-format records," not as a prompt-quality issue. Truncation count still covers all events (current + legacy). |
| **Slow Runs** | > 30 min runs (fixed threshold) — usually Review or Implement phase. Consider splitting or simplifying scope. |
| **Outliers** | Conditionally rendered — only appears when at least one value exceeds 3x its group's median (`duration_s` grouped by tier, `cost_proxy_score` grouped by normalized phase). A *relative* signal, distinct from Slow Runs' fixed 30-minute threshold: a run can be an Outlier without being a Slow Run (fast overall, but far from its tier's norm) and vice versa. Flags a value as worth a look, not a claim about *why* it's high — investigate before assuming (`TCK-20260719-RETRO-OUTLIER-FLAGS`). |
| **Tool Safety Audit** | Conditionally rendered — only appears when at least one Investigate-phase `(run_id, seq)` pair has `tools.jsonl` data in the period. Reports search-before-grep hard-rule (CLAUDE.md) compliance rate for real Investigate phases, and (since `TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE`) a count of `docs/parity_ledger/*.yaml` write calls made in a run that ALSO invokes `parity_index.py`'s build path (same `run_id`, anywhere in that run's own tool history) — an ordinary parity-updater edit with no co-occurring build call in the same run is not flagged, since it's the normal, required workflow (CLAUDE.md's Authoritative Mechanics Rule), not a risk. Also reports a zero-tolerance count of unsafe `parity_index.py build` invocations (targeting the real repo path instead of a scratch path) — unaffected by the rescope. Both counts should read 0 — a nonzero count is a real read-only-guarantee violation, not noise (`TCK-20260803-RETRO-TOOL-SAFETY-AUDIT`). |

---

## Validation

Before reading results, verify data integrity:

```bash
python3 tools/agent-monitoring/validate.py
```

Like `query.py`, `validate.py` reads from the derived SQLite index — run `make agent-monitoring-index`
first if it's missing (`validate.py` exits with an actionable error rather than a raw exception if so).

This checks:
- Every DONE working_log entry has a matching run record
- Every run record has at least one event
- No incomplete (crashed) runs are silently treated as complete

`validate.py` tolerates both the current schema (`final_status`) and the legacy `status` field
when deciding whether a run needs a `working_log.csv` entry — a run using either field is checked,
not just ones already on the current schema.

`generate_retro.py` now applies the same `final_status`/`status` fallback for its DONE/gate-fail
counts (Run Summary, Gate Failure Breakdown, Tier Distribution, and the retro index) — so a reader
shouldn't assume only `validate.py` handles legacy records.

---

## Querying Raw Data

`query.py` reads from the derived SQLite index, not the raw JSONL directly — run
`make agent-monitoring-index` first if you haven't built it yet (or it's gone stale after new
runs). See `docs/agent-monitoring/schema.md`'s "Derived SQLite Index" section.

```bash
# All failed events in the last 14 days
python3 tools/agent-monitoring/query.py --status failed --days 14

# All events for a specific run
python3 tools/agent-monitoring/query.py --run-id TCK-20260607-MON-SCHEMA

# Events mentioning "parity gap"
python3 tools/agent-monitoring/query.py --summary-contains "parity gap"

# Review-phase events only
python3 tools/agent-monitoring/query.py --phase Review

# Run summary list
python3 tools/agent-monitoring/query.py --runs
```

---

## Retrospective Process

After generating the report, fill in the `## Notes` section at the bottom. Answer:

1. **What failed most?** — Which gate or agent produced the most failures?
2. **What was slow?** — Which phase took longest and was it avoidable?
3. **What to change?** — One concrete action: update a prompt, split a ticket, fix a gate criterion.
4. **What worked?** — Note confirmed good patterns so they don't get reverted.

Commit the filled-in report to the repo. Do not discard notes — they are the institutional memory of agent behavior over time.

---

## Epic Staleness Check

`tools/agent-monitoring/epic_staleness_check.py` is a separate, read-only check
(distinct from the retro-cadence nudge above) that scans every open epic —
`epic_id`-mode tickets (`## Tier` -> `epic`) in `tickets/inprogress/`, and
`folder`-mode/hybrid `SEQUENCE.md` folders in `tickets/todos/*/` — for
child-ticket activity that has gone idle.

It resolves each epic's child ticket IDs, then cross-references
`tickets/working_log.csv` rows and `agent-monitoring/runs.jsonl` records for
the most recent matching timestamp across both sources. An epic is flagged
**stale** only if at least one child ticket shows real activity evidence AND
that evidence is older than the default **5-day** staleness window
(`DEFAULT_STALENESS_WINDOW_DAYS`).

If the same epic ticket is discoverable in both scan modes at once (a
transient dual-presence state — e.g. an interrupted Scope-phase move, or a
manual copy), `discover_candidate_epics()` dedupes by `epic_id` before
classification, first-occurrence-wins with the `epic_id`-mode
(`tickets/inprogress/`) candidate preferred, so the epic is reported at most
once rather than double-counted in the stale list or hook nudge.

**Stale vs. never-started — an intentional distinction.** An epic whose
children have **zero activity ever** (no `working_log.csv` row, no
`runs.jsonl` record, for any child, at any time) is **never** flagged stale,
regardless of how old the epic ticket's own `date:` field is. That shape —
scoped and sequenced, then deliberately left queued behind other work — is
normal planning behavior, not abandonment. It is instead surfaced separately
as a lower-priority "Informational: never-started epics" section, visible
only through the directly-queryable surface below, never through the hook
nudge. `TCK-20260702-OBSISO-EPIC` is the concrete real example: zero child
activity ever as of this check's introduction, correctly classified as
never-started rather than stale.

Only an epic with real activity evidence that then goes idle past the window
— the actual "started, then forgotten" failure mode this check targets — is
flagged stale (the motivating case: `TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC`,
whose 10 child tickets were all DONE before the epic ticket itself was left
behind in `tickets/todos/`).

Advisory-only and read-only, matching `retro_nudge_hook.py`'s contract: it
never mutates a ticket file's `Status`/`phase`, never raises past its own
entry point, and never blocks a tool call.

```bash
make agent-monitoring-epic-staleness
```

A `PostToolUse` hook entry (`epic_staleness_check.py --hook`, wired alongside
`retro_nudge_hook.py` in `.claude/settings.json`) fires an `additionalContext`
nudge, at most once per session (own state file,
`.claude/.epic_staleness_state.json`), only when the **stale** list is
non-empty — the never-started/informational list never reaches the hook.

---

## Sidecar Reminder Hook

Hand-orchestrated ticket sessions (no `Workflow` tool available) must
manually replicate `implement-ticket.js`'s `writeSidecar(seq, phase, agent)`
call at each phase transition, writing
`{run_id, seq, phase, agent, execution_id, provider}` to
`.claude/current_run` — this is what lets `post_tool_hook.py` attribute
`tools.jsonl` rows to a run (see "How tool calls are attributed to agent
events" in `docs/agent-monitoring/schema.md`). This step is easy to forget
under hand-orchestration and, when skipped, silently zeroes
`tool_call_count`/`cost_proxy_score` for the affected phase(s)
(`TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP`).

A `PreToolUse` hook entry (matcher `Edit|Write`, in `.claude/settings.json`)
fires an advisory `additionalContext` reminder whenever `tickets/inprogress/`
has an active ticket but `.claude/current_run`'s `run_id` is empty — it goes
silent again as soon as the sidecar is correctly written for that phase.
Advisory-only, non-blocking; does not replace the orchestrating agent's own
responsibility to write the sidecar.

---

## Makefile Targets

```bash
make agent-monitoring-index          # (re)build the derived SQLite index — required by query.py/validate.py
make agent-monitoring-retro          # generate current-week retro report
make agent-monitoring-validate       # cross-check integrity
make agent-monitoring-query          # open interactive query (pass ARGS="...")
make agent-monitoring-epic-staleness # report open epics with no recent child-ticket activity
make agent-monitoring-weight-check   # required before any cost_proxy.py weight change (pass ARGS='--candidate-weights "{...}"')
```

---

## Schema Reference

See `docs/agent-monitoring/schema.md` for full field definitions and join patterns.
