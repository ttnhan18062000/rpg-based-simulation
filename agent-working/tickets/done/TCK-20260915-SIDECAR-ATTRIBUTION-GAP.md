---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-SIDECAR-ATTRIBUTION-GAP
phase: done
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# TCK-20260915-SIDECAR-ATTRIBUTION-GAP

## Title
23.7% of tool rows carry neither `run_id` nor phase, and `cost_proxy_score` is recorded on only 30.5% of events — every spend table is computed on a fraction of real volume

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Measured over the 2026-09-01 → 2026-09-15 window:

| Signal | Value |
|---|---|
| tool rows in window | 50,696 |
| rows with **no `run_id`** | 12,033 (23.7%) |
| rows with **no phase** | 12,033 (23.7%) |
| rows missing **both** | 12,033 (23.7%) |
| events in window | 1,897 |
| events with a nonzero `cost_proxy_score` | 579 (30.5%) |

The identical counts are not a coincidence — it is the *same* set of rows missing both fields,
landing in a single `<MISSING>` bucket that is by far the largest "run" in the corpus.

**Cause is known and already documented**: `.claude/current_run` is a single shared sidecar file
across all concurrent sessions
(`project_sidecar_cross_session_contamination`, confirmed live 2026-08-24). With several sessions
running simultaneously all week — as happened throughout 2026-09-11→15 — rows written while the
sidecar is absent, stale, or owned by another session cannot be attributed.

**Consequence:** `RETRO-LAST14D.md`'s Spend-Proxy-by-Phase and Spend-Proxy-by-Agent tables are a
*ranking*, not a measure of spend. They cannot answer "what does a ticket cost", which is the
question the cost proxy was built to answer
(`TCK-20260708-AGENT-COST-OBSERVABILITY`). This is also the largest single lever in the epic: fixing
it makes several other reports trustworthy rather than indicative.

## Scope
- Determine why the rows lose attribution: sidecar absent, sidecar owned by another session,
  hook firing outside a run, or interactive (non-workflow) tool calls that legitimately have no run.
  The last case is important — a large share may be *correctly* unattributed, and if so the metric
  should exclude them rather than count them as loss.
