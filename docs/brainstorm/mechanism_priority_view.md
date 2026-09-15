# Mechanism Priority View — Top 25 Unverified

Generated from `docs/brainstorm/mechanisms.yaml` — regenerate with
`make mechanism-priority-view`. Do not hand-edit.

**Which mechanism to verify next.** 69 of 75 mechanisms are currently
unverified (see `docs/brainstorm/mechanism_verification_view.md`). Priority is derived, never
hand-ranked: `layer rank × transitive dependent-count`, computed from the registry's own
`depends_on` edges — a hub mechanism nobody has verified is the highest-value next target, since
more depends on it. Ranked below, top 25.

## Text form

| Mechanism | Layer | State | Priority | Transitive Dependents |
|---|---|---|---|---|
| `betrayal_siege_war` | faction | done | 33 | 11 |
| `regional_trauma_hazards_sovereignty` | region | done | 32 | 8 |
| `action_pacing_readiness` | entity | partial | 23 | 23 |
| `tactical_decision` | entity | done | 14 | 14 |
| `combat_resolution` | entity | done | 12 | 12 |
| `reputation` | faction | done | 12 | 4 |
| `cognition_capacity_fatigue` | entity | done | 9 | 9 |
| `city` | region | partial | 8 | 2 |
| `perception` | entity | done | 8 | 8 |
| `trauma` | entity | done | 8 | 8 |
| `belief_cycle` | entity | done | 6 | 6 |
| `interaction_channeling` | entity | done | 6 | 6 |
| `affection_relationship_bonds` | entity | done | 5 | 5 |
| `buildings_town_services` | world | done | 5 | 1 |
| `camp` | region | done | 4 | 1 |
| `goal_hierarchy` | entity | done | 3 | 3 |
| `race_archetype` | entity | done | 3 | 3 |
| `social_memory` | faction | skeleton | 3 | 1 |
| `attributes_biology` | entity | done | 2 | 2 |
| `aging_death` | entity | done | 1 | 1 |
| `class_assignment` | entity | partial | 1 | 1 |
| `derived_stats` | entity | done | 1 | 1 |
| `motivation_doctrine` | entity | partial | 1 | 1 |
| `xp_leveling` | entity | done | 1 | 1 |
| `adventure_routing` | entity | done | 0 | 0 |

## Chart form

```mermaid
flowchart BT
    classDef done fill:#e4efe6,stroke:#3f7d5c,stroke-width:2px,color:#232019
    classDef partial fill:#fdf3d8,stroke:#b8860b,stroke-width:2px,color:#232019
    classDef gap fill:#f7e4e1,stroke:#b0392f,stroke-width:2px,color:#232019
    classDef orphan fill:#f7e4e1,stroke:#b0392f,stroke-width:2px,stroke-dasharray: 2 2,color:#232019
    classDef gated fill:#f7ecd2,stroke:#9a6b0c,stroke-width:2px,stroke-dasharray: 3 3,color:#232019
    classDef skeleton fill:#eee,stroke:#888,stroke-width:1px,stroke-dasharray: 1 3,color:#232019

    action_pacing_readiness["action pacing readiness"]:::partial
    adventure_routing["adventure routing"]:::done
    affection_relationship_bonds["affection relationship bonds"]:::done
    aging_death["aging death"]:::done
    attributes_biology["attributes biology"]:::done
    belief_cycle["belief cycle"]:::done
    betrayal_siege_war["betrayal siege war"]:::done
    buildings_town_services["buildings town services"]:::done
    camp["camp"]:::done
    city["city"]:::partial
    class_assignment["class assignment"]:::partial
    cognition_capacity_fatigue["cognition capacity fatigue"]:::done
    combat_resolution["combat resolution"]:::done
    derived_stats["derived stats"]:::done
    goal_hierarchy["goal hierarchy"]:::done
    interaction_channeling["interaction channeling"]:::done
    motivation_doctrine["motivation doctrine"]:::partial
    perception["perception"]:::done
    race_archetype["race archetype"]:::done
    regional_trauma_hazards_sovereignty["regional trauma hazards sovereignty"]:::done
    reputation["reputation"]:::done
    social_memory["social memory"]:::skeleton
    tactical_decision["tactical decision"]:::done
    trauma["trauma"]:::done
    xp_leveling["xp leveling"]:::done

    motivation_doctrine --> adventure_routing
    cognition_capacity_fatigue --> adventure_routing
    interaction_channeling --> affection_relationship_bonds
    city --> buildings_town_services
    regional_trauma_hazards_sovereignty --> camp
    regional_trauma_hazards_sovereignty --> city
    race_archetype --> class_assignment
    tactical_decision --> combat_resolution
    attributes_biology --> derived_stats
    belief_cycle --> goal_hierarchy
    reputation --> goal_hierarchy
    action_pacing_readiness --> interaction_channeling
    goal_hierarchy --> motivation_doctrine
    affection_relationship_bonds --> motivation_doctrine
    cognition_capacity_fatigue --> perception
    betrayal_siege_war --> regional_trauma_hazards_sovereignty
    affection_relationship_bonds --> reputation
    action_pacing_readiness --> tactical_decision
    combat_resolution --> trauma
    combat_resolution --> xp_leveling
```
