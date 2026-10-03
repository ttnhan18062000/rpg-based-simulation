---
ticket_id: TCK-20260612-CONTENT-PIPELINE-CONTRACT
phase: investigation
---

# Investigation: Content Pipeline Contract

## Current Behavior (file:line refs)

### Compliance IDs found in src/content/
- WORLD-CAT-001, WORLD-CAT-002, WORLD-CAT-003 — src/content/schema.py:1
- WORLD-CAT-004, WORLD-CAT-005 — src/content/repository.py:1
- WORLD-CAT-006, WORLD-CAT-007 — src/content/validator.py:1
- WORLD-CAT-024, WORLD-CAT-025 — src/content/resolver.py:1
- WORLD-PATH-001 — src/content/paths.py:1

### Compliance IDs found in src/content_semantics/
- WORLD-SEM-001, WORLD-SEM-002 — src/content_semantics/faction.py:1
- WORLD-SEM-003, WORLD-SEM-004 — src/content_semantics/relation.py:1, role.py:1
- WORLD-SEM-005, WORLD-SEM-006 — src/content_semantics/defaults.py:1

### Content Pipeline Structure
- **ContentPathConfig** (paths.py:3): frozen dataclass — content_root=data/content, world_modules_dir, world_compositions_dir, simulation_scenarios_dir
- **CatalogRepository** (repository.py): loads YAML files per ContentFamilySpec (family, path, schema, repository_index, required, state_policy); `load_all()` is the entry point
- **ContentFamilySpec** (repository.py): typed record: family name, file path, schema class, repository index key, required flag, state_policy
- **Resolvers** (resolver.py): FoundationResolver, LivingResolver, SocialResolver, EntityResolver, WorldResolver — each wraps CatalogRepository and raises ResolverError on missing ref
- **ResolverError** (resolver.py:52): inherits KeyError; carries family, missing_id, context
- **reference_graph.py**: FAMILY_TO_SHORT (family dotted name → short type name), FIELD_TO_TARGET (field name → target type); used for cross-reference traversal to find dangling refs

### ContentUsageMatrix (matrix.py)
- CONTENT_USAGE_MATRIX: Dict[str, ContentFamilyMatrixEntry] — one entry per content family
- implementation_state values: RESOLVED_PARTIALLY, RUNTIME_AUTHORITATIVE, PROJECTED_TO_LEGACY, DESIGN_ONLY
- Policy: YAML comments are planning notes only; implementation_state is the authoritative status gate
- No RuntimeContentMode enum exists — the ticket's assumption was wrong; content mode is family-level implementation_state

### ContentPackManifest (pack_manifest.py)
- schema_version: "content_pack.v1"
- Required fields: pack_id (lowercase, underscores), display_name, version
- Validation rule: must have at least one consumer — sample_compositions or sample_scenarios (pack_manifest.py:38-44)
- ContentPackManifestValidator: validates manifest against known pack IDs

### content_semantics Layer
- **FactionSemanticsService** (faction.py): process-level singleton (get_faction_semantics_service); translates catalog faction ID → legacy Faction enum; provides hostility/protection queries
- **RelationProjectionService** (relation.py): projects relationship labels between factions using perspectives and faction relationships; returns RelationProjection with label, axes, confidence
- **RoleSemanticsService** (role.py): maps role_id → legacy EntityRole enum; provides role_family and default_stats_profile; fallback: keyword matching on role_id string
- **DefaultSemanticsService** (defaults.py): compile-time defaults for entity combat, building durability, resource harvest, faction vault; falls back to hardcoded values if repo.defaults is empty
- **Status**: advisory layer — not authoritative state; used at compile-time / world-building time, not tick path

## Mechanics/Engine Constraints
- Content is preprocessing input (loaded before any simulation tick)
- No content system calls occur on the tick path — content state is read-only after load
- Authoritative mutation pipeline does not call into src/content/ or src/content_semantics/

## Parity Ledger Overlap
- infrastructure.yaml has entries referencing content/validator.py::validate_matrix_evidence and test_content_usage_evidence.py (approx lines 849, 975, 1812, 1831)
- No entries for WORLD-CAT-* or WORLD-SEM-* IDs directly

## Prior Work
- docs/content/content_pack_format.md (2026-06-09): active, covers pack YAML format — do not duplicate, cross-link
- docs/mechanics/content_usage_matrix.md: referenced in CLAUDE.md as a Mechanics Bible doc

## Risks and Open Questions
- No RuntimeContentMode enum — ticket description was incorrect; must document implementation_state instead
- Singleton pattern in faction.py (WORLD-SEM-001/002) creates process-level state — advisory note in contract

## Anti-Drift Hazards
- CONTENT_USAGE_MATRIX in matrix.py is the single source of truth for content family status; contract must cross-reference it rather than duplicate family state
