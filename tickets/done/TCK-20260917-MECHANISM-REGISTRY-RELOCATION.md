---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-REGISTRY-RELOCATION
phase: done
date: 2026-09-17
tags: [architecture, schema, simulation-quality]
---

# TCK-20260917-MECHANISM-REGISTRY-RELOCATION

## Title
Move `mechanisms.yaml` out of `docs/brainstorm/` into `registries/` — the path misrepresented the
file's own authority

## Status
DONE

## Tier
hotfix

## Type
refactor

## Priority
P1

## Request Summary
User's call, relayed via peer, approved before merging #209: `docs/brainstorm/` implies "not
officially applied yet." `mechanisms.yaml` is CI-enforced, six-invariant-validated data — exactly
the opposite of what its own directory told a reader to assume. Target: `registries/`, not `data/`
(which in this repo means game content — `worlds/`, `content/`, `world_modules/`,
`expectation_packs/` — and would swap one misleading path for another). `registries/` is right
because the name is literally what the file is, and its siblings are all project metadata
(`layer_registry.jsonl`, `tag_registry.jsonl`, `tag_category_registry.jsonl`,
`capability_envelope_registry.jsonl`).

**Rendered outputs stay in `docs/brainstorm/`** — that split is the point, not a compromise:
`registries/` holds source of truth, `docs/brainstorm/` holds rendered and exploratory surfaces.
The four generated views (`mechanism_registry_view.md`, `mechanism_verification_view.md`,
`mechanism_priority_view.md`, `mechanism_registry.html`) belong with the atlas, capabilities page,
and wiring map — their actual peers — and "not officially applied" is a fair label for a rendered
view while being a false one for enforced data.

