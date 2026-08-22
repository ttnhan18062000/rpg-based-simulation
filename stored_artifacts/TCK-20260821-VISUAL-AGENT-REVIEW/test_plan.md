---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-AGENT-REVIEW
artifact_type: test_plan
tags: [visualization, simulation-quality, determinism, world]
---

# Test Plan — TCK-20260821-VISUAL-AGENT-REVIEW

## Regression Surface

Existing tests that must keep passing, unmodified — this ticket adds new modules under
`src/rendering/` and possibly a new `.claude/agents/*.md` file; it must not touch any shipped
sibling's behavior.

**Unit — `src/rendering/` siblings (must not regress):**
- `tests/unit/rendering/test_render_core.py` (golden-hash, PNG validity, no-mutation)
- `tests/unit/rendering/test_terrain_color_normalization.py`
- `tests/unit/rendering/test_render_incremental.py`
- `tests/unit/rendering/test_render_storage_integration.py`
- `tests/unit/rendering/test_render_retention_integration.py`
- `tests/unit/rendering/test_connectivity.py`
- `tests/unit/rendering/test_density.py`
- `tests/unit/rendering/test_shape.py`
- `tests/unit/rendering/test_variants.py`
- `tests/unit/rendering/test_grading.py`

**Architecture:**
- `tests/architecture/test_rendering_zero_new_dependency_guard.py` — must continue to pass against
  every new file this ticket adds under `src/rendering/` (directory-scoped AST walk, no changes
  needed to the guard itself, but new code must stay stdlib-only to keep it green).

**Integration/regression — determinism law this ticket extends:**
- `tests/docs/test_doc_integrity.py` — will re-check `docs/engine/contracts/
  regression_and_verification.md` and `docs/parity_ledger/infrastructure.yaml` frontmatter/schema
  once this ticket edits them; must stay passing.

**Certification (indirect — not expected to be touched, listed to confirm no accidental
coupling):**
- `tests/certification/test_world_compile_determinism.py` — covers a different determinism
  surface (world-compile output), included here only to confirm this ticket's own golden-hash test
  (below) is a distinct, new test, not a duplicate of this one.

## New Tests Required

Per acceptance criteria, mapped one-to-one:

1. **`test_tier0_tier1_pipeline_writes_digest_without_writing_annotated_png_when_not_escalated`**
   — Category: unit (architecture-guard-shaped). Verifies AC #1's testable half: given a
   non-anomalous fixture `AuthoritativeState` (all hard rules pass, grade above the D/F cutoff),
   running the Tier 0→Tier 1 entry point (a) returns a `Tier1Digest` with `escalate=False` and
   `annotated_render_path=None`, and (b) creates **no file** under the annotated-render output
   directory — assert via `os.listdir`/`Path.glob` on the temp output dir, not just on the return
   value, so a bug that computes `escalate=False` but still calls the annotated renderer as a
   side effect is caught. Location: `tests/unit/rendering/test_review_pipeline.py` (or the actual
   module name the plan picks).

2. **`test_tier0_tier1_pipeline_writes_annotated_png_with_gridlines_when_escalated`** — Category:
   unit. Verifies AC #2's render-existence half: given a fixture state engineered to fail the
   `fully_connected` hard rule (e.g. two disconnected walkable regions) or to land grade D/F,
   running the pipeline (a) returns `escalate=True` and a non-`None` `annotated_render_path`, (b)
   a real PNG file exists at that path, and (c) the PNG is distinguishable from a plain render of
   the same state (cheapest real check: annotated output dimensions include the gridline/label
   margin — mirror `render_annotated.py`'s `margin = 20` — or a pixel-level check that the known
   white gridline color `(255,255,255)` appears in the output, which a plain terrain/entity
   palette never produces). Location: same file as test 1.

3. **`test_should_escalate_composes_hard_rule_failure_and_grade`** — Category: unit. Directly
   tests the proposed `should_escalate(hard_results, grade)` function in isolation (no rendering,
   no state) across four cases: all-pass + grade A → False; one hard-rule fail + grade A → True;
   all-pass + grade D → True; all-pass + grade F → True; all-pass + grade C → False. Pins the
   investigation's concrete threshold decision as an explicit, reviewable contract. Location: same
   file as test 1, or `tests/unit/rendering/test_review_pipeline.py::TestShouldEscalate`.

4. **`test_tier1_digest_is_json_serializable_and_round_trips`** — Category: unit. Builds a
   `Tier1Digest`, serializes via the module's `digest_to_json` (or equivalent) helper, asserts
   `json.loads(json.dumps(...))` round-trips to an equal dict, and that every field named in the
   digest's dataclass is present as a key (catches an accidental field silently dropped during
   dict-conversion of `HardRuleResult`/`SoftRuleResult` tuples). Location: same file as test 1.

