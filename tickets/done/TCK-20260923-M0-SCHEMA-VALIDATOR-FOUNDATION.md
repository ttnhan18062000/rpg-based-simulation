---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION
phase: done
date: 2026-09-23
tags: [architecture, schema, documentation, testing]
---

# TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION

## Title
Define M0 Rule-Mechanism edge, causal-edge, and Rule-classification schemas with validator and broken-fixture proof

## Status
DONE

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
- [x] The Rule→Mechanism edge schema file accepts {rule_id, mechanism_id, edge_type, evidence, date} and validate() returns an empty error list on valid/empty data
- [x] validate() rejects a record with edge_type outside {REALIZES, PARTIALLY_REALIZES, CONSTRAINED_BY} on a deliberately-broken fixture
- [x] validate() rejects an unresolved rule_id and, separately, an unresolved mechanism_id, each on its own deliberately-broken fixture
- [x] validate() rejects a duplicate (rule_id, mechanism_id, edge_type) triple on a deliberately-broken fixture
- [x] The Mechanism→Mechanism causal edge schema stores only producer_mechanism_id, consumer_mechanism_id, evidence, date — no shared edge_type field with schema 1, no merged row shape
- [x] validate() rejects an unresolved producer_mechanism_id and, separately, an unresolved consumer_mechanism_id, each on its own deliberately-broken fixture
- [x] validate() rejects a duplicate directed (producer_mechanism_id, consumer_mechanism_id) pair on a deliberately-broken fixture
- [x] An inverse-lookup function (e.g. "what does mechanism B consume") is implemented as a computed/traversed query with zero hand-authored inverse rows in storage
- [x] registries/mechanisms.yaml's depends_on field is unchanged after this ticket
- [x] The per-Rule classification schema holds exactly one record per Rule ID with rule_id, classification, evidence, review date
- [x] validate() rejects a classification value outside the 6-item enum and rejects a duplicate rule_id, each on its own deliberately-broken fixture
- [x] UNKNOWN is accepted and preserved as a valid, non-error classification value — never silently rewritten to MISSING
- [x] No function in the codebase takes only the edge list (schema 1 and/or 2) as input and returns or writes a classification value for schema 3
- [x] Running the validator against real/empty/seed data across all three schemas returns zero errors, proven in a passing test
- [x] The string "Deliberately undecided" no longer appears in architecture.md §3
- [x] architecture.md §3's replacement text names the actual chosen file path(s), field names, and serialization format for all three schemas, still describes them as three distinct structures, and still cites the validator and §7's UNKNOWN-permanence discipline
- [x] No section of architecture.md other than §3 is altered

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

Implemented exactly per `staging_artifacts/TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION/plan.md`,
Steps 1-6. One post-Implement fix, recorded in plan.md's "Deviations" section: the documented CLI
invocation (`python3 tools/semantic_control_plane/registry.py`) initially raised
`ModuleNotFoundError: No module named 'tools'` — an absolute `from tools....` import ran before any
repo-root `sys.path` bootstrap, unlike its sibling `tools/mechanism_registry/registry.py`. Caught by
the Architecture-Verify phase's shadow candidate reviewer (an advisory-only logging call that never
gates the real verdict — the production Architecture-Verify had already independently APPROVED),
then independently reproduced before acting on it. Fixed by moving the `_REPO_ROOT` sys.path
insertion above the `tools.*` imports, plus a new subprocess-based regression test
(`test_documented_cli_invocation_actually_runs`) so this class of gap can't silently recur.

- **Step 1** — `tools/semantic_control_plane/rule_catalog.py::scan_rule_ids()`: walks
  `docs/world_rules/**/*.md` (default), excludes any path with a `review-exports` path component,
  matches `^## ([A-Z]{2,8}-[0-9]{2})\b`. Confirmed against the real corpus: 172 unique ids across
  46 non-review-export files (investigation.md's own sweep found 45 — off-by-one in file count
  only, ids count matches exactly; not a real discrepancy, both counts are "sanity checks," not an
  AC). Confirmed zero false matches inside `docs/world_rules/review-exports/` by direct sweep
  before writing the code.
