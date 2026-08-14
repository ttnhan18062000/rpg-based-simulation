---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260718-LAYER-REGISTRY-CONVERSION
phase: done
date: 2026-07-18
tags: [frontmatter, tagging]
---

# TCK-20260718-LAYER-REGISTRY-CONVERSION

## Title
Convert LAYER_VALUES from a hardcoded Python enum into an append-only registry, mirroring tag_registry.py

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Mid-epic design decision from the user, given during implementation of this
epic: "I think layer can be added if follow the right process and files,
similar to tag." Today `LAYER_VALUES` (`tools/validate_frontmatter.py`) is a
hardcoded Python `set` literal — adding a new legitimate Layer value
requires a code change/PR/review, unlike `Tag`, which already has a
registry-file-backed process (`docs/guidelines/tag_registry.jsonl` +
`tools/tag_registry.py`: append-only JSONL, one entry per line, `add_tag()`
refuses duplicates, CLI `add`/`list` commands — read in full as this
ticket's template). This ticket converts `Layer` to the same
registry-backed mechanism, while preserving two structural differences from
`Tag` that must NOT be collapsed: (1) `Layer` remains **single-value per
ticket** (the `layer:` frontmatter field takes exactly one value — this is
unchanged, do not make it a list like `tags:`), and (2) `Layer` entries are
more curated than `Tag`'s open 4-category taxonomy — a `Layer` registry
entry does not need `Tag`'s `category` field at all (no Subsystem/Process/
Phase/Quality split makes sense for `Layer`, which **is** the
subsystem-topic dimension itself), just `{"layer": ..., "added_date": ...,
"note": "why this layer exists"}`.

## Scope
- Read `tools/tag_registry.py` in full as the template before writing
  anything.
- Create `docs/guidelines/layer_registry.jsonl` — append-only JSONL, one
  `{"layer": ..., "added_date": ..., "note": ...}` entry per line, no
  `category` field (see Request Summary for why).
- Create `tools/layer_registry.py` mirroring `tag_registry.py`'s shape:
  `registry_path()`, `load_registry()` (raises on duplicate registration,
  same invariant), `is_layer_registered()`, `check_layers_registered()`
  (plural-input helper mirroring `check_tags_registered`, even though a
  ticket only ever has one `layer:` value — useful for batch/registry-audit
  callers), `add_layer(layer, note="", root=None)` (append-only, refuses to
  re-add an existing layer), and a CLI (`add <layer> --note "..."`, `list`).
  No `--category` flag on `add` (unlike `tag_registry.py`'s `add` command) —
  `Layer` has no category dimension.
- **Seed the registry** with the 19 currently-hardcoded values from
  `tools/validate_frontmatter.py`'s `LAYER_VALUES` (`mechanics`, `engine`,
  `testing`, `simulation`, `ai`, `architecture`, `core`, `ticket`,
  `artifact`, `guidelines`, `observability`, `performance`, `combat`,
  `compliance`, `strategy`, `systems`, `economy`, `world`, `misc`),
  pre-registered at conversion time with a brief note each (why that
  subsystem exists as a Layer) — this is what keeps the existing ~1135-file
  corpus valid with zero re-validation needed; this ticket is a **mechanism
  change, not a data-drift fix**, do not conflate its scope with
  `TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP`'s (already DONE, do not
  revisit).
- Update `tools/validate_frontmatter.py`: `LAYER_VALUES` becomes a
  computed value loaded from the registry at import time (via the new
  module), **keeping the same importable name** — `tools/ticket_field_values.py`
  currently does `from validate_frontmatter import LAYER_VALUES` (a live
  import, confirmed via direct read); this must keep working unchanged, so
  `ticket_field_values.py` itself needs no edit if this import surface is
  preserved correctly. Verify this holds via a real test, not just assumed.
- Update `CLAUDE.md`'s Ticket Format section: add a Layer-registry
  paragraph directly mirroring the existing Tags-allowlist paragraph
  ("Tags are a hard allowlist..."), answering the open "how do we decide
  layer" question going forward: same discipline as Tag, just single-valued
  and curated — check the registry (`python3 tools/layer_registry.py
  list`), use an existing entry if it fits the ticket's actual subsystem,
  register a new one (`python3 tools/layer_registry.py add <layer> --note
  "why"`) with justification only if it genuinely doesn't fit — never
  force-fit into `misc` when a real category is missing.

