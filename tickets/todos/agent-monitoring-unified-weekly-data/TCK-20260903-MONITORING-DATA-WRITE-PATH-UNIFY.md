---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY
phase: open
date: 2026-09-03
tags: [agent-monitoring, observability, hooks, data-quality]
---

# TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY

## Title
Cut over `record_run.py`/`record_events.py`/`post_tool_hook.py` to the unified
`agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` per-week folder, and fix
`record_events.py`'s live, silently-broken `TOOLS_FILE` ground-truth read

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 1 of `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`, must land **first** in the batch. Two
things happen in this one ticket because they are the same class of fix at the same call sites:

**1. Write-path unification.** Today: `post_tool_hook.py` writes `tools` rows to
`agent-monitoring/tools/tools-YYYY-Www.jsonl` (prior epic's shape); `record_run.py` writes `runs`
rows to a monolithic `agent-monitoring/runs.jsonl` (`RUNS_FILE`, line 13); `record_events.py` writes
`events` rows to a monolithic `agent-monitoring/events.jsonl` (`EVENTS_FILE`, line 16). All 3 must
target the corrected shape: `agent-monitoring/data/<current-ISO-week>/{runs,events,tools}.jsonl`.

**2. URGENT bug fix (this is not a side note — treat it as the highest-priority item in this
ticket).** `record_events.py` also hardcodes `TOOLS_FILE = Path("agent-monitoring/tools.jsonl")`
(line 17) and reads it directly (`load_jsonl(TOOLS_FILE)`, lines 59-60, feeding
`_compute_tool_stats_by_key()`) to deterministically compute `tool_call_count`/`cost_proxy_score` for
every event it writes (see `docs/agent-monitoring/schema.md` lines 151, 382 for the documented
contract). That path was `git rm`'d by the prior epic's `TCK-20260902-MONITORING-SHARD-MIGRATION` on
2026-09-02 and has been permanently empty ever since (`TOOLS_FILE.exists()` is `False` — a silent
degrade, not a crash). **Every real `implement-ticket.js`-orchestrated run since 2026-09-02 has
gotten `tool_call_count=0`/wrong `cost_proxy_score` on its events.** Fixing this at the same time as
the write-path cutover is natural: both are "point the `tools` read/write at the right current
location" work, and this ticket's own write-path change is what makes the fix's own test corpus
exist to test against.

**Design note carried from investigation, not yet resolved — implementer must decide and document:**
before this epic, `record_events.py`'s `TOOLS_FILE` read was a *full-corpus* read of the entire
historical `tools.jsonl` (it was the only file that ever existed). The correct read for
`compute_tool_stats()` to match `(run_id, seq)` ground truth is therefore the **union of every week
folder's `tools.jsonl`**, not just the current week's — a paused/resumed run (see
`TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`) can have tool-call rows in an earlier week than
the event being written now. Globbing all weeks is not a new performance cost; it restores the
original pre-sharding read scope, which already read the entire file every time.

## Scope
- `tools/agent-monitoring/post_tool_hook.py`: change the write target from
  `agent-monitoring/tools/tools-<week>.jsonl` (prior epic's shape) to
  `agent-monitoring/data/<week>/tools.jsonl` (this epic's unified shape). Reuse the existing
  `now_dt = datetime.now(timezone.utc)` / `iso_week = now_dt.strftime("%G-W%V")` computation
  unchanged (lines 56-60) — only the target path template changes.
- `tools/agent-monitoring/record_run.py`: replace `RUNS_FILE = Path("agent-monitoring/runs.jsonl")`
  (line 13) with a write-time ISO-week computation (reuse or duplicate the `%G-W%V` pattern —
  implementer's choice, matching the prior epic's Decision 3 precedent for `post_tool_hook.py`)
  targeting `agent-monitoring/data/<week>/runs.jsonl`. Document explicitly (see Assumptions) whether
  bucketing uses write-time ("now", consistent with `post_tool_hook.py`'s existing precedent) or the
  record's own `start_ts` field — recommended default is write-time, for consistency with the other
  2 sources' existing precedent, but this is the implementer's call to make and record.
- `tools/agent-monitoring/record_events.py`:
  - Replace `EVENTS_FILE = Path("agent-monitoring/events.jsonl")` (line 16) with the same write-time
    ISO-week computation targeting `agent-monitoring/data/<week>/events.jsonl`.
  - **Fix the critical bug**: replace `TOOLS_FILE = Path("agent-monitoring/tools.jsonl")` (line 17)
    with a glob over `agent-monitoring/data/*/tools.jsonl` (all week folders, sorted), concatenated
    before being passed into `_compute_tool_stats_by_key()` — restoring full-corpus read scope, per
    the design note above.
- Continue routing every append through `tools/agent-monitoring/writer.py::write_line()`/
  `write_lines()` unmodified — confirm (don't assume) its `target_path.parent.mkdir(parents=True,
  exist_ok=True)` call correctly creates the new nested `agent-monitoring/data/<week>/` directory on
  first write for each of the 3 sources.
- Extend `.gitattributes` with a `merge=union` entry for the new unified glob (e.g.
  `agent-monitoring/data/*/*.jsonl merge=union`), **keeping** the 3 existing lines
  (`agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`,
  `agent-monitoring/tools/*.jsonl merge=union`) in place during this ticket — child 2 (migration)
  removes them once the old paths are retired, matching the prior epic's precedent exactly.
- Update the write-path language in `docs/agent-monitoring/schema.md`'s per-source sections
  (minimal, targeted paragraph edits only — the broader consumer-facing doc sweep is child 7's scope,
  matching the prior epic's own child-1/child-3 split).
- Preserve every hook/script's existing fail-silent or fail-loud contract exactly as it is today —
  `post_tool_hook.py`'s outer `try/except Exception: pass` must continue to swallow any new-path
  computation failure exactly like every other failure mode already handled there.

## Out of Scope
- Migrating the existing monolithic `runs.jsonl`/`events.jsonl` content or the prior epic's already-
  sharded `tools/tools-YYYY-Www.jsonl` files into the new layout — that is
  `TCK-20260903-MONITORING-DATA-MIGRATION` (child 2).
- Any other consumer's read path (`build_index.py`, `generate_retro.py`, `manifest.py`,
  `seq_offset.py`, `weight_sensitivity_check.py`, `retro_nudge_hook.py`,
  `done_ticket_monitoring_coverage.py`, `validate.py`, `query.py`, `done_checker_static.py`,
  `agent_ops_dashboard/ingest.py`) — those are children 3 and 4. A known, accepted transient gap:
  after this ticket alone lands, new rows are invisible to those readers until children 3/4 land —
  acceptable because they land immediately after per `SEQUENCE.md`, not as a standalone release.
- Removing the historical monolithic files or the old `tools/` shard directory from the working tree
  — they stay present (frozen, receiving no more appends after this ticket's cutover) until child 2.
- The codex-runtime-activation subsystem (`tools/agent_replay_codex/monitoring_shards.py` and its
  call sites) — that is child 5.
- Referential-integrity verification tooling — that is child 6.
- The broader docs/CLAUDE.md/skill sweep beyond the minimal write-path paragraph in `schema.md` —
  that is child 7.
- Any change to `writer.py`'s locking protocol or the 3 per-line record schemas.

## Acceptance Criteria
- [ ] A test (mocked/frozen "now") asserts `post_tool_hook.py` appends its record to
      `agent-monitoring/data/<expected-ISO-week>/tools.jsonl`, never to
      `agent-monitoring/tools/tools-*.jsonl` or `agent-monitoring/tools.jsonl`.
- [ ] Equivalent tests for `record_run.py` (→ `data/<week>/runs.jsonl`) and `record_events.py`
      (→ `data/<week>/events.jsonl`).
- [ ] A test asserts writes in two different mocked ISO weeks land in two distinct week folders for
      all 3 sources.
- [ ] **Regression test proving the critical bug is fixed**: seed `tools` ground-truth rows across 2+
      week folders (including one week different from the event being written, simulating a
      paused/resumed session per `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`'s precedent),
      then assert `record_events.py` computes a correct nonzero `tool_call_count`/`cost_proxy_score`
      for a `(run_id, seq)` pair whose matching tool-call rows live in a non-current week folder — not
      just that the current-week case works.
- [ ] Existing single-writer/concurrent-writer/fail-silent tests for all 3 scripts (from
      `TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK`/the prior epic) still pass against the new
      paths.
- [ ] `.gitattributes` contains the new unified-glob `merge=union` entry; the 3 legacy lines remain
      present (removed by child 2, not this ticket).
- [ ] `docs/agent-monitoring/schema.md`'s per-source sections describe the new per-ISO-week write
      path.
- [ ] No functional change to `tools/agent-monitoring/writer.py`.

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (parent epic)
- TCK-20260903-MONITORING-DATA-MIGRATION (child 2 — depends on this ticket landing first)
- TCK-20260903-MONITORING-DATA-CONSUMERS-CORE, -CONSUMERS-GATES-DASHBOARD (children 3, 4 — depend on
  child 2, which depends on this ticket)
- TCK-20260902-MONITORING-SHARD-WRITE-PATH — established the `%G-W%V` ISO-week write-path precedent
  and the fail-silent contract this ticket extends to `runs`/`events` and re-shapes for `tools`.
- TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION — confirms cross-week-boundary `(run_id, seq)`
  matching is a real, already-encountered scenario, directly motivating this ticket's full-corpus-glob
  fix for `record_events.py`'s `TOOLS_FILE` read.
- TCK-20260719-COST-PROXY-WRITE-PATH / TCK-20260719-LIVE-PHASE-AGENT-LABEL — established the
  `tool_call_count`/`cost_proxy_score` deterministic-computation contract this ticket's bug fix
  restores.

## Related Docs
- `docs/agent-monitoring/schema.md` — per-source write-path paragraphs.
- `docs/agent-monitoring/schema.md` lines 151, 382 — the documented `tool_call_count`/
  `cost_proxy_score` computation contract this ticket's bug fix must keep satisfying.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260902-MONITORING-SHARD-WRITE-PATH/` (if present) and
  `stored_artifacts/TCK-20260721-MONITORING-WRITER-UNIFICATION/` — `writer.py`'s design rationale,
  reused unmodified.

## Related Code Areas
- `tools/agent-monitoring/post_tool_hook.py` (line ~159, target path)
- `tools/agent-monitoring/record_run.py` (line 13, `RUNS_FILE`)
- `tools/agent-monitoring/record_events.py` (lines 16-17, `EVENTS_FILE`/`TOOLS_FILE`; lines 59-60,
  the read call)
- `tools/agent-monitoring/writer.py` (read-only reference; not modified)
- `.gitattributes`
- `docs/agent-monitoring/schema.md`
- `tests/tools/test_post_tool_hook.py`, `tests/tools/test_record_run.py`,
  `tests/tools/test_record_events.py`

## Assumptions / Open Questions
- `runs.jsonl` write-time bucketing vs. `start_ts`-field bucketing is left to the implementer's
  judgment (see Scope) — recommended default is write-time for consistency with the other 2 sources'
  existing precedent; must be documented either way.
- Assumes UTC is the correct timezone for all 3 sources' ISO-week computation, matching existing
  `datetime.now(timezone.utc)` usage throughout this subsystem.
- The critical bug fix's full-corpus glob for `record_events.py`'s `TOOLS_FILE` read is recommended
  over a current-week-only glob specifically because of the pause/resume cross-week scenario — an
  implementer choosing a narrower scope must justify it against that scenario, not silently pick the
  cheaper option.
- `layer: observability` matches this repo's established pattern for all `agent-monitoring/` tooling
  tickets.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
