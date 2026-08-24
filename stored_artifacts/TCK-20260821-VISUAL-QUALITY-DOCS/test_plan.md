---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-QUALITY-DOCS
artifact_type: test_plan
tags: [visualization, simulation-quality, world]
---

# Test Plan — TCK-20260821-VISUAL-QUALITY-DOCS

This is a pure-documentation ticket (Type: chore, no `src/`/`tools/` code changes). There is no
`src/rendering/`-style pytest unit-test surface to add. Everything below is either (a) a
frontmatter/registry static check the new files must pass, or (b) confirming the existing
doc-integrity/regression suite stays green with the new files present — not new behavioral test
coverage, because there is no new behavior.

## Regression Surface

None of the following should change as a result of this ticket — they exist independently of
`docs/visual_quality/` and must simply keep passing with the new files added to the tree.

**Doc integrity (unit-ish, doc-scoped):**
- `tests/docs/test_doc_integrity.py` — full file. Its checks (`test_manifest_file_existence`,
  `test_document_structural_compliance`, `test_terminology_alignment`,
  `test_scoped_reporting_compliance`, `test_recorder_enforcement_logic`,
  `test_release_target_binding`, `test_link_integrity`, the lawbook-precedence tests) operate off
  a fixed manifest of `mandatory_documents` — confirmed by reading `test_link_integrity`
  (`load_manifest()`) — not a directory scan, so the new `docs/visual_quality/*.md` and
  `docs/audits/D26_*.md` files are not implicitly pulled into this suite's scope. Run this suite
  as a general doc-health regression check, not because it is expected to exercise the new files.
- `tests/docs/test_doc_path_existence.py` — `test_doc_path_citations_exist`. Confirmed scoped to
  `SCOPE_DIRS = ("docs/engine", "docs/architecture", "docs/performance")` only — does not scan
  `docs/visual_quality/` or `docs/audits/` at all, so this test cannot regress from this ticket's
  changes either way. Still worth running to confirm the ticket's own edits (if any land inside
  those three directories, which they should not) introduce no new dead citation. Carries a
  `strict=True` xfail for 12 pre-existing dead citations — must still show that exact xfail
  outcome, not a new failure shape.

**Registry / frontmatter tooling (unit, tools-scoped):**
Confirmed present under `tests/tools/` (directory listing, this investigation):
`test_validate_frontmatter.py`, `test_generate_registry.py`, `test_layer_registry.py`,
`test_tag_registry.py`, `test_tag_category_registry.py`, `test_registry_query.py`,
`test_add_frontmatter_live.py`, `test_add_frontmatter_tickets.py`,
`test_add_frontmatter_archive.py`. Run at minimum `test_validate_frontmatter.py` and
`test_generate_registry.py` — these two exercise exactly the tooling this ticket's AC #1 and AC
#4 depend on, and neither should change behavior just because new, correctly-formed docs exist,
but both should be confirmed still green with the new files present in the tree.

**Rendering source regression (unaffected, but the ticket sits on top of it — confirm stays
green so the docs being written describe a still-passing system):**
- `tests/unit/rendering/` (all files: `test_connectivity.py`, `test_density.py`, `test_shape.py`,
  `test_variants.py`, `test_grading.py`, `test_review_pipeline.py`, `test_render_core.py`,
  `test_render_incremental.py`, `test_render_annotated.py`, `test_render_storage_integration.py`,
  `test_render_retention_integration.py`, `test_terrain_color_normalization.py`)
- `tests/architecture/test_rendering_zero_new_dependency_guard.py`
- `tests/tools/test_calibrate_rendering.py`

These three groups should already be green (all 8 prerequisite tickets are DONE) — running them
is a sanity check that nothing else landed on this branch broke the system being documented, not
a test this ticket itself needs to make pass.

## New Tests Required

There is no new pytest test to write for this ticket's own acceptance criteria — all four ACs are
either a manual/scripted static check or a one-time confirmation step, not ongoing regression
coverage:

- **AC #1 (`>=3 files, each passing tools/validate_frontmatter.py`)** — not a pytest test;
  verified by running the validator script directly (see Scoped Commands below). If
  `tests/tools/test_validate_frontmatter.py` or `test_generate_registry.py` already asserts
  frontmatter validity over a directory walk of all of `docs/**` (confirm the exact assertion
  shape at implementation time — this investigation confirmed the files exist but did not read
  their full bodies), the new files will be automatically swept into that existing suite's scope
  with zero new test code required — do not write a bespoke new test for this if such a suite
  already exists; only add one if it genuinely does not.
- **AC #2 (D26 correctly following D20's format, re-confirmed as next-available)** — not a
  pytest test; verified by direct inspection of the new file against
  `docs/audits/D20_simq_integration.md`'s section shape, and by re-running the `docs/audits/D*.md`
  listing immediately before creating the file (per this investigation's own re-verification
  method).
- **AC #3 (registry-allowlisted layer/tags)** — not a pytest test; verified by
  `python3 tools/layer_registry.py list` / `python3 tools/tag_registry.py list` containing
  every layer/tag value used in the new files' frontmatter (already confirmed available in this
  investigation: layer `world`, tags `rendering`/`visualization`/`simulation-quality`/
  `documentation`).
