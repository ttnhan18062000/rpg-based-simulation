---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW
artifact_type: test_plan
tags: [architecture, schema, registry, combat]
---

# Test Plan — TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW

## Regression Surface

All under `tests/unit/tools/` — **not** `tests/tools/` (confirmed: no `tests/tools/` directory
holds these tests; `tests/unit/tools/` is the real location, verified by direct `find`).

- `tests/unit/tools/test_semantic_control_plane_schema.py` — full file must keep passing,
  **especially**:
  - `test_all_three_schemas_pass_on_real_seed_data` — must still pass with **zero** violations
    after Combat's real rows are added (AC2's "zero manual overrides of a reported violation").
  - `test_rule_id_scanner_finds_known_rule_ids` — unaffected (no `docs/world_rules/` edits); stays
    green as a sanity check that `TERR-01` and at least one `LEARN-` id still resolve.
  - `test_no_function_derives_classification_from_edges` — must keep passing unmodified; this
    ticket adds data (and, per the extend-vs-new-file call in `plan.md`, possibly a new/extended
    generator function), never a function that derives a classification from edge data.
  - `test_documented_cli_invocation_actually_runs` — real subprocess run of
    `tools/semantic_control_plane/registry.py`; must still exit 0 and print `OK` against the
    populated files (now including Combat's 12-ID surface).
  - `test_rule_mechanism_edge_same_pair_different_edge_type_is_not_a_duplicate` /
    `test_validator_rejects_duplicate_rule_mechanism_edge_type_triple` — the exact invariants that
    govern whether the shared-Rule-ID-across-domains case (Assumptions/Open Questions #2) is
    accepted; must stay green and must be exercised for real by the new fixture below, not just by
    the existing `TERR-01`/`regional_sovereignty` fixture.
  - `test_architecture_md_no_longer_says_deliberately_undecided` /
    `test_architecture_md_section_3_names_chosen_schema` — must keep passing; the new §3 addition
    (inherited-entry citation rule, Scope item 4) must not remove or contradict the existing
    "registries/", "validate_all", "§7" citations these tests assert on.
- `tests/unit/tools/test_territory_control_view.py` — full file must keep passing **unmodified in
  its assertions about Territory's own four rows**, whether the implementation extends
  `generate_territory_control_view.py` in place or introduces a new cross-domain generator that
  wraps/reuses it. In particular:
  - `test_real_territory_view_is_up_to_date` — the committed
    `docs/brainstorm/territory_control_management_view.md` must still match a fresh render of
    Territory's own four rows byte-for-byte, even if a new combined-view file/target is added
    alongside it.
  - `test_territory_view_has_no_single_collapsed_percentage_or_badge` — the same discipline must
    carry into the new cross-domain view (see New Tests Required below).
- `tests/unit/tools/test_semantic_control_plane_drift_detector.py` — full file must keep passing.
  Combat's new rows (dated `2026-09-24` or later) must not themselves register as cited-code or
  verdict drift the moment they're written — `tactical_decision`'s `contradicted` verdict predates
  today (2026-09-19), so a row dated today citing it should find zero verdict drift, by
  construction of `check_verdict_drift`'s own review-time-vs-current comparison.
- `tests/unit/tools/test_mechanism_registry.py` — full file must keep passing unmodified. This
  ticket makes zero code changes to `tools/mechanism_registry/` and (per Out of Scope) does not
  touch any mechanism's `state`/`verified.verdict` in `registries/mechanisms.yaml` — only the
  three semantic-control-plane registries and the new/extended view generator change.
- `Makefile` targets: `make semantic-control-plane-drift-check` (AC5, must report clean after the
  new rows — a genuine finding to report if it does not, never silenced) and
  `make territory-control-view` (or its cross-domain successor target, once named in `plan.md`)
  must both still run cleanly.

## New Tests Required

1. **Test name**: `test_rule_mechanism_edge_shared_rule_id_across_domains_is_not_a_duplicate`
   - **Category**: unit (schema/validator)
   - **What it verifies**: two edges sharing one `rule_id` (e.g. a synthetic `PERC-01` row citing
     a Perception-domain mechanism, and a second `PERC-01` row citing `tactical_decision`) both
     validate cleanly — the triple-keyed duplicate check (Assumptions/Open Questions #2) accepted,
     not rejected. This is the one AC2/Assumption-#2 case Territory structurally could not
     exercise (Territory only ever cited one domain's own mechanisms); it must be tested with a
     synthetic fixture even before/alongside the real Combat data lands, since it is a pure schema
     property independent of which domain wrote which row.
   - **Where**: `tests/unit/tools/test_semantic_control_plane_schema.py` (alongside the existing
     `test_rule_mechanism_edge_same_pair_different_edge_type_is_not_a_duplicate`).

2. **Test name**: `test_all_twelve_combat_rule_ids_resolve_against_the_live_corpus`
   - **Category**: unit (regression/corpus guard)
   - **What it verifies**: `scan_rule_ids()` resolves every one of the 12 IDs
     (`CONFLICT-01`, `PERC-01`, `KNOW-01`, `AGENCY-01`, `AGENCY-02`, `AGENCY-04`, `LIFE-01`,
     `LIFE-02`, `BODY-07`, `OWN-02`, `CAP-01`, `ECOL-04`) against the real, live
     `docs/world_rules/` corpus, and that `CONFLICT-02` is NOT in the returned set — a direct,
     permanent regression guard against the exact count/ID-list this investigation re-derived, so
     a future edit to any of the 12 IDs' declaring files (or a Catalog-side rename) is caught
     immediately rather than silently drifting the mapping's own foreign keys.
   - **Where**: `tests/unit/tools/test_semantic_control_plane_schema.py`.

3. **Test name**: `test_combat_rule_mechanism_edges_have_nonempty_evidence_and_date`
   - **Category**: unit (data-quality regression, mirrors the existing TERR-equivalent test)
   - **What it verifies**: every real Combat row written to `rule_mechanism_edges.yaml` has a
     non-empty `evidence` string and a `YYYY-MM-DD` `date` — the same invariant
     `test_real_rule_mechanism_edges_have_nonempty_evidence_and_date` already checks generically
     across all rows, but this ticket's own version should assert the Combat-specific `rule_id`s
     are present at all (i.e. the ticket's core deliverable actually landed), not just that
     whatever rows exist are well-formed.
   - **Where**: `tests/unit/tools/test_semantic_control_plane_schema.py` (extend the existing
     generic test's assertion set, or add a Combat-specific companion — implementer's call).

4. **Test name**: `test_cross_domain_view_renders_both_domains`
   - **Category**: unit (view generator)
   - **What it verifies**: the combined view's output contains all four Territory Rule IDs AND all
     however-many Combat Rule IDs actually receive a disposition (mapped or explicitly-not-mapped)
     in `plan.md`, across the same six `architecture.md` §8 axes — mirrors
     `test_territory_view_renders_all_six_axes` but asserts on both domains in one render.
   - **Where**: a new test file, e.g. `tests/unit/tools/test_cross_domain_management_view.py`, or
     appended to `test_territory_control_view.py` if `plan.md` chooses to extend the existing
     generator in place rather than write a new module (the extend-vs-new-file call is `plan.md`'s
     own, per Assumptions/Open Questions #1 — this test plan does not presume the answer).

5. **Test name**: `test_cross_domain_view_shows_raw_counts_not_bare_percentage`
   - **Category**: architecture guard (anti-drift)
   - **What it verifies**: the combined view's mapped/unmapped and verified/unverified counts are
     present as raw `N/M` figures alongside the classification breakdown (mirrors
     `test_territory_view_shows_mapped_unmapped_counts` and
     `test_territory_view_has_no_single_collapsed_percentage_or_badge`), enforced across **both**
     domains in the combined view, not just Territory's own pre-existing rows — this is AC4's own
     literal requirement and the direct regression guard for the
     `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN` precedent the ticket cites.
   - **Where**: same file as test 4.

6. **Test name**: `test_combat_mixed_realization_is_not_smoothed_into_a_clean_result`
   - **Category**: architecture guard (anti-drift, AC7-specific)
   - **What it verifies**: given the real, re-verified live state (`tactical_decision`
     `contradicted`, `status_effects` `orphan`, `skill_unlocks` `partial`), asserts the combined
     view's Combat rows actually surface at least one non-`SUPPORTED` classification (`PARTIAL`,
     `CONFLICTING`, or `UNKNOWN`) rather than all-`SUPPORTED` — a direct, mechanical check against
     AC7's own "never adjust the classification model to manufacture a cleaner contrast" success
     condition. This test should fail loudly if Combat's real mapping is later edited to look
     artificially clean.
   - **Where**: same file as test 4.

7. **Test name**: `test_architecture_md_section_3_documents_inherited_entry_citation_rule`
   - **Category**: unit (doc-coverage regression, mirrors the existing §3-content tests)
   - **What it verifies**: `architecture.md` §3's text now states that an Inherited/Applied
     Foundational entry is cited under the original Rule ID it derives from (Scope item 4) — direct
     regression guard so this documentation requirement, once satisfied, cannot silently regress.
   - **Where**: `tests/unit/tools/test_semantic_control_plane_schema.py` (alongside
     `test_architecture_md_section_3_names_chosen_schema`).

8. **Test name**: `test_core_rpg_design_direction_section_10_has_no_run_on_paragraph`
   - **Category**: unit (doc-quality regression, Scope item 5)
   - **What it verifies**: a blank line now separates the "...Rule realization axis." pointer
     sentence from `**Status note (2026-09-24).**` in
     `docs/brainstorm/core_rpg_design_direction.md` §10 — e.g. assert the two substrings never
     appear on the same paragraph/line, or assert a `\n\n` separates them. Guards the one small,
     concrete Scope-item-5 fix from silently reverting.
   - **Where**: a small standalone test, or folded into an existing docs-quality test file if one
     already covers `core_rpg_design_direction.md` (none was found in `tests/unit/tools/` during
     this investigation — implementer/test-scoper to confirm the right home, e.g.
     `tests/unit/docs/` if that directory exists, else co-locate with the semantic-control-plane
     schema tests since this ticket is what fixes it).

## Scoped Pytest Commands

```
pytest tests/unit/tools/test_semantic_control_plane_schema.py \
       tests/unit/tools/test_territory_control_view.py \
       tests/unit/tools/test_semantic_control_plane_drift_detector.py \
       -v
```

Plus, once the new cross-domain view test file exists:

```
pytest tests/unit/tools/test_semantic_control_plane_schema.py \
       tests/unit/tools/test_territory_control_view.py \
       tests/unit/tools/test_semantic_control_plane_drift_detector.py \
       tests/unit/tools/test_cross_domain_management_view.py \
       -v
```

Never `pytest tests/` — scope stays to `tests/unit/tools/`'s semantic-control-plane files, per the
project's Testing Rule and the ticket's own Related Code Areas (`tests/unit/tools/`, explicitly
not `tests/tools/`).

## Anti-Drift Test Guards

- **Territory's own four rows must not change.** Any new or extended generator must reproduce
  `docs/brainstorm/territory_control_management_view.md`'s existing content byte-for-byte for
  `TERR-01`/`TERR-02`/`TERR-03`/`TERR-05` — `test_real_territory_view_is_up_to_date` (existing) is
  the direct guard; do not weaken or delete it while adding Combat.
- **No silent `MISSING`-for-`UNKNOWN` coercion.** Any new test asserting on Combat's
  classification rows must distinguish `UNKNOWN` (not yet looked at) from `MISSING` (investigated,
  confirmed absent) per `architecture.md` §7 — a test that treats an absent row and a `MISSING` row
  as equivalent would itself be a drift-enabling defect.
- **No §10/Axis-C vocabulary leaking into the registry-enforced axes.** No new test should assert
  that `status_effects`'s `orphan` state or `skill_unlocks`'s `partial` state implies any specific
  §10 term (`DORMANT`, `OFF`, etc.) — `status_axis_model.md` §2 explicitly marks several of these
  cross-axis pairs as "no defined relationship"; a test asserting an inferred mapping would encode
  a false equivalence this project's own doc already forbids.
- **`tactical_decision`'s verdict must not be silently "fixed" by this ticket.** A new test must
  not assert `tactical_decision`'s `verified.verdict` becomes `observed`; it stays `contradicted`,
  and this ticket's own Out of Scope forbids resolving that finding.
- **The duplicate-triple guard must be exercised with a genuinely cross-domain fixture, not just a
  same-file one.** Test 1 above must use two edges that would plausibly come from two different
  investigation passes (not two rows written in the same PR under the same evidence text) to
  actually prove the schema tolerates the real scenario, not merely a copy-paste duplicate with a
  different `edge_type` (which the existing `test_rule_mechanism_edge_same_pair_different_edge_type_is_not_a_duplicate`
  already covers).
