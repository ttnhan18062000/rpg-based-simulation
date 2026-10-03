---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD
artifact_type: plan
tags: [documentation, performance]
---

# Implementation Plan — TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD

## Summary

Structurally shrink the public Docusaurus build by removing the `tickets`, `artifacts`, and
`agent-monitoring` `@docusaurus/plugin-content-docs` instances entirely from
`website/docusaurus.config.js` (read in full at
`/home/u24desktop/Working/rpg-based-simulation/.claude/worktrees/docs-build-lastupdate-metadata-overhead/website/docusaurus.config.js`),
deleting their now-dead sidebar files and navbar/search-theme references, and expanding the
surviving `docs` preset's `exclude` list to drop `archive/**`, `plans/**`, `audits/**`, and
`optimization_audit_ledger.md`. This removes 5,384 of the corpus's 6,223 files
(`tickets/done` 1,688 + `stored_artifacts` 3,684 + `agent-monitoring/retro` 12, per
investigation.md's fresh 2026-08-24 count) plus `docs/archive`'s 448 files from the build, while
leaving the `docs` preset itself — and its `showLastUpdateTime`/`showLastUpdateAuthor: true`
settings — untouched, per the ticket's explicit Out of Scope. `website/src/pages/index.js` loses
its stale ticket/artifact count references. A new static-guard test file,
`tests/static/test_docs_build_content_scope.py`, encodes all 6 tests from test_plan.md so future
edits to this file cannot silently reintroduce a removed plugin, drop the `docs` preset, or
over/under-exclude the approved subset. `docs/parity_ledger/infrastructure.yaml`'s `INFRA-181`
entry is refreshed to match the new four-instance-to-one-instance reality. Because the direct
predecessor hotfix (`TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM`) already proved a merge-first
validation cycle burns a full CI round-trip discovering a fix was insufficient, this plan places a
**required** live `gh workflow run` (`workflow_dispatch`) of `Deploy Docs to GitHub Pages` against
this ticket's own branch as Step 10, positioned after all source/test changes are committed and
scoped pytest is green, but strictly before any PR is opened or merged.

**Cross-check finding surfaced while verifying the config file (see Fact-Verification note in Step
4 and Step 6):** the ticket's Scope prose lists only `Tickets`/`Artifacts`/`Agent Monitoring` as
the navbar items to remove, but `themeConfig.navbar.items` (config lines 82–88) has a **fifth**
item — `{ to: '/docs/archive/', label: 'Archive', position: 'left' }` (line 86) — and
`website/src/pages/index.js` has a matching `<a href="/docs/archive/">Archive</a>` link (line 28).
Once the `docs` preset excludes `archive/**` (Step 5), `/docs/archive/` stops existing as a route,
so both of these become dead links unless also removed. The ticket's own Acceptance Criteria
already require this outcome — "Deployed site's nav shows only `Docs`" and "no broken internal
links introduced by the new excludes" (both from the ticket's AC list) are unsatisfiable if the
`Archive` navbar item and homepage link survive. This plan therefore removes both alongside the
three explicitly-named items, citing the AC text as the basis rather than deciding it as
independent scope expansion.

## Steps

### Step 1 — Remove the three plugin-content-docs instances

**Files:** `website/docusaurus.config.js`

**Change:** Delete the entire `plugins: [...]` array contents (lines 14–48 as read), i.e. the
three `@docusaurus/plugin-content-docs` blocks with `id: 'tickets'` (lines 15–25, `path:
'../tickets/done'`), `id: 'artifacts'` (lines 26–36, `path: '../stored_artifacts'`), and `id:
'agent-monitoring'` (lines 37–47, `path: '../agent-monitoring/retro'`). Leave `plugins: []` (an
empty array) rather than deleting the `plugins` key itself — Docusaurus's config schema accepts an
empty `plugins` array and this keeps the config's top-level shape stable for any future addition.
Confirmed by direct read of the file (cited above) that these are the only three
`plugin-content-docs` instances outside the `docs` preset — the `docs` preset (Step 5) is a
different config surface (`presets[0][1].docs`, not `plugins[]`) and is not touched by this step.

**Do NOT touch:** The `presets` array (lines 61–77) or anything inside it — the `docs` preset's
`path`, `routeBasePath`, `exclude`, `sidebarPath`, `showLastUpdateTime`, `showLastUpdateAuthor` all
stay exactly as they are in this step (Step 5 handles the one permitted change, `exclude`, as a
separate step).

**Verify:** `test_tickets_artifacts_agent_monitoring_plugins_removed` (asserts none of `id:
'tickets'`, `id: 'artifacts'`, `id: 'agent-monitoring'` appear anywhere in the file).

---

### Step 2 — Delete the three now-unused sidebar files

**Files:** `website/sidebars-tickets.js`, `website/sidebars-artifacts.js`,
`website/sidebars-agent-monitoring.js`

**Change:** Delete all three files from disk (`rm website/sidebars-tickets.js
website/sidebars-artifacts.js website/sidebars-agent-monitoring.js`). These were referenced only
via `sidebarPath: require.resolve('./sidebars-*.js')` inside the three plugin blocks removed in
Step 1 — confirmed by direct read of `docusaurus.config.js`: no other `require.resolve` call in
the file references these three filenames (the surviving `docs` preset uses
`require.resolve('./sidebars.js')`, a distinct file, line 69, untouched).

**Do NOT touch:** `website/sidebars.js` (the `docs` preset's own sidebar — different filename, no
`-tickets`/`-artifacts`/`-agent-monitoring` suffix) and `website/sidebars-archive.js`. Investigation
found `sidebars-archive.js` exists but is **not referenced by any plugin or preset in
`docusaurus.config.js` at all** (dead config predating this ticket) — it is explicitly flagged in
investigation.md as "not this ticket's concern," so leave it in place; deleting it is unrelated
cleanup outside this ticket's scope.

**Verify:** `test_removed_sidebar_files_deleted` (asserts the three files no longer exist on disk).

---

### Step 3 — Trim the search-local theme's `docsRouteBasePath`

**Files:** `website/docusaurus.config.js`

**Change:** In the `@easyops-cn/docusaurus-search-local` theme config (lines 50–58), change line
55 from `docsRouteBasePath: ['docs', 'tickets', 'artifacts', 'agent-monitoring']` to
`docsRouteBasePath: ['docs']`. This is the same file, a different top-level key (`themes`, not
`plugins`) than Step 1 — cited directly from the read above, confirmed this is the only
`docsRouteBasePath` occurrence in the file (`grep -n docsRouteBasePath website/docusaurus.config.js`
returns exactly line 55). This directly addresses investigation.md's flagged concern that this
theme "indexes all four route bases, i.e. the same 6,200+-file corpus" — a likely larger memory
driver than the metadata setting the ticket originally targeted, per the Addendum's rationale for
folding the plugin removal into this ticket.

**Do NOT touch:** `hashed: false` and `indexBlog: false` on the same theme block (lines 54, 56) —
unrelated settings, no ticket scope covers them.

**Verify:** `test_navbar_and_search_theme_no_longer_reference_removed_routes` (asserts
`docsRouteBasePath` contains only `'docs'`).

---

### Step 4 — Remove the four now-dead navbar items

**Files:** `website/docusaurus.config.js`

**Change:** In `themeConfig.navbar.items` (lines 82–88), delete the `Tickets` (`to: '/tickets/'`),
`Artifacts` (`to: '/artifacts/'`), `Agent Monitoring` (`to: '/agent-monitoring/'`) entries — these
are the three explicitly named in the ticket's Scope and AC #3 ("navbar.items no longer links to
`/tickets/`, `/artifacts/`, `/agent-monitoring/`"). **Also delete the `Archive` entry** (`{ to:
'/docs/archive/', label: 'Archive', position: 'left' }`, line 86) — this item is not named in the
ticket's Scope prose, but is required by two of the ticket's own Acceptance Criteria: "Deployed
site's nav shows only `Docs`" (only satisfiable if `Archive` is also removed, since it's the only
other item that would remain) and "no broken internal links introduced by the new excludes" (once
Step 5 excludes `archive/**` from the `docs` preset, `/docs/archive/` stops resolving to a real
route, making this a dead link if left in place). After this step, `navbar.items` should contain
exactly one entry: `{ to: '/docs/', label: 'Docs', position: 'left' }` (line 83, unchanged).

**Do NOT touch:** `navbar.title` (line 81, `'RPG Simulation Docs'`) or the surviving `Docs` item's
`to`/`label`/`position` values.

**Verify:** `test_navbar_and_search_theme_no_longer_reference_removed_routes` (asserts no
`/tickets/`, `/artifacts/`, `/agent-monitoring/` entries remain). Note: this specific test, per
test_plan.md, does not assert on `/docs/archive/` — Step 9's manual review and Step 10's live-run
check are the verification path for the `Archive` item's removal (see Anti-Drift Notes).

---

### Step 5 — Expand the `docs` preset's `exclude` list

**Files:** `website/docusaurus.config.js`

**Change:** In the `docs` preset block (`presets[0][1].docs`, lines 65–72), change line 68 from
`exclude: ['superpowers/**', 'specs/**', 'parity_ledger/**', 'scenarios/**', 'entity/**']` to
`exclude: ['superpowers/**', 'specs/**', 'parity_ledger/**', 'scenarios/**', 'entity/**',
'archive/**', 'plans/**', 'audits/**', 'optimization_audit_ledger.md']` — keep all 5 pre-existing
entries, append the 4 new ones. Do not remove or reorder the pre-existing 5. Leave every other key
in this block (`path: '../docs'`, `routeBasePath: 'docs'`, `sidebarPath:
require.resolve('./sidebars.js')`, `showLastUpdateTime: true`, `showLastUpdateAuthor: true`, lines
66–71) byte-for-byte unchanged — this is the ticket's explicit Out of Scope boundary and the
single highest-value anti-drift guard in this plan (see Anti-Drift Notes).

**Do NOT touch:** `showLastUpdateTime`/`showLastUpdateAuthor` on this block (must stay `true`), and
do not exclude any of the approved-subset folder names: `agent-monitoring`, `ai`, `architecture`,
`cognition`, `combat`, `compliance`, `content`, `core`, `engine`, `event_ledger`, `guidelines`,
`guides`, `mechanics`, `observability`, `performance`, `simulation`, `simulation_quality`,
`strategy`, `systems`, `testing`, `visual_quality`, `world`.

**Architecture-review finding, resolved**: `docs/agent-monitoring/` (3 files — `README.md`,
`schema.md`, `codebase_health_history_schema.md`, all frontmattered `audience: developer`,
`layer: observability`) was initially unaccounted for by either the exclude list or the approved
list. Verified by reading all three files: they are schema/design reference documentation for the
monitoring system, the same category as `docs/observability/` (already approved-keep), not
agent-context historical data — distinct from the removed top-level `agent-monitoring` plugin
instance, which published `agent-monitoring/retro/` (generated retro-report data). Resolved by
adding `agent-monitoring` to the approved-keep list above, not to `exclude`. `docs/brainstorm/` (7
`.html` files, 0 `.md`/`.mdx`) is also not in either list — moot, since Docusaurus's `docs` preset
default `include` glob is `**/*.{md,mdx}` and does not pick up `.html` source files regardless of
`exclude` membership.

**Verify:** `test_docs_exclude_list_covers_approved_exclusions_only` (asserts the 4 new excludes
plus the 5 pre-existing ones are present, and none of the 21 approved-subset names appear in
`exclude`) and `test_docs_preset_unchanged_and_present` (asserts the `docs` block itself, and its
`showLastUpdateTime`/`showLastUpdateAuthor: true`, are unchanged).

---

### Step 6 — Update `website/src/pages/index.js`

**Files:** `website/src/pages/index.js`

**Change:** Read in full at
`/home/u24desktop/Working/rpg-based-simulation/.claude/worktrees/docs-build-lastupdate-metadata-overhead/website/src/pages/index.js`
(37 lines). Specifically:
- Line 4: change `const STATS = { docs: 255, tickets: 657, artifacts: 469 };` to `const STATS = {
  docs: 255 };` — drop the `tickets`/`artifacts` fields entirely. Do **not** invent a new `docs`
  count to reflect the post-exclude file total (investigation.md's fresh count of 839 `docs/`
  files predates the Step 5 excludes and this plan does not have a real post-exclude count to cite
  — recomputing it here would be an unverified/fabricated figure, which investigation.md's Anti-
  Drift Hazards explicitly warns against for the analogous build-memory-number case). The ticket's
  Scope item for this file only asks to "drop the now-nonexistent tickets/artifacts references,"
  not to refresh the docs count — leave `docs: 255` as-is.
- Line 12: change `{STATS.docs} documents · {STATS.tickets} closed tickets · {STATS.artifacts}
  artifact sets` to `{STATS.docs} documents` (drop the two now-undefined `STATS.tickets`/
  `STATS.artifacts` references — leaving them would throw `undefined` into the rendered string
  once the `STATS` object no longer has those keys).
- Lines 26–28 (the "Content Sections" `<ul>`): delete the `<li><a href="/tickets/">Tickets</a> —
  Closed ticket history ({STATS.tickets} tickets)</li>` and `<li><a href="/artifacts/">Artifacts</a>
  — Investigation, plan, and test_plan files per ticket</li>` list items (both reference removed
  routes). **Also delete** `<li><a href="/docs/archive/">Archive</a> — Historical docs and design
  specs</li>` (line 28) — same reasoning as Step 4's navbar `Archive` removal: once `archive/**` is
  excluded from the `docs` preset (Step 5), this link 404s. Line 25's `<li><a
  href="/docs/">Docs</a> — ...</li>` stays.

**Do NOT touch:** The "Quick Links — Authoritative Docs (P0)" list (lines 14–22, linking to
`docs/mechanics/*`) — none of those paths are affected by any exclude added in Step 5 (`mechanics`
is in the approved-keep subset), and the ticket's Scope for this file only names ticket/artifact
count references.

**Verify:** `test_homepage_no_longer_references_ticket_artifact_counts` (asserts the strings
"closed tickets" / "artifact sets" no longer appear in the file).

---

### Step 7 — Write the new static guard test file

**Files:** `tests/static/test_docs_build_content_scope.py` (new file)

**Change:** Create this file following the parse-not-execute precedent set by the sibling OOM
hotfix's `tests/static/test_deploy_docs_heap_limit.py` (cited in investigation.md's "Prior Work"
section as the direct structural precedent), adapted for a JS source file: read
`website/docusaurus.config.js` as raw text and use string/regex assertions, never
`require()`/`node -e` (confirmed in test_plan.md's "Context Constraint" section: the file cannot
be `require()`-d in this environment because `@easyops-cn/docusaurus-search-local` isn't
installed, and `website/node_modules/` does not exist in this worktree). Implement exactly the 6
tests specified in test_plan.md's "New Tests Required" section:
1. `test_tickets_artifacts_agent_monitoring_plugins_removed`
2. `test_docs_preset_unchanged_and_present`
3. `test_docs_exclude_list_covers_approved_exclusions_only`
4. `test_navbar_and_search_theme_no_longer_reference_removed_routes`
5. `test_removed_sidebar_files_deleted`
6. `test_homepage_no_longer_references_ticket_artifact_counts`

Each test's exact assertions are specified in test_plan.md — do not add, drop, or rename any of
the 6. Test 3 must assert both directions in one test (excludes present AND approved names absent)
per test_plan.md's explicit rationale ("a single test asserting both directions catches either an
over-broad or under-broad edit").

**Do NOT touch:** `tests/static/test_deploy_docs_heap_limit.py` or any other existing file in
`tests/static/` — this ticket does not touch `.github/workflows/deploy-docs.yml`, so that test
file's assertions are unaffected; it should simply be re-run (Step 9) to confirm no accidental
cross-file edit occurred, per test_plan.md's "Regression Surface" section.

**Verify:** All 6 tests pass against the Step 1–6 changes (run together with Step 9).

---

### Step 8 — Refresh `INFRA-181` in the parity ledger

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Entry `INFRA-181` (cited at
`/home/u24desktop/Working/rpg-based-simulation/.claude/worktrees/docs-build-lastupdate-metadata-overhead/docs/parity_ledger/infrastructure.yaml:1916-1932`)
currently reads: `text: 'Docusaurus 3 site scaffold at website/ with four plugin-content-docs
instances indexing docs/, tickets/done/, stored_artifacts/, docs/archive/. Makefile targets
docs-serve and docs-build available.'`, `v2_evidence: 'website/docusaurus.config.js +
website/package.json + Makefile (docs-serve, docs-build targets)'`, `test_path: null`. This text is
now factually wrong after Steps 1–5 (there is one `plugin-content-docs` instance, the `docs`
preset, not four; `docs/archive/` is excluded, not indexed). Per the project's Authoritative
Mechanics Rule ("If logic changes, update the corresponding doc AND the parity ledger entry ... in
the same session"), update:
- `text` → describe the single surviving `docs` preset instance (path `docs/`, with its exclude
  list covering superpowers/specs/parity_ledger/scenarios/entity/archive/plans/audits), noting the
  three removed instances are gone.
- `v2_evidence` → refresh to cite the current file state and today's date (2026-08-24 or the
  actual implementation date), keeping the same three file references
  (`website/docusaurus.config.js + website/package.json + Makefile`).
- `test_path` → fill in `tests/static/test_docs_build_content_scope.py` (currently `null`; not a
  hard requirement since `INFRA-181` is `priority: P2` not `P0`, but investigation.md recommends
  doing it "while touching this entry anyway," and Step 7 creates exactly the file to point at).

**Other writers to this resource:** `docs/parity_ledger/infrastructure.yaml` is a shared,
multi-entry YAML file. Other parity-ledger update workflows (the `parity-updater` agent role, and
any other in-flight ticket touching a *different* `INFRA-*` entry in this same file) also write to
it, but only ever rewrite their own entry's block — no other ticket or tool is known to touch
`INFRA-181` specifically (confirmed in investigation.md: "No other `infrastructure.yaml` entries
... reference `docusaurus.config.js` ... by name"). Per this project's Worktree & Branch Isolation
rule, this ticket runs in its own worktree/branch, so no concurrent session should be mutating this
same file unless another session is independently working `infrastructure.yaml` — if `git status`
at commit time shows this file already dirty from an unrelated source, treat it as the shared-file
race the project's CLAUDE.md describes and re-check before overwriting.

**Do NOT touch:** `status: verified` (this ticket doesn't change verification status), `priority:
P2`, `legacy_evidence: null`, `divergence_note: null`, `support_boundary`, or any other `INFRA-*`
entry in the file.

**Verify:** `tests/tools/test_parity_ledger_schema.py` and `tests/tools/test_parity_index.py`'s
`entry_health` group (confirms the edited entry stays schema-valid and doesn't leave `verified`
status with a null `v2_evidence`). If filling in `test_path` shifts
`tests/tools/test_parity_index_baseline.py`'s `missing_test_path_count` baseline, treat that as
expected drift requiring a baseline update in the same step, per this project's documented drift
pattern (test_plan.md's "Regression Surface" section and CLAUDE.md's CI Failure Triage precedent)
— not a bug to work around.

---

### Step 9 — Run scoped regression tests

**Files:** None changed; verification-only step.

**Change:** Run, in order:
```
.venv/bin/python3 -m pytest tests/static/ -v
.venv/bin/python3 -m pytest tests/tools/test_parity_ledger_schema.py tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py -v
```
Both commands are copied verbatim from test_plan.md's "Scoped Pytest Commands" section — do not
run the bare `pytest tests/` (project Testing Rule). All tests in both commands must pass,
including the 6 new tests from Step 7 and the pre-existing `test_deploy_docs_heap_limit.py` (must
stay green unchanged, confirming no accidental cross-file edit into `deploy-docs.yml`, which this
ticket does not touch).

**Do NOT touch:** Any test file's assertions to force a pass — if a test fails, the underlying
Step 1–8 change is wrong and must be fixed, not the test (project's Gate Integrity rule).

**Verify:** Both pytest commands report 0 failures.

---

### Step 10 — Live `workflow_dispatch` validation run (required, before any PR)

**Files:** None changed; this is a live CI action, not a code step.

**Sequencing (explicit, per architecture-review finding 2):** Step 10 runs **between Test (Step 9)
and Parity/Verify/Finalize** — the ticket must still be in `tickets/inprogress/`, not yet moved to
`tickets/done/`, when this step runs. If the live run fails (OOMs again, or any other failure), loop
back to Implement (fix the root cause, re-run Steps 1–9, then retry Step 10) — do **not** proceed to
Parity/Verify/Finalize on a failed Step 10, and do not treat a ticket already moved to
`tickets/done/`/`stored_artifacts/` as an acceptable place to discover a Step 10 failure. This is
the entire point of placing Step 10 here rather than after merge: the predecessor hotfix's
merge-first cycle meant discovering the failure only after the ticket was already closed and merged
to `main`, requiring a second ticket to fix it — Step 10's placement here is what prevents a repeat.

**Non-delegable, orchestrator-only (per architecture-review finding 3):** This step must be executed
directly by the orchestrating session's own tool calls (`gh workflow run`, `gh run watch`, log
review) — **never delegated to a further sub-agent**. It requires live judgment on a real
~16-minute CI run's log output (OOM-or-not, which warnings to report), not a boolean gate a
sub-agent could return a schema for, and per this project's Hard Rule on dispatched sub-agents: a
sub-agent that starts a `run_in_background`-equivalent poll and ends its turn before it completes
stalls the pipeline until manually detected. The orchestrator must poll this to completion within
its own turn.

**Change:** This step is **not optional and not a normal pipeline phase** — it is explicitly
authorized by the repo owner per the ticket's Scope ("Test via a live `workflow_dispatch` run ...
**before** opening/merging a PR") and directly addresses the predecessor hotfix's failure mode: its
own merge-first validation already burned one full CI cycle (~16 minutes) discovering the heap-limit
fix alone was insufficient, per investigation.md's "Prior Work" section. Sequence:
1. Ensure Steps 1–9 are committed to this ticket's branch (per this project's Worktree & Branch
   Isolation rule, in the current worktree/branch, not `main`).
2. Push the branch so the workflow can be dispatched against it: `git push -u origin
   <branch-name>` (branch, not yet a PR).
3. Trigger the workflow directly: `gh workflow run "Deploy Docs to GitHub Pages" --ref
   <branch-name>` (confirm the exact workflow name/file matches `.github/workflows/deploy-docs.yml`
   before running — investigation.md cites its numeric ID as `294250397`, but `gh workflow run`
   accepts either the display name or the file name; verify with `gh workflow list` first if
   unsure).
4. Poll to completion: `gh run list --workflow=deploy-docs.yml --limit 1` /
   `gh run watch <run-id>`, per this project's CI Failure Triage guidance (never assume success
   without checking; pull real logs on any failure, not just the job name).
5. Confirm the run's `Build` step does not OOM-abort (the specific failure mode this whole ticket
   exists to fix) and that all four job steps (Build → Configure Pages → Upload Pages artifact →
   Deploy to GitHub Pages) report success.
6. **This run deploys to the real production Pages site early**, per the ticket's own explicit
   acknowledgment ("the workflow's single `deploy` job always runs Build → Deploy regardless of
   trigger type") — this is a known, accepted, already-authorized side effect, not an error to
   avoid or route around.
7. While reviewing the run's Build log, grep for new `[WARNING]` dangling-link lines referencing
   `archive/`, `plans/`, or `audits/` paths from within the kept approved-subset docs (a link-scan
   investigation.md did not perform — see this plan's Anti-Drift Notes). `onBrokenLinks: 'warn'`
   means such warnings will not fail the build or block this step, but any found should be reported
   honestly in the ticket's Test Summary/Completion Summary rather than silently ignored, per the
   Definition of Done's "no known material gap is left unstated."

**Do NOT treat this step as satisfied by Step 9's local pytest pass alone** — Step 9 verifies the
config's static structure; only a real GitHub Actions run against the real corpus and real
`ubuntu-latest` runner exercises the actual memory behavior this ticket exists to fix.

**Do NOT open or merge a PR before this step completes successfully** — per the ticket's Scope
and AC #7 ("A live `workflow_dispatch` run ... completes successfully end-to-end ... before any PR
is opened/merged"), and the explicit lesson from the predecessor hotfix's merge-first cycle.

**Verify:** AC #7 and AC #8 directly (live run success; deployed nav/link check) — there is no
pytest test for this step; it is the live-CI verification path test_plan.md's Context Constraint
section explicitly calls out as unachievable via pytest.

## Scope Guards

Do not touch, under any step of this plan:
- `docs` preset's `showLastUpdateTime`/`showLastUpdateAuthor` values (must remain `true`) —
  explicit ticket Out of Scope.
- `.github/workflows/deploy-docs.yml`'s `NODE_OPTIONS: --max-old-space-size=8192` (the predecessor
  hotfix's fix) — explicit ticket Out of Scope ("already merged and stays as-is").
- The actual `tickets/done/`, `stored_artifacts/`, `agent-monitoring/retro/`, `docs/archive/`,
  `docs/plans/`, `docs/audits/` directories and their contents — only their presence in the Pages
  *build* changes; nothing is deleted or archived from the repository itself.
- `website/sidebars.js` (the `docs` preset's own sidebar) and `website/sidebars-archive.js` (dead
  config, pre-existing, unrelated to any plugin/preset in the current config — flagged by
  investigation.md as a latent inconsistency for a future ticket, not this one).
- Any retention/exclusion policy decision beyond the specific folders the repo owner already named
  (`archive/**`, `plans/**`, `audits/**`, `optimization_audit_ledger.md`) — do not extend the
  exclude list further on independent judgment.
- The `@easyops-cn/docusaurus-search-local` theme's `hashed`/`indexBlog` settings, or any further
  webpack-level tuning (parallelism, source maps) — explicit ticket Out of Scope.
- A paginated/index-only/recent-N-months public view of tickets or artifacts — explicit ticket Out
  of Scope, not a redesign.
- Any `INFRA-*` entry other than `INFRA-181` in `docs/parity_ledger/infrastructure.yaml`.
- Fabricating a "before/after" memory number anywhere (ticket text, test assertions, ledger
  `v2_evidence`, index.js `STATS.docs`) in place of an actual measurement — investigation.md could
  not produce one locally; only Step 10's live run produces real evidence.

## Dependency Map

- Steps 1–6 (all edits to `website/docusaurus.config.js` and `website/src/pages/index.js`) are
  independent of each other in principle (different keys/lines/files) but land in the same commit
  since they're all needed before Step 7's tests can pass — implement in the listed order for
  traceability, but no step blocks another within 1–6.
- Step 7 (write tests) can be authored at any point but should be run only after Steps 1–6 are in
  place, since its assertions describe the post-change file state.
- Step 8 (parity ledger) is independent of Steps 1–7 and can be done in parallel, but should land
  in the same commit/session per the Authoritative Mechanics Rule.
- Step 9 depends on Steps 1–8 all being complete (it is the regression gate over all of them).
- Step 10 depends on Step 9 passing and all changes being committed and pushed to this ticket's
  branch. It runs before Parity/Verify/Finalize (ticket stays in `tickets/inprogress/` until it
  passes) and before any PR — it is the final gate before either, per the ticket's explicit
  ordering requirement and architecture-review finding 2.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `docusaurus.config.js` no longer includes `tickets`/`artifacts`/`agent-monitoring` plugin instances | Step 1 | `test_tickets_artifacts_agent_monitoring_plugins_removed` |
| `sidebars-tickets.js`, `sidebars-artifacts.js`, `sidebars-agent-monitoring.js` removed | Step 2 | `test_removed_sidebar_files_deleted` |
| `navbar.items` no longer links to `/tickets/`, `/artifacts/`, `/agent-monitoring/` | Step 4 | `test_navbar_and_search_theme_no_longer_reference_removed_routes` |
| search-local theme's `docsRouteBasePath` only lists `'docs'` | Step 3 | `test_navbar_and_search_theme_no_longer_reference_removed_routes` |
| `docs` preset's `exclude` list additionally excludes `archive/**`, `plans/**`, `audits/**`, `optimization_audit_ledger.md`, keeping the approved subset; `showLastUpdateTime`/`showLastUpdateAuthor` unchanged | Step 5 | `test_docs_exclude_list_covers_approved_exclusions_only`, `test_docs_preset_unchanged_and_present` |
| `website/src/pages/index.js` no longer references ticket/artifact counts | Step 6 | `test_homepage_no_longer_references_ticket_artifact_counts` |
| Live `workflow_dispatch` run of `Deploy Docs to GitHub Pages` against this ticket's branch completes successfully end-to-end, before any PR is opened/merged | Step 10 | No pytest — live CI run observation (`gh run watch`) |
| Deployed site's nav shows only `Docs`; approved `docs/` subset still renders with working links (no broken internal links introduced by the new excludes) | Steps 4, 5, 6 (source changes), Step 10 (live confirmation) | `test_navbar_and_search_theme_no_longer_reference_removed_routes` (static) + Step 10's live log/link review |

## Anti-Drift Notes

- **Do not remove the `docs` preset itself.** It is the entire remaining public site after this
  ticket. The single highest-value guard against this is `test_docs_preset_unchanged_and_present`
  (Step 7, test 2) — it must fail loudly if an over-eager edit deletes the `docs` block along with
  the three sibling plugin blocks it sits next to in the same array-adjacent region of the file.
- **Do not over-exclude or under-exclude the `docs/` subset.** Under-excluding (forgetting
  `archive/**`, `plans/**`, `audits/**`, or `optimization_audit_ledger.md`) leaves the OOM risk
  unaddressed; over-excluding (accidentally matching an approved folder name, e.g. a careless glob
  like `'a*/**'` that would also catch `ai/**`) silently breaks the public site's stated purpose.
  `test_docs_exclude_list_covers_approved_exclusions_only` (Step 7, test 3) is the structural guard
  for both directions — use exact literal strings in the `exclude` array, not wildcard patterns
  broader than the four named ones.