- **AC #4 (`docs/REGISTRY.yaml` regeneration picks up the new docs)** — not a pytest test per se;
  verified by running `make docs-registry` (or `python3 tools/generate_registry.py`) after the
  new files exist and confirming (a) it exits 0 with no new frontmatter-parse errors, and (b) the
  regenerated `docs/REGISTRY.yaml` contains entries for each new path. If a
  `tests/tools/test_generate_registry*.py`-style suite already exists and asserts registry
  freshness generically (`--check` drift mode), that suite provides the regression coverage here
  too — confirm at implementation time before deciding whether a new assertion is needed.

## Scoped Pytest Commands

```
# Doc-integrity and doc-path-existence regression (must both still show their known-good state,
# including test_doc_path_existence.py's pre-existing strict=True xfail):
pytest tests/docs/ -m "not slow and not extra_slow"

# Rendering system this ticket documents — confirm still green underneath the new docs:
pytest tests/unit/rendering/ tests/architecture/test_rendering_zero_new_dependency_guard.py \
       tests/tools/test_calibrate_rendering.py -m "not slow and not extra_slow"

# Frontmatter/registry tooling this ticket's AC #1 and AC #4 depend on:
pytest tests/tools/test_validate_frontmatter.py tests/tools/test_generate_registry.py \
       tests/tools/test_layer_registry.py tests/tools/test_tag_registry.py \
       -m "not slow and not extra_slow"
```

Never `pytest tests/` (repo-wide) per CLAUDE.md's Testing Rule — the above three scoped
invocations cover every regression surface this ticket's changes can plausibly touch.

## Non-Pytest Verification Commands

```
# AC #1 — frontmatter validity of the new files
python3 tools/validate_frontmatter.py docs/visual_quality/scoring_contract.md \
                                       docs/visual_quality/current_state.md \
                                       docs/visual_quality/audit_workflow.md \
                                       docs/audits/D26_<slug>.md

# AC #2 — re-confirm D26 is still the next available number, right before creating the file
ls docs/audits/D*.md | sort -V

# AC #3 — registry membership (informational cross-check; validate_frontmatter.py above is the
# actual gate for layer, and does not gate doc tags per this investigation's finding)
python3 tools/layer_registry.py list
python3 tools/tag_registry.py list

# AC #4 — registry regeneration picks up the new docs
make docs-registry
grep -c "docs/visual_quality/\|docs/audits/D26_" docs/REGISTRY.yaml
```

## Recommendation on `tests/docs/test_doc_path_existence.py` Coverage (ticket's own open item)

The ticket's Out of Scope explicitly leaves "worth deciding, not required." Recommendation: **do
not add `docs/visual_quality/` (or `docs/audits/`) to `SCOPE_DIRS`.** Evidence:
`SCOPE_DIRS = ("docs/engine", "docs/architecture", "docs/performance")` does not include
`docs/simulation_quality/` — the very directory this ticket's new files are modeled on — even
though that directory is older, larger, and has had far more opportunity to accumulate dead path
citations. Adding coverage for the new, smaller `docs/visual_quality/` directory while its own
structural precedent remains uncovered would be an inconsistent, unrequested scope expansion, and
would also risk tripping over this test's pre-existing `strict=True` xfail mechanism (any new
failure there requires either being folded into the xfail count or fixed immediately — an
unnecessary risk for a docs-only ticket). If broader `docs/**` path-existence coverage is wanted,
it should be its own ticket that adds `docs/simulation_quality/` and `docs/visual_quality/`
together, consistently, not a side effect of this one.

## Anti-Drift Test Guards

- **Regenerating `docs/REGISTRY.yaml` must not silently drop or mis-tag any pre-existing entry.**
  After running `make docs-registry`, diff the regenerated file against its prior committed
  version and confirm every changed/added line is attributable to this ticket's new files (and
  the routine timestamp/ordering churn `generate_registry.py` is already known to produce) — not
  an accidental removal of an unrelated entry.
- **`docs/audits/audit_dimensions.md` must show zero diff** unless the planner has made an
  explicit, documented decision to repair it (see investigation.md's Risks section) — an
  unplanned edit to this file is the single most likely accidental scope-creep vector for this
  ticket, since it is directly adjacent to the new D26 file and touching it "just to add one row"
  is an easy, understandable temptation that this investigation explicitly recommends against for
  this ticket's scope.
- **The three `docs/visual_quality/*.md` files must not claim the healthy-band threshold values
  in `config/rendering/grade_thresholds.toml` are calibrated.** A future reviewer (or a doc-drift
  audit) diffing the new current-state doc's prose against `grade_thresholds.toml`'s own
  "Illustrative values only, NOT calibrated" comment and `calibrate_rendering.py`'s own
  `validation_summary` field ("no threshold value in this report is asserted, gated, or final")
  is the guard against this specific, easy-to-introduce inaccuracy — there is no automated test
  for it, so Verify-phase human/agent review of the doc prose itself is the enforcement point.
