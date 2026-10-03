---
status: active
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260706-DIAGRAM-COVERAGE
artifact_type: investigation
tags: [documentation, diagrams]
---

# Investigation — TCK-20260706-DIAGRAM-COVERAGE

## Diagram inventory (as found, before this ticket)

Searched `docs/` for mermaid blocks (` ```mermaid `, `graph TD`, `stateDiagram`), `.mmd` files, and
dense ASCII box-drawing content:

| Doc | Diagram type | Covers |
|---|---|---|
| `docs/systems/state_machines.md` | Mermaid `stateDiagram-v2` | Engine tick cycle |
| `docs/architecture/observability_behavior_profiling_boundary.md` | Mermaid `graph TD` | Observability/profiling pipeline boundary |
| `docs/strategy/bounded_cognition_decision_flow.md` | Mermaid | Cognition decision flow |
| `docs/entity/entity_aspect_relationship_diagram.mmd` | Standalone `.mmd` | Entity/aspect relationships |
| `docs/engine/architecture.md` | Mermaid | Engine architecture |
| `docs/engine/contracts/infrastructure_overview.md` | Mermaid | Component map |
| `docs/ai/ticket-lifecycle.md` | **ASCII box-and-arrow** (Overview section, lines 30-98) | implement-ticket 11-phase pipeline, gates, tier routing |
| `docs/guides/simulation_quality.md` | **None** | SimQ feed → hub → scorers → grades → API pipeline (prose/tables only) |

Confirms the original exploratory-question hypothesis partially: engine/observability/cognition
already have Mermaid coverage; the process/orchestration side has *a* diagram but it's the only
ASCII one in an otherwise Mermaid-using corpus; SimQ has none at all despite being a real pipeline.

## Ground truth for the ticket-lifecycle diagram (cross-checked, not assumed)

Read `docs/ai/ticket-lifecycle.md`'s existing Overview (ASCII) and `docs/ai/workflows.md`'s
`implement-ticket` phase table side by side — both post-date
`TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR` (a ticket specifically about fixing stale phase
lists), so both are current and consistent with each other. Confirmed phase sequence:

Scope (`ticket-scoper`) → [Investigate (`investigator`) → Plan (`planner`) → Review
(`architecture-reviewer`) — standard tier only] → Implement (`implementer`) → [Architecture-Verify
(`architecture-reviewer`, 2nd call) — skipped for hotfix] → Test (`test-scoper`) → Parity
(`parity-updater`, conditionally skipped) → [Security-Review (`security-reviewer`) — only if tagged
`security` or `suggested_skills` includes `/security-review`] → Verify (`done-checker`) → Finalize
(inline) → DONE.

Gate return values per phase (from the Failure Recovery Reference table):
`CONFLICTS_DETECTED` (Scope), `NEEDS_HUMAN_INPUT` (Plan), `NEEDS_CHANGES`/`BLOCKED` (Review and
Architecture-Verify, same vocabulary), `TESTS_FAILED` (Test), `SECURITY_BLOCKED`
(Security-Review), `DOD_BLOCKED` (Verify), `FINALIZE_INCOMPLETE` (Finalize's own migration
self-check).

## Ground truth for the SimQ diagram

Read `docs/guides/simulation_quality.md`'s "What SimQ does", "Feed modes", and "REST API" sections.
Confirmed flow: engine emits events onto the global observability queue → **feed mode** splits two
ways: `InProcessQualityFeed` (default, drains the queue via a `QueueDrainWorker` background thread,
same process) or `BrokerQualityFeed` (production multi-process, consumes a Redis stream via
`RedisStreamConsumer` in a separate `src/simulation_quality/worker.py` process, exposes a health
endpoint, writes a `QualityReport` to disk on shutdown) → both feed into `QualityHub.on_envelope()`
→ 10 pillar scorers (Cognition, Agency, Combat, Faction, Economy, Progression, Social, Information,
World Dynamics, Narrative) accumulate raw scores → normalized per tick → letter grades → consumed
via the REST API (`/status`, `/pillars`, `/pillars/{id}`, `/alerts`, `/report`).

## Decision: replace, not duplicate, the ASCII diagram

Keeping both an ASCII and a Mermaid version of the same pipeline would create two representations
to keep in sync on every future workflow change — this repo already has an explicit anti-pattern
warning against exactly that shape of problem (`tag_taxonomy.md`'s "kept in sync by hand" note
about `registry_query.py`'s `SEED_TAGS`). Replacing is the only option that doesn't introduce a new
drift risk.
