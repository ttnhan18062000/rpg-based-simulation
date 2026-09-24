---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260923-STATUS-VOCABULARY-RECONCILIATION
artifact_type: test_plan
tags: [architecture, schema, taxonomy, registry, documentation]
---

# Test Plan — TCK-20260923-STATUS-VOCABULARY-RECONCILIATION

## Regression Surface

This is primarily a documentation/vocabulary-contract ticket (AC 7 explicitly forbids any mechanism
row reclassification). The regression surface is: prove nothing enforced today silently changed.

**Unit — Mechanism Registry** (`tests/unit/tools/test_mechanism_registry.py`, 1148 lines, all must
still pass):
- `test_validator_accepts_every_valid_state` (parametrized over `VALID_STATES`) and
  `test_validator_rejects_invalid_state` — must still pass unchanged if AC 4's recommendation (no new
  registry field) is followed; if the planner instead adds a field, these plus every
  `test_validator_accepts_*`/`test_validator_rejects_*` pair must be re-run to confirm no existing
  invariant regressed.
- `test_real_registry_passes_validation` — the real 93-row file must still validate cleanly after any
  header-comment or cross-reference edit (a YAML comment change must not break `yaml.safe_load()`
  parsing or trip `check_duplicate_keys()`).
- `test_real_registry_has_no_duplicate_keys` — guards against an imprecise header edit accidentally
  duplicating a top-level key.
- `test_registry_seed_meets_expected_scale` — guards the 93-mechanism count itself; must show zero
  row count change.
- `test_reader_get_state_known_id`, `test_reader_get_verification_known_and_unknown` — guard
  `MechanismRegistry`'s read API surface if the axis-model doc's cross-reference edit touches
  `registry.py`'s docstrings near these methods.

**Unit — Semantic Control Plane** (`tests/unit/tools/test_semantic_control_plane_schema.py`):
- Full file must still pass. `VALID_RULE_CLASSIFICATIONS` must not change under this ticket (AC 8);
  any test asserting its exact six-value set is a direct regression guard for that.

**Integration — none identified.** No `src/` runtime code path reads any of the four vocabularies
for gameplay behavior (all four are tooling/documentation contracts consumed by validators and
rendered views, not by the simulation kernel). No arena-combat or scenario-level regression surface
applies.

## New Tests Required

Per AC 6 ("if a registry field is added... proven to reject a deliberately-invalid fixture") — this
plan's investigation recommends AC 4 resolve to **no new registry field**, so the tests below are
listed as conditional: build only if the planner overrides the investigation's recommendation.

1. **Test name:** `test_validator_rejects_invalid_reach_value` (name illustrative; adjust to the
   field name the plan actually chooses, if any)
   **Category:** unit
   **What it verifies:** a deliberately-broken fixture with an out-of-vocabulary value for the new
   field is rejected by `validate()`, matching the discipline `TCK-20260920-MECHANISM-REGISTRY-CI-
   WIRING` and M0's own validator both already established.
   **Where it lives:** `tests/unit/tools/test_mechanism_registry.py`, alongside the existing
   `test_validator_rejects_invalid_state`/`test_validator_rejects_unknown_verdict` pattern.
   **Condition:** only required if AC 4 is resolved by adding a field (contrary to this
   investigation's recommendation).

2. **Test name:** `test_no_mechanism_state_or_verdict_changed` (AC 7 regression guard)
   **Category:** unit / architecture guard
   **What it verifies:** a diff-based or snapshot-based check that every mechanism row's `state` and
   `verified.verdict` (where present) match a pre-ticket baseline snapshot — a direct, automatable
   proof of AC 7 beyond "the PR diff looks clean." Practical approach: at ticket start, capture
   `{id: (state, verdict_or_None)}` for all 93 rows (e.g. into a fixture or the test itself as a
   literal baseline); at Verify time, assert the live registry's own values match exactly.
   **Where it lives:** `tests/unit/tools/test_mechanism_registry.py`, new test function, or a
   standalone script run once at Verify (not necessarily a permanent pytest test if it would require
   hand-maintaining a 93-row baseline going forward — the planner should decide standalone-script vs.
   permanent-test based on whether future tickets are expected to touch `state`/`verdict` often
   enough that a permanent regression guard earns its maintenance cost).

3. **Test name:** `test_axis_model_doc_exists_and_is_cross_referenced` (documentation-contract check)
   **Category:** unit / architecture guard
   **What it verifies:** the chosen axis-model doc path exists, and each of the four vocabulary homes
   (`registries/mechanisms.yaml` header, `core_rpg_design_direction.md` §10,
   `simulation_semantic_control_plane/architecture.md` §3/§4, `mechanism_registry/registry.py`
   docstring) contains a literal reference (e.g. the doc's path string) to it — a lightweight,
   automatable proof of AC 5 rather than relying on manual review alone.
   **Where it lives:** a new small test module, e.g.
   `tests/unit/tools/test_status_axis_model_cross_references.py`, or folded into
   `tests/unit/tools/test_mechanism_registry.py` if the planner prefers not to add a new test file
   for one check.

## Scoped Pytest Commands

```
python3 -m pytest tests/unit/tools/test_mechanism_registry.py -q
python3 -m pytest tests/unit/tools/test_semantic_control_plane_schema.py -q
python3 -m pytest tests/unit/tools/test_status_axis_model_cross_references.py -q   # if created
```

Never `pytest tests/` — scope is the mechanism-registry and semantic-control-plane tool tests only;
no other domain's tests are touched by this ticket's scope (documentation + two small tool-docstring
edits, no `src/` changes expected).

## Anti-Drift Test Guards

- **`test_registry_seed_meets_expected_scale`** (existing) doubles as an anti-scope-creep guard: if
  it fails, a mechanism row was added or removed, which this ticket's scope explicitly forbids
  (Out of Scope: "Re-classifying any actual mechanism... Zero row-level reclassification").
- **`test_validator_accepts_every_valid_state`/`test_validator_accepts_all_three_verdicts`**
  (existing, parametrized) guard against an accidental narrowing of `VALID_STATES`/`VALID_VERDICTS`
  while editing the header comment or docstring for the cross-reference addition (AC 5) — a
  copy-paste edit to the comment block sitting directly above these frozensets is the most plausible
  accidental-scope-creep vector in this ticket.
- **`tests/unit/tools/test_semantic_control_plane_schema.py`**'s own `VALID_RULE_CLASSIFICATIONS`
  assertions guard AC 8: if this ticket's homograph-2 recommendation (do not rename `MISSING`/
  `INERT-OFF`) were violated by an implementer tempted to "fix" the collision by renaming, this suite
  fails immediately, before any M1 data is populated against the now-changed schema.
- **New test 2 above (`test_no_mechanism_state_or_verdict_changed`)** is the primary anti-drift guard
  purpose-built for this ticket: it is the only mechanism that would catch a well-intentioned but
  out-of-scope "let me just fix `tactical_decision` while I'm here" edit, which the investigation
  explicitly flags as the most tempting scope-creep vector given how much prose the STARVED
  discussion above devotes to that exact row.
