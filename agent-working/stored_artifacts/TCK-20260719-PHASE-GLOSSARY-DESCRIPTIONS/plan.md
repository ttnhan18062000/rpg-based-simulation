---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS
artifact_type: plan
tags: [dashboard, observability, workflows]
---

# Implementation Plan — TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS

## Summary

Extend `tools/glossary_registry.py`'s `GLOSSARY_CATEGORIES` with an 8th category, `phase`, and
register one freshly-authored, one-sentence description per distinct literal string in
`tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_PHASES` (21 deduplicated strings across all 4
workflows — full coverage, not just `implement-ticket`'s 11). This is a registry population, not a
4th `ingest.py` merge source like Layer/Agent: `DashboardCache.get_glossary()` needs **zero** code
changes because its first merge loop (`load_glossary_registry()`, i.e. `glossary_registry.load_registry()`,
`ingest.py:855`) already reads every row of `glossary_registry.jsonl` generically and passes
`category` straight through — confirmed by direct read, not assumed. Wire
`StatsView.tsx`'s `row.phase` cell (the ticket's primary target) and, as a deliberate in-scope
extension authorized by the ticket's own Out-of-Scope carve-out for "a real, analogous,
non-speculative gap," `ReplayTimelineView.tsx`'s two plain `entry.phase` renders and one plain
`entry.agent` render — all three sit on lines that already have the `GlossaryTooltip`/`glossary`
plumbing in scope, one line even already using it for `entry.status`. Update the contract doc's
`get_glossary()` paragraph in place, and correct a specific error in `investigation.md`'s Parity
Ledger Overlap finding: this ticket does need a new `INFRA-NNN` entry, per direct evidence gathered
below (Anti-Drift Notes).

## Steps

### Step 1 — Extend `GLOSSARY_CATEGORIES` with `"phase"` (8th category)
**Files:** `tools/glossary_registry.py`, `tests/tools/test_glossary_registry.py`
**Change:** Add `"phase"` to the `GLOSSARY_CATEGORIES` set literal (`tools/glossary_registry.py:49-57`),
making it `{"ticket-status", "run-status", "reason-code", "event-status", "tier", "priority", "type",
"phase"}` (8 members). Update `test_glossary_categories_is_the_expected_fixed_set`
(`tests/tools/test_glossary_registry.py:163-172`) to assert this new 8-element set with the same
bare `==` strictness it already uses — do not loosen it to `<=`/`.issuperset()`. Add a new test
`test_add_term_accepts_phase_category` verifying `add_term(term, "phase", description)` succeeds now
that the category exists, mirroring the existing per-category acceptance shape implicit in
`test_add_term_appends_entry_and_returns_it`.
**Do NOT touch:** the other 7 existing category members; `add_term()`'s validation branching logic
itself (no new parameters, no canonical-form check — phase terms are byte-exact fixed strings, same
as every other category); `tools/tag_registry.py`, `tools/layer_registry.py` (separate registries).
**Verify:** `test_glossary_categories_is_the_expected_fixed_set` (updated), `test_add_term_accepts_phase_category` (new).

### Step 2 — Register all 21 phase terms via the CLI
**Files:** `docs/guidelines/glossary_registry.jsonl` (data file — populated via 21 CLI invocations,
never hand-edited JSON)
**Change:** Run, once per term, `python3 tools/glossary_registry.py add "<term>" --category phase
--description "<description>"`. Use this exact term text (byte-identical to `vocabulary.py`,
case-sensitive, register `"Review"` never `"Architecture Review"`) and description:

