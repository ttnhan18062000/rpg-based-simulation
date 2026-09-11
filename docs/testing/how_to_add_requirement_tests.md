---
status: active
layer: testing
authority: P1
audience: agent
last_verified: 2026-06-13
---

# How to Add a Requirement Test

**Related docs:**
- `docs/testing/test_taxonomy.md` — marker definitions and enforcement rules
- `docs/testing/requirement_traceability.md` — the map to update after adding a test
- `docs/testing/regression_policy.md` — which groups are hard gates; authority rules for P0 tests
- `docs/parity_ledger/` — parity evidence entries (update if test proves a P0 law)
- `docs/mechanics/` — Mechanics Bible chapters (authoritative source for laws being tested)

---

## 1. Behavior Test vs Requirement Test

These two test types serve different purposes and must not be conflated.

| | Behavior Test | Requirement Test |
|---|---|---|
| **Question it answers** | "Does this function/system work correctly?" | "Is this simulation law protected?" |
| **Failure meaning** | "The implementation is broken" | "A protected law has been violated — stop and investigate" |
| **Written when** | Implementing a feature | Documenting that a specific invariant must never regress |
| **Example** | `test_harvest_system_returns_item_on_success` | `test_node_not_depleted_on_full_inventory` |
| **Annotation style** | Function docstring describing expected output | `# REQ:` block citing the specific law; assertion comments citing invariant |
| **Taxonomy marker** | `v2_contract`, `legacy_characterization`, `differential` | `v2_contract` or `regression` + law citation in docstring |

A requirement test is specifically a test that would catch a violation of a named simulation law. Its failure is not a signal to update the test — it is a signal to investigate the code. See `docs/testing/regression_policy.md` §4.

---

## 2. Standard Pattern

Every requirement test follows this four-part structure:

```python
# REQ: <Law name or ID>
# Authority: <P0|P1>
# Mechanics Bible: <chapter reference>
# Parity ledger: <subsystem yaml> entry <ID>
# Proof type: <v2_contract|differential|regression>
def test_<law_name>_<condition>(<fixtures>):
    """
    Law: <One-sentence statement of the invariant being protected>.
    
    Condition: <What specific scenario triggers this test>.
    """
    # ── Setup ──────────────────────────────────────────────────────────────
    # Build minimal state that exercises the condition.
    # Use V2EntityBuilder or replace() for state composition.

    # ── Exercise ───────────────────────────────────────────────────────────
    # Call the authoritative path (resolver, pipeline, or apply).
    # Do NOT call worker or decision code directly.

    # ── Assert: law not violated ───────────────────────────────────────────
    # Assert the invariant holds. Comment each assertion with the law it checks.
    assert <invariant>  # Law: <name> — <brief explanation>

    # ── Assert: correct mutation occurred ─────────────────────────────────
    # Assert the expected side effect (or absence of side effect) is present.
    assert <side_effect>  # Expected: <brief explanation>
```

### Rules

1. The `# REQ:` block must appear immediately before the `def` line.
2. The docstring must state the law in one sentence. Use the exact wording from the Mechanics Bible or parity ledger where possible.
3. Assertions must each have an inline comment starting with `# Law:` or `# Expected:`.
4. Setup must use the authoritative path — `AuthoritativeApplyPipeline.refine()` + `ApplyPath.apply_generation()`, not direct mutation of state.
5. The test must be deterministic: no `random`, no live I/O, no time-dependent behavior.

---

## 3. Naming Convention

Test names must be readable as a traceability key. Follow this pattern:

```
test_<law_noun>_<condition>
```

Where:
- `<law_noun>` identifies the law: `node_not_depleted`, `source_not_mutated`, `combat_requires_adjacency`, `seed_produces_identical_hash`
- `<condition>` identifies the specific scenario: `on_full_inventory`, `when_target_is_dead`, `across_ten_runs`

