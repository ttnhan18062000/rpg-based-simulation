---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING
artifact_type: investigation
tags: [feature-flags, determinism]
---

# Investigation — TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING

## The ticket's own RNG-consumption-order hypothesis is REJECTED — real root cause found

Traced with a real, controlled, monkey-patched `frontier_marches` seed-42 Kernel run (one tick,
`ENABLE_ADVENTURE_ROUTING` toggled, everything else identical):

1. **Pre-tick `state.factions` is byte-identical** between ON/OFF (confirmed directly — same
   `_load_world_state()` call, flags are applied via a post-hoc `dataclasses.replace(state,
   feature_flags=...)` that never touches compile-time content).
2. **`compute_transitions(state.factions)`** (`src/domains/faction/diplomatic_state_machine.py:25`)
   is a pure function of its `factions` argument — traced directly, contains zero RNG calls of any
   kind (`grep` confirmed). Monkey-patched and called exactly once per tick in BOTH configurations,
   with the same 16-faction input, returning the **same 58 `FactionUpdate` objects** either way —
   proven by object-level comparison, not just count.
3. **But `AuthoritativeApplyPipeline.refine()`'s own returned `StateUpdate`** has those 58
   `faction_updates` intact when routing is OFF, and **zero** when routing is ON — confirmed by
   monkey-patching `refine()` itself and inspecting its return value directly, before any
   Kernel-level apply step.

This means the divergence happens **inside `refine()`, after `diplomatic_transitions` merges its
updates, before `refine()` returns** — not an RNG issue at all.

**Root cause found** (`src/engine/pipeline.py`, the `adventure_decision` phase's own `run_phase`
call): every other phase in this file wraps its own `StateUpdate` in `u.merge(...)` before
returning it, e.g. `lambda u: u.merge(InformationBeliefPhase.apply(...))`,
`lambda u: u.merge(CooperationPhase.execute(...))`, `lambda u: u.merge(_SU_dt(...))` for
diplomatic_transitions itself. The `adventure_decision` phase's own lambda was the **one
exception**:

```python
lambda u: AdventureDecisionPhase.apply(
    state, faction_directives=faction_directives, factions=state.factions,
),
```

`AdventureDecisionPhase.apply()` (`src/domains/adventure/phase.py:53`) is correctly self-contained
— it starts with `update = StateUpdate()` (a fresh, empty update) and returns only its own
hero-routing `entity_updates`, by design (it has no `u` parameter at all — it was never meant to
see the accumulated update). The bug is entirely in the **call site**: the lambda's `u` parameter
is captured but never used, so `AdventureDecisionPhase.apply()`'s fresh, near-empty `StateUpdate`
is returned directly from the lambda. Inside `run_phase`, `phase_upd = phase_fn(upd)` then
`return phase_upd` (the ON/non-SHADOW branch) — **replacing** the entire accumulated `update`
(everything merged by every phase that ran earlier in the same tick: `information_belief`,
`cooperation`, `contracts`/`blacksmith`, `faction_decision`, `faction_awareness`,
`diplomatic_transitions`) with just the adventure-routing phase's own sliver.

This explains the symptom exactly: **any** tick with `ENABLE_ADVENTURE_ROUTING=ON` silently
discards every pipeline phase's output that ran *before* `adventure_decision` in that same tick
(not just tick 1 — every tick), replacing it with only the routing phase's own entity updates.
`diplomatic_transition`/`belief_assimilated` happened to be the ticket's own visible symptom
because they're the phases immediately preceding `adventure_decision` with real tick-1 content;
`contracts`/`blacksmith` (ECONOMY) are silently affected the same way, corpus-wide, wherever
routing is ON.

## Fix

One-line fix, matching the established pattern of every other phase in the same file:

```python
lambda u: u.merge(AdventureDecisionPhase.apply(
    state, faction_directives=faction_directives, factions=state.factions,
)),
```

**Verified via the same controlled probe**: post-fix, `refine()`'s returned `faction_updates`
count is 58 in both ON and OFF configurations (identical objects), and the final applied
`state.factions[*].diplomatic_relations` is non-empty for all 16 factions in both. Also verified
routing itself still functions correctly post-fix (3 heroes still receive real strategic projects
— `proj.gather_resource`/`proj.form_party` — across a real 5-tick run), confirming the fix doesn't
regress `AdventureDecisionPhase`'s own behavior, only stops it from clobbering everything before
it.

## Does this affect `simq_routing_test`/`hero_guild_routing`'s own existing anchors?

**Yes, the same code path affects them too** (this is a pipeline-level bug, not
`frontier_marches`-specific) — **but its practical impact on their own already-committed anchors
is narrower than it could be**, checked directly rather than assumed:

- **SOCIAL**: unaffected. Neither world's profile sets `ENABLE_SOCIAL_COOPERATION: "ON"`
  (confirmed via direct read of both profile YAMLs) — the `cooperation` phase never runs for
  either world regardless of this bug, so its own `SOCIAL: C/0.0` anchors are correct as-is, not a
  masked casualty.
- **FACTION/INFORMATION**: unaffected. Per `corpus_tier_taxonomy.md`'s own "FACTION/INFORMATION
  Coverage Closure" sections, both worlds are already documented as FACTION/INFORMATION-inert **by
  deliberate tier-purity design** (no `faction_tension_overrides`/`information_source_profiles`
  content authored at all) — there is no real signal for this bug to have suppressed in the first
  place.
- **ECONOMY**: **likely genuinely under-scored** by this bug. Both worlds compose
  `frontier_village_core` (has a blacksmith), and the unconditional `contracts`/`blacksmith`
  phases (`src/engine/pipeline.py` lines 171-175, no feature-flag gate, always attempted) run
  *before* `adventure_decision` — meaning their output was silently discarded every tick this bug
  was live. Real, observed signal supporting this: both worlds' `_seed42_500t` anchors show
  `ECONOMY: C/0.0`, but their own `_seed42_1000t` anchors show `ECONOMY: B/0.213` (non-zero) —
  consistent with a *separate*, later-in-pipeline `economy` phase (visible as its own cost bucket
  in real watchdog telemetry this session's own tools already produced) generating some real
  signal over a longer run, while the earlier `contracts`/`blacksmith` phase's own contribution
  was masked by this bug the whole time.

## Docs Requiring Update
- `docs/guidelines/intentional_divergences.md`: new entry — this is a real, corpus-wide behavior
  change (a full tick's worth of pre-adventure-decision phase output starts surviving to apply,
  where previously it was silently discarded whenever `ENABLE_ADVENTURE_ROUTING=ON`)
- `docs/parity_ledger/strategic_cognition.yaml` and/or `combat_movement.yaml` (whichever
  `expected_subsystems_for_files()` maps `src/engine/pipeline.py` to): new entry documenting the
  fix, per this repo's Parity phase convention for `src/` behavior changes
