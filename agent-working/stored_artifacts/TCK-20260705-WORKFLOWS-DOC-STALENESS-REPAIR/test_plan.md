---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR
artifact_type: test_plan
tags: [ai, documentation, workflows]
---

# Test Plan — TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR

## Regression Surface

None. This is a pure documentation-repair chore with zero code changes (no `.claude/workflows/*.js`,
`.claude/agents/*.md`, `src/`, or `tests/` edits are in scope). There is no existing automated test
suite that parses or validates `docs/ai/*.md` prose/table content against live `.claude/workflows/*.js`
phase arrays — this repo has no doc-code parity checker for the `docs/ai/` tree (unlike
`docs/parity_ledger/`, which does have `tools/parity_ledger_scan.py` as of
`TCK-20260705-WORKFLOW-PARITY-SKIP`, but that only covers `docs/parity_ledger/` entries against `src/`,
not `docs/ai/workflows.md` against `.claude/workflows/`).

Because no code changes: no `pytest` regression surface exists for this ticket. The closest adjacent
regression check is `make docs-registry` (regenerates `docs/REGISTRY.yaml` from doc frontmatter) — not
required here since no frontmatter fields (title, layer, tags, status) change on any touched file, only
body content.

## New Tests Required

None applicable. There is no code path to unit-test, no schema to validate against, and no existing
architecture-guard convention for verifying prose/table content in `docs/ai/*.md` against
`.claude/workflows/*.js` source (grep-based ad hoc checks are how this ticket itself was
investigated — this is inherent to prose docs, not a testing gap this ticket should close). Per the
role prompt's instruction to say so plainly rather than invent inapplicable tests: **manual review is
the only verification mechanism available for this class of change**, matching how the four sibling
`WORKFLOW-*`/`AI-AGENT-OVERVIEW-DOC` tickets that touched these same docs this session were verified
(they also had no code-side test to write).

### Manual Verification Checklist (Implement/Verify phase should confirm, not skip)

- [ ] `docs/ai/workflows.md`'s `create-tickets` phase table lists exactly: Comprehend, Investigate,
      Structure, Write, Link (5 rows) — re-diff against `.claude/workflows/create-tickets.js`'s
      `phase()` call sites (lines 39, 204, 446, 672, 847) at edit time, not against this document's
      citation.
- [ ] `docs/ai/workflows.md`'s `generate-simulation-setup` phase line reads `Scan → Draft → Validate`.
- [ ] `docs/ai/workflows.md`'s `investigate-simulation-result` phase line reads `Load → Analyze →
      Report` (no `Correlate`).
- [ ] `docs/ai/workflows.md`'s `compact-simulation-result` phase line reads `Scan → Compact → Archive`.
- [ ] `docs/ai/workflows.md` gains an 11th `### \`simq-audit\`` section, phases `Recalibrate →
      Classify Drift → Update Anchors → Sync Docs → Parity Check → Verify → Report`, cross-checked
      against `docs/simulation_quality/audit_workflow.md` §2 (confirmed accurate source of truth) and
      `.claude/workflows/simq-audit.js`'s 7 `phase()` call sites.
- [ ] `docs/ai/skills.md` gains exactly **one** new row, in the "Project Skills (Workflow Shortcuts)"
      table only — **not** in "Project-Level Skill Files" (see investigation.md Risk #1: that table is
      reserved for non-workflow-triggered skills by its own header definition; `create-tickets`,
      `implement-ticket`, `implement-epic` are the existing precedent of workflow+SKILL.md-file skills
      that correctly appear in only one table).
- [ ] `docs/ai/README.md` line 40's `workflows.md` Document Index row no longer says "All 8 workflows";
      new text accurately reflects 10 documented + simq-audit as the 11th (or equivalent accurate
      phrasing — exact wording is Implement's call).
- [ ] `docs/ai/system_overview.md` §6's 2026-07-05 dated note is removed (its own framing was "candidates
      for a future documentation-maintenance ticket" pointing at exactly this ticket).
- [ ] (Added per architecture review round 1) `grep -n "Section 6" docs/ai/system_overview.md` returns
      zero matches — confirms all 4 dangling cross-reference parentheticals (lines 62, 152-153, 156,
      158-159 as of plan.md's citation) were struck along with the note itself, not left pointing at a
      section that no longer exists.
- [ ] No unrelated line in any of the five touched files changed (diff review: only the specific
      rows/sections/lines above should appear in `git diff`).
- [ ] `docs/ai/agent_infrastructure_audit.md` has zero diff (confirm out-of-scope file untouched).
- [ ] No `.claude/workflows/*.js` or `.claude/agents/*.md` file has any diff (confirm zero code
      changes, per ticket's explicit Out of Scope).

## Scoped Pytest Commands

None. No `pytest` command applies — there is no code under test. If Implement wants a belt-and-braces
check that nothing under `src/`/`tests/` was touched:

```
git diff --name-only | grep -vE '^(docs/ai/workflows\.md|docs/ai/skills\.md|docs/ai/README\.md|docs/ai/system_overview\.md|tickets/|staging_artifacts/|stored_artifacts/|agent-monitoring/)'
```

Expect empty output (only the ticket-workflow's own bookkeeping files and the four/five doc targets
should appear).

## Anti-Drift Test Guards

- The manual checklist item confirming `docs/ai/agent_infrastructure_audit.md` has zero diff is the
  primary anti-drift guard — that file's stale counts (10 files / 8 documented) are intentionally
  point-in-time and must not be "corrected" to match post-fix reality, which would falsify its own
  "as of 2026-07-03" framing.
- The `git diff --name-only` filter above is the primary guard against scope creep into
  `.claude/workflows/*.js` or `.claude/agents/*.md` — this ticket must produce zero code diff.
- The skills.md single-table-row guard (checklist item above) is the primary guard against
  reintroducing an inconsistency: confirm via `grep -c simq-audit docs/ai/skills.md` equals 1 (one
  occurrence, one row, one table) after the edit — not 2.
