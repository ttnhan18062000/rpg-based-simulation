---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260720-TAG-TOUCHPOINT-CLEANUP
artifact_type: test_plan
tags: [tagging, workflows]
---

# Test Plan — TCK-20260720-TAG-TOUCHPOINT-CLEANUP

## Regression Surface

Existing tests that must keep passing, grouped by domain. None of these should need behavior
changes under the recommended design (Option B, `validate_frontmatter.py`'s public contract
unchanged) — only `tests/tools/test_done_checker_static.py`'s 5 `classify_checklist_failure` tests
and `tests/tools/test_registry_query.py`'s `SEED_TAGS`-adjacent test need fixture/assertion
updates (see New Tests Required).

**Unit — `tools/gate_checks/done_checker_static.py`** (`tests/tools/test_done_checker_static.py`,
~600 lines, all currently passing):
- All `check_staging_artifacts_complete`, `check_data_runs_clean`/`clean_data_runs_early`,
  `check_ticket_location`, `check_working_log_no_row_yet`, `check_frontmatter_valid`,
  `check_ticket_field_values_valid` tests — untouched by this ticket's changes except
  `check_frontmatter_valid`'s own tests must keep passing once it starts passing a real `registry`
  through (see New Tests Required — this could newly surface a `FAIL` for any *existing* fixture
  that happens to carry an unregistered tag; current fixtures use `tags: []`, confirmed safe by
  direct read of `TICKET_FM`/`ARTIFACT_FM` in the test file).
- `run_static_precheck`/`run_finalize_selfcheck` aggregation tests (`test_run_static_precheck_*`,
  `test_run_finalize_selfcheck_*`) — condition count and ordering must stay identical.
- `check_migration_complete`, `check_ticket_finalized`, `check_working_log_exactly_one_row`,
  `check_monitoring_write_recorded`, `check_registry_entry_regenerated` — Part B, untouched.

