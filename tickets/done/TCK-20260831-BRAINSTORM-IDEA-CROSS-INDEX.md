---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX
phase: done
date: 2026-08-31
tags: [architecture, content]
---

# TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX

## Title
Generate `docs/brainstorm/idea_index.json` — a per-idea cross-document index across the Atlas, Schema
Registry, Merit Scorecard, and Wiring Map, plus the owning milestone

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary

Researching a single design idea today requires manually grepping up to 5 separate documents by idea
number: the Feature Atlas (`id="idea-N"`), the Schema Registry (`id="schema-N"`, only for the ~30 ideas
introducing new durable state), the Merit Scorecard (idea number appears in a `<span class="num">` but
the containing `<tr>` has no anchor id — not currently link-through-able at all), the Wiring Map ("Idea
N" prose mentions scattered across rows with no dedicated per-idea anchor), and the owning M1-M9
milestone epic (only derivable by reading each epic doc's own `**Source:**` idea list). This ticket
builds a generated, machine- and human-readable index closing that gap for the three documents where a
clean 1:1 anchor exists, plus milestone ownership — without inventing anchors where the underlying
document structure genuinely doesn't support one.

## Scope

- New script `tools/generate_brainstorm_idea_index.py`, following the same generator pattern already
  established by `tools/generate_registry.py`: parses the real anchor/id conventions already present in
  `rpg_feature_atlas.html` (`id="idea-N"`), `rpg_expected_schemas.html` (`id="schema-N"`), and
  `design_merit_scorecard.html` (after this ticket adds `id="score-N"` — see below), plus each M1-M9
  epic doc's `**Source:**` idea-number list, and writes `docs/brainstorm/idea_index.json`.
- Add `id="score-N"` to each of the Merit Scorecard's 65 idea rows (`<tr>` elements in the Full
  Scorecard table) — the one small content-structure addition this ticket makes, since the scorecard
  currently has no per-row anchor at all and the cross-index is not genuinely useful for that document
  without one. Pure attribute addition, no visible/rendered change.
- Add a `Makefile` target (`brainstorm-idea-index`) mirroring the existing `docs-registry` target's
  shape, so the index can be regenerated on demand after a future brainstorm-doc edit.
- `idea_index.json` includes a `_meta` key documenting its own schema and regeneration command, matching
  the self-documenting convention `docs/REGISTRY.yaml` already uses.

## Out of Scope

- Adding per-idea anchors to `rpg_simulation_wiring_map.html`. Confirmed (`investigation.md`) that
  ideas are referenced there as scattered prose mentions across rows that don't map cleanly 1:1 to a
  single row per idea (an idea can span multiple Lifecycle Arc transitions, e.g. idea 17 touches both
  T6 and T7). Retrofitting real anchors would mean restructuring the document, not just adding
  attributes — out of scope per the same reasoning that kept the Wiring Map out of
  `TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT`'s scope. The index records a text-search hint (raw
  mention count) for this document instead of a fake or misleading anchor link.
- Idea 66: included in the Atlas-anchor and milestone fields (it has `id="idea-66"` and a clear M8/M2
  gate relationship already documented in the roadmap), but has no Scorecard or Schema Registry entry
  by design — `design_merit_scorecard.html` explicitly left it unscored (added after the original
  65-idea pass), and this ticket does not change that.
- Any change to the *content* of any of the four source documents beyond the one `id="score-N"`
  attribute addition to the Scorecard.
- Wiring this index into `search_docs`/the knowledge-index pipeline, or building a UI/page that
  consumes it — this ticket produces the data file and its generator only.

## Acceptance Criteria

- `docs/brainstorm/idea_index.json` exists, contains exactly 66 idea entries (1-66), each with:
  `atlas_anchor` (always present), `schema_anchor` (present only for ideas with a real `id="schema-N"`
  in the Schema Registry, else `null`), `scorecard_anchor` (present for ideas 1-65, `null` for 66),
  `wiring_map_mentions` (integer count, may be 0), `milestone` (M1-M9, or `null` for none).
- Every `atlas_anchor`/`schema_anchor`/`scorecard_anchor` value is verified to actually resolve to a
  real anchor id present in the corresponding file at generation time — not asserted, checked.
- `design_merit_scorecard.html` renders identically (visually) before/after — verified via `html.parser`
  parse plus a diff showing only `id="score-N"` attribute insertions, no other change.
- `make brainstorm-idea-index` regenerates the file idempotently (running it twice produces byte-identical
  output).
- Milestone assignment for all 65 originally-scoped ideas matches each epic doc's own `**Source:**`
  line, cross-checked directly, not retyped from memory.

## Related Tickets
- `TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT` (done) — prior ticket in this initiative; established
  that the Wiring Map has no equivalent blob problem, and this ticket now separately establishes it also
  has no clean per-idea anchor structure, for a different (but related) reason.

