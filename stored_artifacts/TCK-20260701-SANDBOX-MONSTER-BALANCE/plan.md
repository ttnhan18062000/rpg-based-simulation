---
ticket_id: TCK-20260701-SANDBOX-MONSTER-BALANCE
phase: plan
date: 2026-07-02
---

# Plan — TCK-20260701-SANDBOX-MONSTER-BALANCE (ATTEMPT 3 — recompile + verify, UNBLOCKED)

## Decision: PROCEED — blocker cleared, fix verified end-to-end

The prior attempt-3 pass stopped because `resolve sandbox_world` failed outright
(`RegionRecipeSpec`/`WorldAssemblyResolver` didn't forward `hazard_kind`). That gap is fixed by
`TCK-20260701-HAZARD-KIND-RESOLVER-GAP` (DONE) and this pass independently re-verified it: the
resolve/compile pipeline succeeds cleanly, `hazard_kind: NATURAL_TERRAIN` resolves on `wolf_den`/
`near_forest`, `wild_beast_pack`'s `hazard_immunities` resolves through the real
`FactionSemanticsService` → `EnvironmentService.calculate_hazard_drain` path, and a full 200-tick
empirical run (seed 42 and 137) shows all 5 monster entities surviving with **zero**
`hazard_drain_applied` events against them — see `investigation.md` for full evidence. This is a
straightforward recompile + verify + doc-update plan; no further design decision is required.

## Ordered Steps

| # | Step | Files touched | Status |
|---|---|---|---|
| 1 | Recompile `sandbox_world` (`resolve` then `compile --seed 42 --from-resolved`, and again for `--seed 137` to produce/confirm both calibration seeds) as the finalized artifact | `data/worlds/sandbox_world/resolved/*`, `data/worlds/sandbox_world/world_compile_report.json` | **Already executed this session** (seed 42 canonical state left on disk, hash `836b45e8913b46862240c6ba80f177f6`); re-confirm once more at Finalize before commit |
| 2 | Confirm `wild_beast_pack` resolves `hazard_immunities` incl. `NATURAL_TERRAIN`; `wolf_den`/`near_forest` resolve `hazard_kind: NATURAL_TERRAIN` | (verification only, no files) | **Done** — see investigation.md Steps 3-4 |
| 3 | Empirical 200-tick re-run, seed 42 and seed 137; confirm `wild_beast_pack` entities no longer die from `hazard_drain_applied` self-inflicted damage (other attrition still acceptable per original AC) | `data/runs/*` (temp, cleaned after each run) | **Done** — 0/5 dead, 0 `hazard_drain_applied` events against them, both seeds |
| 4 | Regenerate the 4 `sandbox_world_*` calibration anchors (`sandbox_world_seed42_200t`, `sandbox_world_seed137_200t`, `sandbox_world_seed999_200t`, `sandbox_world_seed42_1000t`) as one coordinated action via `tools/calibrate_simq.py` | `data/calibration/sandbox_world_*/{quality_report.json,quality_scores.jsonl}`, `tests/simulation_quality/fixtures/grade_anchors.json` | Not yet done — `seed42_200t` was incidentally refreshed by this pass's verification run and can be reused/re-confirmed rather than re-run a third time; the other 3 need a fresh run |
| 5 | Run `test_grade_regression.py` (or equivalent grade-anchor regression suite) against the regenerated anchors to confirm they're internally consistent | `tests/simulation_quality/...` (test run only) | Not yet done |
| 6 | Update `docs/audits/D20_simq_integration.md` P2 row to fully resolved, with actual outcome (0/5 monster deaths at 200 ticks, both seeds — stronger than the AC's "some attrition is acceptable" bar; note the `ENABLE_COMBAT_ENGAGEMENT`-off caveat from investigation.md Step 6 so the COMBAT-pillar grade shift isn't misread) | `docs/audits/D20_simq_integration.md` | Not yet done |
| 7 | One-line update to `docs/guidelines/intentional_divergences.md` entry 2.20's stale note (currently states sandbox_world "remain[s] stale... until recompiled by TCK-20260701-SANDBOX-MONSTER-BALANCE") to reflect the recompile having happened | `docs/guidelines/intentional_divergences.md` | Not yet done — this is an edit to an *existing* entry, not a new divergence entry (the divergence itself was already documented by `HAZARD-NATIVE-IMMUNITY`) |
| 8 | Full regression pass: `tests/integration/worldassembly/` (44), `tests/unit/worldbuilding/` (92), `tests/unit/worldassembly/` (48) — same scope the hotfix ticket used, to confirm the finalized recompile doesn't regress anything | test run only | Not yet done |
| 9 | Clean up `data/runs/*` from any Finalize-stage verification runs; confirm no stray files | — | Standard Finalize cleanup |
| 10 | Update ticket status, working log, move ticket to `tickets/done/` | `tickets/inprogress/TCK-20260701-SANDBOX-MONSTER-BALANCE.md` → `tickets/done/`, `tickets/working_log.csv` | Not yet done |

No `src/` changes are needed at any step — the engine-layer mechanism (`EnvironmentService.
calculate_hazard_drain`, `FactionSemanticsService.get_hazard_immunities`) and the resolver
wiring (`RegionRecipeSpec.hazard_kind`, `WorldAssemblyResolver.resolve_module_contribution`)
are both already correct and verified. This remains a content-recompile-and-verify ticket, now
actually able to complete as such.

## Scope Guards (reaffirmed)
- Do **NOT** touch `src/world/environment.py`, `src/worldbuilding/compiler.py`,
  `src/worldbuilding/recipe.py`, or `src/worldassembly/resolver.py` — all four are the hotfix's
  and the sibling ticket's files, already correct and verified working; re-touching them here
  would blur traceability across tickets for no behavioral reason.
- Do **NOT** expand scope to general combat balance (`ENABLE_COMBAT_ENGAGEMENT=ON` behavior) or
  to any world other than `sandbox_world` — both explicitly out of scope per the ticket.
- Do **NOT** re-litigate the `hazard_kind`/`hazard_immunities` mechanism design — it is DONE,
  documented (`intentional_divergences.md` 2.20), and independently re-verified in this pass.

## Acceptance Criteria Mapping (current state, after this pass)
| AC | Status |
|---|---|
| Root cause confirmed: which resolver/catalog path assigns sandbox_world monster stats | Confirmed (catalog stats via `SANDBOX-WORLDCOMP-MIGRATE`; hazard self-kill root-caused and fixed via `HAZARD-NATIVE-IMMUNITY` + `HAZARD-KIND-RESOLVER-GAP`) |
| Monsters no longer die as an entire cohort within the first 10 ticks | **Verified — exceeds bar**: 0/5 dead across a full 200 ticks, both seeds |
| Final state hash changes are expected and documented | Verified: seed 42 hash `836b45e8913b46862240c6ba80f177f6`, seed 137 hash `7e8ae05dbeffccb8edd65fd9754787aa`, both reproducible on repeat compiles — to be recorded in the D20 doc update (step 6) |
| `docs/guidelines/v2_intentional_divergences.md` updated if this counts as a divergence | Already covered by entry 2.20 (prior ticket); this pass's remaining job is the one-line staleness-note update (step 7), not a new entry |
| D20 audit P2 row updated to resolved | Pending — step 6 |
| No regression in existing sandbox_world / world-compile tests | Verified so far (`test_real_content_world_modules.py` 6/6); full regression scope pending — step 8 |

## Unresolved Questions
**No.** The genuine blocker from the prior pass is resolved and independently re-verified through
the real code path (not assumed from the hotfix's own working-log claim). Remaining work is
checklist-style finalize steps (anchor regeneration, doc updates, full regression pass, ticket
closeout) with no open design or architecture questions.
