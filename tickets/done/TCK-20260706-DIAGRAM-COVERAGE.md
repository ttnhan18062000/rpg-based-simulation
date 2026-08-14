---
status: active
layer: guidelines
authority: P2
audience: developer
ticket_id: TCK-20260706-DIAGRAM-COVERAGE
phase: done
date: 2026-07-06
tags: [documentation, diagrams]
---

# TCK-20260706-DIAGRAM-COVERAGE

## Title
Add a diagram index and close the two highest-value missing-diagram gaps (ticket pipeline, SimQ data flow)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
User asked whether every major component/mechanism (process development, engine, observability,
simulation quality) has diagram coverage, suspecting a management-flow/component-diagram gap, and
whether diagrams help maintain context for human review or agent work. Investigation confirmed:
engine/observability/cognition already have mermaid diagrams; the agent-orchestration process has
one diagram but it's ASCII-only (`docs/ai/ticket-lifecycle.md`'s Overview section) rather than a
renderable Mermaid diagram like everywhere else; SimQ (`docs/guides/simulation_quality.md`) has
zero diagrams despite being a real multi-stage pipeline described only in prose. User agreed with
the recommendation to (a) add a lightweight diagram index rather than physically relocating
diagrams into a `docs/diagrams/` folder, and (b) build the two highest-value diagrams, and asked
for this to go through the ticket process.

## Scope
- **`docs/guides/diagram_index.md`** (new): a lightweight index listing every diagram in the repo
  (mermaid blocks, `.mmd` files, and dense ASCII flow diagrams), grouped by domain, each linking to
  its host doc — no files physically moved. Diagrams stay co-located with their explanatory prose
  (matches this repo's domain-based `docs/` organization; avoids splitting `search_docs` semantic
  chunks across two files).
- **`docs/ai/ticket-lifecycle.md`**: replace the existing ASCII-art pipeline diagram (Overview
  section) with an equivalent Mermaid flowchart — same phases, same gate/branch conditions, same
  hotfix-tier skip behavior — for consistency with every other rendered diagram in the repo and
  better rendering in the Docusaurus site. Content parity verified against the current phase table
  in `docs/ai/workflows.md`'s `implement-ticket` section (confirmed accurate, last fixed by
  `TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR`).
- **`docs/guides/simulation_quality.md`**: add a new Mermaid diagram covering the SimQ data flow —
  engine event bus → feed mode (`InProcessQualityFeed` in-process default vs. `BrokerQualityFeed`
  Redis-based) → `QualityHub` → the 10 pillar scorers → normalized grades → REST API endpoints /
  `QualityReport` output. Placed near the existing "What SimQ does" / "Feed modes" sections it
  visualizes.
- Add a row to `docs/guides/README.md` for the new diagram index guide.
- `make docs-registry` + `make knowledge-index-update` (docs changed).

## Out of Scope
- Physically moving any existing diagram file or mermaid block into a new location — the whole
  point of the index approach is zero file movement.
- Adding diagrams to every doc that lacks one — scoped narrowly to the two gaps identified as
  genuinely complex enough that prose/tables lose the shape of the thing (per the exploratory
  discussion); a blanket diagramming pass was explicitly not what was agreed.
- Building any tooling to auto-generate or auto-validate the diagram index against the corpus —
  it's a small, hand-maintained list at today's diagram count; automation would be premature.

## Acceptance Criteria
- [ ] `docs/guides/diagram_index.md` exists, lists every diagram found during investigation
      (mermaid + `.mmd` + the ticket-lifecycle ASCII-turned-Mermaid), passes
      `validate_frontmatter.py`.
- [ ] `docs/ai/ticket-lifecycle.md`'s pipeline diagram is Mermaid, not ASCII, and preserves every
      phase, gate condition, and the hotfix-tier skip behavior the original ASCII version conveyed.
- [ ] `docs/guides/simulation_quality.md` has a new Mermaid diagram showing the feed → hub →
      scorers → grades/API flow.
- [ ] `docs/guides/README.md` links the new index.
- [ ] `docs/REGISTRY.yaml` regenerated; `make knowledge-index-update` run successfully.

## Related Tickets
- TCK-20260706-TICKET-REPORTING-GUIDE (prior related docs-guide addition this session, same
  "pillars"/guide-authoring pattern)

## Related Docs
- docs/ai/ticket-lifecycle.md
- docs/ai/workflows.md (source of truth for phase/gate accuracy, cross-checked not duplicated)
- docs/guides/simulation_quality.md
- docs/guides/README.md
- docs/systems/state_machines.md, docs/architecture/observability_behavior_profiling_boundary.md,
  docs/strategy/bounded_cognition_decision_flow.md, docs/entity/entity_aspect_relationship_diagram.mmd,
  docs/engine/architecture.md (existing diagrams the index catalogs, read-only)

## Related Stored Artifacts
None yet.

## Related Code Areas
None — documentation-only ticket, no `src/` changes.

## Assumptions / Open Questions
- Assumed "diagram index" means a doc that links to diagrams in place, not a database/registry
  field — confirmed reasonable given the small (single-digit-to-low-teens) diagram count today.
- Assumed replacing (not duplicating) the ticket-lifecycle ASCII diagram with Mermaid is correct —
  keeping both would mean two representations of the same flow to keep in sync on every future
  workflow change, which this repo's existing patterns avoid elsewhere (e.g. `tag_taxonomy.md`'s
  explicit "one copy, not two" reasoning for `registry_query.py`'s `SEED_TAGS`).

## Implementation Notes
Implemented per plan.md's 5 steps:

