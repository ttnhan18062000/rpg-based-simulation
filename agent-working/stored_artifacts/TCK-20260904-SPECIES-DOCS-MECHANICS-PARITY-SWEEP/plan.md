---
status: active
layer: mechanics
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-DOCS-MECHANICS-PARITY-SWEEP
artifact_type: plan
tags: [content, schema]
---

# Plan — TCK-20260904-SPECIES-DOCS-MECHANICS-PARITY-SWEEP

1. Sweep all 5 listed `docs/mechanics/*.md` files for real "race" hits; update live-behavior
   prose and stale code citations (`RaceDefinition` → `SpeciesDefinition`, `race_id` →
   `species_id`, `race_relations` → `species_relations`); leave historical TCK-ID citations
   unchanged.
2. Map every "race" hit in the 7 listed `docs/parity_ledger/*.yaml` shards to its exact entry ID
   (script-driven, not spot-checked). For each entry, decide: update via
   `tools/parity_ledger_writer.py::write_entry()` (never raw YAML edit) if it's a live citation to
   now-renamed code/tests, or leave unchanged if blocked by a pre-existing, unrelated schema rule
   (P0 priority + null test_path) — document the exact reason per entry, not silently skip.
3. Grep the remaining `docs/` corpus (narrowed from the epic's 81-file candidate list, excluding
   `docs/archive/` and the already-covered mechanics/parity_ledger paths); for each file with a
   hit, read enough context to classify: live/active doc describing current code (fix), frozen
   brainstorm/historical investigation record (leave, matching the epic's own precedent), unrelated
   concurrency "race" terminology (leave), or a pre-existing legacy-checklist stub referencing a
   nonexistent file layout (leave, cross-verified via `docs/compliance/checklist.md`).
4. Rename idea 37's own name citations ("Race Relations" → "Species Relations") wherever it
   appears as the idea's literal name in non-frozen docs — the epic's explicit Scope item 3.
5. Run `tools/validate_frontmatter.py docs/` and cross-reference every touched file against its
   output — confirm zero new violations introduced, not just that the tool exits.
6. Run `tools/parity_index.py build` + `health` to confirm both commands succeed after all edits.
7. Verify every parity-ledger `test_path` I wrote/changed actually exists and passes, by running
   it directly — never citing an unverified test.