| Term | Description |
|---|---|
| `Scope` | Ticket-scoper agent creates the ticket file and staging artifacts, checking first for duplicate or conflicting work already underway. |
| `Investigate` | Digs into the affected code, docs, and prior tickets for a ticket or proposed concern, producing the findings later phases build on. |
| `Plan` | Planner agent turns investigation findings into an ordered, narrow, independently-verifiable implementation plan with explicit scope guards. |
| `Review` | Architecture-reviewer agent checks a proposed implementation plan against durable-state, API-boundary, and Mechanics Bible rules before any code is written. |
| `Implement` | Implementer agent writes the code changes described in the plan, or, in implement-epic, delegates one full implement-ticket run per child ticket. |
| `Architecture-Verify` | Architecture-reviewer agent re-checks the real code diff after implementation, judging only findings flagged by its own static pre-check rather than re-reviewing the whole plan. |
| `Test` | Test-scoper agent maps the changed files to relevant existing tests, runs a scoped test command, and reports pass/fail results. |
| `Parity` | Parity-updater agent updates the relevant docs/parity_ledger entry so documentation and source code stay in sync after a behavior change. |
| `Security-Review` | Security-reviewer agent checks changed code for injection, unsafe deserialization, secrets, and raw-domain-model exposure; runs only when the ticket is tagged security-relevant. |
| `Verify` | Confirms the work is genuinely complete against its own Definition-of-Done conditions — a 13-condition check in implement-ticket, or a regression/anchor-coverage check in simq-audit. |
| `Finalize` | Moves the ticket to tickets/done/, appends the working log, migrates staging artifacts to storage, and cleans up any leftover run data. |
| `Comprehend` | Reads a natural-language proposal document and extracts its discrete concerns before any investigation begins. |
| `Structure` | Synthesis agent turns per-concern investigation results into properly-formed ticket fields, including real file paths and concrete acceptance criteria. |
| `Write` | Writes the finished TCK-YYYYMMDD ticket file(s) into the target output folder. |
| `Link` | Appends newly-created ticket IDs to a parent epic ticket's Related Tickets section, when an epic_id was given. |
| `Recalibrate` | Re-runs the SimQ calibration corpus and captures regressions, pass/fail counts, and any uncovered anchor keys or parity ledger candidates. |
| `Classify Drift` | Classifies each flagged calibration item as expected drift, a real regression, a design-acknowledgment decision, or no action needed. |
| `Update Anchors` | Updates grade-anchor baselines for items classified as expected drift only, then re-runs a targeted test subset to confirm the update holds. |
| `Sync Docs` | Updates the SimQ evaluation and integration docs so they stay consistent with the refreshed calibration results. |
| `Parity Check` | Updates docs/parity_ledger entries flagged by the SimQ audit gap scan, using the same verified/divergent/missing rules as implement-ticket's own Parity phase. |
| `Report` | Reports the audit's final verdict, either suggesting a no-regression chore commit or handing off a pre-seeded ticket for a real regression or design-acknowledgment decision. |

**Do NOT touch:** `tools/agent-monitoring/vocabulary.py` (read-only reference — Out of Scope); any
of the other 35 pre-existing registry rows; term casing/spacing (must be byte-exact:
`Architecture-Verify` hyphenated, `Classify Drift`/`Parity Check`/`Sync Docs`/`Update Anchors`
space-separated title case).
**Depends on:** Step 1 (category must exist or `add_term()` raises `ValueError`).
**Verify:** covered by Step 3's coverage test (this step itself has no dedicated test — it is data
population).

### Step 3 — Add real-corpus coverage guard test
**Files:** `tests/tools/test_glossary_registry.py`
**Change:** Add `test_real_seeded_registry_covers_every_workflow_phase` — imports `WORKFLOW_PHASES`
directly from `tools/agent-monitoring/vocabulary.py` (never a hardcoded copy of the 21 strings),
computes the deduplicated union across all 4 workflows, and asserts every one of those strings has a
real entry in the live `glossary_registry.jsonl` with `category == "phase"` and a non-blank
`description`. This is the phase-domain equivalent of the existing
`test_real_seeded_registry_covers_every_canonical_ticket_field_value`.
**Do NOT touch:** `WORKFLOW_PHASES` itself; the other existing real-corpus tests in the file
(`test_real_seeded_registry_every_entry_has_non_blank_description`,
`test_real_seeded_registry_every_entry_has_valid_category` — must keep passing unmodified).
**Depends on:** Step 2 (fails until all 21 terms are actually registered).
**Verify:** `test_real_seeded_registry_covers_every_workflow_phase` passing against the live registry.

