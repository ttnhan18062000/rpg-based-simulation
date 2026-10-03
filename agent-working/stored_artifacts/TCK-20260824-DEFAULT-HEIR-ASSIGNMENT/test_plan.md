---
status: historical
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260824-DEFAULT-HEIR-ASSIGNMENT
artifact_type: test_plan
tags: [social]
---

# Test Plan — TCK-20260824-DEFAULT-HEIR-ASSIGNMENT

## Regression Surface

**Unit — lifecycle (must keep passing unchanged):**
- `tests/unit/progression/test_lifecycle.py::test_aging_per_tick`
- `tests/unit/progression/test_lifecycle.py::test_death_by_old_age`
- `tests/unit/progression/test_lifecycle.py::test_combat_death_classification`
- `tests/unit/progression/test_lifecycle.py::test_permadeath_death_classification` — guards the
  `TCK-20260826-HOTFIX-PERMADEATH-LIFECYCLE-FIX` PERMADEATH branch this ticket's new code sits next to;
  must not regress.
- `tests/unit/progression/test_lifecycle.py::test_succession_and_heirloom_transfer` — the proven
  manual-heir-set + heirloom-transfer path; the new default-selection code must not alter this test's
  outcome (manual `heir_entity_id` set on the parent must still take priority, unchanged).
- `tests/unit/progression/test_lifecycle.py::test_near_death_hardening_logic` — unrelated pipeline test
  in the same file, must remain unaffected.

**Unit — social bonds (RelationshipService / SocialBond, adjacent subsystem):**
- `tests/unit/social/test_social_bonds.py`
- `tests/unit/social/test_relationships.py`
- `tests/unit/social/test_party_composition.py::test_party_composition_score_reflects_candidate_trust_history`
  — guards the one existing bond-derived weighted-formula precedent (`SOC-244` /
  `docs/mechanics/04_strategic_cognition.md` §7.2); this ticket must not accidentally couple into or
  alter `PartyCompositionScorer`/`score_trust_bonds()`.

**Integration — combat death → lifecycle wiring:**
- `tests/integration/kernel/` combat-death-adjacent tests exercising the full refine pipeline through
  `AuthoritativeApplyPipeline.refine` (identify via `test-scoper` at implementation time by files
  touched; at minimum confirm the pipeline order at `src/engine/pipeline.py:360` still calls
  `LifecycleSystem.resolve_lifecycle` once per tick with unchanged phase ordering relative to
  `near_death_hardening`/`occupancy_resolution`/`groups`).

**Apply-path wiring (must remain untouched and still pass):**
- Any existing test exercising `src/engine/patches.py::LifecyclePatch.apply` and its
  `heir_entity_id_set` branch (line 84) — confirm via `grep -rl LifecyclePatch tests/` at
  implementation time; this ticket must not modify `patches.py`.

## New Tests Required

All new tests live in `tests/unit/progression/test_lifecycle.py`, alongside
`test_succession_and_heirloom_transfer`, using the same `V2EntityBuilder`/`AuthoritativeState`/
`LifecycleSystem.resolve_lifecycle` fixture pattern already established in that file.

1. **`test_default_heir_selected_from_strongest_bond`**
   - Category: unit
   - Verifies: AC 1 — an active entity dies (`OLD_AGE` or `COMBAT`) with `heir_entity_id=None` and at
     least one `SocialBond` to a living entity; the entity with the (per the finalized formula)
     strongest/highest-scored live bond is selected, `LifecycleUpdate.heir_entity_id_set` is populated
     on the dying entity's own `EntityUpdate` (never a direct field mutation), and
     `resource_transfers` land on the selected heir's `EntityUpdate` in the **same tick**, matching
     `test_succession_and_heirloom_transfer`'s existing assertion shape (transfer intent present,
     contains the expected item(s)).
   - Location: `tests/unit/progression/test_lifecycle.py`

2. **`test_default_heir_prefers_strongest_bond_among_multiple_candidates`**
   - Category: unit
   - Verifies: AC 3 (determinism) in its non-tied form — given 2+ live bonded candidates with
     genuinely different scores under the finalized formula, the higher-scored candidate is always
     selected, not merely "a" candidate. Distinguishes "formula is applied" from "formula is a no-op
     that happens to pick the first/last bond."
   - Location: `tests/unit/progression/test_lifecycle.py`

3. **`test_default_heir_zero_bonds_no_heir_assigned`**
   - Category: unit
   - Verifies: AC 2 (first half) — an active entity dies with `heir_entity_id=None` and
     `social.bonds == {}`. No heir is assigned (`LifecycleUpdate.heir_entity_id_set` stays `None`), no
     `resource_transfers` are created for any entity, and no exception is raised. Inventory/heirlooms
     (if any) simply go untransferred — same as today's behavior when `heir_entity_id is None`.
   - Location: `tests/unit/progression/test_lifecycle.py`

4. **`test_default_heir_all_bonded_targets_dead_or_missing_no_heir_assigned`**
   - Category: unit
   - Verifies: AC 2 (second half) — an active entity dies with `heir_entity_id=None` and one or more
     bonds, but every bonded `target_id` is either absent from `state.entities` or present with
     `lifecycle.active=False`. No heir is assigned, no exception is raised. This is the test that
     specifically exercises the **new, stricter** liveness filter (existence AND `.lifecycle.active`)
     that this ticket adds — distinct from the pre-existing manual-heir-transfer `if heir:` check, which
     this test must not exercise or depend on.
   - Location: `tests/unit/progression/test_lifecycle.py`

