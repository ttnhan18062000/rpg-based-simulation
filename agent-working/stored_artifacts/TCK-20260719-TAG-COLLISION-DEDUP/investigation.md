---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260719-TAG-COLLISION-DEDUP
artifact_type: investigation
tags: [tagging, data-quality]
---

# Investigation: TCK-20260719-TAG-COLLISION-DEDUP

## Current Behavior

Full corpus scan (`tickets/{done,inprogress,todos}/` + `stored_artifacts/`,
via `tools/validate_frontmatter.py::extract_frontmatter`, 1352 distinct
tags currently in use) grouped by normalized form (`tag.lower().replace('_','-')`)
found 8 collision groups — same real-world meaning, multiple literal
spellings in the corpus:

| Group (normalized) | Literal variants found (count) | Canonical target |
|---|---|---|
| simulation-quality | `simulation-quality` (195), `simulation_quality` (28) | `simulation-quality` (already registered) |
| grand-strategy | `grand-strategy` (2), `grand_strategy` (4) | `grand-strategy` (newly registered this ticket) |
| feature-flag(s) | `feature-flag` (1), `feature_flag` (3) | `feature-flags` (already registered, **plural** — a 3rd literal spelling this scan's normalization initially missed since singular/plural is a different axis than underscore/hyphen; found by cross-checking `tag_registry.jsonl` directly) |
| dungeon-crawl | `dungeon-crawl` (1), `dungeon_crawl` (1) | `dungeon-crawl` (newly registered this ticket) |
| grade-thresholds | `grade-thresholds` (1), `grade_thresholds` (1) | `grade-thresholds` (newly registered this ticket) |
| p0 (as a tag) | `p0` (8), `P0` (2) | **removed entirely** — duplicates `## Priority` |
| p1 (as a tag) | `p1` (7), `P1` (7) | **removed entirely** — duplicates `## Priority` |
| p2 (as a tag) | `p2` (16), `P2` (4) | **removed entirely** — duplicates `## Priority` |

Cross-checked every group against `tools/tag_registry.py::canonical_form_violation()`,
which already prescribes the exact fix:
- Underscore/lowercase-form violations → rename to the hyphenated canonical
  form (`tag.lower().replace('_', '-')`).
- `p0`/`p1`/`p2` (any case) are explicitly `FORBIDDEN_PRIORITY_TAGS` —
  `canonical_form_violation()` returns "duplicates the dedicated Priority
  field — remove it", not a rename target. `docs/guidelines/tag_taxonomy.md`'s
  own "Forbidden Tags" section already documents this policy; the corpus
  simply has 3 pre-cutoff/pre-enforcement tickets that were never
  retroactively fixed.

## Registry State (before this ticket)

`docs/guidelines/tag_registry.jsonl` (49 entries) already contains
`simulation-quality` (category `subsystem-topic`, note explicitly
anticipating this exact fix: "seed: canonical form for the SimQ subsystem —
the live corpus only uses the non-canonical 'simulation_quality' (2
tickets, already flagged separately)") and `feature-flags` (plural,
`subsystem-topic`). It does NOT contain `grand-strategy`, `dungeon-crawl`,
or `grade-thresholds` in any form — these 3 need fresh registration via
`tools/tag_registry.py add`.

Category determination (checked each tag's actual usage context, not
assumed):
- `grand-strategy`: `TCK-20260322-GRAND_STRATEGY.md`'s Title is "Grand
  Strategy: Faction Wars, Territory Conquest, and Siege Mechanics" — a
  gameplay/engine subsystem a player/the simulation would recognize →
  `subsystem-topic`.
- `dungeon-crawl`: used on SimQ calibration tickets referring to a world/
  scenario archetype (`TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG.md`:
  "ECONOMY and COGNITION score 0 events in dungeon_crawl at every tick
  count") — a content/subsystem concept, same family as `simulation-quality`
  → `subsystem-topic`.
- `grade-thresholds`: used on SimQ scoring/calibration tickets
  (`TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY.md`), same SimQ-subsystem family
  as the already-registered `simulation-quality` → `subsystem-topic`.

## Mechanics/Engine Constraints

None — this is pure ticket/artifact metadata (frontmatter `tags:`), no
simulation code, no Mechanics Bible or Engine Contract overlap.

## Parity Ledger Overlap

None — tag metadata is outside the parity ledger's scope (source-vs-doc
behavioral parity), confirmed via `docs/parity_ledger/` grep (no entries
reference `tags:` or tag registry mechanics).

## Prior Work

- `docs/guidelines/tag_taxonomy.md`'s original corpus review (before the
  registry existed) already found "at least 19 confirmed format-duplicate
  groups (e.g. `p0`/`P0`, `phase-5`/`phase5`)" and deliberately deferred
  fixing them — this ticket picks that exact deferred item back up, now
  under direct user request, for the 8 groups found in today's fresh scan
  (a subset of that original 19; phase-N tags were not found duplicated in
  this scan — `is_phase_milestone_tag()`'s pattern-based recognition
  already handles any-N transparently, no registry entry needed per tag).
