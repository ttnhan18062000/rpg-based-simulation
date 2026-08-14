---
status: active
layer: simulation
authority: P0
audience: agent
ticket_id: TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY
artifact_type: investigation
tags: [simulation-quality, combat, progression, feature-flags, observability]
---

# Investigation: TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY

## Summary

**The ticket's own starting premise was wrong, and the investigation found the real mechanism.**
`ENABLE_COMBAT_ENGAGEMENT` being off-by-default is a **deliberate, already-documented decision**
(DEV-002, rationale class "Stabilized"), not an unexamined gap — and the domain it gates
(`src/domains/combat_engagement/`) is a **posture-assessment layer only** ("Pre-Combat
Assessment" — decides `IGNORE`/`ENGAGE`/`AVOID`/etc.), not the damage-resolution mechanic. Flipping
it would not have produced kills or XP even if it were the right fix, and per
`docs/guides/feature_flags.md`, flipping any of the 11 default-OFF flags requires first re-running
`tools/balance_measure.py` to re-baseline `test_balance_regression.py` — a nontrivial, gated
process, not something to do casually inside this ticket.

The real mechanism was traced instead: `src/observability/event_extractor.py` is a **generic,
cause-blind HP-diff observer**. It compares an entity's `combat.hp` between consecutive tick
snapshots; any decrease at all — regardless of source — is emitted as `combat_damage`,
`combat_initiated`, and (if it crosses the 20% threshold) `near_death_survival`. It does **not**
distinguish real entity-vs-entity combat from environmental/hazard damage. `attacker_id` is read
from `update.entity_updates[eid].combat_upd.attacker_id` if present, and was `None` in every single
observed hit across all 3 sampled runs — consistent with the damage source not being a tracked
combat attack at all.

## Findings

### 1. `ENABLE_COMBAT_ENGAGEMENT`'s off-by-default status is a prior, deliberate ruling — not an unexamined gap

Confirmed via `docs/guides/feature_flags.md` and `docs/guidelines/intentional_divergences.md` §
DEV-002: all 11 `FeatureFlagManager` flags (including `ENABLE_COMBAT_ENGAGEMENT` and
`ENABLE_PROGRESSION_EVOLUTION`) default `OFF` by deliberate design (rationale class
**Stabilized**), guarded by a sentinel test `test_adventure_routing_defaults_off()` in
`test_balance_regression.py`. This is the same mechanism (not the same ruling) as
`ENABLE_ADVENTURE_ROUTING`'s AGENCY-pillar precedent, just documented for all 11 flags at once
rather than per-flag. **This ticket's original Scope item 2 ("determine whether this is a
deliberate ruling or an unexamined gap") is answered: it is deliberate. No policy decision is
needed or appropriate here** — the corpus not exercising these flags is working as designed at the
engine-default level.

### 2. `ENABLE_COMBAT_ENGAGEMENT` gates posture assessment, not damage resolution — it was never the right lever

`docs/simulation/domains/combat_engagement_contract.md` (authoritative, `last_verified:
2026-06-12`): "The combat engagement domain produces a subjective pre-combat assessment... It does
not resolve combat outcomes — that is the combat system's responsibility." The domain's
`CombatEngagementDecisionService.evaluate()` is stateless, read-only, and selects one of 10
`CombatPosture` values (`IGNORE`/`WATCH`/`AVOID`/.../`ENGAGE`/`PANIC_FLEE`). It does not write to
`AuthoritativeState`. **Even with the flag ON, this domain would not have produced the kills or XP
this investigation was looking for** — it only affects which posture an entity picks before a fight
it's already going to have. `D19_domain_phase_inventory.md`'s one-line description of PP-16
("applies the damage formula, durability decay, and tactical modifiers") is imprecise relative to
the domain's own authoritative contract doc — worth a light correction, out of scope here (doc-only
tension, not a behavior bug).

### 3. The actual combat/damage events come from a generic HP-diff extractor with no causal attribution

`src/observability/event_extractor.py` lines 136-203 (read directly): for every entity, every tick,
it computes `hp_diff = entity.combat.hp - prior_ent.combat.hp`. If `hp_diff < 0`, it unconditionally
emits `CombatDamageEvent` (`event_type="combat_damage"`) with `damage=int(-hp_diff)`, reading
`attacker_id` from the tick's `CombatUpdate` if one exists. `combat_initiated` and
`near_death_survival` are derived the same way (full-HP → damaged, and HP crossing 20% threshold,
respectively) — purely from HP deltas between snapshots, with **no check on what caused the HP
loss**. This extractor cannot distinguish real entity-vs-entity combat from hazard drain, or any
other mechanism that reduces `combat.hp` directly.

