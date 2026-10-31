---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-SDLC-HAND-PATH-OFFICIAL-AND-BASELINES-FROZEN
phase: done
date: 2026-10-31
tags: [ai, governance, delivery]
---

# TCK-20261031-SDLC-HAND-PATH-OFFICIAL-AND-BASELINES-FROZEN

## Title
The hand/batch path is recorded as the official delivery model, `owner_directed` closes require a `path_note`, and the baseline table is frozen.

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Phase 0 (plan section 39). OD-1 is decided yes, so the operating model can be recorded. The baselines are the reference for every later phase.

## Scope
1. Commit the hand/batch model as the official path in `docs/plans/agent_infrastructure/session_layer_working_process.md`, citing #715 6529263880.
2. Define the `path_reason` values in `docs/agent-monitoring/schema.md`, and require `path_note` for `owner_directed` in the recorder's validation. Old rows stay readable.
3. Freeze the baseline table (plan section 46) as a dated, SHA-anchored record, re-measuring only what the plan marks as refreshable. State ubuntu's pre-10-30 host instability: its timings are not a baseline (#715 6527003378).
4. Add a decision record listing each OD as decided or undecided with its date.

## Out of Scope
- Pipeline removal (Phase 4, OD-5).
- Editing CLAUDE.md or settings.json.
- Deciding any open OD.

## Acceptance Criteria
1. The record marks OD-1, 2, 3, 10, 14, 15 as decided with #715 6529263880, and OD-3 as subject to E6b; all others read undecided.
2. A closure with `owner_directed` and no `path_note` is refused, with a test; the other path reasons are unaffected.
3. Each baseline row names its ref and SHA.
4. `tests/tools/` passes in a lead slot.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_DECISION_SUMMARY.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/agent-monitoring/record_hand_orchestrated_closure.py
- docs/agent-monitoring/schema.md
- docs/plans/agent_infrastructure/session_layer_working_process.md

## Assumptions / Open Questions
- Owner condition #715 6528807751: credential details from either host stay out of committed files, tickets and public comments unless a decision needs them; they go to the owner directly.
- No credential or ruleset change is authorised by the epic; each gets its own owner ask, by ticket.
- Undecided, and not to be written as decided: OD-4 to OD-9, OD-11 to OD-13, OD-16 to OD-21.

## Implementation Notes
- `owner_directed` now requires a non-empty `path_note`, in both places that enforced `other`: the run-record validator (`tools/agent-monitoring/record_run.py`) and the closure CLI (`record_hand_orchestrated_closure.py`). The set is one constant, `PATH_REASONS_NEEDING_NOTE` in `vocabulary.py`.
- Old rows are not re-validated: the only readers/checkers over stored rows are `validate.py::check_path_record` (checks that `path_reason` is a known value, not the note), `path_report.py` and the retro generator; none asks for a note. Test: `test_an_old_owner_directed_row_without_a_note_is_still_read_by_the_shard_validator`.
- `docs/agent-monitoring/schema.md` defines every `path_reason` value; `monitoring-schema.yaml` is aligned.
- `session_layer_working_process.md` section 7.1 records the hand/batch model as official (OD-1, #715 6529263880) and states what it does not decide (OD-5).
- `SDLC_DECISION_RECORD.md`: decided = exactly what #715 6529263880 and 6529808776 say; every other OD reads undecided. Where the plan's wording differs from the comments, the comment's words are used (listed in the record).
- `SDLC_BASELINES_FROZEN.md`: section 46 as written at `1ccaba303`, each row with ref and SHA; nothing re-measured; the ubuntu pre-2026-10-30 timings statement (#715 6527003378).
- CLAUDE.md was not edited. Its closure example shows `--path-reason` alternatives with no `--path-note`; reported to the planner.

## Test Summary
- `tests/tools/test_path_reason_and_phase_coverage.py`, `test_record_hand_orchestrated_closure.py`, `test_record_run.py`: 116 passed (scoped run). `tests/agent_orchestration` and `tests/docs`: 150 passed, 2 skipped, 1 xfailed.
- New tests: a note is required for `owner_directed` and `other` by the run validator (missing and empty); the other reasons need none; the closure CLI refuses `owner_directed` with no note and with a blank note and writes nothing; an old row without a note still passes the shard check.
- `tests/tools/` in a lead slot (AC4), on `c3a8cf0b7`, CPUs 4-5, `-n 2`: 5301 passed, 56 skipped, 1 xfailed, 1 failed in 7m16s. The one failure, `test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry`, was real drift: `docs/REGISTRY.yaml` lacked the two new records. Regenerated and committed (`8af37db8c`); that file now passes (69 passed). Only `docs/REGISTRY.yaml` differs between the two commits; the full run was not repeated.

## Files Changed
- `tools/agent-monitoring/vocabulary.py`, `record_run.py`, `record_hand_orchestrated_closure.py`
- `tests/tools/test_path_reason_and_phase_coverage.py`
- `docs/agent-monitoring/schema.md`, `agent-working/agent-orchestration/monitoring-schema.yaml`
- `docs/plans/agent_infrastructure/session_layer_working_process.md`, `SDLC_DECISION_RECORD.md` (new), `SDLC_BASELINES_FROZEN.md` (new)

## Completion Summary
AC1: the decision record marks OD-1, 2, 3, 10, 14, 15 decided with #715 6529263880 and OD-3 subject to E6b; all others undecided. AC2: refused with a test on each writer; other reasons unaffected. AC3: every baseline row names ref and SHA. AC4: full `tests/tools` run, one failure found and fixed (registry drift), see Test Summary.

Known gap: the CLAUDE.md closure example still shows `--path-reason` alternatives with no `--path-note` (one-line note chosen by the owner, #715 6540849801; not edited until the owner has seen the final text).
