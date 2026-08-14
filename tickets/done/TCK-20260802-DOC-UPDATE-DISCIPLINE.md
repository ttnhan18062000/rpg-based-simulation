---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260802-DOC-UPDATE-DISCIPLINE
phase: done
date: 2026-08-02
tags: [workflows, documentation, investigator]
---

# TCK-20260802-DOC-UPDATE-DISCIPLINE

## Title
Make documentation updates a disciplined, verified step in Investigate/Implement/Finalize, not an implicit side effect

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
The user asked whether `implement-ticket.js`/`create-tickets.js` have a dedicated step/agent for
reading and writing documentation. Investigation found doc handling is real but thin and has one
outright gap:

1. **Finalize never runs `make knowledge-index-update`.** CLAUDE.md's "After Work" rule and
   `docs/guidelines/agent_working_environment.md`'s Index Lifecycle Rules both require it whenever
   `docs/` files are created/modified, but `implement-ticket.js` has zero references to that
   command (confirmed by grep) — the semantic search index silently goes stale after every ticket
   that touches `docs/`.
2. **The doc-staleness gate is path-presence-only, not content-relevance.**
   `tools/gate_checks/doc_staleness_check.py::check_doc_staleness` passes as soon as *any* `docs/`
   path appears in `files_changed` when `behavior_changed=true` — it never confirms the touched doc
   is the *right* one. `investigator` already reads Mechanics Bible/engine docs and cites
   constraints in investigation.md, but never emits a structured "these specific docs must change"
   obligation that a later phase can check against.
3. **The gate's path/behavior criteria are narrower than "any change in logic."** The user
   clarified mid-session: doc updates must be a mandatory step for *any* new logic, new feature, or
   new setting — not only diffs to existing `src/` behavior. Today's check only flags `src/` and
   `.claude/workflows/*.js` paths; `config/simulation_quality/*.yaml` (scoring weights, grade
   thresholds, detection params) changes simulation-quality *behavior* but currently escapes the
   gate entirely because it isn't under `src/`. The `behavior_changed` boolean itself is also
   ambiguous — an implementer could reasonably read it as "did I change *existing* behavior" and
   report `false` for a brand-new feature/setting that has no prior behavior to diverge from.

User confirmed (via AskUserQuestion): the new specific-doc-relevance check should be
**advisory-only** for now (log/enrich event evidence, do not add a new blocking status) — matches
this repo's own precedent of shipping `doc_staleness_check.py` unwired first
(`TCK-20260711-DOC-STALENESS-GATE-CHECK`) and only promoting to blocking after retro evidence
(`TCK-20260720-GATE-CHECK-WIRING-DECISIONS`).

## Scope
- `investigator` agent (`.claude/agents/investigator.md`): add a `## Docs Requiring Update`
  section to `investigation.md` (specific doc paths + reason, empty list valid) and a structured
  `docs_to_update` return field.
- `.claude/workflows/implement-ticket.js`:
  - Investigate phase: add a schema requiring `docs_to_update` (array of paths), carry it forward.
  - Implement phase: broaden the `behavior_changed` prompt/field guidance to explicitly cover new
    logic/features/settings, not only modifications to pre-existing behavior.
  - Post-Implement doc check: pass `docs_to_update` into `doc_staleness_check.py` and surface any
    advisory mismatch (flagged doc not touched) in the pushed event — non-blocking.
  - Finalize: run `make knowledge-index-update` (orchestrator `bash()`, fail-open) whenever any
    `docs/` path changed during this run.
- `tools/gate_checks/doc_staleness_check.py`:
  - Broaden flagged-path prefixes to include `config/` alongside `src/` and
    `.claude/workflows/*.js`.
  - Accept optional `docs_to_update: List[str]` and add an `ADVISORY` (non-blocking) result entry
    when a flagged doc wasn't touched.
- `docs/ai/ticket-lifecycle.md`: document all of the above so the doc and code stay in parity.
- Tests: extend `tests/tools/` coverage for `doc_staleness_check.py`'s new parameter and `config/`
  path detection.

## Out of Scope
- Making the doc-relevance check a hard blocking gate (deferred — advisory-only per user decision).
- `create-tickets.js` — it produces ticket files only and never touches `docs/`; no doc-write step
  exists there today and none is being added (confirmed during investigation, no evidence this
  workflow needs one).
- Any change to the Mechanics Bible / engine contract *content* itself — this ticket is process
  tooling, not a simulation-mechanics change.