### Step 4 — Add backend integration test for the `/api/glossary` phase terms
**Files:** `tests/tools/test_agent_ops_dashboard_glossary.py`
**Change:** Add `test_glossary_route_includes_phase_terms` — verifies `GET /api/glossary` (via
`DashboardCache.get_glossary()` / the FastAPI route) returns entries for a representative phase term
(e.g. `"Review"`, `"Architecture-Verify"`) under `category == "phase"`. Bump
`test_glossary_against_real_seeded_registries`'s `len(glossary.terms) >= 48` floor upward (e.g. to
`>= 69`) to reflect the real growth from the 21 new phase terms — keep it a `>=` lower bound per its
own established convention, do not weaken it to `==` or tighten it to the exact real total.
**Do NOT touch:** `DashboardCache.get_glossary()` in `ingest.py` — confirmed by direct read
(`ingest.py:855`, `load_glossary_registry(self._repo_root).items()`, which is
`glossary_registry.load_registry` aliased at `ingest.py:50`) that it reads every row of
`glossary_registry.jsonl` generically and constructs `GlossaryEntry(term=entry["term"],
category=entry["category"], description=entry["description"])` with no category allowlist — `phase`
rows flow through automatically with **zero** code change required. Also do NOT touch
`test_glossary_route_never_returns_raw_dict_shape` (untouched architecture guard).
**Depends on:** Step 2 (real registry data must exist for the assertions to be meaningful).
**Verify:** `test_glossary_route_includes_phase_terms` (new), `test_glossary_against_real_seeded_registries` (bumped floor).

### Step 5 — Wire `StatsView.tsx`'s `row.phase` cell
**Files:** `dashboard-frontend/src/views/StatsView.tsx`
**Change:** At line 285, replace the plain `<td className="py-1 pr-3">{row.phase}</td>` with:
```tsx
<td className="py-1 pr-3">
  <GlossaryTooltip term={row.phase} glossary={glossary}>
    {row.phase}
  </GlossaryTooltip>
</td>
```
Byte-identical shape to the Top Agents `row.agent` cell already wired at lines 238-240.
**Do NOT touch:** the already-wired `ok`/`failed`/`blocked`/`skipped` header cells (lines 260-279);
`phaseStatusRows()` (lines 78-90); the Duration/Cost-Proxy outlier tables; the Top Agents table
itself.
**Depends on:** none functionally (frontend component tests mock the glossary fetch), but should
land after Step 2 if a live/manual browser check is done, so real descriptions show.
**Verify:** `renders a hover description for a phase name in the Phase Status Distribution table`
(new), `renders a Phase Status Distribution row plainly, with no hint icon, when the glossary has no
entry for that phase` (new) — both in `StatsView.test.tsx`.

### Step 6 — Wire `ReplayTimelineView.tsx`'s phase/agent gap
**Files:** `dashboard-frontend/src/views/ReplayTimelineView.tsx`
**Change:** Two wirings, both using the already-imported `GlossaryTooltip` and the component's
existing `glossary` (from `useGlossary()`):
- Line 99 (phase-timeline button strip), inside the `<button>`:
  ```tsx
  #{entry.seq}{' '}
  <GlossaryTooltip term={entry.phase ?? null} glossary={glossary}>
    {entry.phase ?? '—'}
  </GlossaryTooltip>
  ```
- Line 108 (detail-area header): wrap both `entry.phase ?? '—'` and `entry.agent ?? '—'` the same
  way, leaving the existing `<GlossaryTooltip term={entry.status} ...>` on that same line untouched:
  ```tsx
  #{entry.seq}{' '}
  <GlossaryTooltip term={entry.phase ?? null} glossary={glossary}>
    {entry.phase ?? '—'}
  </GlossaryTooltip>{' '}
  ·{' '}
  <GlossaryTooltip term={entry.agent ?? null} glossary={glossary}>
    {entry.agent ?? '—'}
  </GlossaryTooltip>{' '}
  ·{' '}
  <GlossaryTooltip term={entry.status} glossary={glossary}>
    {entry.status}
  </GlossaryTooltip>
  ```
