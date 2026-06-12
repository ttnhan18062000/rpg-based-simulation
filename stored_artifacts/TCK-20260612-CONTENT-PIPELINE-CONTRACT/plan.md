---
ticket_id: TCK-20260612-CONTENT-PIPELINE-CONTRACT
phase: plan
---

# Plan: Content Pipeline Contract

## Ordered Steps

1. **Write docs/content/pipeline_contract.md**
   - Sections: Content Path Layout, Load Pipeline (ContentFamilySpec → CatalogRepository.load_all()), Resolver Layer, Reference Graph Rules, ContentUsageMatrix (implementation_state values), ContentPackManifest validation rules
   - Compliance IDs section: WORLD-CAT-001 through WORLD-CAT-025, WORLD-PATH-001 with file:line evidence
   - Cross-link to docs/content/content_pack_format.md (do not duplicate pack YAML format)
   - Frontmatter: status: authoritative, layer: systems, authority: P1, last_verified: 2026-06-12

2. **Write docs/content/content_semantics_contract.md**
   - Sections: Purpose (advisory compile-time defaults), FactionSemanticsService (singleton pattern, what it provides), RelationProjectionService (projection rules), RoleSemanticsService (legacy mapping, fallback rules), DefaultSemanticsService (four default categories, hardcoded fallback values)
   - Compliance IDs section: WORLD-SEM-001 through WORLD-SEM-006 with file:line evidence
   - State: NOT authoritative — advisory only, used at compile-time / world-building
   - Frontmatter: status: authoritative, layer: systems, authority: P1, last_verified: 2026-06-12

3. **Run python3 tools/validate_frontmatter.py docs/content/** — verify exits 0

4. **Run make docs-registry** — verify REGISTRY.yaml picks up both new docs

5. **Add parity ledger entries to docs/parity_ledger/infrastructure.yaml** for WORLD-CAT-* and WORLD-SEM-* IDs

## Scope Guards
- Do NOT change any file in src/content/ or src/content_semantics/
- Do NOT modify docs/content/content_pack_format.md
- Do NOT duplicate ContentUsageMatrix family list in the contract — cross-reference matrix.py instead

## Dependency Map
Step 1 → Step 3 (frontmatter validation requires the file)
Step 4 requires Step 1 and Step 2 complete

## ACs Mapped to Steps
- AC1 (pipeline_contract.md with frontmatter) → Step 1, 3
- AC2 (RuntimeContentMode → implementation_state documented) → Step 1
- AC3 (reference graph rules) → Step 1
- AC4 (ContentUsageMatrix section) → Step 1
- AC5 (content_semantics_contract.md) → Step 2, 3
- AC6 (faction/relation/role sections) → Step 2
- AC7 (fallback behavior) → Step 2
- AC8 (frontmatter validation) → Step 3
- AC9 (REGISTRY.yaml) → Step 4

## Deviations
(none yet)
