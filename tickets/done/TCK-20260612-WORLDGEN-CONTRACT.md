---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260612-WORLDGEN-CONTRACT
phase: open
date: 2026-06-12
tags: [documentation, contract, worldgeneration, determinism, pipeline]
---

# TCK-20260612-WORLDGEN-CONTRACT

## Title
Write engine contract for src/worldgeneration/ (generator pipeline, determinism guarantees)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`src/worldgeneration/` (generator.py, schema.py) sits between worldbuilding output (WorldCompositionSpec) and worldassembly input. `docs/systems/world_generation.md` is a high-level system overview, not an engine contract — it does not declare authoritative status, determinism guarantees, seeding rules, or the generator's exact position in the world data pipeline. The determinism guarantee (same seed → same generated world) is critical to the simulation's integrity contract but is undocumented.

## Scope
- Create `docs/worldgeneration/` folder with `generator_contract.md`
- Contract must cover: generator pipeline (WorldCompositionSpec → generated world data), schema definition (what a generated world object contains), determinism guarantees (seeding contract: given the same seed and input spec, the output must be bit-identical), pipeline position (what feeds into worldgeneration and what worldgeneration produces for worldassembly)
- Declare authoritative status and resource budget
- Pass frontmatter validation and add to parity ledger (substrate.yaml — determinism entry)
- Run `make docs-registry`

## Out of Scope
- Changing source code in `src/worldgeneration/`
- High-level system overview (already in docs/systems/world_generation.md — do not duplicate, cross-link instead)
- Worldassembly, worldbuilding, worldmodules contracts (separate tickets)

## Acceptance Criteria
- [ ] `docs/worldgeneration/generator_contract.md` exists with valid frontmatter (`status: authoritative`, `layer: engine`, `authority: P1`, `last_verified: 2026-06-12`)
- [ ] Contract declares determinism guarantee: same seed + same input spec → bit-identical output (or explicitly documents any known non-deterministic exception)
- [ ] Seeding rules documented: how the seed is passed, what parts of generation are seed-controlled, what is seed-independent
- [ ] Pipeline position section: input (WorldCompositionSpec from worldbuilding), output (what worldassembly consumes), with cross-links to worldbuilding contract and worldassembly contract
- [ ] `python3 tools/validate_frontmatter.py docs/worldgeneration/` exits 0
- [ ] `docs/parity_ledger/substrate.yaml` has at least one entry updated or added for worldgeneration determinism
- [ ] `docs/REGISTRY.yaml` updated after `make docs-registry`

## Related Tickets
- TCK-20260612-WORLDASSEMBLY-CONTRACT
- TCK-20260612-WORLDBUILDING-CONTRACT
- TCK-20260612-WORLDMODULES-CONTRACT

## Related Docs
- docs/systems/world_generation.md (overview — cross-link from contract, do not duplicate)
- docs/engine/engineering_playbook_m10.md
- docs/parity_ledger/substrate.yaml
- docs/parity_ledger/schema.json

## Related Stored Artifacts
- None.

## Related Code Areas
- src/worldgeneration/generator.py
- src/worldgeneration/schema.py

## Assumptions / Open Questions
- Whether seed is passed as a constructor argument or a global config must be read from generator.py before writing
- Whether non-deterministic exceptions exist (e.g., randomized content selection outside seed) must be determined from source before writing the guarantee

## Implementation Notes
- Input is `GenerationIntentSpec`, not `WorldCompositionSpec` (ticket description was slightly imprecise).
- Generator bypasses the full WorldAssembly pipeline — calls `CompileProfileResolver.resolve()` directly.
- Validation failures under `GENERATED_WORLD` context are non-fatal (contrast: worldbuilding compiler aborts on ERROR).
- `created_at` in `ProvenanceManifest` is wall-clock — documented as the only non-deterministic field.

## Test Summary
- `tests/unit/worldgeneration/test_generator.py` — pre-existing; covers generator pipeline.
- `tests/unit/platform/test_rng_hygiene.py` — covers RNG isolation (no global state pollution).
- No new tests required — behavior is already covered.

## Files Changed
- `docs/worldgeneration/generator_contract.md` (created)
- `docs/parity_ledger/substrate.yaml` (SUBSTRATE-NEW-002 appended)
- `docs/REGISTRY.yaml` (regenerated via make docs-registry)

## Completion Summary
Contract written covering: GenerationIntentSpec schema (WORLD-GEN-001/002), 7-phase generation pipeline (WORLD-GEN-003/004), determinism guarantee (isolated RNG, non-deterministic created_at exception), region layout formulas, resource/population count formulas, provenance fingerprint, and pipeline position vs. the declarative path. Parity ledger SUBSTRATE-NEW-002 added at P0.
