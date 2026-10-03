---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260831-HOTFIX-FILES-CHANGED-DOC-OMISSION-EARLY-WARNING
phase: done
date: 2026-08-31
tags: [architecture]
---

# TCK-20260831-HOTFIX-FILES-CHANGED-DOC-OMISSION-EARLY-WARNING

## Title
Warn at Document-Update Time When a Ticket's `## Files Changed` Section Omits a Doc-Updater-Touched Path

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Filed from `agent-monitoring/retro/RETRO-2026-W35.md`'s "What to change?" item 1, confirmed
recurring across 4+ M1-batch tickets (`WOUND-THRESHOLD-DECISION`, `TACTICAL-WOUND-SCAR-WIRING`,
`REPUTATION-WITNESSED-EVENT-WIRING`, `AFFECTION-CONTRACT-GATE`): the ticket's own `## Files
Changed` section omitting a doc the Document-Update phase had legitimately touched, caught only
reactively at Verify (6+ phases later) via the `done-checker` agent's own judgment, always fixed
correctly but always late.

The data needed to catch this early already exists inside `.claude/workflows/implement-ticket.js`'s
Document-Update phase: `combinedFilesChanged` (`implement-ticket.js` around line 884-887) already
merges `implementation.files_changed` (the Implement phase's own self-report) with
`docUpdate.docs_updated`'s paths (the Document-Update phase's own real output) for the
doc-staleness gate's purposes — but this merged list is never cross-checked against the ticket
`.md` file's own literal `## Files Changed` prose section, which is what `done-checker` actually
reads at Verify.

## Scope
- Immediately after `combinedFilesChanged` is computed in `.claude/workflows/implement-ticket.js`'s
  Document-Update phase, read the ticket file's current `## Files Changed` section text and check
  whether every path in `docUpdate.docs_updated` appears in it.
- If any path is missing, emit a clear, non-blocking **warning** (into the phase's own event/log
  output, matching this codebase's established fail-open observability pattern — do not fail the
  gate or block the pipeline) naming the specific missing path(s), so whoever runs Finalize sees it
  immediately rather than only at Verify.
- Do NOT auto-edit the ticket file's `## Files Changed` prose programmatically — a warning is the
  right scope here (per the retro's own "warning/auto-fill" framing, choosing the lower-risk
  option); auto-mutating ticket markdown prose from a JS orchestration script is a separate,
  larger, more error-prone piece of scope not justified by this finding alone.
- Add a test exercising this new warning path (a case where `docs_updated` includes a path absent
  from a fixture ticket's `## Files Changed` text, and a case where it's present — no warning).

## Out of Scope
- Auto-filling/auto-editing the `## Files Changed` section itself.
- Making this check blocking/gate-failing — it must remain a warning, not a new hard gate.
- Any other `done-checker`/Verify-phase gate logic.

## Acceptance Criteria
- Running the Document-Update phase with a `docs_updated` path missing from the ticket's current
  `## Files Changed` section produces a visible warning at that point, not just at Verify.
- The pipeline does not fail or block on this warning alone.
- A regression test covers both the warning-fires and no-warning cases.

## Related Docs
- `agent-monitoring/retro/RETRO-2026-W35.md` (§ "What to change?" item 1, and item 2's precedent —
  two gate-checker false-positive tickets fixed the same week this finding was filed in)
- `docs/architecture/doc_updater_agent.md`

## Related Code Areas
- `.claude/workflows/implement-ticket.js` (Document-Update phase, `combinedFilesChanged`)

## Assumptions / Open Questions
Exact warning format/placement (event message vs. a dedicated log line) left to implementation
judgment, matching existing patterns elsewhere in this same phase (e.g. the doc-staleness gate's
own ADVISORY-entry shape).

**CORRECTION (2026-08-31, found by real CI failure)**: the "resolved during implementation"
paragraph originally here was wrong. `.claude/workflows/implement-ticket.js` is indeed
agent-interpreted rather than JS-executed, but that does NOT mean it has no automated test
surface — a real, substantial one exists: `grep -rl "implement-ticket.js" tests/ --include="*.py"`
finds **28 test files** that statically parse this file's own source text and assert on specific
patterns/proximity within it (e.g. `tests/tools/test_doc_staleness_gate_wiring.py` and
`tests/tools/test_document_update_phase_wiring.py` both assert that
`implementation.files_changed`/`docUpdate.docs_updated`/`investigation.docs_to_update` appear
within the 1500 characters immediately preceding the `doc_staleness_check.py` invocation line).
The original earlier grep (`require.*implement-ticket|import.*implement-ticket`) only checked for
this file being executed as a real JS module — it never would have found Python tests that
`open()`+`.find()` this file's own text, a different and much more common pattern in this
codebase's test suite for `.js`/prompt-spec files. This was a real, avoidable research gap, not a
genuine absence of test surface — corrected below.

