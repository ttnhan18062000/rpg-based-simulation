---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE
artifact_type: plan
tags: [architecture, schema, registry, world]
---

# Implementation Plan — TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE

## Summary

This plan populates the three M0 semantic-control-plane registries with the first real data
(TERR-01, TERR-02, TERR-03, TERR-05 against `regional_sovereignty`, `betrayal_siege_war`, and
`city`), applies one prose-only note convention to `regional_trauma`, then generates the first
Territory-only management view across `architecture.md` §8's six axes. Edges are written and
validated in isolation before any classification row is written (`rule_classifications.yaml`),
per the ticket's own sequencing hint, to keep the classification a real separate human judgment
rather than a derived roll-up. Every step is additive to data/tests/tooling; zero `src/` changes,
zero `mechanisms.yaml` `state`/`verified.verdict` changes (only one `note` prose edit), and zero
`TERR-04` invention anywhere.

**Decisions this plan makes (resolving every open item from investigation.md and the ticket's own
Assumptions/Open Questions section):**

- **TERR-02 → `regional_sovereignty`, edge_type `PARTIALLY_REALIZES`; Rule classification `PARTIAL`.**
  Applying the ticket's own litmus test: `FactionInfluenceService.process_influence_shift()`
  (`src/world/influence.py:28-30,33-71`) is a real, non-contradictory *narrower slice* of TERR-02's
  causal-basis requirement — it gates conquest/liberation ownership writes behind accumulated
  combat-death evidence, a genuine (if narrow) military-capability proxy — but does not cover
  every case: world-generation-time initial ownership (`src/worldbuilding/compiler.py:415,446`)
  is a bare declarative assignment with **zero** causal basis, the exact shape TERR-02 forbids.
  This is not `CONFLICTING` (no overloaded field/slot forecloses eventually adding a causal check
  to world-gen too — nothing structurally blocks it) and not `SUPPORTED` (a real, confirmed gap
  remains for every region's starting state, not just an edge case). `PARTIAL` is the correct call
  under the ticket's own `CONFLICTING`-vs-`PARTIAL` litmus test, reused here for the adjacent
  `SUPPORTED`-vs-`PARTIAL` distinction the Catalog author's framing raises. Matches the doc's own
  existing `:116-123` verdict, now backed by an exhaustive trace instead of a hedge.
- **TERR-05 → `city`, edge_type `PARTIALLY_REALIZES`; Rule classification `PARTIAL`, not
  `MISSING`.** This plan deliberately departs from a naive "TERR-05 = MISSING" framing: `investigation.md`'s
  own section header states "TERR-05 — has a real partial mechanism, not zero," and directly cites
  `RegionState.places` (`src/core/state.py:295`, confirmed by direct read during this planning
  pass) as live, structural containment data satisfying TERR-05's "a Place may lie inside a
  territory other than its controller" half (`territory-control.md:170`). Only the
  cultural/historical-association-survives-control-change *half* is confirmed `MISSING` (no field
  anywhere on `PlaceState`, `src/core/state.py:344-383` — `prior_kind`/`transformed_tick` at
  `:365-367` is a kind-transformation trail, not a polity-association fact, confirmed by direct
  read). A real edge exists (to `city`), so per the ticket's own AC 1 phrasing ("at least one
  mapping entry, or an explicitly recorded reason for having none"), TERR-05 gets the edge, not a
  classification-only row with no edge — and the aggregate classification is `PARTIAL` (a real,
  non-complete slice), with the confirmed-absent half recorded in the classification's own
  `evidence` field rather than invented as a second edge. This matches TERR-05's own doc verdict
  (`:186-190`, already `PARTIAL`) and the `PARTIAL` litmus test exactly.
- **FAC-010 / `betrayal_siege_war` edge shape: `TERR-01`/`TERR-03` → `betrayal_siege_war`,
  edge_type `CONSTRAINED_BY`** (not `REALIZES`/`PARTIALLY_REALIZES` — this mechanism does not
  implement TERR-01/03's required distinct-relation-type semantics; it is a second, independent
  live code path whose own incomplete transfer behavior further limits how well those semantics
  can ever be read off `RegionState`, which is exactly what `CONSTRAINED_BY` is for), separate rows
  from the existing `regional_sovereignty` edges on the same two Rules.
- **`mechanism_causal_edges.yaml` stays at zero rows.** No real producer→consumer fact among the
  five mapped mechanisms was found. The one candidate relation (`regional_sovereignty` and
  `betrayal_siege_war` independently, inconsistently writing `owner_faction_id`) is a
  conflict/duplication relation, not a producer→consumer one, and does not fit this schema's row
  shape — recorded as evidence text on the `TERR-01`/`TERR-03` `betrayal_siege_war` edges (above)
  and as this plan's own AC 7 schema-friction disposition (Step 2, Step 12), not forced into an
  invented row.
- **Territory view path/generator**: `docs/brainstorm/territory_control_management_view.md`,
  generated by new `tools/semantic_control_plane/generate_territory_control_view.py`, wired via new
  Makefile target `territory-control-view` (Step 8-10), following
  `tools/mechanism_registry/generate_mechanism_system_rollup_view.py`'s exact conventions (banner +
  `--output`/`--check` flags + counts-never-badges), confirmed by direct read of that file
  (`tools/mechanism_registry/generate_mechanism_system_rollup_view.py:1-21,84-96,163-190`).
