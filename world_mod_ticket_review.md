You’re right. I misunderstood your intent earlier.

You are **not asking whether the todo tickets are already implemented**. You are asking:

```text
Are these epic tickets pointing the implementation in the correct architectural direction?
Are there any wrong assumptions, bad dependencies, or tickets that may lead agents to implement the wrong thing?
```

My answer: **the direction is mostly correct**, but several tickets need adjustment before giving them to agents.

# Executive direction review

| Area                         | Direction score | Verdict                                                                                                                        |
| ---------------------------- | --------------: | ------------------------------------------------------------------------------------------------------------------------------ |
| Overall epic direction       |    **8.0 / 10** | Good direction: module-first, composition-first, deterministic generation, data expansion after schema foundation.             |
| Dependency order             |    **7.5 / 10** | Mostly correct, but perspective resolution is too late and pack validation is ambiguous.                                       |
| Ticket clarity for agents    |    **7.0 / 10** | Good ACs, but a few tickets mix data, runtime smoke, and architecture in one scope.                                            |
| Risk of wrong implementation |      **Medium** | Not dangerous, but agents may implement pack refs, schema versioning, and worldgen compile gates incorrectly unless clarified. |

The epic direction is **not wrong**. It aligns with your earlier data direction: world modules should compose lower-layer definitions, not invent primitive meaning; perspectives/scenarios should define how the world is observed; hostility should be derived, not stored as entity type.

---

# What is correct directionally

## 1. Correct: module/composition worldgen instead of direct `WorldSpec` generation

The epic correctly identifies that the old procedural generator should not be the future source of truth. The right direction is:

```text
GenerationIntentSpec
→ score/select modules
→ emit WorldCompositionSpec YAML
→ existing assembly pipeline
→ compile/runtime
```

That is much better than:

```text
GenerationIntentSpec
→ directly create WorldSpec
```

The `WORLDGEN-COMPOSE` ticket explicitly says the generated composition should be inspectable, editable, and passable to the assembly pipeline unchanged, which is the right architectural direction.

## 2. Correct: unified module schema before params/quests/generation

The sequence starts with `WORLDMOD-UNIFY`, then params, pack validation, quest schema, quest contribution, scoring, generation, and data expansion. That ordering is broadly right because scoring and generated compositions should not be built on a split v1/v2 module model.

## 3. Correct: params before parametric data

`WORLDMOD-PARAMS` before `WORLDGEN-SEED-PARAMS`, `WORLDDAT-NEWMODS`, and `WORLDDAT-COMPOSE` is correct. Otherwise agents will write YAML like:

```yaml
count: "{danger_scale} * 3"
```

before the resolver knows how to evaluate it. The ticket direction is right.

## 4. Correct: quest schema before module quest contribution

`WORLDMOD-QUEST-SCHEMA` before `WORLDMOD-QUEST-MOD` is correct. Do not let agents add quest dictionaries into modules before there is a typed `QuestDefinition`.

## 5. Correct: data expansion after foundation

`WORLDDAT-MIGRATE`, `WORLDDAT-NEWMODS`, and `WORLDDAT-COMPOSE` come after schema/params/quest support. That is the right order. New modules like `ruins_mystery_quest` and `scalable_bandit_camp` require quest definitions and parameter expressions, so they should not be authored first.

---

# Main direction issues to fix

## 1. `WORLDSCEN-PERSPECTIVES` is too late

Current sequence puts perspective resolution at the very end:

```text
WORLDDAT-COMPOSE
→ WORLDSCEN-PERSPECTIVES
```

But your design direction says perspective is how enemy/ally is derived, and the same world can be observed from different perspectives.

That means perspective is not just a scenario-layer “afterthought.” It affects how generated compositions and scenario validation should be interpreted.

### Why this matters

`WORLDDAT-COMPOSE` already says `dungeon_crawl` may use:

```yaml
default_perspectives: ["hero_guild_perspective"]
```

So the data composition ticket depends on perspective semantics being clear enough.

### Proposed change

Move `WORLDSCEN-PERSPECTIVES` earlier:

```text
After WORLDMOD-UNIFY
Before WORLDDAT-COMPOSE
Before any scenario-facing generated composition
```

Better sequence:

```text
WORLDMOD-UNIFY
→ WORLDSCEN-PERSPECTIVES
→ WORLDGEN-SCORING / WORLDGEN-COMPOSE
→ WORLDDAT-COMPOSE
```

Or split it:

| Ticket                            | Purpose                                                                |
| --------------------------------- | ---------------------------------------------------------------------- |
| `WORLDSCEN-PERSPECTIVES-CONTEXT`  | Add `CompileContext.perspectives` and default perspective propagation. |
| `WORLDSCEN-PERSPECTIVES-SCENARIO` | Scenario-level validation and resolver behavior.                       |

---

