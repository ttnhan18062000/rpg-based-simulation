---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260606-DOCSITE-FM-ARCHIVE
artifact_type: plan
tags: [docsite, fm, archive]
---

# Plan — TCK-20260606-DOCSITE-FM-ARCHIVE

## Objective

Write `tools/add_frontmatter_archive.py` and execute it to prepend minimal YAML frontmatter to all 272 `.md` files across `docs/archive/`, `docs/superpowers/specs/`, and `docs/specs/`. All modified files must pass `tools/validate_frontmatter.py`.

---

## Implementation Steps

### Phase 1 — Script

1. Write `tools/add_frontmatter_archive.py`:
   - Accept optional `--dry-run` flag (print what would change, write nothing)
   - Recurse three target directories with `rglob("*.md")`
   - For each file: check if `content.startswith("---")`; skip if true
   - Extract date from filename with `re.search(r"(\d{4}-\d{2}-\d{2})", filename)`, fallback `"unknown"`
   - Infer layer from keyword map (case-insensitive substring match on stem), fallback `"misc"`
   - Build frontmatter block and prepend to file content
   - Print per-file log lines; print summary at end (prepended, skipped, misc count)

2. Write `tests/tools/test_add_frontmatter_archive.py` — 7 test groups (see test_plan.md)

### Phase 2 — Execution

3. Run script (non-dry): `python3 tools/add_frontmatter_archive.py`
4. Verify: `python3 tools/validate_frontmatter.py docs/archive/`
5. Verify: `python3 tools/validate_frontmatter.py docs/superpowers/specs/`
6. Verify: `python3 tools/validate_frontmatter.py docs/specs/`
7. Run test suite: `pytest tests/tools/ -v -m "not slow"`

### Phase 3 — Finalize

8. Update ticket (Implementation Notes, Test Summary, Files Changed, Completion Summary)
9. Move ticket to `tickets/done/`
10. Append to `tickets/working_log.csv`
11. Move staging artifacts to `stored_artifacts/`
12. Write agent-monitoring records

---

## Files to Create / Modify

| File | Action |
|---|---|
| `tools/add_frontmatter_archive.py` | Create (new script) |
| `tests/tools/test_add_frontmatter_archive.py` | Create (new tests) |
| `docs/archive/**/*.md` (235 files) | Modify: prepend frontmatter |
| `docs/superpowers/specs/*.md` (33 files) | Modify: prepend frontmatter |
| `docs/specs/*.md` (4 files) | Modify: prepend frontmatter |

---

## Dependencies

- `TCK-20260606-DOCSITE-SCHEMA` must be complete (provides `docs/guidelines/frontmatter_schema.md` and `tools/validate_frontmatter.py`) — confirmed done.
