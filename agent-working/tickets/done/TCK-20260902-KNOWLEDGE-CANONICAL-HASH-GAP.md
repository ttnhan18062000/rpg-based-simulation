---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP
phase: done
date: 2026-09-02
tags: [cognition, determinism]
---

# TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP

## Title
Close the StrategicComponent canonical-hash coverage gap (including live source_trust)

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P0

## Request Summary
**Correction on pickup (2026-09-03):** the original finding's consumer claim was wrong — verified
directly against current code, `EntityState.to_canonical_dict()`'s output is NOT `world_compile_report.json`'s
`state_hash` (that comes from the separate, already-known-lightweight `StateFingerprinter.get_fingerprint()`,
`src/replay/fingerprint.py`). The real consumer is `CanonicalStateHasher.to_canonical_data()`/`get_hash()`
(`src/engine/checkpoint.py:63-93`), which calls `to_canonical_dict()` directly and is used by
`src/engine/kernel.py` for both the per-tick audit hash (line 1161-1162) and the final run hash (line
1230-1231), plus `src/certification/harness.py` and dozens of determinism/replay/integrity tests. This
makes the underlying finding *more* significant, not less — it's the kernel's own per-tick determinism
check, not a one-off world-compile artifact.

Also re-verified the field gap itself against current code (`src/core/strategic.py`, post-M3-merge) since
M3 landed after the original investigation and changed coverage (`beliefs`/`marriages` are now covered,
which they weren't before): the real current gap is **9 fields**, not 6 — `home_region_id`,
`candidate_zones`, `hypotheses`, `source_trust`, `contracts`, `turning_points`, `committed_intentions`,
`primary_overload_source`, `last_overload_tick`. `source_trust` (`SourceTrustEntry`) remains confirmed
live — real scoring input to detour selection (`belief_and_detour_contract.md`'s `source_trust_bonus`
term) — and `home_region_id`/`primary_overload_source`/`last_overload_tick` are newly confirmed live too
(`RoutineService` gates on `home_region_id`; both overload fields are exported via
`state_presenter.py`/`cognition_export.py`/the observability recorder). `profile: CognitionProfile` is
the one legitimate exclusion — its own docstring states it is "Derived from entity attributes," fully
reconstructable from already-covered `attributes`, so a divergence there cannot be independent of
already-detected state.

## Scope
- Add the 9 confirmed-live fields to `EntityState.to_canonical_dict()`'s `"strategic"` sub-dict:
  `home_region_id`, `candidate_zones`, `hypotheses`, `source_trust`, `contracts`, `turning_points`,
  `committed_intentions`, `primary_overload_source`, `last_overload_tick`.
- Exclude `profile` explicitly, with a code comment stating why (derived from already-covered
  `attributes`).
- Update the relevant `docs/parity_ledger/` shard (`strategic_cognition.yaml`) via
  `tools/parity_ledger_writer.py` (never a raw YAML edit).
- Update `docs/core/state.md` if its canonical-hash coverage claims reference `StrategicComponent`.
- Correct any doc that names `world_compile_report.json`'s `state_hash` as the canonical-hash consumer —
  it isn't; `CanonicalStateHasher`/kernel's per-tick audit hash is the real one (see corrected Request
  Summary above).

## Out of Scope
- The `BeliefEntry`/`KnowledgeFact` unreconciled-parallel-systems question (tracked separately, see
  Related Tickets) — that is an architecture-reconciliation question, not a coverage gap.
- `SocialComponent`'s parallel gap (separate ticket) — land independently.
- Any change to `source_trust`'s own scoring formula or `source_trust_bonus` behavior — this ticket adds
  hash coverage only, it does not change how the field is used.

## Acceptance Criteria
- [x] All 9 currently-uncovered fields (plus `profile`) have an explicit, recorded decision (covered or
      justified-excluded). All 9 added; `profile` excluded with an inline code comment.
- [x] `source_trust` specifically is either added to the canonical hash or has an explicit, reviewed
      rationale on record for exclusion despite being behaviorally live. Added.
- [x] New or updated determinism test demonstrates the fix actually catches a divergence in the added
      field(s) (fails before, passes after). Verified manually pre-fix (source_trust divergence produced
      identical `to_canonical_dict()`/hash output) and confirmed post-fix via 3 new tests, all passing.
- [x] Existing canonical-hash/replay determinism tests still pass unchanged. 408 passed, 1 skipped
      (pre-existing, unrelated), 0 failed across `tests/unit/core/`, `tests/unit/engine/`,
      `tests/unit/kernel/`, `tests/certification/`.
- [x] Parity ledger entries reflect the new status with real evidence (no fabricated citations).
      `STRAT-268` added via `tools/parity_ledger_writer.py`, index confirmed FRESH.

## Related Tickets
- TCK-20260902-SOCIAL-CANONICAL-HASH-GAP (parallel gap, SocialComponent — separate PR)

## Related Docs
- `docs/brainstorm/2026-09-02-core-rpg-knowledge-belief-axis-proposal.md` (source investigation, §2.2)
- `docs/simulation/belief_and_detour_contract.md` (corrected path — was misfiled as `docs/cognition/`
  in the original investigation; checked directly, contains no canonical-hash/determinism claims that
  needed correcting)
- `docs/core/state.md`

## Related Stored Artifacts
(none yet — investigation already captured in the brainstorm doc above; standard staging artifacts to
be created when this ticket is picked up for implementation)

## Related Code Areas
- `src/core/state.py` (`EntityState.to_canonical_dict()`, "strategic" sub-dict, ~line 783)
- `src/core/strategic.py` (`StrategicComponent` — moved out of `state.py` since the original
  investigation, post-M3-merge)
- `src/engine/checkpoint.py` (`CanonicalStateHasher` — the real consumer)
- `src/engine/kernel.py` (per-tick and final hash computation call sites)
- `docs/parity_ledger/strategic_cognition.yaml`

## Assumptions / Open Questions
- Whether all 6 missing fields should be added, or whether some (e.g. `contracts`, `hypotheses`) are
  legitimately excluded as derived/non-authoritative — needs a field-by-field decision, not a blanket one.
- Whether `source_trust`'s exclusion has ever caused an observed real-world replay mismatch (worth a
  quick check of existing replay-mismatch incident history before implementing, per the axis doc's own
  open question).
