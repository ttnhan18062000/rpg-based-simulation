---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260831-DOC-TAG-ENFORCEMENT
artifact_type: test_plan
tags: [frontmatter, tagging, taxonomy, documentation, schema]
---

# Test Plan — TCK-20260831-DOC-TAG-ENFORCEMENT

## Regression Surface

All must keep passing unmodified (unit, `tools/` scope — no arena-combat/integration surface is
touched by this ticket, it is pure tooling/process infrastructure):

- `tests/tools/test_validate_frontmatter.py` — all 9 groups (`TestFrontmatterDetection`,
  `TestDocContentType`, `TestTicketContentType`, `TestArtifactContentType`,
  `TestArchiveContentType`, `TestDirectoryScan`, `TestForbiddenPriorityTags`,
  `TestTagCanonicalization`, `TestTagRegistryEnforcement`, `TestExitCodeContract`,
  `TestEnumAntiDrift`, `TestPreviouslyFrontmatterMissingDocs`). Particular attention to:
  - `TestDocContentType` (lines 173-245) — every existing doc test must still pass exactly as
    written, including `test_doc_tags_optional_present` (line 236, tags `[combat, ai]`, no
    `registry` argument passed) and `test_doc_tags_optional_absent` (line 243) — these currently
    pass purely because `_validate_doc` never checks tags at all; after this ticket they must still
    pass, but now because the new doc-tag check correctly resolves both cases as in-scope-and-valid
    or out-of-scope, not because the check is silently absent.
  - `TestTagRegistryEnforcement` (lines 559-621) — all 7 tests, unchanged, since they test
    `_check_tags`'s ticket/artifact-side behavior which must not regress when generalized.
  - `TestEnumAntiDrift::test_tag_taxonomy_effective_date` (line 707) — `TAG_TAXONOMY_EFFECTIVE_DATE
    == "20260704"` must remain unchanged; this ticket does not touch the ticket-side cutoff date.
  - `TestPreviouslyFrontmatterMissingDocs` (lines 731+) — 12 real-path regression pins; must keep
    passing since none of those 12 docs' frontmatter is touched by this ticket.
- `tests/tools/test_tag_registry.py` — `canonical_form_violation`, `is_tag_registered`,
  `load_registry`, `add_tag` must be untouched (this ticket only calls into them, never
  reimplements or edits them, per its own Out-of-Scope).
- `tests/tools/test_layer_registry.py` — untouched; `layer_values()`/`is_layer_registered()` logic
  is not modified by this ticket, only potentially *invoked more broadly* if Plan decides to fix
  the 1 invalid-layer doc found in investigation.md.
