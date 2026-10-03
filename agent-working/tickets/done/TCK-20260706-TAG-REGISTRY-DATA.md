---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260706-TAG-REGISTRY-DATA
phase: done
date: 2026-07-06
tags: [tagging, taxonomy, reporting]
---

# TCK-20260706-TAG-REGISTRY-DATA

## Title
Add an append-only tag registry data file; make ticket tag validation a hard allowlist against it

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Follow-up to `TCK-20260706-TAG-REPORT-TOOL`. User observed `tag_report.py`'s heuristic
categorization left most live tags `unclassified`, and asked for a durable, machine-readable tag
data file to (a) prevent near-duplicate-meaning tags (`calibrate` vs `calibration`), (b) support
adding new tags only — never updating/deleting — with a changelog, (c) have
`validate_frontmatter.py`'s tag validation actually check against that data, and (d) manage
category assignment as data too, since the current heuristic mostly failed to classify. User
explicitly asked to be consulted on ambiguous design points before implementation.

## Scope
- New `tools/tag_registry.py`: owns `docs/guidelines/tag_registry.jsonl` (append-only, one tag per
  line: `tag`, `category`, `added_date`, `note`), the canonical-form rule (extracted from
  `validate_frontmatter.py`), the taxonomy constants (`TAG_TAXONOMY_EFFECTIVE_DATE`,
  `FORBIDDEN_PRIORITY_TAGS`, `TAG_SYNONYM_MAP`, moved here), a 5th tag category (`meta-process`),
  `load_registry`/`is_tag_registered`/`is_phase_milestone_tag`/`add_tag`, and an `add`/`list` CLI.
- `tools/validate_frontmatter.py`: `_check_tags` gains a hard-allowlist registry-membership check
  (after canonical-form), threaded through as an optional `registry` parameter (backward compatible
  — omitting it preserves old behavior); `main()` loads the real registry for actual CLI/CI runs.