**Unit — `tools/validate_frontmatter.py`** (`tests/tools/test_validate_frontmatter.py`, 50+
assertions of `validate_file`/`validate_directory` `list[str]`/`dict[Path, list[str]]` return
shape) — **must pass byte-for-byte unmodified**. This is the regression surface that most directly
proves the recommended design (no change to `_check_tags`'s return type) was actually followed —
any diff in this file during implementation is a signal the implementer took the rejected Option A
path instead.

**Unit — `tools/tag_registry.py`** (`tests/tools/test_tag_registry.py`,
`tests/tools/test_tag_category_registry.py`) — `check_tags_registered`, `is_tag_registered`,
`load_registry`, `category_values` all consumed as-is by the new
`_frontmatter_has_unregistered_tags` helper; none of their own behavior changes.

**Unit — `tools/registry_query.py`** (`tests/tools/test_registry_query.py`, 3 test functions,
read in full) — `filter_registry`'s 2 tests (`test_registry_matches_union_layer_and_tags_not_
intersection`, `test_faction_tag_query_surfaces_entries_layer_search_would_miss`) are unaffected
(they never call `candidate_tags_from_text`/`SEED_TAGS`). `test_candidate_tags_from_seed_vocabulary_
matches_substring` must be updated (see New Tests Required) since it directly depends on
`SEED_TAGS`'s existence.

**Unit — `tools/tag_report.py`** (`tests/tools/test_tag_report.py`) — untouched; already reads
category live from the registry, no `SEED_TAGS`/hardcoded-list dependency.

**Unit — agent-monitoring** (`tests/tools/test_generate_retro.py`) — untouched;
`generate_retro.py` has no doc-path or category-list references to fix.

**Integration — CI wiring** — `test.yml` line 124 (`pytest tests/tools`) already covers all of the
above; no new CI mechanism needed (confirmed by this ticket's own Assumptions bullet 4).

## New Tests Required

Per acceptance criteria:

### AC #1 — `done_checker_static.py` reason-code derivation

1. **`test_frontmatter_has_unregistered_tags_detects_real_violation`**
   Category: unit. Verifies `_frontmatter_has_unregistered_tags(ticket_id, tier)` returns `True`
   when the fixture ticket's frontmatter `tags:` includes a tag not present in a fixture registry
   (constructed via `tag_registry.add_tag(..., root=tmp_path)` or a hand-written
   `registries/tag_registry.jsonl` under `tmp_path`, then `monkeypatch.chdir(tmp_path)`) —
   this is the "prove it catches a real violation" fixture this test file's own module docstring
   (line 3-6) requires for every check function.
   Location: `tests/tools/test_done_checker_static.py`.

2. **`test_frontmatter_has_unregistered_tags_false_when_all_registered`**
   Category: unit. Same fixture shape, but every declared tag is present in the fixture registry
   — asserts `False`.
   Location: `tests/tools/test_done_checker_static.py`.

3. **`test_frontmatter_has_unregistered_tags_checks_staging_artifacts_too`**
   Category: unit. Standard-tier fixture where the *ticket* frontmatter's tags are all registered
   but one *staging artifact* file's tags include an unregistered one — asserts `True`. Proves the
   helper checks both locations, not just the ticket file (mirrors `check_frontmatter_valid`'s own
   dual-location behavior).
   Location: `tests/tools/test_done_checker_static.py`.

4. **`test_frontmatter_has_unregistered_tags_hotfix_skips_staging_dir`**
   Category: unit. Hotfix-tier fixture with no `staging_artifacts/` directory and an unregistered
   tag *only* in a staging-dir file that doesn't exist — asserts the function doesn't error and
   correctly reflects only the ticket file's tags (mirrors `check_frontmatter_valid`'s existing
   hotfix branch, lines 250-253).
   Location: `tests/tools/test_done_checker_static.py`.

5. **`test_check_frontmatter_valid_fails_on_unregistered_tag`** (fixes the pre-existing gap
   documented in investigation.md's Current Behavior #1)
   Category: unit, **regression-prone / bug-fix proof**. Direct fixture with an unregistered tag
   in the ticket's frontmatter, real registry loaded — asserts `check_frontmatter_valid(...)`
   itself now returns `("FAIL", ...)`, proving the underlying condition is enforced, not just the
   reason-code classification layered on top. This is the single most important new test in this
   ticket — without it, the "gate never actually enforced registry membership" gap from
   investigation.md could regress silently even if `classify_checklist_failure`'s own tests pass.
   Location: `tests/tools/test_done_checker_static.py`.

6. **`classify_checklist_failure`'s existing 5 tests, updated per AC #1's "equivalently-asserted
   behavior" allowance** (not new tests, but require rewriting):
   - `test_classify_checklist_failure_tag_registry_rejection` and
     `test_classify_checklist_failure_scans_past_leading_pass_entries`: rewrite to build a real
     `tmp_path` fixture (unregistered tag on disk) and call
     `classify_checklist_failure(checklist, ticket_id=..., tier=...)` — assert
     `"tag_registry_rejection"` still returned, now via the independent re-check path instead of
     evidence-text matching.
   - `test_classify_checklist_failure_all_pass_returns_none`,
     `test_classify_checklist_failure_generic_dod_failure`,
     `test_classify_checklist_failure_returns_first_fail_when_multiple`: no fixture change needed
     (none of these ever hit a `frontmatter_valid`-condition `FAIL`) — verify they still pass
     calling the function with the new optional-kwarg signature and no `ticket_id`/`tier` (default
     `None`), proving backward compatibility for callers that don't supply ticket context.
   Location: `tests/tools/test_done_checker_static.py` (same file, in place).

7. **`test_classify_checklist_failure_condition_key_used_not_evidence_text`**
   Category: unit, **anti-drift guard**. Constructs a `checklist` where the `frontmatter_valid`
   item's `evidence` field happens to contain the literal marker string `"is not in the tag
   registry"` as an unrelated quoted example (e.g. inside a docstring-like note), but the item's
   own real tags (as re-checked against a fixture registry) are all registered — asserts
   `classify_checklist_failure` returns `"dod_condition_failed"`, **not**
   `"tag_registry_rejection"`. Proves the classification no longer keys off text content at all.
   Location: `tests/tools/test_done_checker_static.py`.

### AC #2 — `registry_query.py` live registry read

8. **`test_candidate_tags_from_text_reads_live_registry`**
   Category: unit. Monkeypatches/points `registry_query.py`'s registry lookup at a fixture
   `registries/tag_registry.jsonl` (via `root=` param, or `monkeypatch.chdir(tmp_path)` matching
   `tag_registry.py`'s own `root`-parameter convention) containing a *newly invented*
   subsystem-topic tag not in `SEED_TAGS`'s original 10 words (e.g. `"siege-warfare"`) — asserts
   `candidate_tags_from_text("a ticket about siege-warfare tactics")` returns a set containing
   `"siege-warfare"`. This is the ticket's own literal AC wording: "adding a new subsystem-topic
   tag via the CLI makes it queryable with zero code change."
   Location: `tests/tools/test_registry_query.py`.

9. **`test_candidate_tags_from_text_ignores_non_subsystem_topic_tags`**
   Category: unit. Fixture registry with a `process-skill-signal` tag (e.g. `"debugging"`) and a
   `meta-process` tag — asserts neither appears in `candidate_tags_from_text`'s output even when
   its literal word appears in the input text. Proves the live-read is scoped to
   `subsystem-topic` category only, matching `SEED_TAGS`'s original intent (a topic-vocabulary
   filter, not a full-registry filter).
   Location: `tests/tools/test_registry_query.py`.

10. **`test_candidate_tags_from_seed_vocabulary_matches_substring`** (existing test, update in
    place): must keep asserting `"faction" in candidate_tags_from_text(...)` — `faction` is
    confirmed registered as `subsystem-topic` today (see investigation.md), so this specific
    assertion survives the swap unmodified; only the *mechanism* under test changes. The second
    assertion (`candidate_tags_from_text("nothing relevant here", "", "") == set()`) must be
    re-verified against the live registry's actual current subsystem-topic tag list (19 tags as of
    this investigation) to confirm none of "nothing"/"relevant"/"here" collide as substrings —
    confirmed no collision by direct check of the 19 registered words.
    Location: `tests/tools/test_registry_query.py`.

