# Phase 13 — Mutation and Balance Lab

Phase 12 gives you:

```text
WorldSpec + ScenarioSpec + ExperimentSpec
-> validate
-> compile
-> run
-> observe
-> analyze
-> store lab results
```

Phase 13 should add:

```text
controlled variation
+ balance comparison
+ metamorphic validation
+ regression discovery
```

The goal is:

> Take a known world/scenario, mutate it in controlled ways, run experiments, compare results, and decide whether the simulation behavior still makes sense.

This becomes the practical balancing/debugging lab.

---

# Phase 13 Main Objective

Build a **Mutation and Balance Lab** that can answer:

```text
What happens if we change resource density?
What happens if we increase worker count?
What happens if one bridge is blocked?
What happens if shop gold is reduced?
What happens if monster attack increases by 20%?
What happens if inventory capacity doubles?
Did the new engine version make behavior worse?
Did the new balance profile improve the simulation?
```

This is extremely useful because it turns the Observatory from passive monitoring into an active experimental system.

---

# Phase 13 should include

```text
1. MutationSpec schema
2. Controlled world/scenario mutation engine
3. Balance experiment matrix
4. Metamorphic expectation checks
5. Variant run orchestration
6. Variant comparison reports
7. Regression / improvement detection
8. Guardrails for combinatorial explosion
9. Tests that prevent fake balance conclusions
```

---

# Phase 13 should not include yet

```text
1. Automatic stat tuning
2. AI-generated worlds
3. Full optimization loop
4. Genetic algorithm balancing
5. Visual balance editor
6. Database-backed experiment store
7. Distributed execution
```

Do not jump to auto-balancing yet.

First build reliable controlled experiments.

---

# New concept: MutationSpec

Phase 11:

```text
WorldSpec = what exists
```

Phase 12:

```text
ScenarioSpec = what we test
ExperimentSpec = how we run it
```

Phase 13 adds:

```text
MutationSpec = what we change
```

---

# Example MutationSpec

```yaml
schema_version: mutationspec.v1
mutation_id: resource_density_matrix
name: Resource Density Matrix

base_world_id: resource_valley_basic
base_scenario_id: resource_economy_basic

mutations:
  - id: resource_density_low
    target: resources.nodes.wood_zone.count
    operation: multiply
    value: 0.5

  - id: resource_density_high
    target: resources.nodes.wood_zone.count
    operation: multiply
    value: 2.0

  - id: shop_gold_low
    target: buildings.village_shop.inventory.gold
    operation: set
    value: 100

  - id: inventory_capacity_high
    target: entities.populations.workers.inventory.capacity
    operation: multiply
    value: 2.0

matrix:
  mode: one_at_a_time

expected_relationships:
  - id: more_resources_should_not_reduce_production
    type: monotonic_non_decreasing
    metric: resource_production_rate
    baseline_variant: base
    compared_variant: resource_density_high
```

---

# Phase 13 Milestones

```text
Milestone 84 — MutationSpec Schema
Milestone 85 — Mutation Engine
Milestone 86 — Variant Matrix Builder
Milestone 87 — Metamorphic Validation Rules
Milestone 88 — Balance Comparison Engine
Milestone 89 — Mutation Lab Orchestrator
Milestone 90 — Mutation Lab Reports and CLI
Milestone 91 — Phase 13 Safety and Test Strategy
```

---

# Milestone 84 — MutationSpec Schema

## Goal

Define mutation experiments as files.

Recommended layout:

```text
data/mutations/
  resource_density_matrix/
    mutation.yaml
  combat_damage_matrix/
    mutation.yaml
  inventory_capacity_matrix/
    mutation.yaml
```

---

## Supported mutation operations

Start small:

| Operation   | Meaning                 |
| ----------- | ----------------------- |
| `set`       | replace value           |
| `add`       | add numeric value       |
| `multiply`  | multiply numeric value  |
| `remove`    | remove object/item      |
| `duplicate` | duplicate object/recipe |
| `toggle`    | boolean switch          |

Do not support arbitrary Python expressions.

---

## Supported mutation targets

Start with:

```text
world topology
regions
resources
buildings
entity populations
entity stats profiles
inventory profiles
faction starting resources
quest rewards
combat stats
strategic cognition profile
```

Do not allow arbitrary deep object mutation without validation.

---

## Required schema fields

```text
schema_version
mutation_id
base_world_id
base_scenario_id
mutations
matrix
expected_relationships optional
budgets optional
tags optional
```