- **Do not skip Step 10 or treat it as optional/deferrable to a later ticket.** This is the one
  step in this plan that is *not* a normal part of the pipeline (Implement/Test → Verify →
  Finalize) — it is an explicit repo-owner-authorized live production action required *before* PR
  creation specifically because the predecessor hotfix's merge-first approach already failed once
  in exactly this way (see investigation.md's "Prior Work"). Do not substitute Step 9's local
  pytest pass for it.
- **The `Archive` navbar item and homepage link removal (Steps 4 and 6) were not in the ticket's
  Scope prose by name** — they were derived during this plan's fact-verification pass from reading
  the actual `navbar.items` array and `index.js` content and cross-checking against the ticket's
  own AC text ("nav shows only `Docs`"; "no broken internal links introduced by the new excludes").
  If review disagrees this is in scope, flag it back rather than silently reverting — leaving them
  in place produces dead links post-Step-5 and directly contradicts those two ACs as literally
  written.
- **No full link-audit was performed** of cross-references *from* the approved-subset docs *into*
  `docs/archive/`, `docs/plans/`, or `docs/audits/` (e.g. a `mechanics/` doc linking to something
  in `archive/`). `onBrokenLinks: 'warn'` means such links will not fail the Step 10 live build, but
  they would render as dead links on the live site. Step 10 asks for a log grep as a best-effort
  check; if warnings are found referencing the newly-excluded paths, report them honestly in the
  ticket's Completion Summary as a known follow-up rather than silently absorbing or hiding them —
  fixing them is not required by this ticket's AC (which only requires "no broken internal links
  introduced by the new excludes" be *checked and reported*, not that a full remediation pass
  happens here) but their existence must not go unstated.
