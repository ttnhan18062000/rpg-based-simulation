---
status: archive
authority: P2
audience: historical
layer: testing
original_date: unknown
---

# Test Suite Investigation & Fixing Plan

Generated: 2026-05-28  
Scope: Full project test suite — `tests/`, `tests_legacy/`, `scratch/`, `reviews/`

---

## Executive Summary

| Category | Count | Status |
|---|---|---|
| **Active tests collected** (`tests/`) | ~2,332 | ✅ Collectable |
| **Active tests passing** (`tests/`) | ~2,285 | ✅ |
| **Active tests failing** (`tests/`) | **~47** | ❌ Need Fix |
| **Active collection errors** (`tests/`) | **4** | ❌ Need Fix |
| **Legacy tests collected** (`tests_legacy/`) | 1,002 | ⚠️ Partially broken |
| **Legacy collection errors** (`tests_legacy/`) | 276 | ⚠️ Stale — see note |
| **Scratch tests** (`scratch/`) | ~5 | ⚠️ Not production |
| `reviews/test_export.py` | 1 file | ❌ Syntax error (artifact) |

---

## Category A — Collection Errors (Blocking) — 4 errors in `tests/`

These 4 errors prevent pytest from even collecting tests. They must be fixed first.

### A1. `reviews/test_export.py` — SyntaxError: misplaced `from __future__`

**Error:**
```
SyntaxError: from __future__ imports must occur at the beginning of the file (line 120)
```
**Root cause:** `reviews/test_export.py` is a 63,201-line concatenated dump of test files used
as a review artifact. It contains multiple `from __future__ import annotations` statements mid-file
(at lines 120, 360, 514, 1572, …). Python requires these at the very top of a module.

**Impact:** pytest aborts collection when attempting to import this file.

**Fix:** Add `reviews/` to the `norecursedirs` list in `pyproject.toml`. This directory is a review
artifact, not a real test directory.

```toml
# pyproject.toml — [tool.pytest.ini_options]
norecursedirs = ["reviews", "scratch", "stored_artifacts", "tests_legacy", ".venv", ".git"]
```

---

### A2. `tests/integration/kernel/test_milestone_d_closure.py` — Module import mismatch (pycache)

**Error:**
```
import file mismatch:
imported module 'test_milestone_d_closure' has this __file__ attribute:
  stored_artifacts/D145C3D0-MILESTONE-D-TASK4/test_milestone_d_closure.py
```
**Root cause:** `stored_artifacts/D145C3D0-MILESTONE-D-TASK4/` contains a copy of this test file
**without an `__init__.py`**, causing Python to register it as the canonical module of the same
flat module name `test_milestone_d_closure`. Subsequent attempts to import the real file from
`tests/integration/kernel/` fail with an identity mismatch.

**Fix (two-step):**
1. Delete stale `__pycache__` in `stored_artifacts/` directories:
   ```bash
   find stored_artifacts/ -name "__pycache__" -type d -exec rm -rf {} +
   ```
2. Add `__init__.py` to `tests/integration/kernel/` so pytest uses package-qualified imports:
   ```bash
   touch tests/integration/kernel/__init__.py
   ```

---

### A3. `tests/unit/kernel/test_worker_harden.py` — Module import mismatch (pycache)

**Error:**
```
imported module 'test_worker_harden' has this __file__ attribute:
  stored_artifacts/D145C3D0-MILESTONE-D-TASK2/test_worker_harden.py
```
**Root cause:** Same as A2. `stored_artifacts/D145C3D0-MILESTONE-D-TASK2/` has a copy of
`test_worker_harden.py` with pycache entries polluting the flat module namespace.

**Fix:** Same as A2:
```bash
find stored_artifacts/ -name "__pycache__" -type d -exec rm -rf {} +
touch tests/unit/kernel/__init__.py
```

---

### A4. `tests/unit/strategic/test_social_contracts.py` — Duplicate module name

**Error:**
```
imported module 'test_social_contracts' has this __file__ attribute:
  tests/unit/social/test_social_contracts.py
```
**Root cause:** Two files share the exact same basename `test_social_contracts.py`:
- `tests/unit/social/test_social_contracts.py` (older, May 19, 2149 bytes)
- `tests/unit/strategic/test_social_contracts.py` (newer, May 27, 3191 bytes)

