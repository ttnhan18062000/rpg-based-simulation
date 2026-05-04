# Design Spec: Checklist Governance & Stable IDs

## Goal
Establish a machine-readable, stable, and domain-partitioned identifier system for the RPG Engine Logic Checklist to enable enforceable proof governance and prevent regression of verified laws.

## Architecture
The governance system consists of a structured identifier schema and a set of proof markers that will be audited by the `ledger_validator.py`.

### 1. Stable ID Schema
Every checklist item will be prefixed with a unique, backtick-wrapped ID.

**Format**: `- [ ] `RPG-[DOMAIN]-[NNN]` Description`

**Prefixes**:
- `GOV`: Checklist governance, proof ledger, divergence, unsupported registry
- `AUTH`: Authoritative mutation, pipeline, update model, conflict resolution
- `COMBAT`: Combat, movement, tactics, legality, spatial behavior
- `RES`: Resources, inventory, interactions, shops, crafting, town loop
- `STRAT`: Strategic cognition, routines, blockers, leads, detours, memory
- `SOC`: Social contracts, parties, trust, reputation, betrayal
- `PROG`: Progression, stats, attributes, skills, equipment, durability
- `WORLD`: World lifecycle, ecology, regions, raids, bosses, calamities
- `API`: API, inspector, replay truth, observability, metrics
- `INFRA`: CLI, logging, brokerless mode, worker fallback, degraded mode
- `DATA`: Serialization, registry, defaults, schema, immutability/freeze
- `MED`: Medical, wounds, scars, hidden discovery, death, succession, nemesis

### 2. Proof Markers
Verified rows must include an HTML comment block containing proof metadata.

**Format**:
```md
<!-- ID: RPG-XXXX-NNN SOURCE: src/... TEST: tests/... PROOF: unit|integration|negative|race|replay|longrun|divergence -->
```

## Implementation Strategy
1. **Migration Phase**: Perform a section-by-section replacement of legacy `NNN:-` markers in `logic_checklist_exhaustive.md` with the new `RPG-DOMAIN-NNN` identifiers.
2. **Registry Phase**: Create divergence and unsupported registers for items that will not be implemented with legacy parity.
3. **Validator Phase**: Finalize `scripts/ledger_validator.py` to enforce ID uniqueness and proof marker presence.

## Verification
- **Uniqueness Check**: Ensure no duplicate IDs exist after migration.
- **Reference Integrity**: Update existing test references to the new stable IDs.
- **Manual Audit**: Verify that items are categorized in the correct domain.
