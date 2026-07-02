---
status: done
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E51-CHRONICLE
phase: done
date: 2026-06-19
tags: [chronicle-compiler, history, narrative-ledger, event-compression, epic, phase-5]
---

# TCK-20260619-E51-CHRONICLE

## Title
Epic 5.1 · History / Chronicle Compiler

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Zero code exists for event compression or chronicle generation. Only scattered event logs. No event→episode→milestone→era compression. Required for thousand-year-style simulation and for making completed runs legible to a human reader. Uses `NarrativeLedger` from Epic 3.2 as primary input.

Score: 8/10 · Effort: L · Source: `docs/plans/engine_future_epics_roadmap.md` § A

## Scope
- **Prerequisites:** TCK-20260619-E32-CAMPAIGN-RUNTIME (NarrativeLedger); TCK-20260619-E43-SOCIAL-MEMORY (social event feed)
- `ChronicleCompiler`: post-run pipeline reading `NarrativeLedger` and `simulation_events.jsonl`; groups events into named episodes by significance threshold
- Event significance scoring: severity + entity_reach + cascade_downstream_count; only events above threshold appear in chronicle
- Chronicle hierarchy: `Event → Incident (3–10 events) → Episode (5–20 incidents) → Era (campaign phase)`
- Named entities and events: significant NPCs, factions, locations acquire chronicle names ("The Fall of Iron Gate", "The Betrayal of Aldric")
- `Chronicle.md` output: human-readable narrative summary of a completed run, 1–5 pages
- REST:
  - `GET /api/v1/chronicle/{campaign_id}` — structured chronicle JSON
  - `GET /api/v1/chronicle/{campaign_id}/eras/{era_id}/summary` — narrative text for an era
- Child tickets: (a) significance scoring model, (b) event→incident→episode grouping, (c) named entity assignment, (d) Chronicle.md generation, (e) REST endpoints

## Out of Scope
- Generated prose narrative via LLM integration
- Player-facing history book UI
- Cross-campaign historical comparison

## Acceptance Criteria
- A completed 3-episode campaign produces a `Chronicle.md` that a reader with no prior context can understand as a coherent historical summary in under 5 minutes
- At least 3 named milestones appear in the chronicle
- Structured chronicle JSON queryable via REST

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (prerequisite)
- TCK-20260619-E43-SOCIAL-MEMORY (prerequisite)
- TCK-20260619-E53-FACTION-DIPLOMACY (unlocked: faction history feeds chronicles with wars/treaties)
- TCK-20260619-E62-CULTURE-DRIFT (unlocked: uses chronicle data for cultural drift)
- TCK-20260619-E51A-SIGNIFICANCE (child)
- TCK-20260619-E51B-GROUPER (child)
- TCK-20260619-E51C-NAMING (child)
- TCK-20260619-E51D-RENDERER (child)
- TCK-20260619-E51E-REST-API (child)

## Related Docs
- `docs/plans/engine_future_epics_roadmap.md` § A
- `docs/plans/long_term_development_roadmap.md` § Epic 5.1
- `docs/mechanics/05_world_evolution.md` (calamities, regional trauma, and ecology events are world-scale inputs to the chronicle; update to note ChronicleCompiler as their narrative consumer)
- `docs/simulation/domains/campaigns_contract.md` (update to document ChronicleCompiler as post-run step)
- `docs/parity_ledger/social_narrative.yaml` (narrative event compression entries — add as `verified`)
- `docs/parity_ledger/world_dynamics.yaml` (era/milestone entries if world-scale events feed chronicle)
- New doc: `docs/simulation/domains/chronicle_contract.md` (ChronicleCompiler pipeline, significance scoring formula, hierarchy definitions, Chronicle.md schema, REST endpoints)

## Related Stored Artifacts
- `staging_artifacts/TCK-20260619-E51-CHRONICLE/`

## Related Code Areas
- `src/domains/campaigns/schema.py:L43` (CampaignEvent — input to ChronicleCompiler)
- `src/observability/events.py:L54` (SimulationEvent — raw event source)
- `src/observability/reporting/` (artifact output pattern)

## Assumptions / Open Questions
- What constitutes a "significant event"? → Answered in investigation.md: BASE_SIGNIFICANCE dict + CHRONICLE_THRESHOLD=0.5
- How should "Chronicle names" be generated deterministically? → Use entity names from IdentityComponent + event type + tick (templates in E51C)

## Implementation Notes
Post-run pipeline (not tick-live). Runs after campaign completes. The most complex deliverable is the grouping algorithm — implement a simple threshold-based grouper first, then iterate. Chronicle.md is structured Markdown with YAML frontmatter for machine parsing.

After implementation: create `docs/simulation/domains/chronicle_contract.md` documenting significance scoring formula, hierarchy definitions, and Chronicle.md schema. Update `docs/parity_ledger/social_narrative.yaml` with chronicle entries. Run `make knowledge-index-update` after docs/ changes.

## Test Summary
- New file `tests/unit/chronicle/test_chronicle_compiler.py`:
  - `test_significance_scoring_ranks_death_above_harvesting()` — unit test with known events; assert entity_death.significance > harvesting.significance
  - `test_event_grouping_produces_incident_clusters()` — inject 15 related events; assert grouped into 2–4 incidents
  - `test_chronicle_hierarchy_event_incident_episode_era()` — assert output contains all four levels
- New file `tests/integration/scenarios/test_campaign_chronicle.py`:
  - `test_chronicle_md_contains_three_milestones()` — run 3-episode campaign; run ChronicleCompiler; assert ≥3 named milestones in `Chronicle.md`
  - `test_chronicle_readable_without_prior_context()` — human-readability check: assert all named entities have at least one description sentence
- New file `tests/api/test_chronicle_api.py`:
  - `test_chronicle_rest_endpoint_returns_structured_json()`

## Files Changed
- `tickets/todos/TCK-20260619-E51A-SIGNIFICANCE.md`
- `tickets/todos/TCK-20260619-E51B-GROUPER.md`
- `tickets/todos/TCK-20260619-E51C-NAMING.md`
- `tickets/todos/TCK-20260619-E51D-RENDERER.md`
- `tickets/todos/TCK-20260619-E51E-REST-API.md`
- `staging_artifacts/TCK-20260619-E51-CHRONICLE/investigation.md`
- `staging_artifacts/TCK-20260619-E51-CHRONICLE/plan.md`
- `staging_artifacts/TCK-20260619-E51-CHRONICLE/test_plan.md`

## Completion Summary
EPIC_SCOPED. Staged 5 child tickets (E51A–E51E) covering the full ChronicleCompiler pipeline: significance scoring → grouping → naming → rendering → REST API. Staging artifacts written. Sequential implementation order enforced by ticket dependencies.