`GlossaryTooltip` itself renders a `<span>` wrapper (see `GlossaryTooltip.tsx:35-38`), so nesting it
inside a `<button>` (line 99) is a valid, non-interactive child — no `Tooltip.Trigger asChild`
single-child conflict.
**Do NOT touch:** `entry.summary` rendering; `ENTRY_STATUS_CLASS` mapping; `PlaybackScrubber`; the
file-touch list rendered below the detail header.
**Depends on:** none (independent of backend steps and of Step 5).
**Verify:** new hint-icon-present/absent test pairs in `ReplayTimelineView.test.tsx` for phase (both
the button-strip and detail-header locations) and agent (detail-header location only) — same shape
as Step 5's StatsView pair.

### Step 7 — Update the glossary contract doc
**Files:** `docs/observability/agent_ops_dashboard_contract.md`
**Change:** Extend the existing `get_glossary()` paragraph (lines ~102-121) in place — same
convention already used for the Layer and Agent additions, not a new section:
- In the parenthetical listing the registry's own categories (line 108), add `phase` to the list:
  `(ticket-status/tier/priority/type/run-status/reason-code/event-status/phase terms)`.
- After the parenthetical, add one sentence noting `phase` covers all 21 deduplicated
  `WORKFLOW_PHASES` strings across `implement-ticket`/`create-tickets`/`implement-epic`/`simq-audit`,
  sourced from `glossary_registry.jsonl` directly (not a 4th `ingest.py` merge source like Layer/Agent).
