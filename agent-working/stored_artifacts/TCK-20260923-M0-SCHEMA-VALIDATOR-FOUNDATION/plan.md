---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION
artifact_type: plan
tags: [architecture, schema, documentation, testing]
---

# Implementation Plan — TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION

## Summary

Build three new, physically-separate YAML registries (Rule→Mechanism edges, Mechanism→Mechanism
causal edges, per-Rule realization classification) plus one new validator package that mirrors
`tools/mechanism_registry/registry.py`'s own `validate() -> List[str]` / `check_duplicate_keys()`
split, proven against deliberately-broken fixtures the same way the original Mechanism Registry
was, then rewrite `architecture.md` §3's placeholder paragraph to name the real, chosen shape. The
plan resolves all three decisions the ticket/investigation left open (file format, self-edge
handling, validator module location) rather than deferring them — see "Decisions Made by This
Plan" below. Work proceeds bottom-up: build the new rule_id corpus parser first (both schema 1 and
schema 3 need it), then each of the three schemas independently, then a combined validator entry
point, then the doc-sync last (so the doc text names the shape that actually got built, not a
predicted one).

## Decisions Made by This Plan

1. **File format/path**: three new YAML files, sibling to `registries/mechanisms.yaml`, mirroring
   its own dict-of-list-of-dicts shape (`registries/mechanisms.yaml:1-11` header precedent,
   `registries/mechanisms.yaml:109-135` sample entry) — `registries/rule_mechanism_edges.yaml`,
   `registries/mechanism_causal_edges.yaml`, `registries/rule_classifications.yaml`. Adopted as
   investigation.md's own recommendation (Risks and Open Questions (a)): block-scalar `evidence`
   fields need YAML's multi-line support that flat JSONL (the `system_registry.jsonl` alternative,
   `tools/mechanism_registry/system_registry.py:140-141`) would awkwardly escape, and these rows are
   correctable (a re-reviewed classification can change), not append-only, unlike
   `system_registry.jsonl`'s genuinely-append-only vocabulary entries.
2. **Self-edge**: `producer_mechanism_id == consumer_mechanism_id` on one row is **rejected** as a
   validator error. Adopted as investigation.md's own recommendation (Risks and Open Questions
   (b)): every real example in `architecture.md` (`PRODUCES_INPUT_FOR`/`CONSUMES_RESULT_OF`,
   lines 80-81) describes two distinct mechanisms, and a self-edge would make the computed
   inverse-lookup return a mechanism as one of its own inputs, which is not a causal fact the
   vocabulary describes. Multi-node cycles (A→B→A across two distinct rows) are explicitly **not**
   checked — no AC requires it, and unlike `depends_on`'s invariant 2 (`registry.py:318-346`,
   confirmed by direct read), nothing in `architecture.md`/`roadmap.md` requires the causal-edge
   graph to be acyclic.