- `docs/guides/ticket_reporting.md`'s Pillar 1 section documents the
  `simulation_quality` finding from `TCK-20260706-TAG-REPORT-TOOL`'s original
  live snapshot, explicitly noting retagging was "out of scope for the
  registry ticket, same as it was for the original tag-report ticket" —
  this ticket is the first to actually close that loop.
- `TCK-20260718-LAYER-REGISTRY-CONVERSION` and `TCK-20260718-STATUS-DRIFT-REPAIR`
  (both closed 2026-07-18, read in full) establish this project's precedent
  for legacy-file scope decisions: `STATUS-DRIFT-REPAIR` excluded files
  using a genuinely different naming CONVENTION (`resource_v2_*.md`, not
  `TCK-*.md`), not files merely dated before a cutoff. None of the 8
  collision groups in this ticket touch any `resource_v2_*`-style legacy
  file — every hit is a standard `TCK-*.md` ticket or its `stored_artifacts/`
  companion file. This ticket's fix (a one-line `tags:` list edit) does not
  retrofit any new section/structure onto old tickets the way, e.g., adding
  a missing `## Completion Summary` would — so the usual "don't force new
  conventions onto old-format tickets" reasoning does not apply here.
  **Scope decision: fix every occurrence found, regardless of date**,
  including the 3 known pre-2026-07-04 SIMQ-UPLIFT tickets using
  `simulation_quality` that `ticket_reporting.md` previously left alone —
  the user's request was "fix them," not "fix them going forward," and a
  tag-spelling correction carries none of the structural-retrofit risk that
  motivated the format-based exclusions in the two cited precedent tickets.

## Risks and Open Questions

- `p0`/`p1`/`p2` removal shrinks 3 tickets' `## Priority`-adjacent tag lists
  by exactly one entry each in some cases, to potentially an empty list —
  confirmed the correct empty-list representation is `tags: []` (matches
  `extract_frontmatter`'s own parsing and every existing empty-tag-list
  ticket in the corpus), not an omitted `tags:` key.
- None of the 8 groups' target canonical forms collide with any OTHER
  already-registered tag under a different meaning (checked each of the 4
  newly-registered forms against the full existing registry list — no
  near-duplicates found beyond the ones already accounted for above).

## Anti-Drift Hazards

- Must not touch any tag NOT in one of the 8 identified collision groups —
  a ticket's other tags (e.g. `TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG.md`
  also has `economy`, `cognition`, `world_spec`, `archetype` — `world_spec`
  looks superficially similar to this ticket's scope but was NOT found as a
  collision group in the corpus scan, since no `world-spec` hyphenated
  variant exists anywhere — leave `world_spec` untouched, out of scope).
- Must not re-order or reformat any file's `tags:` list beyond the specific
  rename/removal edit — preserve existing list order for all untouched
  entries.
- Registering the 3 new tags must use the real `tag_registry.py add` API
  (append-only, refuses duplicates) — never a hand-written JSONL line.
