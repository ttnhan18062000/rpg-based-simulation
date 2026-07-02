---
status: idea
layer: world
authority: P2
audience: developer
maturity: idea
date: 2026-06-20
tags: [idea, world-grammar, semantic-constraints, content-validation, quest-generation, world-authoring]
---

# Idea: World Grammar with Semantic Constraints

> **Maturity: IDEA** — Not scheduled. Consider before or alongside E13 Content Foundation.

---

## Problem

World authoring today is purely structural: the WorldCompiler validates that field types are correct, catalog IDs are registered, and required sections are present. It does not validate that the *combination* of authored content is semantically coherent — that the world will produce non-trivial behavior when the simulation runs.

Two upcoming tickets expose this gap directly:

1. **E13 Content Foundation** targets 30+ quest definitions across 8+ world modules. Without semantic constraints, it is possible to author quests that reference factions with no territory, resource nodes in biomes where they cannot spawn, or calamity triggers without any entity capable of responding.
2. **E23 Quest Generation** auto-generates `QuestOpportunity` entries triggered by world events. A generator that cannot validate semantic fit will produce dead quests: well-formed YAML that the runtime parses, but that no entity ever has reason to accept.

The result is **silent dead content**: the world compiles without error, the simulation runs without crash, but no interesting behavior emerges because the authored content doesn't form coherent causal chains.

---

## Idea

Define a **World Grammar**: a layer of semantic validation rules that run after structural validation and verify that the authored world's content forms coherent causal chains.

### Grammar rule types

| Rule class | Example |
|---|---|
| **Reachability** | Every quest must have ≥1 entity archetype that can accept it (role + class alignment) |
| **Resource coverage** | Every resource node type referenced by a quest must exist in ≥1 biome region of that world |
| **Trigger completeness** | Every calamity type that triggers quest opportunities must have ≥1 entity within affected region range |
| **Faction coherence** | If a quest involves faction tension, both factions must have territorial presence in the world |
| **Density floor** | Each world module that has quests must have ≥2 entity spawns that can reach the quest zone |

Rules are declarative (YAML or Python predicate functions), composable, and produce **named violations** that map to the authoring file and line that caused them.

### Output

```
WorldGrammarReport:
  world_id: str
  checked_at: datetime
  violations: List[GrammarViolation]
    rule_id: str
    severity: WARNING | ERROR
    message: str
    source_file: str
    source_entity: str
  summary: valid | warnings_only | invalid
```

`ERROR`-level violations block compilation. `WARNING`-level violations pass but appear in the report. The threshold (which rules are ERROR vs WARNING) is configurable per world.

### Where it fits in the pipeline

```
WorldSpec YAML
      ↓
Structural validation (existing — field types, catalog IDs)
      ↓
World Grammar validation (new — semantic coherence)  ← this idea
      ↓
WorldCompiler.compile() → AuthoritativeWorldState
```

---

## Relationship to Planned Tickets

### E13-CONTENT-FOUNDATION (gap — authoring without feedback)

E13 plans: *"Author 30+ quest definitions covering at least 8 world modules (currently only 3 have any)."*

Authoring 30 quest definitions without semantic feedback is high-risk. A quest that references a region role, faction type, or entity archetype not present in the target world will appear to work (no compile error) but never fire at runtime. The author gets no signal until they run the simulation and observe zero quest pickups.

**Impact on E13**: gap. Without a grammar layer, E13 deliverables have no automated quality gate. The acceptance criteria ("30+ quest definitions") may be met on paper while producing dead content. Recommend: define at minimum a `reachability` rule before E13 authoring begins, so each quest has a verifiable "can any entity in this world accept this?" check.

**Risk level: HIGH.** If E13 ships without this, the 30 quest definitions become a maintenance liability — individually valid but collectively incoherent.

### E23-QUEST-GENERATION (gap — generator correctness)

E23 plans: *"QuestOpportunity as new OpportunityType; QuestOpportunityGenerator triggered by: resource depletion events (Epic 2.1), faction tension thresholds, calamity aftermath signals, entity needs unsatisfied for N ticks; wire into adventure decision pipeline for HERO entities."*

The `QuestOpportunityGenerator` will synthesize quest parameters from world event signals. Without semantic constraint checking, a generated quest can reference a faction that no longer has territory (post-conflict), a resource zone that is depleted to zero, or an entity archetype that was never authored in this world.

**Impact on E23**: gap. The generator needs a lightweight **pre-emit validation** step: before a `QuestOpportunity` is added to the entity's opportunity pool, check that it satisfies the same grammar rules as authored quests. The World Grammar layer provides these checks for free if it exposes a programmatic API (not just a build-time validator).

**Risk level: MEDIUM.** Generated quests fail silently at runtime without this — entities see a quest opportunity and evaluate it, but the acceptance score is low because the preconditions are unmet. Difficult to distinguish from intentional design.

---

## Open Questions

- Should grammar rules be defined in code (Python predicates) or data (YAML rule definitions)?
- What is the right severity split — which violations should block compile vs warn?
- Does the grammar layer run at world-load time (each simulation start) or only at author-time (pre-commit)?
- How do grammar rules interact with procedurally generated worlds (E23's runtime generation)? Runtime grammar must be cheaper than build-time grammar.

---

*Raised: 2026-06-20. Deferred pending E13 authoring scope confirmation.*
