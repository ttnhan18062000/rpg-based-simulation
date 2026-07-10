---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT
phase: open
date: 2026-07-10
tags: [simulation-quality, documentation]
---

# TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT

## Title
SimQ Contract Acceptance Criteria (§12) Closeout — Verification & Citation Pass

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
`docs/simulation_quality/quality_scoring_contract.md` §12 defines five acceptance-criteria
checklists (Functional, Performance, Scalability, Extensibility, Traceability, Testing) totaling
25 items — the SimQ module's own definition of done. Every checkbox has remained literal
unchecked markdown `[ ]` since the doc was authored 2026-06-28, through roughly 40 subsequent SimQ
tickets (MVP epic E1–E7, three uplift batches, the Corpus Tiers epic, the Deep Coverage epic).
This is Phase 0.2 of `docs/plans/simq_development_roadmap.md`: go through §12 line by line, cite
live evidence (an existing passing test, a direct grep/code read, or a direct tool invocation) for
each item, and either check the box with an inline citation or file the item as a genuine
confirmed gap. Two items are explicitly called out as safety invariants requiring real
confirmation rather than assumption: "`QUALITY_SCORING_DISABLED=1` produces bit-identical
simulation output" and "scoring exceptions are caught and logged; they do not propagate to
simulation." This is a verification-and-citation pass, not new engineering — most items are
expected to already be true, but must be confirmed against current `src/`, not assumed true
because nothing has broken loudly.

## Scope
- Verify each of §12's 25 checkbox items (Functional: 6, Performance: 5, Scalability: 3,
  Extensibility: 3, Traceability: 3, Testing: 5) against current `src/simulation_quality/` and
  `tests/simulation_quality/` state, citing an existing passing test, a direct grep/code read, or
  a direct tool invocation for each.
- For the two explicit safety-invariant items — "`QUALITY_SCORING_DISABLED=1` produces
  bit-identical simulation output" and "scoring exceptions are caught and logged; they do not
  propagate to simulation" — perform a live confirmation against current source, not just a
  pointer to the 2026-06-28 parity ledger entries from TCK-20260628-SIMQ-E1-FOUNDATION, since
  roughly 40 tickets have touched the module since those entries were written.
- Update `docs/simulation_quality/quality_scoring_contract.md` §12 in place: check each verified
  box and append an inline citation (test path, file:line, or exact command); for any item that
  cannot be verified true, leave it unchecked and add a linked follow-up ticket reference instead.
- Where an item's existing parity ledger entry (`docs/parity_ledger/infrastructure.yaml`,
  INFRA-2xx range) already covers it, cross-reference that entry's `v2_evidence`/`test_path`
  rather than re-deriving evidence from scratch, but still confirm the cited test/code still
  exists and still passes on current branch state before citing it.
- If any parity ledger entry is found stale or contradicted during verification, update its
  `status`/`v2_evidence` in the same session per the Authoritative Mechanics Rule.

## Out of Scope
- Fixing any genuine gap found beyond filing it as a linked follow-up ticket — this ticket does
  not implement new scorer logic, new tests, or new engine behavior.
- Phase 0.1 (long-run calibration anchor reliability, the F6 thread) — already scoped separately
  in `tickets/inprogress/TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY.md`.
- Phase 1.1 (`hazard_kind` corpus-wide test) and Phase 1.2 (`town_council`/`bandit_road` DA
  ruling) — already scoped separately in `tickets/inprogress/TCK-20260710-HAZARD-KIND-CORPUS-WIDE.md`
  and `tickets/inprogress/TCK-20260710-TOWN-COUNCIL-HAZARD-DA.md`.
- Any of §14's Non-Goals (per-entity quality profiles, historical run comparison, real-time push
  alerts, ML-based anomaly detection, automated config suggestion) — explicitly out of scope for
  the whole roadmap, reaffirmed by the user 2026-07-10.
- Touching `src/engine/kernel.py`'s tick-budget throttle/watchdog logic.
- Re-scoping or re-authoring §12 itself (adding, removing, or rewording criteria) — this ticket
  only verifies and cites against the criteria as currently written.
- Phases 2–5 of the roadmap (SOCIAL/FACTION/INFORMATION/COGNITION depth waves, coverage decision
  gate) — unrelated scope, sequenced later.