- Adding fields to the canonical hash changes `state_hash` for any world compiled after this lands —
  confirm whether existing golden/reference `world_compile_report.json` fixtures need regeneration.
- Coordinate with the concurrent M3 implementation session before touching `src/core/state.py` — this is
  a shared, central file; confirm no active M3 work is mid-flight on the same lines first.

## Implementation Notes
Re-verification against current code (post-M3-merge) found the original investigation's premise and
field count both stale — see the corrected Request Summary above. Concretely:
- `StrategicComponent` moved from `src/core/state.py` into its own module, `src/core/strategic.py`,
  between the investigation and pickup.
- M3's merge added canonical-hash coverage for `beliefs`/`marriages`, which weren't covered when the
  investigation was written — shrinking what would have been an 11-field gap to 9.
- The claimed consumer (`world_compile_report.json`'s `state_hash`) is wrong — that comes from
  `StateFingerprinter.get_fingerprint()` (`src/replay/fingerprint.py`), which is explicitly documented as
  a lightweight, non-canonical fingerprint. The real consumer of `to_canonical_dict()` is
  `CanonicalStateHasher` (`src/engine/checkpoint.py`), used directly by `src/engine/kernel.py` for its
  per-tick audit hash and final-run hash — a higher-frequency, more central check than the original
  framing implied.
- `profile: CognitionProfile` was the one field deliberately excluded: its own docstring states it is
  "Derived from entity attributes," so it carries no independent authoritative information once
  `attributes` is already covered.
- Enum-valued fields (`ContractState.kind`/`status`, `TurningPointState.kind`) are wrapped with `str()`
  in the new code, matching the existing `projects` field's established convention, even though these are
  `str`-subclassing enums where it's technically redundant — kept for consistency with house style.
- `source_trust`'s `Dict[int, ...]` keys are wrapped with `str()` for the same reason `social`'s
  int-keyed history dicts already do (JSON-dict-key safety).

## Test Summary
- 3 new tests added to `tests/unit/core/test_entity_integrity.py`:
  `test_strategic_source_trust_participates_in_canonical_hash`,
  `test_strategic_all_nine_newly_covered_fields_participate_in_canonical_hash`,
  `test_strategic_profile_excluded_from_canonical_hash`. All pass.
- Confirmed end-to-end via manual script: a `source_trust` divergence now produces different
  `CanonicalStateHasher.get_hash()` output (previously produced identical output — the exact gap this
  ticket closes).
- Full scoped run: `pytest tests/unit/core/ tests/unit/engine/test_hash_scheduler.py
  tests/unit/engine/test_resource_budget_gate.py tests/unit/kernel/ tests/certification/ -m "not slow"` →
  408 passed, 1 skipped (pre-existing, unrelated), 0 failed.
- Also ran `tests/integration/kernel/test_determinism_suite.py`,
  `tests/integration/kernel/test_checkpoint_reproducibility.py`,
  `tests/integration/kernel/test_replay_fidelity.py` → 15 passed.

## Files Changed
- `src/core/state.py` — `EntityState.to_canonical_dict()`'s `"strategic"` sub-dict: added 9 fields,
  excluded `profile` with an explanatory comment.
- `tests/unit/core/test_entity_integrity.py` — 3 new tests.
- `docs/parity_ledger/strategic_cognition.yaml` — new entry `STRAT-268`, written via
  `tools/parity_ledger_writer.py`.
- `tickets/inprogress/TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP.md` → moved to `tickets/done/`.

## Completion Summary
Closed the `StrategicComponent` canonical-hash coverage gap. The real gap (9 fields, not the originally
estimated 6) is now fully covered in `EntityState.to_canonical_dict()`, including `source_trust` — the
field confirmed behaviorally live via `source_trust_bonus` in detour selection. Corrected two false
claims picked up from the original investigation along the way: the actual consumer of this hash is
`CanonicalStateHasher` via `src/engine/kernel.py`'s per-tick/final-run determinism checks (not
`world_compile_report.json`), and `StrategicComponent` now lives in `src/core/strategic.py`, not
`state.py`. `profile` is the one legitimate exclusion, now documented inline. All existing
determinism/replay/certification tests still pass unchanged; 3 new tests lock in the fix.
