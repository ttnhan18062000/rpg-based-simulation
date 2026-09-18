---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION
artifact_type: investigation
tags: [architecture, documentation, investigation]
---

# Investigation — TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION

Full findings are recorded in the ticket body's own Implementation Notes section. This artifact
preserves the raw derivation script and its complete output, for anyone who wants to re-run or
extend the check.

## Method

Reused `tools.mechanism_registry.registry.transitive_dependencies_of(mechanism_id, dep_map)`
directly — the existing ancestors-of traversal already used by
`generate_mechanism_priority_view.py`'s own chart generation — rather than reimplementing it, per
this ticket's own explicit instruction. Ran against the real, committed `registries/mechanisms.yaml`
(93 mechanisms, post the identity-rules ticket's own 4 splits).

## Script

```python
import yaml, sys
sys.path.insert(0, ".")
from tools.mechanism_registry.registry import transitive_dependencies_of

data = yaml.safe_load(open("registries/mechanisms.yaml"))
dep_map = {m["id"]: m.get("depends_on") or [] for m in data["mechanisms"]}
states = {m["id"]: m.get("state") for m in data["mechanisms"]}
verified = {m["id"]: m.get("verified") for m in data["mechanisms"]}

CANDIDATE_ROOTS = {
    "combat": ["combat_resolution"],
    "progression": ["breakthrough_bonuses", "xp_leveling"],
    "economy/trade": ["crafting", "equipment_scoring"],
    "social": ["reputation", "commitment_pressure_consequences", "goal_hierarchy"],
}

for domain, roots in CANDIDATE_ROOTS.items():
    for root in roots:
        ancestors = transitive_dependencies_of(root, dep_map)
        members = sorted(ancestors | {root})
        # print member list with state/verified per mechanism
```

## Full raw output

```
=== combat ===
  root=combat_resolution (n=8):
    action_pacing_readiness   state=done     verified=scenario/observed
    combat_engagement         state=done     verified=scenario/observed
    combat_resolution         state=done     verified=corpus_run/observed
    entity_role               state=done     verified=unverified
    movement                  state=done     verified=unverified
    personality               state=done     verified=unverified
    skill_unlocks             state=partial  verified=unverified
    status_effects            state=partial  verified=unverified

=== progression ===
  root=breakthrough_bonuses (n=10): [same 8 as combat] + breakthrough_bonuses, xp_leveling
  root=xp_leveling (n=9): [same 8 as combat] + xp_leveling

=== economy/trade ===
  root=crafting (n=2): crafting (partial), inventory_trade_conservation (done)
  root=equipment_scoring (n=2): equipment_scoring (done), inventory_trade_conservation (done)

=== social ===
  root=reputation (n=4):
    action_pacing_readiness, affection_relationship_bonds, interaction_channeling, reputation
  root=commitment_pressure_consequences (n=10): [same 8 as combat] + commitment_betrayal,
    commitment_pressure_consequences
  root=goal_hierarchy (n=17):
    action_pacing_readiness, affection_relationship_bonds, belief_cycle,
    cognition_capacity_fatigue, combat_engagement, combat_resolution, entity_role,
    goal_hierarchy, interaction_channeling, movement, perception, personality, reputation,
    self_model (gated), skill_unlocks, status_effects, trauma
```

## Edge-trust computation

Internal edges = `(A, B)` where both `A` and `B` are in the derived member set and `B ∈
depends_on(A)`. "Audited" = one of the 5 edges directly checked by
`TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY`
(`combat_resolution → {combat_engagement, movement, status_effects, entity_role, skill_unlocks}`).
Every other edge in every derived set predates that check.

| Set | Internal edges | Audited | Unaudited |
|---|---|---|---|
| combat (`combat_resolution`) | 8 | 5 | 3 |
| progression (`xp_leveling`) | 9 | 5 | 4 |
| economy (`crafting`) | 1 | 0 | 1 |
| social (`reputation`) | 3 | 0 | 3 |
| social (`goal_hierarchy`) | 18 | 5 | 13 |

## Axis test case

Tested "do axes attach to mechanisms or systems" against
`docs/brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md`. Its own real concerns
(succession, aging/lifecycle horizons, demographic cohort cycling, institutional/commitment
continuity) map to `succession`, `aging_death`, `demographic_cohort_cycle`, `commitment_betrayal` —
mechanisms spread across the `progression`, `social`, and `world` candidate systems derived above,
not concentrated in one. See ticket body for the resulting conclusion (mechanisms, not systems).
