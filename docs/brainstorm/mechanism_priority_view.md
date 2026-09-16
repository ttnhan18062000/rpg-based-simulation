# Mechanism Priority View — Top 25 Unverified

Generated from `docs/brainstorm/mechanisms.yaml` — regenerate with
`make mechanism-priority-view`. Do not hand-edit.

**Which mechanism to verify next.** 77 of 86 mechanisms are currently
unverified (see `docs/brainstorm/mechanism_verification_view.md`). Priority is derived, never
hand-ranked: `layer weight × transitive dependent-count`, computed from the registry's own
`depends_on` edges — a hub mechanism nobody has verified is the highest-value next target, since
more depends on it. Ranked below, top 25.

## Text form

| Mechanism | Layer | State | Priority | Transitive Dependents |
|---|---|---|---|---|
| `movement` | entity | done | 70 | 14 |
| `personality` | entity | done | 70 | 14 |
| `tactical_decision` | entity | done | 70 | 14 |
| `entity_role` | entity | done | 65 | 13 |
| `skill_unlocks` | entity | partial | 65 | 13 |
| `status_effects` | entity | partial | 65 | 13 |
| `combat_resolution` | entity | done | 60 | 12 |
| `cognition_capacity_fatigue` | entity | done | 45 | 9 |
| `perception` | entity | done | 40 | 8 |
| `trauma` | entity | done | 40 | 8 |
| `betrayal_siege_war` | faction | done | 33 | 11 |
| `belief_cycle` | entity | done | 30 | 6 |
| `interaction_channeling` | entity | done | 30 | 6 |
| `affection_relationship_bonds` | entity | done | 25 | 5 |
| `regional_trauma_hazards_sovereignty` | region | done | 16 | 8 |
| `goal_hierarchy` | entity | done | 15 | 3 |
| `race_archetype` | entity | done | 15 | 3 |
| `reputation` | faction | done | 12 | 4 |
| `attributes_biology` | entity | done | 10 | 2 |
| `world_generation` | world | done | 9 | 9 |
| `aging_death` | entity | done | 5 | 1 |
| `class_assignment` | entity | partial | 5 | 1 |
| `derived_stats` | entity | done | 5 | 1 |
| `xp_leveling` | entity | done | 5 | 1 |
| `campaigns` | world | done | 4 | 4 |

## Chart form

```mermaid
flowchart BT
    classDef done fill:#e4efe6,stroke:#3f7d5c,stroke-width:2px,color:#232019
    classDef partial fill:#fdf3d8,stroke:#b8860b,stroke-width:2px,color:#232019
    classDef gap fill:#f7e4e1,stroke:#b0392f,stroke-width:2px,color:#232019
    classDef orphan fill:#f7e4e1,stroke:#b0392f,stroke-width:2px,stroke-dasharray: 2 2,color:#232019
    classDef gated fill:#f7ecd2,stroke:#9a6b0c,stroke-width:2px,stroke-dasharray: 3 3,color:#232019
    classDef skeleton fill:#eee,stroke:#888,stroke-width:1px,stroke-dasharray: 1 3,color:#232019

    affection_relationship_bonds["affection relationship bonds"]:::done
    aging_death["aging death"]:::done
    attributes_biology["attributes biology"]:::done
    belief_cycle["belief cycle"]:::done
    betrayal_siege_war["betrayal siege war"]:::done
    campaigns["campaigns"]:::done
    class_assignment["class assignment"]:::partial
    cognition_capacity_fatigue["cognition capacity fatigue"]:::done
    combat_resolution["combat resolution"]:::done
    derived_stats["derived stats"]:::done
    entity_role["entity role"]:::done
    goal_hierarchy["goal hierarchy"]:::done
    interaction_channeling["interaction channeling"]:::done
    movement["movement"]:::done
    perception["perception"]:::done
    personality["personality"]:::done
    race_archetype["race archetype"]:::done
    regional_trauma_hazards_sovereignty["regional trauma hazards sovereignty"]:::done
    reputation["reputation"]:::done
    skill_unlocks["skill unlocks"]:::partial
    status_effects["status effects"]:::partial
    tactical_decision["tactical decision"]:::done
    trauma["trauma"]:::done
    world_generation["world generation"]:::done
    xp_leveling["xp leveling"]:::done

    interaction_channeling --> affection_relationship_bonds
    race_archetype --> class_assignment
    tactical_decision --> combat_resolution
    movement --> combat_resolution
    status_effects --> combat_resolution
    entity_role --> combat_resolution
    skill_unlocks --> combat_resolution
    attributes_biology --> derived_stats
    belief_cycle --> goal_hierarchy
    reputation --> goal_hierarchy
    cognition_capacity_fatigue --> perception
    betrayal_siege_war --> regional_trauma_hazards_sovereignty
    world_generation --> regional_trauma_hazards_sovereignty
    affection_relationship_bonds --> reputation
    combat_resolution --> trauma
    combat_resolution --> xp_leveling
```