- **AC 7 schema-friction disposition**: recorded in `investigation.md`'s existing "Risks and Open
  Questions" section (already written), echoed into the ticket body's own `## Implementation Notes`
  section (Step 12) as the closure record done-checker's doc-review will read, and as an inline
  YAML header comment in `registries/mechanism_causal_edges.yaml` (Step 2) so a future mapper who
  does not reread the ticket still sees it. No new ticket filed — this is a genuinely deferred,
  no-schema-change-warranted finding, not a defect needing its own fix ticket.

## Steps

### Step 1 — Populate `rule_mechanism_edges.yaml` with the six real TERR edges

**Files:** `registries/rule_mechanism_edges.yaml`

**Change:** Replace `edges: []` with six rows (`edge_type` values are the M1 mapper's typed
judgment about degree of realization, independent of the Rule-level classification written in
Step 5):

1. `rule_id: TERR-01`, `mechanism_id: regional_sovereignty`, `edge_type: PARTIALLY_REALIZES`.
   Evidence: `RegionState.owner_faction_id` (`src/core/state.py:282`, confirmed by direct read)
   is written by `FactionInfluenceService.process_influence_shift()`
   (`src/world/influence.py:33-71`, confirmed by direct read) as the single slot representing one
   of TERR-01's seven required distinct relation types (de facto control — also read for
   tax/suppression gating at `src/engine/town_resolution.py:65,128-170`), while
   `PlaceState.owner_faction_id`'s own field comment (`src/core/state.py:360`, confirmed by direct
   read, "Sovereignty override; defaults to the parent Region's") names a third concept sharing
   the identical field shape — the same slot cannot represent claim vs. control vs. jurisdiction
   vs. cultural-association simultaneously, per `territory-control.md:27`.
   Date: `2026-09-24`.
2. `rule_id: TERR-01`, `mechanism_id: betrayal_siege_war`, `edge_type: CONSTRAINED_BY`.
   Evidence: siege-driven territory transfer
   (`src/engine/military_conflict.py::MilitaryConflictPhase.execute()`, docstring `:161-165`,
   confirmed by direct read) updates `FactionUpdate.territory_add`/`remove` but **never**
   `RegionState.owner_faction_id`, confirmed independently by `docs/parity_ledger/faction.yaml:227-242`
   (`FAC-010`, `status: verified`, confirmed by direct read) — a second, structurally distinct
   representation of "who controls this region" diverging from `regional_sovereignty`'s own
   `owner_faction_id` on every real siege-driven conquest. Not a restatement of Edge 1's evidence.
   Date: `2026-09-24`.
3. `rule_id: TERR-02`, `mechanism_id: regional_sovereignty`, `edge_type: PARTIALLY_REALIZES`.
   Evidence: see the Summary's TERR-02 decision above — `process_influence_shift()`
   (`src/world/influence.py:28-30,33-71`) gates ownership writes behind accumulated in-region
   combat-death evidence crossing `CONQUEST_THRESHOLD = -50.0`/`LIBERATION_THRESHOLD = 50.0`, a
   real causal-basis proxy per `territory-control.md:100`'s military-capability basis, but two
   caveats stop full realization: (1) world-generation-time initial ownership
   (`src/worldbuilding/compiler.py:415,446`, confirmed by direct read) is a bare declarative
   assignment with zero causal basis; (2) a second live writer,
   `WorldDynamicsSystem.resolve_dynamics()` (`src/engine/world_dynamics.py:23,82-87`, confirmed by
   direct read), re-implements the same check at an inconsistent `±100.0` threshold, not `±50.0`
   — recorded here as evidence, not fixed (Out of Scope).
   Date: `2026-09-24`.
4. `rule_id: TERR-03`, `mechanism_id: regional_sovereignty`, `edge_type: PARTIALLY_REALIZES`.
   Evidence: same overloaded-slot mechanism as Edge 1, applied to TERR-03's own claim-vs-control
   simultaneous-representability requirement (`territory-control.md:130`) — the single
   `owner_faction_id` slot forecloses ever representing a claim that diverges from actual control.
   Date: `2026-09-24`.
