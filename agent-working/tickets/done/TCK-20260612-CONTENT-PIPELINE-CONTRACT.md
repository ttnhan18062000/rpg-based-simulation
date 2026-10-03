---
status: historical
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20260612-CONTENT-PIPELINE-CONTRACT
phase: done
date: 2026-06-12
tags: [documentation, contract, content, content_semantics, pipeline]
---

# TCK-20260612-CONTENT-PIPELINE-CONTRACT

## Title
Write engine contract for src/content/ pipeline and src/content_semantics/ semantic defaults

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`src/content/` (matrix.py, pack_manifest.py, paths.py, reference_graph.py, repository.py, resolver.py, schema.py, validator.py) is the authoritative content resolution gate referenced in 10+ recent tickets, but `docs/content/content_pack_format.md` covers only the user-facing pack format. The internal pipeline — resolver flow, reference graph traversal, RuntimeContentMode semantics, pack validation lifecycle — has no contract. `src/content_semantics/` (defaults.py, faction.py, relation.py, role.py) — the semantic defaults layer for faction/relation/role — has zero documentation anywhere.

## Scope
- Expand `docs/content/` with:
  - `pipeline_contract.md` — covers resolver flow (how content packs are discovered, loaded, validated, and resolved into runtime objects), reference graph rules (cycles, missing refs, resolution order), RuntimeContentMode semantics (STRICT/PERMISSIVE/OFFLINE), pack validation lifecycle
  - `content_semantics_contract.md` — covers faction, relation, and role semantic defaults: how defaults are applied, override rules, what happens when no semantic match is found
- Each contract must follow the Subsystem Contract Template from `docs/engine/engineering_playbook_m10.md`
- ContentUsageMatrix (matrix.py) must be documented with its consumer validation gate semantics
- Pass frontmatter validation on all new docs
- Run `make docs-registry`

## Out of Scope
- Changing source code in `src/content/` or `src/content_semantics/`
- Changing `docs/content/content_pack_format.md` (user-facing pack format — already exists)

## Acceptance Criteria
- [ ] `docs/content/pipeline_contract.md` exists with valid frontmatter (`status: authoritative`, `layer: systems`, `authority: P1`, `last_verified: 2026-06-12`)
- [ ] Pipeline contract documents RuntimeContentMode (STRICT/PERMISSIVE/OFFLINE or equivalent) — enumerate each mode's behavior
- [ ] Pipeline contract covers the reference graph: cycle detection behavior, missing reference handling, resolution order
- [ ] ContentUsageMatrix section in pipeline_contract.md declares what it validates and what makes a consumer usage invalid
- [ ] `docs/content/content_semantics_contract.md` exists with valid frontmatter; covers faction, relation, role default resolution (one section each)
- [ ] content_semantics contract declares fallback behavior when no semantic match is found
- [ ] `python3 tools/validate_frontmatter.py docs/content/` exits 0
- [ ] `docs/REGISTRY.yaml` updated after `make docs-registry`

## Related Tickets
- None in this batch.

## Related Docs
- docs/content/content_pack_format.md
- docs/mechanics/content_usage_matrix.md
- docs/engine/engineering_playbook_m10.md

## Related Stored Artifacts
- None.

## Related Code Areas
- src/content/matrix.py
- src/content/resolver.py
- src/content/reference_graph.py
- src/content/validator.py
- src/content/repository.py
- src/content/schema.py
- src/content/pack_manifest.py
- src/content/paths.py
- src/content_semantics/defaults.py
- src/content_semantics/faction.py
- src/content_semantics/relation.py
- src/content_semantics/role.py

## Assumptions / Open Questions
- Exact names of RuntimeContentMode enum values must be read from schema.py before writing the contract
- Whether content_semantics state is authoritative or advisory must be determined from defaults.py before writing

## Implementation Notes
Compliance namespace is WORLD-CAT-* (not WORLD-* as originally stated in ticket — corrected during investigation). No RuntimeContentMode enum exists; content families use implementation_state (RESOLVED_PARTIALLY / RUNTIME_AUTHORITATIVE / PROJECTED_TO_LEGACY / DESIGN_ONLY). Parity ledger entries INFRA-184 and INFRA-185 added.

## Test Summary
python3 tools/validate_frontmatter.py docs/content/ — OK: 3 files checked, no violations. make docs-registry — 919 entries, both new docs present.

## Files Changed
- docs/content/pipeline_contract.md (created)
- docs/content/content_semantics_contract.md (created)
- docs/parity_ledger/infrastructure.yaml (INFRA-184, INFRA-185 appended)
- docs/plans/missing-docs-contracts.md (frontmatter added)
- docs/plans/tier2-knowledge-search.md (frontmatter added)

## Completion Summary
Wrote engine contract for src/content/ pipeline (WORLD-CAT-* / WORLD-PATH-* compliance namespace) and src/content_semantics/ semantic defaults (WORLD-SEM-* namespace). Both docs pass frontmatter validation and appear in REGISTRY.yaml. Parity ledger updated with INFRA-184 and INFRA-185.