- **Step 2** — `registries/rule_mechanism_edges.yaml` (seeded `edges: []`) +
  `validate_rule_mechanism_edges()` in the new `tools/semantic_control_plane/registry.py`: enforces
  the `edge_type` enum, `rule_id`/`mechanism_id` resolution, and duplicate-triple check exactly as
  planned. `mechanism_id` resolution reuses `MechanismRegistry(...).all_mechanisms()` (imported
  read-only from `tools.mechanism_registry.registry`), never re-parses `mechanisms.yaml`.
- **Step 3** — `registries/mechanism_causal_edges.yaml` (seeded `edges: []`) +
  `validate_mechanism_causal_edges()`: no `edge_type` field anywhere in the row shape or the
  validator's executable body (proven by an AST-based test that strips the docstring before
  checking, since the docstring's own prose legitimately names the field it is explaining the
  *absence* of). Self-edge (`producer_mechanism_id == consumer_mechanism_id`) rejected per Decision
  2 in plan.md. `consumers_of()`/`producers_for()` are pure functions computing the traversal over
  the passed-in `edges` list at call time — no stored inverse row anywhere, proven by a test that
  inspects the fixture itself, not just the function's return value.
- **Step 4** — `registries/rule_classifications.yaml` (seeded `classifications: []`) +
  `validate_rule_classifications()`: enforces the 6-value classification enum, `rule_id`
  resolution, and duplicate-`rule_id` check (not duplicate pair — one record per Rule ID, full
  stop). `UNKNOWN` requires zero special handling to pass, since the function has no normalization
  step of any kind. **Non-derivation confirmation (AC #13)**: no function anywhere in
  `tools/semantic_control_plane/` takes only `rule_mechanism_edges.yaml`/`mechanism_causal_edges.yaml`
  data as input and returns or writes a classification value. Confirmed by direct review of both
  modules' full contents at close of implementation (the only functions touching schema-3 data are
  `validate_rule_classifications()`, which takes classification data and `known_rule_ids` — never
  edge data — and `validate_all()`, which calls all three `validate_*()` functions independently
  and never pipes one schema's data into another's validator). Backed by a cheap grep-shaped test,
  `test_no_function_derives_classification_from_edges`, scanning both modules' public callables for
  a name containing both "edge" and "classif".
