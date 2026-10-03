---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER
artifact_type: test_plan
tags: [ai, workflows, determinism, architecture-reviewer]
---

# Test Plan — TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER

## Regression Surface

Existing tests that must keep passing, grouped by category (all unit-level; no
arena-combat/integration surface is touched by this ticket — it is agent-workflow tooling only):

- **unit — sibling gate-check modules** (must not break from a shared-package change):
  - `tests/tools/test_done_checker_static.py`
  - `tests/tools/test_parity_updater_static.py`
  - `tests/tools/test_mechanics_auditor_static.py`
  - `tools/gate_checks/__init__.py` import path must remain stable — the new
    `architecture_reviewer_static.py` module is an addition to this package, not a modification of
    the existing three; a broken `__init__.py` would fail all three sibling suites simultaneously.
- **unit — architecture guard lane** (must confirm the new module is *not* accidentally captured by
  it, per SEQUENCE.md decision 1 — this is a negative regression check, not a positive one):
  - `make lane-architecture` (`pytest tests/ -m "architecture"`) — this targets `src/`
    architecture guards, a different domain; the new `tools/gate_checks/` tests must carry no
    `architecture` marker and must not be discovered by this lane.
- **JS-side wiring** (`REVIEW_SCHEMA` gaining `verified_by`, and whichever new call site Plan
  chooses for the post-Implement static check per investigation.md Risk 1): no automated test
  exists for this today — confirmed absent by the `GATE-DET-PARITY-UPDATER` investigation
  (`package.json` has no test runner; no `.test.js` files anywhere in the repo), and this ticket
  does not introduce one. Verification of the JS wiring stays manual/structural review, consistent
  with all three DONE sibling tickets.

## New Tests Required

All new tests live in one new file, `tests/tools/test_architecture_reviewer_static.py`, importing
directly from `tools.gate_checks.architecture_reviewer_static` (no CLI/argparse, no pytest marker —
mirrors the three sibling test files). Fixture source files are written inline via
`tmp_path.write_text(...)` per test (mirroring `test_parity_updater_static.py`'s
`_write_ledger(tmp_path, ...)` helper pattern) rather than checked-in static fixture files, so each
test's exact violation/non-violation shape is visible next to its assertion.

Per investigation.md's conclusion, all three check functions must ship with an explicit,
in-docstring precision/recall caveat — the tests below exist specifically to prove each caveat is
accurate (a test that would fail if the caveat were false), not merely that the function runs.

### 1. Durable-state-mutation check

