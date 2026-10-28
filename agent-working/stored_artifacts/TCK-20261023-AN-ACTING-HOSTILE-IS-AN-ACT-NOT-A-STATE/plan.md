---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE
tags: []
---

# plan - TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE (step B)

For designer confirmation before code: sections 1, 2 and 3. No code until they are confirmed.

## 1. (a) The work kinds that count as "attack or pursuit targeting S" (main 341f700d0)
A hostile H counts when S perceives H (`perceived_hostiles`, scorers_support.py:18) and its current `task` plus `navigation.movement_mode` match:
| Counts | Emitted at | Typed key |
|---|---|---|
| `ENTITY_ACT`, action `ATTACK`, `target_id == S.id` (basic attack) | tactical.py:742-746 | payload action |
| the same, reason `HOLD_BETWEEN_BLOWS` (queued swing, target adjacent) | tactical_hold.py:40-50 | payload action |
| `ENTITY_ACT`, action `SKILL`, `target_id == S.id` | tactical.py:724-728 | payload action |
| `ENTITY_MOVE`, `movement_mode == PURSUE`, `target_id == S.id` (plain pursuit) | tactical.py:776-781 | movement mode |
| the same, reason `PURSUIT_BLOCKED_KITE` | tactical.py:658-661 | movement mode |
| `ENTITY_MOVE`, `movement_mode == INTERCEPT`, `target_id == S.id` | tactical.py:605-608 | movement mode |
**Decision needed:** `BRACKETING` (tactical.py:553, positions beside the target to attack with an ally; `target_id = target`). It is an attack approach. Default: include. Say if not.
**Do not count** (they carry `target_id` but are not an attack or pursuit of S): `HOLD` (WATCH_HOSTILE tactical_hold.py:108, AVOID_NO_ROUTE :117, HOLD_CHOKEPOINT tactical.py:623), `KITING` (tactical.py:670, RETREAT mode), `SEEK_COVER` (:520), `GUARDING_ALLY` (:595), `CONTRACT_OBLIGATION_GUARD` (:363), `INTERACT`, and any task with a bare `target_id` and none of the above.
Key on typed `movement_mode` and `payload["action"]`, not on a `reason` string.
**Verify at build, flagged as a risk:** `executor.py:162-169` re-sets the task payload after executing an `ENTITY_ACT`, so a hostile's last ATTACK task stays "current" until its next decision. A hostile that attacked S, lost reach, and has not decided again reads as acting until it does. The ruling says "current task", so this is as designed; the paired measurement and the guard-11 probe show whether it matters.

## 2. (b) The hit window and the typed field
- New field `CombatComponent.last_hit_tick: Optional[int] = None`, beside `last_attacker_id` (state.py:446), same writer: `CombatPatch.apply` (patches.py:329), set to the applying tick when `u_com.attacker_id is not None and u_com.damage_taken > 0`. Opportunity hits go through the same CombatUpdate (`movement.py:311-325`), so they are covered.
- `last_hit_tick` records the tick of the hit but not the attacker. The rule is "H took hp from S" so the predicate also needs `S.combat.last_attacker_id == H.id`. Both fields come from the SAME hit (the patch writes them together), so the pair names the last hit and its attacker. A hit by a different body later overwrites both, so H's earlier hit is forgotten: H "hit S" only counts while H is still the last attacker.
- **Window anchor.** S stores no previous-decision tick: the brain cadence is stateless (`should_run(tick, id, cadence)`, cadence.py:39-60, `(tick + id) % cadence == 0`; `NEED_WAKE_CADENCE` = the strategic cadence, 10, scheduler.py:19; `ADJACENCY_WAKE_COOLDOWN` = 2, scheduler.py:14). **Proposal:** a hit counts if `state.tick - last_hit_tick <= NEED_WAKE_CADENCE`: the existing named constant for the brain's own decision cadence, so "since S's previous decision" is bounded by it. No new constant.
  - Caveat: S can decide more often than every 10 ticks (adjacency wakes every 2, need wakes every 10), so some hits that precede S's previous decision still count. This errs toward "acting" (safe side). The exact alternative is a stored `last_decision_tick`, which is a new durable field per entity, written every decision, and heavier. Not proposed.
  - Designer: confirm `NEED_WAKE_CADENCE`.

## 3. Hash coverage (lead's question) - SUPERSEDED 2026-10-24 by perf ruling PERF-D5 (ii)
Built as: `last_hit_tick` is typed durable state, emitted in the component's canonical dict and pickled in checkpoints, and excluded from the v2 proof digest only (`DIGEST_EXCLUDED_COMBAT_KEYS`, checkpoint.py), until perf's F1. The analysis below is the original reasoning (the digest would have changed for every entity).
Is it hashed today? YES. `CanonicalStateHasher.to_canonical_data` (checkpoint.py:94-113) hashes every entity's `to_canonical_dict()`; `EntityState` includes `"combat": self.combat.to_canonical_dict()` (state.py:1030), and `CombatComponent.to_canonical_dict` includes `"last_attacker_id"` (state.py:458). So the sibling is hashed, and `last_hit_tick` must be too ("canonical" in the ruling). Nothing to note under #593 F1 for this field. [#593 F1 is about the six fields the hasher omits, a separate matter.]
**Consequence for the measurement:** adding a key to the combat canonical dict changes the state hash of EVERY entity at every tick, even where behaviour is identical. So B's paired hashes can never equal the base's. The attribution for B cannot use hash equality; it uses the paired behavioural counters, fingerprints and extinction rows. If the designer wants the hash to stay equal for never-hit entities, the key can be emitted only when not None (the shape `owed` uses, checkpoint.py:58-61), but a hit entity still differs. **Ask the designer/lead which they want.** Default: add the key always (simpler, matches `last_attacker_id`) and use a behavioural comparison. Also state the effect on any stored hashes: `rpg_gate_v1` fingerprints and the determinism hashes pinned in tests will change (the planner to confirm they are not an expectation to keep).

## 4. The predicate and its readers
- `src/ai/goals/present_threat.py`: add `acting_threat_to(entity, state)` (pure read) = any `perceived_hostiles` that satisfies 1 or 2. `present_threat_to` keeps its terms for the callers that keep them.
- `scorers.py:61` `_escalated_unless_threatened` and `:69` `_hunger_escalated_unless_threatened`: swap `present_threat_to` for `acting_threat_to`. (Row 83's "at or past the line" bypass stays as it is.)
- `tactical.py:203-219` panic hold: with an escalated need on the subject (`need_is_pressing(hunger, sleep_debt)`, need_pull.py:58, the existing escalation-onset test) and no acting hostile in `threats`, skip the PANIC_RETREAT branch (both the move and the freeze) and fall through the existing order. Without a pressing need, unchanged. Reuse of `need_is_pressing`; no new constant. [Designer: "escalated need" = pressing need at the onset, 0.6 of the line, as in the rest of SURV-07; confirm vs "past the starving line".]
- Unchanged: `tactical_rest.py:66,94,111`, `tactical_threat.py:81-83`, cognition.py panic start.

## 5. Order of work
1. Designer confirms 1, 2, 3 and the "escalated" reading in 4.
2. Field + patch + hash + tests; predicate + tests; scorers swap; panic hold + tests; named pin changes.
3. Docs: intentional_divergences (new 2.x, Enforced, SURV-07/AGENCY-07), parity (present-threat entry), registries/mechanisms.yaml only if the planner says; designer drafts Bible 04 §1 and SURV-07 sentences.
4. Measure on the host when free.

## Scope guards
No push without the user's yes. No tuning constant. No change to step A's files in this ticket.
