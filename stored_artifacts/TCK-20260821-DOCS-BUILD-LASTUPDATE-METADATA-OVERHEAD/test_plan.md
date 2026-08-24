---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD
artifact_type: test_plan
tags: [documentation, performance]
---

# Test Plan — TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD

## Addendum — Scope Expanded 2026-08-24 (repo-owner decision, post-Investigate)

Per investigation.md's own addendum: the repo owner decided to drop the `tickets`/`artifacts`/
`agent-monitoring` plugins entirely (not just their metadata setting) and expand `docs`'s `exclude`
list to drop `archive/**`, `plans/**`, `audits/**`. The three "New Tests Required" below are
rewritten accordingly (metadata-presence assertions replaced with plugin-absence + exclude-list
assertions); the Context Constraint, Regression Surface, and Anti-Drift sections below still apply
as originally written and are not repeated here. The live-`workflow_dispatch`-before-merge
requirement (ticket AC) is not a pytest test — it's a real CI run the orchestrator triggers
directly, tracked separately from this test plan.

## Context Constraint (read before scoping)

`website/node_modules/` is not installed in this worktree, and `npm ci` was not run during
Investigate (see investigation.md's "What Could Not Be Verified"). This means:
- No real `docusaurus build` can be exercised from pytest here, matching the sibling hotfix
  ticket's own precedent (`tests/static/test_deploy_docs_heap_limit.py` is YAML-parse-based, not
  a live-build test, for the identical reason: no live GitHub Actions/full-build execution is
  possible from pytest).
- `website/docusaurus.config.js` cannot be `require()`-d directly by plain Node either — verified
  during Investigate: `node -e "require('./docusaurus.config.js')"` fails with `Cannot find
  module '@easyops-cn/docusaurus-search-local'` because that theme is referenced via
  `require.resolve(...)` at the top level of the config's `themes` array, and the package isn't
  installed. So the new guard test below must use **text/regex-based parsing** of the raw
  `docusaurus.config.js` source, not `require()`/`node -e` evaluation — following the same
  "parse structurally, don't execute" precedent `test_deploy_docs_heap_limit.py` set for the YAML
  workflow file, adapted for a JS source file.
- This ticket's AC #3 ("A real build comparison ... reports the measured memory/time reduction")
  is **not achievable as a pytest test** at all — it requires either a real local
  `npm ci && npm run build` run (Implement/Test phase, with real time budget) or observation of
  the next live CI run after merge. This test plan does not invent a test claiming to satisfy
  that AC; it is called out explicitly here so Test/Verify don't expect one.

## Regression Surface

Existing tests that must keep passing, grouped by relevance:

**Unit / static — direct regression surface for this ticket's file:**
- `tests/static/test_deploy_docs_heap_limit.py` — must stay green unchanged; this ticket does not
  touch `.github/workflows/deploy-docs.yml`, so no regression is expected, but it's the sibling
  file in the same OOM investigation and should be re-run to confirm no accidental cross-file
  edit occurred.
- `tests/static/__init__.py`, `tests/static/test_ci_narrow_path_filtered_jobs.py`,
  `tests/static/test_ci_requirements_no_ml_stack.py`,
  `tests/static/test_ci_step_summary_reporting.py`,
  `tests/static/test_corpus_diversity_ci_isolation.py`,
  `tests/static/test_no_direct_dirtyset_candidate_selection.py` — the full current
  `tests/static/` directory; none of these currently reference `docusaurus.config.js`, but the
  new test lands in this same directory so the whole directory should be run together as one
  scoped pass.

**Integration / tooling — parity ledger and frontmatter regression surface (touched because
`docs/parity_ledger/infrastructure.yaml`'s `INFRA-181` entry gets edited per investigation.md):**
- `tests/tools/test_parity_ledger_schema.py` — validates `docs/parity_ledger/schema.json`'s raw
  structure (unaffected by an entry-content edit, but cheap to include for the same-directory
  edit).
- `tests/tools/test_parity_index.py` — imports and validates all real parity-ledger YAML shards
  (including `infrastructure.yaml`) into the parity index DB; its "entry_health (missing
  evidence)" test group is the direct regression check that would catch a malformed `INFRA-181`
  edit (e.g. a `verified` entry left with null `v2_evidence`).
