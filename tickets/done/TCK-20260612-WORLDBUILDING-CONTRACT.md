---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260612-WORLDBUILDING-CONTRACT
phase: done
date: 2026-06-12
tags: [documentation, contract, worldbuilding, compliance]
---

# TCK-20260612-WORLDBUILDING-CONTRACT

## Title
Write engine contract for src/worldbuilding/ (WORLD-* compliance namespace)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P0

## Request Summary
`src/worldbuilding/` (compiler.py, recipe.py, repository.py, schema.py, validator.py, cli.py) carries Compliance IDs WORLD-050, WORLD-051, WORLD-052 in compiler.py but the backing contract does not exist. `docs/mechanics/06_worldbuilding_foundation.md` covers RPG declarative topology laws (what the world looks like) but nothing covers the compilation pipeline (how declarative specs become WorldCompositionSpec). Agents modifying the compiler or validator have no contract to enforce against, and the WORLD-* compliance namespace is unverifiable in the parity ledger.

## Scope
- Create `docs/worldbuilding/` folder with `compiler_contract.md`
- Contract must cover: compiler pipeline (input → output), recipe resolution rules, validator contract (what makes a world spec valid), repository interface, CLI entrypoint boundaries
- Map all WORLD-* Compliance IDs found in src/worldbuilding/ source files to their source line
- Add `last_verified` and pass frontmatter validation
- Add entries to `docs/parity_ledger/substrate.yaml` or `infrastructure.yaml` for the compiler pipeline
- Run `make docs-registry`

## Out of Scope
- Changing source code in `src/worldbuilding/`
- Documenting worldassembly, worldmodules, or worldgeneration (separate tickets)
- RPG topology laws (already in docs/mechanics/06_worldbuilding_foundation.md)

## Acceptance Criteria
- [ ] `docs/worldbuilding/compiler_contract.md` exists with valid frontmatter (`status: authoritative`, `layer: engine`, `authority: P0`, `last_verified: 2026-06-12`)
- [ ] Contract describes the compiler pipeline: input (declarative world spec), processing (recipe resolution, validation), output (WorldCompositionSpec)
- [ ] All WORLD-* Compliance IDs found in `src/worldbuilding/` are listed with `source_file:line` as v2_evidence
- [ ] Validator rules section enumerates what makes a world spec invalid (one rule per known rejection path in validator.py)
- [ ] `python3 tools/validate_frontmatter.py docs/worldbuilding/` exits 0
- [ ] At least one parity ledger entry updated or added pointing to the new contract
- [ ] `docs/REGISTRY.yaml` includes the new doc after `make docs-registry`

## Related Tickets
- TCK-20260612-WORLDASSEMBLY-CONTRACT
- TCK-20260612-WORLDMODULES-CONTRACT
- TCK-20260612-WORLDGEN-CONTRACT

## Related Docs
- docs/mechanics/06_worldbuilding_foundation.md
- docs/engine/engineering_playbook_m10.md
- docs/parity_ledger/substrate.yaml
- docs/parity_ledger/schema.json

## Related Stored Artifacts
- None.

## Related Code Areas
- src/worldbuilding/compiler.py
- src/worldbuilding/recipe.py
- src/worldbuilding/repository.py
- src/worldbuilding/schema.py
- src/worldbuilding/validator.py
- src/worldbuilding/cli.py

## Assumptions / Open Questions
- Total count of WORLD-* IDs beyond 050-052 unknown — scan all files before writing
- Whether the compiler is part of authoritative state or a preprocessing step must be determined from the source

## Implementation Notes
Compliance namespace broader than ticket assumed: also covers WORLD-060/061/062 (repository) and WORLD-070/071/072 (validator+recipe+cli) and CLI-002. Two compilation paths documented: direct (WorldSpec→AuthoritativeState) and composition path via WorldAssembly. Compiler uses Python `random` — not deterministic without external seed. Parity ledger entry SUBSTRATE-NEW-001 added to substrate.yaml.

## Test Summary
python3 tools/validate_frontmatter.py docs/worldbuilding/ — OK: 1 file, no violations. make docs-registry — engine layer now 144 docs, P0 authority 17, no errors.

## Files Changed
- docs/worldbuilding/compiler_contract.md (created)
- docs/parity_ledger/substrate.yaml (SUBSTRATE-NEW-001 appended)

## Completion Summary
Wrote worldbuilding compiler contract covering both compilation paths, full WORLD-050/051/052/060/061/062/070/071/072 compliance ID index, validator abort-on-ERROR contract, RegionRecipeSpec validation rules, repository safety contract, and CLI boundary.
