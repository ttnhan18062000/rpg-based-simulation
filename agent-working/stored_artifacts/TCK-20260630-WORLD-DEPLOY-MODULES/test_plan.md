---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260630-WORLD-DEPLOY-MODULES
artifact_type: test_plan
tags: [world, modules, compositions, compile, testing]
---

# Test Plan

## Ticket
TCK-20260630-WORLD-DEPLOY-MODULES — Deploy 7 unused world modules into compiled worlds

---

## Test Scope

### In Scope
- Compilation of 4 worlds (3 stubs + 1 new composition)
- All 7 unused modules appear in at least one compiled world
- No ERROR-severity issues in any compile report
- 200-tick calibration runs complete without crash
- Integration test suite for worldassembly passes

### Out of Scope
- Engine behavior with new modules (covered by calibration)
- Performance regression testing (separate ticket)

---

## Test Cases

### TC-01: frontier_extended resolves and compiles without errors
- **Given**: `data/worlds/frontier_extended/world.yaml` exists with `worldcomposition.v1`
- **When**: `resolve frontier_extended` then `compile frontier_extended --from-resolved`
- **Then**: `data/worlds/frontier_extended/world_compile_report.json` exists with no errors, entity_count > 0

### TC-02: frontier_living_world resolves and compiles (with added modules)
- **Given**: `frontier_living_world` composition has `nomadic_herd`, `settled_quarter`, `survivor_camp_shelter` added
- **When**: resolve + compile
- **Then**: compile report exists with no errors

### TC-03: swamp_border_world resolves and compiles without errors
- **Given**: `data/worlds/swamp_border_world/world.yaml` with `sunken_swamp_border`
- **When**: resolve + compile
- **Then**: compile report exists with no errors

### TC-04: highland_traverse resolves and compiles (new composition)
- **Given**: new composition with `frontier_village_core`, `mountain_pass`, `river_crossing`
- **When**: resolve + compile
- **Then**: compile report exists with no errors

### TC-05: All 7 target modules covered
- **Script**:
```python
import yaml, os
target = {'forest_warden_grove', 'mountain_pass', 'nomadic_herd', 'river_crossing',
          'settled_quarter', 'sunken_swamp_border', 'survivor_camp_shelter'}
covered = set()
for name in os.listdir('data/worlds'):
    wf = f'data/worlds/{name}/world.yaml'
    if not os.path.exists(wf): continue
    with open(wf) as f: d = yaml.safe_load(f)
    for mid in d.get('modules', []): covered.add(mid)
    for ref in d.get('module_refs', []):
        covered.add(ref.get('module_id', ref) if isinstance(ref, dict) else ref)
assert target <= covered, f"Uncovered: {target - covered}"
print("ALL 7 MODULES COVERED")
```

### TC-06: All 20 modules covered
- **Script**: same as TC-05 but for all `data/content/world_modules/*.yaml` module IDs

### TC-07: Integration tests pass
```bash
pytest tests/integration/worldassembly/ -v --timeout=120
```
- All existing tests must pass
- Tests for new compositions in `test_real_content_world_compositions.py` if applicable

### TC-08: 200-tick calibration runs complete (no crash)
- For each new world: `python3 tools/calibrate_simq.py --name <name> --seed 42 --ticks 200`
- Must exit 0 and produce `data/calibration/<name>_seed42_200t/quality_report.json`

---

## Pass Criteria

| Check | Pass Condition |
|---|---|
| frontier_extended compile report | exists, no ERROR entries |
| frontier_living_world compile report | exists, no ERROR entries |
| swamp_border_world compile report | exists, no ERROR entries |
| highland_traverse compile report | exists, no ERROR entries |
| Module coverage check | all 7 target modules in at least one world.yaml |
| Integration tests | all passing |
| Calibration | 4 quality_report.json files written, no crash |