- **Step 5** — `validate_all()` in `tools/semantic_control_plane/registry.py`: loads all three real
  files, resolves `known_rule_ids`/`known_mechanism_ids`, merges all three `validate_*()` results
  plus `check_duplicate_keys()` (a combined guard over all three new files, mirroring
  `tools/mechanism_registry/registry.py`'s own `check_duplicate_keys(path)` machinery, generalized
  to three paths instead of one). Confirmed at close: all three committed seed files are genuinely
  empty (`edges: []` / `classifications: []`) — no illustrative row was committed to `registries/`;
  every example row used to prove `validate()` passes on non-empty data lives only inside
  `tests/unit/tools/test_semantic_control_plane_schema.py`'s own fixtures. No CI/Makefile wiring
  added (Out of Scope, per `TCK-20260920-MECHANISM-REGISTRY-CI-WIRING`'s own sibling pattern).
- **Step 6** — `docs/plans/simulation_semantic_control_plane/architecture.md` §3: replaced only the
  "Deliberately undecided..." paragraph (previously lines 86-90) with the actual chosen file
  paths/field names/YAML shape for all three schemas, still describing them as three distinct
  structures, citing `tools/semantic_control_plane/registry.py::validate_all()` and §7's
  UNKNOWN-permanence discipline. Confirmed via `git diff` that no other line of the file changed.
- **Verify-phase test choice recorded per plan.md**: `test_architecture_md_only_section_3_changed`
  was deliberately NOT written as a pytest test — per test_plan.md's own explicit recommendation,
  this is a Verify-phase `git diff docs/plans/simulation_semantic_control_plane/architecture.md`
  check (confirmed clean by hand during this implementation run), since a pytest test would need a
  pre-change file committed as a fixture to diff against, which is unusual for a doc-only check.

## Test Summary

New file `tests/unit/tools/test_semantic_control_plane_schema.py` — 25 tests, one deliberately-
broken fixture per invariant (never bundling two invariants into one test) plus the parser tests,
the non-derivation guard, the cross-schema real/seed-data pass, the two doc-guard tests, and a
subprocess-based CLI-entry-point regression test (added post-Implement, see Implementation Notes).
All 25 pass.

Regression: `tests/unit/tools/test_mechanism_registry.py` (100 tests) and
`tests/unit/tools/test_mechanism_registry_changed_code_check.py` (17 tests) both pass unchanged —
zero edits to `registries/mechanisms.yaml`'s `depends_on` field or `tools/mechanism_registry/`'s
existing functions.

Scoped run (per test_plan.md's "Scoped Pytest Commands"), re-run after the post-Implement CLI fix:
```
.venv/bin/python3 -m pytest tests/unit/tools/test_mechanism_registry.py tests/unit/tools/test_mechanism_registry_changed_code_check.py tests/unit/tools/test_semantic_control_plane_schema.py -v
→ 125 passed

pytest tests/unit/tools/ -k "frontmatter or docs_to_update or semantic_control_plane or mechanism_registry" -v
→ 168 passed, 135 deselected (run before the CLI-fix test was added; +1 test not yet reflected here)
```
Frontmatter validation (`tools/validate_frontmatter.py`) run individually against the ticket and
all three staging artifacts — all pass.

## Files Changed

- `tools/semantic_control_plane/__init__.py` (new)
- `tools/semantic_control_plane/rule_catalog.py` (new)
- `tools/semantic_control_plane/registry.py` (new; post-Implement fix — sys.path bootstrap moved
  above the `tools.*` imports so the documented CLI invocation actually runs, see Implementation
  Notes)
- `registries/rule_mechanism_edges.yaml` (new, seeded `edges: []`)
- `registries/mechanism_causal_edges.yaml` (new, seeded `edges: []`)
- `registries/rule_classifications.yaml` (new, seeded `classifications: []`)
- `tests/unit/tools/test_semantic_control_plane_schema.py` (new, 25 tests)
- `docs/plans/simulation_semantic_control_plane/architecture.md` (edited — §3's "Where it lives"
  paragraph only, lines 86-90 → now a longer replacement; no other line touched)
- `tickets/inprogress/TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION.md` (this ticket — Implementation
  Notes/Test Summary/Files Changed/Completion Summary/Acceptance Criteria/Status filled in)
- `staging_artifacts/TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION/plan.md` (created this run's
  Plan phase; edited post-Implement to add a "Deviations" section recording the CLI sys.path fix)
- `staging_artifacts/TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION/investigation.md` (created this
  run's Investigate phase)
- `staging_artifacts/TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION/test_plan.md` (created this run's
  Investigate phase)

## Completion Summary

Built the three physically-separate M0 schemas the Simulation Semantic Control Plane's
`architecture.md` §3 left "deliberately undecided" — Rule→Mechanism typed edges, Mechanism→Mechanism
directed causal edges, and per-Rule realization classification — each as a sibling YAML registry to
`registries/mechanisms.yaml`, plus a new `tools/semantic_control_plane/` validator package
(`validate_rule_mechanism_edges()`, `validate_mechanism_causal_edges()`,
`validate_rule_classifications()`, combined `validate_all()`, and a `check_duplicate_keys()` guard)
mirroring `tools/mechanism_registry/registry.py`'s own `validate()`/`check_duplicate_keys()` split.
Every invariant (enum membership, id resolution against a live `docs/world_rules/` heading scan and
`MechanismRegistry`, no-duplicate-triple/pair/rule_id, self-edge rejection, computed-not-stored
inverse lookup, and the schema-3 non-derivation rule) is proven against a deliberately-broken
fixture in the new 24-test `tests/unit/tools/test_semantic_control_plane_schema.py`, which passes
alongside the full, untouched Mechanism Registry regression suite. All three committed registry
files ship genuinely empty (no real Rule/Mechanism mapping rows — that is M1's own deliverable).
`architecture.md` §3's placeholder paragraph was replaced with the real chosen shape, citing the new
validator and §7's UNKNOWN-permanence discipline, with no other section of the file touched.
