---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION
artifact_type: investigation
tags: [progression, simulation-quality]
---

# Investigation — TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION

## Real, decisive finding: no producer exists anywhere in `src/`

Traced the real field names first (`src/core/updates.py:229,233-234`): `IdentityUpdate.traits_add`,
`traits_remove`, `breakthroughs_add` — these are what `trait_expressed`/`pillar_trait_unlocked`'s
own real emitters (`src/observability/event_extractor.py:1103-1121`) diff against
`entity.identity.traits`/`active_breakthroughs`.

**`grep -rn "traits_add=\|breakthroughs_add=" src/ --include=*.py` (excluding the field
declarations themselves) returns zero matches.** No real production code anywhere in `src/`
constructs an `IdentityUpdate` with either field set. The **only** real construction sites are in
test files:

- `tests/unit/progression/test_breakthroughs.py:15,32` — hand-constructs
  `IdentityUpdate(breakthroughs_add=["iron_will"])` directly, asserts the apply path correctly
  adds it to `entity.identity.active_breakthroughs`.
- `tests/unit/observability/test_event_shapers_progression.py:128,136` — hand-constructs
  `traits_add=["brave"]`/`breakthroughs_add=["combat_mastery"]` to test the event-shaper's own
  diff-detection logic in isolation.
- `tests/unit/core/test_domain_6_hardening.py:103` — hand-constructs
  `IdentityUpdate(traits_add=["Tough"])`, confirms the apply path correctly applies the "Tough"
  trait's own stat bonus (`max_hp` 100→142).

**The apply-path (consumer) is real, correct, and tested** — `src/engine/patches.py:187,224` and
`src/engine/apply.py:514`/`src/core/state.py:826` all correctly read and materialize
`traits_add`/`breakthroughs_add` into durable `IdentityComponent` state, and the "Tough" trait's
own real stat-bonus effect (`combat.max_hp` increase) is confirmed to work correctly when the
field is populated.

**Conclusion: this is the exact same class of finding as `IDENTITY`'s own confirmed hard ceiling**
(`docs/audits/D21_entity_lifecycle_foundation_layers.md`) — a real, working, tested mechanism with
**no real gameplay system that ever drives it**. Not a dormant/rare event (like `level_up`), not a
gated-behind-another-dormant-thing event (like `skill_unlocked`'s relationship to `level_up`) —
genuinely **unimplemented**: no trait-acquisition mechanic, no breakthrough-triggering system, no
personality/self-model hook, no training system, nothing in real `src/` ever decides "this entity
should gain trait X" or "this entity should unlock breakthrough Y" during actual gameplay.

## Why this differs from `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`'s own finding

That sibling ticket found a real mechanism (`EvolutionSystem`) that WOULD produce
`skill_unlocked`/`progression_conversion_applied` if only its own gate (`levels_gained > 0`) ever
opened. Fixing the gate (raising real kill rate / XP curve) would make that mechanism start
firing. **No equivalent gate exists here to fix** — there is no `EvolutionSystem`-style
"trait-granting" system sitting dormant behind a threshold. The real gap is a missing mechanic
entirely, not a blocked one.

## Docs Requiring Update
- `docs/audits/D21_entity_lifecycle_foundation_layers.md`: this investigation's own confirmed
  finding (a second real, confirmed-absent producer, alongside `IDENTITY`) is worth recording
  there for future reference, matching that doc's own existing "hard ceiling" framing for
  `IDENTITY`.
