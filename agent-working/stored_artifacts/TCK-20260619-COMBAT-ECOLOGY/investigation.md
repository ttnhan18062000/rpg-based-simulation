# Investigation: TCK-20260619-COMBAT-ECOLOGY

## Grudge System — Current State

### What exists
- `SocialComponent.grudge_history: Dict[int, float]` — continuous damage-ratio score (0.0–5.0 cap)
- `SocialComponent.nemesis_ids: Set[int]` — promoted when grudge >= 3.0 (in `memory.py::check_nemesis_promotion`)
- `combat.py::resolve_attack` emits `grudge_delta = {attacker.id: damage/max_hp}` on every hit
- `cognition.py` gives +250 to enemy score for nemesis, +50×grudge for grudge score
- `combat_engagement/selector.py` has `VENGEANCE_ENGAGE` posture for grudge_vengeance override
- `cooperation/services.py` also raises grudge (0.3 for conflict, 0.9 for betrayal)

### What is missing
- **No per-opponent discrete loss count** — grudge is a float accumulation, not "how many times beaten"
- **No `fear_avoidance_project`** — no project kind, no goal scorer, no posture override for "this entity beaten me too many times"
- **No cross-episode persistence** — all state lives in `AuthoritativeState`; requires Epic 3.2 (CampaignState), not done

## Scope Decision — Run-Only
Cross-episode grudge is BLOCKED by Epic 3.2 (TCK-20260619-E32-CAMPAIGN-RUNTIME, epic tier, not implemented). This ticket implements the **run-scoped** fear avoidance extension only.

## Implementation Approach

### Add `combat_loss_counts: Dict[int, int]` to SocialComponent
Discrete integer counter "how many times was I killed/knocked out by this entity in this run." This is distinct from `grudge_history` (continuous damage ratio). Both serve complementary purposes.

### Emit `combat_loss_delta` on kill
In `combat.py::resolve_attack` at line ~208, when `not alive and defender.combat.alive`, add `combat_loss_delta = {attacker.id: 1}` to the defender's `social_upd`.

### Fear avoidance in CombatEngagementDecisionService
In `service.py::evaluate()`, check `actor.social.combat_loss_counts.get(target.id, 0) >= 3` BEFORE the full pipeline. If true, short-circuit and return `CombatPosture.AVOID` with reason `"fear_avoidance"`. This satisfies "entity generates fear_avoidance_project instead of combat_engage" — the avoidance is the project outcome.

## Files to Change
1. `src/core/models/social.py` — add `combat_loss_counts: Dict[int, int]`
2. `src/core/updates.py` — add `combat_loss_delta: Dict[int, int]` to `SocialUpdate`; update `is_noop()` and `merge()`
3. `src/engine/combat.py` — emit `combat_loss_delta` when defender killed
4. `src/systems/social_systems/relationships.py` — apply `combat_loss_delta`
5. `src/core/builder.py` — carry `combat_loss_counts` through `with_social_changes()`
6. `src/core/state.py` — serialize `combat_loss_counts` in `debug_summary()`
7. `src/domains/combat_engagement/service.py` — fear_avoidance short-circuit

## Parity
Update `docs/parity_ledger/combat_movement.yaml` with:
- COMB-XXX: grudge scope is run-only (status=verified)
- COMB-XXX: fear_avoidance posture at loss_count >= 3 (status=verified)
