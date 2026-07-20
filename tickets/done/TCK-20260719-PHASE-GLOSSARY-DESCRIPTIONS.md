---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS
phase: done
date: 2026-07-19
tags: [dashboard, observability, workflows]
---

# TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS

## Title
Add workflow-phase glossary descriptions, mirroring the existing agent-role glossary

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Direct user follow-up after being shown the difference between `phase` and `agent` in
agent-monitoring data: "Add tooltips descriptions for the phases, similar to agents." The dashboard
already has agent-role hover tooltips (`TCK-20260719-AGENT-ROLE-GLOSSARY`) but no equivalent for
phase names — confirmed via direct read of `dashboard-frontend/src/views/StatsView.tsx`'s new Phase
Status Distribution table (added today by `TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE`): the
`ok`/`failed`/`blocked`/`skipped` column headers already have `GlossaryTooltip` wrapping, but the
`row.phase` cell (Scope, Investigate, Plan, etc.) is plain text — the exact same gap the Agent
column had before `TCK-20260719-AGENT-ROLE-GLOSSARY` fixed it.

## Scope
- **This is real content authorship, not pure extraction/reuse** — unlike the Agent merge (which
  reused `.claude/agents/*.md`'s existing one-sentence `description:` frontmatter verbatim) or the
  Layer merge (which reused `layer_registry.jsonl`'s existing `note` field), no per-phase
  one-sentence description exists anywhere in this repo today. `docs/ai/ticket-lifecycle.md` has
  authoritative multi-paragraph detail per `implement-ticket` phase (Scope through Finalize),
  and `.claude/skills/simq-audit/SKILL.md` has authoritative detail per `simq-audit` phase
  (Recalibrate, Classify Drift, Update Anchors, Sync Docs, Parity Check, Verify, Report) — these
  are the sources to distill from, not invent independently, but each phase's final glossary
  description must be freshly composed (one sentence, in this registry's established style),
  not copy-pasted.
- Extend `tools/glossary_registry.py`'s `GLOSSARY_CATEGORIES` with a new `phase` category (the
  module's own docstring frames the current 7 categories as "not meant to grow openly," but that
  language describes accidental sprawl, not a deliberate, justified addition for a real, distinct
  enum-like domain this dashboard now renders — same judgment call already made once when Agent
  became a legitimate third merge source outside the original two-category scope).
- Register one entry per **distinct literal phase string** found in
  `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_PHASES` (the canonical source, already reused
  by `generate_retro.py`'s casing normalization and the dashboard's Phase Status Distribution table)
  — deduplicated across workflows, since some phase names recur (`Investigate`/`Verify`/`Implement`
  appear in more than one workflow's phase list). Where a phase name means something workflow-
  specific in different contexts, write one description general enough to read correctly in every
  workflow it appears in, matching this registry's own already-documented precedent for the same
  ambiguity ("`DONE` means... whether it is a ticket `## Status` value or a run `final_status`
  value — one entry, not two... pick whichever category is the term's most natural primary home").
- **Anti-drift hazard, confirmed during investigation**: `docs/ai/ticket-lifecycle.md`'s section
  heading for the `Review` phase is titled "### Architecture Review," but the doc's own body text
  ("The workflow resumes from the Review phase") and `vocabulary.py`'s literal value are both
  `Review` — use the literal `vocabulary.py` string as the registered term, never a doc section's
  more-descriptive heading text.
- Wire `dashboard-frontend/src/views/StatsView.tsx`'s Phase Status Distribution table's `row.phase`
  cell in `GlossaryTooltip`, matching exactly how `TCK-20260719-AGENT-ROLE-GLOSSARY` wired the Top
  Agents table's `Agent` column cell.
- Update `docs/observability/agent_ops_dashboard_contract.md`'s glossary section to describe this
  fourth registry category (following the same "extend the existing paragraph" convention used for
  the Layer and Agent additions, not a disconnected new section).
- New backend + frontend test coverage.

## Out of Scope
- Any change to `vocabulary.py`'s `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` sets themselves — this ticket
  only documents existing phase names, never adds/removes one.
- Descriptions for phase names not present in `WORKFLOW_PHASES` (e.g. any ad-hoc label a workflow
  might log outside its own declared phase set) — those already degrade gracefully (no tooltip),
  matching every other unmatched glossary lookup in this dashboard.
- Any dashboard view other than the Stats tab's Phase Status Distribution table — investigate
  whether `phase` renders as a plain label anywhere else in the dashboard (Replay Timeline shows
  phase names too) while implementing, but this ticket's primary target is the newly-added table;
  extend elsewhere only if a real, analogous gap is found, not speculatively.

## Acceptance Criteria
- [ ] `GET /api/glossary` includes a real, accurate one-sentence description for every distinct
      phase string in `vocabulary.py`'s `WORKFLOW_PHASES` (live-verified: term count grows by the
      real deduplicated phase count).
- [ ] Hovering a phase name in the Stats view's Phase Status Distribution table shows its
      description, live-verified via headless browser (matching this session's established
      live-verification discipline: kill stale `dashboard-serve` process, relaunch fresh, verify).
- [ ] The `Review`/`Architecture Review` naming mismatch is resolved correctly (registered term is
      the literal `Review`, not the doc heading's `Architecture Review`).
- [ ] All pre-existing glossary/Stats-view tests still pass.

## Related Tickets
- TCK-20260719-AGENT-ROLE-GLOSSARY (direct precedent this ticket mirrors)
- TCK-20260718-GLOSSARY-REGISTRY
- TCK-20260718-GLOSSARY-API
- TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND
- TCK-20260719-STATS-PHASE-OUTLIERS-EXPOSE (added the Phase Status Distribution table this ticket wires)
- TCK-20260719-PHASE-AGENT-CASE-FOLD (established `vocabulary.py`'s phase canonicalization this ticket reuses)

## Related Docs
- docs/ai/ticket-lifecycle.md (source material for implement-ticket phase descriptions)
- .claude/skills/simq-audit/SKILL.md (source material for simq-audit phase descriptions)
- .claude/skills/create-tickets/SKILL.md (source material for create-tickets phase descriptions)
- docs/observability/agent_ops_dashboard_contract.md
- docs/guidelines/glossary_registry.jsonl

## Related Stored Artifacts
None yet — to be created at Investigate/Plan.

## Related Code Areas
- tools/glossary_registry.py
- docs/guidelines/glossary_registry.jsonl
- tools/agent-monitoring/vocabulary.py (read-only reference — canonical phase list)
- src/api/agent_ops_dashboard/ingest.py (get_glossary())
- dashboard-frontend/src/views/StatsView.tsx
- tests/tools/test_glossary_registry.py
- tests/tools/test_agent_ops_dashboard_glossary.py
- dashboard-frontend/src/test/StatsView.test.tsx

## Assumptions / Open Questions
- Whether `create-tickets`'s `Comprehend`/`Structure`/`Write`/`Link` phases and `simq-audit`'s full
  phase set are in scope for this pass, or whether v1 should cover `implement-ticket`'s 11 phases
  only (the ones actually visible in today's live retro data) and treat the others as a natural,
  cheap follow-up given the registry pattern will already exist — a real judgment call for
  Investigate/Plan, not decided here. Recommendation: cover all of `WORKFLOW_PHASES` in one pass
  since the marginal cost per phase is low once the category/wiring exists, mirroring how the Agent
  merge covered all 13 real role files in one pass rather than staging it.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260719-PHASE-GLOSSARY-DESCRIPTIONS/plan.md`'s 7 steps, in order:

1. Added `"phase"` as an 8th member of `tools/glossary_registry.py::GLOSSARY_CATEGORIES` (also
   updated the module's own docstring listing, beyond the plan's literal instruction — see plan.md's
   Deviations section). Updated `test_glossary_categories_is_the_expected_fixed_set` to the new
   8-element set and added `test_add_term_accepts_phase_category`.
2. Registered all 21 deduplicated `WORKFLOW_PHASES` literals into
   `docs/guidelines/glossary_registry.jsonl` via 21 `python3 tools/glossary_registry.py add ...`
   CLI invocations, each with a freshly-composed one-sentence description. Registered the literal
   `Review` (not `Architecture Review`), and `Parity`/`Parity Check` as two distinct entries.
3. Added `test_real_seeded_registry_covers_every_workflow_phase` to
   `tests/tools/test_glossary_registry.py`, importing `WORKFLOW_PHASES` directly from
   `tools/agent-monitoring/vocabulary.py`.
4. Added `test_glossary_route_includes_phase_terms` to
   `tests/tools/test_agent_ops_dashboard_glossary.py` (asserts `Review`/`Architecture-Verify` come
   back as `category: "phase"` via the live `/api/glossary` route) and bumped
   `test_glossary_against_real_seeded_registries`'s floor from `>= 48` to `>= 69`. Confirmed
   `DashboardCache.get_glossary()` needed zero code change — the real live merge now returns 88
   total terms (56 glossary + 19 layer + 13 agent).
5. Wired `dashboard-frontend/src/views/StatsView.tsx`'s Phase Status Distribution `row.phase` cell
   in `GlossaryTooltip`, byte-identical shape to the Top Agents `row.agent` cell. Added two tests to
   `StatsView.test.tsx` (hint-icon present/absent for a phase name).
6. Wired `dashboard-frontend/src/views/ReplayTimelineView.tsx`'s `entry.phase` (button-strip line
   and detail-header line) and `entry.agent` (detail-header line) in `GlossaryTooltip`, matching the
   existing `entry.status` wiring on the same detail-header line. Added 4 new tests in
   `ReplayTimelineView.test.tsx` covering hint-icon present/absent for both locations. Discovered
   and fixed a real cross-test hazard along the way — see plan.md's Deviations section for why the
   cache-reset `beforeEach`/`afterEach` pair is scoped to only the new describe block.
7. Extended `docs/observability/agent_ops_dashboard_contract.md`'s existing `get_glossary()`
   paragraph in place (added `phase` to the category parenthetical, one sentence on its 21-term
   coverage and registry-population rationale, and corrected the stale "35/19/13, 67 total" sentence
   to the real live counts: 56/19/13, 88 total).

No change was needed to `src/api/agent_ops_dashboard/ingest.py` — `get_glossary()`'s first merge
source already reads every row of `glossary_registry.jsonl` generically with no category filter,
confirmed both during Plan and by the live 88-term count in Step 4.

## Test Summary
- `python3 -m pytest tests/tools/test_glossary_registry.py tests/tools/test_agent_ops_dashboard_glossary.py tests/tools/test_agent_ops_dashboard_stats.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -q` — 57 passed.
- `cd dashboard-frontend && npx vitest run` (full frontend suite) — 100 passed (11 files).
- `cd dashboard-frontend && npx tsc --noEmit` — clean.
- `cd dashboard-frontend && npm run build` — succeeded.

## Files Changed
- `tools/glossary_registry.py`
- `tests/tools/test_glossary_registry.py`
- `docs/guidelines/glossary_registry.jsonl`
- `tests/tools/test_agent_ops_dashboard_glossary.py`
- `dashboard-frontend/src/views/StatsView.tsx`
- `dashboard-frontend/src/test/StatsView.test.tsx`
- `dashboard-frontend/src/views/ReplayTimelineView.tsx`
- `dashboard-frontend/src/test/ReplayTimelineView.test.tsx`
- `docs/observability/agent_ops_dashboard_contract.md`

## Completion Summary
Added a `phase` glossary category (21 freshly-authored, byte-exact-keyed descriptions covering
every distinct `WORKFLOW_PHASES` literal across all 4 agent workflows) and wired hover tooltips for
phase names in the Stats view's Phase Status Distribution table and for phase/agent names in the
Replay Timeline view's button strip and detail header. `GET /api/glossary` required zero backend
code changes — only registry data. All pre-existing and new backend/frontend tests pass (57 backend,
100 frontend), typecheck and production build are clean, and the dashboard contract doc's
`get_glossary()` section and term-count figures were updated to match the real live registry
(56 glossary / 19 layer / 13 agent = 88 total terms).