## Acceptance Criteria
- All 25 checkboxes in §12 (Functional 6, Performance 5, Scalability 3, Extensibility 3,
  Traceability 3, Testing 5) are either (a) checked `[x]` with an inline citation (test path,
  file:line, or exact command run), or (b) left unchecked `[ ]` with an inline link to a filed
  follow-up ticket describing the confirmed gap.
- The "`QUALITY_SCORING_DISABLED=1` produces bit-identical simulation output" item's citation
  reflects a check performed against current source in this ticket's own session (a test run or a
  direct code read of `src/simulation_quality/feed.py::build_feed_from_env`), not solely a pointer
  to the 2026-06-28 parity ledger entry.
- The "scoring exceptions are caught and logged; they do not propagate to simulation" item's
  citation likewise reflects a current-state check (e.g. `src/simulation_quality/quality_hub.py::QualityHub.on_envelope`'s
  try/except is re-read and confirmed to still wrap every scorer call), not assumed unchanged
  since E1-FOUNDATION.
- No checkbox is checked without a citation resolvable to a real file path, test name, or command.
- Any item found to be a genuine gap has a linked follow-up ticket filed (ticket ID referenced
  inline in §12), not silently left unchecked with no trace.
- If any `docs/parity_ledger/infrastructure.yaml` entry is found stale during verification, its
  `status`/`v2_evidence` fields are updated in the same session.
- `docs/plans/simq_development_roadmap.md` Phase 0.2's stated acceptance signal ("every §12
  checkbox is either checked-with-citation or has a linked follow-up ticket") is satisfied and
  recorded.

## Related Tickets
- `docs/plans/simq_development_roadmap.md` Phase 0.2 — the roadmap item this ticket implements.
- `tickets/inprogress/TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY.md` — sibling Phase 0.1 ticket
  (long-run anchor reliability), independent scope, currently OPEN.
- `tickets/inprogress/TCK-20260710-HAZARD-KIND-CORPUS-WIDE.md`,
  `tickets/inprogress/TCK-20260710-TOWN-COUNCIL-HAZARD-DA.md` — sibling Phase 1.1/1.2 tickets,
  independent scope, currently OPEN.
- `tickets/done/TCK-20260628-SIMQ-E1-FOUNDATION.md`, `tickets/done/TCK-20260628-SIMQ-E2-HUB-CORE.md`,
  `tickets/done/TCK-20260628-SIMQ-E6-TESTS.md` — original MVP tickets whose parity ledger entries
  this ticket re-confirms rather than re-derives.
- `tickets/done/TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC.md` — most recent prior SimQ-contract
  doc closeout (§7.5 pillar completeness), same "confirm-and-cite" pattern applied to a different
  section of the same contract.

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §12 (target of this ticket), §1 (module
  goals), §6 (Scenario Registry, referenced by Functional item 6), §9 (Traceability Design,
  referenced by Traceability items), §10 (REST API Surface, referenced by Functional item 5), §11
  (Testing Contract, referenced by Testing items and Performance limits at §11.4), §14 (Non-Goals).
- `docs/plans/simq_development_roadmap.md` Phase 0.2 — the roadmap entry that scoped this ticket.
- `docs/plans/idea_simq_near_perfect_roadmap.md` Thread 2 — original evidence synthesis for this
  gap.
- `docs/parity_ledger/infrastructure.yaml` — INFRA-2xx range entries already covering several §12
  items (QUALITY_SCORING_DISABLED bit-identical output, exception isolation, duplicate-event
  scoring, per-scorer routing) — cross-check against current code, don't re-derive from scratch.
