---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260719-TAG-COLLISION-DEDUP
artifact_type: test_plan
tags: [tagging, data-quality]
---

# Test Plan — TCK-20260719-TAG-COLLISION-DEDUP

## Regression Surface

- `tests/tools/test_tag_registry.py` — must still pass unmodified (no
  change to `tag_registry.py`'s code, only new data rows appended to
  `tag_registry.jsonl`).
- `tests/tools/test_validate_frontmatter.py` — must still pass; confirms
  the edited files' frontmatter remains valid YAML with a registered `tags`
  list.
- `tests/tools/test_generate_registry.py` — `docs/REGISTRY.yaml`
  regenerates from the edited ticket files; must still pass post-edit.

## New Tests Required

No new test file — this ticket is a pure data-correction pass over
existing, already-tested infrastructure (`tag_registry.py`,
`validate_frontmatter.py`). The verification signal is a direct corpus
re-scan (see below), not a new pytest file.

## Scoped Commands

```
python3 -m pytest tests/tools/test_tag_registry.py tests/tools/test_validate_frontmatter.py tests/tools/test_generate_registry.py -q
```

## Anti-Drift Test Guards

- Corpus re-scan must use `tools/validate_frontmatter.py::extract_frontmatter`
  (the real production parser), not a hand-rolled regex, to avoid a false
  "clean" result from a looser check.
- Re-run `python3 tools/tag_registry.py list` directly and grep for the 3
  newly-registered tags — confirms the registration actually persisted to
  disk, not just that the `add` command printed a success message.
