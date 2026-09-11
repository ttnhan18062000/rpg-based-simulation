---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260612-WORLDMODULES-CONTRACT
phase: done
date: 2026-06-12
tags: [documentation, contract, worldmodules, compliance]
---

# TCK-20260612-WORLDMODULES-CONTRACT

## Title
Write engine contract for src/worldmodules/ (WORLD-MOD-* compliance namespace)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P0

## Request Summary
`src/worldmodules/` (normalizer.py, repository.py, schema.py, utils.py) carries Compliance IDs WORLD-MOD-004, WORLD-MOD-005 in repository.py, but there is zero documentation for this module anywhere in docs/. The WORLD-MOD-* compliance namespace is entirely unverifiable. Agents implementing world module features have no contract to reference, and the module's role in the world data pipeline (between worldbuilding output and worldassembly input) is undocumented.

## Scope
- Create `docs/worldmodules/` folder with `modules_contract.md`
- Contract must cover: module schema definition, normalization rules (what normalizer.py enforces), repository interface (how modules are loaded, resolved, and cached), utils boundaries
- Map all WORLD-MOD-* Compliance IDs to their source file:line
- Clarify the module's position in the world data pipeline: relationship to worldbuilding output and worldassembly input
- Pass frontmatter validation and add to parity ledger
- Run `make docs-registry`

## Out of Scope
- Changing source code in `src/worldmodules/`
- Other world pipeline contracts (separate tickets)

## Acceptance Criteria
- [ ] `docs/worldmodules/modules_contract.md` exists with valid frontmatter (`status: authoritative`, `layer: engine`, `authority: P0`, `last_verified: 2026-06-12`)
- [ ] Contract maps all WORLD-MOD-* Compliance IDs to `source_file:line` as v2_evidence
- [ ] Normalization rules section enumerates each rule enforced by normalizer.py (one rule per known normalization path)
- [ ] Pipeline position diagram or description: what feeds into worldmodules and what worldmodules produces
- [ ] `python3 tools/validate_frontmatter.py docs/worldmodules/` exits 0
- [ ] At least one parity ledger entry added pointing to the new contract
- [ ] `docs/REGISTRY.yaml` updated after `make docs-registry`

## Related Tickets
- TCK-20260612-WORLDASSEMBLY-CONTRACT
- TCK-20260612-WORLDBUILDING-CONTRACT
- TCK-20260612-WORLDGEN-CONTRACT

## Related Docs
- docs/engine/engineering_playbook_m10.md
- docs/parity_ledger/infrastructure.yaml
- docs/parity_ledger/schema.json

## Related Stored Artifacts
- None.

## Related Code Areas
- src/worldmodules/normalizer.py
- src/worldmodules/repository.py
- src/worldmodules/schema.py
- src/worldmodules/utils.py

## Assumptions / Open Questions
- Whether worldmodules state is authoritative (participates in simulation hash) or preprocessing must be read from source before writing the contract

## Implementation Notes
- normalizer.py carries NO compliance IDs in source — but is an essential part of the pipeline. Documented under the Normalizer Contract section without a WORLD-MOD-* ID.
- WorldModuleSpec is preprocessing-only — confirmed NOT part of AuthoritativeState. Documented as such.
- topological_sort_modules external requires are silently ignored — documented explicitly as this is a non-obvious behavior.

## Test Summary
- No new tests required — behavior already present in source; contract documents existing behavior.

## Files Changed
- `docs/worldmodules/modules_contract.md` (created)
- `docs/parity_ledger/substrate.yaml` (SUBSTRATE-NEW-003 appended)
- `docs/REGISTRY.yaml` (regenerated via make docs-registry)

## Completion Summary
Contract written covering: WorldModuleSpec schema (WORLD-MOD-001/002/003), ModuleParameterSpec (WORLD-MOD-003), WorldModuleRepository (WORLD-MOD-004/005), WorldModuleAuthoringNormalizer (no compliance ID — documented), topological_sort_modules (WORLD-MOD-006/007), full pipeline position diagram, and normalization rules table. Parity ledger SUBSTRATE-NEW-003 added at P1.
