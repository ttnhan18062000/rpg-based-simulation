---
status: active
layer: guidelines
authority: P2
audience: developer
maturity: proposal
date: 2026-07-19
tags: [tagging, data-quality]
---

# Proposal: Fix duplicate-meaning tags across the ticket/artifact corpus

**Maturity: PROPOSAL** — direct user request: "I found that there some
duplicated meaning tags, for example: simulation-quality and
simulation_quality, fix them, and also update all related documents for the
recent works."

## Background investigation (already done, feed this to Investigate — do not redo)

Full corpus scan (`tickets/{done,inprogress,todos}/` +
`stored_artifacts/`, via `tools/validate_frontmatter.py::extract_frontmatter`,
1352 distinct tags in current use) grouped by normalized form
(lowercase, `_`→`-`) to find literal-tag variants sharing one real meaning.
Found 8 collision groups — cross-checked every one against
`tools/tag_registry.py::canonical_form_violation()`, which **already
prescribes the exact correct fix for each case** (this is existing,
authoritative logic — do not re-derive policy, just apply it):

| Group | Variants found (count) | `canonical_form_violation()` verdict |
|---|---|---|
| simulation-quality | `simulation-quality` (195, canonical/registered), `simulation_quality` (28) | underscore form → use `simulation-quality` |
| grand-strategy | `grand-strategy` (2), `grand_strategy` (4) | underscore form → use `grand-strategy` |
| feature-flag | `feature-flag` (1), `feature_flag` (3) | underscore form → use `feature-flag` |
| dungeon-crawl | `dungeon-crawl` (1), `dungeon_crawl` (1) | underscore form → use `dungeon-crawl` |
| grade-thresholds | `grade-thresholds` (1), `grade_thresholds` (1) | underscore form → use `grade-thresholds` |
| p0 | `p0` (8), `P0` (2) | **forbidden priority tag → remove entirely** (duplicates the ticket's own `## Priority` body field; not a spelling fix) |
| p1 | `p1` (7), `P1` (7) | same — remove |
| p2 | `p2` (16), `P2` (4) | same — remove |

Two distinct fix types, both already codified in `canonical_form_violation()`:
1. **Rename** (5 groups: simulation-quality, grand-strategy, feature-flag,
   dungeon-crawl, grade-thresholds) — replace the underscore literal with
   the hyphenated canonical form in the ticket/artifact's frontmatter
   `tags:` list. Only `simulation-quality` is currently registered in
   `registries/tag_registry.jsonl`; the other 4 canonical forms are
   not registered at all (0 uses of the canonical spelling anywhere in the
   corpus) — Investigate must decide whether to register each canonical
   form via the real `tag_registry.py add` API before or as part of
   retagging (the registry-membership check would otherwise reject the
   rename target), following the exact same "real API call, never a
   hand-written JSON line" discipline `TCK-20260718-GLOSSARY-REGISTRY`
   established earlier today.
2. **Remove** (3 groups: p0/P0, p1/P1, p2/P2 as tags) — these tags
   duplicate the ticket's dedicated `## Priority` body field
   (`P0`/`P1`/`P2`/`P3`, hard-validated since today's
   `TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC`). `canonical_form_violation()`
   already says "remove it," not "rename it" — do not invent a rename
   target for these three groups.

**Legacy-scope note** (per this project's own established precedent —
`tag_report.py`'s pre-taxonomy skip rule, and this session's own repeated
"don't retrofit new conventions onto genuinely old tickets" pattern from
the Layer-registry and Status-drift tickets earlier today): most hits
(dated before `TAG_TAXONOMY_EFFECTIVE_DATE` = 2026-07-04) are pre-taxonomy.
**However**, 3 files under `stored_artifacts/TCK-20260704-SIMQ-*` use
`simulation_quality` (non-canonical) with a `ticket_id` dated exactly
2026-07-04 or later — i.e. **inside** the taxonomy's enforcement window,
not legacy-exempt. Investigate must re-derive the exact legacy/in-scope
split itself (dates shift as the corpus grows) rather than trusting this
proposal's snapshot, and should make an explicit, documented call on
whether pre-taxonomy files get touched too (the user's request — "fix
them" — reads as wanting the corpus actually clean, not just the
in-scope slice; this is a real scope decision, not free to assume either
way without deciding and stating it).

## User's explicit decisions (already made, do not re-ask)

1. Fix the duplicate-meaning tags — "simulation-quality and
   simulation_quality" was given as one example, not the full scope; the
   full collision-group scan above is the real scope.
2. Update all related documents for the recent works — this proposal's own
   scope (tag-corpus cleanup docs) plus a sanity pass confirming the three
   epics closed earlier today/yesterday
   (`TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC`,
   `TCK-20260718-AGENTOPS-STATS-BOARD-EPIC`,
   `TCK-20260718-GLOSSARY-TOOLTIPS-EPIC`) left no stale doc references —
   each of those epics already had its own dedicated docs-update child
   ticket, so this is a verification pass, not a redo.

## Architectural constraints

- Tag registration must go through the real `tools/tag_registry.py add`
  CLI/API (append-only, refuses duplicates) — never a hand-written JSONL
  line, per this repo's own established rule and today's precedent.
- Retagging a ticket/artifact file changes only its frontmatter `tags:`
  list — no other section, no reformatting, no unrelated edits per file.
- `docs/guidelines/tag_taxonomy.md`'s original corpus review already noted
  "at least 19 confirmed format-duplicate groups (e.g. p0/P0,
  phase-5/phase5)" as a known, deliberately deferred cleanup at the time
  the registry was created — this proposal is picking that exact deferred
  item back up, now under explicit user request. Update that doc's framing
  once the cleanup lands (from "known, deferred" to "resolved" or similar),
  don't leave it describing a now-stale future state.
- `docs/guides/ticket_reporting.md`'s Pillar 1 section explicitly documents
  the `simulation_quality`/`simulation-quality` duplicate as a known,
  out-of-scope-at-the-time finding from the original tag-report ticket —
  update this once fixed, don't leave a stale "known issue, not fixed"
  note describing something that's now fixed.
- After any frontmatter change to files under `docs/`: `make
  knowledge-index-update`. `docs/REGISTRY.yaml` regenerates automatically
  per this project's Finalize step — do not hand-edit it.

## Concerns for Comprehend/Investigate to turn into ticket scope

1. Register the 4 missing canonical tag forms (`grand-strategy`,
   `feature-flag`, `dungeon-crawl`, `grade-thresholds`) via real
   `tag_registry.py add` calls with accurate `--category`/`--note` values
   (check `docs/guidelines/tag_taxonomy.md`'s category definitions — likely
   all 4 are `subsystem-topic`, verify each individually rather than
   batch-assuming).
2. Rename every occurrence of the 5 underscore variants to their canonical
   hyphenated form across the corpus (both in-scope and legacy files, per
   the explicit scope decision Investigate must make and document).
3. Remove the 3 forbidden-priority tag groups (`p0`/`P0`, `p1`/`P1`,
   `p2`/`P2`) from every file's `tags:` list entirely — not renamed,
   removed, since `canonical_form_violation()` itself says so and the
   information is already captured by each ticket's dedicated `## Priority`
   body field.
4. Update `docs/guidelines/tag_taxonomy.md` and `docs/guides/ticket_reporting.md`
   per the Architectural Constraints above.
5. Verification: re-run the same corpus collision-group scan post-fix and
   confirm zero remaining collision groups (excluding any explicitly
   deferred as out-of-scope legacy, if Investigate makes that call)
   — mirroring the "re-run the real check, don't trust a prior claim"
   discipline this session used for every prior data-cleanup ticket today.
