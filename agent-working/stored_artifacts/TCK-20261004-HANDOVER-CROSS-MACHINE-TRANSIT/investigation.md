---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-HANDOVER-CROSS-MACHINE-TRANSIT
phase: open
date: 2026-10-04
tags: [ai, hooks, process-improvement]
---

# investigation — TCK-20261004-HANDOVER-CROSS-MACHINE-TRANSIT

- `.claude/handover/` is gitignored (.gitignore:318); `agent-working/handover-transit/**/*.txt` is not ignored (git check-ignore clean).
- docs/REGISTRY.yaml generation, the knowledge index (explicit path patterns) and frontmatter validation never reach the bundle: a real 223-file export produced 0 registry rows.
- Hook was clear-only; settings.json SessionStart matcher is `*`, so widening is script-only.
- search_docs index absent in this worktree (returns []); graphify had no relevant nodes.
