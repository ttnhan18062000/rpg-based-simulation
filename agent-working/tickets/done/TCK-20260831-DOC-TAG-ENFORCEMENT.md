---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260831-DOC-TAG-ENFORCEMENT
phase: done
date: 2026-08-31
tags: [frontmatter, tagging, taxonomy, documentation, schema]
---

# TCK-20260831-DOC-TAG-ENFORCEMENT

## Title
Extend `validate_frontmatter.py`'s hard-allowlist tag/layer enforcement to doc frontmatter

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`tools/validate_frontmatter.py` already enforces two hard allowlists — `layer:` (via
`registries/layer_registry.jsonl`) and `tags:` (via `registries/tag_registry.jsonl`, per
`docs/guidelines/tag_taxonomy.md`) — but only for `ticket` and `artifact` content types, and only
forward-only from `2026-07-04` (gated on the file's `ticket_id` embedding a date
`>= 2026-07-04`). `doc`-type frontmatter (everything under `docs/` outside `docs/archive/`,
`docs/superpowers/`, `docs/specs/`) is explicitly exempted today —
`docs/guidelines/tag_taxonomy.md`'s own "Enforcement" section states: "This taxonomy applies to
`ticket` and `artifact` content types only. `doc`-type frontmatter's `tags` field remains
free-form and unvalidated ... the registry does not apply there either."

Measured impact of that gap this session: `docs/REGISTRY.yaml` (2106 entries) carries 1381
**unique** tag strings across doc frontmatter — 19x the 71-tag registry — because
`_validate_doc()` in `validate_frontmatter.py` never calls `_check_tags()` at all (confirmed by
reading the function directly: `_validate_doc` only enum-checks `status`/`layer`/`authority`/
`audience`, unlike `_validate_ticket`/`_validate_artifact`, which both call `_check_tags(...,
registry)`). Separately, `layer:` enum-checking for docs *is* already wired
(`_validate_doc` does call `_check_enum(..., "layer", LAYER_VALUES)`), but 1709/2106 doc registry
entries (81%) show `layer: <none>` — meaning the check is not being run comprehensively across
the corpus today (no CI workflow invokes `validate_frontmatter.py`; it is only exercised at
ticket-close time via `done_checker_static.py::check_frontmatter_valid`, which is
ticket/artifact-scoped, not doc-scoped).

This ticket scopes (does not yet implement) extending both checks — layer allowlist coverage and
new tag allowlist enforcement — to `doc` content type, analogous to how ticket-side tag
enforcement was rolled out (`TCK-20260704-TAG-TAXONOMY`, `TCK-20260706-TAG-REGISTRY-DATA`,
`TCK-20260706-TAG-REPORT-TOOL`, `TCK-20260720-TAG-CATEGORY-REGISTRY`).