## 2. `WORLDMOD-PACKS` should not use ambiguous `catalog_refs`

The current pack ticket says `WorldCompositionSpec.catalog_refs` may reference content packs, but the same name sounds like it can also reference catalog families. The ticket itself admits this ambiguity: `catalog_refs` may reference catalog family paths rather than pack IDs.

### Why this matters

An agent may implement logic like:

```python
for ref in composition.catalog_refs:
    treat_as_pack(ref)
```

That would be wrong if `catalog_refs` also contains normal catalog family references.

### Proposed change

Add explicit field:

```python
pack_refs: list[str]
```

Then keep `catalog_refs` only for catalog/family-level references.

Better:

```yaml
pack_refs:
  - frontier_extended_pack
catalog_refs:
  - entities/entity_archetypes
  - world/items
```

### Revised direction

`WORLDMOD-PACKS` should become:

```text
Content pack dependency validation through explicit WorldCompositionSpec.pack_refs.
Do not overload catalog_refs.
```

---

## 3. `WORLDMOD-UNIFY` should not remove `schema_version` blindly

The migration ticket says:

```text
Remove schema_version field from all 10 module YAML files
or update to canonical single value if kept
```

That is risky. Removing `schema_version` can weaken fail-closed validation and migration traceability.

### Better direction

Keep a canonical schema version:

```yaml
schema_version: "worldmodule.unified.v1"
```

or:

```yaml
schema_version: "worldmodule.v3"
```

Do not remove it unless you have another explicit versioning mechanism.

### Why

You still need to distinguish:

```text
old v1 module
old v2 module
unified module
future unified module
```

A single canonical value is better than no version.

### Proposed change

Revise `WORLDMOD-UNIFY` and `WORLDDAT-MIGRATE`:

```text
Do not remove schema_version.
Replace old worldmodule.v1/worldmodule.v2 values with schema_version: "worldmodule.unified.v1".
```

---

## 4. `WORLDDAT-COMPOSE` mixes data authoring with runtime smoke testing

The data composition ticket asks each new composition to compile and run 10 simulation ticks.

That is useful, but it makes a **data authoring ticket** depend on runtime stability.

### Why this is risky

If a simulation tick fails due to unrelated combat/economy/runtime logic, the data ticket looks broken.

### Better direction

Split the checks:

| Ticket               | Responsibility                                                     |
| -------------------- | ------------------------------------------------------------------ |
| `WORLDDAT-COMPOSE`   | Create valid composition YAML that loads, assembles, and compiles. |
| `WORLDGEN-E2E-SMOKE` | Generated/new compositions run 10 ticks.                           |

### Proposed change

Move this AC out of `WORLDDAT-COMPOSE`:

```text
Each composition can run 10 simulation ticks without error
```

into a final epic gate:

```text
TCK-20260614-WORLDGEN-E2E-SMOKE
```

---

## 5. `WORLDGEN-COMPOSE` has slight scope conflict

The ticket says assembling/compiling the generated composition is out of scope, but its AC says:

```text
make world-compile WORLD=generated_frontier_3_42 works end-to-end
```

That is not terrible, but it can confuse agents.

### Better direction

Split AC levels:

```text
Unit AC:
- generator writes deterministic YAML
- YAML parses as WorldCompositionSpec
- selected modules and dependencies are correct

Integration AC:
- generated YAML assembles through WorldAssemblyResolver

Epic gate:
- generated YAML compiles and runs smoke ticks
```

So the ticket can keep an integration test, but the `make world-compile` command should probably move to the final smoke ticket.

---

## 6. `WORLDGEN-SCORING` should require explanation/provenance of score

The scorer direction is good, but the ticket only requires module ID → score.

That is enough for a first implementation, but weak for debugging generated worlds.

### Why this matters

When a generated world chooses `goblin_camp_conflict`, you want to know why:

```text
selected because danger_level=3.0, conflict tag, required frontier dependency
```

Otherwise the generator becomes a black box.

### Proposed change

Instead of only:

```python
score(...) -> dict[str, float]
```

prefer:

```python
@dataclass
class ModuleScore:
    module_id: str
    score: float
    reasons: list[str]
    dimensions: dict[str, float]
```

Then:

```python
score(...) -> dict[str, ModuleScore]
```

or keep the dict API but add:

```python
explain(...) -> dict[str, ModuleScoreExplanation]
```

### Direction change

Add AC:

```text
Scoring exposes explanation data for selected modules.
Generated composition provenance includes score and reason for each selected module.
```

This aligns with your earlier rule that provenance must preserve which lower-layer data caused higher-layer world structure.

---

## 7. `WORLDGEN-COMPOSE` needs collision/incompatibility direction

The ticket selects highest-scoring modules and auto-includes dependencies. That is good, but it does not clearly define what happens when modules conflict.

Examples:

```text
two terrain modules define incompatible topology
two settlement modules both claim the same central region
wilderness_survival asks for no settlement, but required dependency pulls one in
```

### Proposed change

Add one of these policies:

```text
Option A: strict collision policy
- generation fails if selected modules conflict

Option B: scorer avoids conflict
- scorer penalizes incompatible modules

Option C: composition generator emits warnings
- generator writes composition but marks blocking validation warnings
```

For this phase, choose **Option A**:

```text
ProceduralCompositionGenerator must fail with GenerationCompositionError if selected modules have blocking conflicts.
```

Do not silently resolve conflicts yet.

---

## 8. `WORLDDAT-NEWMODS` risks making modules too powerful

The new modules are directionally good, especially:

```text
forest_deep_ecology
ruins_mystery_quest
trading_company_hub
scalable_bandit_camp
```

But the module direction must keep your core rule:

```text
Modules compose lower definitions.
Modules should not invent primitive meaning.
```

The `new_data_direction.md` explicitly says modules should not invent primitive meaning, and must compose lower-layer definitions.

### Risk

A module like `ruins_mystery_quest` may tempt agents to embed behavior directly:

```yaml
behavior: spawn_mystery
enemy: cursed_spirit
```

That would be wrong.

### Proposed change

Add explicit anti-drift AC to `WORLDDAT-NEWMODS`:

```text
No new module may introduce primitive behavior, enemy labels, or direct scripted behavior.
All behavior must be expressed through lower-layer refs:
biomes, ecologies, populations, relationships, quests, resources, services, pressure tags, and provenance.
```

---

# Corrected direction table

| Ticket                   | Direction verdict      | Required adjustment                                                    |
| ------------------------ | ---------------------- | ---------------------------------------------------------------------- |
| `WORLDMOD-UNIFY`         | Correct but too broad  | Keep canonical `schema_version`; split schema/resolver/docs if needed. |
| `WORLDMOD-PARAMS`        | Correct                | Add explicit safe expression grammar and type coercion rules.          |
| `WORLDMOD-PACKS`         | Direction partly wrong | Use `pack_refs`, not overloaded `catalog_refs`.                        |
| `WORLDMOD-QUEST-SCHEMA`  | Correct                | Keep `quests` as compatibility alias for one phase if needed.          |
| `WORLDMOD-QUEST-MOD`     | Correct                | Require provenance and duplicate quest ID policy.                      |
| `WORLDGEN-SCORING`       | Correct but incomplete | Add score explanation/provenance.                                      |
| `WORLDGEN-COMPOSE`       | Correct                | Move full compile/smoke to final gate; add conflict policy.            |
| `WORLDGEN-SEED-PARAMS`   | Correct                | Ensure deterministic sampling order is explicit and stable.            |
| `WORLDDAT-MIGRATE`       | Correct                | Do not remove schema version; use canonical unified version.           |
| `WORLDDAT-NEWMODS`       | Correct                | Add anti-drift rule: modules compose, not invent behavior.             |
| `WORLDDAT-COMPOSE`       | Correct                | Move 10-tick smoke to final gate.                                      |
| `WORLDSCEN-PERSPECTIVES` | Correct but too late   | Move earlier or split into context + scenario ticket.                  |

---

# Revised recommended sequence

```text
Phase 1 — Foundation
1. WORLDMOD-UNIFY-SCHEMA
2. WORLDMOD-UNIFY-RESOLVER
3. WORLDMOD-PARAMS
4. WORLDMOD-QUEST-SCHEMA
5. WORLDMOD-QUEST-MOD
6. WORLDMOD-PACKS using pack_refs
7. WORLDSCEN-PERSPECTIVES-CONTEXT

Phase 2 — Procedural generation
8. WORLDGEN-SCORING with explanation/provenance
9. WORLDGEN-COMPOSE with strict conflict policy
10. WORLDGEN-SEED-PARAMS

Phase 3 — Data expansion
11. WORLDDAT-MIGRATE
12. WORLDDAT-NEWMODS
13. WORLDDAT-COMPOSE

Phase 4 — Scenario and E2E gates
14. WORLDSCEN-PERSPECTIVES-SCENARIO
15. WORLDGEN-E2E-SMOKE
```

---

# Final answer

The epic direction is **mostly good**. I would not throw it away.

But before implementation, I would fix these direction issues:

```text
1. Move/split perspective resolution earlier.
2. Replace catalog_refs pack validation with explicit pack_refs.
3. Keep canonical schema_version instead of removing it.
4. Move 10-tick simulation smoke out of data tickets into final E2E gate.
5. Add scoring explanation/provenance.
6. Add strict conflict policy to generated composition selection.
7. Add anti-drift rule: modules compose lower data; they do not invent primitive behavior.
```

After those edits, the epic would be safe to hand to coding agents.