Both exist in directories without `__init__.py`, so they compete for the same flat module name.
The `tests/unit/social/` version wins the import race, breaking the strategic version.

**Fix:**
1. Ensure **all `tests/unit/` subdirectories** have `__init__.py` files:
   ```bash
   find tests/ -type d ! -exec test -f {}/__init__.py \; -exec touch {}/__init__.py \;
   ```
2. Alternatively, rename the strategic file to `test_strategic_social_contracts.py` to avoid collision.

---

## Category B — Logic/Assertion Failures — ~47 failures across active `tests/`

### B1. Interaction Reset Not Propagated — 10 failures

**Affected tests:**
- `tests/unit/core/test_interaction_recovery.py::test_weight_pressure_enforcement`
- `tests/unit/core/test_interaction_recovery.py::test_channeled_looting_one_shot`
- `tests/unit/resource/test_resource_contract.py::test_law_of_capacity_enforcement`
- `tests/unit/resource/test_resource_contract.py::test_law_of_weight_enforcement`
- `tests/unit/resource/test_resource_contract.py::test_law_of_availability_node_depleted`
- `tests/unit/resource/test_resource_v2_boundary.py::test_chest_looting_and_cooldown`
- `tests/unit/world/test_interaction_system.py::test_interaction_channeling_success`
- `tests/unit/world/test_interaction_system.py::test_interaction_inventory_pressure`
- `tests/unit/core/test_migration_proof.py::test_ground_item_pickup_parity`
- `tests/unit/core/test_migration_proof.py::test_corpse_looting_parity`

**Symptom:**
```python
assert ent_upd.interaction.reset == True  # actual: False
assert ent_upd.inventory is not None       # actual: None
```

**Root cause:** `src/engine/interaction.py` — `InteractionSystem.enforce()` has a logic gap in
the completion path. When `new_progress >= required_ticks` but `intents` are not appended (because
the condition `len(intents) > len(ent_upd.resource_transfers)` is False), the function falls through
to the final `pass` with **no reset or inventory update issued**. The inventory update comes from
downstream `ResourceTransferSystem` applying the intent, but the intent is never attached when the
guard condition fails.

Specifically at `src/engine/interaction.py` around line 137:
```python
if intents and len(intents) > len(ent_upd.resource_transfers):
    refined_entity_updates[e_id] = replace(
        ent_upd,
        resource_transfers=intents,
        interaction=InteractionUpdate(reset=True)  # ← only reached if guard passes
    )
    continue
else:
    pass  # ← nothing happens — reset never emitted
```

**Fix:** When `new_progress >= required_ticks` and `intents` is non-empty but already matches
`ent_upd.resource_transfers`, still emit the `InteractionUpdate(reset=True)` to signal completion:
```python
if intents:
    if len(intents) > len(ent_upd.resource_transfers):
        refined_entity_updates[e_id] = replace(
            ent_upd,
            resource_transfers=intents,
            interaction=InteractionUpdate(reset=True)
        )
    else:
        # intents already present — still emit reset signal
        refined_entity_updates[e_id] = replace(
            ent_upd,
            interaction=InteractionUpdate(reset=True)
        )
    continue
```

---

### B2. `self_model` Unauthorized Field in `EntityState` — 1 failure

**Affected test:**
- `tests/unit/core/test_entity_integrity.py::test_entity_field_integrity`

**Symptom:**
```
AssertionError: Unauthorized fields detected in EntityState: {'self_model'}
```

**Root cause:** Phase 6 added `self_model: SelfModelBundle` to `EntityState` (line 590 of
`src/core/state.py`) but the integrity test's allowed-fields whitelist was never updated.

**Fix (two options):**
1. **(Preferred)** Add `"self_model"` to the allowed set in the test:
   ```python
   extra_fields = entity_fields - REQUIRED_BASE_FIELDS - aspects - {
       "_readonly_cache", "_spatial_grid_cache", "_canonical_cache", "timeline",
       "self_model"  # Phase 6: SelfModelBundle (cognition aspect bundle)
   }
   ```
2. **(Alternative)** If `self_model` is a full aspect, add it to the `aspects` set in the test
   alongside `stamina`, `combat`, etc.

---

### B3. Quest System — `REWARDED`/`REWARD_PENDING` Status Not Set — 6 failures

