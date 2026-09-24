---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260924-M2-MAPPING-DRIFT-DETECTION
phase: open
date: 2026-09-24
tags: [architecture, schema, registry]
---

# TCK-20260924-M2-MAPPING-DRIFT-DETECTION

## Title

M2 — report-only drift detector for the semantic control plane's Rule↔Mechanism mappings

## Status

OPEN

## Tier

standard

## Type

feature

## Priority

P1

## Request Summary

M0 built the three mapping schemas and their validator; M1 put the first real data through them
(`TERR-01/02/03/05`, four classifications, `make territory-control-view`). Both are merged
(`origin/main` squash `741b117de`).

M2 is `roadmap.md`'s next milestone and is now gate-clear: a **report-only detector** that answers
"has the world moved under a mapping entry since a human last reviewed it?" — mirroring
`tools/mechanism_registry/mechanism_registry_changed_code_check.py`'s philosophy (report, never
fail the build; a pure testable core separated from its git wrapper).

`roadmap.md` M2 names three drift classes the detector must catch:

1. an `implemented_by` path cited by a mapped mechanism **changed** since the mapping entry was
   last reviewed;
2. a mapped mechanism or Rule was **renamed, removed, split, or merged**;
3. a mapped mechanism's `verified.verdict` **changed** since the mapping was last reviewed.

## Scope

- A new module under `tools/semantic_control_plane/` implementing the detector, structured the same
  way `mechanism_registry_changed_code_check.py` is: a **pure core** taking already-loaded data and
  returning findings (no git, no subprocess — this is what tests exercise), plus a thin git-backed
  wrapper for real invocation.
- **Drift class 1 — cited code changed since review.** Note the axis difference from the existing
  changed-code check, and do not copy its shape blindly: that tool compares two git *refs*
  (`--base`/`--head`), because its question is "did this diff change cited code." M2's question is
  different — "has cited code changed since **this row's own `date`/`review_date`**," which is a
  per-row date comparison, not a two-ref diff. For each mapped mechanism, resolve its
  `implemented_by` citations (reuse
  `tools.mechanism_registry.registry.parse_implemented_by_entry`, do not re-parse) and compare each
  path's last-commit date against the citing row's recorded date.
- **Drift class 3 — `verified.verdict` moved since review.** Mapping rows currently store
  `evidence` + `date`/`review_date` and **no snapshot of the mechanism's verdict at review time**
  (confirmed: `registries/rule_mechanism_edges.yaml` row shape is
  `rule_id, mechanism_id, edge_type, evidence, date`;
  `registries/rule_classifications.yaml` is `rule_id, classification, evidence, review_date`).
  So the detector must recover the review-time verdict rather than read a stored copy.
  **Recommended: read `registries/mechanisms.yaml` out of git history at the row's review date**
  (`git show` at the last commit on/before that date) and compare `verified.verdict` to today's.
  This needs no schema change and stores nothing derivable — the same "don't store what traversal
  can compute" discipline M0's causal-edge schema already followed for its inverse view. The
  alternative (add a `reviewed_mechanism_verdict` field to every edge row) duplicates state that
  will itself go stale and spends M2 on a schema migration; take it only if the git-history read
  proves unworkable, and say so explicitly in `investigation.md` if you do.
- **Drift class 2 — rename/removal/split/merge.** Scope this against what M0's validator already
  covers, rather than rebuilding it: `validate_rule_mechanism_edges()` already **rejects** an
  unresolved `rule_id` or `mechanism_id` (`tools/semantic_control_plane/registry.py:138-143`), so a
  plain rename or removal is already a hard validator failure today, not silent drift. M2's real
  contribution here is the residue the validator cannot see — a mechanism that was **split or
  merged** while keeping a resolvable ID (the mapping still validates, but no longer describes the
  same thing). Reuse `docs/plans/mechanism_identity_and_change_taxonomy.md`'s own change taxonomy
  for what counts as a split/merge rather than inventing a second vocabulary.
- **A real `make` target** — `make semantic-control-plane-drift-check` (or a name consistent with
  the existing `mechanism-registry-changed-code-check` / `territory-control-view` targets). Per
  `roadmap.md`: the target must exist and be runnable now. CI wiring is explicitly *not* required
  at this milestone (Territory alone is a handful of entries; CI makes sense once M4 adds volume).
- **Proof it fires on a deliberately-stale fixture**, per invariant — the same broken-fixture
  discipline M0's validator already met and `TCK-20260920-MECHANISM-REGISTRY-CI-WIRING` established
  for this corpus. A test that only proves "clean today" is not sufficient; each of the three drift
  classes needs a fixture that makes the detector report it.
- Tests under `tests/tools/` (note: no `tests/tools/test_*semantic*` file exists yet — this ticket
  creates the first one).
- Status words in all output must come from `docs/plans/status_axis_model.md`'s vocabulary — do not
  mint new ones.

## Out of Scope

- **CI wiring / any blocking gate.** Report-only, exit 0 regardless of findings, same as every
  other detector in this corpus. Do not add a ratchet.
- **Any new mapping entries.** M2 checks M1's data; it does not extend it. No Combat rows (that is
  M4), no new Territory rows.
- **Fixing any drift the detector finds.** If it reports a real finding on M1's live mapping,
  record it in the ticket and file a follow-up — do not silently re-review the row to make the
  report clean. (`roadmap.md`'s M2 exit criterion expects "clean today"; if it is *not* clean, that
  is a real finding and correct information to report, not an obstacle.)
