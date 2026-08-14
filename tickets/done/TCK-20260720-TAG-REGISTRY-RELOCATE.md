---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260720-TAG-REGISTRY-RELOCATE
phase: done
date: 2026-07-20
tags: [tagging, frontmatter]
---

# TCK-20260720-TAG-REGISTRY-RELOCATE

## Title
Relocate tag/layer/glossary registries from docs/guidelines/ to a top-level registries/ directory

## Status
DONE

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

Moved the 3 registries via `git mv` (rename-history preserved, byte-identical content):
`registries/tag_registry.jsonl`, `registries/layer_registry.jsonl`,
`registries/glossary_registry.jsonl`. Updated `_REGISTRY_REL_PATH` in all 3 owning modules
(`tools/tag_registry.py`, `tools/layer_registry.py`, `tools/glossary_registry.py`) plus their
docstring/description-string mentions of the old path. Updated the 2 hardcoded-path test fixtures
(`test_agent_ops_dashboard_glossary.py`'s `_init_repo_skeleton`/`_write_glossary`/`_write_layers`;
`test_generate_retro.py`'s `_write_registry`) to build against `registries/` instead of
`docs/guidelines/`. Updated `infrastructure.yaml`'s 2 `v2_evidence` occurrences (lines 5038, 5539)
to the new path — deliberately left its 2 `text:`-block occurrences (lines 5018, 5525) untouched,
since those narrate historical fact as of their original writing, not current file location.

Updated all remaining active prose/comment/docstring references (17 files: `validate_frontmatter.py`,
`tag_report.py`, 2 test files, 4 `docs/ai`/`docs/guides` guides, `agent_ops_dashboard_contract.md`,
`docs/agent-monitoring/schema.md`, `tag_taxonomy.md`, `create-tickets.js`, `ticket-scoper.md`,
`implement-ticket.js`, `simq-audit.js`, `CLAUDE.md`) via a scoped, file-list-targeted sed pass — not
a blind repo-wide replace, so `docs/guidelines/tag_taxonomy.md`'s own (unmoved) path references were
never at risk of collision.

Explicit archive decision (AC #6): `docs/plans/archive/agent_ops_dashboard/*.md` (5 files) left
untouched as frozen historical proposals. One non-archived doc,
`docs/plans/tag_dedup/proposal_tag_corpus_dedup.md` (frontmatter `status: active`), was updated
alongside the other active docs — it is not under `docs/plans/archive/`, so the ticket's
archive-exemption did not apply to it; this is recorded here as the explicit, non-silent decision
the AC requires.

`src/api/agent_ops_dashboard/ingest.py` and `models.py` (listed defensively in Related Code Areas)
needed no change — confirmed via direct grep that neither contains a literal old-path string; both
consume the registries only through `load_registry()` calls.

Parity: skip-eligible per the standard rule (no `src/` file changed, `behavior_changed=false`),
confirmed via the P0 lazy-safeguard scan (`find_p0_intersection`) returning no hit. The 2
`infrastructure.yaml` `v2_evidence` path updates above are the only parity-ledger touch, applied
directly rather than via a separate parity-updater pass.

## Test Summary

`python3 -m pytest tests/tools/test_tag_registry.py tests/tools/test_layer_registry.py
tests/tools/test_glossary_registry.py tests/tools/test_generate_retro.py
tests/tools/test_agent_ops_dashboard_glossary.py tests/tools/test_validate_frontmatter.py
tests/tools/test_tag_report.py -q` → **252 passed**, 0 failed.

`make docs-registry` run before and after the move: output byte-identical except the `# Generated:`
timestamp comment — confirms AC #7's no-op claim empirically (`generate_registry.py`'s walk only
matches `**/*.md`, never touched by a `.jsonl` relocation).

Final grep sweep for the 3 old path strings across `tools/ src/ tests/ docs/ .claude/ CLAUDE.md`
returns exactly 7 matches, all in the 2 intentionally-excluded classes: 5 archived proposal docs,
2 `infrastructure.yaml` `text:`-block lines — zero unintended matches.

## Files Changed
- `registries/tag_registry.jsonl`, `registries/layer_registry.jsonl`,
  `registries/glossary_registry.jsonl` (moved from `docs/guidelines/`, byte-identical)
- `tools/tag_registry.py`, `tools/layer_registry.py`, `tools/glossary_registry.py`
  (`_REGISTRY_REL_PATH` + docstring path updates)
- `tests/tools/test_agent_ops_dashboard_glossary.py`, `tests/tools/test_generate_retro.py`
  (hardcoded fixture path updates)
- `docs/parity_ledger/infrastructure.yaml` (2 `v2_evidence` path updates)
- `tools/validate_frontmatter.py`, `tools/tag_report.py`, `tests/tools/test_validate_frontmatter.py`,
  `tests/tools/test_tag_report.py`, `docs/guidelines/tag_taxonomy.md`, `docs/ai/system_overview.md`,
  `docs/ai/ticket-lifecycle.md`, `docs/ai/workflows.md`, `docs/guides/ticket_reporting.md`,
  `docs/guides/ticket_tagging.md`, `docs/guides/agent_ops_dashboard.md`,
  `docs/observability/agent_ops_dashboard_contract.md`, `docs/agent-monitoring/schema.md`,
  `.claude/workflows/create-tickets.js`, `.claude/agents/ticket-scoper.md`,
  `.claude/workflows/implement-ticket.js`, `.claude/workflows/simq-audit.js`, `CLAUDE.md`,
  `docs/plans/tag_dedup/proposal_tag_corpus_dedup.md` (prose path reference updates)
- `docs/REGISTRY.yaml` (regenerated, content byte-identical to before except timestamp)

## Completion Summary
Relocated all 3 durable ticket/doc registries (`tag_registry.jsonl`, `layer_registry.jsonl`,
`glossary_registry.jsonl`) from `docs/guidelines/` to a new top-level `registries/` directory,
since `docs/` implies documentation rather than durable git-tracked data and `data/` is already
established in this repo as ephemeral/wiped-on-cleanup. All 3 owning tools' path constants, 2
hardcoded test fixtures, 2 parity-ledger `v2_evidence` entries, and 18 active prose/doc/workflow
references were updated in the same pass; 5 archived historical docs and 2 parity-ledger `text:`
narrative blocks were deliberately left untouched, per an explicit (not silent) scope decision.
252 regression tests pass; `make docs-registry` confirmed as a byte-identical no-op; a final grep
sweep confirms zero unintended remaining old-path references.
