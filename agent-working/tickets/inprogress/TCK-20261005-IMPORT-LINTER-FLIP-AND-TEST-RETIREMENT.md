---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT
phase: open
date: 2026-10-05
tags: [architecture, delivery]
---

# TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT

## Title
Make the import-linter step blocking and required, then retire the class E tests whose contract is required

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Follow-up to `TCK-20261004-IMPORT-LINTER-ADOPTION`. BLOCKED until a two-week soak from that batch's merge has passed (import-linter adoption merged 2026-10-05 as PR #351, squash `e9585eb02` at 2026-10-05T13:40:06Z; soak ends 2026-10-19T13:40Z; earliest flip 2026-10-19, after the gates-flip PR #329 merges on or after 2026-10-18). Then the advisory step becomes blocking, the owner makes it a required check, and the class E tests whose contract is required are retired. Testing condition 1 (#322): a class E test is retired only in or after the PR that makes its replacement contract a required check.

## Scope
- Soak review (runs, broken-contract runs, false positives, stale `ignore_imports` alerts) in a soak review doc, as for the gates flip
- Step becomes blocking; the owner adds the check as required on `main` (never before `main` has produced the check name; ruleset change and merge in one sitting)
- Retire the class E tests whose contract is required, with the per-test parity table re-shown; the phase19 hot-path test waits on rpg's decision about `kernel.py`'s function-local imports
- Update the testing handoff and the roadmap
- The Import contracts step summary (`codebase.structure.import_contracts`) lists each broken contract's module pairs (importer -> imported, line), not only the contract count; found by the soak review, section 3