- `tests/tools/test_parity_index_baseline.py` — baseline-count guard; per this project's known
  drift pattern (a hardcoded baseline this session's own legitimate edit can shift), if editing
  `INFRA-181` changes any baseline count this test tracks (e.g. `missing_test_path_count`, if
  `test_path` gets filled in), that's an *expected* drift requiring a baseline update alongside
  the fix, not a bug — see CI Failure Triage precedent in this project's CLAUDE.md.

**No architecture-guard or arena-combat tests apply** — this ticket has zero interaction with
`src/`, simulation mechanics, or combat/entity logic. It is a pure docs-build-tooling config
change.

## New Tests Required

1. **Test name**: `test_tickets_artifacts_agent_monitoring_plugins_removed`
   - **Category**: unit / static guard (follows `tests/static/test_deploy_docs_heap_limit.py`
     precedent: parse-not-execute).
   - **What it verifies**: reads `website/docusaurus.config.js` as raw text and asserts none of
     `id: 'tickets'`, `id: 'artifacts'`, `id: 'agent-monitoring'` appear anywhere in the file —
     the three plugin instances are gone entirely, not just metadata-disabled.
   - **Where it lives**: `tests/static/test_docs_build_content_scope.py` (new file, same directory
     as the sibling OOM hotfix's guard test).

2. **Test name**: `test_docs_preset_unchanged_and_present`
   - **Category**: unit / static guard — anti-drift companion, the higher-value test given the
     realistic failure mode is an over-eager edit taking out the `docs` preset along with the three
     removed plugins.
   - **What it verifies**: the `classic` preset's `docs` block (`path: '../docs'`,
     `routeBasePath: 'docs'`) is still present, and its `showLastUpdateTime: true` /
     `showLastUpdateAuthor: true` are unchanged (still `true`) — this ticket's Out-of-Scope boundary
     enforced by a failing test.
   - **Where it lives**: same new file.

3. **Test name**: `test_docs_exclude_list_covers_approved_exclusions_only`
   - **Category**: architecture guard (structural invariant — the core correctness check for the
     expanded scope).
   - **What it verifies**: the `docs` preset's `exclude` list contains `archive/**`, `plans/**`,
     `audits/**` (plus the pre-existing `superpowers/**`, `specs/**`, `parity_ledger/**`,
     `scenarios/**`, `entity/**`), AND does **not** exclude any of the approved-subset folder names
     (`agent-monitoring`, `guides`, `mechanics`, `engine`, `core`, `systems`, `combat`, `strategy`,
     `world`, `simulation`, `cognition`, `testing`, `architecture`, `observability`, `ai`,
     `compliance`, `guidelines`, `performance`, `visual_quality`, `simulation_quality`, `content`,
     `event_ledger`) — a single test asserting both directions catches either an over-broad or
     under-broad edit to the same list. `docs/agent-monitoring/` (3 developer-facing schema docs)
     is distinct from the removed top-level `agent-monitoring` plugin instance and must stay
     published — an architecture-review finding that caught this being unaccounted for in the
     original list.
   - **Where it lives**: same new file.

4. **Test name**: `test_navbar_and_search_theme_no_longer_reference_removed_routes`
   - **Category**: unit / static guard.
   - **What it verifies**: `themeConfig.navbar.items` contains no `/tickets/`, `/artifacts/`, or
     `/agent-monitoring/` entries, and the `@easyops-cn/docusaurus-search-local` theme's
     `docsRouteBasePath` array contains only `'docs'`.
   - **Where it lives**: same new file.

5. **Test name**: `test_removed_sidebar_files_deleted`
   - **Category**: unit / static guard (file-existence, not config-parsing).
   - **What it verifies**: `website/sidebars-tickets.js`, `website/sidebars-artifacts.js`,
     `website/sidebars-agent-monitoring.js` no longer exist on disk (dead config removed alongside
     the plugin instances that referenced them).
   - **Where it lives**: same new file.

6. **Test name**: `test_homepage_no_longer_references_ticket_artifact_counts`
   - **Category**: unit / static guard.
   - **What it verifies**: `website/src/pages/index.js` no longer contains the strings "closed
     tickets" / "artifact sets" (or equivalent stale-count language) that referenced the now-removed
     sections.
   - **Where it lives**: same new file.

No test is proposed for the `docs/parity_ledger/infrastructure.yaml` content edit itself beyond
the existing `test_parity_index.py`/`test_parity_ledger_schema.py` regression coverage — the
`INFRA-181` change is a data/prose update (refreshed `v2_evidence`/date), not new logic, and
`INFRA-181` is `priority: P2` (not P0), so no dedicated `test_path` is a hard requirement per this
project's Authoritative Mechanics Rule. If Implement chooses to fill in `INFRA-181`'s
currently-null `test_path` with the new `tests/static/test_docs_build_content_scope.py`
path, that alone satisfies traceability without a separate new test.

## Scoped Pytest Commands

```
# Primary regression scope: the static guard directory (new test lands here)
.venv/bin/python3 -m pytest tests/static/ -v

# Secondary scope: parity-ledger tooling regression, only if INFRA-181's YAML entry is edited
.venv/bin/python3 -m pytest tests/tools/test_parity_ledger_schema.py tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py -v
```

Never `pytest tests/` — both commands above are scoped to the two domains this ticket actually
touches (docs-build static guards; parity-ledger tooling), per this project's Testing Rule.

## Anti-Drift Test Guards

- **Test 2 (`test_docs_preset_unchanged_and_present`) is itself the primary anti-drift guard** for
  this ticket: it fails loudly if the `docs` preset itself gets accidentally removed or its
  `showLastUpdateTime`/`showLastUpdateAuthor` flipped while deleting the three sibling plugin
  blocks — the single most realistic scope-creep/silent-regression risk for this file.
- **Test 3 (`test_docs_exclude_list_covers_approved_exclusions_only`)** guards the core correctness
  of the expanded scope in both directions: an under-broad edit (forgetting to add `archive/**`)
  would leave the OOM risk unaddressed; an over-broad edit (accidentally excluding an approved
  folder like `mechanics/**`) would silently break the public site's own stated purpose. Confirmed
  during Investigate that no existing test in `tests/` references `docusaurus.config.js` at all
  (`grep -rl "docusaurus.config" tests/` returns nothing except an unrelated fixture file), so this
  closes a genuine, previously-uncovered gap.
- **`test_parity_index.py`'s entry_health group** guards against the adjacent-system risk of a
  parity-ledger edit silently breaking the entry's own schema validity (e.g. leaving `verified`
  status with a null `v2_evidence`) while updating `INFRA-181`'s evidence text.