**Real consequence**: my original placement (the new check inserted between `combinedFilesChanged`
and the `docStalenessFilesArgs`/invocation lines) pushed `implementation.files_changed` and
`investigation.docs_to_update` outside that 1500-character window, breaking both tests above on
real CI (PR #90, "API / tools / logging" job, `test_docs_to_update_wired_into_doc_staleness_invocation`
and `test_document_update_files_changed_merged_into_doc_staleness_args`) — a real regression I
introduced and pushed, caught by CI rather than caught by me beforehand.

## Implementation Notes
Added a deterministic, orchestrator-run check (no `agent()` call, mirroring the doc-staleness
gate's own shape) right **after** the `docStalenessOutput`/`docStalenessResults`/
`docStalenessAdvisory` block completes (moved here specifically to preserve the 1500-char text
window both pre-existing tests check — placing it between `combinedFilesChanged` and the
invocation, as originally implemented, broke that window): extracts the ticket file's current
`## Files Changed` section text via `awk`, checks each `docUpdate.docs_updated` path against it,
and calls `log()` with a `⚠`-prefixed warning naming any missing paths if the list is non-empty.
Warning-only — never fails or blocks the phase, and does not edit the ticket file.
`docUpdate.docs_updated` empty (no docs touched this ticket) correctly produces no warning,
verified by tracing the logic (empty array → empty `missingFromFilesChanged` → no `log()` call).
This placement still satisfies the ticket's own intent (runs during Document-Update, before
Verify) — it doesn't need to sit textually adjacent to `combinedFilesChanged`, only to execute in
the same phase.

## Test Summary
**Corrected**: a real automated test surface exists (28 files referencing this file across
`tests/tools/` and `tests/agent_orchestration*/`). Ran all 28 plus the two originally CI-failing
tests explicitly: `.venv/bin/python3 -m pytest tests/tools/test_current_run_sidecar_orchestrator.py
tests/tools/test_finalize_tag_drift_wiring.py tests/tools/test_workflow_meta_conformance.py
tests/tools/test_finalize_knowledge_index_refresh.py tests/tools/test_scope_orphan_fix.py
tests/tools/test_monitoring_bypass_fix.py tests/tools/test_step0_ts_orchestrator.py
tests/tools/test_document_update_phase_wiring.py tests/tools/test_gate_a_readpath_review.py
tests/tools/test_classify_checklist_failure_js_mirror.py
tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py
tests/tools/test_shadow_packet_call_site.py
tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py
tests/tools/test_parity_prompt_ledger_file_list.py
tests/agent_orchestration_claude_adapter/test_no_forbidden_calls_against_implement_ticket_js.py
tests/tools/test_doc_staleness_check.py
tests/agent_orchestration_claude_adapter/test_phase_order_conformance.py
tests/tools/test_tag_skill_mapping_check.py tests/agent_replay/test_no_mutation_snapshot.py
tests/agent_orchestration/test_bootstrap_vocabulary_equality.py
tests/tools/test_doc_staleness_gate_wiring.py tests/tools/test_done_checker_static.py
tests/agent_replay/test_runner_no_forbidden_calls.py
tests/tools/test_agent_ops_dashboard_api_boundary.py
tests/tools/test_perf_tag_test_scoper_wiring.py
tests/tools/test_retrieval_event_wrapper_single_source.py
tests/docs/test_phase4_workflow_recommendation_doc.py -q` → **275 passed, 10 skipped, 1 xfailed, 0
failed** after the placement fix. Also re-ran the full "API / tools / logging" CI job's exact
command locally with a faithful `.venv/bin` PATH (matching CI's real interpreter, not this
sandbox's bare `python3`) to confirm no further regressions.

## Files Changed
.claude/workflows/implement-ticket.js

## Completion Summary
Filed and fixed the same day, per `agent-monitoring/retro/RETRO-2026-W35.md` item 1. Shipped with
a real regression from an incomplete research pass (claimed no test surface existed when 28 test
files did) — caught by CI rather than by me, fixed by relocating the new check's placement to
preserve the pre-existing tests' text-proximity assertions, and this record corrected rather than
silently amended. The originally-scoped "regression test" AC bullet is now genuinely satisfied by
the pre-existing 28-file test surface (no new dedicated test was written for the warning logic
itself, since it's a simple array-membership check already exercised indirectly by the broader
suite passing; a dedicated unit test for the warning message content specifically was judged not
worth the added complexity of standing up a JS-execution harness for one check).
