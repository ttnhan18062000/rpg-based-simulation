---
status: archive
authority: P2
audience: historical
layer: testing
original_date: unknown
---

## 1. Split tests by execution cost and dependency level

Right now, fast logic tests and slow process/integration tests are mixed. For example, the uploaded test base includes normal engine tests, subprocess API tests using `python3 -m src serve`, WebSocket tests, certification harness tests, and release-gate tests in the same broad run surface. 

Use this structure:

```text
tests/
  unit/
    core/
    builder/
    services/
    systems/

  integration/
    engine/
    pipeline/
    combat/
    resource/
    town/
    social/
    strategy/
    world/

  api/
    rest/
    websocket/

  cli/
    command_contracts/

  certification/
    gate/
    harness/
    scenarios/

  regression/
    legacy_parity/
    bug_repro/

  helpers/
    entities.py
    resources.py
    presets.py
    assertions.py
    runtime.py
    domain.py
```

Then configure markers:

```text
unit
integration
api
cli
certification
slow
longrun
legacy
```

This lets you run:

```bash
pytest tests/unit
pytest tests/integration/resource
pytest -m "not slow and not certification"
pytest -m certification
```

Without this separation, every full run becomes noise.

---

## 2. Stop letting every test build its own world

A lot of your tests manually create:

```text
AuthoritativeState
EntityState
BuildingState
ResourceNodeState
InventoryComponent
StrategicComponent
```

That creates inconsistent setups. Some tests provide `building_tiles` but forget `state.buildings`. Some use strings instead of `ItemStack`. Some construct `EntityState(position=...)` directly, which no longer matches the model. These patterns are visible in the uploaded auto-updated test file. 

Rule:

```text
Tests should describe scenario intent, not internal construction details.
```

Bad:

```python
state = AuthoritativeState(
    tick=1,
    seed=42,
    entities={1: actor},
    town_tiles={pos},
    building_tiles={pos: "shop"},
)
```

Better:

```python
state = make_town_state(
    actor,
    building=make_shop(pos=pos, gold=1000),
)
```

This prevents invalid partial state.

---

## 3. Use scenario helpers, not direct builder calls everywhere

Raw builder calls should be rare outside builder tests.

Use:

```python
hero = make_hero(...)
monster = make_monster(...)
state = make_resource_state(...)
shop = make_shop(...)
```

Instead of repeating:

```python
V2EntityBuilder(...).kind(...).location(...).identity(...).inventory(...).combat(...).build()
```

Reason: tests should survive internal builder refactors. Your current pain is proof that direct builder usage everywhere is fragile.

---

## 4. Create domain-specific fixtures

Use fixtures for repeated valid worlds.

Example fixture categories:

```text
combat_world
resource_world
town_world
social_world
strategic_world
empty_world
two_actor_world
shop_world
blacksmith_world
```

Example style:

```python
@pytest.fixture
def shop_world():
    hero = make_hero(1, pos=(5, 5), gold=100, items=[stack("wood", 2)])
    shop = make_shop(10, pos=(5, 5), gold=1000)
    state = make_town_state(hero, building=shop)
    return state, hero, shop
```

Then tests focus only on law/assertion.

---

## 5. Separate “law tests” from “behavior scenario tests”

You are mixing low-level laws and end-to-end scenarios.

Example law test:

```text
selling 2 wood produces gold_delta = 10 and removes exactly 2 wood
```

Example scenario test:

```text
hero enters town, auto-sells junk, crafts sword, rests at inn, then leaves
```

Do not put both styles in the same test module.

Suggested naming:

```text
test_shop_laws.py
test_blacksmith_laws.py
test_town_scenarios.py
test_town_regression.py
```

---

## 6. Use assertion helpers aggressively

Right now tests repeat extraction logic:

```python
e_upd = refined.entity_updates[e_id]
assert e_upd.inventory.gold_delta == ...
actual_removed = sorted(...)
```

Use:

```python
e_upd = entity_update(refined, hero.id)
assert_inventory_delta(
    e_upd,
    gold_delta=10,
    removed=["wood", "wood"],
)
```

This reduces duplication and prevents each test from inventing slightly different inventory comparison behavior.

---

## 7. Make process/API tests environment-safe

The uploaded tests still use hardcoded:

```python
cmd = ["python3", "-m", "src", ...]
port = 8002
time.sleep(3)
```

That is fragile, especially on Windows, CI, or parallel runs. 

Use helpers:

```python
run_src_module(...)
run_src_server(...)
get_free_port()
wait_for_http(...)
```

Rules:

```text
Never hardcode python3.
Never hardcode ports unless the test owns the port.
Never use fixed sleep as readiness.
Always terminate subprocesses safely.
```

---

## 8. Mark release-gate tests separately

This test should not run in normal pytest:

```text
test_real_release_proof_is_valid
```

It requires pre-generated release artifacts. That is not a normal unit/integration test. It belongs under:

```text
tests/certification/gate/test_release_gate.py
```

and should be marked:

```python
@pytest.mark.release
@pytest.mark.certification
```

Default test run should exclude it:

```ini
addopts = -m "not release"
```

Otherwise developers get false failures because `reports/release_proof` is missing.

---

## 9. Stop mixing legacy names into new tests

Some tests still reference old concepts like:

```text
LEG-RPG-150
RPG-0034
RPG-1654
```

That is fine for traceability, but the implementation should not encode legacy construction style.

Better format:

```python
"""
Covers:
- RPG-RES-034: shop sell price enforcement
- LEG-RPG-150: belief decay parity
"""
```

Then use new V2 helper setup.

---

## 10. Add a test migration guard

Add a guard test that fails when old builder methods remain in tests.

Example rule:

```text
No .position(
No .at(
No .gold(
No .item(
No .items(
No .with_base_stats(
No .with_class(
No .monster(
No .strategic_project(
No .strategic_contract(
No EntityState(... position=...)
```

Put it in:

```text
tests/integrity/test_no_legacy_builder_api.py
```

This prevents old style from creeping back.

---

## 11. Add one builder contract test suite

Since you now have a fresh builder, protect it.

Create:

```text
tests/unit/core/test_v2_entity_builder_contract.py
```

Cover:

```text
location writes navigation.position
inventory preserves ItemStack quantity
identity writes recipes/class/personality/life_stage
combat writes hp/max_hp/range/readiness
strategic writes projects/hypotheses/current IDs
cognition writes profile but not runtime hypotheses
replace_inventory preserves exact component object
```

This catches builder regressions early.

---

## 12. Avoid giant test modules

Your uploaded combined file is massive and includes many domains. That is bad for debugging. A failure in a 1,000+ line file slows diagnosis.

Target module size:

```text
100–250 lines for normal unit/integration tests
300–500 lines max for domain scenario suites
```

Split by domain law.

