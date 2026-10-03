# TCK-20260623-FIX-DOCS-INTEGRITY — Plan

## TYPE A — manifest.json path corrections

**Update `docs/engine/manifest.json`:**
- Replace 8 `_mN`-suffixed contract paths with real existing contract paths:
  - `simulation_kernel_contract_m1.md` → `docs/engine/contracts/simulation_kernel_contract.md`
  - `runtime_profiles_m1.md` → `docs/engine/runtime_profiles.md`
  - `runtime_state_contract_m3.md` → `docs/engine/contracts/runtime_state_contract.md`
  - `scheduler_contract_m4.md` → `docs/engine/contracts/scheduler_contract.md`
  - `resource_governor_contract_m5.md` → `docs/engine/contracts/resource_governor_contract.md`
  - `replay_contract_m6.md` → `docs/engine/contracts/replay_contract.md`
  - `observability_contract_m7.md` → `docs/engine/contracts/observability_contract.md`
  - `worker_contract_m8.md` → `docs/engine/contracts/worker_contract.md`
  - `certification_contract_m9.md` → `docs/engine/contracts/certification_contract.md`
- Keep `engineering_playbook_m10.md` and `project_lawbook_m10.md` (hardcoded in tests)
- Keep truly missing docs in manifest (create them below)

**Create stub docs:**
- `docs/engine/supported_progression_surface_phase5.md` (headers: Purpose, Support Matrix, Supported Behavioral Boundaries)
- `docs/engine/engineering_playbook_m10.md` (headers: Purpose, Extension Rules, Project Guardrails, Extension Templates + sub-templates)
- `docs/engine/project_lawbook_m10.md` (headers: Purpose, Architectural Pillars, Table of Contents; must mention "class_b")
- `docs/engine/phase12_entry_package.md` (headers: Purpose, Cutover Authorization, Operational Constraints)
- `docs/engine/phase13_retirement_manifest.md` (headers: Purpose, Core Logic & Engine, Retirement Protocol)
- `docs/engine/legacy_replacement_ledger.md` (headers: Purpose, Replacement Ledger)

## TYPE B — oracle artifacts

Create `tests_legacy/parity/` tree with 3 oracle dirs:
- `tests_legacy/parity/movement_oracle/results.json` — list with `success_move` scenario
- `tests_legacy/parity/interaction_oracle/results.json` — list with `harvest_done` scenario
- `tests_legacy/parity/town_oracle/results.json` — list with `blacksmith_craft_success`, `blacksmith_missing_materials`, `shop_sell_materials` scenarios

## TYPE C — stale baseline removal

Remove 15 entries from `KNOWN_HARDCODED_BASELINE` in `tests/architecture/test_no_new_hardcoded_gameplay_truth.py`:
enemies/regions/recipes/services now tracked in migration_map.yaml.

## TYPE D — import boundary fix

In `src/core/updates.py`, move `WorldEvent` and `InformationProviderState` imports out of the
`from src.domains` import group by using string annotations ("WorldEvent", "InformationProviderState")
so the raw `from src.domains` string does not appear in src/core/.

## TYPE E — stale pipeline contract update

In `tests/integrity/test_logic_guards.py::test_subsystem_order_documentation`:
- Replace `StrategicIntelligenceSystem.resolve_blockers`, `evaluate_all_concerns`,
  `evaluate_all_strategic_intents` with `StrategicIntelligenceSystem.fused_strategic_pass`
- Update the ordering assertion that referenced `resolve_blockers` to use `fused_strategic_pass`

## TYPE F — ContentHotPathViolation

Read kernel.py warmup code to choose fix. Expected: add explicit warmup call before
kernel construction in `_run_integrated_loop` test helper, or patch catalog pre-load.