- **Name:** `test_flags_setattr_bypass_outside_allowlist_on_non_cache_field`
- **Category:** unit — coverage-honesty positive control
- **Verifies:** a fixture source file containing
  `object.__setattr__(entity, "combat", new_combat)` (a non-`_cache`-suffixed field, in a file path
  not in the module's known-legitimate-call-site allowlist) is flagged `FAIL`. This is the
  "clearest violation" case the ticket asks a first version to reliably catch.
- **Location:** `tests/tools/test_architecture_reviewer_static.py`

- **Name:** `test_does_not_flag_cache_suffix_setattr`
- **Category:** unit — negative control (false-positive regression guard)
- **Verifies:** a fixture mirroring the real `src/engine/apply.py` `replace()` idiom
  (`object.__setattr__(res, "_spatial_grid_cache", None)`) is **not** flagged — directly guards
  against the false-positive failure mode investigation.md identifies as the dominant risk (most
  real `object.__setattr__` call sites in this codebase are this exact idiom).
- **Location:** same file

- **Name:** `test_does_not_flag_allowlisted_call_site_outside_src_engine`
- **Category:** unit — negative control (regression guard against the rejected naive design)
- **Verifies:** a fixture reproducing the real, legitimate pattern at
  `src/world/environment.py:87` / `src/systems/strategic_systems/intelligence.py:240` (a
  `_cache`-suffixed `object.__setattr__` on `AuthoritativeState` from a file outside `src/engine/`)
  is not flagged merely for being outside `src/engine/` — proves the check does not use a
  directory-prefix test (confirmed nonexistent as `src/engine/authoritative_pipeline*`), only the
  field-name/allowlist logic.
- **Location:** same file

- **Name:** `test_flags_mutable_container_mutation_by_known_field_name`
- **Category:** unit — coverage-honesty positive control (the highest-value, hardest-to-catch case)
- **Verifies:** a fixture containing `entity.inventory.items.append(x)` or
  `state.global_resources["gold"] = 5` (subscript-`Store` or a mutating-method call on an
  attribute chain ending in a name from the small known-mutable-field allowlist,
  e.g. `.items`/`.global_resources`) is flagged. Must be paired with an explicit assertion (or a
  code comment cross-referenced in the test) that this is a **name-heuristic** match, not a
  type-resolved one — the test name/docstring should make the limitation visible, not just the
  behavior.
- **Location:** same file

- **Name:** `test_does_not_crash_on_unrelated_attribute_with_same_name`
- **Category:** unit — documents a known false-positive limitation (not a fix — a proof the
  limitation is real and disclosed, per investigation.md's honesty requirement)
- **Verifies:** a fixture where an unrelated, non-state object also has a `.items` attribute
  (`some_other_object.items.append(x)`) — assert the check's actual behavior (most likely: it
  *does* flag this, since name-only matching cannot distinguish object identity). This test exists
  to keep the documented caveat honest — if someone "fixes" the heuristic later without updating
  this test, the test forces the docstring/caveat to be revisited too.
- **Location:** same file

- **Name:** `test_direct_attribute_assignment_on_frozen_field_is_flagged`
- **Category:** unit — coverage-honesty positive control (the narrower, already-runtime-guarded
  case)
- **Verifies:** plain `entity.combat.hp = 5` syntax (not `object.__setattr__`) inside a fixture is
  also flagged. Documents explicitly (in the test or its docstring) that this pattern would already
  raise `FrozenInstanceError` at runtime — the check's value here is catching it before a test run,
  not catching a bug that would otherwise ship.
- **Location:** same file

- **Name:** `test_tolerates_unparseable_python_fixture`
- **Category:** unit — legacy-data tolerance (mirrors sibling try/except-continue convention)
- **Verifies:** a fixture file with a syntax error does not raise out of the check function; it
  returns a non-crashing status (`NA`/`SKIP` with evidence noting the parse failure), matching
  `parity_updater_static.py`'s `except Exception: continue` convention for malformed YAML.
- **Location:** same file

### 2. Raw-domain-object API-boundary check

- **Name:** `test_flags_route_returning_raw_domain_model_directly`
- **Category:** unit — coverage-honesty positive control
- **Verifies:** a fixture function under a `src/api/`-style path,
  `def get_entity(...) -> EntityState:` (or `AuthoritativeState`/`RegionState` — any name matching
  the known raw-model set sourced from `src/core/state.py`), is flagged `FAIL`.
- **Location:** same file

- **Name:** `test_does_not_flag_presenter_or_response_return_types`
- **Category:** unit — negative control
- **Verifies:** fixtures mirroring the real, confirmed-clean patterns —
  `def present_entity(entity: EntityState) -> Dict[str, Any]:` (presenter convention: raw type
  as *input*, `Dict`/`*Response` as *output*) and `def get_x(...) -> CampaignHistoryResponse:` —
  are not flagged. Directly encodes the convention investigation.md confirmed actually exists.
- **Location:** same file

- **Name:** `test_does_not_flag_private_helper_returning_raw_model`
- **Category:** unit — negative control (scope-boundary regression guard)
- **Verifies:** a fixture reproducing the real `decisions.py:_get_index(...) -> DecisionTraceIndex`
  shape (leading-underscore name, non-`Response`/non-`Dict` return type) is **not** flagged —
  proves the check is scoped to registered route handlers, not every function in the file.
- **Location:** same file

- **Name:** `test_does_not_flag_or_crash_on_unannotated_handler`
- **Category:** unit — documents a known blind spot (per investigation.md's disclosed caveat)
- **Verifies:** a fixture handler with no return annotation at all
  (`async def get_x(...):`) does not crash the scan and is reported as `NA`/unchecked rather than
  a silent `PASS` — keeps the "this check cannot see unannotated handlers" limitation visible in
  output rather than indistinguishable from "checked, clean."
- **Location:** same file

### 3. Reason/metadata-smuggling regex check

- **Name:** `test_flags_delimiter_joined_reason_field`
- **Category:** unit — coverage-honesty positive control
- **Verifies:** a fixture constructing a `reason=`/`metadata[...]=` value by joining multiple
  semantically distinct values with a delimiter for later re-parsing (e.g.
  `reason=f"{cause}|{severity}|{actor_id}"`, later consumed via `.split("|")` elsewhere in the same
  fixture) is flagged. Since investigation.md found **zero real historical incidents** of this
  pattern to mine from, this fixture must be explicitly commented in the test as
  *rule-derived, not incident-derived* — the test itself is part of the honesty record.
- **Location:** same file

- **Name:** `test_does_not_flag_plain_human_readable_reason_string`
- **Category:** unit — negative control
- **Verifies:** the real, confirmed-clean pattern from `src/lab/workflows.py:1176`
  (`return {"status": "BLOCKED", "reason": f"Malformed or unparseable run manifest: {e}"}` — a
  diagnostic message, not encoded durable meaning) is not flagged. This is the one real production
  code sample investigation.md found and confirmed clean; using it directly as the negative-control
  fixture keeps the test grounded in actual code rather than an invented example.
- **Location:** same file

- **Name:** `test_docstring_discloses_no_incident_corpus`
- **Category:** unit — honesty-caveat regression guard (specific to this check only, since it is
  the sole one of the three with zero empirical grounding)
- **Verifies:** the check function's (or module's) docstring contains language disclosing that its
  patterns are derived from the rule text, not from confirmed historical violations — a lightweight
  string-content assertion that prevents a future edit from silently dropping this disclosure.
- **Location:** same file

### 4. Aggregation / schema-shape parity with siblings

- **Name:** `test_run_all_returns_list_of_condition_status_evidence_dicts`
- **Category:** unit — structural parity with the three DONE siblings
- **Verifies:** the module's aggregate `run_*()` function returns `list[dict]` with
  `condition`/`status`/`evidence` keys (or the equivalent shape used by
  `done_checker_static.run_static_precheck` / `parity_updater_static.cross_reference_touched`),
  keeping the `verified_by` field's eventual construction mechanical rather than ad hoc.
- **Location:** same file

## Scoped Pytest Commands

```
pytest tests/tools/test_architecture_reviewer_static.py -v
pytest tests/tools/ -v
```

Do **not** run `pytest tests/` or add an `architecture` marker to any test in this file — this
ticket's tests are agent-workflow-hygiene tests (`tools/gate_checks/`), a different domain from the
`lane-architecture` simulation-code guard lane (confirmed by the sibling tickets' own
`Makefile:185` finding).

## Anti-Drift Test Guards

- **Not-in-lane-architecture guard**: a `pytest tests/ -m "architecture"` run (or a direct check of
  the new test file's collected markers) must show zero tests from
  `test_architecture_reviewer_static.py` — catches accidental scope bleed into the simulation-code
  architecture-guard lane.
- **False-positive-dominance guard** (`test_does_not_flag_cache_suffix_setattr`,
  `test_does_not_flag_allowlisted_call_site_outside_src_engine`): these two negative controls are
  the single most important anti-drift guard in this whole ticket — investigation.md's central
  finding is that a naive version of the durable-state check would flag the codebase's own correct,
  existing code almost everywhere. If a future edit to the allowlist or field-name pattern breaks
  either of these, the check has regressed into the rejected naive design.
- **No-nonexistent-path guard**: a test (or an assertion inside one of the above) confirming the
  module contains no reference to a literal `src/engine/authoritative_pipeline` glob/path — guards
  against a future edit reintroducing the ticket's original (confirmed-wrong) path assumption.
- **Honesty-disclosure guard** (`test_docstring_discloses_no_incident_corpus`, plus the naming of
  `test_flags_delimiter_joined_reason_field` and
  `test_does_not_crash_on_unrelated_attribute_with_same_name`): these tests exist specifically so a
  later contributor cannot quietly strengthen the docstring's claims (e.g. claiming a real incident
  corpus, or claiming full type-resolution precision) without also updating the test that would
  contradict the stronger claim.
- **Legacy-data tolerance guard** (`test_tolerates_unparseable_python_fixture`): confirms the module
  follows the same try/except-continue convention as `parity_updater_static.derive_mapping`
  (skip a file that fails to parse rather than raising) — required so the check can run against
  the full `src/` tree, including any legacy file, without crashing the Review/post-Implement gate
  it backstops.
