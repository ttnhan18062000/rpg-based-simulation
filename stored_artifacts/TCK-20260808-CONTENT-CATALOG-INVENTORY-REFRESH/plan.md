---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-CONTENT-CATALOG-INVENTORY-REFRESH
artifact_type: plan
phase: plan
date: 2026-08-08
tags: [content, world, documentation]
---

# Plan — TCK-20260808-CONTENT-CATALOG-INVENTORY-REFRESH

## 1. `tools/generate_content_inventory.py` (new)

A small, real, data-driven counter (mirrors `tools/generate_corpus_registry.py`'s own "generated,
never hand-transcribed" pattern): for each of the 31 real categories investigation.md enumerated,
count entries from their real `data/content/` source file, plus `world_modules`/
`world_compositions` (file-count based) and `simulation_scenarios` (summed across its 4 files).
Outputs a machine-readable snapshot: `config/content_inventory.json` (or similar — final path
decided during Implement based on where other generated-but-not-corpus-registry artifacts live).

## 2. Refresh `docs/audits/D07_content_depth.md`

- Every Layer table (Foundation, Entity, World, Social & Scenario, Module) updated with real
  current counts from the new generator's own output.
- Fix the Recipes/Simulation-scenarios internal inconsistency (table said one number, the doc's
  own Gap Risk Summary further down already said RESOLVED with a different, correct number).
- Re-score F4 (archetype distribution) and F6 (faction relationships) given their real, evidenced
  resolution/improvement (investigation.md's own findings) — move to RESOLVED (F6) or
  substantially-improved (F4), with the real new numbers cited, not silently left at their old
  Gap Risk scores.
- Update `Audit date` to today's real date.
- Add a short new section noting the generator script exists and how to re-run it
  (`make content-inventory` or equivalent), so future re-audits start from real numbers instead of
  a fresh manual count.

## 3. `Makefile` target

New `content-inventory` target, matching `simq-corpus-registry`'s own style.

## No change to D07's own qualitative scoring methodology

Per Out of Scope — the Content Gap Risk / Layer Content Health formulas themselves are untouched;
only the numeric inputs to them are refreshed.

## Acceptance-criteria map

| Criterion | Satisfied by |
|---|---|
| Real current counts reported, real diff shown | investigation.md |
| Regressed-finding check | investigation.md (F1/F2/F3/F5 re-verified still resolved) |
| Generator-script decision with real rationale | investigation.md's own "Decision" section |
| D07 updated with real data | Step 2 |
| Consumable by `LIFECYCLE-FULL-COVERAGE-WORLD` | D07's own refreshed content is directly citable |
| Scoped pytest passes | test_plan.md |