- **`registries/mechanisms.yaml` content changes**, including `tactical_decision`'s `contradicted`
  verdict — named in `roadmap.md` M4 as live state to re-check there, not here.
- **The ±50 / ±100 regional-sovereignty threshold contradiction**
  (`TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT`, awaiting a user balance decision).
  M2 must not "resolve" it by editing `TERR-02`'s classification. If that ticket lands first,
  `TERR-02`'s row changes under M2 — which is exactly the drift M2 is built to report, and is a
  legitimate live test of it, not a conflict.
- M3 finding ingestion and M4's second slice / cross-domain view.

## Acceptance Criteria

- [ ] A detector module exists under `tools/semantic_control_plane/` with a pure, git-free core
      function and a separate git-backed wrapper, mirroring
      `mechanism_registry_changed_code_check.py`'s three-entry-point separation.
- [ ] All three `roadmap.md` M2 drift classes are implemented, or any one consciously descoped with
      a written reason in `investigation.md` and a note in this ticket (class 2's overlap with the
      existing validator is the expected candidate).
- [ ] A `make` target runs it and is documented in the Makefile's own help text.
- [ ] Running it against M1's live Territory mapping produces a report. If the report is not
      clean, every finding is recorded in this ticket's Completion Summary with a disposition
      (real drift → follow-up ticket filed; false positive → detector fixed).
- [ ] For **each** drift class implemented, a test proves the detector reports a deliberately-stale
      fixture, not just that it passes on clean data.
- [ ] Report-only: exits 0 with findings present. A test asserts this.
- [ ] `python3 tools/semantic_control_plane/registry.py` still validates clean (M2 must not alter
      the committed mapping files).
- [ ] Every status word in the output resolves to `docs/plans/status_axis_model.md`.
- [ ] `docs/plans/simulation_semantic_control_plane/roadmap.md`'s M2 section and the epic's
      milestone-disposition table are updated to reflect the shipped state.

## Related Tickets

- `TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC` — parent epic (this is its M2 row).
- `TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION` — DONE. Built the three schemas + validator this
  detector reads.
- `TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE` — DONE. The live data M2 checks drift against.
- `TCK-20260923-STATUS-VOCABULARY-RECONCILIATION` — DONE. Governs M2's output vocabulary.
- `TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION` — the prior-art detector whose
  structure M2 mirrors (and whose *ref-diff* axis M2 deliberately differs from).
- `TCK-20260920-MECHANISM-REGISTRY-CI-WIRING` — source of the prove-it-fails-on-broken-input
  discipline.
- `TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT` — parked on a user balance decision;
  may move `TERR-02`'s row. Out of scope here, see Out of Scope.

## Related Docs

- `docs/plans/simulation_semantic_control_plane/roadmap.md` — M2 goal/deliverables/exit criteria
  (authoritative for this ticket).
- `docs/plans/simulation_semantic_control_plane/rollout_plan.md` — Stage C.
- `docs/plans/simulation_semantic_control_plane/architecture.md` §3 (schemas), §7 (`UNKNOWN` is
  permanent), §8 (six axes).
- `docs/plans/status_axis_model.md` — status vocabulary.
- `docs/plans/mechanism_identity_and_change_taxonomy.md` — split/merge definitions for class 2.

## Related Stored Artifacts

- `stored_artifacts/TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION/`
- `stored_artifacts/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE/`

## Related Code Areas

- `tools/semantic_control_plane/registry.py` — the three validators; class 2's existing coverage.
- `tools/semantic_control_plane/rule_catalog.py` — `scan_rule_ids()`, live Rule-ID resolution.
- `tools/semantic_control_plane/generate_territory_control_view.py` — existing reader of the same
  data; reuse its loading helpers rather than adding a fourth loader.
- `tools/mechanism_registry/mechanism_registry_changed_code_check.py` — structural prior art.
- `tools/mechanism_registry/registry.py` — `parse_implemented_by_entry`, `MechanismRegistry`.
- `registries/{rule_mechanism_edges,rule_classifications,mechanism_causal_edges,mechanisms}.yaml`
- `Makefile` (~line 361 `territory-control-view`, ~382 `mechanism-registry-changed-code-check`).
- `tests/tools/` — new test module.

## Assumptions / Open Questions

- **Assumed:** a per-row date comparison is the right drift axis, not a two-ref diff. Stated
  explicitly because copying the existing tool's `--base`/`--head` shape would silently answer a
  different question.
- **Assumed:** the review-time verdict is recoverable from git history, so no schema change is
  needed. Verify this early in Implement — `registries/mechanisms.yaml` must have a commit on or
  before each row's review date. If it does not, raise it before adding a field.
- **Open (implementer's call, record it):** does drift class 2 justify its own code at all, given
  the validator already hard-fails rename/removal? Scope says the split/merge residue is the real
  gap; if investigation finds no mechanical signal for split/merge, descope class 2 with a written
  reason rather than shipping a check that cannot fire.
- **Open (not blocking):** whether a row's `date` should be interpreted as a calendar date only
  (no time component — both files store `"2026-09-24"`). Pick the conservative reading (a same-day
  code change counts as "changed since review") and state it in a test.

## Implementation Notes

_(implementer fills)_

## Test Summary

_(implementer fills)_

## Files Changed

_(implementer fills)_

## Completion Summary

_(implementer fills)_
