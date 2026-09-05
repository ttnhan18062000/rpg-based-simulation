---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE
phase: done
date: 2026-09-05
tags: [core, faction]
---

# TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE

## Title
Affiliation's real change path (M6 idea 39) — the authoritative faction-mutation primitive

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
No entity today has a real, event-driven path to change `identity.faction` after construction — the
field is set once at birth/spawn and never mutated by any live system. Idea 39 (M6 epic child 1 of
3, `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY`) establishes that mutation primitive first, per the
2026-08-29 plan-owner decision confirmed in the epic's own scope: idea 39 is not split into a
separate primitive/trigger pair, and it lands before idea 56 (Drifting Loyalty) so idea 56's derived
signal has a real path to request/influence.

**Confirmed real, not assumed, before this ticket's own Investigate phase re-confirms at
implementation time:**
- The write-side apply-path already exists and is idle: `IdentityUpdate.faction_set: Optional[int]`
  (`src/core/updates.py:227`) is a real, typed field, threaded through `apply.py:321`'s dirty-check,
  but nothing in `src/` currently constructs an `IdentityUpdate` with `faction_set` set to a
  non-`None` value — it is a fully wired but unused writer.
- A dormant observability event exists for this exact transition (`entity_faction_changed` — confirm
  its emission call site, or lack thereof, during Investigate).
- **Real risk, not diplomatic flavor**: `identity.faction` is read directly by combat/action legality
  itself. Confirmed 6 call sites in `src/engine/legality.py` (lines 269, 451, 521, 530, 543, 556) —
  ally/enemy determination for targeting, guarding, and threat evaluation all read this field
  directly. A faction change mid-tick or mid-encounter has real combat-legality consequences that
  must be scoped explicitly, not discovered after implementation.
- **No Mechanics Bible chapter exists to document this in.** Per the parent roadmap's own audit, idea
  39 is the single widest cross-ledger idea in the whole 65-idea roadmap (touches 5 of 8 parity
  ledger files) with no chapter home. `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` tracks authoring
  that chapter separately — this ticket should cross-reference it, and at minimum document its own
  formula/trigger conditions somewhere real (even a `docs/world/` contract doc) rather than leaving
  it undocumented pending that chapter's own timeline.

## Scope
- Design and implement the real trigger condition(s) under which `IdentityUpdate.faction_set` is
  populated with a non-`None` value through the authoritative apply-path — reusing the existing
  `apply.py:321` dirty-check wiring, not inventing a parallel path.
- Wire (or confirm already-wired, and fix if not) the `entity_faction_changed` observability event to
  fire on this exact transition.
- Explicitly scope the combat/action-legality interaction from `src/engine/legality.py`'s 6 call
  sites: does a faction change take effect immediately (mid-tick correctness risk) or only at the
  next tick boundary? Document the chosen semantics and add a regression test proving it.
- Document the new mechanism somewhere real and citable (a `docs/world/` contract doc at minimum;
  full Mechanics Bible chapter integration is `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER`'s own
  scope, cross-reference rather than duplicate).
- Add the corresponding parity-ledger entries for whichever of the 5 affected ledger files this
  ticket's actual change touches.

## Out of Scope
- Idea 56 (Drifting Loyalty) — the derived pressure signal that may request this mutation; that is
  `TCK-20260905-DRIFTING-LOYALTY-SIGNAL`'s own scope, sequenced after this ticket.
- Idea 59/65 (Home, Exile & Return; Named Refugee Threads) — `TCK-20260905-HOME-EXILE-REFUGEE-THREADS`.
- Authoring the full Social/Political Mechanics Bible chapter — `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER`.
- Any UI/API surface for affiliation changes — no `src/api/` exposure found for faction/identity
  fields today; adding one is out of scope unless a future ticket asks for it.

## Acceptance Criteria
- [x] A real, event-driven trigger populates `IdentityUpdate.faction_set` through the existing
      authoritative apply-path — confirmed via a test that constructs the trigger condition and
      asserts the entity's `identity.faction` changes only through `apply.py`, never via direct
      mutation.
- [x] `entity_faction_changed` observability event fires exactly once per real faction change,
      confirmed by a test.
- [x] The combat/action-legality interaction (6 `legality.py` call sites) has documented, tested
      semantics for what happens when a faction change occurs relative to a live encounter — not
      left as an unstated edge case.
- [x] The new mechanism is documented in a real, citable doc (contract doc minimum; Bible chapter if
      `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` has landed by the time this ticket implements).
- [x] Parity-ledger entries added for the affected ledger file(s), each with a real `test_path`.
- [x] `src/replay/fingerprint.py` coverage confirmed for the new/changed field(s) — this is exactly
      the failure class PR #128's own architecture review caught (nondeterministic derivation feeding
      a durable, replay-sensitive structure); do not repeat it.