---

## Tests

Add:

```text
tests/unit/lab/test_mutationspec_schema.py
tests/unit/lab/test_mutationspec_validator.py
```

Required tests:

```text
[ ] valid MutationSpec loads
[ ] missing mutation_id is rejected
[ ] missing base_world_id is rejected
[ ] invalid operation is rejected
[ ] invalid target path is rejected
[ ] unknown matrix mode is rejected
[ ] expected relationship references known metric
```

Anti-misdirection tests:

```text
[ ] MutationSpec validation does not mutate the world
[ ] unknown target path is not silently ignored
[ ] arbitrary code/expression is rejected
```

---

# Milestone 85 — Mutation Engine

## Goal

Apply controlled changes to WorldSpec / ScenarioSpec safely.

Component:

```text
MutationEngine
```

Input:

```text
base WorldSpec
base ScenarioSpec
MutationSpec
```

Output:

```text
mutated WorldSpec / ScenarioSpec variants
MutationApplyReport
```

---

## Important rule

The mutation engine should not mutate the original object in place.

It should produce a copy:

```text
base_world
  -> cloned_world
  -> apply mutation
  -> validate mutated world
```

---

## Mutation report

Each mutation should produce:

```text
mutation_id
target
operation
old_value
new_value
status
warnings
errors
```

---

## Tests

Add:

```text
tests/unit/lab/test_mutation_engine.py
```

Required tests:

```text
[ ] set operation works
[ ] add operation works
[ ] multiply operation works
[ ] remove operation works
[ ] toggle operation works
[ ] base world is not mutated
[ ] mutation report includes old/new values
[ ] invalid target fails clearly
[ ] invalid resulting world fails validation
```

Critical test:

```text
[ ] mutation cannot bypass WorldValidator
```

This prevents a mutated world from becoming structurally invalid.

---

# Milestone 86 — Variant Matrix Builder

## Goal

Generate experiment variants.

Mutation can be applied in different ways.

---

## Matrix modes

Start with three:

| Mode                | Meaning                             |
| ------------------- | ----------------------------------- |
| `one_at_a_time`     | apply one mutation per variant      |
| `combined`          | apply all mutations together        |
| `factorial_limited` | generate combinations up to a limit |

Do not start with full factorial for everything. It can explode quickly.

---

## Example

Given mutations:

```text
resource_low
resource_high
shop_low_gold
inventory_high
```

`one_at_a_time` produces:

```text
base
resource_low
resource_high
shop_low_gold
inventory_high
```

`combined` produces:

```text
base
combined_all
```

`factorial_limited` might produce:

```text
base
resource_low + shop_low_gold
resource_high + inventory_high
...
```

with max variant count.

---

## Components

```text
VariantMatrixBuilder
WorldVariant
ScenarioVariant
VariantManifest
```

---

## VariantManifest fields

```text
variant_id
base_world_id
base_scenario_id
applied_mutations
world_spec_path
scenario_spec_path
status
validation_result
```

---

## Tests

Add:

```text
tests/unit/lab/test_variant_matrix_builder.py
```

Required tests:

```text
[ ] one_at_a_time creates expected variants
[ ] combined creates expected variant
[ ] factorial_limited respects max variant count
[ ] base variant is included
[ ] variant IDs are stable
[ ] variant manifest is deterministic
```

Anti-misdirection test:

```text
[ ] matrix builder refuses unbounded full factorial by default
```

---

# Milestone 87 — Metamorphic Validation Rules

## Goal

Define expected relationships between variants.

This is very important.

Traditional test:

```text
exact output should be X
```

Metamorphic test:

```text
when input changes in a known way, output should change in a reasonable direction
```

---

## Examples

### Resource economy

```text
Increasing resource nodes should not reduce resource production.
Increasing inventory capacity should not increase inventory-full anomalies.
Adding shops should not reduce transaction completion.
Blocking a bridge should not improve pathing health.
```

### Combat

```text
Increasing monster attack should not reduce hero death rate.
Increasing armor should not increase incoming damage.
Increasing faction size should not reduce that faction's survival rate unless overcrowding occurs.
```

### Quest

```text
Increasing quest reward should not reduce quest acceptance if reward is part of scoring.
Making required item unavailable should increase quest stall or failure.
```

---

## Components

```text
MetamorphicRule
MetamorphicRuleEngine
MetamorphicComparisonResult
```

