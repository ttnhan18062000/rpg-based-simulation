---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE
artifact_type: investigation
tags: [simulation-quality, progression]
---

# investigation.md — TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE

## Current Behavior

`docs/simulation_quality/quality_scoring_contract.md` §7.6 (this ticket's own rationale source)
correctly identifies the gap: PROGRESSION scores isolated per-event deltas (`xp_granted`,
`level_up`, `skill_unlocked`, etc.) but has no signal for whether an entity's overall build is
trending upward, and no life-arc coherence check. This investigation confirms what state is
queryable and designs the concrete fix.

## What's queryable at scoring time — corrected from the ticket's own premise

**`ScoringContext` (§4.2 of the contract) has NO entity-state access at all** — it exposes only
`run_id`, `current_tick`, `entity_count`, `pillar_scores`, `pillar_event_counts`,
`window_tag_counts`. No `AttributeComponent`, no equipped-item state, no gold. This corrects the
ticket's own Scope premise (option "(b): reading equipped-slot state directly from
`ScoringContext`'s entity snapshot" is not actually possible — `ScoringContext` carries no entity
snapshot of any kind). Confirmed via `src/simulation_quality/score_record.py`.

Confirmed no "item equipped/changed" observability event exists anywhere (`grep -n "equip"
src/observability/event_extractor.py` — zero hits), even though a typed `EquipmentUpdate` record
does exist on `EntityUpdate.equipment` (`src/core/updates.py:40,631`) — matches the ticket's own
prior finding, re-verified directly.

**Where the real capability state IS available**: `event_extractor.py`'s own `extract()` method
receives both `prior_state` and `current_state` as full snapshots (it is diff-based by design),
giving direct access to `entity.identity.evolution_level`, `entity.identity.learned_skills`,
`entity.equipment.slots` (`Dict[EquipSlot, str | None]`, `src/core/state.py:648`),
`entity.inventory.gold`, and `entity.lifecycle.generation`/`age_ticks`
(`src/core/state.py:142-151`, hero-rebirth/permadeath fields) — no reconstruction needed, unlike
the push-shaper architecture (`ProgressionShaper` in `event_shapers.py`), which only receives
`prior_state` + `update` (delta) and must reconstruct "current" state field-by-field.

## Architecture decision: implement in `event_extractor.py`, unconditionally (not flag-gated,
## not in `ProgressionShaper`)

This session's prior work (`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`, DONE)
migrated PROGRESSION's existing events to live delivery via `ProgressionShaper`
(`event_shapers.py`), with `event_extractor.py`'s legacy branches flag-gated behind
`_push_shapers_phase2_active` (default `ON`) as the rollback path. This raises a real design
question for a **brand-new** signal like this one: should it live in the (now-default-off)
extractor, or the (default-on) shaper?

**Decision: `event_extractor.py`, as new, unconditional (non-flag-gated) code.** Reasoning:
1. This is a *new* signal, not a migration of pre-existing behavior — there is no "old path" it
   needs to stay consistent with, so it does not need a shaper/extractor rollback pair the way
   every Phase 1/2 *migrated* event did.
2. `_push_shapers_phase2_active` exists solely to prevent *double-firing* between two
   constructions of the *same* event. Since `ProgressionShaper` never constructs
   `capability_growth_stalled`/`life_arc_incoherent`, there is no double-fire risk — the new code
   can run unconditionally regardless of the flag's value.