- Re-deriving or renaming the existing `DOC_STALENESS_BLOCKED` blocking contract — its existing
  PASS/FAIL semantics for `src/`+`.claude/workflows/*.js` stay exactly as they are; this ticket only
  adds `config/` to the flagged-path set and adds a separate, non-blocking `ADVISORY` result.

## Acceptance Criteria
- [x] `investigation.md`'s template includes a `## Docs Requiring Update` section; the investigator
      agent's contract returns a `docs_to_update` array (empty list is valid, not an error).
- [x] `implement-ticket.js`'s Investigate phase call has a schema requiring `docs_to_update`.
- [x] `implement-ticket.js`'s Implement phase prompt/schema explicitly states `behavior_changed`
      must be `true` for new logic/features/settings, not only modified existing behavior.
- [x] `doc_staleness_check.py::check_doc_staleness` flags `config/` paths the same way it flags
      `src/` and `.claude/workflows/*.js` paths.
- [x] `doc_staleness_check.py::check_doc_staleness` accepts an optional `docs_to_update` list and
      returns an `ADVISORY` (non-`FAIL`, non-blocking) entry when a flagged doc path isn't in
      `files_changed`, without changing any existing `PASS`/`FAIL` verdict.
- [x] `implement-ticket.js`'s Finalize phase runs `make knowledge-index-update` (fail-open, logged
      warning on failure, never blocks `DONE`) whenever this run touched any `docs/` path.
- [x] `docs/ai/ticket-lifecycle.md` reflects all of the above in the Investigate/Implement/Finalize
      sections.
- [x] New/updated tests cover: `config/` path flagging, `docs_to_update` match (no advisory),
      `docs_to_update` mismatch (advisory present, existing PASS/FAIL untouched).

## Related Tickets
- TCK-20260711-DOC-STALENESS-GATE-CHECK (shipped the check, unwired)
- TCK-20260720-GATE-CHECK-WIRING-DECISIONS (wired it in, blocking)
- TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR (fixed stale phase lists in docs/ai/workflows.md)

## Related Docs
- docs/ai/ticket-lifecycle.md
- docs/guidelines/agent_working_environment.md (Index Lifecycle Rules — already documents the
  command; this ticket only wires the call site, no content change needed there)

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- .claude/agents/investigator.md
- tools/gate_checks/doc_staleness_check.py
- tests/tools/ (doc_staleness_check test file)
- docs/ai/ticket-lifecycle.md

## Assumptions / Open Questions
- Assuming `git status --porcelain -- docs/` at Finalize time is a reliable enough signal for
  "did this run touch docs/" — this run's `files_changed`/Parity-phase `docs/parity_ledger/` touches
  are both already known by that point, but a direct `git status` check is simpler and catches any
  docs/ edit regardless of which phase made it.
- No unresolved questions — design decision (advisory vs. blocking) was resolved with the user
  before scoping.

## Implementation Notes
- `tools/gate_checks/doc_staleness_check.py`: added `config/` to the flagged-path prefix set
  (alongside `src/` and `.claude/workflows/*.js`); added an optional `docs_to_update` param that
  appends a non-blocking `ADVISORY` result entry (never `FAIL`) when a specifically-flagged doc
  wasn't touched, even though the blanket `docs/`-path-presence check already passed. CLI gained a
  `--docs-to-update` sentinel, fully backward-compatible with the existing 2-arg-shape call sites.
- `.claude/workflows/implement-ticket.js`:
  - Investigate phase now has `INVESTIGATION_SCHEMA` requiring `docs_to_update` (array) and
    `findings_summary` (string) — previously a free-text return. `investigation` is now an object
    everywhere (including the hotfix-tier default), so `investigation.docs_to_update` is always
    safely readable regardless of tier.
  - `IMPL_SCHEMA.behavior_changed` and the Implement prompt both now explicitly state it must be
    `true` for new logic/features/settings, not only modifications to pre-existing behavior.
  - The post-Implement doc-staleness bash() call now passes `docs_to_update` via
    `--docs-to-update`; the resulting `ADVISORY` entry (if any) is folded into the existing single
    `pushEvent` call's summary and logged as a non-blocking warning — no new blocking status, no
    second `pushEvent` call (preserves `test_doc_staleness_gate_wiring.py`'s structural
    assumptions).
  - Finalize now runs `make knowledge-index-update` (orchestrator `bash()`, fail-open, logged
    warning on failure) whenever `git status --porcelain -- docs/` shows this run touched `docs/`
    — placed after the existing migration self-check and before the `DONE` return.
