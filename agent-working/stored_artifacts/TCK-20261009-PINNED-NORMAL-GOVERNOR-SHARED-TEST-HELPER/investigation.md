---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261009-PINNED-NORMAL-GOVERNOR-SHARED-TEST-HELPER
phase: done
date: 2026-10-09
tags: [testing, determinism]
---

# Investigation

Copies on origin/main (identical bodies: `_get_indicated_mode` returns `RuntimeMode.NORMAL`, `force_mode` returns `None`):
1. `tests/unit/world/test_resource_regrowth_wiring.py:21` (base `ResourceGovernor`, used at line 59, no docstring).
2. `tests/integration/lab/test_species_relations_metamorphic_validation.py:117` (base `governor_module.ResourceGovernor`, installed by `monkeypatch.setattr(governor_module, "ResourceGovernor", ...)` at line 193; the monkeypatch replaces the module attribute, so the shared class must subclass the real class imported at module load, not the patched name).
3. `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py:132` (used at line 258).
4. `tests/mechanic_scenarios/test_entity_death_authority_boundary.py`: only on PR #457's branch (gate 1).

Non-matching overrides (guard negatives): `tests/integration/world/test_camp_raid_targeting.py` (pins DEGRADED), `tests/integration/kernel/test_tick_budget_report_only.py` (records force_mode, calls super()).

`tests/helpers/` has `__init__.py`; no existing kernel helper. `tests/architecture/` holds AST/source guards (pattern to follow).

Open: the optional factory is added only if two call sites can use it without changing what they run; decide after copy 4 lands.
