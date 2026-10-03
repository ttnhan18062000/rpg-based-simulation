---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE
artifact_type: investigation
tags: [agent-monitoring, process-improvement]
---

# Investigation — TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE

## Context scan
`mcp__knowledge-search__search_docs` and `graphify query` run first, per CLAUDE.md's mandatory
Context Scan. Surfaced the directly relevant prior work:
- `stored_artifacts/TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT/investigation.md` — built
  `tools/agent-monitoring/done_ticket_monitoring_coverage.py`, the audit this ticket's own Request
  Summary cites. At that time (2026-08-05), 719/1303 done tickets were missing coverage, and the
  investigation concluded the gap was almost entirely historical (before agent-monitoring existed,
  2026-06-07) — a "shrinking rollout tail," not an ongoing problem. It explicitly considered and
  **rejected** a blocking Finalize-time gate, because at that time the coverage script itself
  contained a real bug (reading a stale SQLite index instead of raw `runs.jsonl`) that produced
  false positives against that session's own just-recorded tickets — a blocking gate on top of a
  buggy check would have halted legitimate closes. That bug was fixed in the same ticket (switched
  to reading `runs.jsonl` directly via `load_data_glob`).
- `docs/agent-monitoring/README.md`'s "Done-Ticket Monitoring Coverage Audit" section documents the
  audit tool's existence but not any lightweight recording path for hand-orchestrated work.
- `tools/agent-monitoring/record_run.py` / `record_events.py` — real, already-existing standalone
  CLI tools that append one run record / a batch of event records to the current-week
  `agent-monitoring/data/<ISO-week>/{runs,events}.jsonl` shard. Confirmed working in this session:
  used directly (no `Workflow` tool, no multi-agent dispatch) to record real monitoring coverage
  for this session's own two immediately-preceding hotfix closures
  (`TCK-20260904-HOTFIX-KGMCP-FROZEN-FILE-BASELINE-UPDATE`,
  `TCK-20260818-HOTFIX-PROFILE-SWEEP-EXPORT-TOOL`) — both now show up as `covered` in a fresh audit
  run.

## Is the gap still real, and is it still "mostly historical"?

Ran `tools/agent-monitoring/done_ticket_monitoring_coverage.py` fresh (not trusting the ticket's
own 2-day-old 771/1773 figure):

```
total: 1815
covered: 1017
missing: 798
```

