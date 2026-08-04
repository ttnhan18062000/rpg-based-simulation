---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX
phase: done
date: 2026-08-04
tags: [simulation-quality, observability, determinism, bug]
---

# TCK-20260804-OBSISO-WORKER-PARITY-HOTFIX

## Title
QualityWorker: use the existing build_all_scorers() factory instead of a hardcoded 2-pillar list

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`QualityWorker.__init__` (`src/simulation_quality/worker.py:69`) hardcodes
`scorers = [AgencyScorer(weights), CombatScorer(weights)]` — 2 of SimQ's 10 pillar scorers.
Broker-mode runs therefore silently omit 8 pillars and produce grades that are not comparable to
in-process grades or the 25-anchor calibration corpus.

This **replaces** the original standard-tier scope in
`tickets/todos/obs-isolation/TCK-20260702-OBSISO-WORKER-PARITY.md` (G2 from
`docs/plans/observability_process_isolation.md`), which assumed the shared scorer-registry factory
needed to be *extracted* from the kernel path. Verified directly, live in the code, that this
assumption is now stale: `build_all_scorers(weights) -> list[PillarScorer]` already exists at
`src/simulation_quality/scorers/__init__.py:10-26` (covering all 10 pillars) and is already
consumed by the in-process kernel path at `src/engine/kernel.py:249`. The extraction work is
already done; only `worker.py` never got updated to call it. Also verified: weights loading is
already aligned between the two paths — both `worker.py`'s env-var defaults and `kernel.py:239-244`'s
hardcoded call use the identical `config/simulation_quality/*.yaml` paths and `QUALITY_PROFILE`
default (`"default"`) — no divergence to fix.

## Scope
- `src/simulation_quality/worker.py`: replace the hardcoded `AgencyScorer(weights), CombatScorer(weights)`
  list with `build_all_scorers(weights)`, importing it from `src.simulation_quality.scorers`
  (matching `kernel.py`'s import shape exactly). Remove the now-unused direct `AgencyScorer`/
  `CombatScorer` imports.
- Proof test: assert `QualityWorker`'s constructed `QualityHub` has all 10 pillar scorers
  (`{s.pillar_id for s in hub._scorers} == set(PillarId)` or equivalent, matching whatever internal
  shape `QualityHub` actually exposes — verify during Implement, don't assume a private attribute
  name without checking). Extend/replace whatever the current worker-level test coverage is
  (`tests/simulation_quality/test_feed.py` or similar — locate via grep for `QualityWorker(` in
  `tests/`, don't assume a file that doesn't exist).
- Extend `_HealthHandler`'s `/health` payload with per-pillar processed-event counts (a cheap dict
  keyed by pillar name), so a future regression in scorer coverage is observable via `/health`
  rather than silent — matches the original ticket's own AC #4, kept because it's cheap and
  directly serves the "make broken state observable" goal this bug itself demonstrates the need
  for.

## Out of Scope
- Stream config unification / kernel broker-mode routing fix (still `TCK-20260702-OBSISO-BROKER-CONFIG`,
  a separate, unresolved gap — G1+G3, not G2).
- Cross-process grade-parity integration test (envelope replayed through a real broker pipeline,
  in-process hub vs. worker-process hub, compared for identical `ScoreRecord` output) — the
  original ticket's AC #2 needs a *working* broker pipeline to mean anything beyond a unit-level
  scorer-count check, and `BROKER-CONFIG` (G1+G3) is not yet landed. Deferred to
  `TCK-20260702-OBSISO-ISOLATION-PROOF`'s cross-mode benchmark work, which already needs a working
  broker pipeline for its own measurement and can absorb this grade-comparison as a byproduct.