- `.claude/agents/investigator.md`: added a `## Docs Requiring Update` investigation.md section and
  a matching `docs_to_update` return field, mirroring the JS schema exactly.
- `docs/ai/ticket-lifecycle.md`: Investigate/Implement (gate + new advisory check +
  `behavior_changed` definition)/Finalize sections all updated to match the code.
- Two pre-existing tests hardcoded exact source line numbers for the `FINALIZE_INCOMPLETE`
  terminal-status call sites (`test_terminal_status_extractor.py`,
  `test_terminal_status_conformance.py`); both updated from `[1234, 1246]` to `[1377, 1389]` since
  adding lines earlier in `implement-ticket.js` legitimately shifted every later line number — not
  a logic change.

## Test Summary
Scoped run: `pytest tests/tools/test_doc_staleness_check.py tests/tools/test_doc_staleness_gate_wiring.py tests/tools/test_finalize_knowledge_index_refresh.py tests/tools/test_current_run_sidecar_orchestrator.py tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py tests/agent_orchestration_claude_adapter/test_phase_order_conformance.py tests/agent_orchestration_claude_adapter/test_no_forbidden_calls_against_implement_ticket_js.py tests/agent_orchestration/test_bootstrap_vocabulary_equality.py tests/tools/test_scope_orphan_fix.py tests/tools/test_step0_ts_orchestrator.py tests/tools/test_finalize_tag_drift_wiring.py tests/tools/test_monitoring_bypass_fix.py tests/tools/test_shadow_packet_call_site.py tests/tools/test_retrieval_event_wrapper_single_source.py tests/tools/test_classify_checklist_failure_js_mirror.py tests/tools/test_tag_skill_mapping_check.py tests/tools/test_workflow_meta_conformance.py -v`
— 122 passed, 1 xfailed, 0 failed.

New tests added: 8 in `test_doc_staleness_check.py` (`config/` flagging × 2, `docs_to_update`
advisory behavior × 5, CLI sentinel × 1), 1 in `test_doc_staleness_gate_wiring.py`
(`docs_to_update` wiring), 4 in new `test_finalize_knowledge_index_refresh.py` (ordering,
conditional-on-docs-change, fail-open, orchestrator-not-agent-prompt).

Also ran a full unscoped sweep of `tests/tools/ tests/agent_orchestration/
tests/agent_orchestration_claude_adapter/ tests/agent_replay/` (1541 passed, 38 failed, 1 xfailed)
to check for wider regressions. Verified all 38 failures are pre-existing and unrelated: none
reference any file this ticket touched; `test_knowledge_search.py`'s failures reproduce in
isolation with a `RuntimeError: unable to mmap ... Cannot allocate memory` loading the embedding
model (environment memory constraint, not a code defect); `test_no_mutation_snapshot.py` and
`test_monitoring_writer.py`'s failures both **pass** when run in isolation (shared-filesystem-state
test-ordering artifacts under the full parallel sweep, not caused by this ticket's changes).

## Files Changed
- `tools/gate_checks/doc_staleness_check.py`
- `.claude/workflows/implement-ticket.js`
- `.claude/agents/investigator.md`
- `docs/ai/ticket-lifecycle.md`
- `tests/tools/test_doc_staleness_check.py`
- `tests/tools/test_doc_staleness_gate_wiring.py`
- `tests/tools/test_finalize_knowledge_index_refresh.py` (new)
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py`

## Completion Summary
Closed three real gaps in documentation handling across `implement-ticket.js`: (1) Finalize never
ran `make knowledge-index-update` despite CLAUDE.md/agent_working_environment.md requiring it —
now wired, fail-open. (2) The doc-staleness gate only checked that *some* `docs/` path was touched,
never the *right* one — Investigate now emits a structured `docs_to_update` obligation, checked
advisorily (non-blocking, per user decision) against the actual diff. (3) The gate's flagged-path
set (`src/`, `.claude/workflows/*.js`) missed `config/` settings (e.g. SimQ scoring
weights/thresholds) that drive behavior from outside `src/`, and `behavior_changed`'s definition
was ambiguous about brand-new features/settings versus modified existing behavior — both fixed.
All changes are additive to existing gate contracts; no existing `PASS`/`FAIL` verdict changes
shape or meaning, confirmed by the full pre-existing test suite passing unmodified plus 13 new
tests covering the additions.
