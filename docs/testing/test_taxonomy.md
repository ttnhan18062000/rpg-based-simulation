---
status: active
layer: testing
authority: P1
audience: developer
---

# Test Taxonomy and Proof Standards

This document answers, for a change or a new test: **which level and harness fit, where the test lives,
what a passing test is evidence of, and how it is reported.** Sections:

| Section | Answers |
|---|---|
| §1–§3 | Legacy-parity markers for `tests/parity/` (`legacy_characterization`, `v2_contract`, `differential`, ...) |
| §4 | Performance test authoring |
| §5 | Test levels: harness, oracle, placement, cadence, report line |
| §6 | Technique criteria (example, property, metamorphic, characterization) |
| §7 | Evidence classes: what a passing test proves |
| §8 | Placement and the classification of non-test trees |
| §9 | The oracle principle |
| §10 | Domain and level marker vocabulary (the single definition) |

Sources: `docs/plans/test_architecture/roadmap.md` §4 (binding) and
`docs/plans/test_architecture/reference/architecture_design_notes.md` §3 (non-binding detail).

To ensure the engine is truthful and deterministic, all tests in the `tests/parity/` suite must adhere to the marker taxonomy in §1.

## 1. Taxonomy Markers

### `legacy_characterization`
- **Purpose**: To document and freeze the current behavior of the legacy `src`.
- **Standard**: These tests should ideally run against the original `src` modules or use frozen output data (Oracles) to define the "Legacy Truth".

### `v2_contract`
- **Purpose**: To define the behavior of engine components where no legacy parity is required (e.g., new engine substrate, improved observability).
- **Standard**: Should focus on idempotency, immutability, and deterministic state transitions.

### `differential`
- **Purpose**: To prove bit-identical or semantic parity between `src` and `src`.
- **Standard**: Must use the same seeds and configurations. These are the strongest proof of parity.

### `intentional_divergence`
- **Purpose**: To explicitly document where current behavior *must* differ from legacy (e.g., fixing a legacy non-deterministic bug).
- **Standard**: Must assert the difference. Requires an `id` argument (e.g., `@pytest.mark.intentional_divergence(id="COMB-001")`) mapping to the Parity Ledger.

### `regression`
- **Purpose**: To prevent the return of bugs identified during the hardening process.
- **Standard**: Must include a comment or link to the original ticket/issue.

### `certification`
- **Purpose**: High-level "Smoke Tests" that verify the engine can complete a full tick/run without crashing or drifting.
- **Standard**: Runs long scenarios with randomized seeds.

### `worldassembly`
- **Purpose**: Tests that own the world module assembly, composition spec loading, region/faction/population merging, provenance manifest generation, and CompileContext serialization.
- **Location**: `tests/unit/worldassembly/`, `tests/integration/worldassembly/`
- **Ownership boundary**: These tests own the behaviors listed below. The strict world matrix suite **must not** duplicate them.

| Owned behavior | Test file |
|---|---|
| Region merge / duplicate collision | `test_assembly.py` |
| WorldSpec structural correctness | `test_assembly.py` |
| Deterministic provenance manifests | `test_provenance.py` |
| CompileContext serialization | `test_resolver.py` |
| Archetype metadata preservation | `test_archetype_preservation.py` |
| Real module catalog loads | `test_real_content_world_modules.py` |
| Real composition load/normalize | `test_real_content_world_compositions.py` |
| Module normalization snapshot | `test_real_module_normalized_snapshot.py` |

**Strict matrix tests** may verify scenario-specific assembly constraints (e.g., per-scenario region counts, population distributions) but must not re-assert basic "assembly produces a valid WorldSpec" or "catalog loads without error."

**Process guard — adding a new content field to a `worldspec.v1` schema (e.g. `RegionSpec`):**
When a field is added to a `worldspec.v1` schema class, it must also be added to the
corresponding `worldcomposition.v1` recipe schema (`src/worldbuilding/recipe.py`) and forwarded
in `WorldAssemblyResolver.resolve_module_contribution()` (`src/worldassembly/resolver.py`) — these
are two separate, easy-to-miss authoring paths. Unit tests that construct schema objects directly
(e.g. `RegionState(...)`, `RegionSpec(...)`) do **not** exercise this gap; only a real
module-loading pipeline test does (module YAML → `WorldModuleAuthoringNormalizer.normalize()` →
`WorldAssemblyResolver.resolve_module_contribution()` → resolved spec, as in
`test_real_content_world_modules.py::test_hazard_kind_survives_module_pipeline`). A ticket that
adds a content field should run `tests/integration/worldassembly/test_real_content_world_modules.py`
(the `MODULE_MATRIX` covers all real `data/content/world_modules/*.yaml` files) as part of its own
test plan, not just its new unit tests. See TCK-20260701-HAZARD-KIND-RESOLVER-GAP for the
incident this guards against.