3. **Validator module location**: a new sibling package, `tools/semantic_control_plane/`, not an
   extension of `tools/mechanism_registry/registry.py`. Adopted as investigation.md's own
   recommendation: these three schemas' `rule_id` resolution depends on a `docs/world_rules/`
   corpus scan that `registry.py` has never needed (confirmed: `registry.py` has no
   `docs/world_rules` reference in its current ~500 lines), and `registries/mechanisms.yaml` is
   only a foreign-key *target* for the new schemas, not their own home file. The new package
   mirrors `tools/mechanism_registry/`'s own shape (`tools/mechanism_registry/__init__.py`
   re-exporting `registry.py`'s public names) and **imports, never modifies**,
   `tools.mechanism_registry.registry.MechanismRegistry` to resolve `mechanism_id` values (reusing
   `registry.py:156-162`'s existing loader rather than re-parsing `mechanisms.yaml`).

None of these three needed to be raised as an Unresolved Question: the ticket's own Scope/
Assumptions section explicitly assigns all three to "this ticket" to resolve, and investigation.md
already produced a reasoned, evidence-backed recommendation for each with no conflicting design
doc found.

## Steps

### Step 1 — Rule ID corpus parser
**Files:** `tools/semantic_control_plane/__init__.py` (new), `tools/semantic_control_plane/rule_catalog.py` (new), `tests/unit/tools/test_semantic_control_plane_schema.py` (new — parser tests only in this step)
**Change:** Implement `scan_rule_ids(base_path: Path = Path("docs/world_rules")) -> set[str]`
that walks `base_path.rglob("*.md")`, **excludes any path under a `review-exports/` directory
component**, and matches each line against `^## ([A-Z]{2,8}-[0-9]{2})\b` (confirmed by direct
regex sweep in investigation.md's "Current Behavior" section to match exactly 172 headings across
45 non-review-export files — same count as the ticket's own stated fact; real examples:
`docs/world_rules/places-culture/territory-control.md:27`, `## TERR-01 — Territorial claim, de
facto control, ...`). This is genuinely new code — no prior-art module exists to reuse (confirmed:
investigation.md Assumptions/Open Questions, "does not exist yet and must be built new"). Also
export a small `__init__.py` that re-exports `scan_rule_ids`, mirroring
`tools/mechanism_registry/__init__.py`'s own re-export shape.
**Do NOT touch:** any file under `docs/world_rules/` (read-only scan); do not attempt to also
parse or index `review-exports/` content — exclude it entirely, do not special-case its different
heading vocabulary (`## Rule Inventory`, `## Repository Findings`, etc.) inside the same regex.
**Verify:** `test_rule_id_scanner_finds_known_rule_ids` (assert `TERR-01` and at least one ID from
a second family are present), `test_rule_id_scanner_excludes_review_exports` (assert no ID is
picked up from a `docs/world_rules/review-exports/*.md` file even though those files mention Rule
IDs inline in prose — the exact untested risk investigation.md's own "Risks and Open Questions"
section flags).

### Step 2 — Rule→Mechanism edge schema (schema 1)
**Files:** `registries/rule_mechanism_edges.yaml` (new, empty `edges: []` seed), `tools/semantic_control_plane/registry.py` (new)
**Change:** Create the YAML file with a header comment (mirroring
`registries/mechanisms.yaml:1-11`'s own explanatory-header pattern) and a single top-level key
`edges:` (a list of dicts: `rule_id`, `mechanism_id`, `edge_type`, `evidence`, `date`). Seed it as
genuinely empty (`edges: []`), not illustrative rows — see Step 5 for why. Implement
`validate_rule_mechanism_edges(data: dict, known_rule_ids: set[str], known_mechanism_ids: set[str]) -> List[str]`
mirroring `registry.py:273-320`'s per-invariant-loop, append-don't-raise pattern
(`registry.py:45-49` docstring rationale, "build the failure loud"): (1) `edge_type` must be one
of `{REALIZES, PARTIALLY_REALIZES, CONSTRAINED_BY}`; (2) `rule_id` must resolve against
`known_rule_ids` (Step 1's `scan_rule_ids()` output); (3) `mechanism_id` must resolve against
`known_mechanism_ids` (loaded via `MechanismRegistry(...).all_mechanisms()` and its `id` field,
reusing `registry.py:156-162`/`registry.py:168-170`'s existing loader — do not re-implement
`mechanisms.yaml` parsing); (4) no duplicate `(rule_id, mechanism_id, edge_type)` triple (two rows
sharing `rule_id`+`mechanism_id` but a *different* `edge_type` must NOT error — the triple is the
key, not the pair).
**Other writers to `registries/mechanisms.yaml` (read dependency of this step):** none this step
writes to — `mechanisms.yaml` is loaded read-only via the existing `MechanismRegistry` class, which
itself has no write path (the file is hand-edited only, per `registries/mechanisms.yaml:6-9`'s own
"NOT append-only... correcting a wrong state in place... is expected, ordinary maintenance" header
note — this step never edits it). Confirmed no existing tool in `tools/` glob-scans `registries/*`
generically (checked: `tag_registry.py`, `layer_registry.py`, `capability_envelope_baseline.py`,
`glossary_registry.py`, `system_registry.py` each reference only their own dedicated filename), so
the new `rule_mechanism_edges.yaml` file cannot be silently picked up or mutated by an unrelated
existing tool.
**Do NOT touch:** `registries/mechanisms.yaml` itself or its `depends_on` field; do not add an
`edge_type`-shaped field to any future schema-2 row (that merge is the exact mistake
`roadmap.md` lines 48-51 names as already-happened once).
**Verify:** `test_rule_mechanism_edge_schema_accepts_valid_row`,
`test_rule_mechanism_edge_schema_accepts_empty_data`, `test_validator_rejects_invalid_edge_type`,
`test_validator_rejects_unresolved_rule_id`, `test_validator_rejects_unresolved_mechanism_id`,
`test_validator_rejects_duplicate_rule_mechanism_edge_type_triple` (+ its same-pair-different-
edge_type companion, must NOT error).

### Step 3 — Mechanism→Mechanism causal edge schema (schema 2) + computed inverse
**Files:** `registries/mechanism_causal_edges.yaml` (new, empty `edges: []` seed), `tools/semantic_control_plane/registry.py` (extend)
**Change:** Create the YAML file, top-level key `edges:` (list of dicts: `producer_mechanism_id`,
`consumer_mechanism_id`, `evidence`, `date` — **no `edge_type` field**, per AC #5). Implement
`validate_mechanism_causal_edges(data: dict, known_mechanism_ids: set[str]) -> List[str]`: (1)
`producer_mechanism_id` and `consumer_mechanism_id` must each resolve against `known_mechanism_ids`
(same `MechanismRegistry`-sourced set as Step 2, loaded once and passed in — do not reload the file
twice); (2) **reject** `producer_mechanism_id == consumer_mechanism_id` on the same row (Decision 2
above); (3) no duplicate directed `(producer_mechanism_id, consumer_mechanism_id)` pair — the
reversed pair `(B, A)` after `(A, B)` already exists must NOT error, since the edge is directed and
both are independently valid facts. Implement `consumers_of(mechanism_id, edges) -> List[str]` (and
its symmetric `producers_for(mechanism_id, edges) -> List[str]`) as pure functions computing the
traversal over the loaded `edges` list at call time — zero hand-authored inverse rows in storage,
mirroring `registry.py:174-182`'s own `dependents_of()` computed-traversal docstring rationale
("a stored dependent-count would disagree with the real edges within a month").
**Other writers:** none — this is a brand-new file, same "no generic `registries/*` scanner exists"
confirmation as Step 2. The existing `depends_on` field (`registries/mechanisms.yaml:32-46` header,
invariant 1 at `registry.py:309-317`, cycle-check invariant 2 at `registry.py:318-346`) is a
functionally distinct, narrower axis (unordered-in-time prerequisite, not a directed causal-produce
fact) — this step's code never reads or writes `depends_on`, and does not reuse its cycle-check
logic (Decision 2 above explains why: multi-node cycle-freedom is not required here the way it is
for `depends_on`).
**Do NOT touch:** schema 1's `edge_type` enum or file; `depends_on` field/header/semantics.
**Verify:** `test_mechanism_causal_edge_schema_has_no_shared_edge_type_field`,
`test_validator_rejects_unresolved_producer_mechanism_id`,
`test_validator_rejects_unresolved_consumer_mechanism_id`,
`test_validator_rejects_duplicate_directed_causal_pair` (+ reversed-pair-not-a-duplicate
companion), `test_validator_rejects_self_producing_causal_edge`,
`test_causal_edge_inverse_is_computed_not_stored`.

### Step 4 — Per-Rule realization classification schema (schema 3) + non-derivation guard
**Files:** `registries/rule_classifications.yaml` (new, empty `classifications: []` seed), `tools/semantic_control_plane/registry.py` (extend)
**Change:** Create the YAML file, top-level key `classifications:` (list of dicts: `rule_id`,
`classification`, `evidence`, `review_date`). Implement
`validate_rule_classifications(data: dict, known_rule_ids: set[str]) -> List[str]`: (1)
`classification` must be one of `{SUPPORTED, PARTIAL, CONFLICTING, MISSING, INERT-OFF, UNKNOWN}`
(vocabulary confirmed already in prose use at
`docs/world_rules/places-culture/territory-control.md:56-59`, TERR-01's own "Repository evidence:
CONFLICTING... MISSING..." line, cited by `architecture.md` §4 as the source this schema
formalizes); (2) `rule_id` must resolve against `known_rule_ids` (Step 1's parser); (3) no
duplicate `rule_id` (at most one record per Rule ID present in the file — a Rule with **no** record
is not an error, per §7's UNKNOWN-permanence discipline; only a *second* row for an already-present
`rule_id` is rejected). `UNKNOWN` must be accepted with **zero** special-case normalization
anywhere in the load/validate path — no code may rewrite a loaded `"UNKNOWN"` string to `"MISSING"`
or drop it.
**Non-derivation guard (AC #13, enforced by omission):** do **not** write any function, anywhere in
`tools/semantic_control_plane/`, whose only parameters are schema-1/schema-2 edge data and whose
return value or side effect is a schema-3 classification value — not even as an unused/dead
utility. Per test_plan.md's two-part proof, implement (1) only if a cheap grep-based early-warning
check is trivial (e.g. flag any function whose name contains both `edge` and `classif`, reviewed by
a human, never auto-failing), and (2) as the primary, required proof, record an explicit
confirmation in this ticket's own Implementation Notes stating no such function was written — do
not consider Step 4 complete without that confirmation line being written, per §3/§4 of
`architecture.md` and `docs/plans/mechanism_tier_model_initiative.md` §3's "declared, not derived"
precedent for the `system` tier.
**Other writers:** none — new file, same "no generic `registries/*` scanner" confirmation as Steps
2-3. The World Rule Catalog's own review-export prose (e.g.
`docs/world_rules/review-exports/places-territory-batch-11a-review.md`) is cited only as an
*evidence precedent* for the classification vocabulary — this step does not parse or transcribe
that file; populating real rows from it is explicitly M1, out of scope here.
**Do NOT touch:** schema 1/2's files or fields; do not implement any edge→classification
derivation helper, not even as a documented-but-unused function.
**Verify:** `test_rule_classification_schema_holds_one_record_per_rule`,
`test_validator_rejects_invalid_classification_value`,
`test_validator_rejects_duplicate_rule_id_in_classification_registry`,
`test_unknown_classification_is_accepted_and_preserved`,
`test_no_function_derives_classification_from_edges`.

### Step 5 — Combined validator entry point + duplicate-key guard + real/empty pass
**Files:** `tools/semantic_control_plane/registry.py` (extend), `tests/unit/tools/test_semantic_control_plane_schema.py` (extend)
**Change:** Implement `validate_all(base_path: Path = Path("registries"), world_rules_path: Path = Path("docs/world_rules")) -> List[str]` that: loads the three YAML files via `yaml.safe_load`,
resolves `known_rule_ids` via Step 1's `scan_rule_ids(world_rules_path)`, resolves
`known_mechanism_ids` via `MechanismRegistry().all_mechanisms()`, calls all three schema-specific
`validate_*` functions from Steps 2-4, and returns the merged error list (mirroring
`registry.py:273-283`'s own merge-don't-raise philosophy). Also implement a
`check_duplicate_keys()`-equivalent for each of the three new files, reusing/mirroring
`registry.py:210-257`'s `_load_yaml_checking_duplicate_keys`/`DuplicateYamlKeyError` machinery
(these are hand-edited YAML files with the identical silent-last-key-wins risk that
`mechanisms.yaml` itself suffered once for real — `registry.py:216-234`'s own incident docstring).
Confirm the three seed files committed in Steps 2-4 are genuinely empty
(`edges: []`/`classifications: []`), per Out of Scope's "no real mapping entries... populated" —
this makes the "real/empty data" AC line provable directly against the committed files, while the
"seed data" half of that AC line is proven only inside a test fixture (a small closed synthetic
example), never as a committed row that could later be mistaken for a real M1 finding.
**Other writers:** none — `tools/semantic_control_plane/registry.py`'s own `validate()`/
`check_duplicate_keys()` in `tools/mechanism_registry/` are read/imported only (via
`MechanismRegistry`), never modified by this step; no CI/make-target wiring is added here (Out of
Scope line, distinct ticket `TCK-20260920-MECHANISM-REGISTRY-CI-WIRING`'s own sibling pattern) —
`validate_all()` is invoked only by this ticket's own tests until a future ticket wires it in.
**Do NOT touch:** `tools/mechanism_registry/registry.py`'s existing `validate()`/
`check_duplicate_keys()` functions (import only); no `Makefile`/CI config changes.
**Verify:** `test_all_three_schemas_pass_on_real_seed_data`.

### Step 6 — Doc-sync: `architecture.md` §3 rewrite
**Files:** `docs/plans/simulation_semantic_control_plane/architecture.md` (lines 86-90 only, confirmed by direct read: the `**Where it lives.** Deliberately undecided...` paragraph)
**Change:** Replace that single paragraph with concrete text naming: the three chosen file paths
(`registries/rule_mechanism_edges.yaml`, `registries/mechanism_causal_edges.yaml`,
`registries/rule_classifications.yaml`), their field names (as built in Steps 2-4), and their YAML
serialization format (mirroring `mechanisms.yaml`'s own shape, per Decision 1 above) — while
continuing to describe them as three distinct structures (do not collapse the paragraph into one
generic description) and continuing to cite the validator (name
`tools/semantic_control_plane/registry.py::validate_all()`) and §7's UNKNOWN-permanence discipline,
matching the surrounding paragraphs' own citation style. The immediately-following "Two distinct
records, not one" paragraph (current lines 92-101) does not reference the undecided file path and
needs no edit — confirm it still reads correctly after the §3 paragraph above it changes, but do
not touch its text.
**Do NOT touch:** any line of `architecture.md` outside lines 86-90 (all of §§1/2/4-9, and the rest
of §3 itself); `roadmap.md`, `rollout_plan.md`, `mechanism_tier_model_initiative.md`,
`registries/mechanisms.yaml`'s header — investigation.md's "Docs Requiring Update" section confirmed
none of these require a change for this ticket.
**Verify:** `test_architecture_md_no_longer_says_deliberately_undecided`,
`test_architecture_md_section_3_names_chosen_schema`; `test_architecture_md_only_section_3_changed`
is a Verify-phase `git diff docs/plans/simulation_semantic_control_plane/architecture.md` check
(hand/CI-reviewed), not a new pytest test, per test_plan.md's own explicit recommendation — record
that choice in Implementation Notes so it is not later flagged as a missing test.

## Scope Guards

- No real Rule↔Mechanism mapping rows, causal edges, or classification records for any actual
  Rule or Mechanism — all three committed registry files stay genuinely empty; any illustrative
  row lives only inside a test fixture, never a committed `registries/` row.
- No Cartesian-product generation of Rule×Mechanism pairs; unmapped pairs stay `UNKNOWN`
  permanently and are never auto-filled or auto-generated.
- No CI/make-target wiring for the new validator — that is `TCK-20260920-MECHANISM-REGISTRY-CI-
  WIRING`'s own later-layer concern, not this ticket's.
- No edit to `registries/mechanisms.yaml`'s `depends_on` field, its header comment, or any of its
  existing eleven invariants/functions in `registry.py`.
- No function anywhere that takes only schema-1/schema-2 edge data as input and returns or writes
  a schema-3 classification value — enforced by omission, not by a comment.
- No merge of schema 1's `edge_type` enum into schema 2's row shape, or vice versa — the two stay
  physically separate files with disjoint field sets.
- No edit to `architecture.md` outside its own §3 lines 86-90.
- No edit to `roadmap.md`, `rollout_plan.md`, or `mechanism_tier_model_initiative.md` — investigation
  confirmed none require a change.
- No M1/M2/M3/M4 deliverable (real edge population, Rule Catalog re-verification, review-export
  promotion) of any kind.

## Dependency Map

- **Step 1** (rule_id parser) has no dependencies. Blocks Step 2 and Step 4 (both need
  `scan_rule_ids()` for `rule_id` resolution). Step 3 does not depend on Step 1 (schema 2 only
  resolves mechanism ids) and can be built in parallel with Step 1/2/4 if desired, though the
  ordered numbering above is the recommended sequence.
- **Step 2** depends on Step 1.
- **Step 3** is independent of Steps 1/2/4 (only needs `MechanismRegistry`, which already exists
  outside this ticket).
- **Step 4** depends on Step 1.
- **Step 5** depends on Steps 2, 3, and 4 (merges all three `validate_*` functions).
- **Step 6** depends on Step 5 (the doc text must name the shape as actually built, including the
  final `validate_all()` function name), and transitively on Steps 1-4.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Schema 1 accepts `{rule_id, mechanism_id, edge_type, evidence, date}`, `validate()` empty on valid/empty | Step 2 | `test_rule_mechanism_edge_schema_accepts_valid_row`, `test_rule_mechanism_edge_schema_accepts_empty_data` |
| Rejects `edge_type` outside the 3-value enum | Step 2 | `test_validator_rejects_invalid_edge_type` |
| Rejects unresolved `rule_id`, separately unresolved `mechanism_id` | Step 1, Step 2 | `test_validator_rejects_unresolved_rule_id`, `test_validator_rejects_unresolved_mechanism_id` |
| Rejects duplicate `(rule_id, mechanism_id, edge_type)` triple | Step 2 | `test_validator_rejects_duplicate_rule_mechanism_edge_type_triple` |
| Schema 2 stores only `producer_mechanism_id, consumer_mechanism_id, evidence, date` — no shared `edge_type` | Step 3 | `test_mechanism_causal_edge_schema_has_no_shared_edge_type_field` |
| Rejects unresolved `producer_mechanism_id`, separately `consumer_mechanism_id` | Step 3 | `test_validator_rejects_unresolved_producer_mechanism_id`, `test_validator_rejects_unresolved_consumer_mechanism_id` |
| Rejects duplicate directed `(producer, consumer)` pair | Step 3 | `test_validator_rejects_duplicate_directed_causal_pair` |
| Inverse-lookup is computed, zero hand-authored inverse rows | Step 3 | `test_causal_edge_inverse_is_computed_not_stored` |
| `depends_on` unchanged | Steps 2-3 (scope guard) | `tests/unit/tools/test_mechanism_registry.py` full suite unchanged (regression run) |
| Schema 3 holds exactly one record per Rule ID | Step 4 | `test_rule_classification_schema_holds_one_record_per_rule`, `test_validator_rejects_duplicate_rule_id_in_classification_registry` |
| Rejects classification outside 6-item enum, rejects duplicate `rule_id` | Step 4 | `test_validator_rejects_invalid_classification_value`, `test_validator_rejects_duplicate_rule_id_in_classification_registry` |
| `UNKNOWN` accepted and preserved, never rewritten to `MISSING` | Step 4 | `test_unknown_classification_is_accepted_and_preserved` |
| No function derives/writes schema-3 classification from schema-1/2 edges | Step 4 | `test_no_function_derives_classification_from_edges` + Implementation Notes confirmation |
| Validator returns zero errors on real/empty/seed data across all three schemas | Step 5 | `test_all_three_schemas_pass_on_real_seed_data` |
| "Deliberately undecided" no longer appears in `architecture.md` §3 | Step 6 | `test_architecture_md_no_longer_says_deliberately_undecided` |
| §3 replacement names chosen paths/fields/format, 3 distinct structures, cites validator + §7 | Step 6 | `test_architecture_md_section_3_names_chosen_schema` |
| No section of `architecture.md` other than §3 altered | Step 6 | `test_architecture_md_only_section_3_changed` (Verify-phase `git diff`) |

## Anti-Drift Notes

- **Non-derivation (schema 3) is the highest-risk drift.** Even an innocuous-looking "suggest a
  classification from edge counts" helper is the same forbidden derivation as a "set" helper — do
  not write it, not even as dead code, and do not defer the Implementation Notes confirmation to a
  later ticket.
- **Do not let schema 1 and schema 2 re-converge into one file/row-shape.** `roadmap.md` lines
  48-51 name this exact mistake as something an earlier draft already did; keep the two files and
  their field sets disjoint.
- **The rule_id parser must actually be proven to exclude `review-exports/`**, not just assumed
  to — investigation.md flagged this as a real, previously-untested risk; Step 1's own
  `test_rule_id_scanner_excludes_review_exports` is the proof, not a documentation note.
- **`depends_on` is a different axis, not a smaller version of schema 2.** Do not reuse
  `registry.py`'s invariant-2 cycle-check logic for schema 2 — Decision 2 above explicitly leaves
  multi-node cycles unchecked for schema 2, unlike `depends_on`'s required acyclicity.
- **The three seed registry files must ship empty**, not with an illustrative row committed as if
  it were real — any example row belongs only in a test fixture. Confirm this at Step 5 before
  closing the ticket.
- **`architecture.md` §3's surrounding paragraphs (lines 92-101 onward) are settled text** — verify
  the Step 6 edit does not require touching them, and if it turns out it does, stop and re-flag
  rather than silently expanding the edit's line range.

## Unresolved Questions

None. All three items investigation.md flagged as open (file format/path, self-edge handling,
validator module location) are resolved above under "Decisions Made by This Plan," each backed by
investigation.md's own evidence and recommendation with no conflicting design-doc constraint found.

## Deviations

- **Step 5 (`tools/semantic_control_plane/registry.py`)**: the documented CLI invocation
  (`python3 tools/semantic_control_plane/registry.py`, cited in the module docstring and all three
  registry file headers) initially failed with `ModuleNotFoundError: No module named 'tools'` —
  the `from tools.mechanism_registry.registry import MechanismRegistry` absolute import ran before
  any repo-root `sys.path` bootstrap, unlike its sibling `tools/mechanism_registry/registry.py`
  which inserts its own path before importing. Caught post-Implement (Architecture-Verify shadow
  candidate reviewer, independently reproduced before acting on it), not by the plan or the
  original test suite — no test previously exercised the `__main__` entry point, only
  `validate_all()` in-process. Fixed by moving the `_REPO_ROOT` computation above the `tools.*`
  imports and inserting it into `sys.path` first (matching the sibling's pattern), plus a new
  regression test (`test_documented_cli_invocation_actually_runs`) that runs the CLI as a real
  subprocess with no pytest-inherited `sys.path`, so this class of gap can't silently recur.