- `tools/tag_report.py`: `categorize_tag` becomes a direct registry lookup (phase-N by pattern,
  else registry's `category` field, else `unclassified`), replacing 3 hardcoded heuristic tag sets.
- Seed the registry (via the real `add` CLI, not a hand-written file) with every tag in use across
  the live post-cutoff `tickets/done/` corpus, each assigned a category backed by grepped ticket
  evidence (see stored_artifacts/.../investigation.md).
- Update `docs/guidelines/tag_taxonomy.md` (new Tag Registry section, 5th category, revised
  Enforcement/Purpose), `docs/guides/ticket_tagging.md` (5-category table, "Registering a New Tag"
  section), `docs/guides/ticket_reporting.md` (Pillar 1 detail refreshed for registry-based
  classification).
- New/updated tests: `tests/tools/test_tag_registry.py` (new), `tests/tools/test_tag_report.py`
  and `tests/tools/test_validate_frontmatter.py` (updated for the new registry-based behavior).

## Out of Scope
- Rewiring `tools/registry_query.py`'s `SEED_TAGS` to derive from this registry — disclosed
  follow-up opportunity, not built (touches `create-tickets.js`/`investigator.md`, larger blast
  radius than this ticket).
- Deciding whether `bug`/`feature`/`refactor`/`chore`/`repair` tags should be forbidden for
  duplicating the `## Type` field — flagged as an open question in `tag_taxonomy.md`, not decided.
- Retagging the 2 tickets still using non-canonical `simulation_quality` — disclosed, not fixed.

## Acceptance Criteria
- [ ] `docs/guidelines/tag_registry.jsonl` exists, append-only, seeded with every tag in live use.
- [ ] `tools/tag_registry.py add`/`list` CLI works; rejects duplicates, non-canonical tags, invalid
      categories, and `phase-milestone` as an addable category.
- [ ] `validate_frontmatter.py` rejects an unregistered (non-phase) tag on a post-cutoff
      ticket/artifact, with a message pointing at the `add` CLI.
- [ ] Re-running `validate_frontmatter.py tickets/done` after seeding produces the **same**
      violation count as an unmodified-tree baseline (`git stash` diff) — zero new regressions.
- [ ] `tools/tag_report.py`'s live run shows 0 unexpected `unclassified` tags after seeding.
- [ ] All new/updated tests pass; full `tests/tools/` regression shows no new failures.
- [ ] `docs/guidelines/tag_taxonomy.md`, `docs/guides/ticket_tagging.md`,
      `docs/guides/ticket_reporting.md` updated and consistent with the new model.

## Related Tickets
- TCK-20260706-TAG-REPORT-TOOL (the tool whose "mostly unclassified" output motivated this ticket)
- TCK-20260706-TICKET-REPORTING-GUIDE (doc this ticket also updates)
- TCK-20260704-TAG-TAXONOMY (original categories + forward-only enforcement cutoff)
- TCK-20260705-TAG-REGISTRY-QUERY (prior art for the same-package import pattern; also the source
  of the un-fixed `registry_query.py`/`create-tickets.js` `layer` bug, unrelated to this ticket)

## Related Docs
- docs/guidelines/tag_taxonomy.md
- docs/guides/ticket_tagging.md
- docs/guides/ticket_reporting.md

## Related Stored Artifacts
staging_artifacts/TCK-20260706-TAG-REGISTRY-DATA/{plan.md, investigation.md, test_plan.md}

## Related Code Areas
- tools/tag_registry.py (new)
- tools/validate_frontmatter.py
- tools/tag_report.py

## Assumptions / Open Questions
- Assumed "changelog" is satisfied by the append-only JSONL file's own git history, not a separate
  changelog file to design and keep in sync — matches this repo's existing `agent-monitoring/*.jsonl`
  append-only-log precedent.
- Assumed seeding should happen via the real `add` CLI (dogfooding it end-to-end for all 37 tags)
  rather than hand-writing the JSONL file directly.
- Two new tags (`reporting`, discovered only after re-running `tag_report.py` post-seed once the
  prior two tickets' own tags were in scope) required a second, smaller seed pass — disclosed in
  Implementation Notes, not hidden.
- `bug`-vs-`## Type` redundancy and the `registry_query.py` `SEED_TAGS` duplication are flagged as
  open follow-ups per Out of Scope, not resolved here.

## Implementation Notes
Implemented per plan.md's 8 steps:

1. **`tools/tag_registry.py`** (new): `docs/guidelines/tag_registry.jsonl` append-only data file;
   `ALL_CATEGORIES` (5) / `ADDABLE_CATEGORIES` (4, excludes `phase-milestone`); `canonical_form_violation`
   (extracted pure function); `load_registry`/`is_tag_registered`/`is_phase_milestone_tag`/`add_tag`;
   `add`/`list` CLI. Zero dependency on `validate_frontmatter.py` or `tag_report.py` (leaf module).
2. **Import direction**: `validate_frontmatter.py` imports constants + `canonical_form_violation` +
   `load_registry`/`is_tag_registered` from `tag_registry.py` and re-exports them, so every existing
   `from validate_frontmatter import FORBIDDEN_PRIORITY_TAGS`-style import kept working unchanged
   (confirmed: all 64 pre-existing tests passed without modification before any new tests were added).
3. **`validate_frontmatter.py`**: `_check_tags(filepath, fm, registry=None)` now does canonical-form
   then (if `registry is not None`) registry-membership. Threaded through `_validate_ticket`/
   `_validate_artifact`/`_validate_doc`/`_validate_archive`/`validate_file`/`validate_directory`.
   `main()` calls `load_registry()` (repo-root-relative, cwd-independent) and passes it through —
   real CLI/CI runs now enforce the hard allowlist.
4. **`tag_report.py`**: removed `PROCESS_SKILL_TAGS`/`QUALITY_ATTRIBUTE_EXAMPLE_TAGS`/
   `registry_query.SEED_TAGS` heuristics entirely. `categorize_tag(tag, registry)` is now a direct
   lookup; `build_tag_rows` threads the registry through; non-canonical diagnostic now calls
   `tag_registry.canonical_form_violation` instead of a local reimplementation.
5. **Seeding**: ran the real `add` CLI 36 times (one per live tag from investigation.md's
   evidence-based categorization), then discovered a 37th (`reporting`, used by the 2 tickets this
   very session's prior work created) only after re-running `tag_report.py` post-seed — registered
   it as `meta-process` in a second pass. Disclosed, not hidden: this is exactly the kind of gap the
   zero-regression verification step (next) is designed to catch.
6. **Verification**: `python3 tools/validate_frontmatter.py tickets/done` on the modified tree
   produced `FAIL: 185 violation(s) in 1046 file(s) checked`. `git stash` + the same command on the
   unmodified tree (with the seeded-but-untracked `tag_registry.jsonl` still present, harmlessly
   unused since the old `validate_frontmatter.py` doesn't import it) produced the **identical**
   `185` count. Confirmed via `grep "not in the tag registry"` on the modified-tree run: zero hits —
   every live tag is registered. The only 2 tag-related failures in both runs are the pre-existing
   non-canonical `simulation_quality` usages, unrelated to registration.
7. **Tests**: `tests/tools/test_tag_registry.py` (20 new), `tests/tools/test_tag_report.py`
   (updated: `categorize_tag`/`build_tag_rows` tests now pass an explicit in-memory registry),
   `tests/tools/test_validate_frontmatter.py` (7 new tests in `TestTagRegistryEnforcement`; all 57
   pre-existing tests in that file pass unmodified).
8. **Docs**: `tag_taxonomy.md` (Purpose revised, `Meta-Process` category + disambiguation rule
   added, new "Tag Registry" section, Enforcement revised to describe the 2-step check and cite the
   zero-regression result, disclosed-not-decided note on `bug`/`## Type` redundancy),
   `ticket_tagging.md` (5-category table, "Registering a New Tag" section), `ticket_reporting.md`
   (Pillar 1 classification table and legacy-context numbers refreshed: 1046 scanned, 29 included,
   37 tags, 0 unclassified). `make docs-registry` (1288 entries) and `make knowledge-index-update`
   (6 files re-embedded) both run successfully.

**Category assignment evidence** (full detail in investigation.md): every non-obvious tag
(`rollback`, `audit-trail`, `knowledge-store`, `stasis`, `resource-registry`, `root-cause`, `ai`,
`data-quality`, `determinism`) was grepped against its actual ticket usage before assigning a
category — not guessed from the tag name alone. Notably, `ai` was reclassified from an initial
`subsystem-topic` guess to `meta-process` after evidence showed this repo's `ai` tag/layer means the
Claude agent-orchestration system (`docs/ai/*`), not gameplay AI/cognition.

## Test Summary
`pytest tests/tools/test_tag_registry.py tests/tools/test_validate_frontmatter.py
tests/tools/test_tag_report.py tests/tools/test_generate_registry.py
tests/tools/test_registry_query.py -v` → **146 passed, 0 failed** (20 + 71 + 13 + 39 + 3, all new
tests passing, all pre-existing tests unmodified and passing). Full `tests/tools/`
regression (excluding the pre-existing environmental `test_knowledge_search.py` failure mode) →
**479 passed, 2 failed** — the 2 failures are `test_search_mcp.py`'s `.mcp.json` config assertions,
confirmed pre-existing and unrelated via `git stash` (identical failure on the unmodified tree, no
file this ticket touches). Live-corpus verification (see Implementation Notes point 6): identical
185-violation count on modified vs. unmodified tree — zero regressions from enabling the hard
allowlist.

## Files Changed
- `tools/tag_registry.py` (new)
- `docs/guidelines/tag_registry.jsonl` (new, 37 seeded entries)
- `tools/validate_frontmatter.py` (registry-membership check added, backward compatible)
- `tools/tag_report.py` (heuristic categorization replaced by registry lookup)
- `tests/tools/test_tag_registry.py` (new)
- `tests/tools/test_tag_report.py` (updated)
- `tests/tools/test_validate_frontmatter.py` (updated)
- `docs/guidelines/tag_taxonomy.md`, `docs/guides/ticket_tagging.md`,
  `docs/guides/ticket_reporting.md` (updated)
- `docs/REGISTRY.yaml` (regenerated)
- `tickets/inprogress/TCK-20260706-TAG-REGISTRY-DATA.md` → `tickets/done/...`
- `staging_artifacts/TCK-20260706-TAG-REGISTRY-DATA/` → `stored_artifacts/...`

## Completion Summary
Added `tools/tag_registry.py`, an append-only, machine-readable tag data file
(`docs/guidelines/tag_registry.jsonl`) that closes the gap canonical-form rules alone couldn't
(catching near-duplicate-meaning tags like `calibrate`/`calibration`, not just format issues).
`validate_frontmatter.py` now enforces a hard allowlist against it (registration via
`tools/tag_registry.py add`, never update/delete — the append-only file plus its git history is the
changelog), verified to introduce zero regressions against the live 1046-file `tickets/done/`
corpus via a `git stash` before/after diff. `tag_report.py`'s categorization is now a direct
registry lookup rather than a 3-set heuristic that left 89% of live tags `unclassified` — after
seeding, 0 of 37 live tags are unclassified. A 5th category, `meta-process`, was added based on
evidence that most live tags describe the ticket/agent-workflow process itself, not gameplay,
matching the user's diagnosis. All category assignments were evidence-based (grepped against real
ticket usage), not guessed — one initial guess (`ai` as `subsystem-topic`) was corrected to
`meta-process` after evidence contradicted it. Two items were disclosed but deliberately left open
per the Uncertainty Rule: whether `bug`-family tags should be forbidden for duplicating `## Type`,
and whether `registry_query.py`'s separate `SEED_TAGS` tuple should now derive from this registry.