In all 3 sampled runs, every observed damage event had `attacker_id: None` — the update never
carried a populated `CombatUpdate.attacker_id`. `EnvironmentService.calculate_hazard_drain()`
(`src/world/environment.py:16`, formula `hazard_level * (1.0 + calamity_intensity)`) is a strong
candidate source: it reduces HP directly and has no reason to populate a combat attacker field. All
3 runs also independently emitted real `hazard_drain_applied` events (10/0/16 occurrences) in the
same tick ranges. **Not conclusively proven in this investigation** (would require tracing a
specific hit's region hazard_level to confirm the exact 25-damage match), but the mechanism fit is
strong enough to treat as the leading hypothesis, not a coincidence.

**This means the SimQ corpus's COMBAT pillar events may currently include hazard/environmental
damage misclassified as combat** — a distinct data-integrity concern from the original
"combat-engagement-gate" hypothesis, and arguably more consequential, since it means COMBAT's
existing "Healthy, archetype-correct spread" grade history may be partly scoring non-combat HP
loss.

### 4. Zero XP is a clean, directly-confirmed downstream consequence — not a separate bug

`xp_granted` (event_extractor.py:206-214) is likewise generic: any positive delta in
`entity.identity.evolution_points` between ticks. Per
`docs/mechanics/attribute_progression_contract.md`'s XP Gain Sources table, that field only
increases via a combat kill or a quest reward. With zero real kills (`combat_kill` event type —
confirmed absent from all 3 runs' full event-type inventories, not just a search miss; see
`quality_hub.py:21`'s `"combat_kill": "entity_killed"` translation, which was never exercised) and
zero quest rewards observed, zero `xp_granted` is exactly what the mechanics predict — not an
independent anomaly. `PP-28 evolution` (`EvolutionSystem`) is confirmed `active`/ungated in
`D19_domain_phase_inventory.md` and is not implicated.

### 5. Quest-reward gap traced to a plausible pacing explanation, not confirmed as a bug

`QuestRewardPhase.resolve()` (`src/engine/pipeline_phases/quests.py:22-28`, always active, not
flag-gated) explicitly "converts quest completion/retry state into authoritative reward intents" —
it requires the quest to have reached a completion or retry state, not merely "started."
Every sampled `quest_event` message this session read followed the pattern "quest ... updated to
status started" — none were confirmed reaching "completed" in the small sample directly read (2
messages out of 650+ total events; not exhaustively checked before the run data was cleaned per
convention). This is consistent with a **tick-length pacing issue** (quests may need more than 500
ticks to reach completion in these worlds) rather than a broken reward pipeline, but this
investigation did not run long enough (1000-2000t) to confirm quest completions eventually occur.
**Left open, not resolved** — see Recommendation.

## Addendum — Finding 3 escalated from hypothesis to confirmed root cause

Follow-up tracing (same investigation session, continued after initial write-up) found the exact
bug rather than the coincidental-hazard-level hypothesis originally proposed:

- `event_extractor.py` lines 136-151 (combat-damage detection) check `hp_diff < 0` and
  unconditionally construct `CombatDamageEvent` — **no check on `CombatUpdate.outcome_kind`**.
- The same file, lines 394-396, has a *separate* branch that correctly checks
  `combat_upd.outcome_kind == "HAZARD"` before emitting `hazard_drain_applied`.
- `src/engine/world_dynamics.py:39` confirms hazard drain already tags itself honestly:
  `outcome_kind="HAZARD"` on the same `CombatUpdate` record the combat-damage branch reads
  `attacker_id` from (but not `outcome_kind`).
- `src/engine/combat.py` confirms real combat outcomes are tagged too:
  `outcome_kind` ∈ `{SURVIVE, DEFEAT, KILL, REJECTED}` at every real resolution site.

**The causal data was never missing — the extractor just never read it in the branch that needed
it.** This is a precise, small, confirmed bug, not an architectural gap. Filed as its own hotfix
ticket: `TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX`.

## Addendum — the diffing pattern generalizes to the entire observability pipeline

`src/engine/kernel.py:909` confirms `EventExtractor.extract()` is called once per tick and is the
**sole source of nearly every event type in the corpus** — not just combat. Direct grep of
`gold_sink.py`, `quests.py`, `faction_decision.py` found zero direct event-push calls in any of
them; `quest_event`, `diplomatic_transition`, `gold_sink_fired`, etc. are all reconstructed by the
same post-tick diff pass. A real, thread-safe, non-blocking delivery queue already exists
(`BoundedObservabilityQueue`) but sits downstream of event creation — nothing feeds it directly
from a mutation call site today. This is a materially bigger question than this ticket's original
scope and is filed separately: `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE`.

## Recommendation

Do not flip `ENABLE_COMBAT_ENGAGEMENT`. It is a deliberate default (DEV-002) and would not fix the
observed symptom even if flipped (Finding 2). Two precisely-scoped follow-up investigations are
warranted instead, filed as separate tickets so each can be gated/tested independently rather than
bundled into this ticket's now-corrected scope:

1. Whether `event_extractor.py`'s cause-blind HP-diff combat detection is misclassifying
   hazard/environmental damage as combat — a real SimQ data-integrity question independent of any
   feature flag.
2. Whether quest completion (and therefore `quest_reward_dispensed`/XP-via-quest) simply needs a
   longer tick window than 500t to occur in these worlds, via a targeted 1000-2000t probe run.

`D20_simq_quality_status_review.md`'s COMBAT "Healthy, archetype-correct spread" verdict should be
corrected to note this open question rather than left as an unqualified "Healthy" — the underlying
event data may include misclassified non-combat damage, which this investigation cannot rule out
with the current sample.

`TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE` remains blocked, now on the two follow-up
tickets rather than on this one's originally-assumed flag question.
