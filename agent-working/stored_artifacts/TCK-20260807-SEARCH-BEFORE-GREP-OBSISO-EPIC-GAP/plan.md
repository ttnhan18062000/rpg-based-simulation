---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP
artifact_type: plan
tags: [agent-monitoring, process-improvement]
---

# Plan — TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP

## Fix

Add an explicit instruction to `.claude/agents/investigator.md`'s `## Inputs` section (before its
existing "Read: ..." bullet list), stating: even when a ticket's own Scope phase (or the epic-level
research that produced it) already surfaced relevant context, Investigate must still make its own
`mcp__knowledge-search__search_docs` and `graphify query` call(s) — scoped to this ticket's own
specific investigation question — before any `grep`/`find`/raw file read within its own phase. Do
not rely on CLAUDE.md's global instruction alone; state it directly in this agent's own persistent
definition, matching the same pattern already applied to the sidecar-write gap in
`TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP`.

Not a template/prompt REWRITE — a small, targeted addition. The rest of the file (Output 1/2
structure, Docs Requiring Update format, etc.) is unaffected and stays as-is.

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md identifies exact tool-call sequence for both pairs, confirms/refutes shared cause | Done — confirmed shared cause: Scope-phase research front-loading + investigator.md's own missing explicit instruction |
| If shared cause found: concrete fix to relevant prompt/template/skill instruction | `.claude/agents/investigator.md` addition |
| If no shared cause: honest "isolated, no pattern" conclusion | N/A — real shared cause found |
| Scoped pytest passes (if any code/prompt change made) | `tests/tools/test_workflow_meta_conformance.py` |
