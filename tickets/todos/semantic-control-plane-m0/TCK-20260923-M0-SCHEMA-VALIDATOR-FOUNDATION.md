---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION
phase: open
date: 2026-09-23
tags: [architecture, schema, documentation, testing]
---

# TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION

## Title
Define M0 Rule-Mechanism edge, causal-edge, and Rule-classification schemas with validator and broken-fixture proof

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Define the concrete schema and validator for the Simulation Semantic Control Plane's M0 milestone, turning architecture.md §3's currently "deliberately undecided" mapping shape into something real, the same way registries/mechanisms.yaml itself started. Three separate, independent structures are needed: (1) a Rule-to-Mechanism edge schema (rule_id, mechanism_id, an edge_type restricted to exactly one of REALIZES / PARTIALLY_REALIZES / CONSTRAINED_BY, evidence, date) recording how a Rule from docs/world_rules/ is realized by a Mechanism from registries/mechanisms.yaml; (2) a separate Mechanism-to-Mechanism causal edge schema (producer_mechanism_id, consumer_mechanism_id, evidence, date) recording "A produces input for B" as one directed fact, distinct from the existing depends_on field and from schema (1), with the inverse relationship generated/traversed rather than hand-authored; and (3) a separate, independent per-Rule realization classification record (rule_id, one of SUPPORTED/PARTIAL/CONFLICTING/MISSING/INERT-OFF/UNKNOWN, evidence, review date) that stays a human judgment call and must never be mechanically inferred from the edges in (1) or (2) — repeating that mistake was already rejected once for the Mechanism Registry's own "system" tier. A validator, mirroring tools/mechanism_registry/registry.py::validate(), must enforce every id-resolution, enum, and no-duplicate invariant across all three schemas, proven against deliberately-broken fixtures the same way the original mechanism registry validator was proven (its own AC #4, not a separate ticket — same precedent applies here). Once the three schemas and validator are real, architecture.md §3's placeholder note must be replaced with the actual chosen shape, since docs and code must stay in parity. All six investigated concerns (schema 1, schema 2, schema 3, the shared validator, the broken-fixture proof, and the doc-sync) converged on being one tightly-coupled unit: the validator cannot be built before the schemas exist, the proof is normally the schema-ticket's own AC line rather than a separate ticket, and the doc-sync has no content until the schemas are designed — splitting them would also risk re-deriving shared validator/file-layout infrastructure three separate times.

