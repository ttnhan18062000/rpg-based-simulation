---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION
phase: open
date: 2026-07-28
tags: [agent-monitoring, data-quality, root-cause, bug]
---

# TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION

## Title
Pause/resume across separate sessions silently aliases `tool_call_count`/`cost_proxy_score` onto stale `(run_id, seq)` buckets

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`agent-monitoring/tools.jsonl` groups tool calls by `(run_id, seq)` only. `seq` is a per-*session*
phase counter inside `.claude/workflows/implement-ticket.js` that starts at 1 on every invocation.
When a ticket's run is paused mid-pipeline and resumed later as a **separate session** under the
same `run_id`, the new session's counter also restarts at 1 — so its phases silently alias onto
whichever `(run_id, seq)` buckets the original (pre-pause) session already wrote.

Confirmed concretely on `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` (paused mid-Implement per its
own event summary `"PAUSED by user request mid-Step-7"`, resumed in a later session per
`"resuming mid-implementation at Step 7"`). Comparing `events.jsonl`'s reported `tool_call_count`
against `tools.jsonl` ground truth for that run:

| seq | ground truth | 1st-session phase (reported) | 2nd-session phase (reported) |
|---|---|---|---|
| 2 | 61 | Investigate: 61 | Implement: **61** |
| 3 | 19 | Plan: 19 | Architecture-Verify: **19** |
| 4 | 25 | Review (failed): 25 | Test: **25** |
| 5 | 10 | Review (ok): 10 | Parity: **10** |
| 6 | 114 | Implement (paused): 112 | Verify (failed): **114** |

Every resumed-session phase from seq 2 onward reports the exact same `tool_call_count`/
`cost_proxy_score` as the pre-pause session's phase at that seq (e.g. `cost_proxy_score:28601.745`
appears twice, under two unrelated phase labels). The resumed session's real work received zero
authentic attribution — this is what produced the 28-day retro's ~450-470x cost-proxy "outliers"
for this ticket; not real cost, a monitoring artifact.

Blast radius, checked directly against the live corpus: 8 `run_id`s show more than one `seq=1`
`Scope`-phase entry (the signature of a multi-invocation/resumed run and therefore a candidate for
this collision) — `TCK-20260719-LIVE-PHASE-AGENT-LABEL` (4 invocations),
`TCK-20260623-DEAD-CODE-REMOVAL`, `TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION`,
`TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT`,
`TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING`, `TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME`,
`TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`, and this ticket's own subject (2 each unless
noted). Bounded (a few percent of sampled runs) but real, silent, and undermines retro cost-ranking
conclusions specifically for the more complex/notable tickets — the ones most likely to need a pause.

This is a **third, distinct mechanism**, not a regression of the already-fixed
`TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` (closed 2026-07-11, before this ticket's own
run happened). That ticket fixed two deterministic *within-session* gaps (a Scope-phase sidecar
gap, and `writeMonitoring` self-pollution) and explicitly ruled out concurrency/cross-session
causes as its root mechanism. This ticket's collision only fires across two genuinely separate
workflow invocations sharing one `run_id` — a case that ticket's investigation never covered.

Full analysis: `docs/plans/idea_agent_monitoring_pause_resume_seq_collision.md`.

## Scope
- Investigate/Plan phase decides between the candidate fixes named in the linked idea doc (resume-aware `seq` continuation reading prior max seq from `events.jsonl`/`tools.jsonl` for the run_id; or a genuinely unique per-invocation attribution key) — not pre-decided here.
- Fix `.claude/workflows/implement-ticket.js`'s resume path (the "load existing ticket, resume mid-pipeline" branch) so a resumed session cannot write to a `(run_id, seq)` bucket a prior session already used.
- Extend `tools/agent-monitoring/validate.py`'s `compute_tool_count_drift_report()` (built by the sibling ticket) with a check that specifically identifies this mechanism (multi-invocation `run_id` collision) distinct from the two mechanisms it already detects, so a future recurrence is diagnosed automatically rather than requiring another manual investigation.
- Update `docs/agent-monitoring/schema.md`'s "How tool calls are attributed to agent events" section to document this third mechanism and its fix, alongside the two `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` already documented there.