## 2. Enforcement
All tests in `tests/parity/` are subject to automated collection-time enforcement. A test will NOT run unless it has at least one of these markers.

## 3. How to Mark a Test
```python
import pytest

@pytest.mark.differential
def test_movement_parity():
    ...

@pytest.mark.intentional_divergence(id="SUB-042")
def test_improved_determinism():
    ...
```

---

## 4. Performance Test Authoring

Performance tests live in `tests/perf/` and use the `perf_budget` fixture (defined in `tests/perf/conftest.py`).  The fixture enforces budgets declared in `perf_baselines.json` at the repo root.  See also `docs/engine/performance_contract.md` §3.2 for measurement methodology and hardware class definitions.

### 4.1 Adding a new performance test

1. Write the test function in `tests/perf/`, accepting `perf_budget` as a parameter.
2. **Before running the test**, add a baseline entry to `perf_baselines.json`.  The fixture calls `pytest.fail` (not skip) if no entry exists — this is intentional to force authors to declare a budget up-front.
3. Obtain a starting budget by running:
   ```
   make perf-measure
   ```
   `perf_guard.py` will print a proposed JSON entry.  Copy it into `perf_baselines.json`, fill in `rationale` and `updated_by` (your ticket ID), and commit the baseline alongside the test.

**Minimal test structure:**

```python
import time
import pytest

def test_my_operation_perf(perf_budget):
    rss_before = perf_budget.snapshot_rss()
    t0 = time.perf_counter()

    result = my_expensive_operation()

    elapsed_ms = (time.perf_counter() - t0) * 1000
    rss_delta_kb = perf_budget.snapshot_rss() - rss_before
    perf_budget.assert_within_budget(elapsed_ms, rss_delta_kb)
```

### 4.2 Updating after an intentional performance change

If a code change legitimately increases (or decreases) cost:

1. Land the code change.
2. Run `make perf-measure` — review the proposed diff on stdout.
3. Update the relevant `perf_baselines.json` entries: set `time_ms` / `memory_kb` to the new measured values, update `rationale`, set `updated_by` to your ticket ID, and set `updated_at` to today's date.
4. Commit `perf_baselines.json` in the same commit as the code change.

**Do not** commit a new baseline without a rationale explaining why the budget changed.

### 4.3 Tolerance bands

| `tolerance_pct` | When to use |
|---|---|
| 20 | Deterministic, CPU-bound operations — tight gate |
| 50 | Moderate noise (I/O, allocator variance) |
| 100 | High VM or scheduler noise; wide gate preferred over flaky test |

Use the narrowest band that avoids false positives on Class B hardware (shared VM, `PERF_HARDWARE_CLASS=B`).

### 4.4 Hardware class (`PERF_HARDWARE_CLASS`)

Override the hardware class via environment variable:

```
PERF_HARDWARE_CLASS=A python3 -m pytest tests/perf/
```

| Class | Description |
|---|---|
| A | Dedicated CI / bare-metal |
| B | Shared VM (default) |
| C | Laptop / dev workstation |

In the current pass, hardware class is **informational only** — it is recorded in `perf_baselines.json` entries and printed by `perf_guard.py`, but does not modify the effective tolerance band.  Per-class tolerance multipliers will be added when CI hardware is classified (see `docs/engine/performance_contract.md` §4.2).

---

## 5. Test Levels

Pick the **lowest level that can observe the behaviour being claimed**. Each level names its executed
boundary, harness, oracle, placement and cadence. "Reported as" is the level's line in the core-RPG test
report (`tools/test_architecture/core_rpg_report.py`): a level is reported by its lane execution state
(`pass`, `fail`, `skipped`, `not-in-supplied-runs`, `no-junit-artifact`, ...), never merged with another level.

| Level (`level` value) | Executed boundary | Harness | Oracle | Placement | Cadence | Reported as |
|---|---|---|---|---|---|---|
| Unit / component (`unit`) | a function or domain service on hand-built state | `V2EntityBuilder`, `tests/helpers/*` | exact value or law from the spec | `tests/unit/<component>/` | every PR | lane execution per file |
| Kernel integration (`kernel_integration`) | real `Kernel` + profile + RNG, no world compiler | the `tests/integration/kernel/test_minimal_kernel.py` pattern | state over N ticks | `tests/integration/<area>/` | every PR | lane execution per file |
| Mechanic outcome scenario (`mechanic_scenario`) | compiled world + kernel, one mechanic | scenario helper (`tests/helpers/scenario.py`) | occurrence **and** effect; a control arm only where the claim needs one | `tests/mechanic_scenarios/` | every relevant PR | lane execution; scenario lane |
| Cross-domain scenario (`cross_domain_scenario`) | two or more domains in one run | same scenario helper | effect at each hop | `tests/mechanic_scenarios/` | relevant PR, or nightly (then **not** PR evidence) | lane execution; nightly results reported separately |
| Broad simulation (`broad_simulation`) | long runs, corpus worlds | certification harness, SimQ | invariant monitors; SimQ tolerance bands | slow-marked tests, `simulation_quality` | nightly / on demand | system-health evidence only |

