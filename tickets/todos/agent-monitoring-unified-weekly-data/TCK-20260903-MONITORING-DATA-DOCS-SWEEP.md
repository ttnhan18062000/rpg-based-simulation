---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-DOCS-SWEEP
phase: open
date: 2026-09-03
tags: [agent-monitoring, observability, documentation, claude-md]
---

# TCK-20260903-MONITORING-DATA-DOCS-SWEEP

## Title
Update docs, `CLAUDE.md`, `.gitattributes`, and workflow/skill prose to describe the unified per-week
`agent-monitoring/data/` layout, correcting the prior epic's already-stale `CLAUDE.md` claims

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Child 7 of `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`, implementing the requester's explicit
instruction to also update "the rule, skill and related configuration." Confirmed via direct grep
this session:

- **`CLAUDE.md` itself is already stale today**, from the *already-shipped* prior tools-only epic,
  independent of this epic's own changes: line 94 ("Always stage `agent-monitoring/` (including
  `tools.jsonl`)... the monitoring tools auto-update `tools.jsonl` on every run") — factually wrong,
  the hook has written to a shard directory since 2026-09-02; lines 137/140 ("`agent-monitoring/
  tools.jsonl` is rewritten by a hook on nearly every tool call" plus an example command chaining
  `git add agent-monitoring/tools.jsonl`); line 254 (DoD checklist literally naming
  `agent-monitoring/runs.jsonl`/`agent-monitoring/events.jsonl`). These need fixing regardless of
  this epic landing, and additionally need to describe the new unified `data/` layout once it does.
- `docs/agent-monitoring/README.md` — confirmed already updated for the `tools` source by the prior
  epic (e.g. line 19's `tools/tools-YYYY-Www.jsonl` naming, lines 20-21's logical shorthand kept),
  but still correctly (for today) describes `runs.jsonl`/`events.jsonl` as single files — needs
  updating to the unified `data/YYYY-Www/{runs,events,tools}.jsonl` shape.
- `docs/agent-monitoring/schema.md` — per-source sections (beyond child 1's minimal write-path
  paragraph edits), the staleness-check description, and the Join Example Python snippet (confirmed
  this session to literally do `Path('agent-monitoring/runs.jsonl')`-style single-file reads).
- `docs/guides/agent_monitoring.md`, `docs/ai/system_overview.md` §6.
- `.gitattributes` — currently has, post children 1-2, one unified glob for the new layout plus
  (removed by child 2) none of the 3 legacy lines; confirm final state matches the target shape and
  no dangling reference remains.
- `.claude/workflows/implement-ticket.js` — confirmed this session to have **no functional file I/O**
  on these paths (delegates entirely to the Python tools) but has prose-only references inside
  template strings at multiple lines (confirmed: ~48-49, 269, 365, 369, 385, 563, 572, 1706) that
  should be corrected for accuracy even though no functional JS change is required.
- `.claude/skills/agent-monitoring-retro/SKILL.md` — check for path references (not yet checked this
  session).
- `docs/parity_ledger/infrastructure.yaml` `INFRA-291` — the entry the prior epic's consumer-migration
  child updated for the tools-only cutover; needs a further addendum for this epic's unification,
  via `tools/parity_ledger_writer.py::write_entry()` only, **never a raw YAML edit** (CLAUDE.md hard
  rule; the addendum pattern for this exact entry is already established by the prior epic).

## Scope
- Update every doc/config file named above to describe `agent-monitoring/data/YYYY-Www/{runs,events,
  tools}.jsonl` as the current physical layout, replacing every remaining reference to any of the 3
  retired shapes (monolithic `runs.jsonl`/`events.jsonl`, or the prior epic's `tools/tools-YYYY-
  Www.jsonl`) — except where a doc is deliberately describing historical/legacy shape in a "how we
  got here" note, which should stay accurate to history, not be rewritten away.
- Fix `CLAUDE.md`'s already-stale claims (lines 94, 137, 140, 254) as part of the same pass.
- Update `.gitattributes` if children 1/2 left anything inconsistent (confirm, don't assume clean).
- Add the `INFRA-291` addendum via `tools/parity_ledger_writer.py`.
- Run `make knowledge-index-update` at the end, per CLAUDE.md's "After Work" rule (docs were
  modified).

## Out of Scope
- Any functional code change — this ticket is docs/config/prose only.
- `.claude/workflows/implement-ticket.js`'s actual JS logic — confirmed no functional file I/O exists
  on these paths; only its template-string prose changes.
- Any new parity ledger entry beyond `INFRA-291`'s addendum, unless investigation finds this epic's
  changes genuinely require a new entry (unlikely — physical layout change, not a mechanics/behavior
  change) — document the finding either way.
- Rewriting any doc's historical/"how we got here" framing of the prior epic's tools-only shape into
  something that never happened — history stays accurate, only "current state" claims are corrected.

## Acceptance Criteria
- [ ] Grep for `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, and
      `agent-monitoring/tools/tools-` across `docs/`, `CLAUDE.md`, `.gitattributes`,
      `.claude/workflows/implement-ticket.js`, and `.claude/skills/` returns zero hits describing
      current physical layout (historical/"how we got here" references, if any, are excluded and
      individually justified).
- [ ] `CLAUDE.md` lines 94, 137, 140, 254 (or their post-edit equivalents) no longer make the
      confirmed-stale claims identified above.
- [ ] `.gitattributes` contains exactly the unified `data/*/*.jsonl`-style glob and no legacy lines.
- [ ] `docs/parity_ledger/infrastructure.yaml`'s `INFRA-291` entry has a new, date-stamped addendum
      describing this epic's unification, added via `tools/parity_ledger_writer.py` (confirmed by
      `git diff` showing a scoped, sanctioned-writer-shaped change, not a raw hand-edit).
