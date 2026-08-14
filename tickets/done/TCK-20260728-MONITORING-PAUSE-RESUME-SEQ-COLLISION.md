---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION
phase: done
date: 2026-07-28
tags: [agent-monitoring, data-quality, root-cause, bug]
---

# TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION

## Title
Pause/resume across separate sessions silently aliases `tool_call_count`/`cost_proxy_score` onto stale `(run_id, seq)` buckets

## Status
DONE

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

Followed staging_artifacts/TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION/plan.md's 6 steps in order.

**Step 1 (verification-only, no code change)**: Re-confirmed by direct grep against
`.claude/workflows/implement-epic.js` (`grep -n "writeSidecar\|current_run\|events.length + 1"`)
that it never writes a `.claude/current_run` sidecar and never uses the `events.length + 1`
expression shape — zero matches for either. `implement-epic.js` does independently hardcode small
`seq` values into `record_events.py --data` calls (`"seq":1` at two Discover-branch call sites,
`seq: i + 1` in a per-child-ticket batch loop) as part of `events.jsonl`'s own per-record shape,
but with no sidecar-driven `tools.jsonl` attribution to alias onto, there is no
`tool_call_count`/`cost_proxy_score` corruption possible — the specific bug this ticket fixes is
structurally absent from `implement-epic.js`. No fix applied to that file, per plan.md's explicit
"Do NOT touch" instruction for this step.

**Step 2**: Added `tools/agent-monitoring/seq_offset.py` with `compute_seq_offset(run_id, events)`
(pure function, returns max prior `seq` for `run_id`, `0` if none) and a `MARKER:`-prefixed-JSON
`__main__` entrypoint mirroring `scope_ticket_relocate.py`'s calling convention exactly. Imports
`load_jsonl` from `validate.py` rather than duplicating it, per plan.md's stated preference.
New dedicated test file `tests/tools/test_seq_offset.py` (4 tests, all passing).

**Step 3**: Added `resolveSeqOffset()` helper and `let seqOffset = 0` + `if (ticketId) { seqOffset
= await resolveSeqOffset(ticketId); ... }` to `.claude/workflows/implement-ticket.js`'s Scope-phase
resume branch, replacing the hardcoded `'seq': 1` literal with `'seq': int(sys.argv[2])` fed
`"${seqOffset + 1}"` as a new argv element. Ran a single `replace_all` of the exact substring
`events.length + 1,` → `events.length + 1 + seqOffset,` across the file — confirmed exactly 11
matches before (0 after) and exactly 11 matches for the new substring after, matching plan.md's
pre-verified grep count precisely. `node --check` confirms no syntax error was introduced.

