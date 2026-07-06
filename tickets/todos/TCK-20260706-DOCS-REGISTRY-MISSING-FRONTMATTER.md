---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER
phase: open
date: 2026-07-06
tags: [documentation, registry, frontmatter, tagging]
---

# TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER

## Title
`make docs-registry` exits non-zero: 12 docs lack YAML frontmatter entirely

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
While implementing `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC` (adding a new doc under
`docs/simulation_quality/`), running `make docs-registry` to pick up the new file surfaced a
pre-existing, repo-wide issue: 12 doc files under `docs/` have no YAML frontmatter block at all
(confirmed by direct inspection — e.g. `docs/simulation_quality/eval_matrix_results.md` and
`docs/engine/project_lawbook_m10.md` both start directly with a markdown `#` heading, no `---`
block). `tools/generate_registry.py` treats this as a hard error and exits 1, even though it still
successfully writes `docs/REGISTRY.yaml` with defaults substituted for the affected files — meaning
`make docs-registry` can never exit 0 cleanly today, for anyone, regardless of what they're working
on.

Affected files (from the current run's error output):
```
docs/engine/engineering_playbook_m10.md
docs/engine/legacy_replacement_ledger.md
docs/engine/phase12_entry_package.md
docs/engine/phase13_retirement_manifest.md
docs/engine/project_lawbook_m10.md
docs/engine/supported_progression_surface_phase5.md
docs/mechanics/content_usage_matrix.md
docs/simulation/domains/party_contract.md
docs/simulation_quality/eval_matrix_results.md
docs/simulation_quality/event_type_coverage.md
docs/systems/faction_contract.md
docs/world/demographics_contract.md
```

Confirmed this is pre-existing and unrelated to `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC`'s own work
(that ticket's new doc, `docs/simulation_quality/corpus_tier_taxonomy.md`, has correct frontmatter
and is indexed successfully in the regenerated registry).

## Scope
- Add a minimal, correct YAML frontmatter block (`status`, `layer`, `authority`, `audience`, `tags`)
  to all 12 listed files, following the existing pattern used by sibling docs in the same
  directories (e.g. `docs/simulation_quality/quality_scoring_contract.md`'s frontmatter as a
  template for the two `docs/simulation_quality/` files).
- Confirm `make docs-registry` exits 0 after the fix.
- Spot-check whether any of these 12 files are themselves stale/superseded (several look like
  milestone-era artifacts — `phase12_entry_package.md`, `phase13_retirement_manifest.md`,
  `legacy_replacement_ledger.md`) — if a file is confirmed genuinely obsolete, archiving it (per
  existing `docs/archive/` convention) is an acceptable alternative to adding frontmatter, but this
  requires confirming obsolescence first, not assuming it.

## Out of Scope
- Re-litigating `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC`'s already-completed work
- Content changes to any of the 12 files beyond adding/correcting frontmatter (or archiving, per the
  Scope item above)
- Auditing docs beyond this specific 12-file list (a broader frontmatter audit across all of
  `docs/` is a larger, separate initiative if ever warranted)

## Acceptance Criteria
- [ ] All 12 listed files have valid, correct YAML frontmatter (or are confirmed obsolete and moved
      to `docs/archive/` instead)
- [ ] `make docs-registry` exits 0
- [ ] `python3 tools/validate_frontmatter.py <each file> --content-type doc` passes for every file
      still under `docs/` after this ticket

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC — the ticket during which this pre-existing gap was
  discovered (unrelated to that ticket's own scope)

## Related Docs
(the 12 files listed above)

## Related Stored Artifacts
(none — discovered during another ticket's implementation, not its own investigation)

## Related Code Areas
- `tools/generate_registry.py` — the script that currently treats missing frontmatter as a hard
  error

## Assumptions / Open Questions
- UQ-1: Whether `tools/generate_registry.py`'s hard-error behavior itself should change (e.g. warn
  and continue with exit 0, vs. requiring every doc to have frontmatter) is a separate process
  design question from just fixing these 12 files — this ticket assumes the current hard-error
  behavior is correct and the files should conform to it, not that the tool should be relaxed.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