## Scope
- Create the Rule→Mechanism edge schema/registry (sibling file to registries/mechanisms.yaml, not inside depends_on): rule_id, mechanism_id, edge_type (REALIZES | PARTIALLY_REALIZES | CONSTRAINED_BY), evidence, date
- Create the Mechanism→Mechanism causal edge schema/registry (physically separate from schema 1 and from the depends_on field): producer_mechanism_id, consumer_mechanism_id, evidence, date; store only the directed fact, implement the inverse ("what does mechanism B consume") as a computed/traversed function with zero hand-authored inverse rows
- Create the per-Rule realization classification schema/registry (physically separate from schemas 1 and 2): exactly one record per Rule ID with rule_id, classification (SUPPORTED | PARTIAL | CONFLICTING | MISSING | INERT-OFF | UNKNOWN), evidence, review date
- Build a validator (new module or extension mirroring tools/mechanism_registry/registry.py::validate()'s return-list-of-error-strings pattern) enforcing: rule_id resolves against a live scan of docs/world_rules/**/*.md headings (not a hardcoded ID list); mechanism_id/producer_mechanism_id/consumer_mechanism_id resolve in registries/mechanisms.yaml; edge_type is one of the 3 enum values; classification is one of the 6 enum values; no duplicate (rule_id, mechanism_id, edge_type) triple; no duplicate directed (producer_mechanism_id, consumer_mechanism_id) pair; no duplicate rule_id in the classification registry
- Write pytest tests mirroring tests/unit/tools/test_mechanism_registry.py's structure: one deliberately-broken fixture per invariant asserting validate() returns a non-empty error list, plus a real/empty/seed-data pass asserting zero errors
- Explicitly do not implement any function/helper that derives or overwrites a Rule's classification from its own edge list — the non-derivation rule must be enforced by omission, not just documented
- Replace architecture.md §3's "Deliberately undecided..." paragraph (current lines 86-90) with the actual chosen file path(s)/field names/serialization format for all three schemas, keeping them described as three distinct structures, and keep citing the validator + §7's UNKNOWN-is-permanent discipline; leave every other section of architecture.md unchanged

## Out of Scope
- No real mapping entries/rows/edges/classifications populated for any actual Rule or Mechanism — that is M1, gated on this ticket landing first
- No Cartesian-product generation of Rule×Mechanism pairs; unmapped pairs stay UNKNOWN permanently, never auto-filled
- No CI/make-target wiring for the new validator (that pattern, TCK-20260920-MECHANISM-REGISTRY-CI-WIRING, is a distinct later-layer concern not named in M0's own roadmap text)
- No changes to the existing depends_on field or its semantics
- No M1, M2, M3, or M4 deliverable of any kind (real edge population, Rule Catalog re-verification, promotion of existing review-export prose, etc.)

## Acceptance Criteria
- [ ] The Rule→Mechanism edge schema file accepts {rule_id, mechanism_id, edge_type, evidence, date} and validate() returns an empty error list on valid/empty data
- [ ] validate() rejects a record with edge_type outside {REALIZES, PARTIALLY_REALIZES, CONSTRAINED_BY} on a deliberately-broken fixture
- [ ] validate() rejects an unresolved rule_id and, separately, an unresolved mechanism_id, each on its own deliberately-broken fixture
- [ ] validate() rejects a duplicate (rule_id, mechanism_id, edge_type) triple on a deliberately-broken fixture
- [ ] The Mechanism→Mechanism causal edge schema stores only producer_mechanism_id, consumer_mechanism_id, evidence, date — no shared edge_type field with schema 1, no merged row shape
- [ ] validate() rejects an unresolved producer_mechanism_id and, separately, an unresolved consumer_mechanism_id, each on its own deliberately-broken fixture
- [ ] validate() rejects a duplicate directed (producer_mechanism_id, consumer_mechanism_id) pair on a deliberately-broken fixture
- [ ] An inverse-lookup function (e.g. "what does mechanism B consume") is implemented as a computed/traversed query with zero hand-authored inverse rows in storage
- [ ] registries/mechanisms.yaml's depends_on field is unchanged after this ticket
- [ ] The per-Rule classification schema holds exactly one record per Rule ID with rule_id, classification, evidence, review date
- [ ] validate() rejects a classification value outside the 6-item enum and rejects a duplicate rule_id, each on its own deliberately-broken fixture
- [ ] UNKNOWN is accepted and preserved as a valid, non-error classification value — never silently rewritten to MISSING
- [ ] No function in the codebase takes only the edge list (schema 1 and/or 2) as input and returns or writes a classification value for schema 3
- [ ] Running the validator against real/empty/seed data across all three schemas returns zero errors, proven in a passing test
- [ ] The string "Deliberately undecided" no longer appears in architecture.md §3
- [ ] architecture.md §3's replacement text names the actual chosen file path(s), field names, and serialization format for all three schemas, still describes them as three distinct structures, and still cites the validator and §7's UNKNOWN-permanence discipline
- [ ] No section of architecture.md other than §3 is altered

## Related Tickets
- TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC
- TCK-20260920-MECHANISM-REGISTRY-CI-WIRING
- TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT
- TCK-20260918-MECHANISM-UNCLASSIFIABLE-DEPENDS-ON-EDGES-RESOLUTION
- TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY
- TCK-20260915-MECHANISM-REGISTRY-FOUNDATION
- TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION
- TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION

## Related Docs
- docs/plans/simulation_semantic_control_plane/architecture.md
- docs/plans/simulation_semantic_control_plane/roadmap.md
- docs/plans/simulation_semantic_control_plane/rollout_plan.md
- docs/plans/mechanism_tier_model_initiative.md

## Related Stored Artifacts
None.

## Related Code Areas
- registries/mechanisms.yaml
- tools/mechanism_registry/registry.py
- tools/mechanism_registry/system_registry.py
- tests/unit/tools/test_mechanism_registry.py
- tests/unit/tools/test_mechanism_registry_changed_code_check.py
- docs/world_rules/places-culture/territory-control.md
- docs/world_rules/review-exports/places-territory-batch-11a-review.md
- expected: registries/rule_mechanism_edges.yaml (or equivalent sibling file, exact path/format is this ticket's own decision)
- expected: registries/mechanism_causal_edges.yaml (or equivalent sibling file, exact path/format is this ticket's own decision)
- expected: registries/rule_classifications.yaml (or equivalent sibling file, exact path/format is this ticket's own decision)

## Assumptions / Open Questions
- Exact file path(s) and serialization format for all three schemas are deliberately undecided by architecture.md/roadmap.md today; this ticket must pick and document them (and reflect that choice in the architecture.md §3 rewrite)
- Whether a producer_mechanism_id == consumer_mechanism_id self-citing edge is valid or must be rejected is an open question left to this ticket to resolve
- The rule_id resolution parser (scanning docs/world_rules/**/*.md "## <ID> —" headings) does not exist yet and must be built new as part of this ticket, not reused from prior art
- 172 Rule IDs are confirmed unique today, so a bare Rule ID is treated as a safe foreign key without a namespacing scheme

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
