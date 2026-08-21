---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-VISUAL-AGENT-REVIEW
phase: open
date: 2026-08-21
tags: [visualization, simulation-quality, determinism, world]
---

# TCK-20260821-VISUAL-AGENT-REVIEW

## Title
Tiered agent-review pipeline for visual-quality escalation

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Build a tiered agent-review pipeline: Tier 0 (pure data, zero image, deterministic hard/soft/scoring-rule path, primary/default) -> Tier 1 (compact JSON digest) -> Tier 2 (actual image, fetched only on escalation, annotated/gridlined by default for citable coordinates).

## Scope
- Implement the Tier 0 -> Tier 1 -> Tier 2 escalation pipeline per PROPOSAL.md §4c-§4h's proven mechanism (Tier 0/1 already shown bit-identical SHA256; annotated-vs-plain distinction already tested)
- Decide new .claude/agents/world-render-reviewer.md subagent vs folding into an existing agent (simulation-analyst.md is the closest structural template; world-debugger.md ruled out as a different job)
- Define the exact Tier 1 digest JSON schema and the exact escalation threshold (both explicitly open, decide jointly with the grade-scorer ticket at Plan-phase time)
- Ensure the annotated/gridlined PNG variant (not plain) is fetched on escalation, giving citable tile-coordinate ranges
- Follow simulation-analyst.md's contract output shape: one-line summary, findings table with severity + evidence/coordinates, recommended next steps

## Out of Scope
- Any change to the renderer itself or to the Tier 0 scoring system's internals beyond consuming their output
- CI-gating this pipeline — report-only, on-demand, never CI-gated

## Acceptance Criteria
- [ ] When Tier 0 does not flag an anomaly, the pipeline completes with a Tier 1 digest only and zero image is ever fetched via Read
- [ ] When Tier 0 flags an anomaly, the ANNOTATED/gridlined PNG variant (not plain) is fetched, and the resulting verdict cites tile-coordinate ranges traceable to that image
- [ ] The Tier 1 digest is deterministic — byte/field-identical across repeated runs of the same state
- [ ] Agent-review output follows simulation-analyst.md's contract shape: one-line summary, findings table with severity + evidence/coordinates, recommended next steps
- [ ] A golden-hash regression test (tests/unit/, regression marker) covers the Tier 0/1 determinism claim

## Related Tickets
- TCK-20260821-WORLD-RENDER-CORE
- TCK-20260821-VISUAL-GRADE-SCORER
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- experiments/spatial_rendering/PROPOSAL.md
- .claude/agents/simulation-analyst.md
- .claude/agents/world-debugger.md

## Assumptions / Open Questions
- Whether this becomes a new .claude/agents/world-render-reviewer.md subagent or folds into an existing agent is a genuine unresolved tradeoff, decided during this ticket's own Plan phase
- Exact Tier 1 digest JSON schema and exact escalation threshold are explicitly open, likely decided jointly with the grade-scorer ticket
- simulation-quality: this pipeline consumes the SimQ-sibling Tier 0 scoring system, tagged for topical adjacency rather than SimQ-subsystem membership

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
