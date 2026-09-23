---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION
artifact_type: test_plan
tags: [architecture, schema, documentation, testing]
---

# Test Plan — TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION

## Regression Surface

Existing tests that must keep passing — nothing in this ticket's Scope touches their subject
matter directly (no edit to `registries/mechanisms.yaml`'s `depends_on` field, no edit to
`registry.py`'s existing functions), but the new validator/module may import from or sit next to
these, so a scoped run must still confirm zero regression:

**Unit — mechanism registry (must stay green untouched):**
- `tests/unit/tools/test_mechanism_registry.py` — all existing tests (registry shape,
  `depends_on` invariants 1/2, layer invariant 3, state invariant 4, `verified` invariants 5/6,
  `implemented_by` invariant 7, `unaudited_depends_on_edges` invariant 8, system membership
  invariants 9/10, `check_duplicate_keys` invariant 11). None of this ticket's AC touch these
  invariants or their fixtures.
- `tests/unit/tools/test_mechanism_registry_changed_code_check.py` — the changed-code advisory;
  unaffected since this ticket adds no `implemented_by` claim to any existing mechanism.
- `tests/unit/tools/conftest.py`'s autouse `_empty_system_registry_by_default` fixture — must
  continue to apply correctly to every pre-existing fixture in the directory; if new tests are
  added to a *different* test file (recommended — see New Tests Required), this fixture's
  `autouse=True` scope (per-directory conftest) means it will also apply there. Confirm the new
  tests' own fixtures don't unintentionally rely on system-registry behavior this autouse fixture
  suppresses (should be a non-issue: none of the three new schemas touch `systems: []`).

**Integration / doc-parity — architecture.md itself:**
- Any existing test asserting `docs/plans/simulation_semantic_control_plane/architecture.md`'s
  content (none found in this investigation's own search of `tests/` for a reference to that file
  path — confirm this remains true; if a future test does reference it, it must still pass after
  §3's rewrite, and should specifically not assert the literal string "Deliberately undecided" is
  present, since AC requires its removal).
- `tools/validate_frontmatter.py`'s corpus test(s) over `staging_artifacts/**/*.md` (if any exist)
  — this ticket's own two new artifact files must pass frontmatter validation (`artifact_type`,
  `layer`, `tags` all drawn from registered values) the same way every other staging artifact
  does.

**No other domain's tests are affected** — this ticket's own Scope is entirely new files plus one
doc section; nothing under `src/` changes.

## New Tests Required

Per AC, mirroring `tests/unit/tools/test_mechanism_registry.py`'s own "one deliberately-broken
fixture per invariant, plus a real/empty/seed-data pass" structure. Recommended location:
`tests/unit/tools/test_semantic_control_plane_schema.py` (new file — keeps the new subject's tests
separate from `test_mechanism_registry.py`, matching this ticket's own recommendation in
investigation.md to give the new validator its own module rather than extend `registry.py`
directly; if the implementer instead extends `tools/mechanism_registry/registry.py`, the tests
should extend `test_mechanism_registry.py` instead — the two choices should move together).

