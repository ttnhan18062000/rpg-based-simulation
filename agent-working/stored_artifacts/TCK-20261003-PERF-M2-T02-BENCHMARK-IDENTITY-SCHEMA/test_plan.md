---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA
date: 2026-10-03
tags: [performance, documentation]
---

# Test Plan: TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA

Documents only; no behavior changes, so no new tests.

## Proof Plan

| Acceptance criterion | Level | Proof kind | Oracle source | Expected effect | Selected commands |
|---|---|---|---|---|---|
| Document exists, valid frontmatter, provisional status in opening lines | static | validator and read-through | frontmatter schema | no violations; first lines say provisional | `python3 tools/validate_frontmatter.py docs/performance/benchmark_identity_schema.md` |
| Inventory covers every Scope item 1 format with writer, reader, fields | static | read-through | ticket Scope item 1 list | every named path appears in the inventory table | `grep -c` of each named path in the document |
| Coverage matrix has a cell per dimension x format | static | read-through | M2 epic "Required contract dimensions" | no empty cell | count rows and columns |
| Every schema field has type, required status, source or milestone | static | read-through | ticket Scope item 3 | no empty cell in the field tables | read the §3.1 tables |
| JSON Schema embedded parses | unit-level check | parse | JSON Schema draft 2020-12 metaschema | the block loads and passes check_schema | `python3 -c` with json.loads and Draft202012Validator.check_schema |
| Comparability rule covers every identity field | static | cross-check | the identity field list in §3.1 | each identity field has a blocking or recorded-only row | compare §3.1 and §4 |
| Tool mapping cites versions | static | read-through | ticket Scope item 5 | pytest-benchmark 5.3.0 and pyperf stable docs cited with fetch date | read §5 |
| `tests/docs` and `tests/static` pass | test | pytest | existing suites | all pass | `pytest tests/docs tests/static -m "not slow" -q` |
| Diff limited to allowed paths | static | diff check | ticket acceptance criteria | only allowed paths | `git diff --name-only origin/main...HEAD` |