Examples:
```python
def test_node_not_depleted_on_full_inventory(...)
def test_combat_requires_adjacency_for_melee(...)
def test_seed_produces_identical_hash_across_ten_runs(...)
def test_quest_status_not_set_by_worker(...)
```

Avoid generic names like `test_resource_system` or `test_works`. The name is used as a lookup key in `docs/testing/requirement_traceability.md` and must survive a `grep -r` search.

---

## 4. Taxonomy Marker

Apply the correct marker from `docs/testing/test_taxonomy.md`:

| Situation | Marker |
|---|---|
| Test proves a new engine invariant with no legacy equivalent | `@pytest.mark.v2_contract` |
| Test proves current behavior matches legacy bit-for-bit | `@pytest.mark.differential` |
| Test documents legacy behavior as ground truth | `@pytest.mark.legacy_characterization` |
| Test prevents recurrence of a specific bug | `@pytest.mark.regression` |
| Test documents an intentional departure from legacy | `@pytest.mark.intentional_divergence(id="<LEDGER-ID>")` |
| Test is a high-level smoke run over full ticks | `@pytest.mark.certification` |

Most new requirement tests will use `@pytest.mark.v2_contract`. Use `@pytest.mark.regression` when the test was written specifically to prevent a bug from recurring — include a comment linking to the ticket.

For tests in `tests/parity/`, a marker is **mandatory** — collection-time enforcement will reject the test without one.

```python
import pytest

@pytest.mark.v2_contract
def test_node_not_depleted_on_full_inventory(entity_full_inventory):
    ...
```

---

## 5. After Adding a Test — Update the Traceability Map

After writing and verifying the test, update `docs/testing/requirement_traceability.md`:

1. Find the row for the requirement group the test belongs to (e.g., "Resource Conservation").
2. Add the new test file path to the "Test File(s)" column if it is not already listed.
3. Confirm the "Markers" column reflects the marker you applied.
4. If you created a new requirement group that does not yet exist in the table, add a new row. A row requires at least one verified test file path.

This update must happen in the same commit or session as the test. Do not defer it.

---

## 6. Verifying the Parity Ledger for P0 Laws

If the test protects a **P0** requirement (authority column in the traceability map), you must also update the parity ledger:

1. Find the subsystem YAML in `docs/parity_ledger/`:
   - Resource conservation → `town_resource.yaml`
   - Combat legality → `combat_movement.yaml`
   - World determinism → `substrate.yaml`
   - Progression → `progression.yaml`
   - Kernel/mutation pipeline → `infrastructure.yaml`

2. Find (or create) the entry for the specific law being tested.

3. Set or confirm:
   - `status: verified`
   - `v2_evidence: <path to your new test file>`
   - `test_path: <path>::<test_function_name>`
   - `priority: P0`
   - `evidence_kind: invocation` (optional, descriptive-only field — you ran this test and confirmed it passes; no enforcement rule reads it yet)

4. If no entry exists for the law, add one. The schema is in `docs/parity_ledger/schema.json`.

A P0 test without a corresponding parity ledger entry is incomplete. The definition of done for a P0 requirement test requires both.

Note: a P0 entry only requires a non-null `test_path` when `status` is `verified`/`divergent`/`legacy_verified`. A P0 entry with `status: missing`/`unsupported` requires a non-empty `support_boundary` instead — not relevant to this worked flow (which always ends in `verified`), but see `tools/parity_ledger_writer.py::validate_entry` if you are downgrading an existing P0 entry rather than adding a new passing test.

---

## 7. Worked Example: Atomic Conservation Law (Resource Transfer)

**Law:** No source resource (node, ground item, corpse) may be mutated unless the destination entity successfully receives the transfer. (Mechanics Bible: `docs/mechanics/03_economic_laws.md` — Atomic Conservation)

**Parity ledger:** `docs/parity_ledger/town_resource.yaml`

**Model file:** `tests/integration/pipeline/test_transaction_completion.py`

### Step 1 — Write the `# REQ:` block and test function

