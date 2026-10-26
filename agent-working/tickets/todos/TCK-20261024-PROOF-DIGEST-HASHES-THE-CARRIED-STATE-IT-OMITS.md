---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS
phase: open
date: 2026-10-24
tags: [performance, determinism]
---

# TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS

## Title
The proof digest hashes the seven carried-state fields it omits: a new `flat-sha256` scheme version, the fixture re-pinned, and the v1 base re-recorded

## Status
OPEN

Unblocked 2026-10-26: HUNGER step B is on main (#753, `3533fde71`; ruling (ii) as `DIGEST_EXCLUDED_COMBAT_KEYS` / `_entity_digest_form`, pinned by a test). rpg-planner granted the co-edit lift (#593 issuecomment-6420451647).

**Lift scope:**
- `src/engine/checkpoint.py`
- `docs/engine/deterministic_execution.md`, `docs/engine/known_limitations.md` and `substrate_baseline_contract.md`, only where they cite the digest scheme
- the INFRA parity rows for the digest

**Conditions:**
1. Digest scheme only. No change to restore or replay semantics, or to the checkpoint payload shape. F3 (`rpg-checkpoint-restore-randoms`, `scenario_checkpoint.py`) owns restore; ask rpg before touching `scenario_checkpoint.py`.
2. The proofs:
   - the v3-minus-7 = v2 migration proof
   - a positive control per field
   - a cross-PYTHONHASHSEED check
   - each `FIXTURE_DIGEST` / digest-pinned re-pin named in the PR's Review notes; only digests move
   - `paired --neutral` IDENTICAL on 3 worlds × s42, stated as a neutrality measure, not behaviour coverage
3. rpg (rpg-planner or rpg-designer) reviews the PR's docs and ledger rows; merge stays the owner's.
4. F1 may be coded and opened in parallel with HUNGER step A. It does not merge while step A's PR is open unless rpg is told first.
5. rpg re-records v1 under v3 (§12.5) on the u24 host after the merge; perf checks that only the digests move.

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`CanonicalStateHasher.to_canonical_data` (`src/engine/checkpoint.py:94-168`) leaves out mutable durable state that
`ApplyPath.apply_generation` carries forward every tick (`src/engine/apply.py:529,543-547`):

1. `item_instances`
2. `recent_world_events` (rpg-planner, #593 2026-10-22: carried state, not a view; the run ledger reads it)
3. `quest_registry`
4. `factions`
5. `clans`
6. `information_providers`
7. `CombatComponent.last_hit_tick`, added unhashed by HUNGER step B under the owner's ruling (ii) (#593
   issuecomment-6384425767)

A divergence in any of them is invisible to the final hash, to paired P1 hash-equality proofs and to mode
conformance. The replay fingerprint does not cover them either (conformance_suite_design.md). Source: the port-leak
audit, finding F1 (`TCK-20261022-ARCHITECTURE-PORT-LEAK-AUDIT`, `docs/plans/architecture/port_leak_audit.md` §7).
The v1 record states that the baseline cannot vouch for the six.

Hashing them changes every state digest. Under PERF-D5 that needs a new scheme version, and under the roadmap's
§12.5 "Hash scheme" rule, the v1 base has to be re-recorded under the new scheme before any M1 paired or gate
comparison uses it. The owner approved both on 2026-10-24 (#715 issuecomment-6384423281), starting after step B.

## Scope
- **Scheme:** `PROOF_DIGEST_SCHEME` → `flat-sha256-v3`. The v3 canonical data is the v2 data plus the seven fields,
  nothing else changed (the same shape as the v1→v2 update in PERF-D5).
  - Each field gets a deterministic canonical form: sorted keys, ids as strings, collections sorted by a stable
    key, and the same float handling as the existing fields. No `hash()`, no `id()`, no set iteration order.
  - `recent_world_events` is hashed as the ordered window it is.
- **Removing the step-B exclusion:** step B ships an explicit exclusion of `last_hit_tick` and a test that pins it.
  This ticket removes that exclusion and flips the test.
- **Fixture:** `tests/unit/engine/test_proof_digest_contract.py` gets `FIXTURE_DIGEST_V3`, and the fixture gains
  non-empty values for all seven fields.
  - Add a migration proof in the style of the existing v1→v2 one: v3 data minus the seven keys reproduces
    `FIXTURE_DIGEST_V2` exactly.
  - Add a positive control per field: changing that field alone changes the v3 digest. That is seven cases.
- **Scheme callers:** every place that names the scheme, from a search of main on 2026-10-24:
  - `src/perf/benchmark_record.py`, `src/perf/long_run_harness.py`, `tools/perf/hash_callsite_inventory.py`
  - `tests/unit/engine/test_hash_scheduler.py`, `test_kernel_digest_via_scheduler.py`,
    `tests/unit/perf/test_benchmark_record.py`
  - Re-run the search before closing.
- **Perf docs:**
  - `benchmark_identity_schema.md` (scheme enum)
  - `baseline_invalidation_ledger.md` (a row: every digest-bearing baseline is invalidated by the scheme)
  - `hash_callsite_inventory.{md,json}` (regenerated)
  - the PERF-D5 amendment in `performance_optimization_decisions.md` (owner sign-off in this PR)
- **rpg-owned docs, rpg co-edit:** `docs/engine/deterministic_execution.md`, `known_limitations.md`,
  `contracts/substrate_baseline_contract.md`, the INFRA parity-ledger entries that cite the scheme, and
  `intentional_divergences.md` if it cites v2.
- **v1 base re-record:** re-record the v1 base (simulation `e8df8b96d`) under v3 per roadmap §12.5. rpg owns the
  record and its harness; perf supplies the scheme and checks that the re-record's outcomes (fates, counters) equal
  v1's, with only the digests moving.

## Out of Scope
- Any change to which state exists or how it evolves. This is hash coverage only: a hash-neutral claim on
  outcomes, a digest-moving change on hashes.
- The `pressure_signals` `ENABLE_*` back door (port-leak F5, rpg's ticket) and the id counters. Hashing
  `pressure_signals` is only needed if rpg keeps that mapping.
- Hierarchical or incremental hashing (C-09, Gate A).
- F3 and F4 (rpg's restore-seed and salted-`hash()` tickets), although F4 must land before the A0 cross-hashseed
  case can mean anything.

## Acceptance Criteria
- [ ] `PROOF_DIGEST_SCHEME == "flat-sha256-v3"`, and the v3 canonical data = the v2 data plus exactly the seven keys.
- [ ] `FIXTURE_DIGEST_V3` is pinned.
- [ ] The v3-minus-seven-keys migration proof reproduces `FIXTURE_DIGEST_V2`.
- [ ] Seven per-field positive controls pass.
- [ ] The step-B `last_hit_tick` exclusion and its test are removed or flipped.
- [ ] Determinism: same seed, two processes, different `PYTHONHASHSEED`, 3 worlds × 300 ticks under `audit_mode`
      give identical v3 digests. This is the check that each canonical form is order-stable.
- [ ] Outcome neutrality: on 3 worlds × s42 × 1000 ticks, fates and counters are identical before and after. Only
      the digests differ.
- [ ] Every scheme caller and doc in Scope is updated, and the search for `flat-sha256-v2` outside history and
      tickets returns only the PERF-D5 history and the migration-proof constant.
- [ ] The PERF-D5 amendment is in `performance_optimization_decisions.md`, with the owner's approval recorded in
      the PR.
- [ ] The baseline-invalidation-ledger row is written.
- [ ] The v1 base is re-recorded under v3 (rpg) before any M1 paired or gate comparison, with outcomes equal to v1.
- [ ] The cost of the wider digest is measured: same host, phase-7 digest share on `strategic_100` and
      `frontier_extended` before and after, in a lead-granted slot. PROVISIONAL.

## Related Tickets
- `TCK-20261022-ARCHITECTURE-PORT-LEAK-AUDIT` (finding F1)
- rpg HUNGER step B (adds `last_hit_tick`, unhashed under ruling (ii))
- `TCK-20261019-RECORD-BASELINE-V1` (#725): the base to re-record
- `TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`: the v1→v2 precedent
- `TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED`: the phase-7 digest cost method

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` PERF-D5
- `docs/plans/architecture/port_leak_audit.md` §7
- `docs/plans/architecture/conformance_suite_design.md` (C1 canary, §4.2 side digest)
- roadmap §12.5 "Hash scheme"
- `docs/performance/baseline_invalidation_ledger.md`, `benchmark_identity_schema.md`, `hash_callsite_inventory.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE/`

## Related Code Areas
- `src/engine/checkpoint.py` (rpg co-edit or lift needed: `src/engine` is rpg's)
- `src/perf/benchmark_record.py`, `src/perf/long_run_harness.py`
- `tools/perf/hash_callsite_inventory.py`
- `tests/unit/engine/test_proof_digest_contract.py`

## Assumptions / Open Questions
- The `checkpoint.py` change is a co-edit with rpg-planner: the scheme is perf's, the file is rpg's. The lift was granted 2026-10-26 (see Status).
- Whether the suite-only side digest of the conformance design (§4.2) is retired by this ticket or kept as a canary.
  The default: C1 becomes an assertion on the v3 digest, and the side digest is dropped.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