## Related Docs
- `docs/brainstorm/rpg_feature_atlas.html`, `rpg_expected_schemas.html`, `design_merit_scorecard.html`,
  `rpg_simulation_wiring_map.html` — the four source documents.
- `docs/plans/rpg_design_roadmap/rpg_m{1-9}_*.md` — milestone-ownership source (`**Source:**` lines).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX/{investigation,plan,test_plan}.md`

## Related Code Areas
- N/A — `docs/`/`tools/`/`Makefile` only, no `src/` change.

## Assumptions / Open Questions
- `id="score-N"` was chosen (not e.g. `id="idea-N"`) to avoid any collision with the Atlas's own
  `idea-N` anchor convention, in case both pages are ever combined or cross-linked directly.
- Milestone ownership for M7/M8/M9 is recorded as `null` — those three epics are audits/oversight
  spanning all ideas, not owners of a specific idea subset, confirmed by their own `**Source:**` lines
  citing process documents, not idea numbers.

## Implementation Notes
Added `id="score-N"` to the Merit Scorecard's 65 idea rows first (pure attribute insertion, verified via
diff to touch nothing else). Wrote `tools/generate_brainstorm_idea_index.py` following
`tools/generate_registry.py`'s established generator shape.

One real bug caught during implementation, not assumed away: the initial version grepped the Atlas for
literal `id="idea-N"` text and found zero matches for all 66 ideas — those anchors are generated
client-side by `renderCard`'s regex against each card's `title` field at render time and never exist as
literal text in the static HTML source. Fixed by parsing the `card-sections-data` JSON block (itself a
direct product of `TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT`, confirming the value of sequencing that
ticket first) and replicating the exact same `^(\d+)\.` regex render logic uses, rather than grepping
for text that was never written to disk.

A second bug: M1's epic doc's `**Source:**` line has different phrasing from the other 8 epics
(`"...Rev 60+ (Design Ideas 1, 3, ..., 42), cross-checked against..."` — parenthesis-terminated, not
period-terminated), which silently produced zero M1 entries on the first run. Caught because the
generator prints milestone counts on every run and M1 was visibly absent; fixed the terminator regex to
accept either `.` or `)`.

## Test Summary
All checks in `test_plan.md` ran and passed:
- 66 entries, idea numbers 1-66, no gaps/duplicates.
- Every non-null anchor (66 atlas, 30 schema, 65 scorecard) independently re-verified against its real
  source file — not just trusted from the generator's own internal check.
- Milestone counts match `investigation.md`'s directly-grepped totals exactly: M1=20, M2=16, M3=5, M4=12,
  M5=8, M6=4, idea 66="M8" — 66 total, none unaccounted for.
- Idea 66 edge case confirmed directly: `schema_anchor` present (idea 66 does have a Schema Registry
  section), `scorecard_anchor` null (never scored), `milestone: "M8"`.
- Idempotency: ran the generator twice, `ideas` array byte-identical between runs (only `_meta.generated`
  differs, matching the same precedent `docs/REGISTRY.yaml`'s own header timestamp already sets).
- `design_merit_scorecard.html`: `html.parser` parses cleanly; diff shows exactly 65 `id="score-N"`
  insertions, nothing else.
- `tests/tools/test_dashboard_makefile_targets.py`: 5 passed, confirms the new `.PHONY` entry didn't
  break the existing set-based phony-target check or any pinned recipe snapshot.
- `make -n brainstorm-idea-index` / `make brainstorm-idea-index`: both resolve `$(PYTHON3)` correctly
  and produce the expected output.

## Files Changed
- `tools/generate_brainstorm_idea_index.py` (new)
- `docs/brainstorm/idea_index.json` (new, generated)
- `docs/brainstorm/design_merit_scorecard.html` (`id="score-N"` added to 65 rows)
- `Makefile` (new `brainstorm-idea-index` target + `.PHONY` entry)

## Completion Summary
Built `docs/brainstorm/idea_index.json`, a generated per-idea cross-document index spanning the Atlas
(all 66 ideas), Schema Registry (30 ideas with real durable-state schemas), and Merit Scorecard (65
scored ideas, after adding the `id="score-N"` anchors it was missing entirely), plus milestone ownership
parsed directly from each M1-M9 epic doc. The Wiring Map was confirmed to have no reliable 1:1 per-idea
anchor structure and is represented by a mention-count hint instead of a fabricated anchor. Every
anchor value is independently verified against its real source file, not asserted. Two real bugs
(Atlas anchors don't exist as literal text; M1's Source-line phrasing differs from the other 8 epics)
were caught and fixed during implementation rather than silently producing a wrong or incomplete index.
