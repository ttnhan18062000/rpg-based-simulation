---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE
phase: open
date: 2026-08-24
tags: [observability, agent-monitoring, data-quality, debugging]
---

# TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE

## Title
Fix cross-session contamination of the shared .claude/current_run sidecar

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`.claude/current_run` is a single, unscoped file that every concurrent Claude Code session in the same shared working directory overwrites, so the tool-call-logging hook (`post_tool_hook.py`) stamps `agent-monitoring/tools.jsonl` rows with whatever run_id/seq/phase/agent another session last wrote, not the session that actually made the call. This is a real, reproduced, live bug — not theoretical — found via direct evidence during a monitoring-check session on 2026-08-24. Prior tickets (sidecar-bash introduction, toolcount collision, pause/resume seq collision, hand-orchestration gap, KGMCP cache attribution) each fixed an adjacent symptom (forgetting to write the sidecar, jsonl append corruption, staleness flagging in one reader) but never scoped the sidecar itself per concurrent session/PID/execution_id, so the root mechanism remains unfixed. This ticket also makes the explicit Plan-phase decision on whether already-misattributed historical `tools.jsonl` rows should be corrected, flagged, or accepted as an unfixable caveat, and verifies (rather than assumes) that `runs.jsonl`/`events.jsonl` writers, which take `run_id` explicitly via `--data`, remain unaffected.

