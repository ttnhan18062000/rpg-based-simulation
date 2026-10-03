---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE
artifact_type: test_plan
tags: [architecture, schema, registry, world]
---

# Test Plan — TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE

## Regression Surface

- `tests/unit/tools/test_semantic_control_plane_schema.py` — full file must keep passing,
  **especially**:
  - `test_all_three_schemas_pass_on_real_seed_data` (`:406-408`) — currently passes on empty
    `edges: []`/`classifications: []`. After this ticket populates real rows, it must still pass
    with **zero** violations (AC 4's "zero manual overrides of a reported violation" — if this
    test fails, the data or the schema changes, never the test).
  - `test_documented_cli_invocation_actually_runs` (`:411-424`) — real subprocess run of
    `tools/semantic_control_plane/registry.py`; must still exit 0 and print `OK` against the
    populated files.
  - `test_no_function_derives_classification_from_edges` (`:387-400`) — must keep passing
    unmodified; this ticket adds data, not code, to `tools/semantic_control_plane/`, so no new
    function name should ever trip this guard.
  - `test_rule_id_scanner_finds_known_rule_ids` / `test_rule_id_scanner_excludes_review_exports`
    (`:40-61`) — unaffected by this ticket (no `docs/world_rules/` edits), must stay green as a
    sanity check that the scan still resolves `TERR-01`/`TERR-02`/`TERR-03`/`TERR-05`.
- `tests/unit/tools/test_mechanism_registry.py` — full file must keep passing unmodified. This
  ticket makes **zero** code changes to `tools/mechanism_registry/`; per AC 8, `registries/
  mechanisms.yaml` itself must show only `verified.note` prose diffs (if any), never a `state` or
  `verified.verdict` change, so every state/verdict-shaped assertion in this file
  (`test_validator_accepts_every_valid_state`, `test_real_registry_passes_validation`, etc.)
  should be unaffected by this ticket's own diff.
- `tests/unit/tools/test_mechanism_registry_changed_code_check.py` — unaffected (no `src/` code
  changes in this ticket); confirm still green as a sanity check, since the changed-code advisory
  is run at Finalize regardless.
- `Makefile` targets touched by this ticket (`mechanism-registry-validate`,
  `mechanism-system-rollup-view` as the structural precedent) — no existing target is modified,
  only a new one (`territory-control-view`) added; confirm `make mechanism-registry-validate`
  still passes against the unmodified `registries/mechanisms.yaml`.

## New Tests Required

Per AC, one test group per criterion (grouped where one test naturally covers more than one AC):

1. **AC 1 — all four real TERR Rules mapped or explicitly reasoned absent; TERR-04 never invented.**
   - `test_all_four_terr_rules_have_a_classification_record` — asserts
     `rule_classifications.yaml`'s real (non-empty, post-population) data has exactly one record
     each for `TERR-01`, `TERR-02`, `TERR-03`, `TERR-05`, and **no** record for `TERR-04`.
     Category: unit/data-integrity. Lives in `tests/unit/tools/test_semantic_control_plane_schema.py`
     (extends the existing file rather than a new one, matching its own "Cross-schema" section
     shape).
   - `test_terr04_never_appears_in_populated_registries` — greps the real
     `rule_mechanism_edges.yaml`/`rule_classifications.yaml` content for the literal string
     `"TERR-04"` and asserts zero matches. Category: unit/architecture guard (anti-drift, directly
     enforces the ticket's own Out of Scope line). Same file.

2. **AC 2 — every edge carries a real citation and a date; zero uncited edges.**
   - `test_real_rule_mechanism_edges_have_nonempty_evidence_and_date` — loads the real (populated)
     `rule_mechanism_edges.yaml`, asserts every row's `evidence` is a non-empty string and `date`
     matches `YYYY-MM-DD`. Category: unit/data-integrity. Same file, alongside
     `test_all_three_schemas_pass_on_real_seed_data`.

3. **AC 3 — one aggregate verdict per Rule, each a visible judgment, not a roll-up.**
   - Already covered by the existing, unmodified `test_no_function_derives_classification_from_edges`
     (structural guard) plus `test_all_four_terr_rules_have_a_classification_record` above
     (one-record-per-Rule). No new test needed beyond confirming both stay green against real data
     — `validate_rule_classifications()`'s own duplicate-`rule_id` rejection (already tested against
     synthetic fixtures) is the enforcement; a fresh test against the real populated file is not
     required since the validator itself is the enforcement point (`test_all_three_schemas_pass_
     on_real_seed_data` already exercises it against real data).