- `docs/engine/performance_contract.md` — checked for SimQ-specific performance budget entries;
  none found (a grep for "quality"/"simq" returned zero matches) — SimQ's own performance limits
  live entirely in `quality_scoring_contract.md` §11.4, not in the engine-wide contract; confirm
  this remains true during verification.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260628-SIMQ-E1-FOUNDATION/` — original disable-flag and
  exception-isolation implementation evidence.
- `stored_artifacts/TCK-20260628-SIMQ-E2-HUB-CORE/` — QualityHub routing/exception-isolation
  implementation evidence.
- `stored_artifacts/TCK-20260628-SIMQ-E6-TESTS/` — full test suite implementation, primary source
  for most Testing-checklist citations.
- `stored_artifacts/TCK-20260701-SIMQ-LOOP-WINDOW-TUNE/` — prior SimQ investigation with reusable
  performance/calibration evidence.
- `stored_artifacts/TCK-20260702-SIMQ-EVAL-HARNESS/`, `stored_artifacts/TCK-20260702-SIMQ-EVAL-MATRIX/`
  — evaluation harness and matrix evidence relevant to Traceability/Testing items.

Note: the originating request referenced `stored_artifacts/TCK-20260630-SIMQ-RECALIBRATE`; no
artifact by that exact name exists. The closest matching 2026-06-30 SimQ artifacts are
`TCK-20260630-SIMQ-CALFIX/`, `TCK-20260630-SIMQ-ANCHORS/`, `TCK-20260630-SIMQ-TIMEGATE/`, and
`TCK-20260630-SIMQ-WIRE-KERNEL/` — flagged in Assumptions/Open Questions below.

## Related Code Areas
- `src/simulation_quality/quality_hub.py` (`QualityHub.on_envelope`) — exception isolation,
  disabled-check, registry routing (Performance items 2–3, Functional item 1).
- `src/simulation_quality/feed.py` (`build_feed_from_env`, `BrokerQualityFeed.start`) —
  `QUALITY_SCORING_DISABLED=1` short-circuit (Performance item 2).
- `src/simulation_quality/pillar_accumulator.py` (`PillarAccumulator.add`, `.worst_events`,
  `.window_buffer`) — Scalability items 1–2, duplicate-event dedup.
- `src/simulation_quality/persistence.py` (`QualityPersistence`) — `quality_scores.jsonl` /
  `quality_report.json` write paths (Functional items 3–4).
- `src/simulation_quality/quality_report.py` — `QualityReport.build()` (Performance item 5).
- `src/simulation_quality/scorers/*.py`, `src/simulation_quality/scorers/base.py`
  (`PillarScorer`) — per-scorer `score()` timing (Performance item 4), Extensibility items 1–2.
- `src/simulation_quality/weights.py` (`ScoringWeights`) — Extensibility item 3 (`QualityProfile`
  weight overrides).
- `src/simulation_quality/api/routes.py` — REST endpoint correctness (Functional item 5).
- `tests/simulation_quality/*` (all 24 test files) — primary citation source for the Testing
  checklist and cross-referenced Functional/Performance/Scalability items; in particular
  `test_performance.py` (Performance items 4–5, Scalability items 1–2), `test_scenario_coverage.py`
  (Functional item 6, Testing item 5), `test_quality_hub_integration.py` (Performance items 2–3),
  `test_grade_regression.py` (Testing item 3).
- `docs/parity_ledger/infrastructure.yaml` (INFRA-2xx range) — existing verified entries to
  cross-check against current code.

## Assumptions / Open Questions
- Assumes the originating request's reference to `stored_artifacts/TCK-20260630-SIMQ-RECALIBRATE`
  was a naming approximation for the 2026-06-30 SimQ calibration artifacts that do exist
  (`TCK-20260630-SIMQ-CALFIX`, `TCK-20260630-SIMQ-ANCHORS`, `TCK-20260630-SIMQ-TIMEGATE`,
  `TCK-20260630-SIMQ-WIRE-KERNEL`). If a genuinely separate `RECALIBRATE` artifact was intended and
  exists elsewhere, the implementer should locate and fold it in; if it truly doesn't exist, no
  action needed — but some evidence this ticket expects to reuse may need re-deriving instead.
- Tier is set to `hotfix` per the roadmap's own sizing ("S–M effort... closer to a paperwork pass
  than new engineering") and because `tests/simulation_quality/` already has 24 test files that
  appear to cover nearly every §12 item by name. This could be wrong if, during verification, one
  or more items — most plausibly the two safety-invariant items, or Traceability item 3
  ("integration test validates §9's path") — turn out to require a real code change rather than a
  citation. If so, the implementer should escalate tier to `standard` and re-scope rather than
  force a hotfix-tier close.
- Assumes `docs/engine/performance_contract.md` does not separately govern any of §12's
  Performance items (confirmed by a grep returning zero SimQ/quality references in that file). If
  a future revision of that contract adds SimQ-specific budgets, this ticket's Performance
  citations would need to cross-check against it too.
- Assumes no ticket currently in `tickets/inprogress/` or recently closed targets §12 directly —
  confirmed by scan (only the sibling Phase 0.1/1.1/1.2 tickets exist, none touching §12 or
  `quality_scoring_contract.md`'s Acceptance Criteria section).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