## Out of Scope
- Any file under `src/`
- The 42 rules that stay tests
- Edits to the `or True` assert at `tests/unit/observability/test_decision_trace.py:376` (testing's)

## Acceptance Criteria
- [ ] Soak review finalized; no false-positive class open
- [ ] Owner's yes to the required check recorded (date, who)
- [ ] Each retired test's replacement contract is required in the same or an earlier PR; parity table re-shown
- [ ] `git diff --stat` lists no path under `src/`
- [ ] A run with 2+ broken pairs in one contract shows every pair in the job summary and annotations (test pins it)

## Related Tickets
- TCK-20261004-IMPORT-LINTER-ADOPTION
- TCK-20261004-IMPORT-LINTER-EVALUATION

## Related Docs
- docs/plans/codebase_health/import_linter_adoption_ticket_brief.md
- docs/plans/codebase_health/import_linter_evaluation.md
- docs/plans/codebase_health/import_linter_soak_review.md

## Related Stored Artifacts
None.

## Related Code Areas
- tests/architecture/
- codebase/structure/
- pyproject.toml

## Assumptions / Open Questions
- Testing's agreement and four conditions (#322 comment, 2026-10-04; copied from `TCK-20261004-IMPORT-LINTER-ADOPTION`, where they are recorded). They govern this ticket:
  1. a class E test is retired only in or after the PR that makes its replacement contract a required check;
  2. parity is shown per retired test (the injected violation, and the contract failing on it);
  3. phase19 `test_hot_path_does_not_import_heavy_analyzers` is an expectation change, not a retirement: the engine/observability owner first decides whether `kernel.py`'s function-local imports at 149/304/305/316/1241 are allowed (allowlist with a reason) or violations (an engine ticket);
  4. the blind spots and the stale allowlist are covered by contracts. The `or True` assert (`tests/unit/observability/test_decision_trace.py:376`) is testing's, not one of the eight.
- phase19 waits on rpg (`handoff_to_rpg.md`)
- Soak dates are unknown until the adoption batch merges

## Implementation Notes
Soak review drafted 2026-10-08, interim

## Test Summary
### Step 3: class E retirements, parity proof (2026-10-15, head `8ec5a369f`, scratch copy)
Made in a scratch copy (`git archive HEAD src tests codebase visual_assets pyproject.toml registries`), one injection at a time appended to one file, the file restored after each; this checkout was not touched. Test run as `PYTHONPATH=<scratch> python -m pytest <node id> -o addopts=` from the scratch root; contract run as `lint-imports --config codebase/structure/importlinter.toml --contract <id>`. A test counts as "caught" only if it fails on an assertion (not an import error). Baseline on the clean copy: all 7 tests PASS, all 7 contracts KEPT.

Result: 37 injections, the contract went BROKEN on all 37 and named the pair; no row has the test failing while the contract stays KEPT, so none of the 7 is blocked. The test missed 9 of them (TYPE_CHECKING imports for rule 1 and belief, `from src.core import state` into belief/fame/fidelity, plain `import src.engine.governor` / `from src.engine import governor` into admission_control). One row (rule 6, `top: from src.engine.phase_governor import PhaseGovernor`) made the test error on something other than an assertion; it is not counted as caught, and the contract caught it.

Retired (node id -> replacement contract): `tests/architecture/test_phase18_import_boundaries.py::test_entity_models_do_not_import_domain_services` -> c01_core_not_domains; `tests/architecture/test_belief_institution_write_paths.py::test_belief_institution_module_no_engine_or_core_state_imports` -> c08_belief_model_pure; `tests/architecture/test_fame_legend_fact_distinctness.py::test_fame_deriver_and_model_no_engine_or_core_state_imports` -> c08_fame_model_pure; `tests/architecture/test_fidelity_write_paths.py::test_fidelity_deriver_and_model_no_engine_or_core_state_imports` -> c08_fidelity_model_pure; `tests/api/test_admission_control.py::test_admission_control_does_not_reach_into_governor_internals` -> c09_admission_governor; `tests/unit/domains/campaigns/test_campaign_state.py::test_campaign_state_module_has_no_engine_imports` -> c13_campaign_state; `tests/visual_assets/test_boundaries.py::test_src_never_imports_visual_assets` -> c15_src_no_visual_assets. Dead helpers and constants left by them were removed with them (`_is_type_checking_test`, `_collect_type_checking_node_ids`, three `_FORBIDDEN_TOP_LEVEL_IMPORT_PREFIXES`, `_FAME_DERIVER_AND_MODEL_FILES`, unused imports). The c01 contract name no longer cites the retired test.

Not retired: `tests/visual_assets/test_boundaries.py::test_visual_assets_module_respects_the_boundaries` (8a; encodes about 10 more rules than c14), the phase19 `test_hot_path_does_not_import_heavy_analyzers` (waits on testing's pick on #547), the 42 rules that stay tests.

After retirement: the 7 touched test files plus `tests/codebase/test_import_contracts.py`: 221 passed; `make lint-imports`: 17 kept, 0 broken; `ruff check --select F` on the touched files: clean.

| kind | rule | contract | injected (into one file) | existing test | contract | pair named |
|---|---|---|---|---|---|---|
| baseline | 1 core not domains | c01_core_not_domains | (clean copy) | PASS (missed) | KEPT (missed) |  |
| baseline | 3 belief model/deriver | c08_belief_model_pure | (clean copy) | PASS (missed) | KEPT (missed) |  |
| baseline | 4 fame model/deriver | c08_fame_model_pure | (clean copy) | PASS (missed) | KEPT (missed) |  |
| baseline | 5 fidelity model/deriver | c08_fidelity_model_pure | (clean copy) | PASS (missed) | KEPT (missed) |  |
| baseline | 6 admission control | c09_admission_governor | (clean copy) | PASS (missed) | KEPT (missed) |  |
| baseline | 7 campaign state | c13_campaign_state | (clean copy) | PASS (missed) | KEPT (missed) |  |
| baseline | 8b src must not import visual_assets | c15_src_no_visual_assets | (clean copy) | PASS (missed) | KEPT (missed) |  |
| inject | 1 core not domains | c01_core_not_domains | top: import src.domains.campaigns.state | **FAIL** (caught) | BROKEN (caught) | src.core is not allowed to import src.domains:; -   src.core.builder -> src.domains.campaigns.state (l.955) |
| inject | 1 core not domains | c01_core_not_domains | local: import src.domains.campaigns.state | **FAIL** (caught) | BROKEN (caught) | src.core is not allowed to import src.domains:; -   src.core.builder -> src.domains.campaigns.state (l.957) |
| inject | 1 core not domains | c01_core_not_domains | tc: import src.domains.campaigns.state | PASS (missed) | BROKEN (caught) | src.core is not allowed to import src.domains:; -   src.core.builder -> src.domains.campaigns.state (l.958) |
| inject | 1 core not domains | c01_core_not_domains | top: from src.domains.campaigns import state as _s | **FAIL** (caught) | BROKEN (caught) | src.core is not allowed to import src.domains:; -   src.core.builder -> src.domains.campaigns.state (l.955) |
| inject | 3 belief model/deriver | c08_belief_model_pure | top: import src.engine.cadence | **FAIL** (caught) | BROKEN (caught) | src.domains.belief_institution.model is not allowed to import src.engine:; -   src.domains.belief_institution.model -> src.engine.cadence (l.114) |
| inject | 3 belief model/deriver | c08_belief_model_pure | local: import src.engine.cadence | **FAIL** (caught) | BROKEN (caught) | src.domains.belief_institution.model is not allowed to import src.engine:; -   src.domains.belief_institution.model -> src.engine.cadence (l.116) |
| inject | 3 belief model/deriver | c08_belief_model_pure | tc: import src.engine.cadence | PASS (missed) | BROKEN (caught) | src.domains.belief_institution.model is not allowed to import src.engine:; -   src.domains.belief_institution.model -> src.engine.cadence (l.117) |
| inject | 3 belief model/deriver | c08_belief_model_pure | top: from src.core import state as _s | PASS (missed) | BROKEN (caught) | src.domains.belief_institution.model is not allowed to import src.core.state:; -   src.domains.belief_institution.model -> src.core.state (l.114) |
| inject | 4 fame model/deriver | c08_fame_model_pure | top: import src.engine.cadence | **FAIL** (caught) | BROKEN (caught) | src.domains.fame.model is not allowed to import src.engine:; -   src.domains.fame.model -> src.engine.cadence (l.79) |
| inject | 4 fame model/deriver | c08_fame_model_pure | local: import src.engine.cadence | **FAIL** (caught) | BROKEN (caught) | src.domains.fame.model is not allowed to import src.engine:; -   src.domains.fame.model -> src.engine.cadence (l.81) |
| inject | 4 fame model/deriver | c08_fame_model_pure | tc: import src.engine.cadence | **FAIL** (caught) | BROKEN (caught) | src.domains.fame.model is not allowed to import src.engine:; -   src.domains.fame.model -> src.engine.cadence (l.82) |
| inject | 4 fame model/deriver | c08_fame_model_pure | top: from src.core import state as _s | PASS (missed) | BROKEN (caught) | src.domains.fame.model is not allowed to import src.core.state:; -   src.domains.fame.model -> src.core.state (l.79) |
| inject | 5 fidelity model/deriver | c08_fidelity_model_pure | top: import src.engine.cadence | **FAIL** (caught) | BROKEN (caught) | src.domains.fidelity.model is not allowed to import src.engine:; -   src.domains.fidelity.model -> src.engine.cadence (l.78) |
| inject | 5 fidelity model/deriver | c08_fidelity_model_pure | local: import src.engine.cadence | **FAIL** (caught) | BROKEN (caught) | src.domains.fidelity.model is not allowed to import src.engine:; -   src.domains.fidelity.model -> src.engine.cadence (l.80) |
| inject | 5 fidelity model/deriver | c08_fidelity_model_pure | tc: import src.engine.cadence | **FAIL** (caught) | BROKEN (caught) | src.domains.fidelity.model is not allowed to import src.engine:; -   src.domains.fidelity.model -> src.engine.cadence (l.81) |
| inject | 5 fidelity model/deriver | c08_fidelity_model_pure | top: from src.core import state as _s | PASS (missed) | BROKEN (caught) | src.domains.fidelity.model is not allowed to import src.core.state:; -   src.domains.fidelity.model -> src.core.state (l.78) |
| inject | 6 admission control | c09_admission_governor | top: from src.engine.governor import GovernorPolicy | **FAIL** (caught) | BROKEN (caught) | src.api.admission_control is not allowed to import src.engine.governor:; -   src.api.admission_control -> src.engine.governor (l.267) |
| inject | 6 admission control | c09_admission_governor | local: from src.engine.governor import GovernorPolicy | **FAIL** (caught) | BROKEN (caught) | src.api.admission_control is not allowed to import src.engine.governor:; -   src.api.admission_control -> src.engine.governor (l.269) |
| inject | 6 admission control | c09_admission_governor | tc: from src.engine.governor import GovernorPolicy | **FAIL** (caught) | BROKEN (caught) | src.api.admission_control is not allowed to import src.engine.governor:; -   src.api.admission_control -> src.engine.governor (l.270) |
| inject | 6 admission control | c09_admission_governor | top: import src.engine.governor | PASS (missed) | BROKEN (caught) | src.api.admission_control is not allowed to import src.engine.governor:; -   src.api.admission_control -> src.engine.governor (l.267) |
| inject | 6 admission control | c09_admission_governor | local: import src.engine.governor | PASS (missed) | BROKEN (caught) | src.api.admission_control is not allowed to import src.engine.governor:; -   src.api.admission_control -> src.engine.governor (l.269) |
| inject | 6 admission control | c09_admission_governor | tc: import src.engine.governor | PASS (missed) | BROKEN (caught) | src.api.admission_control is not allowed to import src.engine.governor:; -   src.api.admission_control -> src.engine.governor (l.270) |
| inject | 6 admission control | c09_admission_governor | top: from src.engine import governor as _g | PASS (missed) | BROKEN (caught) | src.api.admission_control is not allowed to import src.engine.governor:; -   src.api.admission_control -> src.engine.governor (l.267) |
| inject | 6 admission control | c09_admission_governor | top: from src.engine.phase_governor import PhaseGovernor | **ERROR** (not an assertion: check) | BROKEN (caught) | src.api.admission_control is not allowed to import src.engine.phase_governor:; -   src.api.admission_control -> src.engine.phase_governor (l.267) |
| inject | 6 admission control | c09_admission_governor | local: from src.engine.phase_governor import PhaseGovernor | **FAIL** (caught) | BROKEN (caught) | src.api.admission_control is not allowed to import src.engine.phase_governor:; -   src.api.admission_control -> src.engine.phase_governor (l.269) |
| inject | 6 admission control | c09_admission_governor | tc: from src.engine.phase_governor import PhaseGovernor | **FAIL** (caught) | BROKEN (caught) | src.api.admission_control is not allowed to import src.engine.phase_governor:; -   src.api.admission_control -> src.engine.phase_governor (l.270) |
| inject | 7 campaign state | c13_campaign_state | top: import src.engine.cadence | **FAIL** (caught) | BROKEN (caught) | src.domains.campaigns.state is not allowed to import src.engine:; -   src.domains.campaigns.state -> src.engine.cadence (l.538) |
| inject | 7 campaign state | c13_campaign_state | local: import src.engine.cadence | **FAIL** (caught) | BROKEN (caught) | src.domains.campaigns.state is not allowed to import src.engine:; -   src.domains.campaigns.state -> src.engine.cadence (l.540) |
| inject | 7 campaign state | c13_campaign_state | tc: import src.engine.cadence | **FAIL** (caught) | BROKEN (caught) | src.domains.campaigns.state is not allowed to import src.engine:; -   src.domains.campaigns.state -> src.engine.cadence (l.541) |
| inject | 7 campaign state | c13_campaign_state | top: import src.systems.economy_systems.market | **FAIL** (caught) | BROKEN (caught) | src.domains.campaigns.state is not allowed to import src.systems:; -   src.domains.campaigns.state -> src.systems.economy_systems.market (l.538) |
| inject | 7 campaign state | c13_campaign_state | local: import src.systems.economy_systems.market | **FAIL** (caught) | BROKEN (caught) | src.domains.campaigns.state is not allowed to import src.systems:; -   src.domains.campaigns.state -> src.systems.economy_systems.market (l.540) |
| inject | 7 campaign state | c13_campaign_state | tc: import src.systems.economy_systems.market | **FAIL** (caught) | BROKEN (caught) | src.domains.campaigns.state is not allowed to import src.systems:; -   src.domains.campaigns.state -> src.systems.economy_systems.market (l.541) |
| inject | 7 campaign state | c13_campaign_state | top: from src.engine import cadence as _c | **FAIL** (caught) | BROKEN (caught) | src.domains.campaigns.state is not allowed to import src.engine:; -   src.domains.campaigns.state -> src.engine.cadence (l.538) |
| inject | 8b src must not import visual_assets | c15_src_no_visual_assets | top: import visual_assets.store.contracts | **FAIL** (caught) | BROKEN (caught) | src is not allowed to import visual_assets:; -   src.core.builder -> visual_assets.store.contracts (l.955) |
| inject | 8b src must not import visual_assets | c15_src_no_visual_assets | local: import visual_assets.store.contracts | **FAIL** (caught) | BROKEN (caught) | src is not allowed to import visual_assets:; -   src.core.builder -> visual_assets.store.contracts (l.957) |
| inject | 8b src must not import visual_assets | c15_src_no_visual_assets | tc: import visual_assets.store.contracts | **FAIL** (caught) | BROKEN (caught) | src is not allowed to import visual_assets:; -   src.core.builder -> visual_assets.store.contracts (l.958) |
| inject | 8b src must not import visual_assets | c15_src_no_visual_assets | top: from visual_assets.store import contracts as _c | **FAIL** (caught) | BROKEN (caught) | src is not allowed to import visual_assets:; -   src.core.builder -> visual_assets.store.contracts (l.955) |


## Files Changed

## Completion Summary