## Out of Scope
- Any change to `Tag`'s own registry/mechanism — this ticket only adds an
  analogous, structurally distinct mechanism for `Layer`.
- Re-validating or re-scanning the existing ticket corpus for Layer drift —
  seeding the registry with the exact current 19 values makes this a
  behavior-preserving conversion, not a data cleanup; no corpus scan is
  needed or in scope.
- `TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL`'s own scope (making the
  dashboard's Layer filter facet canonical) — that ticket already plans to
  import `LAYER_VALUES` generically from `tools/ticket_field_values.py`;
  this ticket must confirm that import surface still resolves correctly
  post-conversion (via a test), not redo that ticket's work.

## Acceptance Criteria
- [ ] `docs/guidelines/layer_registry.jsonl` exists, seeded with exactly the
      19 current `LAYER_VALUES`, each with a real (non-empty) `note`.
- [ ] `tools/layer_registry.py` exists with `load_registry`/
      `is_layer_registered`/`check_layers_registered`/`add_layer` and a
      working CLI, structurally mirroring `tag_registry.py` (append-only,
      duplicate-registration raises, no update/delete).
- [ ] `tools/validate_frontmatter.py`'s `LAYER_VALUES` is now
      registry-backed (computed from `layer_registry.py`, not a hardcoded
      literal), while the importable name/surface is unchanged.
- [ ] A real test confirms `tools/ticket_field_values.py`'s existing `from
      validate_frontmatter import LAYER_VALUES` import still resolves to
      the full, correct 19-value set post-conversion — proving the
      downstream import chain (`ticket_field_values.py` →
      `ingest.py`/`done_checker_static.py`) is unaffected.
- [ ] A real test/direct run confirms the full existing ~1135-ticket corpus
      still passes `validate_frontmatter.py`'s layer check with zero new
      failures — this is the one action in this ticket with real blast
      radius (get it wrong and every future ticket close could start
      failing `check_frontmatter_valid` spuriously); verify explicitly, do
      not just assume the seed data is complete.
- [ ] `CLAUDE.md`'s Ticket Format section has a Layer-registry paragraph
      mirroring the Tags-allowlist paragraph.

## Related Tickets
- Parent epic: TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC
- Depends on: TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM (DONE — this ticket
  builds on `tools/ticket_field_values.py`'s existing live import of
  `LAYER_VALUES`)
- Blocks: TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL,
  TCK-20260718-CANONICAL-ENUM-DOCS-UPDATE (both need the final,
  registry-backed mechanism to exist/document before proceeding)
- Prior art / template: `tools/tag_registry.py`,
  `docs/guidelines/tag_registry.jsonl`,
  `docs/guidelines/tag_taxonomy.md`

## Related Docs
- tools/tag_registry.py (template)
- docs/guidelines/tag_taxonomy.md
- CLAUDE.md
- docs/plans/agent_ops_dashboard/proposal_canonical_ticket_field_enums.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/validate_frontmatter.py
- tools/tag_registry.py (read-only template reference)
- tools/ticket_field_values.py (verify, likely no edit needed)
- tests/tools/test_validate_frontmatter.py
- CLAUDE.md

## Assumptions / Open Questions
None outstanding — the design decision (single-value, no category field,
seed with current 19 values, preserve import surface) was specified
explicitly by the user; this ticket implements it, not re-litigates it.

## Implementation Notes

Same execution-context deviation as the rest of this epic (no Agent tool
access — every phase executed directly, self-flagged per established
precedent). This ticket was inserted mid-epic per an explicit user design
change ("I think layer can be added if follow the right process and files,
similar to tag") received while `TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP`
was finishing — that ticket was left uninterrupted, and this one, plus a
`SEQUENCE.md`/epic Related-Tickets update and a `CANONICAL-ENUM-DOCS-UPDATE`
scope amendment, were done immediately after.

Read `tools/tag_registry.py` in full as the template. Created
`tools/layer_registry.py` — structurally identical (append-only JSONL,
`load_registry`/duplicate-detection, CLI `add`/`list`) but with two
deliberate differences: no `category` field (Layer has no taxonomy split —
it IS the subsystem-topic dimension), and a new `layer_values()` helper
returning the registry as a `frozenset` (the shape
`tools/ticket_field_values.py`'s other canonical enums already use).
Seeded `docs/guidelines/layer_registry.jsonl` with exactly the 19 original
`LAYER_VALUES` via the real `add_layer()` API (not hand-written JSONL),
each with a real note — confirmed the seeded set is byte-identical to the
original hardcoded set via a dedicated test
(`test_layer_values_matches_real_seeded_registry`, run against the live
repo registry, no fixture override).

Converted `tools/validate_frontmatter.py`'s `LAYER_VALUES` from a hardcoded
`set` literal to `_layer_values()` (imported from `layer_registry.py`) —
the importable name is unchanged, so `tools/ticket_field_values.py`'s
existing `from validate_frontmatter import LAYER_VALUES` needed **zero
edits** and was confirmed still correct via its own existing identity test
(`test_layer_values_is_imported_not_duplicated`) plus the existing
anti-drift value test (`test_enum_values_layer`) — both re-run and still
passing unmodified.

**Blast-radius verification** (the one action in this ticket with real
risk, called out explicitly in its own AC): ran `validate_file` against the
full corpus (`tickets/{done,inprogress,todos}/`, 1190 files) both before
and after the conversion (via `git stash` on just `validate_frontmatter.py`
to get the true "before" state). Both runs found **exactly the same 14
layer-related errors** — pre-existing corpus drift using layer values
(`social`, `infrastructure`, `content`) that were never valid under the
original hardcoded set either. Zero new failures introduced by this
conversion, proven by direct before/after comparison, not assumed. These 14
are explicitly out of this ticket's scope (a mechanism change, not a data
cleanup) and are not touched.

Added `CLAUDE.md`'s Layer-registry paragraph, mirroring the Tags-allowlist
paragraph's structure, plus a short summary paragraph distinguishing
`layer`/`tags` (both registry-backed, differ in cardinality/categorization)
from `## Tier`/`## Status`/`## Priority` (ticket-body fields, a separate
validation mechanism entirely — `tools/ticket_field_values.py`).