```python
import pytest
from dataclasses import replace
from src.core.state import (
    AuthoritativeState, ResourceNodeState, InventoryComponent, ItemStack
)
from src.core.updates import StateUpdate, EntityUpdate, ResourceTransferIntent
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder

# REQ: Atomic Conservation — resource transfer is source-safe
# Authority: P0
# Mechanics Bible: docs/mechanics/03_economic_laws.md
# Parity ledger: docs/parity_ledger/town_resource.yaml entry ECON-ATOMIC-001
# Proof type: v2_contract

@pytest.mark.v2_contract
def test_node_not_depleted_when_item_transfer_fails(base_state):
    """
    Law: Node charges must not decrease if the harvested item cannot be
    added to the entity's inventory (inventory full).

    Condition: Entity has a full inventory; harvest intent is submitted.
    """
    # ── Setup ──────────────────────────────────────────────────────────────
    entity = (
        V2EntityBuilder(1)
        .kind("HERO")
        .location(0, 0)
        .inventory(gold=0, items=[ItemStack("iron_ore", 5)], max_slots=1)
        .build()
    )
    node = ResourceNodeState(
        id=101, kind="IRON_NODE", position=(1, 0),
        yields_item="iron_ore", remaining_charges=5, max_charges=5,
        required_ticks=1
    )
    state = replace(base_state, entities={1: entity}, resource_nodes={101: node})

    # ── Exercise ───────────────────────────────────────────────────────────
    update = StateUpdate(entity_updates={
        1: EntityUpdate(
            entity_id=1,
            resource_transfers=[ResourceTransferIntent(
                source_id=101, source_kind="NODE",
                items_add=[ItemStack("iron_ore", 1)],
                transfer_kind="HARVEST"
            )]
        )
    })
    refined = AuthoritativeApplyPipeline.refine(state, update)
    final_state = ApplyPath.apply_generation(state, refined)

    # ── Assert: law not violated ───────────────────────────────────────────
    assert final_state.resource_nodes[101].remaining_charges == 5  # Law: Atomic Conservation — node not depleted on failed transfer

    # ── Assert: correct mutation occurred ─────────────────────────────────
    # No new item was added (inventory was full, harvest failed)
    original_items = {i.item_id for i in state.entities[1].inventory.items}
    final_items = {i.item_id for i in final_state.entities[1].inventory.items}
    assert original_items == final_items  # Expected: inventory unchanged on failed harvest
```

### Step 2 — Determine the file location

This test belongs in `tests/integration/pipeline/test_transaction_completion.py` — it is an integration-level pipeline test of atomic conservation. Do not create a new file for a single law variant; add it to the existing owning file.

### Step 3 — Run the test

```bash
pytest tests/integration/pipeline/test_transaction_completion.py -v
```

Confirm it passes. If it fails, fix the test setup, not the production code.

### Step 4 — Update the traceability map

In `docs/testing/requirement_traceability.md`, confirm the "Resource Conservation" row includes `tests/integration/pipeline/test_transaction_completion.py`. The test function name is searchable via grep.

### Step 5 — Update the parity ledger

In `docs/parity_ledger/town_resource.yaml`, find or add the entry for atomic conservation. Set `status: verified`, `test_path: tests/integration/pipeline/test_transaction_completion.py::TestSourceMutationConservation::test_node_not_depleted_on_full_inventory` (or your new function name).

### Step 6 — Commit

Reference the ticket in the commit message:

```
TCK-YYYYMMDD-SHORT-SCOPE: Add requirement test for atomic conservation on harvest failure

Co-Authored-By: ...
```

---

## 8. Quick Reference

```
1. Write test with # REQ: block + docstring citing the law
2. Apply @pytest.mark.<taxonomy_marker>
3. Name the test test_<law_noun>_<condition>
4. Run pytest on the owning file to confirm it passes
5. Update docs/testing/requirement_traceability.md
6. If P0: update docs/parity_ledger/<subsystem>.yaml
7. Commit with ticket ID reference
```