- Decide whether per-session sidecar isolation is feasible (a per-session path, a lock, or an
  identifier carried on the hook's own environment) versus accepting a documented floor.
- Make the reports honest either way: if a share of volume is unattributable by design, the spend
  tables should say what they cover rather than presenting a total.

## Out of Scope
- Retroactively attributing historical rows.
- `tool_call_count` disagreeing with actual row counts — that is
  `TCK-20260915-TOOL-CALL-COUNT-MISMATCH`, which may share this cause but must be confirmed, not
  assumed.

## Acceptance Criteria
- [x] The unattributed rows are classified into "legitimately has no run" versus "lost attribution
      that should have been recorded", with counts for each. (2 of 10 sessions are 100%
      unattributed/legitimate; the remaining 72% of unattributed volume comes from sessions that
      also did real, attributed ticket work — direct sampling confirms real file-edit content, not
      noise. See investigation.md; a clean per-row split isn't possible without deeper tracing this
      ticket doesn't have the tooling for, disclosed rather than forced.)
- [x] A disposition is recorded for the second category: fix, or accept with a documented floor.
      (Accept with a ratcheted floor — see Completion Summary for why a structural fix is out of
      this ticket's scope.)
- [x] `generate_retro.py`'s spend sections state their coverage (e.g. "computed over N% of tool
      rows") rather than presenting an unqualified total.
- [x] Any detector ratchets from the measured baseline; it must not assert zero. (Floor ratchet,
      75.3% — the mirror image of a ceiling ratchet, disclosed as such since it's the first of this
      shape in the batch.)

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)
- `TCK-20260915-TOOL-CALL-COUNT-MISMATCH` — probable shared cause
- `TCK-20260708-AGENT-COST-OBSERVABILITY` (done) — introduced `cost_proxy_score`
- `TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION` (blocked by design — needs a real
  `implement-epic` run, which must not be triggered artificially)

## Related Docs
- `agent-monitoring/retro/RETRO-LAST14D.md`
- `docs/agent-monitoring/schema.md`
- `docs/guides/agent_monitoring.md`

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `.claude/current_run` (the shared sidecar)
- `.claude/settings.json` (the `PostToolUse` hook that writes `tools.jsonl`)
- `tools/agent-monitoring/record_events.py` (`compute_tool_stats`)
- `tools/agent-monitoring/generate_retro.py` (spend sections)

## Assumptions / Open Questions
- **A meaningful share of the 12,033 may be correct.** Interactive tool calls outside any workflow
  run have no run to belong to. Do not treat the whole figure as loss before classifying it — that
  would overstate the defect.
- Whether a per-session sidecar is achievable given that the hook has no session identifier is the
  real design question.

## Implementation Notes
Derived from the JSONL shards directly, matching the ticket's own instruction.

**The stated cause was stale.** Reading `post_tool_hook.py` directly showed the exact
cross-session-contamination bug named in the Request Summary was already fixed on the same day it
was found (`TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` + `TCK-20260824-SIDECAR-ADHOC-NULL-
ATTRIBUTION`). The live 24.7% gap has a different, more nuanced shape: uniform ~21-33% unattributed
rate across every tool type (rules out a tool-specific timing race), and direct sampling of
unattributed `Edit`/`Write` rows shows real ticket-implementation file edits, not interactive noise.
Most plausible mechanism: hand-orchestration sessions not calling `writeSidecar()` for every phase
(CLAUDE.md's own documented "single most common hand-orchestration gap"), possibly compounded by a
subagent-vs-orchestrator session-id mismatch (disclosed as an open hypothesis, not confirmed to the
same certainty — recorded for the capstone or a follow-up, not silently dropped).

**Confirmed the link to `TCK-20260915-TOOL-CALL-COUNT-MISMATCH`** (not just "probable," per that
ticket's own AC): `record_events.py::compute_tool_stats()` groups tool rows by `(run_id, seq)`, so
an unattributed tool row can never match any event, by construction — the identical mechanism
drives both this ticket's `cost_proxy_score` coverage gap and (very likely) ticket 3's
`tool_call_count` mismatches. Ticket 3 should build on this rather than re-deriving it.

## Test Summary
- `tests/tools/test_generate_retro.py` — extended with 4 new tests (coverage computed correctly,
  `None` when no events, note rendered when scored events exist, note omitted when the whole
  spend-proxy section is skipped); 1 pre-existing exhaustive-keys test updated to include the new
  `spend_proxy_coverage` key. Full file: 156 passed.
- `tests/tools/test_sidecar_attribution_coverage_check.py` (new, 8 tests) — floor pass/fail, the
  14-day window boundary, floor-may-only-increase pin, real-corpus check, Makefile wiring.
- `make sidecar-attribution-coverage-check` confirmed end-to-end against the real corpus: PASS.

## Files Changed
- `tools/agent-monitoring/generate_retro.py` — `compute_retro_metrics()` gained
  `spend_proxy_coverage`; `generate()` renders a coverage note above the Spend Proxy tables.
- `tools/gate_checks/sidecar_attribution_coverage_check.py` (new) — floor ratchet, 75.3%.
- `tests/tools/test_generate_retro.py` (extended), `tests/tools/test_sidecar_attribution_coverage_check.py` (new).
- `Makefile` — `sidecar-attribution-coverage-check` target + `.PHONY` entry.

## Completion Summary
Disposition: accept with a documented, ratcheted floor, not fix. Investigation ruled out the
ticket's own stated cause (already fixed weeks earlier) and classified the live gap directly rather
than assuming its shape: uniform per-tool-type rate and real-file-edit sampling both point to
genuine, in-principle-attributable ticket work lacking sidecar coverage, not legitimate interactive
noise — but a full per-row classification would need per-session tracing beyond this ticket's
practical scope, disclosed as a limit rather than forced into a false-precision split. A structural
fix (guaranteeing 100% hand-orchestration compliance, or redesigning session-id threading through
subagent dispatch) is a cross-cutting architecture change out of this ticket's reasonable scope.
Shipped the concrete, unambiguous win instead: `generate_retro.py`'s spend tables now disclose their
own coverage explicitly, and a floor ratchet (the batch's first "coverage percentage" ratchet,
shaped as the mirror image of every other check's ceiling ratchet) catches future regression.
Confirmed (not just flagged) the shared-cause link to `TCK-20260915-TOOL-CALL-COUNT-MISMATCH` via
direct code reading of `compute_tool_stats()`'s own `(run_id, seq)` grouping logic.
