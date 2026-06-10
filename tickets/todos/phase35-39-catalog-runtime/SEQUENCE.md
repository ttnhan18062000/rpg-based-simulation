# Phase 35–39 Catalog Runtime — Ticket Sequence

Source: `world_phase_35_39.md`

## Skipped (already done)

| Task | Covered by |
|---|---|
| Phase 35.1 — Set default to catalog_with_compatibility | TCK-20260609-REGISTRY-BOOTSTRAP-MODES (bootstrap.py already uses CATALOG_WITH_COMPATIBILITY) |
| Phase 35.2 — Startup content source report | TCK-20260609-REGISTRY-BOOTSTRAP-MODES (ContentSourceReport exists) |
| Phase 35.3 — Preserve explicit legacy/test modes | TCK-20260609-REGISTRY-BOOTSTRAP-MODES + TCK-20260609-MIGRATION-TEST-MARKERS |
| Phase 38.1 — Move legacy records behind migration map | TCK-20260609-MIGRATION-MAP-YAML |
| Phase 38.2 — Add hardcoded gameplay guard | TCK-20260609-HARDCODED-GAMEPLAY-GUARD |
| Phase 38.3 — Convert fallback warnings to strict errors by mode | TCK-20260609-REGISTRY-BOOTSTRAP-MODES |
| Phase 39.1 — frontier_extended_pack manifest | TCK-20260609-FRONTIER-EXTENDED-PACK |
| Phase 39.2 — First pack content data | TCK-20260609-FRONTIER-EXTENDED-PACK |
| Phase 39.3 — First pack strict matrix rows | TCK-20260609-FRONTIER-EXTENDED-PACK |

## New tickets (implementation order)

| Order | Ticket | Phase | Dependency |
|---|---|---|---|
| 1 | TCK-20260610-CATALOG-SCENARIO-BUILDER | 36.1 | none |
| 2 | TCK-20260610-CATALOG-ARENA-SMOKE | 36.2 | CATALOG-SCENARIO-BUILDER |
| 3 | TCK-20260610-CATALOG-VS-LEGACY-SEMANTICS | 36.3 | CATALOG-SCENARIO-BUILDER |
| 4 | TCK-20260610-COMBAT-RELATION-PROJECTION | 37.1 | none (parallel to 36) |
| 5 | TCK-20260610-QUEST-RELATION-PROJECTION | 37.2 | none (parallel to 36) |
| 6 | TCK-20260610-REGION-THREAT-PROJECTION | 37.3 | none (parallel to 36) |
