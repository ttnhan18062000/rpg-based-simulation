---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260612-WORLDASSEMBLY-CONTRACT
phase: done
date: 2026-06-12
tags: [documentation, contract, worldassembly, compliance]
---

# TCK-20260612-WORLDASSEMBLY-CONTRACT

## Title
Write engine contract for src/worldassembly/ (WORLD-ASM-* compliance namespace)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P0

## Request Summary
`src/worldassembly/` (resolver.py, entity_spawner.py, models.py, schema.py, context.py) already carries Compliance IDs WORLD-ASM-008, WORLD-ASM-009, WORLD-ASM-010 in source comments, but the backing contract document does not exist. The parity ledger cannot record `v2_evidence` for these IDs, and agents implementing world assembly features have no contract to enforce against. The only existing coverage is two ADRs (world_assembly_architecture.md, world_repository_layout.md) — decision records, not a pipeline contract. This ticket writes the missing `docs/worldassembly/` contract.

## Scope
- Create `docs/worldassembly/` folder with a primary contract doc `assembly_contract.md`
- Contract must declare: authoritative status of WorldAssembly state, assembly pipeline phases (how WorldCompositionSpec becomes a live world), entity spawning rules, schema validation flow, context lifecycle
- Cover the full WORLD-ASM-* compliance ID namespace — read source files to identify all existing IDs and map each to the corresponding source line
- Add `last_verified` date and pass `python3 tools/validate_frontmatter.py docs/worldassembly/`
- Add at least one entry to `docs/parity_ledger/infrastructure.yaml` linking to the new contract
- Run `make docs-registry` after writing

## Out of Scope
- Changing any source code in `src/worldassembly/`
- Writing tests (test coverage is a separate concern)
- Documenting worldbuilding, worldmodules, or worldgeneration (separate tickets)

## Acceptance Criteria
- [ ] `docs/worldassembly/assembly_contract.md` exists with valid frontmatter (`status: authoritative`, `layer: engine`, `authority: P0`, `last_verified: 2026-06-12`)
- [ ] Contract declares authoritative status (YES/NO), resource budget, retention/overflow policy, and degradation laws per engineering_playbook_m10.md Subsystem Contract Template
- [ ] Every Compliance ID found in `src/worldassembly/` source files is listed in the contract with its source file:line as `v2_evidence`
- [ ] `python3 tools/validate_frontmatter.py docs/worldassembly/` exits 0
- [ ] `docs/parity_ledger/infrastructure.yaml` has at least one new entry with `v2_evidence` pointing to `docs/worldassembly/assembly_contract.md`
- [ ] `docs/REGISTRY.yaml` includes the new doc after `make docs-registry`

## Related Tickets
- TCK-20260612-WORLDBUILDING-CONTRACT
- TCK-20260612-WORLDMODULES-CONTRACT
- TCK-20260612-WORLDGEN-CONTRACT

## Related Docs
- docs/architecture/world_assembly_architecture.md
- docs/architecture/world_repository_layout.md
- docs/engine/engineering_playbook_m10.md
- docs/engine/authoritative_pipeline.md
- docs/parity_ledger/infrastructure.yaml
- docs/parity_ledger/schema.json

## Related Stored Artifacts
- None.

## Related Code Areas
- src/worldassembly/resolver.py
- src/worldassembly/entity_spawner.py
- src/worldassembly/models.py
- src/worldassembly/schema.py
- src/worldassembly/context.py

## Assumptions / Open Questions
- Authoritative status of WorldAssembly state (participates in hash or shadow-only) must be determined by reading resolver.py and context.py before writing the contract
- Number of WORLD-ASM-* IDs beyond 008-010 is unknown — read all files in src/worldassembly/ to find all compliance comments

## Implementation Notes
WORLD-ASM-004/005 not present in source — noted as retired/reserved in contract. Entity spawner has no compliance IDs. Two spawn paths: archetype-native (primary) and V2EntityBuilder legacy guard for non-archetype entities. Assembly confirmed as preprocessing (not AuthoritativeState). Parity ledger INFRA-187 added at P0.

## Test Summary
python3 tools/validate_frontmatter.py docs/worldassembly/ — OK: 1 file, no violations. make docs-registry — engine layer now 143 docs, P0 authority count 16, no errors.

## Files Changed
- docs/worldassembly/assembly_contract.md (created)
- docs/parity_ledger/infrastructure.yaml (INFRA-187 appended)

## Completion Summary
Wrote world assembly contract covering full pipeline (WorldCompositionSpec→ResolvedWorldBundle→EntityState), all WORLD-ASM-* compliance IDs, CompileContext accumulation, two-path entity spawner, and fatal ResolverError contract.