11. If the planner adopts this investigation's SEED_TAGS-coverage-gap recommendation (registering
    `combat`/`economy`/`resource`/`content`/`engine`/`strategy` as `subsystem-topic` tags):
    **`test_seed_words_still_registered_as_subsystem_topic`** — a coverage-preservation guard
    asserting all 6 previously-unregistered `SEED_TAGS` words are present in the live registry as
    `subsystem-topic` tags after this ticket lands. Category: unit, anti-drift guard.
    Location: `tests/tools/test_registry_query.py` or `tests/tools/test_tag_registry.py`.

### AC #3 — doc references

No new tests required — this AC is documentation-only and, per investigation.md, appears already
satisfied by `TCK-20260720-TAG-REGISTRY-RELOCATE`/`TCK-20260720-TAG-CATEGORY-REGISTRY`. If the
planner finds and fixes any residual stale reference, no dedicated test is warranted (docs have no
existing test harness in this repo beyond frontmatter-schema validation, which is unaffected).

### AC #4 — JS mirror decision

12. **`test_classify_checklist_failure_js_mirror_matches_python_reference`** (if the JS mirror is
    updated in lockstep, per this investigation's recommendation) — category: **architecture
    guard**, likely implemented as a Node-side test or an extension of the existing
    `tests/tools/test_current_run_sidecar_orchestrator.py`-style JS-behavior test (need to confirm
    this repo's JS test harness — check for an existing `.claude/workflows/*.test.js` or similar
    convention before assuming pytest can drive it; if no Node test harness exists in this repo, a
    documented manual verification step in plan.md is an acceptable substitute, but should not be
    silently skipped).
    What it verifies: for both the `tag_registry_rejection` case and the `dod_condition_failed`
    case, the JS mirror's classification agrees with the Python reference implementation's,
    exercised against the same fixture ticket/registry state.
    Location: TBD by planner (`tests/` JS-side location does not yet clearly exist in this repo —
    flag as an open question for the planner rather than assuming a location).

## Scoped Pytest Commands

```bash
# Primary regression surface for this ticket's touched modules:
python3 -m pytest tests/tools/test_done_checker_static.py tests/tools/test_validate_frontmatter.py \
  tests/tools/test_registry_query.py tests/tools/test_tag_registry.py \
  tests/tools/test_tag_category_registry.py tests/tools/test_tag_report.py \
  tests/tools/test_generate_retro.py -v

# Full tools/ regression sweep (matches CLAUDE.md's Testing Rule scoping guidance — this repo's
# existing CI convention, test.yml line 124, already runs this full directory):
python3 -m pytest tests/tools/ -v
```

Never `pytest tests/` — out of scope per CLAUDE.md's Testing Rule; this ticket touches no
simulation/engine code, so no `tests/unit/engine/`, `tests/integration/`, or arena-combat suites
are implicated.

## Anti-Drift Test Guards

- **`test_classify_checklist_failure_condition_key_used_not_evidence_text`** (New Test #7 above)
  — the direct proof that classification no longer depends on evidence-text content, closing off
  a future regression back to substring matching.
- **`test_check_frontmatter_valid_fails_on_unregistered_tag`** (New Test #5) — guards against the
  pre-existing enforcement gap (registry never actually checked by the static precheck) silently
  persisting even after `classify_checklist_failure` itself is "fixed." This is the test most
  likely to catch an implementer who fixes only the classification layer without also threading a
  real `registry` through `check_frontmatter_valid`.
- **`test_candidate_tags_from_text_ignores_non_subsystem_topic_tags`** (New Test #9) — guards
  against `candidate_tags_from_text` silently widening scope to match *any* registered tag
  (defeating the "seed vocabulary" framing) rather than staying scoped to `subsystem-topic`.
- **Zero-diff guard on `tests/tools/test_validate_frontmatter.py`**: run this file's full suite
  before and after the change and diff the output — any assertion change here is itself a signal
  the implementer took the rejected Option A path (changing `_check_tags`'s return contract)
  instead of the recommended Option B. Not a new test, but an explicit verification step the
  implementer/verifier should perform and note in plan.md's Deviations section if it fires.
- **`INFRA-180`/`INFRA-263` parity-ledger entries** (both `verified`, P2) should be spot-checked
  at Verify time to confirm their `v2_evidence` still accurately describes `validate_frontmatter.py`
  and `check_registry_entry_regenerated` behavior — expected to need zero edits under the
  recommended design, but this is a cheap confirmation, not a new automated test.
