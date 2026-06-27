---
status: active
artifact_type: plan
ticket_id: TCK-20260627-P3D-CATALOG-BROWSER
date: 2026-06-27
---

# Plan — TCK-20260627-P3D-CATALOG-BROWSER

## Goal

1. Add `make catalog-list` target that lists catalog IDs grouped by type — no world
   assembly required.
2. Document all 10 scenario templates in `docs/content/authoring_guide.md`.

## Unresolved Questions

None. Investigation complete.

---

## Implementation Steps

### Step 1 — Create `tools/catalog_list.py`

A standalone script that:
1. Instantiates `CatalogRepository` with the default content path.
2. Calls `load_all()` (no `strict=True` — avoids erroring on optional files).
3. Iterates over the five author-relevant types: biomes, ecologies, populations,
   factions, regions.
4. Prints each group to stdout with a header and sorted IDs.

Sample output format:
```
=== biomes (N) ===
  coastal_wetlands
  deep_forest
  ...

=== ecologies (N) ===
  ...
```

### Step 2 — Add `catalog-list` to `Makefile`

Additive changes only:
1. Add `catalog-list` to the `.PHONY` line.
2. Add the target after the `world-template` block:

```makefile
catalog-list: ## List catalog IDs by type (biomes, ecologies, populations, factions, regions)
	python3 tools/catalog_list.py
```

### Step 3 — Append to `docs/content/authoring_guide.md`

Append two new sections:

**Section 9 — Catalog ID Browser**
- Explains the `make catalog-list` target.
- Replaces the placeholder note in Section 8 FAQ ("A catalog browser tool is planned").
- Update the FAQ answer to point at `make catalog-list` instead.

**Section 10 — Scenario Templates Reference**
- Table of all 10 templates: ID, world type description, required world features,
  allowed perspective types, allowed focus modules, when to use.

---

## Files Changed

| File | Change |
|---|---|
| `tools/catalog_list.py` | New script |
| `Makefile` | Add `catalog-list` to `.PHONY` and add target |
| `docs/content/authoring_guide.md` | Append sections 9 and 10; update FAQ answer |

---

## Acceptance Criteria Check

- [x] `make catalog-list` target exists and prints catalog IDs grouped by type
- [x] 10 scenario templates documented with name, world type, content requirements, when to use
- [x] `make knowledge-index-update` run after doc creation
- [x] `docs/REGISTRY.yaml` — not required (no new doc file created)
