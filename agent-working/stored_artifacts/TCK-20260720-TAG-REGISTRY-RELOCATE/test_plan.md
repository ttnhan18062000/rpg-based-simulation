---
status: active
layer: ai
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260720-TAG-REGISTRY-RELOCATE
date: 2026-07-30
tags: [tagging, frontmatter]
---

# Test Plan — TCK-20260720-TAG-REGISTRY-RELOCATE

## Regression Surface (existing tests that must pass)

```
python3 -m pytest tests/tools/test_tag_registry.py tests/tools/test_layer_registry.py \
  tests/tools/test_glossary_registry.py tests/tools/test_generate_retro.py \
  tests/tools/test_agent_ops_dashboard_glossary.py tests/tools/test_validate_frontmatter.py \
  tests/tools/test_tag_report.py -q
```

## New Tests Required (per AC)

None — this is a pure relocation with no new behavior. Two existing test files have hardcoded
path fixtures that must be *updated* (not added to) to point at `registries/` instead of
`docs/guidelines/`: `test_agent_ops_dashboard_glossary.py` (lines 27, 32) and
`test_generate_retro.py` (fixture-writer helper, line 168's docstring + its actual path literal).

## Scoped Pytest Commands

Same command as Regression Surface above — no separate new-test-only command needed.

## Anti-Drift Test Guards

- After the move, `grep -rn "docs/guidelines/tag_registry\.jsonl\|docs/guidelines/layer_registry\.jsonl\|docs/guidelines/glossary_registry\.jsonl" tools/ src/ tests/ docs/ .claude/ CLAUDE.md` must return zero matches, EXCEPT inside `docs/plans/archive/agent_ops_dashboard/*.md` (6 files, intentionally untouched) and `infrastructure.yaml`'s `text:` blocks (2 lines, intentionally untouched historical narrative).
- `python3 tools/tag_registry.py list`, `python3 tools/layer_registry.py list`, `python3 tools/glossary_registry.py list` (or equivalent read call) must succeed and return the same entry counts as before the move, proving each tool resolves the new path correctly from repo-root cwd.
- `make docs-registry` run before and after the move: diff the two `docs/REGISTRY.yaml` outputs — must be byte-identical (confirms the `.jsonl`→`registries/` move is invisible to the doc-only registry walk).
