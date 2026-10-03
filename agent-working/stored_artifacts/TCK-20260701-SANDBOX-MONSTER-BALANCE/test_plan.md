---
ticket_id: TCK-20260701-SANDBOX-MONSTER-BALANCE
phase: test_plan
date: 2026-07-02
---

# Test Plan — TCK-20260701-SANDBOX-MONSTER-BALANCE (ATTEMPT 3 — recompile + verify, UNBLOCKED)

> **Status update:** The prior version of this file described a plan that could not be executed
> because `resolve sandbox_world` failed outright. That blocker (`TCK-20260701-HAZARD-KIND-
> RESOLVER-GAP`) is now fixed and re-verified — see `investigation.md`. This file is rewritten
> to describe the test surface actually exercised (this pass) and what remains for the
> implementation pass.

## Regression Surface

1. **`tests/integration/worldassembly/test_real_content_world_modules.py`** — the suite whose
   failure originally proved the blocker. Re-run this pass: **6/6 passed** (was 5/5 ERROR).
   Includes `test_hazard_kind_survives_module_pipeline`, the pipeline-level regression test
   added by the hotfix ticket specifically for this class of gap.
2. **`sandbox_world` resolve/compile pipeline** — exercised directly via the real CLI
   (`python3 -m src.worldbuilding.cli resolve sandbox_world` then
   `compile sandbox_world --seed {42,137} --from-resolved`). Both seeds compile cleanly, zero
   validation errors, deterministic hashes reproduced on repeat runs.
3. **Empirical behavioral check (not a pytest test, a direct Kernel run)** — 200 ticks against
   the real compiled state for seed 42 and seed 137, inspecting the 5 `wild_beast_pack`
   entities' (`14-18`) `lifecycle.active`/`death_tick` and `hazard_drain_applied` event
   incidence directly. This is the test that actually answers the ticket's core acceptance
   criterion ("monsters no longer die as an entire cohort... from hazard_drain_applied
   self-kill") — no existing pytest test asserts this end-to-end behavioral outcome, and
   authoring one would require a full Kernel-driven fixture at a scope beyond a unit test
   (consistent with how attempt 2's regression test was event-log/kernel-driven, not a pure
   unit assertion).
4. **Faction/environment unit coverage** (pre-existing, from `HAZARD-NATIVE-IMMUNITY`, re-run
   as a sanity check, not modified by this ticket): `tests/unit/world/test_regional_
   consequences.py`, `tests/unit/content_semantics/test_semantics.py::test_get_hazard_
   immunities`, `tests/unit/content/test_catalog.py::test_faction_definition_hazard_
   immunities_field` / `test_faction_catalog_loads_with_hazard_immunities_authored`. These
   assert the mechanism's unit-level correctness in isolation; this ticket's job is the
   integration-level proof (content actually loads + engine actually applies it to
   `sandbox_world`), not re-deriving those unit tests.

## What Remains for the Implementation Pass
- No new `src/` code and no new unit tests are needed — the mechanism itself is correct and
  already covered (see item 4). This ticket's remaining work is content/data/doc:
  - Finalize the `sandbox_world` recompile as the committed artifact (this pass already
    performed it; implementation should confirm the same command sequence one more time as the
    "official" run and leave `resolved/`, `world_compile_report.json` in that state).
  - Regenerate the 4 `sandbox_world_*` calibration anchors as one coordinated action (per
    `investigation.md` note: `seed42_200t` was already incidentally refreshed by this pass's
    verification; the other 3 were already dirty from the prior migration ticket and need a
    fresh, coordinated regeneration together).
  - `docs/audits/D20_simq_integration.md` P2 row → resolved, with the actual outcome (0/5
    deaths at 200 ticks, both seeds, vs. the original 5/5 dead by tick 8).
  - One-line update to `docs/guidelines/intentional_divergences.md` entry 2.20's stale note
    (currently says `sandbox_world` "remain[s] stale... until recompiled by
    TCK-20260701-SANDBOX-MONSTER-BALANCE" — needs to reflect that the recompile has happened).
- **Full regression pass before closing**: re-run `tests/integration/worldassembly/` (44),
  `tests/unit/worldbuilding/` (92), `tests/unit/worldassembly/` (48) — same scope the hotfix
  ticket used — to confirm the recompiled artifacts don't regress anything beyond
  `sandbox_world` itself. Not re-run in this Investigate pass (out of scope for re-verification;
  the hotfix ticket already ran this exact suite clean); should be re-run once as part of
  Implement/Finalize.

## Non-Goals (reaffirmed, unchanged from prior scope)
- Not testing `ENABLE_COMBAT_ENGAGEMENT=ON` general combat attrition — out of this ticket's
  scope (general combat balance, not the self-hazard-kill mechanism).
- Not testing any world other than `sandbox_world`.
- Not testing `goblin_camp_conflict` (the other `hazard_kind`-authored module) beyond what
  `test_real_content_world_modules.py` already covers generically — no ticket currently compiles
  a world using it standalone; flagged only as a known related-blast-radius note in the hotfix
  ticket, not this ticket's job to chase down.