---

## Rule types

Start with:

| Rule type                   | Meaning                                   |
| --------------------------- | ----------------------------------------- |
| `monotonic_non_decreasing`  | metric should stay same or increase       |
| `monotonic_non_increasing`  | metric should stay same or decrease       |
| `within_tolerance`          | metric should remain near baseline        |
| `expected_worse`            | mutation intentionally worsens condition  |
| `expected_better`           | mutation intentionally improves condition |
| `no_new_hard_law_violation` | mutation must not introduce laws          |

---

## Tests

Add:

```text
tests/unit/lab/test_metamorphic_rules.py
tests/integration/lab/test_metamorphic_validation_flow.py
```

Required tests:

```text
[ ] monotonic_non_decreasing passes when metric increases
[ ] monotonic_non_decreasing fails when metric decreases
[ ] within_tolerance handles small differences
[ ] expected_worse passes when target metric worsens
[ ] no_new_hard_law_violation fails on hard law violation
[ ] missing metric produces INSUFFICIENT_DATA
```

Anti-misdirection tests:

```text
[ ] missing metric is not treated as pass
[ ] weak baseline is marked as weak evidence
[ ] expected_worse does not mean engine failure
```

---

# Milestone 88 — Balance Comparison Engine

## Goal

Compare variants and explain whether a mutation improved or worsened behavior.

Component:

```text
BalanceComparisonEngine
```

---

## Inputs

```text
base variant run results
mutated variant run results
scenario expectations
metamorphic rules
observability metrics
anomaly summaries
```

---

## Outputs

```text
balance_comparison.json
balance_comparison.md
```

---

## Comparison dimensions

Start with:

```text
health score
critical anomalies
hard law violations
stuck ratio
resource production
quest completion
combat resolution
runtime performance
memory usage
event volume
```

Only include metrics that exist.

---

## Classification

Each variant comparison should produce:

```text
IMPROVED
REGRESSED
UNCHANGED
MIXED
INSUFFICIENT_DATA
```

---

## Tests

Add:

```text
tests/unit/lab/test_balance_comparison_engine.py
```

Required tests:

```text
[ ] variant with better health score is marked improved
[ ] variant with hard law violation is marked regressed
[ ] mixed metrics produce MIXED
[ ] missing data produces INSUFFICIENT_DATA
[ ] comparison includes evidence
[ ] comparison does not claim root cause
```

---

# Milestone 89 — Mutation Lab Orchestrator

## Goal

Run the full mutation experiment.

Component:

```text
MutationLabOrchestrator
```

---

## Flow

```text
1. Load base WorldSpec
2. Load base ScenarioSpec
3. Load MutationSpec
4. Validate all
5. Generate variant matrix
6. Validate each variant
7. Compile each variant
8. Run ExperimentSpec for each variant
9. Collect Observatory results
10. Run metamorphic validation
11. Run balance comparison
12. Write mutation lab summary
```

---

## Execution mode

Start with:

```text
sequential variant execution
```

Parallel execution later.

---

## Mutation lab layout

```text
data/mutation_labs/
  mutation_lab_001/
    mutation_lab_manifest.json
    mutation.yaml
    variants/
      base/
        world.yaml
        scenario.yaml
        lab_run/
      resource_density_high/
        world.yaml
        scenario.yaml
        lab_run/
    analysis/
      metamorphic_results.json
      balance_comparison.json
      mutation_lab_report.md
```

---

## Tests

Add:

```text
tests/integration/lab/test_mutation_lab_orchestrator.py
```

Required tests:

```text
[ ] valid mutation lab runs base + one variant
[ ] invalid mutation stops before execution
[ ] invalid variant is reported, not hidden
[ ] each variant has its own lab run
[ ] mutation lab summary is written
[ ] failed variant does not corrupt base result
```

Anti-misdirection tests:

```text
[ ] orchestrator does not compare variants with different unrelated scenario IDs
[ ] orchestrator does not mark success when all variants failed
```

---

# Milestone 90 — Mutation Lab Reports and CLI

## Goal

Make mutation experiments usable.

---

## CLI commands

```text
rpg-lab mutation validate <mutation_id>
rpg-lab mutation preview <mutation_id>
rpg-lab mutation run <mutation_id> --experiment <experiment_id>
rpg-lab mutation report <mutation_lab_id>
rpg-lab mutation compare <mutation_lab_id>
```

---

## Report sections

