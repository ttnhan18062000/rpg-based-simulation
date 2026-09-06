---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE
artifact_type: test_plan
tags: [core, faction]
---

# Test Plan — TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE

## Regression Surface

Existing tests that must keep passing — grouped by domain, since a real `faction_set` producer
touches identity, apply-path, legality, observability, and replay simultaneously.

**Unit — identity/updates:**
- `tests/unit/core/` (identity/update-merge coverage, e.g. wherever `IdentityUpdate.merge()`/
  `is_noop()` are exercised — confirm exact file at implementation time via
  `grep -rl "IdentityUpdate" tests/unit/core/`)
- `tests/unit/observability/test_event_extractor_identity.py` — the 9 existing tests for
  `entity_role_changed`/`entity_faction_changed`/`recipe_learned`/`skill_cooldown_started` must
  still pass unmodified; this ticket must not need to touch this file's assertions (only add new
  ones if a real-kernel-reachable path is confirmed).
- `tests/unit/observability/test_event_shapers_deferred_instrumentation.py` — covers the
  `faction_extinct` event shaper path that already reads `faction_set` defensively
  (`event_shapers.py:1392`).

**Unit — social systems (candidate trigger surface):**
- `tests/unit/social/test_party_lifecycle.py` — `check_defection()` coverage; must not regress if
  this ticket extends or reuses this trigger.
- Any existing contract-betrayal tests under `tests/unit/social/` covering
  `SocialContractSystem.resolve_contract_outcome()`.

**Unit — engine/legality (the 6 cited sites plus adjacent):**
- `tests/unit/engine/test_combat_relation_projection.py`
- `tests/unit/engine/test_pressure_perception_consumers.py`
- Any `tests/unit/engine/` file covering `LegalityServiceV2.verify_attack_legality()`,
  `get_engaged_hostiles_at_pos()`, `is_flanked`/`is_surrounded` — confirm exact set via
  `grep -rl "verify_attack_legality\|get_engaged_hostiles" tests/unit/engine/`.

**Integration / architecture:**
- `tests/architecture/test_social_write_paths.py` — the precedent pattern this ticket's own new
  guard test should follow (see New Tests Required); must keep passing unmodified since it guards
  a different field (`public_reputation`/`regional_reputation`).
- `tests/static/test_semantic_entity_index_no_stateupdate_write.py`,
  `tests/static/test_semantic_entity_index_returns_ids_only.py` — `semantic_entity_index.py:163`
  buckets by `identity.faction`; must not regress if faction becomes live-mutating.

**Arena-combat / determinism:**
- Any `tests/unit/replay/` or `tests/integration/` coverage of `StateFingerprinter.
  get_fingerprint()` and `CanonicalStateHasher` — both must be re-run since this ticket changes
  what `get_fingerprint()` covers (AC #6).
- Certification harness tests touching `src/certification/harness.py`'s 3 `identity.faction` read
  sites (alive-faction-set computation) — confirm via
  `grep -rl "certification.harness\|CertificationHarness" tests/`.

## New Tests Required

Per acceptance criteria:

1. **AC #1 — real trigger populates `faction_set` through the authoritative apply-path only.**
   - Test name: `test_<trigger_name>_produces_faction_set_via_apply_path` (e.g.
     `test_defection_produces_faction_reassignment_via_apply_path` if the chosen trigger extends
     `check_defection`, or named for whatever concrete trigger the Plan phase selects).
   - Category: unit
   - Verifies: constructing the real trigger condition (e.g. grievance threshold met) produces an
     `EntityUpdate(identity=IdentityUpdate(faction_set=<new_faction>))`, and that
     `entity.identity.faction` only changes after this update is run through `ApplyPath`/
     `patches.py` — never via direct `dataclasses.replace(entity.identity, faction=...)` anywhere
     in the trigger's own code.
   - Location: alongside the trigger's existing test file (e.g.
     `tests/unit/social/test_party_lifecycle.py` if `check_defection` is extended, or a new
     `tests/unit/social/test_affiliation_mutation.py` if a dedicated new trigger function is
     added).

2. **AC #2 — `entity_faction_changed` fires exactly once per real faction change.**
   - Test name: `test_entity_faction_changed_fires_once_on_real_trigger`
   - Category: unit (extends the existing hand-built-state pattern already used in
     `test_event_extractor_identity.py`)
   - Verifies: running the new trigger through a real (or hand-built, per the repo's own
     precedented pattern from `TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP`)
     tick produces exactly one `entity_faction_changed` event per entity whose faction actually
     changed, with correct `payload={"faction": ..., "previous_faction": ...}`, and zero events
     for entities whose faction did not change.
   - Location: `tests/unit/observability/test_event_extractor_identity.py` (extends the existing
     file rather than duplicating its setup).