Filtered `missing` to only `TCK-202609*`-prefixed ticket IDs (tickets dated this month, i.e. work
from the last ~3 days, well after agent-monitoring's 2026-06-07 rollout) — **30 tickets**,
including several this session directly observed being closed in `tickets/working_log.csv` earlier
today (`TCK-20260904-HOTFIX-RETRIEVAL-TOOLS-CONSUMERS-DEAD-CONSTANTS`,
`TCK-20260904-HOTFIX-DOCS-SWEEP-TEST-STALENESS`,
`TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK`,
`TCK-20260904-HOTFIX-AGENT-REPLAY-MONITORING-PATH-STALENESS`,
`TCK-20260904-HOTFIX-PARITY-BASELINE-DRIFT-WORLD-085-AND-NEXT-ID`), plus the
`TCK-20260903-MONITORING-*`/`TCK-20260902-MONITORING-*` epic and its own children (the epic that
built the unified weekly-shard restructure is itself missing coverage — the same "founding ticket
predates its own mechanism" pattern TCK-20260805 already found once).

**Conclusion: this is a real, ongoing, live gap — not (only) a shrinking historical tail.** The
2026-08-05 investigation's "shrinking rollout tail, converging toward complete coverage" verdict
was correct for what it measured at the time, but the pattern has not actually converged to zero;
it continues to produce new misses every session that hand-orchestrates a closure without
independently knowing to call `record_run.py`/`record_events.py` itself.

## Root cause: not a tooling gap — a discoverability/requirement gap

The lightweight, standalone recording path the ticket's own Scope Option 1 asks for **already
exists** and already works, with zero new code needed:

```bash
python3 tools/agent-monitoring/record_run.py --data '{"run_id": "<TCK-ID>", "execution_id": "claude-<TCK-ID>-<epoch_ms>", "provider": "claude", "ticket_id": "<TCK-ID>", "start_ts": "...", "end_ts": "...", "workflow": "implement-ticket", "tier": "hotfix", "final_status": "DONE", "agent_count": 6}'
python3 tools/agent-monitoring/record_events.py --data '[{"run_id": "<TCK-ID>", ..., "seq": 1, "phase": "Scope", "agent": "claude", "status": "ok", "summary": "...", "ts": "..."}, ...]'
```

Confirmed directly in this session: these two calls are what actually populated real, valid
coverage for this session's own 2 hand-orchestrated hotfix closures moments ago — no gate rejected
them, `vocabulary.py`'s `"claude"` literal is already a recognized hand-orchestration agent value
(`WORKFLOW_AGENTS["implement-ticket"]`, with an explicit comment confirming it's "the real,
dominant hand-orchestration literal (45 of ~91 non-standard agent values in events.jsonl history,
confirmed via direct query)" — i.e. this exact pattern is already common and already recognized,
just not consistently done).

**Nothing tells a hand-orchestrating session it must do this.** `CLAUDE.md`'s own Hard Rule
("Every implement-ticket workflow run... must record a run entry and at least one event entry")
reads naturally as applying to the formal `Workflow` tool's pipeline, and its "After Work"
checklist has no bullet calling out the hand-orchestrated case specifically. The existing
PreToolUse sidecar-check hook (`.claude/settings.json`, `Edit|Write` matcher) nudges toward writing
`.claude/current_run` when `tickets/inprogress/` has an active ticket — but that only fixes
`tool_call_count`/`cost_proxy_score` attribution on `tools.jsonl` rows (a different, narrower gap
than this ticket's — the file already exists, it's the row-level attribution that's blank); it does
**not** prompt writing an actual `runs.jsonl` run record, which is this ticket's real gap.

## Deciding between Scope's Option 1 vs Option 2

- **Option 1** (give hand-orchestrated closures a lightweight, standalone recording path):
  effectively free to adopt — the path already exists and is proven working. The only real cost is
  documentation + a convenience wrapper to lower friction further (crafting two raw `--data` JSON
  blobs by hand is more error-prone than it needs to be for routine use).
- **Option 2** (teach `done_ticket_monitoring_coverage.py` to recognize an alternate, lower-cost
  signal, e.g. a `working_log.csv` row): the ticket's own Assumptions section already flags the
  real tradeoff — this "weakens the audit's own original guarantee that a `run_id` implies a full
  pipeline run actually happened." Since Option 1's real path costs nothing extra to use (it's
  already used successfully in this very session) and produces a genuinely real record instead of a
  proxy signal, there is no good reason to weaken the audit's guarantee instead.

**Decision: pursue Option 1 only.** Reject Option 2 — the tradeoff it would accept (a weaker
audit guarantee) buys nothing that Option 1 doesn't already provide for free.

## Should this be enforced by a new gate/hook?

Investigated whether to add a new blocking or advisory mechanism (e.g. a PreToolUse/PostToolUse
hook on `tickets/done/` writes, mirroring the existing sidecar-check hook's shape) that would flag
a ticket move into `tickets/done/` lacking a matching `run_id`.

**Decision: do not add a new hook in this ticket.** Two independent reasons:
1. `CLAUDE.md`'s own Definition of Done already states, in plain text, that monitoring records are
   "guaranteed by workflow — **not verified by done-checker**" — an explicit, deliberate boundary.
   Changing that boundary (even just adding an advisory, non-blocking signal at the done-checker or
   hook layer) is a real architectural change to a gate contract, not a documentation fix, and
   deserves its own scoped decision rather than folding it silently into this ticket.
2. `.claude/settings.json` hooks are shared, global config — a change there takes effect
   immediately for every concurrent session on this machine, not just this one (confirmed via
   `ps aux`/`git worktree list` that 3+ other sessions are actively running RPG-core and
   agent-design work right now). That is a materially larger blast radius than a source-file change
   scoped to this ticket's own files, and warrants more deliberate review than a single-session
   hotfix-adjacent standard ticket should decide unilaterally.

This is recorded as a real, deliberate scope boundary (per the ticket's own Acceptance Criteria
wording, "a decision is recorded" — not necessarily "a gate is built") and flagged as a documented
follow-up recommendation in the Completion Summary, not silently dropped.

## Historical backfill decision

798 currently-missing entries, the vast majority still attributable to the same 2026-08-05
investigation's rollout-timeline finding (pre-2026-06-07 monitoring didn't exist; adoption tail
through mid-2026). **Decision: do not backfill.** Matches the already-established precedent
(`TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT`'s own explicit rejection): fabricating
`runs.jsonl` records for work that happened before or without real monitoring instrumentation would
create data the real events never generated, which CLAUDE.md's Durable State Rule and this
project's own established precedent both forbid. The 30 live 2026-09 misses are a different
category — not backfilled either (same reasoning), but expected to stop recurring once the fix
below lands and is followed going forward.

## Branch-named isolation-folder question (Scope's third bullet)

The 2026-09-03 branch-named isolation folder pattern this ticket's Request Summary references
(`agent-monitoring/<branch>/` instead of the canonical files, used temporarily because another
session was mid-restructure on `agent-monitoring/tools.jsonl`) is now moot: PR #112/#120 (`Unify
agent-monitoring runs/events/tools into weekly shards`, `agent-monitoring: fold 5 legacy per-ticket
subfolders into unified weekly shards`) already landed and removed the legacy per-ticket-subfolder
pattern entirely, replacing it with the current `agent-monitoring/data/<ISO-week>/{runs,events,tools}.jsonl`
shard convention. Confirmed via `git log --oneline` on `main` — both PRs are already merged. No
further decision needed here; noted as resolved by already-completed, unrelated work.

## Files that will change
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` (new) — thin convenience wrapper
  over `record_run.py`/`record_events.py`, reducing the two-call raw-JSON recipe above to one call
  with sensible defaults.
- `tests/tools/test_record_hand_orchestrated_closure.py` (new) — unit tests for the wrapper.
- `CLAUDE.md` — new "After Work" bullet requiring hand-orchestrated closures to call the wrapper
  (or the two underlying tools directly), matching the Workflow pipeline's own existing
  requirement.
- `docs/agent-monitoring/README.md` — new subsection documenting the lightweight recording path,
  the real CLI recipe, and the wrapper.