**Schema 1 — Rule↔Mechanism edges:**
- `test_rule_mechanism_edge_schema_accepts_valid_row` — unit — AC line 1: a well-formed
  `{rule_id, mechanism_id, edge_type, evidence, date}` row (using a real Rule ID and real
  mechanism ID from the live corpus, or a small closed synthetic fixture mirroring
  `test_mechanism_registry.py`'s own closed-fixture pattern) produces `validate() == []`.
- `test_rule_mechanism_edge_schema_accepts_empty_data` — unit — AC line 1's "empty data" case: an
  empty `edges: []` list produces zero errors (never an error just for being empty — mirrors
  `architecture.md` §7's UNKNOWN-permanence discipline: an absent row is not itself invalid).
- `test_validator_rejects_invalid_edge_type` — unit — AC line 2: a deliberately-broken fixture
  with `edge_type` outside `{REALIZES, PARTIALLY_REALIZES, CONSTRAINED_BY}` (e.g. `"FOO"`, or
  accidentally `"PRODUCES_INPUT_FOR"` from schema 2's own vocabulary — a good negative case given
  `architecture.md` §3's table lists all four edge names together) produces a non-empty error list
  naming the offending row.
- `test_validator_rejects_unresolved_rule_id` — unit — AC line 3 (first half): a fixture with a
  `rule_id` that does not resolve against the live `docs/world_rules/**/*.md` heading scan (e.g.
  `"NOPE-99"`) produces a non-empty error list naming the id.
- `test_validator_rejects_unresolved_mechanism_id` — unit — AC line 3 (second half), same
  fixture shape, `mechanism_id: "nonexistent_mechanism"` against the real (or a small closed)
  `registries/mechanisms.yaml`-shaped id set.
- `test_validator_rejects_duplicate_rule_mechanism_edge_type_triple` — unit — AC line 4: two rows
  sharing the identical `(rule_id, mechanism_id, edge_type)` triple produce a non-empty error list;
  a companion case with the same `rule_id`/`mechanism_id` but a *different* `edge_type` must NOT
  error (two distinct, legitimately co-existing relations between the same Rule and mechanism —
  confirm the duplicate check is on the full triple, not a `(rule_id, mechanism_id)` pair alone).

**Schema 2 — Mechanism→Mechanism causal edges:**
- `test_mechanism_causal_edge_schema_has_no_shared_edge_type_field` — unit / architecture guard —
  AC line 5: assert the schema 2 row shape has no `edge_type` key at all (a structural assertion
  on the loader/validator's accepted field set, or a fixture-based check that a row carrying
  `edge_type` is rejected as an unexpected field if the loader is strict, or simply that
  `producer_mechanism_id`/`consumer_mechanism_id`/`evidence`/`date` are the only fields the
  validator inspects) — proves schema 1 and schema 2 were not accidentally merged into one row
  shape, the exact `roadmap.md`-named mistake this ticket must not repeat.
- `test_validator_rejects_unresolved_producer_mechanism_id` — unit — AC line 6 (first half).
- `test_validator_rejects_unresolved_consumer_mechanism_id` — unit — AC line 6 (second half).
- `test_validator_rejects_duplicate_directed_causal_pair` — unit — AC line 7: two rows with the
  identical `(producer_mechanism_id, consumer_mechanism_id)` pair produce a non-empty error list;
  a companion case with the pair reversed (`(B, A)` after `(A, B)` already exists) must NOT error
  — the schema is directed, and `(A, B)` + `(B, A)` are two distinct, individually valid facts
  (unless the self-edge / cycle decision investigation.md flags changes this — see below).
- `test_validator_rejects_self_producing_causal_edge` — unit — resolves investigation.md's open
  question (b): a fixture with `producer_mechanism_id == consumer_mechanism_id` on the same row
  is rejected, per this investigation's recommendation. **If the implementer/planner instead
  decides to allow self-edges, this test must be rewritten as
  `test_validator_accepts_self_producing_causal_edge` asserting zero errors** — either way, the
  decision must be proven by a test, not left implicit; do not skip both variants.
- `test_causal_edge_inverse_is_computed_not_stored` — unit / architecture guard — AC line 8: given
  a schema 2 dataset with only forward `PRODUCES_INPUT_FOR`-shaped rows (e.g. `A -> B`), an
  inverse-lookup function ("what does B consume") returns `[A]` without any row in the underlying
  data file/fixture ever having stored the reverse direction — assert both (1) the correct answer
  is returned, and (2) the storage/fixture itself never contains a `consumer_mechanism_id: A,
  producer_mechanism_id: B`-shaped row (i.e. inspect the fixture/schema, not just the function's
  return value, so a future accidental hand-authored inverse row would be caught).

**Schema 3 — Rule realization classification:**
- `test_rule_classification_schema_holds_one_record_per_rule` — unit — AC line 9: a fixture with
  two distinct `rule_id`s each having exactly one record passes with zero errors; combined with
  the duplicate-rule_id test below, proves both halves of "exactly one record per Rule ID."
- `test_validator_rejects_invalid_classification_value` — unit — AC line 10 (first half): a
  fixture with `classification` outside the 6-value enum (e.g. `"REJECTED"`, or a plausible
  near-miss like `"INERT"` missing the `-OFF` suffix) produces a non-empty error list.
- `test_validator_rejects_duplicate_rule_id_in_classification_registry` — unit — AC line 10
  (second half): two rows sharing the same `rule_id` produce a non-empty error list.
- `test_unknown_classification_is_accepted_and_preserved` — unit — AC line 11, the load-bearing
  negative-space test: a fixture row with `classification: UNKNOWN` produces zero errors from
  `validate()`, AND (if the implementation includes any read/normalize path between file and
  in-memory representation) the loaded value is still literally `"UNKNOWN"`, never silently
  rewritten to `"MISSING"` or dropped. This is the test most likely to catch an accidental "helpful"
  normalization the ticket explicitly forbids.
- `test_no_function_derives_classification_from_edges` — architecture guard — AC line 13: since
  this is a negative claim about the codebase's own shape rather than a runtime input/output
  fact, this cannot be a conventional behavioral assertion. Two complementary approaches, both
  recommended: (1) a static guard scanning the new module(s)' source for any function whose only
  parameters are edge-schema-shaped (schema 1/2 data) and whose return type or body writes a
  classification-shaped value — brittle if written as free-form AST matching, so prefer (2) as the
  primary proof: a **manual code-review checklist item** recorded in the PR/ticket's own
  Implementation Notes confirming no such function was written, backed by (1) only if a cheap,
  low-false-positive static check is feasible (e.g. grep for any function whose name contains both
  "edge" and "classif" as an early warning, reviewed by a human, not auto-failing on a false
  positive). Document in the ticket's own Implementation Notes which approach was used.

**Cross-schema:**
- `test_all_three_schemas_pass_on_real_seed_data` — integration — AC line 14: load the real
  committed `registries/rule_mechanism_edges.yaml` (or chosen path),
  `registries/mechanism_causal_edges.yaml`, and `registries/rule_classifications.yaml` and assert
  the combined validator returns zero errors — the direct analog of
  `test_mechanism_registry.py`'s own `registry_data` real-file fixture tests. If the ticket ships
  with genuinely empty (zero-row) registries rather than illustrative seed rows, this test still
  must exist and pass against the empty files (proving "empty is valid," not just "seed data is
  valid" — AC's own wording lists both).
- `test_architecture_md_no_longer_says_deliberately_undecided` — unit / doc-guard — AC line 15:
  read `docs/plans/simulation_semantic_control_plane/architecture.md` and assert the literal
  string `"Deliberately undecided"` is absent.
- `test_architecture_md_section_3_names_chosen_schema` — unit / doc-guard — AC line 16: assert §3
  of `architecture.md` contains the actual chosen file path(s) (e.g. a substring check for
  `registries/rule_mechanism_edges.yaml` or whatever path was actually chosen), still names all
  three structures as distinct, and still references the validator and §7's UNKNOWN-permanence
  discipline (substring checks for key terms, not full-text equality — full-text equality would be
  too brittle against future prose-only edits within §3).
- `test_architecture_md_only_section_3_changed` — architecture guard — AC line 17: a `git diff`-
  based check (or a stored pre-change hash/line-range comparison) confirming no line outside §3's
  own span changed. This is best proven at Verify time via `git diff docs/plans/.../architecture.md`
  reviewed by hand/CI rather than as a pytest unit test (a pytest test would need the pre-change
  file committed as a fixture to diff against, which is unusual for a doc-only check) — recommend
  this be a Verify-phase manual/CI diff check, not a new pytest test, and note that choice
  explicitly in Implementation Notes so it isn't silently skipped as "should have been a test."

## Scoped Pytest Commands

```
pytest tests/unit/tools/test_mechanism_registry.py tests/unit/tools/test_mechanism_registry_changed_code_check.py tests/unit/tools/test_semantic_control_plane_schema.py -v
```

If the implementer instead extends `registry.py`/`test_mechanism_registry.py` directly rather than
adding a new module (see investigation.md's open module-path question), scope to:

```
pytest tests/unit/tools/test_mechanism_registry.py tests/unit/tools/test_mechanism_registry_changed_code_check.py -v
```

Never `pytest tests/` — scope to `tests/unit/tools/` for this ticket's domain. If a doc-coverage
or frontmatter-validation corpus test exists over `staging_artifacts/`/`tickets/` (commonly under
`tests/unit/tools/` or `tests/tools/`), include it too:

```
pytest tests/unit/tools/ -k "frontmatter or docs_to_update or semantic_control_plane or mechanism_registry" -v
```

## Anti-Drift Test Guards

- **`test_causal_edge_inverse_is_computed_not_stored`** doubles as an anti-drift guard against a
  future edit silently reintroducing a hand-authored inverse row — it inspects the fixture/schema
  itself, not just the function's return value, so a well-intentioned "just add the reverse row
  too, it's clearer" edit would fail this test immediately.
- **`test_mechanism_causal_edge_schema_has_no_shared_edge_type_field`** guards against the exact
  regression `roadmap.md` names as an already-happened mistake in an earlier draft — re-merging
  schema 1 and schema 2 into one row shape. This should fail loudly and immediately if anyone
  later "simplifies" the two schemas into one file.
- **`test_no_function_derives_classification_from_edges`**, even as a manual-review-backed guard
  rather than a hard static check, should be re-run (the checklist re-confirmed) at every future
  ticket that touches schema 1/2/3's own modules — flag this in Implementation Notes so a later
  ticket's own Investigate phase picks it up as a standing constraint, not a one-time check.
- **A regression test asserting `registries/mechanisms.yaml`'s `depends_on` field is byte-identical
  before/after this ticket** (or at minimum, that `registry.py::validate()` and
  `test_mechanism_registry.py`'s full existing suite still pass unmodified) is the direct proof for
  AC's "depends_on is unchanged" line — already covered by the Regression Surface section above,
  but called out again here since it is explicitly named as an anti-drift concern in the ticket's
  own Scope, not just an incidental regression.
- **`test_architecture_md_only_section_3_changed`** is itself the anti-drift guard against scope
  creep into `architecture.md`'s settled §§1/2/4-9 — see New Tests Required for why this is
  recommended as a Verify-phase diff check rather than a pytest test specifically.