4. **AC 4 — validator passes with zero manual overrides.**
   - Already covered: `test_all_three_schemas_pass_on_real_seed_data` and
     `test_documented_cli_invocation_actually_runs`, both pre-existing, both must pass unmodified
     against the newly-populated files. No new test — this AC is enforced by keeping two existing
     tests green, not by adding a third.

5. **AC 5 — Territory view renders an explicit state for every one of the six axes, `UNKNOWN`
   included.**
   - `test_territory_view_renders_all_six_axes` — new file
     `tests/unit/tools/test_territory_control_view.py`, mirroring
     `tests/unit/tools/test_mechanism_registry_view.py`'s own structure. Asserts the rendered
     Markdown contains all six axis labels (`DESIGN`, `REALIZATION`, `IMPLEMENTATION`,
     `VERIFICATION`, `INTEGRATION`, `OBSERVED OUTCOME`) at least once per mapped Rule row, and that
     none is silently omitted when its value is `UNKNOWN` (positive control: force a Rule fixture
     with no runtime evidence and assert the rendered `OBSERVED OUTCOME` cell literally contains
     `UNKNOWN`, not a blank cell). Category: unit (generated-view rendering).
   - `test_territory_view_check_flag_detects_staleness` — mirrors
     `generate_mechanism_registry_html.py --check`'s own tested pattern: write a stale copy, run
     `--check`, assert non-zero exit. Category: unit.

6. **AC 6 — mapped/unmapped + verified/unverified counts alongside classification breakdown; no
   single collapsed number.**
   - `test_territory_view_shows_mapped_unmapped_counts` — asserts the rendered view contains an
     explicit `mapped`/`unmapped` count pair (e.g. "4/4 TERR Rules mapped") and a
     `verified`/`unverified` count pair, distinct from any classification breakdown table, per the
     `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN` lesson this AC cites directly.
     Category: unit. Same new file.
   - `test_territory_view_has_no_single_collapsed_percentage_or_badge` — an anti-drift structural
     guard: asserts the rendered output contains no pattern matching a single top-level completion
     percentage/badge (e.g. no bare `XX% complete` outside a per-axis, per-Rule breakdown row) —
     mirrors `mechanism_system_rollup_view.md`'s own "never a single summary status" discipline.
     Category: architecture guard. Same new file.

7. **AC 7 — schema friction points written down, resolved or explicitly deferred with a reason.**
   - Not independently testable as a pytest assertion (this is a documentation/process AC). The
     `investigation.md`'s own "Risks and Open Questions" section already records the one soft
     friction point found (the `mechanism_causal_edges.yaml` producer/consumer shape not fitting a
     "two mechanisms inconsistently write the same field" relation) with an explicit deferral
     reason. No new test — verified by done-checker's doc-review, not pytest.

