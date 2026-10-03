---
status: active
layer: guidelines
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260718-CANONICAL-ENUM-DOCS-UPDATE
date: 2026-07-18
tags: [documentation, claude-md]
---

# Implementation Plan — TCK-20260718-CANONICAL-ENUM-DOCS-UPDATE

## Summary

Fix genuinely stale agent-instruction and doc text left behind across this
epic's 4 prior tickets: `done-checker.md`'s static-check mapping table,
`ticket-scoper.md`'s Priority/Layer guidance, 3 `.claude/workflows/*.js`
files' stale `LAYER_VALUES` reference, and 2 dashboard docs' "one
exception" facets language. Confirm `parity-updater.md` and
`architecture-reviewer.md`/`simulation-analyst.md` need no change (already
investigated and correctly scoped). Confirm no new standalone doc is
warranted.

## Steps

### Step 1 — `done-checker.md`

Add `ticket_field_values_valid` to the static-check mapping table (maps to
checklist #3). Update checklist item #3's own text to note `## Tier`/
`## Priority` are now static-verified, `## Type` remains judgment.

### Step 2 — `ticket-scoper.md`

Fix Priority guidance (add `P3`). Fix Layer guidance (mention the
registry, `python3 tools/layer_registry.py list`/`add`). Fix the
frontmatter template's `layer:` placeholder text.

### Step 3 — `.claude/workflows/*.js`

Fix the identical stale `layer: <infer... use LAYER_VALUES in
tools/validate_frontmatter.py>` text in `create-tickets.js`,
`simq-audit.js`, `implement-ticket.js`. Verify with `node --check` after
each edit.

### Step 4 — Dashboard docs

Rewrite the "statuses is the one exception" paragraphs in
`docs/observability/agent_ops_dashboard_contract.md` and
`docs/guides/agent_ops_dashboard.md` to describe the final state (4 of 5
facets canonical, only `tags` corpus-derived).

### Step 5 — Verify no other stale references remain

Grep for `LAYER_VALUES` and `P0 | P1 | P2` (missing P3) across
`.claude/` and `docs/` to confirm nothing else was missed; confirm every
remaining hit is either already-correct (parity-ledger's own P0-P2 scale)
or already fixed.

## Scope Guards

- `concern-investigator.md`'s `priority_hint`/`tier_recommendation` fields
  are intentionally narrower/looser (a *hint*, not a validated ticket
  field) — not touched, to avoid unrelated coupling with
  `create-tickets.js`'s own Structure-phase mapping logic.
- `parity-updater.md`'s `priority: P0 | P1 | P2` — confirmed correct
  (parity ledger's own distinct scale), not touched.
- No new `docs/guidelines/` file created — folded into `CLAUDE.md`, already
  done by the prerequisite ticket.

## Dependency Map

All 5 steps are independent of each other; sequenced for readability, not
correctness.

## Acceptance Criteria Map

- AC "agent files corrected, others left alone with reasoning" → Steps
  1-2 + investigation.md's per-file reasoning.
- AC "validate_frontmatter.py docstring accurate" → investigated, no
  change needed (already correct).
- AC "Layer-vs-Tag doc decision made and documented" → investigation.md's
  Risks section.
- AC "CLAUDE.md Priority line confirmed correct" → already landed by
  TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM; re-confirmed here.

## Anti-Drift Notes

None beyond what investigation.md already covers.