3. `event_extractor.py` has direct, un-reconstructed access to both full entity snapshots
   (`entity`, `prior_ent`), making all 4 capability dimensions (level, gear, gold, skills)
   directly and reliably readable — avoiding the same class of reconstruction-correctness risk
   this epic repeatedly found in the shaper architecture (any-update-vs-specific-update gating
   bugs, same-tick dual-signal double-counts). This is the "minimal viable, lower-risk" approach
   the ticket's own Scope asked for, just realized via extractor placement rather than the
   originally-imagined `ScoringContext` mechanism (which doesn't exist).

## One combined rule or two? — Decision: two, matching §7.6's own framing

§7.6 names two genuinely distinct questions: "capability trend" (is the entity's build trending
upward across its *ongoing* lifetime) and "life-arc coherence" (does the *full* arc, especially
around a Hero's Journey rebirth milestone, look healthy). These have different trigger shapes —
one is an elapsed-time-since-last-growth check (like `progression_frozen`'s own pattern), the
other is a lifecycle-milestone check (generation-based, independent of tick count) — so two
distinct event types avoids conflating two different failure modes into one payload-disambiguated
event (the alternative, overloading `progression_plateau_detected` further, was rejected: it
already carries 3 sub-types via `payload["type"]`, and these two new checks are conceptually
distinct enough from XP/skill silence to warrant their own names, matching §7.3's "no duplicate
signals" spirit by being unambiguously distinguishable in `simulation_events.jsonl` without
needing to inspect payload).

## Rule design

**`capability_growth_stalled`** (negative only — the degenerate case; positive growth is already
covered by the pillar's existing per-event positive deltas, so no separate positive event is
added): entity goes `_CAPABILITY_STALL_TICKS` (300, matching `all_level_1`'s existing dormancy
magnitude) ticks with zero movement across **all four** dimensions simultaneously (level, skill
count, equipped-gear count, gold) — a genuinely broader, harder-to-trip check than any single
existing rule (`progression_frozen` is XP-only; this requires *every* growth axis to be flat).
Tracked via a per-entity `_last_capability_growth_tick` dict (mirrors `_last_xp_tick`'s existing
pattern exactly), fires once per entity (`_emitted_capability_stalled` set, mirrors
`_emitted_plateau`). Deliberately initializes an entity's tracked tick to its *first-observed*
tick (not 0) — `_last_xp_tick`'s own established pattern has a latent gap here (an entity
first observed well into a run, e.g. via late spawn or Hero rebirth, could compute
`tick - 0` and immediately appear stalled) — this ticket's own new code avoids introducing that
gap rather than copying it, since it's cheap to avoid; not filed as a separate finding against
the pre-existing pattern (low practical impact, out of this ticket's own scope to fix elsewhere).

**`life_arc_incoherent`**: entity reaches `lifecycle.generation >= _LATE_GENERATION_THRESHOLD` (2 —
at least one Hero's Journey rebirth has already occurred, per `docs/mechanics/02_combat_laws.md`
Victory Outcomes) while still at `evolution_level <= 1` with zero unlocked skills — a full prior
life-arc (spawn through death/rebirth) that produced no meaningful growth at all. Fires once per
entity (`_emitted_life_arc_incoherent` set).

## Docs Requiring Update

- `docs/simulation_quality/quality_scoring_contract.md`: §5 PROGRESSION table (2 new rows, 2 new
  event types in the "Event types scored" list).
- `docs/simulation_quality/event_type_coverage.md`: §1.1 Direct Emission table (2 new rows).
- `docs/parity_ledger/progression.yaml`: new entry documenting this addition.

## Parity Ledger Overlap

`PROG-117` (`docs/parity_ledger/progression.yaml`) covers the *existing* PROGRESSION events'
push-migration — this ticket adds genuinely new events, not touched by that migration; a new,
separate entry is warranted, not an update to `PROG-117`.

## Prior Work

- `TCK-20260806-SIMQ-LIFECYCLE-PILLAR-BOUNDARY-DOC` (rationale source, DONE)
- `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC` / `-PHASE2-EPIC` (DONE — established the
  `_push_shapers_phase2_active` flag and shaper architecture this investigation reasoned against
  using for this new signal)

## Risks and Open Questions

None left open — both design questions the ticket's own Scope flagged (new event type vs.
snapshot read; one rule vs. two) are resolved above with reasoning.

## Anti-Drift Hazards

- Any future PROGRESSION signal needing full entity-snapshot access (not just typed update
  deltas) should default to `event_extractor.py` placement, following this ticket's own reasoning
  — not assume it must go through the push-shaper architecture just because that's now the
  default-live path for *migrated* events. A brand-new signal has no migration obligation.
- `capability_growth_stalled`'s 4-dimension "any growth" check and
  `TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE`'s Finding 1 (the real quest system is
  unreachable from live gameplay) are unrelated — quest rewards are not one of the 4 tracked
  dimensions here (level/skills/gear/gold), so that finding does not affect this rule's behavior
  either way.
