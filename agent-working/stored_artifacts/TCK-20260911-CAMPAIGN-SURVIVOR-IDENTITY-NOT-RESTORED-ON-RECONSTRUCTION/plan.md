# Plan — TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION

## Steps

1. **`EntityCarryForward`** (`src/domains/campaigns/state.py`): add `kind: str`, `role: int`,
   `faction: int`, `properties: dict`, `traits: list` (serialized as a sorted list for determinism,
   reconstructed as a `set`), `personality: dict` (`{greed, bravery, sociability, industry}`).
   `kind`/`role`/`faction` are required-with-sane-defaults (a spawned entity always has them);
   `properties`/`traits`/`personality` default to empty/zero to match `IdentityComponent`'s own
   defaults for round-trip safety on old records.

2. **Capture at extraction** (`_extract_entity_carry_forwards()`): read `entity.kind`,
   `entity.identity.role`, `entity.identity.faction`, `entity.identity.properties`,
   `entity.identity.traits`, `entity.identity.personality` unconditionally (not gated by a
   `carry_forward_rules` flag — same reasoning as `last_position`: these aren't opt-in carry-
   forward preferences, they're required for the entity to be who it actually is next episode).

3. **Personality: carry forward, not re-derive.** `PersonalityComponent`'s own docstring says
   "Persistent psychological traits" — the dataclass's own stated intent is that this is
   accumulated, persistent per-entity state, not a fresh per-episode roll. Carrying it (matching
   level/xp's own treatment) is the more defensible reading; re-deriving fresh via
   `build_personality_for_entity()` at reconstruction would silently give every survivor a *new*
   personality each episode, contradicting "persistent." Recorded as a real decision with
   reasoning, not left ambiguous.

4. **Wire into `_build_initial_state()`'s survivor branch**: set `kind` on the `EntityState`
   construction itself (replacing the `kind="entity"` literal), and extend the existing
   `identity = dc_replace(base.identity, evolution_level=..., evolution_points=...)` call to also
   set `role=cf.role, faction=cf.faction, properties=cf.properties, traits=set(cf.traits),
   personality=PersonalityComponent(**cf.personality)`.

5. **Watch the branch's own complexity** (per this ticket's own Scope) — if the per-entity loop in
   `_build_initial_state()` starts accumulating enough field-by-field special cases across three
   tickets now (position, identity, and whatever's next) to be hard to follow inline, extract
   reconstruction into its own module (`survivor_reconstruction.py`?) matching
   `survivor_placement.py`'s own precedent. Real call once the diff is visible, not pre-decided.

6. **Fix the misleading comment already partially corrected by the predecessor ticket** — confirm
   it still accurately describes the branch after this change (it should, since the predecessor
   already rewrote it to describe the real mechanism rather than the false
   `world_composition`-governs-placement claim).

7. **Real identity-equivalence test**: construct a freshly-spawned entity and a reconstructed
   survivor from that same entity's own carry-forward snapshot, assert all six fields match
   (`kind`, `role`, `faction`, `properties`, `traits`, `personality`) — not a field-by-field
   spot-check, the actual equivalence claim this ticket's own governing invariant makes.

8. **Stall investigation, separate from the fix itself**: real event-stream instrumentation
   (`_CollectingRecorder` pattern) comparing episode 1 (completes) against episode 2 (stalls) both
   before and after the identity fix, recording whichever of the three predicted outcomes (fixed /
   still stalls / changes shape) actually occurs — not asserted in advance.

## Test Plan Summary
See `test_plan.md`. Headline: unit tests for extraction/reconstruction identity-equivalence, plus
the real 3-episode acceptance run (reused from the predecessor ticket's own test file, extended to
assert full completion now that identity is fixed — or to record and report whatever the real
outcome turns out to be, per Scope's three-outcomes framing).

## Scope Guards
- `class_id`, `life_stage`, `learned_skills`, `known_recipes`, `veterancy_*`, `unspent_ap`,
  `territory_maturity`, `active_breakthroughs`, `cooldowns`, `group_id`, `latest_intent_results` —
  confirmed unset even by a real spawn, not touched.
- `AttributeComponent`, `combat.hp`/`.atk`/`.def_stat` — different divergence, different ticket
  (`TCK-20260911-CAMPAIGN-SURVIVOR-COMBAT-STATS-NOT-RECOMPUTED-ON-RECONSTRUCTION`), not folded in.
