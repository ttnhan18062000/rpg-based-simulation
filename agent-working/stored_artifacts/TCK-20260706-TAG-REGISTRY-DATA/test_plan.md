---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260706-TAG-REGISTRY-DATA
artifact_type: test_plan
tags: [tagging, taxonomy, reporting]
---

# Test Plan — TCK-20260706-TAG-REGISTRY-DATA

## Unit tests

**`tests/tools/test_tag_registry.py`** (new):
- `canonical_form_violation`: valid tag → `None`; forbidden priority tag, uppercase, underscore,
  non-canonical phase (`phase5`), known synonym (`sim`/`cog`) → each returns a violation.
- `is_phase_milestone_tag` / `is_tag_registered`: canonical phase tags recognized without a
  registry; registered tags recognized; unregistered non-phase tags rejected.
- `load_registry`: missing file → `{}`; parses real entries; skips blank lines; raises
  `ValueError` on a duplicate tag across two lines.
- `add_tag`: appends and returns the entry; rejects non-canonical tag name; rejects invalid
  category string; rejects `phase-milestone` specifically as a category (it's in `ALL_CATEGORIES`
  but not `ADDABLE_CATEGORIES`); rejects re-adding an already-registered tag; two sequential adds
  leave the first entry's fields untouched (append-only, no in-place mutation).

**`tests/tools/test_tag_report.py`** (updated):
- `categorize_tag(tag, registry)` against a small in-memory registry: known tag → its category;
  `phase-5` → `phase-milestone` even with an empty registry; unregistered tag → `unclassified`.
- `build_tag_rows(included, registry)`: count/sort/category assignment via registry lookup;
  non-canonical-hit diagnostic still fires independent of registry membership.
- `collect_completed_tickets` tests unchanged (registry-agnostic — that function never looks at
  categories, only gathers raw tag lists).

**`tests/tools/test_validate_frontmatter.py`** (new `TestTagRegistryEnforcement` class):
- Registered tag on a post-cutoff ticket → `validate_file(f, registry=...)` returns `[]`.
- Unregistered tag → error mentioning the tag, "not in the tag registry", and the
  `tools/tag_registry.py add` hint command.
- `phase-5` tag with an *empty* registry → still accepted (pattern bypass).
- A non-canonical tag (`Combat`) with an empty registry → error mentions "not canonical form", and
  does **not** also claim "not in the tag registry" (canonical-form check short-circuits first).
- Calling `validate_file(f)` with no `registry` argument at all → unregistered tags still pass
  (backward-compat contract for every pre-existing test in the file that never passes a registry).
- Same unregistered-tag rejection reproduced for the `artifact` content type, not just `ticket`.
- A pre-cutoff `ticket_id` with an unregistered tag and an empty registry → still exempt (taxonomy
  cutoff check runs before either tag check).

## Regression suites (must show zero new failures vs. an unmodified-tree baseline)

Run and compare against a `git stash`-based baseline (untracked new files, like
`tools/tag_registry.py` itself, are not stashed by default, but the modified/tracked files —
`validate_frontmatter.py`, its test file — revert cleanly for a fair diff):

```bash
pytest tests/tools/test_tag_registry.py tests/tools/test_validate_frontmatter.py \
       tests/tools/test_tag_report.py tests/tools/test_generate_registry.py \
       tests/tools/test_registry_query.py -v

pytest tests/tools/ -q --ignore=tests/tools/test_knowledge_search.py
```

## Live-corpus verification (not unit tests, but required before declaring done)

1. `python3 tools/tag_report.py` after seeding — expect 0 tags falling to `unclassified` among the
   live post-cutoff tag set (any that do must be registered, not left as a gap).
2. **The critical check:** `python3 tools/validate_frontmatter.py tickets/done` run twice — once
   on the modified tree (hard allowlist active, registry seeded), once via `git stash` on the
   unmodified tree (registry check never runs) — and diff the total violation count. Must be
   **identical**. Any new violation beyond the pre-existing 2 non-canonical `simulation_quality`
   hits would mean the seed list missed a live tag, and must be fixed by registering the missing
   tag, not by loosening enforcement.
3. `validate_frontmatter.py` on each newly-edited doc individually
   (`tag_taxonomy.md`, `ticket_tagging.md`, `ticket_reporting.md`, `README.md`) to confirm no
   frontmatter regressions from doc edits.

## Acceptance criteria mapped to tests

- "Data file for total available tags" → `test_load_registry_*`, live `docs/guidelines/tag_registry.jsonl` populated with 37 entries.
- "Avoid different tag same meaning" → hard-allowlist tests (`TestTagRegistryEnforcement`) + the registry's own membership check being the mechanism.
- "Only add, never update/delete" → `test_add_tag_rejects_duplicate_tag`, `test_add_tag_is_append_only_existing_entries_unchanged`, no `update`/`delete` CLI subcommand exists at all.
- "Changelog" → the JSONL file plus its own git history *is* the changelog (documented explicitly in `tag_taxonomy.md`'s Tag Registry section) — no separate file to design/keep in sync.
- "Ticket tagging works on that data" → `validate_frontmatter.py`'s hard allowlist, verified against the live corpus with zero regressions.
- "Category managed as data, fix mostly-unclassified" → `categorize_tag` now a pure registry lookup; live re-run after seeding shows 0/37 unclassified (down from 32/36 before).
