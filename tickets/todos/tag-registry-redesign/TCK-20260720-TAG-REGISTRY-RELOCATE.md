---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260720-TAG-REGISTRY-RELOCATE
phase: open
date: 2026-07-20
tags: []
---

# TCK-20260720-TAG-REGISTRY-RELOCATE

## Title
Relocate tag/layer/glossary registries from docs/guidelines/ to a top-level registries/ directory

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Move tag_registry.jsonl, layer_registry.jsonl, and glossary_registry.jsonl from docs/guidelines/ to a new top-level registries/ directory, because docs/ implies documentation rather than durable git-tracked data, and data/ is already established in this repo as ephemeral/wiped-on-cleanup so it would misrepresent these files as disposable. Every doc/code reference to the old docs/guidelines/*_registry.jsonl paths must be updated in the same pass.

## Scope
- Move the 3 existing files (tag_registry.jsonl, layer_registry.jsonl, glossary_registry.jsonl) from docs/guidelines/ to registries/ with byte-identical content
- Update each tool's _REGISTRY_REL_PATH constant (tools/tag_registry.py, tools/layer_registry.py, tools/glossary_registry.py) to point at the new registries/ path
- Update every active reference to the old docs/guidelines/*_registry.jsonl paths across tools/, src/, tests/, docs/, .claude/, and CLAUDE.md
- Update docs/parity_ledger/infrastructure.yaml's v2_evidence path references in place
- Update the two hardcoded-path tests (test_generate_retro.py, test_agent_ops_dashboard_glossary.py) to the new registries/ path

## Out of Scope
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX (separate, already-filed hotfix — not duplicated or absorbed by this batch)
- Creating the new tag_category_registry.jsonl file (that is TCK-20260720-TAG-CATEGORY-REGISTRY's job, not this ticket's)
- Updating docs/plans/archive/** historical references unless an explicit decision to do so is recorded

## Acceptance Criteria
- [ ] registries/tag_registry.jsonl, registries/layer_registry.jsonl, registries/glossary_registry.jsonl exist with byte-identical content to their former docs/guidelines/ counterparts; old files no longer exist
- [ ] Each tool's _REGISTRY_REL_PATH constant points at registries/<name>.jsonl and resolves correctly from any cwd
- [ ] Grep for old path strings across tools/, src/, tests/, docs/, .claude/, CLAUDE.md returns zero matches in active (non-historical) files after the move — tickets/done/ and stored_artifacts/ historical records are exempt
- [ ] pytest tests/tools/test_tag_registry.py test_layer_registry.py test_glossary_registry.py test_generate_retro.py test_agent_ops_dashboard_glossary.py test_validate_frontmatter.py all pass, including the two hardcoded-path tests updated to registries/
- [ ] docs/parity_ledger/infrastructure.yaml's v2_evidence entries referencing old paths (approx lines 4997, 5017, 5492, 5506) are updated in place
- [ ] An explicit decision (not a silent omission) is recorded on whether docs/plans/archive/** references are updated or intentionally left as historical archive
- [ ] make docs-registry diff confirms the move is a no-op for docs/REGISTRY.yaml (registry generation only walks .md files)

## Related Tickets
- TCK-20260706-TAG-REGISTRY-DATA
- TCK-20260718-LAYER-REGISTRY-CONVERSION
- TCK-20260718-GLOSSARY-REGISTRY
- TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX

## Related Docs
- CLAUDE.md
- docs/guidelines/tag_taxonomy.md
- docs/guidelines/glossary_registry.jsonl
- docs/ai/system_overview.md
- docs/ai/workflows.md
- docs/ai/ticket-lifecycle.md
- docs/guides/ticket_reporting.md
- docs/guides/ticket_tagging.md
- docs/guides/agent_ops_dashboard.md
- docs/agent-monitoring/schema.md
- docs/observability/agent_ops_dashboard_contract.md
- docs/parity_ledger/infrastructure.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- tools/tag_registry.py
- tools/layer_registry.py
- tools/glossary_registry.py
- tools/validate_frontmatter.py
- tools/tag_report.py
- tests/tools/test_generate_retro.py
- tests/tools/test_agent_ops_dashboard_glossary.py
- tests/tools/test_tag_registry.py
- tests/tools/test_layer_registry.py
- tests/tools/test_glossary_registry.py
- tests/tools/test_validate_frontmatter.py
- tests/tools/test_tag_report.py
- src/api/agent_ops_dashboard/ingest.py
- src/api/agent_ops_dashboard/models.py
- .claude/agents/ticket-scoper.md
- .claude/workflows/create-tickets.js
- .claude/workflows/implement-ticket.js
- .claude/workflows/simq-audit.js

## Assumptions / Open Questions
- docs/plans/archive/** references are archived historical docs — likely out of scope, must be flagged as an explicit decision, not a silent omission
- generate_registry.py's docs/ walk only picks up .md files, so moving .jsonl out of docs/ should be a no-op for docs/REGISTRY.yaml — verify via make docs-registry diff
- No root-level registries/ name collision exists (confirmed via ls; only the unrelated src/.../registries.py Python module shares the word)
- layer set to `ai` (Claude agent/orchestration tooling) since this ticket's scope is entirely about registries backing ticket/tag/workflow tooling under .claude/ and tools/, not gameplay cognition or generic guidelines docs; flagged here per CLAUDE.md's registry-check requirement rather than defaulting to `guidelines`

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