- [ ] `make knowledge-index-update` completes successfully.

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (parent epic)
- TCK-20260903-MONITORING-DATA-MIGRATION (child 2 — this ticket should describe the real, landed
  final shape, so should run after child 2 at minimum)
- TCK-20260903-MONITORING-DATA-CONSUMERS-CORE, -CONSUMERS-GATES-DASHBOARD, -CODEX-REMIGRATION,
  -REFERENTIAL-INTEGRITY (children 3-6 — no hard file-level dependency, but sequencing this ticket
  last avoids describing an interim/incomplete consumer state and matches the requester's own
  suggested ordering)
- TCK-20260902-MONITORING-SHARD-CONSUMERS — updated `INFRA-291` for the tools-only cutover; this
  ticket adds the further addendum for the full unification.

## Related Docs
- `CLAUDE.md`, `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md`,
  `docs/guides/agent_monitoring.md`, `docs/ai/system_overview.md`, `.gitattributes`,
  `.claude/workflows/implement-ticket.js`, `.claude/skills/agent-monitoring-retro/SKILL.md`,
  `docs/parity_ledger/infrastructure.yaml`.

## Related Stored Artifacts
None yet.

## Related Code Areas
None — docs/config only, no `src/`/`tools/` production code changes (per Graphify Integration's own
rule, `graphify update .` is not required for this ticket since no `src/`/`tests/` files change).

## Assumptions / Open Questions
- Sequenced last in `SEQUENCE.md` on the reasoning above — no hard technical blocker prevents running
  it earlier, but doing so risks describing a not-yet-true state that then needs a second edit pass.
- `.claude/skills/agent-monitoring-retro/SKILL.md`'s exact content was not checked this session —
  confirm at implementation time whether it needs any change.
- `layer: observability` matches this repo's established pattern; `documentation`/`claude-md` tags
  reflect this ticket's docs-and-CLAUDE.md-specific scope, distinct from the other children's
  code-focused `data-quality`/`hooks`/`dashboard`/`schema` tags.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
