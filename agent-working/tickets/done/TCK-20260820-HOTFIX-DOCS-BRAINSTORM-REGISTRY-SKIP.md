---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260820-HOTFIX-DOCS-BRAINSTORM-REGISTRY-SKIP
phase: done
date: 2026-08-20
tags: [documentation, registry, frontmatter]
---

# TCK-20260820-HOTFIX-DOCS-BRAINSTORM-REGISTRY-SKIP

## Title
Exempt `docs/brainstorm/` from the registry — free-form ideation prose with no frontmatter convention, breaking `tests/tools/test_generate_registry.py::TestRealDocsTree`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
A concurrent session added a new `docs/brainstorm/` directory (`character_capabilities_review.md`,
`entity_idea.md`, `entity_reproduction_review.md`) — free-form external-review and ideation prose,
none of which has ever had YAML frontmatter, matching the directory's actual nature (raw
brainstorming notes, not structured reference docs). `tools/generate_registry.py`'s `collect_docs()`
walks all of `docs/` except a fixed skip-list (`_SKIP_DOC_SUBDIRS = {"archive", "parity_ledger",
"scenarios", "entity"}`) and requires every `.md` file it finds to have frontmatter, so these 3 new
files broke `tests/tools/test_generate_registry.py::TestRealDocsTree::test_registry_exits_zero_on_real_docs_tree`
and `::test_check_flag_detects_no_drift_against_real_registry` in CI on PR #31
(`docs-plans-experiments-backlog-sweep`), which bundles this content alongside 3 unrelated tickets
from a different session.

## Scope
- Add `"brainstorm"` to `_SKIP_DOC_SUBDIRS` in `tools/generate_registry.py`, matching how
  `archive`/`parity_ledger`/`scenarios`/`entity` are already treated — real exclusions for
  `archive`/`parity_ledger` (contain `.md` files that would otherwise be indexed), documented
  inert-but-retained entries for `scenarios`/`entity`. `brainstorm` is a real, active exclusion
  like `archive`/`parity_ledger` (it does contain `.md` files that would otherwise be indexed).
- Extend the adjacent comment block explaining the addition, following the existing style.
- Re-run `make docs-registry` to confirm it now exits 0 against the real docs tree.
- Re-run the two previously-failing tests plus the full `test_generate_registry.py` suite locally.

## Out of Scope
- Adding frontmatter to the 3 `docs/brainstorm/` files themselves — explicitly rejected; this
  content is free-form ideation prose, not a structured reference doc, and forcing a frontmatter
  schema onto it would misrepresent its nature. This was a deliberate choice between two options,
  not an oversight.
- Any change to the content of the 3 `docs/brainstorm/` files — not this ticket's concern, owned by
  the session that authored them.
- Auditing whether other new top-level `docs/` subdirectories need similar treatment — out of scope,
  this ticket only fixes the concrete CI failure at hand.

## Acceptance Criteria
- [x] `_SKIP_DOC_SUBDIRS` includes `"brainstorm"`, with the adjacent comment block explaining why.
- [x] `make docs-registry` exits 0 against the real docs tree (no missing-frontmatter error).
- [x] `tests/tools/test_generate_registry.py::TestRealDocsTree::test_registry_exits_zero_on_real_docs_tree`
      and `::test_check_flag_detects_no_drift_against_real_registry` both pass.
- [x] `tests/tools/test_generate_registry.py::TestRealDocsTree::test_skip_doc_subdirs_exist_on_disk`
      still passes (requires `docs/brainstorm/` to actually exist on disk, which it does).
- [x] Full `tests/tools/test_generate_registry.py` suite passes (51/51).

## Related Tickets
- TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES — established the disk-parity regression test this ticket's
  change must keep passing, and the "real exclusion vs. documented inert entry" distinction in the
  `_SKIP_DOC_SUBDIRS` comment block this ticket extends.
- TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER — prior precedent for handling missing-frontmatter
  doc gaps; that ticket chose to backfill frontmatter rather than exempt, but for docs intended as
  structured reference content — different situation from this ticket's free-form prose case.

## Related Docs
None beyond `tools/generate_registry.py` itself.

## Related Stored Artifacts
None — hotfix tier, self-evident intent captured directly in this ticket.

## Related Code Areas
- tools/generate_registry.py
- tests/tools/test_generate_registry.py

## Assumptions / Open Questions
- Assumes `docs/brainstorm/` is intended to remain a permanent, ungoverned scratch/ideation space
  (like the CI-failure context suggests) rather than eventually graduating to a frontmatter
  convention of its own — if that assumption is wrong, this exemption is easy to reverse later.

## Implementation Notes
Added `"brainstorm"` to `_SKIP_DOC_SUBDIRS` in `tools/generate_registry.py`, extending the adjacent
comment to classify it alongside `archive`/`parity_ledger` as a real (load-bearing) exclusion —
`docs/brainstorm/` genuinely contains `.md` files that would otherwise be indexed and would fail
the frontmatter requirement, unlike the `scenarios`/`entity` inert-no-op entries. Chose exemption
over backfilling frontmatter (the other option considered) because this content is free-form
external-review/ideation prose authored by a different concurrent session, not structured reference
documentation — forcing a frontmatter schema onto it would misrepresent its nature, and guessing at
`layer`/`authority`/`tags` values for content I didn't author risked getting them wrong.

Document-Update phase found one real, concrete staleness this change caused: a live doc,
`docs/engine/contracts/context_packet_contract.md` (line 125-126), directly quoted the literal
`_SKIP_DOC_SUBDIRS` set value and its exact source line number in its Open Decision 3 Resolution
section — both went stale. Fixed to include `"brainstorm"` and the corrected line number (61).
A related but genuinely out-of-scope reference in `docs/architecture/doc_updater_agent.md` (a
scope-boundary policy table asking whether `docs/brainstorm/` should also join doc-updater's own
"out-of-scope-for-everyone" set) was correctly left untouched — that's a separate policy decision
this ticket's own Out of Scope section explicitly declined to make.

## Test Summary
- `make docs-registry` — exits 0 against the real docs tree, no missing-frontmatter error (was
  previously failing with "ERROR: 2 doc file(s) missing frontmatter").
- `pytest tests/tools/test_generate_registry.py -q` — 51 passed, 0 failed, including
  `test_registry_exits_zero_on_real_docs_tree`, `test_check_flag_detects_no_drift_against_real_registry`,
  and `test_skip_doc_subdirs_exist_on_disk` (all previously-failing or at-risk tests now pass).

## Files Changed
- `tools/generate_registry.py` — added `"brainstorm"` to `_SKIP_DOC_SUBDIRS`, extended the adjacent
  comment block.
- `docs/engine/contracts/context_packet_contract.md` — corrected a stale quoted `_SKIP_DOC_SUBDIRS`
  literal and source line-number citation.
- `docs/REGISTRY.yaml` — regenerated.

## Completion Summary
Fixed the real CI failure on PR #31 (`docs-plans-experiments-backlog-sweep`):
`tests/tools/test_generate_registry.py::TestRealDocsTree`'s two tests were failing because a
concurrent session's new `docs/brainstorm/` directory (3 free-form ideation/review prose files, no
frontmatter convention) broke the registry's frontmatter requirement. Exempted `docs/brainstorm/`
via `_SKIP_DOC_SUBDIRS`, matching the existing `archive`/`parity_ledger` real-exclusion pattern,
rather than forcing an unnatural frontmatter schema onto content I didn't author. Found and fixed
one genuine doc-staleness side effect (a stale literal quote in an Engine Contract doc). All 51
tests in the affected suite pass; `make docs-registry` exits 0 clean.