Rules:
- A test states one level. A multi-domain test declares all its domains and one primary.
- A higher level does not replace a lower one: a scenario does not excuse missing unit tests for a formula.
- A scenario claiming an effect must observe the authoritative state delta, not a log line or an event
  count alone.
- Cadence "every relevant PR" is a target; whether CI runs the scenario lane on a given PR is decided by
  the CI rule, not by this document.

## 6. Technique Criteria

Techniques are chosen per behaviour; none is required everywhere.

| Technique | Choose when | Not when |
|---|---|---|
| Example | a documented value | the law must hold over ranges |
| Property | bounds, monotonicity, per-transaction conservation | one documented value is the whole oracle |
| Stateful property | invariants over action sequences | only meaningful in a compiled world |
| Metamorphic | relations between runs | replay reliability is unverified (long-run determinism is parked; only short runs are verified) |
| Characterization | complex output must not drift unnoticed, with explicit re-approval | a simpler exact oracle exists |

## 7. Evidence Classes

What a passing test is evidence **of** — the report keeps these separate and never sums them:

| Class | Meaning |
|---|---|
| Proof of an approved claim | a test whose oracle is an authoritative document (§9) and whose claim is recorded |
| Executed evidence | a test ran and passed with no approved claim attached; it is not proof of correctness |
| Change-detection | characterization tests: the output did not change; never correctness proof |
| System-health | broad simulation and SimQ: invariants and tolerance bands held |
| Architecture evidence | static guards (`architecture` marker): a structural rule holds |

Report states: `pass` · `fail` · `skipped` · `not-run` (layer not run) · `not-in-supplied-runs` · `no-junit-artifact` · `no-coverage-artifact` ·
`drift-classified` · `unstable` · `stale` · `unknown` · `quarantined`. Package coverage is not domain
coverage; domain coverage stays `not-derived` until a defensible mapping exists.

## 8. Placement and Non-Test Trees

- New tests go to the placement column of §5. Do not create a new top-level test directory.
- Domain is declared by marker (§10), not inferred from the directory; directory and import signals are
  only the report's fallback classification.
- `tests/mutation/baselines/` holds **data, not tests**. It is not a level, is never collected, and the
  report does not classify it. Its shape check lives in `tests/unit/tools/`, which has a CI lane.
- `tests/parity/` follows §1–§3.
- Performance tests follow §4.

## 9. The Oracle Principle

**The oracle is a document, not a session.** Expected behaviour comes from the Mechanics Bible
(`docs/mechanics/`) and the Engine Contracts (`docs/engine/`), with the parity ledger
(`docs/parity_ledger/`) recording status.

- Changing an expected behaviour means changing the oracle document **and** its parity-ledger entry in the same
  session; an intentional departure also needs a `docs/guidelines/intentional_divergences.md` entry.
- If the document is silent (for example party/group composition), or two sections disagree, the test does
  not invent an oracle: escalate to the user.
- Investigation notes and roadmap addenda are not oracle sources.
- A test that derives its expected value by running the code under test is characterization (§6), not proof.

## 10. Domain and Level Marker Vocabulary

This section is the **single definition** of the vocabulary. `pyproject.toml` only registers the marker
names; a test (`tests/unit/tools/test_marker_vocabulary.py`) fails if the registered markers and this
section drift. Usage:

```python
import pytest

pytestmark = [pytest.mark.domain("combat"), pytest.mark.level("unit")]
```

A multi-domain test lists several `domain(...)` markers; the first is primary. Markers are **required for new
or modified core-RPG tests** and checked **advisorily** (`tools/test_architecture/marker_check.py`; report only,
never a CI gate). Existing tests are not bulk-marked.

<!-- marker-vocabulary:begin -->
```yaml
markers:
  domain: {description: "gameplay domain the test is about (ownership map)"}
  level: {description: "test level (section 5)"}
domain:
  - substrate
  - movement
  - combat
  - progression
  - economy
  - quests_guild
  - strategic_cognition
  - world_dynamics
  - social_narrative
level:
  - unit
  - kernel_integration
  - mechanic_scenario
  - cross_domain_scenario
  - broad_simulation
```
<!-- marker-vocabulary:end -->

Domain values follow the ownership map (`architecture_design_notes.md` §3.1). Party/group has no oracle
or owner (decision D-P, deferred), so it has no domain value; tests about it stay unclassified.

