---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE

Measured at `origin/main` `9640ff942877cc7264e83309f35d19022a4a3fe6`, 2026-10-03.

- Target `src/systems/social_systems/appraisal.py`: 542 lines, sha256 `d921245aaab745c724f5e1ef1011b8b5ef2eb3f2df1d48b6eb9891e12b78eceb`, last changed in commit `243e798ad`.
- Selection by `mutation_selection.resolve(..., "src.systems.social_systems.appraisal")`: 46 files. One-hop `src/` importers: `src.engine.domain.combat_actions`, `src.engine.domain.core_actions`, `src.engine.pipeline_phases.paid_information`, `src.systems.strategic_systems.intelligence`. Resolved-files hash `41fc8fd64d2e7ed53d04ae56609c21c02443a74ee55f776891417316374ecb00`. No curated additions.
- The selection runs green: 313 passed in about 5 s, so a full mutation run is cheap.
- G3 (determinism): the kernel DOES run in this selection. A read-only probe plugin (kept outside the repo) saw 5 `Kernel.tick_once` calls, in `tests/mechanic_scenarios/test_action_pacing_readiness_gate.py` (2), `tests/mechanic_scenarios/test_combat_judgement_withdrawal.py` (2) and `tests/simulation_quality/test_clan_reputation_witnessed_betrayal.py` (1), all with `audit_mode` False and `max_tick_budget_ms` 100. The scratch run therefore forces `audit_mode=True` and a relaxed tick budget (10,000,000 ms) through that plugin only; the selection is still 313 passed under that forcing. The test files themselves are untouched.
- `tests/unit/social/test_multi_hero.py` (the file the plan expected to run the kernel) is NOT in the resolved selection: it does not import `appraisal`.
- `mutmut` 3.x rejects `src.` module paths (v3's finding), so `mutmut==2.5.1` is used, installed with `pip --target`.

Docs to update: `docs/testing/social_test_report_2026-10-03.md` (section 4), plus the new baseline JSON.