- **Do not fabricate a docs file count or a before/after memory number anywhere** — `STATS.docs:
  255` in `index.js` stays as-is (Step 6), and no v2_evidence/text update in Step 8 should assert a
  specific MB or file-count figure that wasn't actually measured. The only source of truth for the
  actual memory outcome is Step 10's live run.
- **`sidebars-archive.js` is intentionally left untouched** even though investigation.md flags it
  as dead config (not referenced by any plugin/preset today) — cleaning it up is unrelated scope
  creep for a future ticket, not this one.

## Deviations (recorded during Implement, 2026-08-24)

- **Step 8/9 interaction not anticipated at exact magnitude, but Plan already called it out
  correctly**: filling in `INFRA-181`'s `test_path` (previously `null`) shifted
  `tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`'s
  hardcoded `live_missing == 1335` assertion to `1334` (one fewer `verified`/`divergent` entry now
  missing a `test_path`). This is exactly the "expected drift requiring a baseline update in the
  same step" scenario Step 8 and the Anti-Drift Notes anticipated (matching this project's
  documented `missing_test_path_count` drift pattern). Updated the assertion from `1335` to `1334`
  and appended a changelog comment line (matching the file's existing per-ticket changelog-comment
  convention) attributing the shift to this ticket's `INFRA-181` edit. Re-ran the full scoped
  command afterward — all 55 tests pass. No other step deviated from the plan as written; Steps 1–7
  were implemented exactly as specified, including the `Archive` navbar/homepage-link removal
  called out in Steps 4 and 6.