5. `rule_id: TERR-03`, `mechanism_id: betrayal_siege_war`, `edge_type: CONSTRAINED_BY`.
   Evidence: same FAC-010 second-desync fact as Edge 2, cited independently for TERR-03's own
   claim-vs-control requirement (distinct citation per Rule, per `architecture.md` §3's typed,
   non-Cartesian edge model — not a copy-paste of Edge 2's row).
   Date: `2026-09-24`.
6. `rule_id: TERR-05`, `mechanism_id: city`, `edge_type: PARTIALLY_REALIZES`.
   Evidence: `RegionState.places` (`src/core/state.py:295`, confirmed by direct read) /
   `PlaceState.region_id` (`src/core/state.py:355-356`, confirmed by direct read) confirm the
   structural containment half of TERR-05's requirement ("a Place may lie inside... a territory
   other than its current controller", `territory-control.md:170`) via the `city` mechanism
   (`RegionState` itself, `registries/mechanisms.yaml:2327-2350`, confirmed by direct read —
   `depends_on: [regional_sovereignty]`, `state: partial`). The cultural/historical-association-
   survives-control-change half has zero implementing field on `PlaceState`
   (`src/core/state.py:344-383`, confirmed by direct read) and is **not** mapped as its own edge —
   recorded as `MISSING` in Step 5's classification evidence instead of an invented edge.
   Date: `2026-09-24`.

**Do NOT touch:** `TERR-04` (never referenced — it is not a real Rule ID, per the ticket's own Out
of Scope and Findings #1). `settlement_capacity_axis` (zero implementing code, confirmed;
no edge). `regional_trauma` (not edge-mapped to any TERR Rule — its only touch in this plan is
Step 4's note-only edit). Any Rule ID outside TERR-01/02/03/05.

**Verify:** `pytest tests/unit/tools/test_semantic_control_plane_schema.py::test_all_three_schemas_pass_on_real_seed_data -v`
(will still fail at this point because `rule_classifications.yaml` is empty and
`validate_rule_classifications()` has no per-rule-required invariant — confirm no *new* violation
is introduced by this step specifically by running
`python3 tools/semantic_control_plane/registry.py` and checking every reported error, if any,
concerns only the still-empty `rule_classifications.yaml`, not this step's own edges).

---

### Step 2 — Populate `mechanism_causal_edges.yaml` with zero rows and record the schema-friction reasoning inline

**Files:** `registries/mechanism_causal_edges.yaml`

**Change:** Leave `edges: []` unchanged (per the ticket's own Scope: "Zero rows is an acceptable
outcome; invented edges are not"). Add one new comment block above the existing header comment
recording, for this ticket specifically: no real producer→consumer fact was found among the five
mapped mechanisms (`regional_sovereignty`, `betrayal_siege_war`, `city`, `regional_trauma`,
`settlement_capacity_axis`) during TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE's investigation;
the one candidate relation considered — `regional_sovereignty` (`FactionInfluenceService`,
`±50.0` thresholds) and `betrayal_siege_war` (`MilitaryConflictPhase`) independently and
inconsistently writing the same durable field (`RegionState.owner_faction_id`) — is a
conflict/duplication relation, not a producer→consumer one, and does not fit this schema's
`producer_mechanism_id`/`consumer_mechanism_id` row shape (per this schema's own header comment,
"NO edge_type field," and its `producer == consumer` self-edge rejection, both confirmed by direct
read of `registries/mechanism_causal_edges.yaml`'s existing header and
`tools/semantic_control_plane/registry.py::validate_mechanism_causal_edges()`). This is recorded
as evidence on the `TERR-01`/`TERR-03` → `betrayal_siege_war` edges in Step 1 instead, and is this
ticket's one AC 7 schema-friction finding, explicitly deferred with the reason above — no schema
revision performed.

**Do NOT touch:** The schema's own field shape (`producer_mechanism_id`/`consumer_mechanism_id`,
no `edge_type`) — this is exactly the "fix the schema" temptation the investigation flagged and
the ticket's Out of Scope forbids acting on here.

**Verify:** `python3 tools/semantic_control_plane/registry.py` reports zero errors attributable to
this file (an empty `edges: []` list trivially satisfies every `validate_mechanism_causal_edges()`
invariant).

---

### Step 3 — Add the AC 8 mechanism state/verdict stability guard test

**Files:** `tests/unit/tools/test_terr_mapping_mechanism_state_stability.py` (new file)

**Change:** New test `test_mechanisms_yaml_state_and_verdict_unchanged_for_terr_mapped_mechanisms`.
Loads the real `registries/mechanisms.yaml` via `MechanismRegistry` (`tools/mechanism_registry/registry.py::MechanismRegistry.get_state()`
and `.get_verification()`, both confirmed to exist by direct read of
`tools/mechanism_registry/registry.py:168-213`) and asserts `state` + `verified.verdict` for the
five mechanisms this ticket touches match the pre-implementation snapshot, confirmed by direct
read of `registries/mechanisms.yaml` during this planning pass:

| mechanism_id | state | verified.verdict | line (as read) |
|---|---|---|---|
| `regional_sovereignty` | `done` | `observed` | `:1971` block |
| `city` | `partial` | `observed` | `:2327` block |
| `regional_trauma` | `done` | `contradicted` | `:1949` block |
| `settlement_capacity_axis` | `gap` | *(no `verified` block at all — `get_verification()` returns `None`)* | `:2428` block |
| `betrayal_siege_war` | `partial` | `contradicted` | `:1804` block |

A new dedicated file, not an addition to `tests/unit/tools/test_mechanism_registry.py`, because
`test_plan.md`'s own Regression Surface requires that file "keep passing unmodified" (zero code
changes to `tools/mechanism_registry/` this ticket makes) — adding a new assertion to it would
blur that guarantee.

**Do NOT touch:** `tests/unit/tools/test_mechanism_registry.py` itself.

**Verify:** Run this new test now (before Step 4's edit) to confirm it passes against the current,
unedited `registries/mechanisms.yaml` — establishes the guard is live before any file it protects
is touched.

---

### Step 4 — Apply the STARVED-convention note edit to `regional_trauma`

**Files:** `registries/mechanisms.yaml`

**Change:** Per `docs/plans/status_axis_model.md` §4 (confirmed by direct read, `:75-99`): "When
`verified.verdict: contradicted` is paired with a runtime `instrument`, the `note` field should
name which of STARVED / REACH-LIMITED / genuinely-broken applies, in prose." `regional_trauma`'s
current note (`registries/mechanisms.yaml`, `regional_trauma` block, confirmed by direct read)
already describes the STARVED shape ("correct, wired code, defeated by real-world data... never
meeting the accumulation precondition") but does not literally name it. Edit the `note` prose only
to explicitly state "This is a STARVED case per `docs/plans/status_axis_model.md` §4: the logic is
correct and would fire under real combat conditions; the Lair region's actual gameplay never
supplies the precondition." **`state: done` and `verified.verdict: contradicted` are not touched
— only the `note:` block's text changes.**

**Do NOT touch:** `state`, `verified.instrument`, `verified.verdict`, `verified.date` on this or
any other mechanism entry. Do not apply this convention to any other mechanism not already flagged
by the ticket's own Scope (only `regional_trauma` is named).

**Verify:** Re-run Step 3's new test — must still pass (identical `state`/`verdict` values). Manual
`git diff registries/mechanisms.yaml` at this point should show exactly one changed region, wholly
inside the `regional_trauma` block's `note: >-` text.

---

### Step 5 — Populate `rule_classifications.yaml` with the four Rule-level verdicts

**Files:** `registries/rule_classifications.yaml`

**Change:** Replace `classifications: []` with four rows — written as a **separate pass**, after
Steps 1-2's edges are already on disk (sequencing hint: `docs/plans/simulation_semantic_control_plane/architecture.md`
§3/§4, confirmed by direct read via `validate_rule_classifications()`'s own docstring in
`tools/semantic_control_plane/registry.py:224-244`, "Deliberately does NOT take
`rule_mechanism_edges.yaml`... as input"):

1. `rule_id: TERR-01`, `classification: CONFLICTING`. Evidence: the shared `owner_faction_id`
   three-concept overload (Step 1 Edge 1's own evidence) plus the independent FAC-010
   `betrayal_siege_war` second-desync (Step 1 Edge 2) — two structurally distinct pieces of
   CONFLICTING evidence, per the ticket's own pre-settled precedent
   (`architecture.md:132`, "`TERR-01` is `CONFLICTING`... even though the mechanisms reading
   `owner_faction_id` are all `state: done`"). Review date: `2026-09-24`.
2. `rule_id: TERR-02`, `classification: PARTIAL`. Evidence: see Summary decision above (real
   causal-basis gating for conquest/liberation; zero causal basis at world-generation time; two
   mutually inconsistent live thresholds). Review date: `2026-09-24`.
3. `rule_id: TERR-03`, `classification: CONFLICTING`. Evidence: same root cause as TERR-01 (Step 1
   Edges 4-5). Review date: `2026-09-24`.
4. `rule_id: TERR-05`, `classification: PARTIAL`. Evidence: see Summary decision above (real
   structural containment via `city`/`RegionState.places`; confirmed-absent
   cultural/historical-association-survives-control-change half on `PlaceState`). Review date:
   `2026-09-24`.

**Do NOT touch:** `TERR-04` (no row — not a real Rule ID). Do not add a second row for any of the
four rule_ids (the validator rejects duplicates). Do not derive these four values mechanically
from Step 1's edge_type column — each `classification` value is written here as its own
independent judgment call, using the edges only as cited evidence, matching the reasoning already
spelled out in this plan's Summary (not re-derived at implementation time).

**Verify:** `pytest tests/unit/tools/test_semantic_control_plane_schema.py::test_all_three_schemas_pass_on_real_seed_data -v`
and `python3 tools/semantic_control_plane/registry.py` — zero errors now that all three files carry
real, mutually-consistent data.

---

### Step 6 — Add cross-schema data-integrity tests for AC 1, AC 2, AC 3

**Files:** `tests/unit/tools/test_semantic_control_plane_schema.py` (extend existing "Cross-schema"
section, confirmed present at `:404-408` by direct read)

**Change:** Add three tests:
- `test_all_four_terr_rules_have_a_classification_record` — loads the real, populated
  `rule_classifications.yaml`; asserts exactly one record each for `TERR-01`, `TERR-02`,
  `TERR-03`, `TERR-05`, and none for `TERR-04`.
- `test_terr04_never_appears_in_populated_registries` — loads the real (populated)
  `rule_mechanism_edges.yaml` and `rule_classifications.yaml` file text; asserts the literal
  string `"TERR-04"` never appears. Directly enforces the ticket's own Out of Scope line.
- `test_real_rule_mechanism_edges_have_nonempty_evidence_and_date` — loads the real, populated
  `rule_mechanism_edges.yaml`; asserts every row's `evidence` is a non-empty string and `date`
  matches `YYYY-MM-DD` (AC 2's "zero uncited edges").

**Do NOT touch:** `test_no_function_derives_classification_from_edges` (`:387-400`) — leave
unmodified; it is the structural guard for AC 3 and must keep passing exactly as written.

**Verify:** `pytest tests/unit/tools/test_semantic_control_plane_schema.py -v` — all three new
tests plus the full existing file green.

---

### Step 7 — Confirm the existing validator/CLI tests pass unmodified against the populated files

**Files:** none changed (verification-only step)

**Change:** No new code. Run the full existing regression surface named in `test_plan.md`:
`test_all_three_schemas_pass_on_real_seed_data`, `test_documented_cli_invocation_actually_runs`
(real subprocess run of `tools/semantic_control_plane/registry.py`, confirmed present at `:411-424`
by direct read), `test_no_function_derives_classification_from_edges`,
`test_rule_id_scanner_finds_known_rule_ids`/`test_rule_id_scanner_excludes_review_exports`
(`:40-61`). AC 4 requires this: "zero manual overrides of a reported violation. If the validator
reports a violation, either the data or the schema changes — never the check." If any violation
appears here, return to Step 1 or Step 5 and fix the data — do not edit `registry.py`'s validation
logic to accommodate it.

**Do NOT touch:** `tools/semantic_control_plane/registry.py`, `tools/semantic_control_plane/rule_catalog.py`
— zero code changes anywhere in this package for this ticket.

**Verify:** `pytest tests/unit/tools/test_semantic_control_plane_schema.py -v` full file green;
`python3 tools/semantic_control_plane/registry.py` exits 0 printing `OK`.

---

### Step 8 — Build the Territory Control management view generator

**Files:** `tools/semantic_control_plane/generate_territory_control_view.py` (new file)

**Change:** New script mirroring `tools/mechanism_registry/generate_mechanism_system_rollup_view.py`'s
own structure exactly (confirmed by direct read of that file, `:1-21` module docstring,
`argparse` block `:163-175`, `--check`/`--output` flags `:167-183`): loads
`registries/rule_mechanism_edges.yaml` + `registries/rule_classifications.yaml` (via
`tools/semantic_control_plane/registry.py`, imported not reimplemented) and
`registries/mechanisms.yaml` (via `MechanismRegistry`, imported not reimplemented). For each of the
four mapped Rules (`TERR-01`, `TERR-02`, `TERR-03`, `TERR-05`), renders a Markdown table row per
`architecture.md` §8's six axes, each independently reported, never averaged (confirmed by direct
read, `architecture.md:204-220`):

- **DESIGN** — from `docs/world_rules/places-culture/territory-control.md`'s own frontmatter
  `status: authoritative` (confirmed by direct read, `:1-7`) and header `**Status.** Batch 11A
  (Places/Settlements/Territory), first draft` (`:19`) — shared value across all four rows, cited
  with file path.
- **REALIZATION** — the exact `classification` value from Step 5's `rule_classifications.yaml`
  row for that `rule_id` (`SUPPORTED`/`PARTIAL`/`CONFLICTING`/`MISSING`/`INERT-OFF`/`UNKNOWN`) —
  never re-derived, read directly.
- **IMPLEMENTATION** — the `implemented_by` list of every mechanism that Rule has a
  `rule_mechanism_edges.yaml` row for (via `MechanismRegistry`), concatenated per Rule.
- **VERIFICATION** — per mapped mechanism, `verified.instrument` (`code_trace` vs.
  `scenario`/`corpus_run`/`census` = runtime), rendered as a count (e.g. "2/2 code_trace, 0/2
  runtime") — reusing the same code_trace-vs-runtime distinction
  `build_system_rollup()`/`generate_mechanism_system_rollup_view.py` already renders for the
  mechanism-wide view (confirmed by direct read, `:130-142`), not reinvented.
- **INTEGRATION** — `UNKNOWN` for all four Rules (Step 2's zero `mechanism_causal_edges.yaml` rows
  means no cross-mechanism causal chain exists among this Rule's mapped mechanisms to report on),
  rendered with the one-line reason "no `mechanism_causal_edges.yaml` row exists among this Rule's
  mapped mechanisms — see the schema-friction note" rather than a bare blank cell.
- **OBSERVED OUTCOME** — `UNKNOWN` for all four Rules, since none of `regional_sovereignty`,
  `betrayal_siege_war`, or `city` carries a runtime `verified.instrument` (all three are
  `code_trace`, confirmed above) — rendered exactly as AC 5's own example text: `"OBSERVED OUTCOME:
  UNKNOWN — no runtime evidence currently exists"`.

Also renders, distinct from the per-Rule axis table (AC 6): a `mapped`/`unmapped` count ("4/4 real
TERR Rules mapped; `TERR-04` excluded — stale citation, not a Domain Rule, see the ticket's
Findings #1"), a `verified`/`unverified` count computed as *rules whose mapped mechanisms include
at least one runtime-instrument verification* vs. not (`0/4` here, since all three mapped
mechanisms are `code_trace`-only), and a classification breakdown (`CONFLICTING: 2, PARTIAL: 2,
SUPPORTED: 0, MISSING: 0, INERT-OFF: 0, UNKNOWN: 0`) — three separate figures, never collapsed into
one number or badge, per AC 6 and `architecture.md` §8's own "never averaged into one score."
Includes the same `"Generated from ... — regenerate with `make territory-control-view`. Do not
hand-edit."` banner convention (confirmed by direct read,
`generate_mechanism_system_rollup_view.py:89-91`) and `--output PATH`/`--check` CLI flags
(confirmed by direct read, `:167-183`).

**Do NOT touch:** `tools/mechanism_registry/generate_mechanism_system_rollup_view.py` itself (read
as a pattern, not modified). Do not collapse the six axes or the counts into one score anywhere in
the render function.

**Verify:** `python3 tools/semantic_control_plane/generate_territory_control_view.py --output /tmp/test_view.md`
runs without error and produces Markdown containing all six axis labels for all four Rules.

---

### Step 9 — Wire the `territory-control-view` Makefile target

**Files:** `Makefile`

**Change:** Add a new target alongside the `mechanism-system-rollup-view`/`mechanism-verification-view`
block (confirmed present at `Makefile:349-365` by direct read):
```
territory-control-view: ## Regenerate docs/brainstorm/territory_control_management_view.md (Territory Rules against architecture.md §8's six axes)
	$(PYTHON3) tools/semantic_control_plane/generate_territory_control_view.py
```

**Do NOT touch:** Any existing target (`mechanism-registry-validate`, `mechanism-system-rollup-view`,
etc.) — add only, never fold this into an existing target, since it renders a structurally
different (per-Rule, six-axis) rollup from a different data source
(`tools/semantic_control_plane/registry.py` + `rule_catalog.py`, not
`tools/mechanism_registry/registry.py`).

**Verify:** `make territory-control-view` runs successfully and writes
`docs/brainstorm/territory_control_management_view.md`.

---

### Step 10 — Generate the real Territory management view file

**Files:** `docs/brainstorm/territory_control_management_view.md` (new, generated file)

**Change:** Run `make territory-control-view` against the real, now-populated registries from
Steps 1 and 5. Commit the generated output as-is — never hand-edited, per the banner's own
convention and every existing generated-view precedent in `docs/brainstorm/`.

**Do NOT touch:** Hand-edit this file after generation for any reason (including cosmetic
formatting) — regenerate via the Makefile target instead if anything needs to change.

**Verify:** File exists, contains all six axis labels for all four TERR Rules, and the
mapped/unmapped + verified/unverified + classification-breakdown counts from Step 8. `make
territory-control-view` followed immediately by `git diff --stat` shows no further changes (the
committed file matches what the generator produces from the final registry state).

---

### Step 11 — Add Territory view rendering tests

**Files:** `tests/unit/tools/test_territory_control_view.py` (new file, mirroring
`tests/unit/tools/test_mechanism_registry_view.py`'s structure, confirmed as the stated precedent
in `test_plan.md`)

**Change:** Add:
- `test_territory_view_renders_all_six_axes` — asserts rendered Markdown contains all six axis
  labels (`DESIGN`, `REALIZATION`, `IMPLEMENTATION`, `VERIFICATION`, `INTEGRATION`, `OBSERVED
  OUTCOME`) at least once per mapped Rule row, and that the `OBSERVED OUTCOME` cell for at least
  one Rule fixture literally contains `UNKNOWN` rather than being blank (positive control — all
  four real rows already exercise this per Step 8's design, so this can assert directly against
  real output rather than a synthetic fixture).
- `test_territory_view_check_flag_detects_staleness` — writes a stale copy to a temp path, runs
  `--check` against it, asserts non-zero exit; mirrors
  `generate_mechanism_registry_html.py --check`'s own tested pattern per `test_plan.md`.
- `test_territory_view_shows_mapped_unmapped_counts` — asserts the rendered view contains an
  explicit `mapped`/`unmapped` count pair and a `verified`/`unverified` count pair, each distinct
  from the classification-breakdown table.
- `test_territory_view_has_no_single_collapsed_percentage_or_badge` — asserts no pattern matching a
  single top-level completion percentage/badge appears outside a per-axis, per-Rule breakdown row.

**Do NOT touch:** `tests/unit/tools/test_mechanism_registry_view.py` itself (read as a structural
model only).

**Verify:** `pytest tests/unit/tools/test_territory_control_view.py -v` — all four tests green.

---

### Step 12 — Record the AC 7 schema-friction disposition and the threshold-mismatch finding in the ticket body

**Files:** `tickets/inprogress/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE.md` (`##
Implementation Notes` section)

**Change:** Fill in `## Implementation Notes` (currently `_To be completed by the implementer._`)
with: (1) the AC 7 schema-friction finding and its disposition — `mechanism_causal_edges.yaml`'s
producer→consumer shape does not fit the "two mechanisms inconsistently write the same field"
relation found during mapping; deferred with reason (Step 2), no schema revision performed, no new
ticket filed since nothing is broken that needs fixing, only a representational gap noted for a
future mapper; (2) the `FactionInfluenceService` (`±50.0`) vs. `WorldDynamicsSystem` (`±100.0`)
dual-threshold inconsistency — recorded as evidence on the TERR-02 edge (Step 1), explicitly not
fixed here (Out of Scope), flagged for whoever next touches `regional_sovereignty`; (3) a one-line
pointer to `investigation.md`'s "Risks and Open Questions" section as the fuller record of both.

**Do NOT touch:** Any other ticket body section beyond `## Implementation Notes` at this point
(`## Test Summary`, `## Files Changed`, `## Completion Summary` are filled at Finalize, not here).

**Verify:** Read back the filled section; confirm both findings are present with an explicit
disposition (resolved-and-how, or deferred-and-why) — done-checker's doc-review reads this
directly, no pytest assertion exists for AC 7.

---

### Step 13 — Full scoped regression run and final AC 8 diff confirmation

**Files:** none changed (verification-only step)

**Change:** Run the combined scoped command from `test_plan.md`:
```
pytest tests/unit/tools/test_semantic_control_plane_schema.py \
       tests/unit/tools/test_mechanism_registry.py \
       tests/unit/tools/test_territory_control_view.py \
       tests/unit/tools/test_terr_mapping_mechanism_state_stability.py \
       -v
```
Then a manual `git diff registries/mechanisms.yaml` — confirm every changed line falls inside the
`regional_trauma` block's `note: >-` text (Step 4) and nowhere else in the file.

**Do NOT touch:** Do not run repo-wide `pytest tests/` — scope stays exactly these four files, per
`test_plan.md`'s own "never a bare `-k` filter... test_scope_coverage_static wants the real file
paths" rule.

**Verify:** All four files green; `git diff registries/mechanisms.yaml` output is empty or
`note:`-block-only.

## Scope Guards

- No domain other than Territory/Control — no edges, classifications, or view rows for any Rule
  family outside `TERR-01`/`TERR-02`/`TERR-03`/`TERR-05`.
- `TERR-04` is never written to `rule_mechanism_edges.yaml`, `rule_classifications.yaml`, or the
  generated view — it is not a real Rule ID (Findings #1); guarded by Step 6's dedicated test.
- No `src/` file is changed anywhere in this plan. The `owner_faction_id` overload, the FAC-010
  desync, and the `±50.0`/`±100.0` threshold mismatch are recorded as evidence (Steps 1, 12), never
  fixed in code.
- **Zero `state`/`verified.verdict` changes** to any mechanism in `registries/mechanisms.yaml` —
  the only permitted edit anywhere in that file is `regional_trauma`'s `note:` prose (Step 4).
  Covers all five now-implicated mechanisms: `regional_sovereignty`, `city`, `regional_trauma`,
  `settlement_capacity_axis`, `betrayal_siege_war`. Guarded by Step 3's dedicated regression test,
  written *before* Step 4's edit and re-run after it.
- No row is added to `mechanism_causal_edges.yaml` — zero real producer→consumer fact was found;
  do not force the `regional_sovereignty`/`betrayal_siege_war` conflict-relation into this schema's
  shape (Step 2).
- No edit to `tools/semantic_control_plane/registry.py`, `tools/semantic_control_plane/rule_catalog.py`,
  or `tools/mechanism_registry/registry.py` — this ticket adds data and one new generator script,
  never modifies existing validation logic. If the validator reports a violation, the data or the
  schema changes — never the check (AC 4).
- No hand-edit of `docs/brainstorm/territory_control_management_view.md` after generation.
- No CI wiring of any kind (Out of Scope).
- Do not edit `docs/world_rules/places-culture/territory-control.md` (frozen Batch 11A doc) — the
  one known stale citation (`TERR-04` at `:30`) is tracked separately
  (`TCK-20260923-TERR01-STALE-JURISDICTION-CITATION`), not touched here.

## Dependency Map

- Step 1 (rule_mechanism_edges) and Step 2 (mechanism_causal_edges) are independent of each other,
  both independent of Step 3 (new stability-guard test) and Step 4 (note edit).
- **Step 5 (rule_classifications) depends on Steps 1 and 2 being on disk first** — the ticket's own
  sequencing hint: classify only after all edges are laid down, as a separate pass, never in the
  same pass as writing edges.
- Step 3 should run once before Step 4 (baseline) and once after (regression check) — Step 4
  depends on Step 3 existing first to be meaningful as a guard, though Step 4 itself is otherwise
  independent of Steps 1/2/5.
- Step 6 (cross-schema tests) depends on Steps 1 and 5 (needs real populated data to assert against).
- Step 7 (existing validator/CLI regression) depends on Steps 1, 2, and 5 all being complete.
- Step 8 (generator script) depends on Steps 1 and 5 (needs real edge + classification data to
  render).
- Step 9 (Makefile target) depends on Step 8.
- Step 10 (generated output file) depends on Steps 8 and 9.
- Step 11 (view tests) depends on Step 8 (and benefits from Step 10 existing, though it can run
  against a `--output`-redirected temp file independently).
- Step 12 (ticket body notes) depends on Steps 1 and 2 (the findings it records are produced
  there) but has no code dependency — can happen any time after.
- Step 13 (final full run) depends on every prior step.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC 1 — all four real TERR Rules mapped or reason recorded; TERR-04 never mapped | Steps 1, 5, 6 | `test_all_four_terr_rules_have_a_classification_record`, `test_terr04_never_appears_in_populated_registries` |
| AC 2 — every edge carries citation + date, zero uncited | Step 1, 6 | `test_real_rule_mechanism_edges_have_nonempty_evidence_and_date` |
| AC 3 — one aggregate verdict per Rule, a visible judgment not a roll-up | Step 5 | `test_no_function_derives_classification_from_edges` (existing, unmodified), `test_all_four_terr_rules_have_a_classification_record` |
| AC 4 — validator passes, zero manual overrides | Steps 1, 2, 5, 7 | `test_all_three_schemas_pass_on_real_seed_data`, `test_documented_cli_invocation_actually_runs` |
| AC 5 — Territory view gives explicit state for all six axes, UNKNOWN legitimate | Step 8, 10, 11 | `test_territory_view_renders_all_six_axes` |
| AC 6 — mapped/unmapped + verified/unverified counts, no collapsed number | Step 8, 10, 11 | `test_territory_view_shows_mapped_unmapped_counts`, `test_territory_view_has_no_single_collapsed_percentage_or_badge` |
| AC 7 — schema friction written down, resolved or deferred with reason | Step 2, 12 | done-checker doc-review (no pytest assertion; see `test_plan.md`'s own AC 7 note) |
| AC 8 — no mechanism state/verdict changes, note-only diff | Step 3, 4, 13 | `test_mechanisms_yaml_state_and_verdict_unchanged_for_terr_mapped_mechanisms`, manual `git diff` check |

## Anti-Drift Notes

- **Do not re-introduce the `RegionalSovereigntyService` binding.** Every `regional_sovereignty`
  edge/evidence in this plan cites `FactionInfluenceService` (`src/world/influence.py`) — never
  `src/world/regional_sovereignty.py::RegionalSovereigntyService`, which has zero real callers.
- **Do not classify Rules (Step 5) in the same implementation pass as writing edges (Steps 1-2).**
  Run and confirm Step 1/2 are on disk and validator-clean before starting Step 5 — this is the
  exact mistake `test_no_function_derives_classification_from_edges` exists to catch, and doing
  both in one sitting without the pause is how it silently happens anyway.
- **Do not force an invented edge for `settlement_capacity_axis`** or a forced cultural/residence
  field on `PlaceState` for TERR-01/TERR-05 — both are confirmed absences (not "unlooked-at"), and
  UNKNOWN/MISSING is the correct, complete answer for each, not a reason to invent data to fill the
  row.
- **The TERR-05 classification decision (`PARTIAL`, not `MISSING`) is the one place this plan
  diverges from a plausible naive reading of the ticket's Assumptions section.** Follow this plan's
  reasoning (Summary, Step 1 Edge 6, Step 5 row 4), not a blind "TERR-05 has no mechanism" default
  — the investigation directly confirmed a real, live, structural mechanism (`city`) for
  TERR-05's containment half.
- **Regional_trauma's Step 4 edit is prose-only.** If implementing this step produces a diff
  touching `state:`, `verified.instrument:`, `verified.verdict:`, or `verified.date:` on any
  mechanism, stop — that is an AC 8 violation, not a permitted side effect of naming STARVED in the
  note.
- **The `±50.0`/`±100.0` threshold mismatch and the FAC-010 desync are real, live, confirmed bugs
  — do not patch either in `src/world/influence.py` or `src/engine/world_dynamics.py` or
  `src/engine/military_conflict.py` while implementing this plan.** They are evidence citations
  only.

## Unresolved Questions

None. Every open item carried by `investigation.md` and the ticket's own Assumptions/Open Questions
section (TERR-02's classification axis, TERR-05's classification and edge-or-no-edge question, the
FAC-010/`betrayal_siege_war` edge shape, the Territory-view generator's structure and location, and
AC 7's schema-friction recording location) has been resolved as a concrete decision above, with the
reasoning that produced it spelled out in the Summary and the relevant Step's Change text.

## Deviations

One implementation-time correction, no change to any decision above:

- **Step 1's own suggested header-comment prose for `registries/rule_mechanism_edges.yaml`** (the
  "Do NOT touch: `TERR-04`..." framing implied by this plan's own language, e.g. "TERR-04 (never
  referenced — it is not a real Rule ID...)") would, if copied verbatim into the file's own header
  comment, spell out the literal string `TERR-04` inside the populated registry file itself. This
  directly conflicts with Step 6's `test_terr04_never_appears_in_populated_registries` (a
  literal-string scan of the whole file, comments included — by design, per AC 1's "TERR-04 is not
  mapped and not invented" enforced as strictly as possible). Caught by running that test against
  the real file during implementation, not predicted here. Fix: the header comment added to
  `rule_mechanism_edges.yaml` in Step 1 describes the stale jurisdiction citation
  (`territory-control.md:30`) and its Inherited-entry-carries-no-local-ID explanation without
  spelling out the specific ID it dangles toward. No change to Step 1's edge rows, Step 5's
  classifications, Step 6's test itself, or any decision in this plan's Summary — purely a wording
  fix to avoid tripping the guard the plan itself specified.
- The Territory-view generator's own rendered mapped/unmapped explanatory prose (Step 8) does
  still name `TERR-04` explicitly ("TERR-04 excluded — stale citation, not a Domain Rule"), exactly
  as this plan's own Step 8 Change text specifies — that is legitimate, human-readable explanation
  in *generated documentation output*, not a write to a *populated registry file*, so it is outside
  Step 6's guard by design; `test_territory_view.py`'s own assertions were written to check for
  "no `TERR-04` table row" rather than "no `TERR-04` substring anywhere" for this reason.