**Affected tests:**
- `tests/unit/quest/test_quest_lifecycle.py::test_quest_completion_and_reward_emission`
- `tests/unit/quest/test_quest_lifecycle.py::test_no_double_completion`
- `tests/unit/quest/test_quest_system.py::test_bounty_quest_completion`
- `tests/unit/quest/test_quest_transactions.py::test_successful_quest_reward_transaction`
- `tests/unit/quest/test_quest_transactions.py::test_full_inventory_blocks_quest_reward`
- `tests/unit/quest/test_quest_transactions.py::test_recovery_after_freeing_inventory`

**Symptom:**
```python
assert quest_upd.status_set == QuestStatus.REWARDED   # actual: None
assert quest_upd.status_set == QuestStatus.REWARD_PENDING  # actual: None
```

**Root cause:** The quest engine marks `QuestStatus.COMPLETED` but does not advance to
`REWARDED` or `REWARD_PENDING`. The test expects the reward transaction phase to run as part
of the same pipeline tick. Either:
- (a) The reward-phase code was not wired into the pipeline, or
- (b) The reward phase is conditional on inventory-space check that is now using the new
  `InteractionUpdate` mechanism broken in B1.

**Investigation needed:** Check `src/engine/pipeline_phases/` for a quest reward phase and
confirm it is registered in `src/engine/apply.py`.

**Fix:** Wire quest reward resolution into the engine pipeline, or ensure the quest system's
`complete_quest()` method properly transitions `COMPLETED → REWARDED` when inventory is available.

---

### B4. `GuildIntelSystem` — Certainty Level Downgraded — 1 failure

**Affected test:**
- `tests/unit/world/test_guild_intel.py::test_guild_intel_emission`

**Symptom:**
```python
assert lead.certainty == LeadCertainty.APPROXIMATE  # actual: VAGUE
```

**Root cause:** The test sets `trauma_score=10.0` on a region and expects the guild intel system
to emit a lead at `APPROXIMATE` certainty. The system emits `VAGUE` instead, suggesting the
certainty-mapping threshold was changed (e.g., `trauma_score` threshold for `APPROXIMATE` was
raised from `10.0` to something > 10.0).

**Fix:** Check `src/systems/world/guild_intel.py` — find the certainty mapping logic and either:
- Restore the old threshold (if it was a regression), or
- Update the test threshold to match the current spec.

---

### B5. Anchored World Persistence — Missing Entity Update — 1 failure

**Affected test:**
- `tests/unit/world/test_anchored_world.py::test_anchored_world_persistence_pipeline_integration`

**Symptom:**
```python
ent_upd = refined.entity_updates[1]  # KeyError: 1
```

**Root cause:** The pipeline does not produce an `EntityUpdate` for entity `1` when expected.
Likely connected to the interaction reset gap (B1) or the pipeline phase ordering.

**Fix:** Investigate `src/systems/world/anchored_world.py` — confirm it generates entity updates
when entities interact with anchored world nodes. Likely shares root cause with B1.

---

### B6. Resource V2 Boundary — Town Tax Refactor & Chest Looting — 2 failures

**Affected tests:**
- `tests/unit/resource/test_resource_v2_boundary.py::test_town_tax_refactor`
- `tests/unit/resource/test_resource_v2_boundary.py::test_chest_looting_and_cooldown`

**Symptoms:**
```python
assert ent_upd is not None     # actual: None  (town tax refactor)
assert 10 in refined.chest_updates  # actual: {}  (chest cooldown)
```

**Root cause:**
- Town tax: The pipeline doesn't produce an entity update for entity being taxed — likely the
  tax system was refactored or the triggering condition changed.
- Chest cooldown: The `chest_updates` dict is empty after looting — trace back to B1 (interaction
  reset not emitted, so chest_update is never added to `StateUpdate`).

**Fix:**
- Chest cooldown: Fix B1 first — the chest cooldown code in `interaction.py` at lines 134-144
  only fires when `should_reset = True` or intents are generated. Once B1 is fixed, chest updates
  should propagate.
- Town tax: Investigate `src/systems/resource/` for the town tax system and confirm it emits
  `EntityUpdate` for the taxed entity.

---

### B7. Social Phase 7 — Contract Expiration Heroism Delta — 1 failure

**Affected test:**
- `tests/unit/social/test_social_phase7.py::test_contract_expiration_resolves_and_dissolves`

**Symptom:**
```python
assert l_upd.social.heroism_delta == 0.05  # actual: 0.1
```

