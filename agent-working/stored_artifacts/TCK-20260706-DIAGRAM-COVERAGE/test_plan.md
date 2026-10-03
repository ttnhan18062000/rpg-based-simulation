---
status: active
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260706-DIAGRAM-COVERAGE
artifact_type: test_plan
tags: [documentation, diagrams]
---

# Test Plan — TCK-20260706-DIAGRAM-COVERAGE

Documentation-only ticket — no `src/`/`tools/` changes, no pytest suite applies. Verification is:

1. `python3 tools/validate_frontmatter.py docs/guides/diagram_index.md`
2. `python3 tools/validate_frontmatter.py docs/ai/ticket-lifecycle.md`
3. `python3 tools/validate_frontmatter.py docs/guides/simulation_quality.md`
4. `python3 tools/validate_frontmatter.py docs/guides/README.md`
5. Manual content-parity diff: every phase/agent/gate-status string in the new
   `ticket-lifecycle.md` Mermaid diagram cross-checked against `docs/ai/workflows.md`'s
   `implement-ticket` phase table (the acknowledged source of truth).
6. `make docs-registry` — confirm exit 0 (no *new* missing-frontmatter doc; the 12 pre-existing
   ones, confirmed unrelated to this ticket in prior session work, are expected and disclosed).
7. `make knowledge-index-update` — confirm it completes and the new
   `docs/guides/diagram_index.md` is retrievable via `search_docs` afterward.

## Acceptance-criteria-to-check mapping

- "Every phase/gate/tier-skip preserved" → step 5.
- "Diagram index lists every diagram" → manual cross-check against investigation.md's inventory
  table (8 entries: state_machines, observability boundary, cognition decision flow, entity
  relationship `.mmd`, engine architecture, infrastructure overview, ticket-lifecycle (now
  Mermaid), simulation_quality (new)) — all 8 must appear in `diagram_index.md`.
- "No files moved" → `git status` after the change shows only edits/new files, zero renames.