```text
1. Executive Summary
2. Base World / Scenario
3. Mutation Matrix
4. Variant Results
5. Metamorphic Validation
6. Balance Comparison
7. Regressions
8. Improvements
9. Insufficient Data
10. Recommended Follow-up Experiments
11. Storage and Runtime Cost
```

---

## Tests

Add:

```text
tests/cli/test_mutation_lab_cli.py
tests/integration/lab/test_mutation_lab_report.py
```

Required tests:

```text
[ ] mutation validate command works
[ ] mutation preview shows variants without running
[ ] mutation run creates mutation lab
[ ] mutation report returns report path
[ ] report includes base and variant results
[ ] report includes insufficient data section
```

---

# Milestone 91 — Phase 13 Safety and Test Strategy

## Goal

Prevent the Mutation Lab from producing misleading balance claims.

This is the most important milestone.

---

# Required anti-misdirection rules

## 1. Never compare invalid variants

```text
invalid world
invalid scenario
failed compile
failed run
```

must not be treated as normal balance regression.

They are:

```text
INVALID_VARIANT
```

---

## 2. Missing metric is not pass

If a metamorphic rule needs:

```text
resource_production_rate
```

but that metric is missing, result must be:

```text
INSUFFICIENT_DATA
```

not pass.

---

## 3. Designed failure is not engine failure

Some mutations intentionally worsen behavior.

Example:

```text
remove all shops
```

Expected result:

```text
shop failures increase
```

That may mean the Observatory works, not that the engine is broken.

---

## 4. Small sample size must be marked weak

If a variant has only one seed, do not claim strong balance conclusion.

Use:

```text
WEAK_EVIDENCE
```

---

## 5. Performance cost must be visible

Every mutation lab should report:

```text
runtime
artifact size
event count
analysis time
```

---

# Required tests

Add:

```text
tests/integration/lab/test_mutation_lab_safety.py
```

Required tests:

```text
[ ] invalid variant is excluded from balance comparison
[ ] missing metric produces INSUFFICIENT_DATA
[ ] designed failure is classified as expected degradation
[ ] one-seed comparison is marked WEAK_EVIDENCE
[ ] artifact size is included in report
[ ] huge mutation matrix is blocked by budget guardrail
```

---

# Phase 13 end-to-end flow

At the end of Phase 13:

```text
1. User defines base world.
2. User defines scenario intent.
3. User defines experiment.
4. User defines mutation matrix.
5. Mutation engine creates variants.
6. Each variant is validated.
7. Each variant is compiled.
8. Each variant is run through Scenario Lab.
9. Observatory records artifacts.
10. Analysis runs per variant.
11. Metamorphic rules compare expected relationships.
12. Balance engine compares variant outcomes.
13. Report identifies improvements, regressions, weak evidence, and missing data.
```

---

# Minimal Phase 13 deliverables

```text
MutationSpec schema
MutationEngine
VariantMatrixBuilder
MetamorphicRuleEngine
BalanceComparisonEngine
MutationLabOrchestrator
Mutation report
Mutation CLI
Safety tests
```

Minimum sample mutations:

```text
resource_density_matrix
inventory_capacity_matrix
shop_liquidity_matrix
combat_damage_matrix
pathing_bottleneck_matrix
```

---

# What Phase 13 should not do

```text
auto-tune balance
generate worlds with AI
search huge parameter space
optimize stats automatically
run distributed experiments
make product-level visual UI
```

Those belong later.

---

# Final acceptance criteria

```text
[ ] MutationSpec exists.
[ ] Mutation engine safely applies changes.
[ ] Base specs are never mutated in place.
[ ] Variant matrix is generated deterministically.
[ ] Variant count is budget-limited.
[ ] Metamorphic rules work.
[ ] Balance comparison works.
[ ] Mutation lab orchestrator runs base + variants.
[ ] Reports show improvement/regression/insufficient data.
[ ] Missing metrics do not pass silently.
[ ] Invalid variants are excluded from balance claims.
[ ] Small samples are marked weak.
```

# My recommendation

Phase 13 should be named:

```text
Mutation and Balance Lab
```

Its purpose:

```text
controlled changes
+ repeated experiments
+ observability analysis
+ balance comparison
+ metamorphic validation
```

This is where the system becomes truly powerful for debugging and balancing, because you are no longer only asking:

```text
What happened in this world?
```

You are asking:

```text
What changes make the world better, worse, unstable, or suspicious?
```