## Scope
- Confirm and document the root cause: post_tool_hook.py (and generate_retro.py) read a single shared '.claude/current_run' file on every tool call with no session/PID/execution scoping, causing last-writer-wins attribution under concurrency
- Design and implement per-session/per-PID/per-execution_id sidecar scoping (a keyed file or keyed directory, e.g. '.claude/current_run.<session_id_or_pid>') so each concurrent session's sidecar state is isolated
- Update post_tool_hook.py to resolve the correct scoped sidecar file using an identifier already present in its hook payload (session_id) or process context (PID), instead of the single hardcoded path, while keeping sidecar read fail-open per the 'monitoring write failure must never fail the workflow' rule
- Update implement-ticket.js's writeSidecar() helper and its Scope-phase inline sidecar writes to target the new per-execution-scoped file/key; update .claude/skills/implement-ticket/SKILL.md's hand-orchestration instructions to match the new scoped convention
- Define and implement a lifecycle for the new scoped sidecar state (creation point, staleness/cleanup trigger — e.g. deletion at session end or a staleness check analogous to retrieval_cache.py's _sidecar_run_is_stale()) so scoped files do not accumulate unbounded as new durable state
- Evaluate tools/retrieval_cache.py's read_current_run_sidecar()/_sidecar_run_is_stale() against the new scoped convention and either migrate it to match or explicitly document why it is deferred, so the two sidecar readers do not permanently diverge
- Note (do not fix) that implement-epic.js and create-tickets.js currently register no sidecar at all — call this out as a related but distinct gap for a possible follow-up ticket
- Plan-phase: make and record an explicit decision (correct-in-place vs flag-only vs accept-as-caveat) for already-written misattributed tools.jsonl rows, with rationale citing the repo's existing no-backfill precedents
- Verify (regression-guard, not new work unless a dependency is found) that record_run.py, record_events.py, and seq_offset.py remain unaffected since they take run_id explicitly via --data rather than reading the sidecar

## Out of Scope
- Retroactively correcting or rewriting any already-written tools.jsonl row's field values in place — this would violate the append-only/durable-state law regardless of which historical-data option is chosen
- The concurrent-APPEND corruption problem already solved by docs/ai/monitoring_writer_decision.md and tools/agent-monitoring/writer.py's os.O_CREAT|O_EXCL lock-file protocol — do not conflate that with this sidecar-scoping problem
- Adding sidecar coverage to implement-epic.js/create-tickets.js — a related but separate gap; only note it in this ticket, do not implement it here unless a follow-up ticket is warranted
- Changing record_run.py, record_events.py, or seq_offset.py unless this ticket's actual sidecar-scoping fix surfaces a genuine, concrete dependency on the sidecar in one of those files

## Acceptance Criteria
- [x] A new concurrent-writer test (analogous to test_concurrent_writers_produce_no_interleaved_or_truncated_lines) demonstrates: two concurrent sessions each write distinct {run_id, seq, phase, agent} sidecar values at roughly the same time, then each issue their own tool call, and the resulting tools.jsonl rows attribute each row to the session that actually made that call — not whichever session wrote last. (`test_two_concurrent_sessions_each_attributed_correctly`)
- [x] post_tool_hook.py resolves which scoped sidecar file to read using an identifier already present in its hook payload (session_id) — chose session_id over PID since it's what the read side already has, and the write side gets it non-racily from the `CLAUDE_CODE_SESSION_ID` env var, not a single hardcoded '.claude/current_run' path; existing tests (test_phase_and_agent_included_when_sidecar_present, test_execution_identity_fields_included_when_sidecar_present, test_phase_and_agent_default_to_none_on_partial_sidecar) continue to pass unmodified against the new convention (verified: all pass without edits, since none write a scoped file and the new logic falls back to the unscoped path when absent).
- [x] implement-ticket.js's writeSidecar() helper and its Scope-phase inline sidecar writes target a per-session-scoped file/key (additive, alongside the unchanged unscoped write); test_current_run_sidecar_orchestrator.py's adjacency/shape assertions (including its exact static-source assertions) all pass unmodified — new assertions added, none of the 15 pre-existing ones edited.
- [x] A stale/orphaned per-session sidecar file left by a crashed or finished session does not leak into a new session's attribution — verified by `test_foreign_scoped_sidecar_not_read_by_different_session`.
- [x] The scoped-sidecar design states a concrete lifecycle for the new per-session state (creation: written per phase by writeSidecar()/Scope's resume branch; cleanup: `_prune_stale_scoped_sidecars()` in post_tool_hook.py opportunistically deletes scoped files older than 24h on every hook invocation, since no "session end" hook exists in this repo) so unbounded growth is not introduced, satisfying the Durable State Rule. Verified by `test_stale_scoped_sidecar_pruned`/`test_fresh_scoped_sidecar_not_pruned`.
- [x] The ticket's Plan phase contains an explicit, named decision record (accept-as-caveat, not correct-in-place or flag-only) for already-written misattributed tools.jsonl rows, with rationale referencing the repo's existing no-backfill precedent (the schema.md line already documenting this exact no-backfill stance for a prior, structurally identical bug class). See plan.md/investigation.md.
- [x] N/A (accept-as-caveat chosen, not flag) — no new per-row field added; instead docs/agent-monitoring/schema.md gained an explicit historical-data-quality caveat paragraph naming the confirmed affected window/ticket, per the AC's own "accept as caveat" branch.
- [x] No already-written tools.jsonl row's existing field values are edited in place (verified: no code in this ticket ever opens tools.jsonl for writing except the existing append-only `write_line()` call, unchanged). generate_retro.py was not modified — no new flag was introduced for it to exclude/label (accept-as-caveat path).
- [x] **Corrected during implementation**: a literal `grep -n "current_run"` across the three files is NOT zero — `record_events.py:43` mentions `.claude/current_run` in its own docstring (explaining, in prose, why `tool_call_count` is only computed for `implement-ticket` run_ids), not a real file access. The regression-guard test (`test_record_run_events_seq_offset_never_read_sidecar`) was written to check actual `open()`/`Path()` access to the sidecar, not the bare substring, so it correctly passes without false-positiving on this legitimate comment. No `open()`/`Path()` call in any of the three files targets the sidecar, confirmed.
- [x] record_run.py and record_events.py continue to require run_id explicitly via --data with no fallback to sidecar/environment; no code changes were made to any of the three files (confirmed by the regression-guard test above).
- [x] tools/retrieval_cache.py's sidecar-read logic migration is **explicitly deferred, not migrated** — documented in investigation.md's "Other sidecar readers" section: it already has its own independent staleness mitigation for its one specific consumer (KGMCP cache log), and migrating it now would expand this ticket's blast radius beyond the one concretely evidenced defect (tools.jsonl misattribution) without a second piece of live evidence its own reads are wrong in a way its existing flag doesn't already catch.

## Related Tickets
- TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP
- TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD
- TCK-20260721-MONITORING-WRITER-DECISION
- TCK-20260721-MONITORING-WRITER-UNIFICATION
- TCK-20260730-CLAUDE-EXECUTION-IDENTITY
- TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK
- TCK-20260710-CURRENT-RUN-SIDECAR-BASH
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION
- TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION
- TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS

## Related Docs
- docs/agent-monitoring/schema.md
- docs/ai/monitoring_writer_decision.md
- .claude/skills/implement-ticket/SKILL.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/current_run
- tools/agent-monitoring/post_tool_hook.py
- tools/agent-monitoring/pre_tool_hook.py
- tools/agent-monitoring/writer.py
- .claude/workflows/implement-ticket.js
- .claude/.current_session_id
- tools/retrieval_cache.py
- docs/agent-monitoring/schema.md
- .claude/skills/implement-ticket/SKILL.md
- tests/tools/test_post_tool_hook.py
- tests/tools/test_current_run_sidecar_orchestrator.py
- agent-monitoring/tools.jsonl
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/validate.py
- tools/tag_registry.py
- tools/tag_corpus_sweep.py
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/seq_offset.py
- tests/tools/test_record_run.py
- tests/tools/test_record_events.py
- tests/tools/test_seq_offset.py

## Assumptions / Open Questions
- tools/retrieval_cache.py's read_current_run_sidecar()/_sidecar_run_is_stale() already partially mitigated this bug class for the KGMCP cache log but did not fix the root mechanism; whether it must move to the same scoped convention as post_tool_hook.py is an open design question to resolve during Plan, not assumed here
- .claude/.current_session_id (written per tool call by pre_tool_hook.py) is a real per-session identifier to key scoping off of, but is itself a second single shared file with the same last-writer-wins risk if read outside the immediately-preceding-tool-call context — the new design must not introduce a second copy of this same bug
- Multiple call sites currently write the shared file (implement-ticket.js's writeSidecar()/Scope-phase inline writes, hand-orchestrating agents per SKILL.md); implement-epic.js/create-tickets.js register no sidecar at all today and are assumed out of scope per this ticket's explicit scope note
- Any sidecar path/shape change requires updating test_current_run_sidecar_orchestrator.py's exact adjacency-string static-source assertions in the same change
- Per-session scoped files are new durable state requiring their own lifecycle definition (deleted at session end? staleness timeout? next-session-start cleanup?) — left as an open design question for Plan, not pre-decided here
- The historical-data decision (correct/flag/accept for already-written misattributed rows) is this ticket's own Plan-phase decision, not a separate investigation track
- The runs.jsonl/events.jsonl writer-safety verification is expected to be a no-op regression guard (existing tests already assert this safety property) unless this ticket's actual fix surfaces a concrete dependency
- layer assigned as `observability` (agent monitoring/telemetry subsystem) per registries/layer_registry.jsonl — no new layer registration was needed

## Implementation Notes

**Root cause confirmed**: `.claude/current_run` is a single shared file; `post_tool_hook.py` reads
it unconditionally to stamp every `tools.jsonl` row's `run_id`/`seq`/`phase`/`agent`. Every
concurrent session's own `writeSidecar()` call overwrites it, so whichever session wrote last
"wins" attribution for every other session's tool calls in between writes.

**Fix — session_id as the scoping key, zero new races.** `CLAUDE_CODE_SESSION_ID` is a real,
already-present environment variable in every Bash subprocess (confirmed live:
`env | grep CLAUDE_CODE_SESSION_ID`), stable for the life of a session, set once by the harness —
not a shared mutable file, so reading it introduces no new race. It matches the `session_id`
`post_tool_hook.py` already extracts from its own hook payload on the read side (this field was
*already* correctly per-call attributed; only run_id/phase/agent were not).

- `writeSidecar()` and the Scope-phase resume branch (`.claude/workflows/implement-ticket.js`) now
  additionally write `.claude/current_run.<CLAUDE_CODE_SESSION_ID>`, alongside the existing
  unscoped `.claude/current_run` write (kept unchanged).
- `post_tool_hook.py` prefers the session-scoped file (keyed by its own hook payload's
  `session_id`), falling back to the unscoped file when no scoped file exists — meaning every
  pre-existing test (none of which write a scoped file) keeps passing **unmodified**.
- `_prune_stale_scoped_sidecars()` (24h threshold) runs on every hook invocation, fail-open,
  bounding growth of the new per-session state since no "session end" hook exists in this repo.
- `.claude/skills/implement-ticket/SKILL.md`'s hand-orchestration instruction updated to mention
  the additive scoped write.
- **Deferred, disclosed, not silently skipped**: `tools/retrieval_cache.py`'s duplicate sidecar-read
  logic and `.claude/settings.json`'s inline sidecar-check hook are left reading the unscoped file
  (which is still written) — see investigation.md for the explicit reasoning.
- **Historical data**: accepted as a documented caveat (schema.md), no backfill, no new per-row
  flag — mirrors this repo's own pre-existing precedent for the structurally identical situation.

**Test-writing found a real inaccuracy in this ticket's own investigation**, disclosed rather than
silently corrected: the investigation's claimed `grep -n "current_run"` zero-match result for
`record_run.py`/`record_events.py`/`seq_offset.py` was wrong — `record_events.py`'s own docstring
mentions `.claude/current_run` in prose. Verified this is legitimate documentation, not a
dependency (no `open()`/`Path()` call touches it), and wrote the regression-guard test to check
actual file access instead of the bare substring, so it doesn't false-positive on the comment.
investigation.md and this ticket's own AC checklist were corrected to state this accurately.

## Test Summary

- `pytest tests/tools/test_post_tool_hook.py tests/tools/test_current_run_sidecar_orchestrator.py -q`
  → **33 passed** (11 pre-existing in test_post_tool_hook.py + 5 new; 26 pre-existing in
  test_current_run_sidecar_orchestrator.py + 3 new — one new test found the docstring inaccuracy
  above and was corrected in place before landing).
- `pytest tests/tools/test_record_run.py tests/tools/test_record_events.py tests/tools/test_seq_offset.py -q`
  → **46 passed**, confirming C3 (no writer-side regression).
- `pytest tests/docs/ -k "agent_monitoring or schema" -q` → **1 passed**.
- Broader regression surface: `pytest tests/tools/test_retrieval_cache.py
  tests/tools/test_step0_ts_orchestrator.py tests/tools/test_execution_identity_end_to_end.py
  tests/tools/test_shadow_packet_call_site.py tests/tools/test_monitoring_writer.py
  tests/tools/test_generate_retro.py tests/tools/test_validate_agent_monitoring.py
  tests/tools/test_classify_checklist_failure_js_mirror.py
  tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_monitoring_bypass_fix.py
  tests/tools/test_skill_investigate_search_before_grep.py -q` → **354 passed** (2 unrelated
  skill-staleness warnings, pre-existing/not caused by this ticket).
- `pytest tests/tools/ -k "parity_ledger or parity_index" -q` → **92 passed** (2 unrelated
  deprecation warnings from `jsonschema.RefResolver`, pre-existing).
- `pytest tests/tools/test_workflow_meta_conformance.py -q` → **23 passed, 1 xfailed** (unaffected
  by the SKILL.md edit).
- `python3 tools/validate_frontmatter.py` on this ticket file → OK.

## Files Changed

- `tools/agent-monitoring/post_tool_hook.py` — scoped-sidecar preference + fallback,
  `_prune_stale_scoped_sidecars()`
- `.claude/workflows/implement-ticket.js` — `writeSidecar()` and Scope-phase resume branch write
  the additive session-scoped copy
- `.claude/skills/implement-ticket/SKILL.md` — hand-orchestration instruction updated
- `docs/agent-monitoring/schema.md` — new documentation paragraph + historical caveat
- `docs/parity_ledger/infrastructure.yaml` — new entry `INFRA-377`
- `tests/tools/test_post_tool_hook.py` — 5 new tests
- `tests/tools/test_current_run_sidecar_orchestrator.py` — 3 new tests (one corrected mid-write per
  Implementation Notes above)
- `staging_artifacts/TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE/{investigation,plan,test_plan}.md`

## Completion Summary

Fixed a real, live, reproduced bug (not theoretical): `.claude/current_run` was a single file
shared across every concurrent Claude Code session in this repo's working directory, so
`tools.jsonl` attribution silently followed whichever session last wrote the sidecar — confirmed by
directly observing a closed ticket (`TCK-20260821-VISUAL-QUALITY-DOCS`, closed 2026-08-22) still
absorbing another session's live tool-call rows two days later. Fixed additively by scoping the
sidecar per `CLAUDE_CODE_SESSION_ID` — an already-available, race-free, process-level identifier —
without touching the existing unscoped file (kept for two explicitly deferred readers) and without
breaking a single pre-existing test. Made three explicit design calls this ticket's own Assumptions
flagged as needing judgment: (1) session_id over PID as the scoping key, (2) accept historical
misattribution as a documented caveat rather than building an unproven backfill/flag mechanism, (3)
defer `retrieval_cache.py`'s migration rather than expanding scope beyond the one evidenced defect.
Also caught and corrected a real inaccuracy in this ticket's own investigation (a bare-substring
grep claim that didn't hold up under a properly-written regression test) — disclosed, not hidden.