## Scope
- Investigate and decide (at Plan phase, informed by this ticket's Open Questions below) a cutover
  mechanism for doc-frontmatter enforcement, analogous to the ticket-side forward-only date gate
  (`_ticket_id_effective_date()` keyed on `TCK-YYYYMMDD-` in `validate_frontmatter.py`), since docs
  have no ticket-ID-shaped identifier to hang that check on.
- Investigate and decide the retrofit strategy for the existing ~1310 unregistered/1381-total
  distinct doc tags and ~1709 doc entries with missing/empty `layer:` — options include (a)
  forward-only enforcement gated on the chosen cutover signal with legacy docs grandfathered, (b) a
  bulk one-time backfill pass registering existing legitimate doc tags (mirroring
  `TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`'s report-only sweep pattern, extended or reused for docs),
  or (c) another approach — do not assume the answer; the decision belongs to the Plan phase with
  evidence from this ticket's investigation.
- Wire `_validate_doc()` in `tools/validate_frontmatter.py` to call `_check_tags(filepath, fm,
  registry)` for `doc` content type (currently it does not call `_check_tags` at all — this is a
  code gap, not just a coverage gap), once the cutover/retrofit decision above is made.
- Update `docs/guidelines/tag_taxonomy.md`'s "Enforcement" section (which currently states
  doc-type tags are exempt) and `docs/guidelines/frontmatter_schema.md` to reflect the new,
  narrower or newly-enforced scope, consistent with whatever cutover mechanism is chosen.
- Update `docs/parity_ledger/infrastructure.yaml` entry `INFRA-180` ("Frontmatter validator ...
  correctly enforces the doc schema ... applied forward-only from 2026-07-04") to reflect the
  behavior change, per the Authoritative Mechanics Rule's parity-update requirement.
- Add/update tests in `tests/tools/test_validate_frontmatter.py` covering the new doc-tag/doc-layer
  enforcement paths (registered tag passes, unregistered tag hard-rejects, canonical-form
  violations, legacy/grandfathered docs are not newly broken per the chosen retrofit strategy).

## Out of Scope
- Actually performing a bulk backfill/registration of the ~1310 currently-unregistered doc tags
  into `registries/tag_registry.jsonl`, or bulk-assigning `layer:` to the 1709 doc entries missing
  it — that bulk data-repair work (if the Plan phase decides it's needed) is large enough to be its
  own follow-up ticket, not silently absorbed here.
- Wiring `validate_frontmatter.py` (doc-scoped or otherwise) into CI (`.github/workflows/test.yml`)
  as a new blocking gate — confirmed via investigation that no CI workflow currently invokes it at
  all (it only runs at ticket-close time via `done_checker_static.py::check_frontmatter_valid`,
  which is ticket/artifact-scoped). Whether/how to add a CI gate for docs is a separate decision.
- Changing `tools/generate_registry.py`'s existing hard-error-on-missing-frontmatter behavior
  (that tool's own separate contract, already fixed for the 12-file gap in
  `TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER` and left unchanged since).
- Re-deriving or duplicating `tag_registry.py`'s/`layer_registry.py`'s existing canonical-form,
  registry-membership, or synonym-mapping logic — any new doc-side check must call those same
  functions, not reimplement them (mirrors the existing "single source of truth" pattern already
  established for tickets/artifacts).
- Adding a `last_verified`-based or other doc-level opt-in cutover mechanism beyond investigating
  and recommending one — implementation of the chosen mechanism happens at Implement phase.

## Acceptance Criteria
- [x] `plan.md` (Plan phase) documents a decided cutover mechanism for doc-frontmatter enforcement
      (with rationale, given `last_verified` covers only 75/2106 doc entries — confirmed via `grep
      -c "last_verified:" docs/REGISTRY.yaml` — and is therefore not a viable universal signal on
      its own) and a decided retrofit strategy for the existing corpus, before implementation
      begins.
- [x] `_validate_doc()` in `tools/validate_frontmatter.py` calls `_check_tags()` (or an equivalent
      doc-appropriate variant) so that a `doc`-type file with an unregistered, in-scope tag hard-
      rejects (exit 1) under `python3 tools/validate_frontmatter.py <file>`.
- [x] A `doc`-type file that predates/falls outside the chosen cutover signal is not newly rejected
      by the new tag check (grandfathering verified against a real pre-existing doc fixture).
- [x] `docs/guidelines/tag_taxonomy.md`'s "Enforcement" section no longer states doc-type tags are
      unconditionally exempt; it states the actual new scope precisely.
- [x] `docs/parity_ledger/infrastructure.yaml` entry `INFRA-180`'s `status`/`v2_evidence` reflect
      the new doc-enforcement behavior.
- [x] New/updated tests in `tests/tools/test_validate_frontmatter.py` cover: doc with registered
      tag passes, doc with unregistered in-scope tag hard-rejects, doc with non-canonical-form tag
      hard-rejects, doc outside the cutover/grandfathered scope is unaffected.
- [x] Running `python3 tools/validate_frontmatter.py docs/` against the real corpus after the
      change produces a bounded, understood violation count (not a silent mass-failure) — the
      actual count and its composition (by the chosen retrofit strategy) is recorded in this
      ticket's `Test Summary` at close.

## Related Tickets
- TCK-20260704-TAG-TAXONOMY — defined the tag taxonomy and the existing forward-only,
  ticket/artifact-only enforcement this ticket extends.
- TCK-20260706-TAG-REGISTRY-DATA — seeded `registries/tag_registry.jsonl` from the live corpus;
  the same seeding pattern likely applies to any doc-tag backfill decided here.
- TCK-20260706-TAG-REPORT-TOOL — built `tools/tag_report.py`'s corpus-walk/reporting pattern,
  reusable for doc-side reporting if the retrofit strategy needs one.
- TCK-20260720-TAG-CATEGORY-REGISTRY — added the 4-category registry
  (`registries/tag_category_registry.jsonl`) tags must resolve against.
- TCK-20260720-TAG-CORPUS-REPAIR-SWEEP — built a report-only, non-cutoff-gated sweep
  (`tools/tag_corpus_sweep.py`) already covering `stored_artifacts/**` and `tickets/**` (not
  `docs/**`) for unregistered/non-canonical tags; directly relevant prior art for whatever
  doc-side reporting or retrofit sweep this ticket's Plan phase decides on — **not a duplicate**,
  since its own Scope explicitly covers `tickets/done|inprogress|todos` and `stored_artifacts`
  only, not `docs/`.
- TCK-20260718-LAYER-REGISTRY-CONVERSION — converted `LAYER_VALUES` from a hardcoded set to the
  registry-backed `registries/layer_registry.jsonl`; this ticket's layer-side work extends that
  registry's *enforcement coverage* to docs, not its data model.
- TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER — separate, already-closed fix for 12 docs with
  no frontmatter block at all (a `generate_registry.py` hard-error, unrelated tool/contract) — cited
  as related context, not a blocker or duplicate.

## Related Docs
- docs/guidelines/tag_taxonomy.md — "Enforcement" section explicitly scopes current enforcement to
  `ticket`/`artifact` only; must be updated once this ticket's decision is implemented.
- docs/guidelines/frontmatter_schema.md — documents `doc` content type's schema, including `tags:
  no | list of strings | free-form` (must change to reflect enforcement) and the doc-level
  `last_verified` conditional-required field surfaced in this ticket's cutover-mechanism
  investigation.
- docs/guides/ticket_tagging.md — practical walkthrough for the existing ticket-side tagging
  process; a doc-side equivalent guide may be needed depending on the Plan-phase decision.
- docs/guides/ticket_reporting.md — documents `tag_report.py`/`tag_corpus_sweep.py`'s existing
  "Pillar" reporting tools; a doc-corpus sweep, if the retrofit decision needs one, likely belongs
  here too.

## Related Stored Artifacts
None found directly on point. `stored_artifacts/TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER/`
(investigation.md, plan.md, test_plan.md) covers a related but distinct problem (missing
frontmatter blocks entirely, not tag/layer allowlist enforcement) and is useful background reading
for how doc-frontmatter fixes have been staged before, but does not investigate this ticket's
scope.

## Related Code Areas
- tools/validate_frontmatter.py — `_validate_doc()` (does not call `_check_tags`), `_check_tags()`,
  `_ticket_id_effective_date()` (the ticket-side cutover mechanism this ticket needs a doc-side
  analog for), `LAYER_VALUES`/`_layer_values()` import.
- tools/tag_registry.py — `is_tag_registered()`, `canonical_form_violation()`, `load_registry()`
  (the single source of truth any new doc-side check must call, not reimplement).
- tools/layer_registry.py — `layer_values()`, `is_layer_registered()`.
- registries/tag_registry.jsonl, registries/layer_registry.jsonl — the two append-only allowlists.
- docs/REGISTRY.yaml, tools/generate_registry.py — doc corpus index; source of the 1381-unique-tag
  and 1709-missing-layer measurements cited above.
- tools/tag_corpus_sweep.py, tools/tag_report.py — existing report-only sweep/report tooling,
  reusable pattern for any doc-side sweep.
- tests/tools/test_validate_frontmatter.py — existing test suite to extend.
- docs/parity_ledger/infrastructure.yaml — entry `INFRA-180`.

## Assumptions / Open Questions
- **Cutover mechanism (open, for Plan phase):** docs have no `TCK-YYYYMMDD-` id to date-gate on.
  `last_verified` exists on doc frontmatter (required only when `status: authoritative`) but covers
  just 75/2106 entries — not viable as a universal signal without also deciding what happens to the
  other ~2031 docs with no `last_verified`. Candidate mechanisms to evaluate at Plan phase: (a) a
  new doc-level opt-in marker field, (b) a global date cutover (any doc modified/touched on or
  after a chosen date, via git history or a new field), (c) directory/path-scoped rollout (enforce
  only under specific `docs/` subtrees first), (d) something else. This ticket does not decide
  which.
- **Retrofit blast radius (open, for Plan phase):** naive full-corpus enforcement would immediately
  fail ~1310 currently-unregistered tags and ~1709 no-layer docs. Whether the right answer is
  forward-only grandfathering (mirroring the ticket-side precedent exactly), a bulk backfill pass
  first, or a hybrid, is explicitly left to Plan phase with evidence, not assumed here.
- **`layer:` enforcement for docs is code-already-wired but not comprehensively run** — the 1709
  no-`layer` finding does not mean the enum check is broken; it means `validate_frontmatter.py` is
  not currently run across the full `docs/` tree in any automated gate. Whether this ticket's scope
  includes actually running/wiring that check broadly (vs. just the new tag check) should be
  confirmed at Plan phase — current Scope above treats both layer-coverage and tag-enforcement as
  in-scope together, since they share the same cutover/retrofit decision.
- **No CI gate currently invokes `validate_frontmatter.py` at all** (confirmed: no match in
  `.github/workflows/*.yml`); it only runs at ticket-close time, ticket/artifact-scoped. This means
  extending doc enforcement will not break CI on landing, but also won't be enforced automatically
  anywhere until/unless a future ticket wires it in — explicitly deferred, see Out of Scope.
- **`INFRA-180` parity ledger entry currently describes today's (soon-to-be-superseded) scope** —
  flagged in Scope/Acceptance Criteria as something Implement/Finalize must update, per
  `CLAUDE.md`'s Authoritative Mechanics Rule (logic changes require parity ledger updates in the
  same session).
- Layer chosen as `guidelines` (cross-cutting process/convention docs — tagging, patterns,
  taxonomy), matching every directly-related prior-art ticket
  (`TCK-20260704-TAG-TAXONOMY`, `TCK-20260706-TAG-REGISTRY-DATA`, `TCK-20260706-TAG-REPORT-TOOL`,
  `TCK-20260720-TAG-CATEGORY-REGISTRY` all used `layer: guidelines`) — confirmed via
  `python3 tools/layer_registry.py list` that `guidelines` is registered and no better-fitting
  layer exists (this is validation/convention tooling, not a gameplay subsystem or the `testing`
  layer's test-infrastructure focus).

## Implementation Notes

Implemented plan.md's 8 steps in order, in `tools/validate_frontmatter.py`:

- **Step 1** — extracted `_tag_membership_errors(filepath, tags, registry)` from `_check_tags`'s
  existing two-stage canonical-form/registry-membership loop. `_check_tags` now computes its
  `ticket_id`-based scope decision exactly as before, then delegates to
  `_tag_membership_errors`. Signature, docstring, and behavior of `_check_tags` are byte-for-byte
  unchanged (verified: all 7 `TestTagRegistryEnforcement` tests pass unmodified).
- **Step 2** — added `_check_doc_tags(filepath, fm, registry=None)`, a doc-specific function with
  its own scope decision: exempt (`[]`) unless `fm.get("tags_enforced")` is truthy, in which case
  it delegates to the same `_tag_membership_errors`. This is the new, doc-appropriate cutover
  signal decided in plan.md's Decision 2 (`tags_enforced: true`, a per-file opt-in boolean, not a
  date cutoff) — deliberately *not* a call to `_check_tags` itself, since that call is a
  structural no-op for docs (no doc frontmatter carries `ticket_id`).
- **Step 3** — wired `_validate_doc()` to call `errors += _check_doc_tags(filepath, fm, registry)`
  before `return errors`. This is the actual fix for the ticket's named code gap.
- **Step 4** — added `test_invalid_layer_doc_fixture_still_rejected` to `TestDocContentType` in
  `tests/tools/test_validate_frontmatter.py`, pinning the one real pre-existing doc-layer
  violation (`docs/simulation/domains/social_memory_contract.md`, `layer: social`). No production
  code change — the layer enum check already existed and already ran.
- **Step 5** — rewrote `docs/guidelines/tag_taxonomy.md`'s "Enforcement" section's final paragraph
  to state the actual new doc scope (opt-in `tags_enforced: true` marker, not a date cutoff;
  entire existing corpus remains exempt/unvalidated).
- **Step 6** — updated `docs/guidelines/frontmatter_schema.md`'s `doc` schema table: changed the
  `tags` row's description and added a new `tags_enforced` row. Also applied the plan's flagged
  optional/trivial cleanup: added the missing `frontend` value to the `LAYER_VALUES` "Enum
  Reference" list (pre-existing staleness unrelated to this ticket's core scope, already exercised
  by the existing `test_enum_values_layer` test).
- **Step 7** — updated `docs/parity_ledger/infrastructure.yaml` entry `INFRA-180`'s `text` and
  `v2_evidence` fields using `tools/parity_ledger_writer.py::write_entry()` (loaded the existing
  entry via `yaml.safe_load`, amended only `text`/`v2_evidence`, called `write_entry`, which
  validated and upserted by `id` and rebuilt the derived parity index in-process). No raw
  Edit/hand-written YAML rewrite was used, per the ticket's explicit instruction and this repo's
  documented prior corruption incident with that anti-pattern. `git diff --stat` confirms only the
  `INFRA-180` entry's `text`/`v2_evidence` fields changed (10 insertions, 3 deletions) — no other
  entry in the shard was touched, and the shard's entry count (402) is unchanged.
- **Step 8** — ran `python3 tools/validate_frontmatter.py docs/` post-implementation. See Test
  Summary below for the full recorded composition. The tag-side result matched plan.md's
  prediction exactly (0 new tag violations, since no doc anywhere carries `tags_enforced`); the
  raw full-tree run surfaced a larger set of pre-existing, unrelated violations
  (`status`/`original_date`/`frontmatter`/`last_verified`, plus 18 additional pre-existing
  `layer`-missing archive files) than plan.md's narrower `docs/REGISTRY.yaml`-scoped estimate
  anticipated — see `staging_artifacts/TCK-20260831-DOC-TAG-ENFORCEMENT/plan.md`'s new
  "Deviations" section for the full accounting and why this is not a regression caused by this
  ticket's code changes.

Also added the full `TestDocTagEnforcement` class (10 tests) to
`tests/tools/test_validate_frontmatter.py`, per test_plan.md's coverage outline, placed after
`TestTagRegistryEnforcement` and before `TestExitCodeContract`.

No scope guard from plan.md was violated: no tag was registered into
`registries/tag_registry.jsonl`, no doc's frontmatter was edited to add `tags_enforced`, no doc's
`layer:` value was changed, no new `social` layer was registered, `_check_tags`'s external
signature/behavior is unchanged, `tag_registry.py`/`layer_registry.py` internals are unchanged, no
CI workflow was touched, `generate_registry.py`/`tag_corpus_sweep.py`/`tag_report.py` are
unchanged, and `docs/parity_ledger/infrastructure.yaml` was edited only via the sanctioned writer
tool.

## Test Summary

Scoped test run (never full suite), using the venv interpreter
(`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` — bare `python3` lacks
`pydantic`, a known local-sandbox gap unrelated to this ticket):

```
python3 -m pytest tests/tools/test_validate_frontmatter.py -v
  → 93 passed (83 pre-existing + 10 new TestDocTagEnforcement/TestDocContentType tests)

python3 -m pytest tests/tools/test_tag_registry.py tests/tools/test_layer_registry.py \
  tests/tools/test_done_checker_static.py tests/tools/test_tag_report.py \
  tests/tools/test_tag_corpus_sweep.py -v
  → 184 passed, 1 pre-existing unrelated SyntaxWarning (done_checker_static.py escape sequence)

python3 -m pytest tests/tools/test_ticket_field_values.py -v
  → 8 passed
```

Total: **285 passed, 0 failed**, across the full Regression Surface named in test_plan.md plus all
new tests. All 7 `TestTagRegistryEnforcement` tests and `TestEnumAntiDrift::
test_tag_taxonomy_effective_date` pass unmodified, confirming Step 1's refactor is behavior-
preserving for tickets/artifacts.

**Step 8 — real-corpus verification (`python3 tools/validate_frontmatter.py docs/`, run against
the full 851-file raw `docs/` tree):**

```
FAIL: 355 violation(s) in 851 file(s) checked
```

Composition by field (all pre-existing, none newly introduced by this ticket's code changes):

| Field | Count | Cause |
|---|---|---|
| `status` | 161 | Pre-existing — mostly `docs/archive/**` (missing/invalid `status`, e.g. `idea`), plus 4 in `docs/guides/*.md` |
| `original_date` | 150 | Pre-existing — all `docs/archive/**`, the `archive` content-type's own already-existing required field |
| `frontmatter` | 22 | Pre-existing — files with no frontmatter block at all (mostly `docs/brainstorm/codex/**`) |
| `layer` | 19 | 18 pre-existing `docs/archive/legacy_agents_skills_20260722/*/SKILL.md` (missing `layer`, `archive` content type) + 1 known pre-existing doc-layer violation (`docs/simulation/domains/social_memory_contract.md`, `layer: social`) — pinned by `test_invalid_layer_doc_fixture_still_rejected` |
| `last_verified` | 3 | Pre-existing — missing when `status: authoritative` |
| **`tags`** | **0** | **This ticket's own new check — matches plan.md's prediction exactly: zero existing doc carries `tags_enforced`, so zero new tag violations.** |

None of the 355 violations are `tags:`-prefixed (confirmed via `grep "tags:"` against the run's
output — zero matches). This satisfies AC #6 ("bounded, understood violation count, not a silent
mass-failure") — see plan.md's Deviations section for why the total is larger than plan.md's
narrower, `docs/REGISTRY.yaml`-scoped pre-Implement estimate (that estimate only covered the 397
curated `type: doc` registry entries, not the raw 851-file `docs/` tree, which additionally
surfaces `archive`-content-type and missing-frontmatter files the registry excludes/pre-filters).
None of this composition was fixed as part of this ticket, per Decision 3/4 and the Out of Scope
section.

## Files Changed

- `tools/validate_frontmatter.py` — added `_tag_membership_errors`, `_check_doc_tags`; refactored
  `_check_tags` to delegate to `_tag_membership_errors`; wired `_validate_doc` to call
  `_check_doc_tags`.
- `tests/tools/test_validate_frontmatter.py` — added `load_registry` import; added
  `test_invalid_layer_doc_fixture_still_rejected` to `TestDocContentType`; added new
  `TestDocTagEnforcement` class (10 tests).
- `docs/guidelines/tag_taxonomy.md` — rewrote the "Enforcement" section's final paragraph to
  describe the new doc-tag opt-in scope.
- `docs/guidelines/frontmatter_schema.md` — updated the `doc` schema table's `tags` row, added a
  `tags_enforced` row, added `frontend` to the `LAYER_VALUES` Enum Reference list.
- `docs/parity_ledger/infrastructure.yaml` — updated entry `INFRA-180`'s `text`/`v2_evidence`, via
  `tools/parity_ledger_writer.py::write_entry()`.
- `staging_artifacts/TCK-20260831-DOC-TAG-ENFORCEMENT/plan.md` — added a "Deviations" section
  documenting Step 8's actual real-corpus composition versus the plan's narrower pre-Implement
  estimate.
- `tickets/inprogress/TCK-20260831-DOC-TAG-ENFORCEMENT.md` — this file (Status, Acceptance
  Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary).

Note: `staging_artifacts/TCK-20260831-DOC-TAG-ENFORCEMENT/investigation.md` and `test_plan.md`
were already present (written during this ticket's earlier Investigate/Plan phases, before this
Implement pass began) and were not modified during Implement — only `plan.md` was amended, per
the Deviations addition above.

## Completion Summary

Extended `tools/validate_frontmatter.py`'s hard-allowlist tag enforcement to `doc`-type
frontmatter via a new, doc-appropriate opt-in cutover signal (`tags_enforced: true`), avoiding the
investigation-identified failure mode of a naive, permanently-no-op `_check_tags` wire-in (docs
carry no `ticket_id` to date-gate on). The existing 397+-doc corpus is fully grandfathered — zero
existing doc carries the new field, so zero existing doc is newly rejected; no bulk tag
registration or layer correction was performed, per Out of Scope. `docs/guidelines/tag_taxonomy.md`
and `docs/guidelines/frontmatter_schema.md` were updated to document the new scope, and
`docs/parity_ledger/infrastructure.yaml` entry `INFRA-180` was updated via the sanctioned writer
tool. 285 scoped tests pass (0 failures); Step 8's real-corpus run confirms 0 new tag violations
and records the full, understood composition of the 355 pre-existing (unrelated) violations now
visible for the first time.
