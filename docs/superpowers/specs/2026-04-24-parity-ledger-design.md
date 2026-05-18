# Parity Ledger Design Specification

## 1. Goal
The Parity Ledger System provides a structured, machine-verifiable map between the legacy RPG-core requirements and the hardened V2 implementation. It ensures that 100% of the 1,144 identified requirements are tracked, prioritized, and backed by formal proof.

## 2. Architecture

### 2.1 Sharded Ledger
The ledger is stored in `docs/parity_ledger/` as a collection of YAML files, each representing a major gameplay domain.

- `substrate.yaml`: Foundation, Immutability, RNG, Persistence.
- `combat_movement.yaml`: Spatial laws, Legality, Tactics, Damage.
- `strategic_cognition.yaml`: Projects, Leads, Decision-making, Directives.
- `social_narrative.yaml`: Trust, Contracts, Betrayal, Social Appraisal.
- `town_resource.yaml`: Buildings, Inventory, Harvesting, Shops.
- `progression.yaml`: XP, Leveling, Attributes, Skill evolution.
- `world_dynamics.yaml`: Regions, Hazards, Scars, Environmental consequences.

### 2.2 Requirement Schema
Each entry in a ledger file MUST follow this schema:

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | string | Unique stable identifier (e.g., COMBAT-001). |
| `text` | string | The original requirement text from the checklist. |
| `status` | enum | `verified`, `divergent`, `missing`, `unsupported`. |
| `priority` | enum | `P0` (Core), `P1` (Critical), `P2` (Polish). |
| `legacy_evidence` | string | Path/line in the legacy `src` folder. |
| `v2_evidence` | string | Path/line in the `src` folder. |
| `proof_type` | enum | `parity`, `contract`, `differential`, `regression`. |
| `test_path` | string | Path to the verification test in `tests/parity/`. |
| `divergence_note` | string | Rationale for intentional behavioral differences. |
| `support_boundary` | string | Milestone or Phase ID where parity was achieved. |

## 3. Validation Logic
The `tools/parity/validate_ledger.py` script enforces the following invariants:

1. **Global Uniqueness**: All IDs must be unique across all YAML files.
2. **Schema Compliance**: All fields must match the defined types and enums.
3. **Evidence Integrity**: 
   - If `status` is `verified` or `divergent`, `v2_evidence` and `test_path` must be non-null.
   - If `status` is `divergent`, `divergence_note` must be non-null.
4. **Exhaustive Coverage**: Every `[ ]` or `[x]` item in `legacy_checklist.md` must have a corresponding entry in the ledger.

## 4. Workflow
1. **Creation**: A tool (`tools/parity/build_ledger.py`) initializes the ledger by parsing the existing `legacy_checklist.md`.
2. **Update**: As developers implement logic, they update the `status` and `evidence` in the relevant domain YAML.
3. **Verification**: CI runs the validation script. Any mismatch between implementation status and recorded evidence fails the build.

## 5. Security and Integrity
The ledger is the **Source of Truth** for engine certification. It is stored in Git to provide a full audit trail of how and why logic was changed or verified during the transition.