- Update the stale count sentence (line 120: "35 glossary terms, 19 layer names, 13 agent names, all
  verified disjoint — 67 total") to the real post-registration counts. Confirm the exact real total
  via `python3 tools/glossary_registry.py list | wc -l` (or equivalent) after Step 2 completes —
  expected `56 glossary terms (35 + 21 phase), 19 layer names, 13 agent names ... 88 total`, but do
  not hardcode from this plan without confirming live.
**Do NOT touch:** other sections of the doc (API route table, Ingest/cache section, etc.) unless
they independently cite the stale `67 total` figure — check and update those too if found, but do
not restructure the doc.
**Depends on:** Step 2 (needs the real final count to be accurate).
**Verify:** no dedicated automated test; visually confirm the doc's prose and figures are accurate
post-registration (doc-only step, consistent with how the Layer/Agent doc updates were verified in
prior sibling tickets).

## Scope Guards

- Do **not** modify `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` sets
  — this ticket only reads and documents existing phase names, never adds/removes one (ticket's
  explicit Out of Scope).
- Do **not** register descriptions for phase names not present in `WORKFLOW_PHASES` — those already
  degrade gracefully (no tooltip), matching every other unmatched glossary lookup (ticket's explicit
  Out of Scope).
- Do **not** add a 4th `ingest.py` merge source (a `_load_phase_descriptions()`-shaped function with
  its own `if term in terms: continue` shadow guard) — `phase` goes into `glossary_registry.py`'s own
  registry via `add_term()`, exactly like the original 7 categories, not a fourth Layer/Agent-style
  merge loop. `get_glossary()` needs zero code changes (see Step 4's Do NOT touch).
- Do **not** touch any dashboard view's phase/agent rendering other than `StatsView.tsx`'s Phase
  Status Distribution table (Step 5) and `ReplayTimelineView.tsx`'s two confirmed-real gaps (Step 6)
  — no speculative extension to any other view.
- Do **not** write two separate glossary entries for `Investigate`, `Verify`, or `Implement` (each
  recurs across more than one workflow) — one entry per literal string, generalized to read correctly
  in every workflow it appears in, matching the registry's own documented `DONE` precedent.
- Do **not** weaken `test_glossary_categories_is_the_expected_fixed_set`'s exact-set `==` assertion,
  or `test_glossary_against_real_seeded_registries`'s `>=` lower-bound assertion (in either direction)
  — update the literal expected values, keep the strictness/looseness shape identical.
- Do **not** hand-edit `docs/guidelines/glossary_registry.jsonl` directly — always go through the
  `add_term()` CLI so `added_date`/append-only invariants are preserved consistently with every other
  entry in the file.

## Dependency Map

- Step 1 → Step 2 (category must exist before any `phase`-category term can be registered).
- Step 2 → Step 3, Step 4, Step 7 (all three need the real registered data to assert against or cite).
- Step 3 and Step 4 are independent of each other (both depend only on Step 2) and can be done in
  either order.
- Step 5 and Step 6 are independent of the backend steps (1-4, 7) and of each other — frontend
  component tests mock the glossary fetch, so they do not require the real registry to exist first.
  A live/manual browser verification of Step 5/6, however, is more meaningful after Step 2 has run.
- Step 7 should be done last among the backend steps since its count sentence depends on the final
  real total.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `GET /api/glossary` includes a real, accurate one-sentence description for every distinct phase string in `WORKFLOW_PHASES` | Steps 1, 2, 3, 4 | `test_real_seeded_registry_covers_every_workflow_phase`, `test_glossary_route_includes_phase_terms` |
| Hovering a phase name in the Stats view's Phase Status Distribution table shows its description, live-verified via headless browser | Step 5 (built on Steps 1-2) | `renders a hover description for a phase name in the Phase Status Distribution table`; live-verified manually per session discipline |
| The `Review`/`Architecture Review` naming mismatch is resolved correctly (literal `Review` registered) | Step 2 | `test_real_seeded_registry_covers_every_workflow_phase` (asserts `Review` specifically, since it's a `WORKFLOW_PHASES` member) |
| All pre-existing glossary/Stats-view tests still pass | Steps 1, 3, 4, 5 (regression preservation) | Full scoped pytest + frontend test/build/typecheck trio (see Scoped Pytest Commands in test_plan.md) |
| (Plan-added, authorized by ticket's Out-of-Scope carve-out for a real, non-speculative analogous gap) `ReplayTimelineView.tsx`'s `phase`/`agent` plain renders get the same tooltip treatment | Step 6 | New hint-icon-present/absent tests in `ReplayTimelineView.test.tsx` |

## Anti-Drift Notes

- **Byte-exact casing is load-bearing.** `glossary_registry.py` has no canonical-form normalization
  by design. A typo in Step 2 (e.g. `"architecture-verify"` or `"Architecture Verify"` instead of
  `"Architecture-Verify"`) registers a dead term that never matches a real
  `phase_status_distribution`/timeline `entry.phase` key and silently never shows a tooltip — Step 3's
  `test_real_seeded_registry_covers_every_workflow_phase` is the only automated guard against this,
  since it imports `WORKFLOW_PHASES` directly rather than re-deriving the string list.
- **`Review` vs `Architecture Review`.** `docs/ai/ticket-lifecycle.md:210`'s section heading is
  `### Architecture Review`, but its own body text (`docs/ai/ticket-lifecycle.md:221`, "The workflow
  resumes from the Review phase") and `vocabulary.py:22`'s literal set member are both `Review`. Step
  2 registers `Review`, never `Architecture Review` — confirmed correct by direct read of both files,
  not assumed.
- **`Parity` and `Parity Check` are two distinct literal strings, not one term with two spellings** —
  `Parity` belongs to `implement-ticket` (the `parity-updater` agent's ledger-sync phase), `Parity
  Check` belongs to `simq-audit` (a related but separately-named phase in that workflow's pipeline,
  per `simq-audit/SKILL.md`'s Pipeline step 5). Step 2 registers both, with distinct descriptions.
- **Zero code change required in `ingest.py`, confirmed by direct read, not inferred.**
  `DashboardCache.get_glossary()`'s first merge source (`ingest.py:855`) calls
  `load_glossary_registry(self._repo_root).items()`, which is literally
  `glossary_registry.load_registry` (aliased at `ingest.py:50`) — this function has no category
  filter; it returns every row in `glossary_registry.jsonl` regardless of category, and
  `GlossaryEntry(category=entry["category"], ...)` passes whatever category string is on that row
  straight through. `phase`-category rows added by Step 2 will appear in `GET /api/glossary`'s
  response automatically the moment they're registered — no Step is needed in `ingest.py` itself.
  This directly confirms (does not merely assume) the ticket's own Scope-section framing that this is
  a registry-population change, not a 4th merge source.
- **Parity Ledger correction — `investigation.md`'s "None. ... No parity ledger entry needs a
  status/v2_evidence update" finding is incomplete and should NOT be treated as license to skip the
  Parity phase.** Direct evidence gathered during planning: `TCK-20260719-AGENT-ROLE-GLOSSARY` (this
  ticket's own cited precedent for "no ledger edit needed") skipped the Parity phase only because it
  was implemented and its ticket written *retroactively*, after a background execution context
  stalled three times — its own Implementation Notes say so explicitly — not because of any
  deliberate "dashboard tooling never gets a parity entry" rule. By contrast, the two siblings that
  went through the Parity phase normally — `TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE` (`INFRA-286`)
  and `TCK-20260719-LIVE-PHASE-AGENT-LABEL` (`INFRA-281`) — both received a new `INFRA-NNN` entry,
  despite both entries' own `support_boundary` text using the same "Agent-orchestration/
  monitoring-pipeline tooling only -- no simulation behavior is involved" framing this ticket would
  also use. This ticket's `files_changed` will include `dashboard-frontend/src/views/StatsView.tsx`
  (Step 5) and `dashboard-frontend/src/views/ReplayTimelineView.tsx` (Step 6) — both literal `src/`
  path components — so `implement-ticket.js`'s Parity-phase static pre-check
  (`expected_subsystems_for_files`) will flag an expected `infrastructure` subsystem touch and the
  full `parity-updater` agent call will run (it is not skip-eligible under the "no `src/` path and
  `behavior_changed` false" rule). The Parity phase should add a new entry (`INFRA-287`, the next
  available number after `INFRA-286` at the time this plan was written — confirm the actual next-free
  number at Parity time) documenting: `GLOSSARY_CATEGORIES` extended to 8 with `phase`, 21 phase
  terms registered, `StatsView.tsx` `row.phase` wiring, and `ReplayTimelineView.tsx` `phase`/`agent`
  wiring — `status: verified`, citing real `file:line` `v2_evidence` post-implementation and the new
  test names from Steps 1-6 as `test_path`.
- **`StatsView.test.tsx`'s `never hardcodes a glossary description string in its own source` guard
  must keep passing unmodified** after Step 5 — it proves the new phase-cell wiring reads its
  description from the fetched `glossary` object, never a literal string embedded in `StatsView.tsx`.
- **`test_glossary_route_never_returns_raw_dict_shape` is untouched** — its continued pass after Step
  4 is required evidence the new phase entries don't leak an untyped shape at the API boundary.

## Deviations

- **Step 6 implementation note, not a plan change**: adding new `it()`s to
  `ReplayTimelineView.test.tsx` that vary the mocked `/api/glossary` response (needed to prove the
  hint-icon-present/absent behavior for `entry.phase`/`entry.agent`) surfaced a real pre-existing
  hazard the plan didn't call out: `useGlossary()`'s module-level `_glossaryPromise` cache persists
  across every `it()` in a test *file*, not just within one `describe` block. A naive file-wide
  `afterEach(_resetGlossaryCacheForTests)` (the shape used in `StatsView.test.tsx`) breaks the
  pre-existing `scrub/playback never fetches` describe block's `fetches the timeline exactly once`
  assertion, because forcing a fresh glossary fetch on every test adds a second `fetch()` call that
  test never expected. Fix: scoped the cache-reset `beforeEach`/`afterEach` pair to only the new
  `ReplayTimelineView — glossary tooltip wiring` describe block, leaving every pre-existing describe
  block's fetch-count assumptions untouched. No plan step or file list changed — this is a
  test-authoring detail within Step 6's existing scope, documented here per the "never silently
  deviate" rule.
- Also updated `tools/glossary_registry.py`'s own module docstring (lines ~26-28, the prose listing
  of `GLOSSARY_CATEGORIES`) to include `phase`, beyond the plan's literal Step 1 instruction (which
  named only the set literal and the test file). Not doing so would leave the docstring's own
  category listing stale immediately after the change it documents; the plan's Step 1 "Do NOT touch"
  list did not prohibit this and no other constraint conflicts with it.
