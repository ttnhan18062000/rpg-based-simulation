---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260719-TAG-COLLISION-DEDUP
artifact_type: plan
tags: [tagging, data-quality]
---

# Implementation Plan — TCK-20260719-TAG-COLLISION-DEDUP

## Summary

Fix 8 tag-collision groups across the ticket/artifact corpus: rename 5
underscore-form tags to their canonical hyphenated form (registering 3 new
canonical forms that don't yet exist in the registry; the 4th,
`simulation-quality`, and `feature-flags`, are already registered), and
remove 3 forbidden-priority-duplicate tag groups (`p0`/`P0`, `p1`/`P1`,
`p2`/`P2`) entirely. Update the two docs that describe this as a known,
deferred issue. Spot-check today's three closed epics for stale doc
references.

## Steps

### Step 1 — Register the 3 missing canonical tag forms

Real `tools/tag_registry.py add` calls (not hand-written JSONL):
```
python3 tools/tag_registry.py add grand-strategy --category subsystem-topic --note "Strategic layer: faction wars, territory conquest, siege mechanics (TCK-20260322-GRAND_STRATEGY)"
python3 tools/tag_registry.py add dungeon-crawl --category subsystem-topic --note "SimQ calibration world archetype (pure-combat, no town/service infrastructure) — distinct from sandbox_world"
python3 tools/tag_registry.py add grade-thresholds --category subsystem-topic --note "SimQ pillar-score grading/decay threshold tuning"
```

### Step 2 — Rename underscore-form tags to canonical (5 groups)

For each file found in Investigation with a non-canonical literal tag,
edit its frontmatter `tags:` list, replacing only the one matching entry:
- `simulation_quality` → `simulation-quality` (28 occurrences across ~25 files)
- `grand_strategy` → `grand-strategy` (4 occurrences, 3 files — 1 ticket + 2 stored_artifacts companions)
- `feature_flag` → `feature-flags`, `feature-flag` → `feature-flags` (4 occurrences total, ~3 files)
- `dungeon_crawl` → `dungeon-crawl` (1 occurrence, 1 file)
- `grade_thresholds` → `grade-thresholds` (1 occurrence, 1 file)

If a file's `tags:` list already contains the canonical form alongside the
non-canonical one (duplicate after rename), collapse to a single entry —
check for this case explicitly per file, don't assume it can't happen.

### Step 3 — Remove forbidden-priority tag groups (3 groups)

For each file found in Investigation with `p0`/`P0`/`p1`/`P1`/`p2`/`P2` as
a tag, remove that one entry from the `tags:` list. If the list becomes
empty, write `tags: []`, not an omitted key.

### Step 4 — Update docs

- `docs/guidelines/tag_taxonomy.md`: the "at least 19 confirmed
  format-duplicate groups" framing (Purpose section) still accurately
  describes the *original* pre-registry review — leave that historical
  claim as-is (it's dated context, not a live claim), but confirm no
  language elsewhere in the file implies these specific 8 groups are still
  outstanding.
- `docs/guides/ticket_reporting.md`: Pillar 1's "Legacy / historical
  context" section explicitly says retagging the 2 `simulation_quality`
  tickets was "out of scope for the registry ticket" — update this note to
  reflect that TCK-20260719-TAG-COLLISION-DEDUP has now closed that gap
  (and found more instances than the original 2-ticket count).

### Step 5 — Spot-check today's three epics' docs

Grep for any obviously stale claim in
`docs/observability/agent_ops_dashboard_contract.md`,
`docs/guides/agent_ops_dashboard.md`, `docs/guides/ticket_reporting.md`
(Pillar 2 section), `CLAUDE.md` referencing anything the
canonical-field-enums/stats-board/glossary-tooltips epics changed — this is
a verification pass (each epic already had its own docs-update child
ticket), not a redo. Fix only if something concrete and stale is found.

### Step 6 — `make knowledge-index-update`

Required per this project's After-Work rule since `docs/` files change.

## Scope Guards

- Do not touch any tag outside the 8 identified collision groups.
- Do not reorder or reformat any file's `tags:` list beyond the specific
  rename/removal.
- Do not re-audit or redo the three epics' own docs-update work — spot-check
  only.
- Do not touch `resource_v2_*.md`-style pre-TCK-naming legacy files (none
  are affected by this ticket's 8 groups, confirmed in Investigation — this
  guard exists in case a re-scan surfaces one that was missed).

## Dependency Map

Steps 1 → 2/3 (renames need the target tags registered first, so
`check_tags_registered`-style validation would pass if re-run). Steps 2, 3
independent of each other. Step 4 independent of 1-3 (doc text, not data).
Step 5 independent. Step 6 last (after all `docs/` edits land).

## Acceptance Criteria Map

- [ ] `grand-strategy`, `dungeon-crawl`, `grade-thresholds` all appear in
      `python3 tools/tag_registry.py list` output (Step 1).
- [ ] Zero files in the corpus still use `simulation_quality`, `grand_strategy`,
      `feature_flag`/`feature-flag` (singular), `dungeon_crawl`, or
      `grade_thresholds` as a literal tag (Step 2, verified by a fresh
      corpus re-scan).
- [ ] Zero files still have `p0`/`P0`/`p1`/`P1`/`p2`/`P2` in any `tags:`
      list (Step 3, verified by the same re-scan).
- [ ] `docs/guides/ticket_reporting.md` no longer describes the
      `simulation_quality` retag as out-of-scope/deferred (Step 4).
- [ ] `make knowledge-index-update` run successfully after all doc edits
      (Step 6).

## Anti-Drift Notes

The corpus-wide re-scan in Verify must use the exact same technique as
Investigation's original scan (`extract_frontmatter` + normalize +
group-by-count) so the "before" and "after" numbers are directly
comparable — not a different, looser or stricter check that could produce
a false sense of completeness.