3. **AC #3 — mid-tick vs next-tick-boundary legality semantics, documented and tested.**
   - Test name: `test_faction_change_mid_tick_legality_semantics` (exact name depends on the
     Plan-phase decision of which semantics is chosen — "takes effect immediately" vs "next tick
     boundary")
   - Category: integration
   - Verifies: an entity that changes faction mid-tick has the documented, deterministic effect on
     a concurrently-resolving `verify_attack_legality()`/`get_engaged_hostiles_at_pos()` call
     against it — either immediately reflecting the new faction (if apply.py's existing cache
     invalidation at line 321 is relied on) or provably still using the pre-change faction for
     that tick's already-queued actions (if next-tick-boundary semantics is chosen). Must assert
     the specific chosen behavior, not merely "it doesn't crash."
   - Location: `tests/unit/engine/test_legality_faction_mutation.py` (new file, since no existing
     legality test file covers a live faction mutation scenario).

4. **AC #4 — documented in a real, citable doc.** No test required (doc-coverage is verified by
   `done-checker`'s static check, not pytest) — but add a doc-existence assertion if the chosen
   doc introduces a machine-checkable contract (e.g. a schema/format the new doc claims to
   guarantee).

5. **AC #5 — parity-ledger entries added, each with a real `test_path`.**
   - Not a new test per se — but every new parity entry's `test_path` must point at one of the
     new tests in this list (items 1-3, 6), and this test plan's Scoped Pytest Commands must
     include those paths so the Parity phase's own verification can run them.

6. **AC #6 — `src/replay/fingerprint.py` coverage confirmed for the new/changed field(s).**
   - Test name: `test_fingerprint_changes_when_faction_changes`
   - Category: unit
   - Verifies: `StateFingerprinter.get_fingerprint(state)` produces a different string before and
     after an entity's `identity.faction` changes (currently it does NOT — `role`/`faction` are
     absent from `fingerprint.py:56-72`'s per-entity string). This test should be written to FAIL
     against the current code (documenting the gap) and PASS once the fingerprint fix lands —
     the classic regression-guard-added-alongside-the-fix pattern.
   - Location: new or extended file under `tests/unit/replay/` (confirm exact existing file via
     `grep -rl "StateFingerprinter" tests/unit/`; create `tests/unit/replay/
     test_fingerprint_identity_coverage.py` if none exists).

7. **Architecture guard — single-authoritative-writer for `faction_set`.**
   - Test name: `test_faction_set_write_restricted_to_authoritative_writer`
   - Category: architecture guard
   - Verifies: following the exact precedent of `tests/architecture/test_social_write_paths.py`
     (`TCK-20260904-REPUTATION-LOCALITY-SCOPE`'s single-authoritative-writer pattern), scan `src/`
     for the write-pattern `faction_set=` (and, separately, direct `identity.faction=`/
     `replace(..., faction=...)` writes bypassing `IdentityUpdate`) and assert only the field
     declaration (`updates.py`), the apply-path consumer (`patches.py`), and the new trigger's own
     file appear — any other file constructing `IdentityUpdate(faction_set=...)` or mutating
     `identity.faction` directly fails the test.
   - Location: `tests/architecture/test_faction_mutation_write_paths.py` (new file, sibling to
     `test_social_write_paths.py`).

## Scoped Pytest Commands

```
pytest tests/unit/core/ tests/unit/social/ tests/unit/engine/ tests/unit/observability/test_event_extractor_identity.py tests/unit/observability/test_event_shapers_deferred_instrumentation.py -m "not slow"
pytest tests/architecture/ -m "not slow"
pytest tests/unit/replay/ -m "not slow"
pytest tests/static/test_semantic_entity_index_no_stateupdate_write.py tests/static/test_semantic_entity_index_returns_ids_only.py
```

Never `pytest tests/` — scoped to core/social/engine/observability/architecture/replay/static
domains directly touched by this ticket's blast radius (identity mutation, apply-path, legality,
observability, replay fingerprint).

## Anti-Drift Test Guards

- **`test_faction_set_write_restricted_to_authoritative_writer`** (item 7 above) is itself the
  primary anti-drift guard: it directly prevents a future change from reintroducing a second,
  bypassing write path to `identity.faction`, the same class of regression
  `test_social_write_paths.py` already prevents for `public_reputation`/`regional_reputation`.
- **`test_entity_faction_changed_fires_once_on_real_trigger`** guards against the observability
  event silently double-firing or under-firing if the chosen trigger's `EntityUpdate` merge logic
  changes later (e.g. if a future ticket makes two systems both attempt to set `faction_set` in
  the same tick — `IdentityUpdate.merge()`'s current `if other.faction_set is not None:
  changes["faction_set"] = other.faction_set` silently takes the *last* merged value with no
  conflict detection; a guard test asserting deterministic last-write-wins order, or flagging if
  two systems compete for the same tick, would catch silent behavior change here).
- **A test explicitly scoped to `check_defection()` NOT independently starting to set
  `faction_set` unless it is the ticket's actual chosen trigger** — if the Plan phase chooses a
  different trigger (e.g. a dedicated new function rather than extending `check_defection`), add
  a guard asserting `check_defection()`'s returned `EntityUpdate` still has `identity is None`
  (or `faction_set is None`), preventing accidental scope bleed into a trigger this ticket did not
  actually choose to modify.
- **A guard against idea-56 scope creep**: if the implementation introduces any loyalty/pressure-
  accumulation state (fields resembling "loyalty_score", "affiliation_pressure", etc.) on
  `IdentityComponent`/`EntityState`, that is idea 56's own scope
  (`TCK-20260905-DRIFTING-LOYALTY-SIGNAL`) — a simple static grep-based guard test (same style as
  the architecture guards above) asserting no such field exists yet would catch an accidental
  scope expansion during this ticket's own implementation.
- **`test_fingerprint_changes_when_faction_changes`** (item 6) doubles as an anti-drift guard for
  any *future* new `IdentityComponent` field: it establishes the precedent that
  `StateFingerprinter` must be updated whenever `to_canonical_dict()` gains new replay-visible
  fields, closing the exact gap class PR #128's architecture review caught.