1. **`docs/guides/diagram_index.md`** (new): 8 diagrams cataloged, grouped into 5 domains
   (Engine & Simulation, Observability & Simulation Quality, Cognition & Strategy, Entities, Agent
   Process), each linking to its host doc with a one-line "Covers" description. Notes explicitly
   that the list isn't automated and should be updated by hand when new diagrams land.
2. **`docs/ai/ticket-lifecycle.md`**: replaced the ASCII Overview with a Mermaid `flowchart TD`.
   All 10 agent names verified to match `workflows.md`'s phase table exactly (grepped both files'
   agent lists and diffed). Content-parity check caught a real labeling bug before finalizing: the
   Security-Review gate edge was initially labeled with the *agent's own* internal verdict
   vocabulary (`NEEDS_CHANGES / BLOCKED`) instead of the *workflow's* outer return status
   (`SECURITY_BLOCKED`, per `workflows.md`'s Return Values table and `ticket-lifecycle.md`'s own
   Failure Recovery Reference) — every other gate edge in the diagram uses the outer workflow
   status, so this was an inconsistency, not a style choice. Fixed; re-verified all 7 distinct gate
   labels (`CONFLICTS_DETECTED`, `NEEDS_HUMAN_INPUT`, `NEEDS_CHANGES / BLOCKED`, `TESTS_FAILED`,
   `SECURITY_BLOCKED`, `DOD_BLOCKED`, `FINALIZE_INCOMPLETE`) against the source-of-truth table.
3. **`docs/guides/simulation_quality.md`**: added a Mermaid `flowchart LR` under "What SimQ does",
   before "Quick start" — engine event bus → 2 feed-mode branches (in-process/broker, cross-linked
   to the existing "Feed modes" section rather than duplicating its prose) → `QualityHub` → 10
   pillar scorers (grouped as one labeled node, not 10 separate boxes, to stay readable) → grades →
   REST API/`QualityReport`.
4. **`docs/guides/README.md`**: added the `diagram_index.md` row.
5. **`make docs-registry`** (1290 entries) and **`make knowledge-index-update`** (run twice — once
   after the initial diagrams, once after the `SECURITY_BLOCKED` fix — both completed successfully,
   confirmed `diagram_index.md` retrievable via `search_docs`).

Both new Mermaid blocks were checked for balanced `[`/`]`/`(`/`)`/`{`/`}` via a small one-off Python
bracket-count script (this repo has no Mermaid linter) — both balanced on the first pass; no syntax
issues found.

**Disclosed, not fixed (pre-existing, unrelated to this ticket):** `docs/guides/README.md` and
`docs/guides/simulation_quality.md` both lack a `status` frontmatter field — confirmed via `git
show HEAD:<path>` that this predates this ticket's edits (same class of gap already disclosed in
this session's earlier tag-registry ticket for `docs/engine/project_lawbook_m10.md` and others).

## Test Summary
Documentation-only ticket, no pytest suite applies (per test_plan.md). Verification performed:
- `validate_frontmatter.py` on all 4 touched/new docs: `diagram_index.md` OK, `ticket-lifecycle.md`
  OK, `simulation_quality.md` and `README.md` show the pre-existing `status`-missing gap noted
  above (not introduced by this ticket — confirmed via `git show HEAD:...` on both before editing).
- Content-parity diff (manual): all 10 agent names and all 7 gate-status labels in the new
  `ticket-lifecycle.md` Mermaid diagram cross-checked against `docs/ai/workflows.md`'s
  `implement-ticket` table — 1 mismatch found and fixed (`SECURITY_BLOCKED`, see Implementation
  Notes), 0 remaining after the fix.
- `make docs-registry` exit 1 is the same pre-existing 12-file gap disclosed in this session's
  earlier ticket (`TCK-20260706-TAG-REGISTRY-DATA`), unrelated to any file this ticket touches.
- `make knowledge-index-update` completed successfully both times; `search_docs` query for
  "diagram index where are diagrams located" returned `docs/guides/diagram_index.md` as the top hit.

## Files Changed
- `docs/guides/diagram_index.md` (new)
- `docs/ai/ticket-lifecycle.md` (ASCII → Mermaid pipeline diagram)
- `docs/guides/simulation_quality.md` (new data-flow diagram)
- `docs/guides/README.md` (index row added)
- `docs/REGISTRY.yaml` (regenerated)
- `docs/guidelines/tag_registry.jsonl` (`diagrams` tag registered, `meta-process`)
- `tickets/inprogress/TCK-20260706-DIAGRAM-COVERAGE.md` → `tickets/done/...`
- `staging_artifacts/TCK-20260706-DIAGRAM-COVERAGE/` → `stored_artifacts/...`

## Completion Summary
Added `docs/guides/diagram_index.md` cataloging all 8 diagrams in the repo in place (no files
moved, per the agreed approach), and closed the 2 diagram gaps identified in the exploratory
discussion: `docs/ai/ticket-lifecycle.md`'s pipeline is now a Mermaid flowchart (was ASCII-only,
the one inconsistent diagram format in an otherwise-Mermaid corpus) with every phase, agent, and
gate-branch status verified against `workflows.md`'s table (catching and fixing one real
labeling bug — `SECURITY_BLOCKED` vs. the agent's internal `NEEDS_CHANGES/BLOCKED` vocabulary —
in the process); `docs/guides/simulation_quality.md` now has a data-flow diagram for a pipeline
that previously existed only in prose. No files relocated, no blanket diagramming pass — scope
stayed to the 2 gaps actually agreed on.