- `tests/tools/test_tag_report.py` (all ~15 existing tests) and `tests/tools/test_tag_corpus_sweep.py`
  (all ~20 existing tests) — untouched; this ticket does not modify `tag_report.py`'s or
  `tag_corpus_sweep.py`'s existing ticket/artifact-scoped corpus walk, per investigation.md's Prior
  Work section (the corpus-repair-sweep ticket's own Scope Guards explicitly protect these).
- `tests/tools/test_generate_registry.py` — untouched; this ticket does not modify
  `generate_registry.py`'s `collect_docs`/`collect_tickets` projections.
- `tests/tools/test_done_checker_static.py` — must keep passing; `check_frontmatter_valid`'s
  existing `validate_file(ticket_path, registry=registry)` / `validate_directory(staging_dir,
  content_type_override="artifact", registry=registry)` call sites (confirmed in investigation.md
  as the only consumers of `validate_file`/`validate_directory`) never invoke the `doc` content
  type, so they are structurally unaffected — but re-run explicitly as a direct regression check
  since `_check_tags`'s internals are being generalized/refactored.
- `tests/tools/test_ticket_field_values.py` — untouched; only imports `LAYER_VALUES`, unaffected by
  tag-check changes.

## New Tests Required

All new tests live in `tests/tools/test_validate_frontmatter.py`, following the file's existing
`TestDocContentType`/`TestTagRegistryEnforcement`-style class-per-concern grouping (add a new
`TestDocTagEnforcement` class placed after `TestTagRegistryEnforcement`, before
`TestExitCodeContract`, to preserve the file's numbered-group-comment structure). Exact assertions
depend on which cutover mechanism `plan.md` selects (per investigation.md's Open Question #1) —
listed here at the behavior level so they apply regardless of the chosen mechanism's concrete field
name/shape:

- **`test_doc_registered_tag_accepted`** — unit. A synthetic doc fixture, marked in-scope per the
  chosen cutover signal, with a tag already in an in-memory `registry` dict → `validate_file(...,
  registry=registry) == []`. Mirrors `TestTagRegistryEnforcement::test_registered_tag_accepted`.
  Lives in `TestDocTagEnforcement`.
- **`test_doc_unregistered_tag_rejected`** — unit. Same in-scope doc fixture, tag not in the
  in-memory registry → error list contains a message naming the tag and "not in the tag registry",
  matching `_check_tags`'s existing error-message shape (`f"{filepath}: tags: {tag!r} is not in the
  tag registry — register it first via ..."`) so the doc-side error is not a divergent second
  format. Lives in `TestDocTagEnforcement`.
- **`test_doc_non_canonical_tag_rejected`** — unit. In-scope doc fixture with a tag like `Combat`
  (uppercase) → error contains "not canonical form", reported before/independent of registry
  membership (mirrors `test_canonical_form_violation_reported_before_registry_check`). Lives in
  `TestDocTagEnforcement`.
- **`test_doc_phase_milestone_tag_exempt_from_registration`** — unit. In-scope doc fixture with
  `tags: [phase-5]` and an empty registry → passes with no error, mirroring
  `test_phase_milestone_tag_accepted_without_registration`. Lives in `TestDocTagEnforcement`.
- **`test_doc_predating_cutover_signal_not_newly_rejected`** — unit, **the single AC-mandated
  grandfathering test**. Uses a *real* pre-existing doc fixture from the repo tree that (a) predates
  whatever cutover signal Plan picks (i.e. does not carry it, or carries a pre-cutoff value) and (b)
  is known, from investigation.md's measurement, to carry an unregistered tag today — e.g.
  `docs/world/assembly_contract.md` (tags include `contract`, confirmed unregistered per
  investigation.md's "Retrofit blast radius" table) or `docs/simulation/domains/campaigns_contract.md`
  (tags include `domains`, `campaigns`, `contract`, several unregistered). Assert
  `validate_file(<real_path>, registry=<real_or_empty_registry>) == []` (or at minimum, contains no
  `tags:`-prefixed error) — i.e. the file is not newly broken by this ticket. This directly
  satisfies Acceptance Criterion #3 ("grandfathering verified against a real pre-existing doc
  fixture"). Lives in `TestDocTagEnforcement`.
- **`test_doc_within_cutover_scope_with_registered_tag_passes_end_to_end`** — unit/integration
  hybrid. Constructs a synthetic doc fixture carrying the chosen cutover signal at/after the
  effective date, with only already-registered tags (e.g. `combat`, `ai` — both present in
  `registries/tag_registry.jsonl` per investigation.md) → `validate_file(f, registry=load_registry())
  == []` using the *real* registry (not a synthetic in-memory one), confirming the new check
  integrates correctly with the live registry file, not just a mock. Lives in
  `TestDocTagEnforcement`.
- **`test_check_tags_ticket_scope_unaffected_by_doc_generalization`** — architecture guard. Re-runs
  (or directly re-asserts) the exact scenarios from `TestTagRegistryEnforcement`'s existing 7 tests
  against whatever the refactored `_check_tags` (or its generalized helper) looks like post-
  Implement, to make explicit — not just implicit via existing-test-reruns — that generalizing the
  scope-derivation for docs did not alter ticket/artifact behavior. Category: architecture guard.
  Lives in `TestDocTagEnforcement` or a new small `TestCheckTagsGeneralization` class, whichever
  Implement's actual refactor shape makes more natural.
- **`test_validate_doc_no_longer_silently_skips_tags`** — architecture guard, **the single
  highest-value anti-regression test in this plan**. Directly guards against investigation.md's
  named failure mode (a naive, structurally-inert wire-in of `_check_tags` into `_validate_doc`
  that always no-ops because docs never carry `ticket_id`). Constructs an in-scope doc fixture with
  a *definitely*-unregistered tag and an *empty* registry, and asserts the returned error list is
  **non-empty** and mentions `tags`. This test must fail against the naive/broken implementation
  and pass only against a real, functioning doc-tag check. Lives in `TestDocTagEnforcement`.
- **`test_invalid_layer_doc_fixture_still_rejected`** — unit, regression pin for investigation.md's
  layer finding. Uses the real fixture `docs/simulation/domains/social_memory_contract.md`
  (currently `layer: social`, not in `LAYER_VALUES`) and asserts `validate_file(<path>)` contains a
  `layer: invalid value 'social'` error — confirms the pre-existing (already-working) doc-layer
  enum check is unaffected by this ticket's tag-check changes, and pins the one real doc-layer
  violation this investigation found so a future fix to that file is a deliberate, visible test
  change rather than a silent pass-to-fail flip. Lives in `TestDocContentType` (extends the
  existing group, since this is a layer-only assertion, not a tag one) or a new
  `TestDocLayerCoverage` class if Plan/Implement decides to make the real-corpus layer check a
  first-class documented behavior.
- **(Conditional on Plan's cutover-mechanism choice) `test_doc_missing_cutover_field_defaults_to_exempt`**
  — unit. If Plan picks option (a) (a new opt-in marker/date field per investigation.md), a doc
  fixture with no such field at all must be exempt (matches every currently-existing doc in the
  corpus, since the field doesn't exist yet anywhere). This is effectively the general form of
  `test_doc_predating_cutover_signal_not_newly_rejected` above, stated as the *default* case rather
  than against one specific real file.

## Scoped Pytest Commands

```bash
# Primary regression + new-test surface for this ticket
python3 -m pytest tests/tools/test_validate_frontmatter.py -v

# Adjacent tag/layer registry surface this ticket reads from but must not alter
python3 -m pytest tests/tools/test_tag_registry.py tests/tools/test_layer_registry.py -v

# Consumer surface confirmed in investigation.md as the only validate_file/validate_directory caller
python3 -m pytest tests/tools/test_done_checker_static.py -v

# Adjacent reporting tools confirmed untouched but sharing tag_registry.py imports
python3 -m pytest tests/tools/test_tag_report.py tests/tools/test_tag_corpus_sweep.py -v

# Combined single scoped run for Test-phase verification
python3 -m pytest tests/tools/test_validate_frontmatter.py tests/tools/test_tag_registry.py \
  tests/tools/test_layer_registry.py tests/tools/test_done_checker_static.py \
  tests/tools/test_tag_report.py tests/tools/test_tag_corpus_sweep.py -v
```

Never: `pytest tests/` (full suite) — this ticket's blast radius is entirely within
`tools/validate_frontmatter.py` and its direct `tools/tools/tests` neighborhood; no `src/`
simulation code is touched.

## Real-Corpus Verification (per Acceptance Criterion #6, not a pytest test)

Acceptance Criterion #6 requires running `python3 tools/validate_frontmatter.py docs/` post-
implementation and recording "a bounded, understood violation count (not a silent mass-failure)"
in the ticket's `Test Summary`. Based on this investigation's direct measurement, whoever
implements should expect (subject to whatever retrofit/cutover choice Plan makes):

- If Plan chooses pure forward-only grandfathering (option (a), no backfill): **0 new tag
  violations** against the existing 397-doc corpus, since every existing doc predates the new
  cutover signal by construction (the field/marker doesn't exist on any of them yet) — the check
  only bites future/newly-touched docs.
- If Plan chooses any retroactive/no-cutoff enforcement instead: up to **234 unregistered-tag
  violations** (362 tag occurrences) plus **3 canonical-form violations**, spread across roughly
  206 doc files that carry tags at all — this is the concrete "understood count" AC #6 asks for,
  not a surprise.
- Layer side, independent of the cutover decision: **1 pre-existing violation**
  (`docs/simulation/domains/social_memory_contract.md`, `layer: social`) — already-latent today,
  unmasked the first time `validate_frontmatter.py docs/` is actually run comprehensively,
  regardless of anything this ticket changes.

This section is guidance for Implement/Verify to compare their actual run's output against, not a
pytest assertion (a hardcoded live-corpus count would itself violate the corpus-repair-sweep
ticket's own established anti-drift precedent against asserting exact live-corpus counts in tests).

## Anti-Drift Test Guards

- `test_validate_doc_no_longer_silently_skips_tags` (above) is the primary guard against the
  ticket's own named failure mode: a technically-present-but-functionally-inert doc-tag check.
- `test_check_tags_ticket_scope_unaffected_by_doc_generalization` (above) guards against the
  `_check_tags` generalization silently changing ticket/artifact-side forward-only semantics while
  fixing the doc-side gap — the two content types must remain independently correct.
- Full unmodified re-run of `TestTagRegistryEnforcement`'s 7 existing tests is itself an anti-drift
  guard by construction — any refactor of `_check_tags`'s internals that breaks ticket/artifact
  behavior fails these before anything doc-specific is even exercised.
- `test_invalid_layer_doc_fixture_still_rejected` guards against a future accidental "fix" to
  `docs/simulation/domains/social_memory_contract.md` silently disappearing without a corresponding,
  deliberate test update — a silent pass-to-fail-to-pass flip on this fixture is itself a signal
  worth catching.
- No test in this plan may assert an exact violation count against the *live* corpus
  (`docs/REGISTRY.yaml`'s current 397 doc entries or `validate_frontmatter.py docs/`'s real output)
  — mirrors `TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`'s explicit anti-drift precedent
  (`stored_artifacts/TCK-20260720-TAG-CORPUS-REPAIR-SWEEP/plan.md`'s Anti-Drift Notes) against
  count-based assertions that would break as the corpus grows; all count-shaped findings in this
  test plan and investigation.md are point-in-time evidence for Plan/Implement/Verify to read, not
  values to hardcode into `assert`s.
- If Plan's chosen retrofit strategy includes any bulk registration of doc tags into
  `registries/tag_registry.jsonl`, that registration must go through `tag_registry.py::add_tag()`
  (never a raw JSONL append) and must not be silently absorbed into this ticket at all per its own
  Out-of-Scope — a test asserting `registries/tag_registry.jsonl` is unchanged by this ticket's own
  commits (a simple `git diff --stat` check in CI/Verify, not necessarily a pytest test) is a
  reasonable scope-creep guard if Implement is tempted to "just register the obvious ones while
  I'm in there."
