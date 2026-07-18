---
status: active
layer: guidelines
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260718-LAYER-REGISTRY-CONVERSION
date: 2026-07-18
tags: [frontmatter, tagging]
---

# Implementation Plan — TCK-20260718-LAYER-REGISTRY-CONVERSION

## Summary

Create `tools/layer_registry.py` (mirroring `tag_registry.py`, minus the
`category` field), seed `docs/guidelines/layer_registry.jsonl` with the 19
original `LAYER_VALUES` via the real `add_layer()` API, convert
`validate_frontmatter.py`'s `LAYER_VALUES` to a registry-backed computed
value while preserving its importable name, and document the new mechanism
in `CLAUDE.md`.

## Steps

### Step 1 — `tools/layer_registry.py`

New file: `canonical_form_violation`, `registry_path`, `load_registry`,
`is_layer_registered`, `check_layers_registered`, `add_layer`, and a new
`layer_values()` convenience returning a `frozenset` (matching
`tools/ticket_field_values.py`'s other canonical enums' type) — no
`category` parameter/field anywhere.

### Step 2 — Seed the registry

Run `add_layer()` for each of the 19 original values with a real,
non-empty note. Verify `layer_values() == {the 19 original values}`
immediately after.

### Step 3 — Convert `validate_frontmatter.py`

`LAYER_VALUES = _layer_values()` (imported from `layer_registry.py`),
replacing the hardcoded literal. Import name unchanged.

### Step 4 — Verify the import chain and blast radius

Confirm `tools/ticket_field_values.py`'s existing `LAYER_VALUES` import
still resolves correctly (existing identity test). Run
`validate_file`-based full-corpus scan before (via `git stash`) and after
the conversion; confirm identical error sets — zero new failures.

### Step 5 — `CLAUDE.md`

Add a Layer-registry paragraph mirroring the Tags-allowlist paragraph, plus
a short paragraph distinguishing `layer`/`tags` (registry-backed,
differ in cardinality/categorization) from the ticket-body fields
(`Tier`/`Status`/`Priority`, a separate mechanism).

### Step 6 — Tests

`tests/tools/test_layer_registry.py`, mirroring `test_tag_registry.py`'s
structure.

## Scope Guards

- Do not touch `Tag`'s own mechanism.
- Do not re-scan/fix the 14 pre-existing, unrelated layer-value drift
  errors found during Step 4's verification — out of scope, a mechanism
  change not a data cleanup.
- Do not add a `category` field to Layer registry entries.
- Do not touch `TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL`'s own
  scope — only confirm its planned generic `LAYER_VALUES` import still
  holds.

## Dependency Map

Step 1 → Step 2 → Step 3 → Step 4 (verification, needs 1-3 done) → Step 6
(tests, needs 1-3). Step 5 is independent, can run any time.

## Acceptance Criteria Map

- AC "registry exists, seeded correctly" → Steps 1-2.
- AC "structurally mirrors tag_registry.py" → Step 1.
- AC "LAYER_VALUES registry-backed, import surface unchanged" → Step 3 +
  Step 4's identity-test confirmation.
- AC "zero new corpus failures" → Step 4's before/after comparison.
- AC "CLAUDE.md documents it" → Step 5.

## Anti-Drift Notes

Seed via the real `add_layer()` API, never hand-written JSONL — proves the
write path itself works, not just that the resulting file happens to look
right.
