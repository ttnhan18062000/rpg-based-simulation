---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT
phase: done
date: 2026-07-10
tags: [simulation-quality, documentation]
---

# TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT

## Title
SimQ Contract Acceptance Criteria (§12) Closeout — Verification & Citation Pass

## Status
DONE

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

Verification-and-citation pass performed 2026-07-11 against current `src/simulation_quality/`,
`src/observability/`, `src/engine/kernel.py`, and `tests/simulation_quality/` state (not assumed
unchanged since 2026-06-28).

**Summary: 24 of 25 items checked `[x]` with inline citation; 1 genuine gap left unchecked with a
linked follow-up ticket.**

By checklist:
- Functional: 6/6 checked.
- Performance: 5/5 checked (including both explicit safety-invariant items, re-verified live this
  session per the ticket's own requirement — see below).
- Scalability: 3/3 checked.
- Extensibility: 3/3 checked.
- Traceability: 2/3 checked; item 3 ("The traceability path in §9 is validated by an integration
  test") is a confirmed genuine gap — no test in the repo exercises the §9 drill-down end-to-end.
  Filed `tickets/todos/TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST.md` (tier: standard,
  since it requires writing a new integration test, not just documentation).
- Testing: 5/5 checked.

**Safety-invariant items (special attention per scope):**
- `QUALITY_SCORING_DISABLED=1` bit-identical output: re-read `src/simulation_quality/feed.py::build_feed_from_env`
  directly — the unconditional short-circuit (`if os.environ.get("QUALITY_SCORING_DISABLED") == "1": return None`,
  checked before any `QUALITY_FEED_MODE` branching) still exists at lines 125-126. Ran
  `tests/simulation_quality/test_feed.py::test_build_feed_returns_none_when_disabled` this session — passes.
- Scoring exception isolation: re-read `src/simulation_quality/quality_hub.py::QualityHub.on_envelope`
  directly — the disabled check at entry plus a `try/except Exception` wrapping every individual
  `scorer.score()` call (logging at WARNING, never re-raising) still exists at lines 135-159. Ran
  `tests/simulation_quality/test_quality_hub_integration.py::TestErrorIsolation::test_scorer_exception_does_not_propagate`
  this session — passes.

**Parity ledger correction:** `docs/parity_ledger/infrastructure.yaml` INFRA-233's `test_path` cited
`tests/simulation_quality/test_feed.py::test_build_feed_disabled_returns_none`, which does not exist
(confirmed via a live `pytest` collection attempt returning 0 items — the test was apparently
renamed to `test_build_feed_returns_none_when_disabled` at some point after the entry was written).
Corrected the `test_path` and added a `divergence_note` documenting the correction and the live
re-confirmation. `status` remains `verified` since the underlying behavior is still correct — only
the citation was stale.

**Other findings (not gaps, just drift noted inline):**
- §6's Scenario Registry now has 23 entries (SQ-01 through SQ-23), not the 22 that Functional
  item 6 and Testing item 5 were literally authored against. All 23 current entries have unit test
  coverage in `test_scenario_coverage.py`, so both items are still true as written (22 is a subset
  of 23) — noted inline rather than treated as a gap, since re-wording §12's count is out of this
  ticket's scope.
- INFRA-250's "353 tests total" count is already flagged stale by a prior ticket's `STALENESS FLAG`
  note; current live count is 456 passed + 5 skipped in `tests/simulation_quality/` alone. Not
  re-touched — the flag is already accurate, and the count-text correction is explicitly called out
  in that entry as a separate ticket's scope, consistent with how a prior sibling ticket handled it.

**Full test runs performed this session** (all passing, evidence for the Testing checklist and
several Performance/Scalability items):
- `pytest tests/simulation_quality/ -q` → 456 passed, 5 skipped (broker/REDIS_AVAILABLE-gated)
- `pytest tests/simulation_quality/ -q -m slow` → 24 passed, 2 skipped
- `pytest tests/simulation_quality/test_performance.py -v -m slow` → 6/6 passed
- `pytest tests/simulation_quality/test_scenario_coverage.py -q` → 36/36 passed
- `pytest tests/simulation_quality/test_api_routes.py -q` → 14/14 passed
- `pytest tests/simulation_quality/test_feed.py tests/simulation_quality/test_quality_hub_integration.py -v` → 21/21 passed

No engine, scorer, or API logic was changed — this ticket is documentation and parity-ledger
citation only, per its hotfix scope.

## Test Summary
All cited tests were run live in this session against current branch state (see command list
above); all passed. No new tests were added (out of scope for this ticket — the one genuine gap
found, Traceability item 3, is deferred to `TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST`).

## Files Changed
- `docs/simulation_quality/quality_scoring_contract.md` (§12: 24/25 checkboxes checked with inline
  citations; 1 left unchecked with follow-up ticket reference)
- `docs/parity_ledger/infrastructure.yaml` (INFRA-233: corrected stale `test_path`, added
  `divergence_note`)
- `tickets/todos/TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST.md` (new — follow-up ticket
  for the one confirmed gap)

## Completion Summary
§12's 25 acceptance-criteria checkboxes are now either checked with a live-verified citation (24)
or left unchecked with a linked follow-up ticket for the one confirmed genuine gap (1: Traceability
item 3, the §9 integration test). Both explicit safety-invariant items were re-confirmed against
current source and a current passing test run in this session, not assumed unchanged from the
2026-06-28 parity ledger entries. One stale parity ledger entry (INFRA-233) was found and corrected
in the same session. `docs/plans/simq_development_roadmap.md` Phase 0.2's acceptance signal is
satisfied.
