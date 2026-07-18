---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-GLOSSARY-REGISTRY
artifact_type: plan
tags: [dashboard, observability, reporting]
---

# Implementation Plan — TCK-20260718-GLOSSARY-REGISTRY

## Summary
Build `tools/glossary_registry.py` mirroring `tag_registry.py`'s shape, seed
`docs/guidelines/glossary_registry.jsonl` with 35 real terms via the real `add_term()` API (never
hand-written JSON — matches the seeding precedent `layer_registry.py` established today), add a
dedicated test file mirroring `test_layer_registry.py`'s structure.

## Steps

### Step 1 — Write `tools/glossary_registry.py`
Files: `tools/glossary_registry.py` (new).
Registry schema: `{"term": str, "category": str, "added_date": str, "description": str}`.
`GLOSSARY_CATEGORIES` fixed set: `ticket-status`, `run-status`, `reason-code`, `event-status`,
`tier`, `priority`, `type`. No canonical-form check (deliberate — see module docstring).
`add_term()` validates category membership and non-blank description, refuses duplicate `term`
keys. `load_registry()`/`registry_path()` mirror the established shape exactly. CLI: `add`/`list`.

### Step 2 — Seed the registry via the real API
No manual file — call `add_term()` once per compiled term (35 total, per investigation.md) via a
throwaway Python invocation, exactly as `layer_registry.py`'s seeding did. Verify
`load_registry()` returns 35 entries with no duplicate-key exception afterward.

### Step 3 — Test file
`tests/tools/test_glossary_registry.py` mirroring `test_layer_registry.py`'s structure: I/O tests
(missing file, read entries, skip blanks, duplicate-key raise), `add_term` validation tests
(invalid category, blank description, duplicate term, append-only), plus two "real seeded
registry" tests proving live coverage (every `ticket_field_values.py` canonical value has an
entry; every entry has a non-blank description and valid category) — mirrors
`test_layer_values_matches_real_seeded_registry`'s precedent of testing the actual live file, not
just a fixture.

## Scope Guards
- Do not touch `tag_registry.py`/`layer_registry.py` — read-only reference, not modified.
- Do not add a canonical-form check — explicitly wrong for this domain (see investigation.md).
- Do not wire this registry into any API endpoint yet — that is
  `TCK-20260718-GLOSSARY-API`'s scope, sequenced after this ticket.

## Dependency Map
No dependencies within this batch — first ticket in `SEQUENCE.md` order. Blocks
`TCK-20260718-GLOSSARY-API` (which imports `load_registry()` from this module).

## Acceptance Criteria Map
- AC "registry seeded with real, accurate descriptions" → Step 2 + investigation.md's term list.
- AC "no description text hardcoded in frontend" → out of this ticket's direct scope but the
  registry's existence is the prerequisite that makes it possible.

## Anti-Drift Notes
Seeded via the real `add_term()` function, not hand-written JSON lines — verified by re-loading
the file afterward and confirming entry count/no duplicate-key error, mirroring
`TCK-20260718-LAYER-REGISTRY-CONVERSION`'s own stated precedent for this exact concern.