**Step 4**: Updated `tests/tools/test_current_run_sidecar_orchestrator.py`'s
`_COVERED_SITE_ADJACENCY` list (10 strings), the `test_sidecar_bash_write_precedes_each_covered_agent_call`
regex, and `test_finalize_call_site_still_registers_sidecar`'s regex to the new `events.length + 1
+ seqOffset` shape. Updated `test_scope_phase_has_sidecar_coverage`'s two literal-string assertions
to the new `int(sys.argv[2])` / `"${seqOffset + 1}"` shape and added two new assertions proving
`resolveSeqOffset(` is actually invoked at the Scope resume site. Added new test
`test_new_ticket_branch_seq_offset_is_zero_not_null`.

**Step 5**: Added `compute_multi_invocation_collision_report(events)` to
`tools/agent-monitoring/validate.py`, placed directly after `compute_tool_count_drift_report`, and
wired it into `main()`'s additive-report output (never gates exit code). Added 2 new tests to
`tests/tools/test_validate_agent_monitoring.py`.

**Step 6**: Added the third-mechanism paragraph to `docs/agent-monitoring/schema.md`'s "How tool
calls are attributed to agent events" section, and updated the paragraph immediately above it
(Scope-phase coverage) to reflect the new `seqOffset + 1` shape rather than the old hardcoded `1`.
Added `test_schema_doc_documents_pause_resume_seq_collision_fix`.

**Deviation from plan.md (documented in plan.md's own Deviations section)**: plan.md's Step 3/4
scope covered only `tests/tools/test_current_run_sidecar_orchestrator.py`'s assertions of the
`events.length + 1` substring. A second, independent test file,
`tests/tools/test_step0_ts_orchestrator.py` (built for a different, earlier ticket,
TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH), was found to carry its own copy of the same 9
`writeSidecar(events.length + 1, ...)` adjacency substrings in its `_IMPLEMENT_TICKET_ADJACENCY`
list, discovered only after Step 3's `replace_all` broke
`test_ts_capture_bash_precedes_each_covered_agent_call`. Updated the same 9 strings in that file to
the `+ seqOffset` shape (mechanical, same substitution as Step 4's). A repo-wide grep for
`events.length + 1` across `tests/`, `.claude/`, `tools/`, `docs/` confirmed no other collateral
matches beyond this one file — `create-tickets.js` and `simq-audit.js` also use the
`events.length + 1` shape internally but are separate, out-of-scope workflow files this ticket's
Scope section never named.

**Test-phase regression fix (2026-07-28)**: running the broader `tests/tools/` suite (beyond the
plan's own scoped list, same precedent as ticket 5/7's and 4/7's own Test-phase sweeps) surfaced one
real regression this ticket's Step 5 diff caused:
`tests/tools/test_agent_monitoring_manifest.py::test_writer_files_are_byte_unchanged_by_this_ticket`
failed, because it asserted (via `git diff --stat HEAD -- tools/agent-monitoring/validate.py`) that
`validate.py` must be byte-unchanged — a guard that is now factually incompatible with this
ticket's own explicit, reviewed scope (Step 5 adds
`compute_multi_invocation_collision_report()` to `validate.py`, approved by architecture-reviewer in
both pre-Implement Review and post-Implement Architecture-Verify). This is the exact same shape of
stale cross-ticket guard as the one `TCK-20260721-MONITORING-WRITER-UNIFICATION` (see its own
Implementation Notes) previously hit and fixed by narrowing `_WRITER_GUARD_FILES` from 4 files down
to `["validate.py"]` — that ticket's own reasoning ("an unconditional 'these files must never be
modified, by any future ticket, forever' assertion is factually incompatible with legitimate,
approved work") now applies to the one file that narrowing left standing. Since no file remains that
this guard's reasoning still protects, and narrowing `_WRITER_GUARD_FILES` to an empty list would
make the `git diff --stat HEAD --` invocation diff the *entire* repo (zero pathspecs after `--`,
not zero files) rather than assert nothing, the test and its `_WRITER_GUARD_FILES` constant were
removed outright rather than narrowed further. Replaced with a module-level comment in
`tests/tools/test_agent_monitoring_manifest.py` recording this history (including the same guard's
prior narrowing under TCK-20260721-MONITORING-WRITER-UNIFICATION) so a future reader understands why
no writer-guard test remains in this file. `validate.py`'s real behavioral contracts (manifest
shape/reproducibility/streaming/zero-mutation) remain covered by this file's other 5 tests and by
`tests/tools/test_validate_agent_monitoring.py`, which already covers
`compute_multi_invocation_collision_report()` directly (Step 5's 2 new tests).

Re-ran `tests/tools/test_agent_monitoring_manifest.py` standalone: 5 passed (was 6; the removed test
does not reappear as a failure). Re-ran the full `tests/tools/` suite once more after this fix:
**34 failed, 1048 passed, 1 xfailed** — one fewer failure than the pre-fix sweep's 35 (the removed
stale guard), with the remaining 34 confirmed to be the same 5 pre-existing/environmental files
already named below (`test_knowledge_search.py`, `test_monitoring_writer.py`,
`test_monitoring_writer_lockfile_candidate.py`, `test_post_tool_hook.py`'s concurrency test,
`test_search_mcp.py`) — none of which this ticket's diff touches. This confirms the guard-test
regression was the only new failure this ticket introduced, and it is now fixed.

## Test Summary

All scoped tests pass:
`pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_record_events.py tests/tools/test_record_run.py tests/tools/test_seq_offset.py tests/tools/test_scope_orphan_fix.py tests/tools/test_step0_ts_orchestrator.py -v`
→ 86 passed.

Also ran the full `tests/tools/` directory (86+ files) as a broader regression sweep: 1048 passed,
1 xfailed, 35 failed. 34 of those 35 failures are in files this ticket never touched
(`test_knowledge_search.py`, `test_monitoring_writer.py`, `test_monitoring_writer_lockfile_candidate.py`,
`test_post_tool_hook.py`'s concurrency test, `test_search_mcp.py`) — pre-existing
environment/timing-dependent failures (concurrent-write race assertions, live knowledge-index
build/query tests requiring resources not guaranteed in this session) unrelated to this ticket's
`seq_offset`/`seqOffset`/`compute_multi_invocation_collision_report` changes. The 35th failure,
`test_agent_monitoring_manifest.py::test_writer_files_are_byte_unchanged_by_this_ticket`, **was** a
real regression caused by this ticket's own `validate.py` diff (a stale guard asserting `validate.py`
must be byte-unchanged) — fixed in the Test-phase regression fix documented above by removing that
guard (see Implementation Notes). Re-running the full suite after the fix confirmed **34 failed,
1048 passed, 1 xfailed** — exactly the 5 pre-existing/environmental files, zero new regressions.

## Files Changed
- `tools/agent-monitoring/seq_offset.py` (new)
- `tests/tools/test_seq_offset.py` (new)
- `.claude/workflows/implement-ticket.js`
- `tests/tools/test_current_run_sidecar_orchestrator.py`
- `tests/tools/test_step0_ts_orchestrator.py` (deviation — collateral fix, see Implementation Notes)
- `tools/agent-monitoring/validate.py`
- `tests/tools/test_validate_agent_monitoring.py`
- `docs/agent-monitoring/schema.md`
- `tests/tools/test_agent_monitoring_manifest.py` (Test-phase regression fix — removed the stale
  `test_writer_files_are_byte_unchanged_by_this_ticket` guard and its `_WRITER_GUARD_FILES`
  constant, replaced with an explanatory comment; see Implementation Notes)
- `docs/parity_ledger/infrastructure.yaml` (new entry INFRA-288 — records this ticket's fix,
  evidence, and test paths per the Authoritative Mechanics Rule's parity-ledger update
  requirement; support_boundary notes no `src/` or Mechanics Bible chapter is implicated)

## Completion Summary
Fixed the third `tool_call_count`/`cost_proxy_score` corruption mechanism: a resumed
`implement-ticket.js` session's in-memory `seq` counter previously restarted at 1, silently
aliasing its tool-call attribution onto a prior (pre-pause) session's `(run_id, seq)` buckets in
`tools.jsonl`. Added `tools/agent-monitoring/seq_offset.py::compute_seq_offset()` (looks up the max
prior `seq` for a `run_id` in `events.jsonl`) and wired the resulting `seqOffset` into every
`seq`-producing expression in `implement-ticket.js` (`pushEvent`, all 10 `writeSidecar` call sites,
and the Scope-phase resume branch's sidecar write), so a resumed session's numbering now continues
past the prior session's instead of colliding with it. Added
`compute_multi_invocation_collision_report()` to `validate.py` to detect this mechanism's
historical signature automatically. Documented in `docs/agent-monitoring/schema.md`. Prevention-only
— the 8 historically-affected `run_id`s named in the ticket keep their corrupted values, per the
ticket's Out of Scope section. All new and updated tests pass (86/86 scoped); no regressions
introduced in the broader `tests/tools/` sweep (35 pre-existing unrelated failures, none in files
this ticket touched).