**Root cause:** Contract expiration for entity 1 (leader) generates `heroism_delta=0.1` instead
of `0.05`. The `process_active_contracts()` call in `contracts.py` (line 288) calls
`resolve_contract_outcome(success=True)` which sets `heroism_delta=0.05`. However, since both the
leader AND member share contract `c1`, the delta gets applied twice — once when processing
entity 1's contracts, and again when processing entity 2's contracts and it merges social updates.
The accumulated `base_social.heroism_delta + my_social_up.heroism_delta = 0.05 + 0.05 = 0.1`.

**Fix:** Ensure each contract is only processed once per tick (deduplicate by contract ID), or
restrict `process_active_contracts` to only act on the contract source (not both participants).

---

### B8. Inventory Serialization — `collections.deque` Not JSON-serializable — 1 failure

**Affected test:**
- `tests/unit/resource/test_inventory_serialization.py::test_entity_serialization_roundtrip`

**Symptom:**
```
TypeError: Type <class 'collections.deque'> not serializable
```

**Root cause:** The `EntityState.to_canonical_dict()` method (or one of its nested calls) emits a
`collections.deque` object that the test's JSON serializer cannot handle. Phase 6/7 likely
introduced a deque in the `SelfModelBundle` or timeline-related field.

**Fix (two options):**
1. Convert all deques to lists in `to_canonical_dict()`:
   ```python
   # In SelfModelBundle.to_canonical_dict() or EntityState.to_canonical_dict()
   "timeline": list(self.timeline)
   ```
2. Update the test's `set_default` handler to serialize deques:
   ```python
   def set_default(obj):
       if isinstance(obj, (set, deque)):
           return list(obj)
       raise TypeError(...)
   ```

---

### B9. RNG Hygiene — Global `random` Import in Worldbuilding — 1 failure

**Affected test:**
- `tests/unit/platform/test_rng_hygiene.py::test_rng_hygiene_no_global_random_in_src`

**Symptom:**
```
AssertionError: Forbidden global random import found in:
  src/worldbuilding/recipe.py, src/worldbuilding/compiler.py
```

**Root cause:** The worldbuilding module uses Python's built-in `random` module directly.
Project policy requires `src.platform.rng.DeterministicRNG` everywhere in `src/`.

**Fix:**
```python
# In src/worldbuilding/recipe.py and src/worldbuilding/compiler.py
# Replace:
import random
# With:
from src.platform.rng import DeterministicRNG
# And use DeterministicRNG(seed) instance instead of random.choice, random.random, etc.
```

---

### B10. Live Anomaly Worker — Processed Count Zero — Flaky — 1 failure

**Affected test:**
- `tests/unit/observability/test_live_anomaly_worker.py::test_worker_lifecycle_in_process`

**Symptom:**
```python
assert worker.processed_count == 1  # actual: 0
```

**Note:** This test passes when run in isolation but fails in the full suite. It's a timing/
ordering flaky test. The worker's `processed_count` stays 0 because the async queue doesn't flush
before the assertion.

**Fix:** Add a small sleep or event-based sync in the test before asserting `processed_count`:
```python
import time
time.sleep(0.1)  # Give the worker thread time to process
assert worker.processed_count == 1
```
Or use `worker.drain()` / `worker.join()` if such methods exist.

---

### B11. Non-Blocking IO — Run Manager Chunks Empty — 1 failure

**Affected test:**
- `tests/unit/core/test_non_blocking_io.py::test_on_tick_end_is_non_blocking_on_io`

**Symptom:**
```python
assert len(rm._manifest["chunks"]) == 1  # actual: 0
```

**Note:** This also passes in isolation. Likely a test-ordering side-effect where a previous test
exhausts or resets the `RunManager` instance shared across the suite.

**Fix:** Ensure the test creates a fresh `RunManager` instance with a unique run ID. Verify that
`RunManager` doesn't rely on module-level state or singletons that bleed between tests.

---

## Category C — Collection Errors in `tests_legacy/` — 276 errors (informational)

`tests_legacy/` has **276 collection errors** out of 1,002 collected tests. These are **expected**
for a legacy codebase being ported to V2. Key error categories:

