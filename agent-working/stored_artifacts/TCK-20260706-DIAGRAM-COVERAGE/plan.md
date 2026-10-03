---
status: active
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260706-DIAGRAM-COVERAGE
artifact_type: plan
tags: [documentation, diagrams]
---

# Plan — TCK-20260706-DIAGRAM-COVERAGE

## Steps

1. **`docs/guides/diagram_index.md`** (new): a short guide, grouped by domain
   (Engine/Simulation, Observability, Cognition/Strategy, Entities, Agent Process), each row
   linking to the host doc and naming the diagram type (Mermaid `stateDiagram`/`graph TD`,
   standalone `.mmd`). Includes the 2 new diagrams built in steps 2-3 below. Frontmatter:
   `layer: guidelines`, matches sibling guides (`ticket_tagging.md`, `ticket_reporting.md`).

2. **`docs/ai/ticket-lifecycle.md`**: replace the ASCII Overview block with a Mermaid `flowchart TD`
   carrying the same information density — phase name, agent name, and gate-branch edges labeled
   with their return status (`CONFLICTS_DETECTED`, `NEEDS_HUMAN_INPUT`, `NEEDS_CHANGES`/`BLOCKED`,
   `TESTS_FAILED`, `SECURITY_BLOCKED`, `DOD_BLOCKED`, `FINALIZE_INCOMPLETE`) and a visual grouping
   or annotation for the phases hotfix tier skips (Investigate, Plan, Review, Architecture-Verify).
   Keep the surrounding prose (Tier Routing table, Step-by-Step Detail sections) untouched — only
   the Overview diagram itself changes representation.

3. **`docs/guides/simulation_quality.md`**: add a Mermaid `graph TD` (or `flowchart LR`) placed
   right after "What SimQ does" (before "Quick start"), showing: engine event bus → 2 feed-mode
   branches (in-process / broker) → `QualityHub` → 10 pillar scorers (can be grouped as one
   subgraph node listing all 10, rather than 10 separate boxes, to stay readable) → grades → REST
   API / `QualityReport`. Cross-reference the existing "Feed modes" section below it rather than
   duplicating that prose.

4. **`docs/guides/README.md`**: add one row for `diagram_index.md`, same table style as existing
   rows.

5. **`make docs-registry`** (new doc) and **`make knowledge-index-update`** (docs changed).

## Verification (docs-only ticket, no pytest)

- `python3 tools/validate_frontmatter.py <each changed/new doc>` — frontmatter schema.
- Manual mermaid syntax sanity: each mermaid block must open with a valid diagram-type keyword
  (`flowchart`/`graph`/`stateDiagram-v2`) and have balanced `[`/`]`/`{`/`}` per node — checked by
  eye since this repo has no mermaid linter; note this as a limitation, not silently assume it
  renders.
- Content-parity check: every phase name, agent name, and gate status string in the new
  ticket-lifecycle Mermaid diagram must appear in `docs/ai/workflows.md`'s `implement-ticket` phase
  table (the source of truth) — manual side-by-side diff, not automated (no existing tooling parses
  Mermaid against a markdown table, and building one would be disproportionate for a single
  diagram).

## Out of scope reaffirmed

No file relocation, no blanket diagramming pass beyond the 2 identified gaps, no automated
diagram-index generation/validation tooling.