5. **`test_default_heir_selection_deterministic_across_repeated_calls`**
   - Category: unit / determinism-replay-parity regression (required by AC 3 and ticket Scope)
   - Verifies: calling `LifecycleSystem.resolve_lifecycle(state, update)` multiple times against
     byte-identical `state`/`update` inputs (same dying entity, same `social.bonds` dict contents)
     always selects the same heir — proving no dependence on dict/hash iteration order, object
     identity, or any non-deterministic source (e.g. `id()`, `hash()`, unseeded `random`). Recommended
     shape: construct the bonds dict twice with a different insertion order for the same
     `{target_id: SocialBond}` pairs (e.g. via two dicts built by iterating a reversed candidate list)
     and assert both produce the identical selected heir ID. This directly targets "no hash-order
     dependence" from the ticket's Scope, which a same-input/same-call-repeated test alone would not
     catch (Python dict iteration is already insertion-order-stable within one process, so a naive
     repeat-the-same-call test could pass even with an order-dependent implementation bug; varying
     insertion order is the actual regression guard).
   - Location: `tests/unit/progression/test_lifecycle.py`

6. **`test_default_heir_tie_break_deterministic`**
   - Category: unit
   - Verifies: two or more live bonded candidates score exactly equal under the finalized formula
     (construct `SocialBond`s with identical `familiarity`/`sentiment`); the documented tie-break rule
     (e.g. lowest/highest `target_id`) is applied consistently and matches
     `docs/mechanics/04_strategic_cognition.md`'s new subsection exactly. This is the direct AC 4 /
     "exact tie-break formula matching code" regression guard, distinct from test 5 above (which
     guards non-tied, order-independence; this one guards the explicit tie-break rule itself).
   - Location: `tests/unit/progression/test_lifecycle.py`

7. **`test_default_heir_does_not_override_manual_heir_entity_id`**
   - Category: unit / anti-drift guard
   - Verifies: when `heir_entity_id` is already manually set (non-`None`), the new default-selection
     logic never runs/never overrides it, even if stronger bonded candidates exist — i.e.
     `test_succession_and_heirloom_transfer`'s exact scenario, but with an additional live bonded
     candidate added to the dying entity's `social.bonds` that would "win" under the new formula, to
     positively prove the manual path still takes precedence (not just "the old test still passes,"
     which could be true by coincidence if the new logic is gated wrong).
   - Location: `tests/unit/progression/test_lifecycle.py`

8. **Parity ledger test** — the `test_path` cited in the new `docs/parity_ledger/social_narrative.yaml`
   entry (proposed `SOC-245`) must point at one of the above tests (recommend test 1 or 6, whichever
   most directly demonstrates the documented formula) so the entry is verifiable, per this project's
   Authoritative Mechanics Rule.

## Scoped Pytest Commands

```
pytest tests/unit/progression/test_lifecycle.py -v
pytest tests/unit/social/test_social_bonds.py tests/unit/social/test_relationships.py tests/unit/social/test_party_composition.py -v
pytest tests/unit/progression/ tests/unit/social/ -v -m "not slow"
```

Never `pytest tests/`. If implementation touches `src/engine/pipeline.py` phase wiring or
`src/engine/patches.py` (not expected per this investigation, but re-check if the plan changes shape),
add:
```
pytest tests/integration/kernel/ -v -m "not slow"
```

## Anti-Drift Test Guards

- **`test_succession_and_heirloom_transfer` itself is the primary anti-drift guard** for "manual
  `heir_entity_id` still wins" — already covered under Regression Surface; test 7 above strengthens it
  further by adding a competing bonded candidate.
- **`test_permadeath_death_classification`** guards against this ticket accidentally coupling into or
  reordering the `PERMADEATH`/`KILL` combat-death check added by the prior hotfix — the new
  heir-selection code must be purely additive after death classification, never conditional on
  `death_reason` in a way that silently changes when death is detected.
- **A negative test for the existing manual-heir liveness check (`if heir:`) staying unchanged**: add
  or confirm a test asserting that a manually-set `heir_entity_id` pointing at an entity that is
  *present but `lifecycle.active=False`* still receives the transfer under the pre-existing (looser)
  `if heir:` check — i.e. explicitly prove the manual path's existing behavior was not tightened as a
  side effect of adding the new, stricter default-selection filter. If no such test exists today, add
  one; this directly guards the investigation's flagged "do not modify the existing check" hazard.
- **`test_party_composition.py`'s trust-bonus test** guards against accidental reuse/coupling of
  `TRUST_BONUS_WEIGHT`/`score_trust_bonds()` into the new heir-selection formula (the investigation
  flags this as a real risk given both mechanics live in the same Mechanics Bible chapter).
- **A no-op guard**: a scenario with an active entity dying, `heir_entity_id=None`, and `social.bonds`
  containing only bonds to entities that are alive but themselves have `heir_entity_id` already set
  (i.e. confirm the new logic never looks at or is influenced by the *candidate's own* lifecycle/heir
  fields other than `.active` — only the dying entity's bonds and the candidate's liveness matter).