## Out of Scope
- Backfilling or correcting historical corrupted `tool_call_count`/`cost_proxy_score` values — same append-only precedent the sibling ticket already established in `docs/agent-monitoring/schema.md`'s Known Limitations. Prevention-only.
- Redesigning `cost_proxy_score`'s weighting formula (`tools/agent-monitoring/cost_proxy.py`) — unaffected in principle; it's fed corrupted input for these specific runs, not itself wrong.
- The separate, already-documented wall-clock duration contamination from session pauses (naive `duration_s = end_ts - start_ts` including idle gaps) — that is a different bug with its own plan doc, `docs/plans/idea_agent_monitoring_active_duration.md`. Do not fold the two fixes together; they touch different fields and different consumers even though both stem from the same underlying pause/resume behavior.
- Whether `implement-epic`'s per-child dispatch has an analogous issue — flagged as an open question in the linked idea doc, not assumed in or out of scope here without investigation.

## Acceptance Criteria
- [ ] Root cause mechanism confirmed and documented precisely (which code path in `implement-ticket.js` causes the resumed session's `seq` to restart at 1 and collide with the prior session's `tools.jsonl` buckets)
- [ ] Resumed sessions can no longer write tool-call attribution into a `(run_id, seq)` bucket a prior session already populated — verified against a reproduction of the `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`-shaped scenario (pause mid-pipeline, resume in a new session)
- [ ] `compute_tool_count_drift_report()` (or a new sibling function) can detect this specific mechanism (multi-invocation seq collision) and distinguish it from the two mechanisms the sibling ticket's version already covers
- [ ] `docs/agent-monitoring/schema.md` updated with the third mechanism and its fix
- [ ] Existing `tests/tools/test_current_run_sidecar_orchestrator.py` and `tests/tools/test_validate_agent_monitoring.py` suites still pass; new tests cover the resume-collision fix and its detection directly

## Related Tickets
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION (done — direct precedent, same failure class, same fix location, same validation-tooling home; read its Implementation Notes first)
- TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION (done — the concrete instance this ticket was discovered from; no changes needed to that ticket itself, it already closed correctly)
- TCK-20260708-AGENT-COST-OBSERVABILITY (introduced `cost_proxy_score`, which inherits this corruption via the same grouped `tools.jsonl` rows)
- TCK-20260705-MONITORING-RUNID-JOIN (prior empirical audit of `runs.jsonl`/`events.jsonl` join integrity — same investigative pattern, different field)

## Related Docs
- docs/plans/idea_agent_monitoring_pause_resume_seq_collision.md (full analysis this ticket implements)
- docs/plans/idea_agent_monitoring_active_duration.md (sibling finding, same investigation session, different bug)
- docs/agent-monitoring/schema.md ("How tool calls are attributed to agent events", Known Limitations)
- docs/guides/agent_monitoring.md

## Related Stored Artifacts
N/A yet — created at this ticket's own Investigate/Plan phase.

## Related Code Areas
- `.claude/workflows/implement-ticket.js` (resume/"load existing ticket" branch, `writeSidecar`, `writeMonitoring`)
- `tools/agent-monitoring/post_tool_hook.py` (sidecar read)
- `tools/agent-monitoring/validate.py` (`compute_tool_count_drift_report`, natural home for the new check)
- `tools/agent-monitoring/cost_proxy.py` (consumer of the corrupted grouping, unaffected in formula itself)

## Assumptions / Open Questions
- Whether `max(seq) + 1` continuation is sufficient on its own, or needs a race-safety argument for a third resume of the same ticket — see linked idea doc's Open Questions.
- Whether `implement-epic`'s per-child-ticket dispatch has an analogous exposure — not assumed either way, needs its own check during Investigate.
- Whether the fix should extend the existing sidecar-write mechanism or add a purely additive "look up max prior seq" read without touching sidecar semantics.

## Implementation Notes
(filled in during Implement phase)

## Test Summary
(filled in during Test phase)

## Files Changed
(filled in during Implement phase)

## Completion Summary
(filled in at Finalize)