## Related Tickets
- `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY` (parent epic)
- `TCK-20260905-DRIFTING-LOYALTY-SIGNAL` (idea 56, sequenced after this ticket)
- `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` (documentation prerequisite/cross-reference)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`
- `docs/plans/rpg_design_roadmap/rpg_social_narrative_mechanics_hardening_plan.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/core/state.py` (`IdentityComponent`)
- `src/core/updates.py` (`IdentityUpdate.faction_set`)
- `src/engine/apply.py`
- `src/engine/legality.py`
- `src/content_semantics/faction.py`
- `src/replay/fingerprint.py`

## Assumptions / Open Questions
- Whether the trigger condition is player-initiated, event-driven (e.g. betrayal, conquest), or
  derived from idea 56's own loyalty-drift signal (creating a soft ordering dependency the other
  direction) is not decided here — real design work for this ticket's own Investigate/Plan phases.
- Whether `entity_faction_changed`'s dormant wiring is fully correct or itself needs a fix should be
  re-confirmed at implementation time, not assumed from this scoping pass alone.

## Implementation Notes

Implemented plan.md's 7 steps in order:

1. **`src/replay/fingerprint.py`** — added `role={ent.identity.role}:` and
   `faction={ent.identity.faction}:` to `StateFingerprinter.get_fingerprint()`'s per-entity
   f-string, immediately after `f"{ent.kind}:"`. `CanonicalStateHasher` was left untouched (it
   already covered `faction`).
2. **`src/systems/social_systems/party_lifecycle.py`** — `check_defection()`'s returned
   `EntityUpdate` now also carries `identity=IdentityUpdate(faction_set=Faction.NEUTRAL)`,
   constructed via a local import (`from src.core.enums import Faction`,
   `IdentityUpdate` added to the existing local `EntityUpdate, SocialUpdate` import), matching
   the function's existing local-import pattern. Updated the module's own docstring to describe
   the new defection-sets-NEUTRAL behavior. `GroupRecord` was not touched — no `faction` field
   was added, per the plan's NEUTRAL-sentinel scope guard.
3. Added `test_entity_faction_changed_fires_once_on_real_defection_trigger` to
   `tests/unit/observability/test_event_extractor_identity.py`, running the real
   `check_defection()` -> `StateUpdate` -> `ApplyPath.apply_partial()` -> `EventExtractor.extract()`
   sequence end-to-end against a `sandbox_world` fixture entity. `event_extractor.py` itself was
   not touched (confirmed already correct).
4. Added `tests/unit/engine/test_legality_faction_mutation.py` with
   `test_faction_change_mid_tick_legality_semantics`: builds a 2-entity `AuthoritativeState`
   (HERO_GUILD attacker, MONSTER_HORDE target), confirms `LegalityServiceV2.verify_attack_legality`
   is legal pre-defection, runs `check_defection()`, confirms the *same frozen `state`* object
   still evaluates legal afterward (proving same-tick immutability), then applies the update via
   `ApplyPath.apply_partial` and confirms the post-apply state evaluates
   `FRIENDLY_FIRE_ILLEGAL` (HERO_GUILD vs NEUTRAL has no hostile-compat relationship in
   `data/content/social/`). No `src/engine/legality.py` or `pipeline.py` change was made.
5. Added `tests/architecture/test_faction_mutation_write_paths.py` with 4 tests. See Deviations
   below — Step 5's originally-specified bare `\bfaction\s*=` scan was found, during
   implementation, to produce 19 false positives (equality comparisons matched via `==`, local
   variables named `faction`, an f-string label, and dozens of legitimate
   `V2EntityBuilder(...).identity(faction=...)` construction-time calls across
   world-generation/assembly files) and was replaced with a regex targeting the actual named
   bypass shape, `replace\([^)]*?faction\s*=(?!=)`, allowlisting only `src/engine/patches.py`.
   The `faction_set\s*=` guard matched the plan exactly with zero false positives.
6. Added `docs/world/affiliation_mutation.md` (layer `world`, tag `faction`) documenting the
   write-path contract, the defection trigger, observability, the next-tick-boundary legality
   semantics, and fingerprint coverage, cross-referencing
   `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` rather than duplicating it.
7. Added parity-ledger entries via `tools/parity_ledger_writer.py::write_entry` (never a raw
   YAML edit): `SOC-273` (`docs/parity_ledger/social_narrative.yaml`), `COMB-323`
   (`docs/parity_ledger/combat_movement.yaml`), and amended `SUB-378`'s `v2_evidence` and
   `support_boundary` in `docs/parity_ledger/substrate.yaml` (the latter because its existing
   text asserted `entity_faction_changed` "cannot fire in ANY current code path," which this
   ticket's change directly contradicts — see Deviations in plan.md).

Ran `graphify update .` after all `src/`/`tests/` changes, per project convention.

## Test Summary

New/updated tests, all passing (`/home/u24desktop/Working/venv/bin/python3 -m pytest`):
- `tests/unit/replay/test_fingerprint_identity_coverage.py` (new) — 2 tests
- `tests/unit/social/test_party_lifecycle.py` — 1 new test
  (`test_defection_produces_faction_set_neutral_via_apply_path`)
- `tests/unit/observability/test_event_extractor_identity.py` — 1 new test
  (`test_entity_faction_changed_fires_once_on_real_defection_trigger`)
- `tests/unit/engine/test_legality_faction_mutation.py` (new) — 1 test
- `tests/architecture/test_faction_mutation_write_paths.py` (new) — 4 tests

Regression sweep run and green: `tests/unit/social/`, `tests/unit/engine/`,
`tests/unit/observability/`, `tests/unit/replay/`, `tests/unit/progression/`,
`tests/unit/combat/`, `tests/architecture/` (all `-m "not slow"`), plus
`tests/tools/ -k parity` including `test_parity_index_baseline.py` (no baseline drift). Full
combined new-test run: 44 passed. Full regression sweep across the above directories: 1274+454+98
passed, 0 failed.

## Files Changed

- `src/replay/fingerprint.py` — fingerprint role/faction coverage (Step 1)
- `src/systems/social_systems/party_lifecycle.py` — defection sets `faction_set=NEUTRAL` (Step 2)
- `tests/unit/replay/__init__.py` (new)
- `tests/unit/replay/test_fingerprint_identity_coverage.py` (new, Step 1 verify)
- `tests/unit/social/test_party_lifecycle.py` — new test (Step 2 verify)
- `tests/unit/observability/test_event_extractor_identity.py` — new test (Step 3)
- `tests/unit/engine/test_legality_faction_mutation.py` (new, Step 4)
- `tests/architecture/test_faction_mutation_write_paths.py` (new, Step 5)
- `docs/world/affiliation_mutation.md` (new, Step 6)
- `docs/parity_ledger/social_narrative.yaml` — new entry SOC-273 (Step 7)
- `docs/parity_ledger/combat_movement.yaml` — new entry COMB-323 (Step 7)
- `docs/parity_ledger/substrate.yaml` — amended SUB-378 (Step 7)
- `staging_artifacts/TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE/plan.md` — added Deviations
  section
- `staging_artifacts/TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE/investigation.md` — pre-existing
  from this ticket's Investigate phase, not authored by this implementer run, but part of this
  ticket's changeset (previously untracked in git)
- `staging_artifacts/TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE/test_plan.md` — pre-existing
  from this ticket's Plan phase, not authored by this implementer run, but part of this ticket's
  changeset (previously untracked in git)
- `tickets/inprogress/TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE.md` — this file
- `graphify-out/` — refreshed via `graphify update .`
- `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md` — Document-Update phase:
  landed status for idea 39, corrected stale "5 of 8 ledger files" framing
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — Document-Update phase: M6 status line
  synced, corrected ledger count to the current 9-file canonical set
- `docs/event_ledger/entity.yaml` — Document-Update phase: ENTITY-007's evidence/notes updated to
  record `faction_set`'s new real producer
- `docs/simulation_quality/event_type_coverage.md` — Document-Update phase: §5 `entity_faction_changed`
  row updated to record the new live producer

## Completion Summary

Idea 39's real, live faction-mutation trigger now exists: `PartyLifecycleService.check_defection()`
sets a defecting entity's `identity.faction` to `Faction.NEUTRAL` through the pre-existing but
previously-idle `IdentityUpdate.faction_set` -> `IdentityPatch.apply()` authoritative apply-path.
`entity_faction_changed` observability (pre-existing, unchanged) confirmed firing end-to-end from
this real trigger. The mid-tick-vs-next-tick-boundary combat-legality question is resolved as a
structural consequence of `AuthoritativeApplyPipeline.refine()`'s existing phase order
(`"action_routing"` before `"groups"`), proven by a new regression test, with no
`src/engine/legality.py` change required. `src/replay/fingerprint.py`'s previously-missing
role/faction coverage is fixed. A new architecture guard
(`tests/architecture/test_faction_mutation_write_paths.py`) restricts `faction_set=` writes and
the realistic `dataclasses.replace(entity.identity, faction=...)` bypass shape to the
authoritative writer only — its originally-planned bare-word regex had to be narrowed during
implementation after it produced 19 false positives against construction-time builder calls
across the codebase (documented in plan.md's Deviations section). The mechanism is documented in
`docs/world/affiliation_mutation.md` and reflected in 3 parity-ledger entries
(`SOC-273`, `COMB-323`, amended `SUB-378`), all written via `tools/parity_ledger_writer.py`.