## Test Summary

- `python3 -m pytest tests/tools/test_layer_registry.py -v` — 18/18
  passing (canonical-form checks, registry I/O, `add_layer`
  append-only/duplicate-rejection, `check_layers_registered`,
  `layer_values()` against both a fixture and the real live-seeded
  registry).
- `python3 -m pytest tests/tools/test_layer_registry.py
  tests/tools/test_validate_frontmatter.py tests/tools/test_ticket_field_values.py
  tests/tools/test_add_frontmatter_tickets.py tests/tools/test_status_drift_check.py
  tests/tools/test_done_checker_static.py tests/tools/test_tag_registry.py -q` —
  235/235 passing.
- `python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py
  tests/tools/test_agent_ops_dashboard_api.py -q` — 35/35 passing; direct
  import confirms `src.api.agent_ops_dashboard.main.app` still imports
  cleanly.
- CLI smoke test: `python3 tools/layer_registry.py list` (19 entries,
  correctly formatted) and `python3 tools/layer_registry.py add testlayer
  --note "smoke test" --root <tmpdir>` (exit 0, correct confirmation
  message) both verified directly.
- **Genuine before/after corpus comparison** (the ticket's own
  highest-risk AC): `git stash push -- tools/validate_frontmatter.py`,
  re-ran the full-corpus `validate_file` scan against the pre-conversion
  state — 14 layer errors. `git stash pop`, re-ran against the
  post-conversion state — the same 14 errors, byte-identical file list.
  Zero regressions, proven by direct comparison rather than a single
  post-hoc scan.

## Files Changed
- tools/layer_registry.py (new)
- docs/guidelines/layer_registry.jsonl (new, seeded with 19 entries)
- tools/validate_frontmatter.py (`LAYER_VALUES` now computed from the
  registry; importable name/surface unchanged)
- tests/tools/test_layer_registry.py (new, 18 tests)
- CLAUDE.md (new Layer-registry paragraph + Tier/Status/Priority summary
  paragraph)

## Completion Summary
All acceptance criteria met: `docs/guidelines/layer_registry.jsonl` exists,
seeded with exactly the original 19 `LAYER_VALUES`, each with a real note;
`tools/layer_registry.py` structurally mirrors `tag_registry.py` (minus the
category dimension, which doesn't apply to Layer); `LAYER_VALUES` is now
registry-backed with the import surface fully preserved, confirmed via
existing identity/value tests that needed no changes; a genuine before/after
full-corpus comparison (not a single post-hoc scan) proves zero new
validation failures; `CLAUDE.md` documents the new mechanism. This ticket
was a pure mechanism conversion — the 14 pre-existing, unrelated layer-value
drift errors found during blast-radius verification are explicitly out of
scope and untouched.
