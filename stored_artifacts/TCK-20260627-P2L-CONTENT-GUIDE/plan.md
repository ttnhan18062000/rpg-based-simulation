# Plan — TCK-20260627-P2L-CONTENT-GUIDE

## Ordered Steps

### Step 1 — Create docs/content/ directory and write authoring_guide.md

**File to create:** `docs/content/authoring_guide.md`

Structure (from Implementation Notes in ticket):
1. Introduction — what this guide covers and who it's for
2. Quick Start — add a world module (step-by-step, using `make world-template` as entry point)
3. Reference — full WorldModuleSpec YAML field table
4. Adding a Composition — step-by-step for WorldCompositionSpec
5. Adding a Scenario — step-by-step for SimulationScenarioDefinition
6. Make Targets — table of all authoring-relevant targets
7. Sharp Edges — explicit named traps (observability_tags, provided_features, catalog IDs,
   hazard_level, auto-discovery note from P2K)
8. FAQ — common validation errors and their fixes

**Acceptance criteria mapped to steps:**
- AC1 (guide exists, covers 6 areas) → entire guide
- AC2 (sharp edges section names specific traps) → Step 7
- AC3 (make target per authoring task) → Steps 2, 4, 5, 6
- AC4 (REGISTRY.yaml updated) → Step 2 below
- AC5 (knowledge-index-update) → Step 3 below

### Step 2 — Regenerate docs/REGISTRY.yaml

Run: `make docs-registry`

This auto-generates the registry from all docs with YAML frontmatter. The new
`docs/content/authoring_guide.md` must include frontmatter with status, layer, authority,
audience, and tags fields so it appears in the registry.

### Step 3 — Run make knowledge-index-update

Run: `make knowledge-index-update`

Incremental reindex so the new file is discoverable via mcp__knowledge-search__search_docs.

## Files to Change

| Step | File | Action |
|---|---|---|
| 1 | `docs/content/authoring_guide.md` | Create (new file) |
| 2 | `docs/REGISTRY.yaml` | Regenerate via `make docs-registry` |

## Scope Guards (What NOT to Touch)

- Do NOT modify `docs/world/modules_contract.md` — it's the technical contract; the guide
  references it, not replaces it.
- Do NOT modify `src/worldmodules/schema.py` or any source files.
- Do NOT modify `docs/engine/manifest.json` — the authoring guide is not a mandatory engine doc.
- Do NOT add scenario template documentation — explicitly Out of Scope.
- Do NOT add a catalog browser — Out of Scope (P3-D).

## Dependency Map

Step 1 → Step 2 (docs-registry requires the file to exist with frontmatter)
Step 2 → Step 3 (knowledge-index runs after registry is updated)

## Deviations

None.