5. **`test_tier1_digest_golden_hash_field_identical_across_three_independent_runs`** — Category:
   unit, **`regression` marker** (per AC #5's explicit instruction: "tests/unit/, regression
   marker"). Mirrors `test_render_core.py::test_render_golden_hash_bit_identical_across_three_
   independent_runs`'s exact shape: build three independently-constructed-but-content-equal
   `AuthoritativeState` fixtures, run the full Tier 0→Tier 1 pipeline against each with a fixed
   `world_id`/`seed`/`tick`, serialize each resulting digest to JSON with `sort_keys=True`,
   SHA256-hash the JSON bytes, assert all three hashes are equal. This is the one test AC #5
   requires by name — comment/docstring must cite this ticket ID, mirroring the `regression`
   marker's documented standard in `docs/testing/test_taxonomy.md` ("must include a comment or
   link to the original ticket/issue"). Location: `tests/unit/rendering/test_review_pipeline.py`.

6. **`test_agent_review_output_contract_shape`** — Category: unit (contract/shape check, not an
   LLM-behavior test — this cannot and does not execute the `.claude/agents/*.md` file itself).
   If the pipeline exposes a Python-side helper that assembles the structured verdict skeleton
   (one-line summary field, findings-table row shape with severity + coordinate-evidence columns,
   recommended-next-steps list) for the agent to fill in, test that skeleton's shape directly.
   If no such Python-side skeleton is planned (the agent's own prompt owns the whole output
   contract), this test is N/A — record that explicitly in Implementation Notes rather than
   silently omitting AC #4 coverage; AC #4's real verification is a manual read of the finished
   `.claude/agents/world-render-reviewer.md` body against `simulation-analyst.md`'s Output section
   shape, not a pytest assertion. Location: same file as test 1, if applicable.

7. **`test_review_module_does_not_import_simulation_quality_or_observability_events`** — Category:
   architecture guard. Mirrors `test_density.py`/`test_shape.py`'s
   `test_<module>_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline` pattern
   exactly (AST-walk for `simulation_quality`/`observability.events` substrings in imports, and
   for `PillarScorer` in any class base list), applied to whichever new module(s) this ticket adds.
   Location: same file as test 1.

8. **`test_annotated_renderer_produces_valid_png_and_matches_plain_terrain_palette`** — Category:
   unit. New coverage for the newly-promoted `render_annotated()`-equivalent itself (not yet
   covered by any existing test, since it does not exist in `src/` yet): valid PNG structure
   (mirror `test_render_core.py::_read_chunks`'s hand-walked chunk/CRC32 verification), and that
   non-gridline pixels use the same `terrain_color()`/entity-color palette `render.py` already
   uses (no independent, drifted color table). Location: `tests/unit/rendering/
  test_render_annotated.py` (new file, following the one-test-file-per-module convention).

9. **`test_annotated_renderer_golden_hash_bit_identical_across_three_independent_runs`** —
   Category: unit, `regression` marker (extends `WORLD-RENDER-CORE`'s determinism guarantee to
   the new annotated renderer, matching `test_render_core.py`'s exact shape). Location: same file
   as test 8.

10. **`test_parity_ledger_infra_375_entry_matches_shipped_code`** — Category: unit
    (docs-consistency, not behavior). If this repo's existing parity-ledger-consistency test
    infrastructure (check for a generic `tests/tools/test_parity_index_*.py` or similar, per
    `docs/testing/regression_policy.md`'s documented baseline-drift pattern) already covers new
    entries generically, no new test is needed — confirm during implementation rather than add a
    redundant one-off test; only add a dedicated test if no generic parity-ledger-shape checker
    already exists.

## Scoped Pytest Commands

```bash
PYTHONPATH=. pytest tests/unit/rendering/ tests/architecture/test_rendering_zero_new_dependency_guard.py -v
```

```bash
PYTHONPATH=. pytest tests/unit/rendering/ -m regression -v
```

```bash
PYTHONPATH=. pytest tests/docs/test_doc_integrity.py -q
```

Never `pytest tests/` — scoped to `tests/unit/rendering/` (this ticket's real surface),
the rendering architecture guard, and the doc-integrity check triggered by editing
`docs/engine/contracts/regression_and_verification.md` and `docs/parity_ledger/infrastructure.yaml`.

## Anti-Drift Test Guards

- **Test 1 above is the load-bearing anti-drift guard for this entire ticket** — it is the only
  test that would catch a regression where someone "helpfully" renders the annotated PNG
  unconditionally (e.g. for caching, or because a later change forgets the escalation gate). Do
  not weaken it to only check the returned `Tier1Digest` fields; it must check the filesystem
  directly.
- **Test 7 (SimQ/observability import guard)** catches the same class of drift all four upstream
  metric siblings already guard against — a future edit accidentally importing
  `src.simulation_quality.*` for "convenience" (e.g. to reuse a formatting helper) would silently
  violate this batch's architectural-independence boundary without this test.
- **`tests/architecture/test_rendering_zero_new_dependency_guard.py`** (existing, regression
  surface, not new) already catches a drift risk specific to this ticket: a tempting
  implementation shortcut for the bitmap-digit font or gridline drawing (e.g. reaching for
  `Pillow` instead of porting `render_annotated.py`'s hand-rolled 3×5 font) would fail this guard
  immediately.
- **Test 5 and test 9 (golden-hash regression tests)** guard against the same determinism-drift
  class `test_render_core.py`'s existing golden-hash test guards for the plain renderer — a future
  change introducing set/dict iteration-order dependence, wall-clock timestamps, or
  hash-randomized ordering into either the digest-building or annotated-rendering path would be
  caught immediately, before it reaches AC #3's determinism claim.
- **A test that should NOT be written, flagged explicitly so it isn't added by mistake later:**
  no test should pin a specific `grade` letter or `combined_score` value against real corpus
  worlds as a regression anchor — mirroring `test_grading.py`'s own documented Test 14 precedent
  ("deliberately does NOT pin a specific grade letter ... since this ticket's illustrative
  thresholds are explicitly uncalibrated"). This ticket's `should_escalate` threshold is derived
  from `grading.py`'s still-uncalibrated config; pinning real-world grade output now would create
  false regression noise the moment `TCK-20260821-VISUAL-QUALITY-CALIBRATION` lands.