8. **AC 8 — no mechanism `state`/`verified.verdict` changes; diff shows only `verified.note` prose
   edits, if any.**
   - `test_mechanisms_yaml_state_and_verdict_unchanged_for_terr_mapped_mechanisms` — new test in
     `tests/unit/tools/test_mechanism_registry.py` (or a small dedicated
     `tests/unit/tools/test_terr_mapping_mechanism_state_stability.py` if the implementer prefers
     not to touch the existing file's own scope): captures `state` and `verified.verdict` for
     `regional_sovereignty`, `city`, `regional_trauma`, `settlement_capacity_axis`,
     `betrayal_siege_war` from a **known-good snapshot taken before this ticket's own
     implementation** (the values already confirmed in this investigation:
     `regional_sovereignty`=`done`/`observed`, `city`=`partial`/`observed`,
     `regional_trauma`=`done`/`contradicted`, `settlement_capacity_axis`=`gap`/no-verdict,
     `betrayal_siege_war`=`partial`/`contradicted`), and asserts the real, current
     `registries/mechanisms.yaml` still reports the identical five values after implementation.
     Category: unit/regression guard, directly enforces AC 8. This is the single most important
     new test in this ticket — AC 8 is a hard invariant the ticket's own Out of Scope also states
     ("Changing any mechanism's `state` or `verified.verdict`... is a finding to report, not an
     edit to make here").
   - `test_mechanisms_yaml_diff_is_note_only_or_empty` (optional, stronger form): a `git diff
     registries/mechanisms.yaml` scoped check (via `subprocess`, mirroring
     `test_documented_cli_invocation_actually_runs`'s own subprocess pattern) run at Verify/CI time
     — every changed line, if any, must fall within a `note: >-` block. This is closer to an
     integration/CI-shaped check than a hermetic unit test; recommend the implementer decide
     whether to write it as a pytest test (requires a git-aware fixture) or leave it as a manual
     `git diff` check documented in the ticket's own Test Summary, given the existing repo pattern
     favors hermetic unit tests over git-diff-dependent ones in `tests/unit/`.

## Scoped Pytest Commands

```
pytest tests/unit/tools/test_semantic_control_plane_schema.py -v
pytest tests/unit/tools/test_mechanism_registry.py -v
pytest tests/unit/tools/test_territory_control_view.py -v   # new file this ticket adds
```

Combined single scoped run for Verify:

```
pytest tests/unit/tools/test_semantic_control_plane_schema.py \
       tests/unit/tools/test_mechanism_registry.py \
       tests/unit/tools/test_territory_control_view.py \
       -v
```

Never `pytest tests/` (repo-wide) and never a bare `-k` filter that could silently skip one of the
three files above — the bare test-directory form matches the "no cherry-picked files" lesson from
`feedback_hand_orchestration_gate_patterns` (test_scope_coverage_static wants the real file paths
or directory, not an ad-hoc subset).

## Anti-Drift Test Guards

- `test_terr04_never_appears_in_populated_registries` (above) — directly guards against the most
  likely scope-creep failure mode for this ticket: "fixing" the TERR-04 stale citation by quietly
  admitting a `TERR-04` row somewhere in the new data, which the ticket's own Out of Scope
  forbids.
- `test_mechanisms_yaml_state_and_verdict_unchanged_for_terr_mapped_mechanisms` (above) — guards
  against the second most likely scope-creep failure mode: "fixing" `regional_trauma`'s
  `contradicted` verdict, `city`'s `partial` state, or similar, while mapping them, which AC 8 and
  the ticket's Out of Scope both explicitly forbid.
- `test_no_function_derives_classification_from_edges` (existing, unmodified) — guards against the
  classification silently becoming a mechanical roll-up of the edge list, the exact failure the
  ticket's own Implementation Notes sequencing hint warns about.
- `test_territory_view_has_no_single_collapsed_percentage_or_badge` (above) — guards against the
  view quietly regressing into the single-score-badge shape `architecture.md` §8 and
  `mechanism_tier_model_initiative.md` §5 both explicitly forbid.
- A manual (non-pytest) check worth running before Verify: `git diff registries/mechanisms.yaml`
  by hand, confirming every changed line is inside a `note:` block — cheap, fast, and catches an
  accidental state/verdict edit even before the dedicated unit test above would.