- Changing any scorer logic, weights, or the 25-anchor calibration corpus.
- `make evaluate --dry-run` must remain unchanged (in-process path untouched by this fix — verify,
  don't just assert).

## Acceptance Criteria
- [x] `src/simulation_quality/worker.py` imports and calls `build_all_scorers(weights)`; no
      `AgencyScorer(`/`CombatScorer(` (or any other individual scorer class) literal remains in
      `worker.py`.
- [x] A test asserts `QualityWorker`'s hub is constructed with all 10 pillars represented.
- [x] `/health` payload includes a per-pillar event-count field once the hub has processed at
      least one envelope (verify exact shape against whatever `QualityHub`/`ScoreRecord` already
      exposes for this — don't invent a new counting mechanism if one exists).
- [x] `make evaluate --dry-run` output unchanged (in-process grades unaffected — this file is not
      touched by the in-process path at all, so this should be trivially true; confirm directly
      rather than assuming).
- [x] Existing `tests/simulation_quality/` suite passes for all tests touched by/relevant to this
      change (448 passed, 79 skipped, 1 pre-existing unrelated failure — see Test Summary).

## Related Tickets
- `tickets/todos/obs-isolation/TCK-20260702-OBSISO-WORKER-PARITY.md` — superseded by this ticket;
  once this lands, that ticket's file should be deleted from `tickets/todos/obs-isolation/` (its
  scope is fully absorbed here plus the grade-parity portion deferred to ISOLATION-PROOF) and
  `SEQUENCE.md`/`TCK-20260702-OBSISO-EPIC.md`'s child-ticket list updated to point at this hotfix
  instead.
- `TCK-20260702-OBSISO-EPIC` — parent epic tracking this batch.
- `TCK-20260702-OBSISO-BROKER-CONFIG` — must land before the deferred cross-process parity proof
  can be meaningful (not a hard blocker for this hotfix's own narrower scope).
- `TCK-20260702-OBSISO-ISOLATION-PROOF` — inherits the deferred cross-process grade-parity proof.

## Related Docs
- `docs/plans/observability_process_isolation.md` (G2) — original gap analysis; this ticket's
  Request Summary corrects its "no shared scorer-registry builder exists" claim, now stale.
- `docs/simulation_quality/quality_scoring_contract.md` — pillar/scorer contract.

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/simulation_quality/worker.py`
- `src/simulation_quality/scorers/__init__.py` (`build_all_scorers`, read-only reference)
- `src/engine/kernel.py:238-252` (structural precedent for the import/call shape, read-only
  reference)

## Assumptions / Open Questions
- Assumes `QualityHub`'s internal scorer storage is introspectable enough to write a coverage
  assertion without needing new instrumentation beyond the `/health` extension itself — verify
  during Implement.
- The deferred cross-process parity proof (real broker pipeline, two hub construction paths,
  identical `ScoreRecord` output) is a real gap this hotfix does NOT close on its own — flagged
  explicitly in Out of Scope rather than silently dropped, and explicitly handed to
  ISOLATION-PROOF's own scope.

## Implementation Notes
- `src/simulation_quality/worker.py`: `QualityWorker.__init__` now imports
  `build_all_scorers` from `src.simulation_quality.scorers` (same import shape as
  `src/engine/kernel.py:240`) and calls `scorers = build_all_scorers(weights)`, replacing the
  hardcoded `[AgencyScorer(weights), CombatScorer(weights)]`. The direct `AgencyScorer`/
  `CombatScorer` imports were removed — no other code in the file referenced them.
- `_HealthHandler.do_GET`: added a second `try/except Exception: pass` block (matching the
  existing `current_tick`/`run_id` block's fail-open pattern) that builds
  `payload["pillar_event_counts"]` as `{pid.value: hub._accumulators[pid].snapshot()["event_count"]
  for pid in PillarId}`. This reuses `QualityHub`'s existing per-pillar `PillarAccumulator`
  machinery (`quality_hub.py:111,168,170`) — no new counting mechanism was added. `PillarId` is a
  `str` Enum (`pillars.py`), so `pid.value` gives the plain pillar name (`"AGENCY"`, `"COMBAT"`,
  etc.) as the JSON key.
- `tests/simulation_quality/test_worker.py` (pre-existing file from the sibling
  TCK-20260702-OBSISO-BROKER-CONFIG session): added two tests.
  1. `test_quality_worker_hub_has_all_ten_pillars_represented` — constructs a real `QualityWorker`
     and asserts `{scorer.PILLAR_ID for scorers in hub.SCORER_REGISTRY.values() for scorer in
     scorers} == set(PillarId)`. Verified `QualityHub` has no `_scorers` attribute (confirmed by
     reading `quality_hub.py`) — `SCORER_REGISTRY` (built from each scorer's `EVENT_TYPES`) is the
     real introspection surface, and every one of the 10 scorer classes declares a non-empty
     `EVENT_TYPES`, so registry coverage is equivalent to pillar coverage.
  2. `test_quality_worker_health_payload_includes_per_pillar_event_counts` — feeds one
     `action_executed` envelope through `worker._hub.on_envelope(...)` (scores under AGENCY per
     `AgencyScorer`), then spins up a real `HTTPServer` bound to `_HealthHandler` on an
     OS-assigned port (`("127.0.0.1", 0)`), issues a real GET `/health` via `urllib.request`, and
     asserts the response JSON's `pillar_event_counts["AGENCY"] == 1` and that all 10 pillar keys
     are present. Chose a real HTTP round-trip over re-implementing the payload-building logic
     inline in the test, to avoid testing a duplicate of the shipped code path.
- Verified `make evaluate --dry-run` (`tools/evaluate_simq.py --dry-run`, the exact command the
  `evaluate` Makefile target runs) produces byte-identical output before and after this change
  (diffed via `git stash`/`git stash pop`) — confirms the in-process path is untouched, as expected
  since `worker.py` is broker-mode-only.
- Ran full `tests/simulation_quality/` suite: 448 passed, 79 skipped, 1 failed
  (`test_grade_regression.py::test_grade_anchor_file_exists_and_valid`, a `TypeError: 'NoneType'
  object is not subscriptable` from a missing calibration report file). Confirmed via `git stash`
  that this failure is pre-existing on the unmodified branch and unrelated to this change (it
  fails identically with `worker.py` reverted).
- Deleted the superseded `tickets/todos/obs-isolation/TCK-20260702-OBSISO-WORKER-PARITY.md` per
  this ticket's own Related Tickets instruction. Updated
  `tickets/todos/obs-isolation/SEQUENCE.md` (ticket 3's row and Dependency Notes) and
  `tickets/todos/obs-isolation/TCK-20260702-OBSISO-EPIC.md` (Related Tickets + a new
  Implementation Notes paragraph) to point at this hotfix instead. Also updated
  `TCK-20260702-OBSISO-ISOLATION-PROOF.md`'s Related Tickets, which still referenced the deleted
  ticket, for consistency (not explicitly called out in this ticket's own text, but the same
  supersession logic applies — leaving a dangling reference to a deleted file would be a new
  inconsistency).
- Did not move this ticket to `tickets/done/`, touch `tickets/working_log.csv`, or run the
  `data/runs/`/`reports/release_proof/` cleanup — those are Finalize-phase actions outside
  implementer scope; this ticket's own task explicitly scoped only the ticket-notes update and the
  Related Tickets supersession cleanup.

**Document-Update phase additions (found while auditing `docs/plans/observability_process_isolation.md`
for this ticket's own G2 update):** the sibling `TCK-20260702-OBSISO-BROKER-CONFIG` ticket's own
Document-Update phase never flagged this file for update, so G1 and G3 were still marked as open,
live bugs in this doc despite that ticket being fully `DONE` — a real staleness gap in an adjacent
section of the same file I was already editing. Fixed both (mirroring the G2/G4 RESOLVED pattern
exactly): G1 now cites `TCK-20260702-OBSISO-BROKER-CONFIG` and `INFRA-317`; G3 cites the same
ticket and `INFRA-318`. Updated §5's Ticket Map to mark both rows `(RESOLVED)` for consistency
with the WORKER-PARITY row's existing annotation. Also found and fixed a genuine, pre-existing
frontmatter defect this file always had — `status: proposal` is not a valid enum value per
`tools/validate_frontmatter.py` (`['active', 'archive', 'authoritative', 'historical']`); this had
apparently never been caught because no prior Document-Update pass ran the validator against this
specific file. Corrected to `status: active` (correct value — G5 remains genuinely open, so the
doc is not yet archivable/historical).

## Test Summary
- `tests/simulation_quality/test_worker.py` — 7 passed (5 pre-existing + 2 new).
- `tests/simulation_quality/` (full directory) — 448 passed, 79 skipped, 1 failed
  (pre-existing/unrelated, see Implementation Notes).
- `tools/evaluate_simq.py --dry-run` — output byte-identical before/after (diffed directly).

## Files Changed
- `src/simulation_quality/worker.py`
- `tests/simulation_quality/test_worker.py`
- `tickets/todos/obs-isolation/SEQUENCE.md`
- `tickets/todos/obs-isolation/TCK-20260702-OBSISO-EPIC.md`
- `tickets/todos/obs-isolation/TCK-20260702-OBSISO-ISOLATION-PROOF.md`
- `tickets/todos/obs-isolation/TCK-20260702-OBSISO-WORKER-PARITY.md` (deleted)
- `docs/plans/observability_process_isolation.md` (G2 marked RESOLVED; also G1/G3 marked RESOLVED
  and a pre-existing invalid `status: proposal` frontmatter value fixed to `active`, found while
  auditing this file)
- `docs/guides/simulation_quality.md` (documented new `pillar_event_counts` `/health` field)
- `docs/parity_ledger/infrastructure.yaml` (new `INFRA-319`, P0 — closes G2; no existing entry
  covered QualityWorker's scorer completeness, confirmed via `INFRA-318`'s own explicit
  `support_boundary` disclaimer)

## Completion Summary
Replaced `QualityWorker`'s hardcoded 2-pillar scorer list with the existing
`build_all_scorers(weights)` factory (already used by the in-process kernel path), so broker-mode
runs now score all 10 SimQ pillars instead of silently omitting 8. Extended the worker's `/health`
endpoint with a per-pillar event-count dict sourced from `QualityHub`'s existing
`PillarAccumulator` snapshots, so a future scorer-coverage regression is observable rather than
silent. Added test coverage for both. Confirmed `make evaluate --dry-run` (in-process path) is
unaffected. Superseded and deleted the original standard-tier `TCK-20260702-OBSISO-WORKER-PARITY`
ticket and updated the epic's sequencing docs to point at this hotfix.