| Error | Count (approx.) | Root cause |
|---|---|---|
| `ImportError: cannot import name 'SimulationConfig'` | ~30 | `src_legacy.config` API changed |
| `ImportError: cannot import name 'Faction'` from `src_legacy.core.enums` | ~15 | Enum renamed |
| `ImportError: cannot import name 'ItemDefinition'/'ItemRegistry'` | ~20 | Items API removed |
| `ImportError: cannot import name 'QuestState'` | ~10 | Quest API renamed |
| `ImportError: cannot import name 'ReasonCode'` | ~10 | Enum removed |
| `ImportError: cannot import name 'LifecycleSystem'` | ~10 | System restructured |
| `ModuleNotFoundError: No module named 'httpx'` | ~30 | Missing test dependency |
| `ModuleNotFoundError: No module named 'src.systems.social'` | ~20 | Module moved/renamed |
| `AttributeError: 'EntityRole' has no attribute 'MONSTER'` | ~5 | Enum value removed |
| `FileNotFoundError: tests/parity/town_oracle/results.json` | ~3 | Missing fixture file |

**Recommendation:** These are **not regressions** — they reflect that the `src_legacy` module
has been progressively superseded. Do NOT attempt to fix all 276. Instead:
1. Add `tests_legacy/` to `norecursedirs` in `pyproject.toml` so it's excluded from the default run.
2. Run `tests_legacy/` separately with `pytest tests_legacy/` only when testing legacy parity.

---

## Category D — Non-Test Directories Collected by pytest

### D1. `scratch/` — 5 informal tests, 1 failure

`scratch/test_getattr.py::test` fails because it uses an outdated `EntityState` constructor
signature (`position=` kwarg removed). These are developer scratch files, not production tests.

**Fix:** Add `scratch/` to `norecursedirs` in `pyproject.toml`.

### D2. `reviews/test_export.py` — Concatenated artifact

Already covered in A1. Add `reviews/` to `norecursedirs`.

---

## Fix Priority Order

| Priority | Category | Action |
|---|---|---|
| 🔴 P0 | A2, A3 | Delete `stored_artifacts/` pycache, add `__init__.py` to kernel test dirs |
| 🔴 P0 | A4 | Add `__init__.py` to all `tests/unit/` subdirs OR rename duplicate file |
| 🔴 P0 | A1, D1, D2 | Add `reviews/`, `scratch/`, `tests_legacy/` to `norecursedirs` |
| 🔴 P1 | B1 | Fix `InteractionSystem.enforce()` reset logic gap (unblocks B5, B6) |
| 🔴 P1 | B3 | Wire quest reward phase into pipeline |
| 🟠 P2 | B2 | Add `self_model` to entity integrity test whitelist |
| 🟠 P2 | B7 | Deduplicate contract expiration processing |
| 🟠 P2 | B9 | Replace global `random` in worldbuilding with `DeterministicRNG` |
| 🟡 P3 | B4 | Investigate guild intel certainty threshold regression |
| 🟡 P3 | B8 | Fix deque serialization in `to_canonical_dict()` |
| 🟡 P3 | B10, B11 | Fix flaky async tests (timing / singleton state leak) |

---

## Recommended `pyproject.toml` Changes

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
norecursedirs = [
    "reviews",
    "scratch",
    "stored_artifacts",
    ".venv",
    ".git",
    "node_modules",
    "__pycache__",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "world_long_run: long-run living-world stability tests",
    "legacy_characterization: proves legacy behavior in src",
    "v2_contract: defines a new V2-specific contract",
    "differential: parity test comparing src and src_legacy",
    "intentional_divergence: asserts a documented behavioral difference",
    "regression: targets a specific bug identified during porting",
    "certification: engine integrity proof for milestone gates",
    "perf: performance measurement tests",
    "integration: integration tests across multiple components",
    "e2e: end-to-end simulation scenario tests",
    "strategic_loop: strategic loop mechanics tests",
]
```

## One-Liner Fix Commands (P0 — can be run immediately)

```bash
# 1. Clear stored_artifacts pycache pollution
find stored_artifacts/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true

# 2. Add __init__.py to kernel test directories
touch tests/integration/kernel/__init__.py
touch tests/unit/kernel/__init__.py
touch tests/unit/strategic/__init__.py

# 3. Add __init__.py to all tests/ subdirs (safe operation)
find tests/ -type d -exec touch {}/__init__.py \;

# 4. Verify collection is now clean (should be 0 errors, ~2332 tests)
pytest --ignore=tests_legacy --collect-only -q 2>&1 | tail -5
```