**Append-only objection checked and cleared**: `registries/` has no convention document. Append-
only is a property of the *allowlist* registries specifically (tickets cite layer/tag values by
id, so they can't be renamed) — it isn't a rule the directory itself imposes. A mutable registry
violates nothing written down, but is handled explicitly rather than left implicit: the file's own
header now says outright that it's the one mutable, non-append-only, YAML (not JSONL) file among
its four siblings, so nobody assumes allowlist semantics and refuses to correct a state.

## Scope
1. `git mv docs/brainstorm/mechanisms.yaml registries/mechanisms.yaml`.
2. Header comment explicitly stating the mutability/format difference from its four JSONL
   siblings, and citing why this ticket moved it.
3. Citation sweep: 14 tools' own `_REGISTRY_PATH`/`_DEFAULT_PATH`/`_DEFAULT_REGISTRY_PATH`
   constructions, the Makefile's `mechanism-registry-validate` target description, 11 test files'
   own hardcoded registry-path constants, and 2 still-open tickets referencing the old path.
4. Regenerate all four rendered views (their own "generated from `docs/brainstorm/mechanisms.yaml`"
   headers would otherwise render a stale path to every reader).
5. Grep repo-wide afterward and confirm zero stale references remain outside `tickets/done/`/
   `stored_artifacts/` (frozen historical records, not rewritten) — same discipline as the tools
   package move.

## Out of Scope
- `docs/plans/mechanism_claims_as_tests_initiative.md` — lives in peer's own worktree, uncommitted
  here; peer owns fixing their own copy.
- Renaming or restructuring anything else in `registries/` or `docs/brainstorm/`.

## Acceptance Criteria
1. `registries/mechanisms.yaml` exists; `docs/brainstorm/mechanisms.yaml` does not.
2. The file's own header explicitly states it is mutable and YAML, unlike its four append-only
   JSONL siblings.
3. All four rendered views regenerate cleanly from the new path and land in `docs/brainstorm/`
   unchanged in location.
4. A repo-wide grep for the old path returns zero hits outside `tickets/done/`/`stored_artifacts/`.
5. Full scoped suite passes, including with `graphify-out/` genuinely moved aside and restored.

## Related Tickets
- `TCK-20260916-MECHANISM-REGISTRY-TOOLS-PACKAGE` — the same citation-sweep discipline, one
  directory move earlier in this same epic.
- `TCK-20260915-EPIC-MECHANISM-REGISTRY` — the epic whose own source-of-truth file this is.

## Related Docs
None new — the rationale lives in this ticket and the file's own new header comment.

## Related Stored Artifacts
None — hotfix tier, self-evident intent (a mechanical file move plus citation sweep) captured in
this ticket.

## Related Code Areas
- `registries/mechanisms.yaml` (moved)
- `tools/mechanism_registry/*.py` (12 of 14 files touched; 2 have no direct path reference)
- `Makefile`
- `tests/unit/tools/test_mechanism_*.py` (11 files)
- `docs/brainstorm/mechanism_registry_view.md`, `mechanism_verification_view.md`,
  `mechanism_priority_view.md`, `mechanism_registry.html` (regenerated, unchanged location)

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
Two path-construction styles existed across the 14 tools (`_REGISTRY_PATH`/`_DEFAULT_PATH` using
`_REPO_ROOT`, and test files using a bare `REPO_ROOT`) — both needed a broader regex than a single
literal-string replace to catch every variable-name variant; the first sweep pass missed several
test files for exactly this reason and needed a second, wider pass before the suite was green.

`docs/REGISTRY.yaml` still shows the old path in several `related_code_areas` entries after
regeneration — confirmed these are extracted verbatim from already-closed tickets' own frozen
bodies (historical record, not a live citation), not a live path assertion; left alone, consistent
with the "tickets/done/ is frozen" convention already established for the tools-package move.

## Test Summary
181 tests passing in the full scoped suite (`tests/unit/tools/`,
`tests/unit/engine/test_capability_registry.py`, `tests/mechanic_scenarios/`), both with
`graphify-out/` present and with it genuinely moved aside and restored. No test content/assertions
changed — only path constants.

## Files Changed
- `registries/mechanisms.yaml` — moved from `docs/brainstorm/mechanisms.yaml`, header comment
  added
- `tools/mechanism_registry/registry.py`, `mechanism_atlas_regenerate.py`,
  `mechanism_capabilities_regenerate.py`, `mechanism_registry_graphify_check.py`,
  `mechanism_registry_completeness_check.py`, `mechanism_state_caller_check.py`,
  `mechanism_wiring_map_classdef.py`, `generate_mechanism_charts.py`,
  `generate_mechanism_priority_view.py`, `generate_mechanism_registry_view.py`,
  `generate_mechanism_verification_view.py`, `generate_mechanism_registry_html.py` — registry
  path constant updated
- `Makefile` — `mechanism-registry-validate` target description updated
- `tests/unit/tools/test_mechanism_registry.py`, `test_mechanism_registry_view.py`,
  `test_mechanism_atlas_regenerate.py`, `test_mechanism_state_caller_check.py`,
  `test_mechanism_capabilities_regenerate.py`, `test_mechanism_registry_completeness_check.py`,
  `test_mechanism_priority_derivation.py`, `test_mechanism_capabilities_tier.py`,
  `test_mechanism_wiring_map_classdef.py`, `test_mechanism_artifact_convergence.py`,
  `test_mechanism_registry_html.py` — registry path constant updated
- `tickets/todos/TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION.md`,
  `TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT.md` — citation updated (still open)
- `docs/brainstorm/mechanism_registry_view.md`, `docs/brainstorm/mechanism_verification_view.md`,
  `docs/brainstorm/mechanism_priority_view.md`, `docs/brainstorm/mechanism_registry.html` —
  regenerated, own "generated from" headers now cite the new path
- `docs/REGISTRY.yaml` — regenerated at Finalize

## Completion Summary
Closed. `mechanisms.yaml` now lives at `registries/mechanisms.yaml`, matching what the file
actually is (CI-enforced, validated data) rather than what its old directory implied ("not
officially applied yet"). Rendered views stay in `docs/brainstorm/` alongside their actual peers.
The file's own header now explicitly records that it is the one mutable, non-append-only member of
its `registries/` cohort, so its own convention doesn't get silently assumed from its siblings. A
repo-wide grep confirmed zero stale citations remain outside frozen historical tickets/stored
artifacts. `docs/plans/mechanism_claims_as_tests_initiative.md` (peer's own uncommitted worktree
copy) is peer's own to fix, per their explicit request.
