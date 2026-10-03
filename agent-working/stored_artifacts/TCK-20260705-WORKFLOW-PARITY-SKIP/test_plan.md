---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKFLOW-PARITY-SKIP
artifact_type: test_plan
tags: [workflows, observability]
---

# Test Plan — TCK-20260705-WORKFLOW-PARITY-SKIP

## Regression Surface

- **No existing automated test exercises `.claude/workflows/*.js` semantics.** Confirmed by a repo-wide
  search: zero hits for `implement-ticket`/`workflows/*.js` in `tests/` or `tools/` outside the unrelated
  `tests/integration/lab_agent/*_workflow.py` / `tests/unit/lab_agent/test_workflow_registry.py` suite,
  which covers a distinct, actually-Python-executed `lab_agent` workflow system, not this pseudocode DSL.
  This file is read and manually translated to tool calls by the orchestrating Claude agent per
  `.claude/skills/implement-ticket/SKILL.md`'s translation table — there is no Node/pytest runner wired to
  it. `TCK-20260705-WORKFLOW-SECURITY-GATE`'s own test_plan.md (merged, same file, sibling change) already
  established this precedent and used purely structural/manual verification; this ticket follows the same
  category of checks rather than inventing a new pattern.
- **`tools/agent-monitoring/{record_run,record_events,validate,query,generate_retro}.py`** — must continue
  accepting a `'skipped'` status value for the Parity phase's event record with zero code changes. Already
  proven safe by the existing hotfix-tier skip precedent (`implement-ticket.js:421-426`, which uses the
  same `'skipped'` status for Investigate/Plan/Review events) — confirmed none of these 5 scripts validate
  phase names or status values against an enum/allowlist (`record_run.py` only checks required *keys* are
  present). Run as a regression guard only if these scripts are touched (they should not be for this
  ticket).
- **`tests/tools/test_validate_frontmatter.py`** — validates ticket/doc YAML frontmatter. This ticket
  modifies `docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md` body content
  (Parity phase description) — run as a regression guard since frontmatter could be accidentally disturbed
  while editing body text near the top of these files.
- **Existing Security-Review gate** (`implement-ticket.js:573-629`) — confirmed structurally independent
  (different trigger data, sits after Parity's `pushEvent`/skip-equivalent). No regression risk expected,
  but include one manual check (below) confirming the skip path still leaves `parity`/`parityText` in a
  state that does not break anything Security-Review or Verify reads later (neither reads `parity`/
  `parityText` directly today — confirmed by grep — but re-verify after the edit in case the skip
  implementation introduces a new variable name mismatch).
- **`docs/parity_ledger/*.yaml` themselves** — read-only for this ticket. No ledger entry content changes;
  regression guard is simply "no P0 entry's `status`/`v2_evidence`/`test_path` differs before/after" (a
  `git diff --stat docs/parity_ledger/` should show zero changes once this ticket is implemented).

## New Tests Required

Since `.claude/workflows/implement-ticket.js` has no executable Python/pytest surface, verification is
structural/manual, matching the `TCK-20260705-WORKFLOW-SECURITY-GATE` precedent. Per Acceptance Criteria:

1. **Syntax validity** — `node -c .claude/workflows/implement-ticket.js` must exit 0 after the edit.
2. **Skip-trigger correctness (AC 1 — docs-only ticket)** — grep/read-verify the new skip branch's
   condition is exactly
   `implementation.files_changed.every(f => !f.startsWith('src/')) && !implementation.behavior_changed`
   (both signals, `&&` not `||`), reads `implementation.*` (post-Implement variable), and **never**
   references `ticketInfo` / any Scope-phase field / `Related Code Areas` text.
3. **Scope-drift regression (AC 2 — the single most important test)** — construct a synthetic case: a
   ticket whose `Related Code Areas` at Scope time list only `docs/`/`tickets/` paths, but whose Implement
   phase (simulated) returns `files_changed: ['docs/foo.md', 'src/core/state.py']`. Trace the code path by
   hand (or via a minimal harness if one is built) and confirm the skip condition evaluates false (because
   `files_changed.every(...)` is false — `src/core/state.py` fails the `!f.startsWith('src/')` predicate),
   so the full `agent(...)` Parity call still fires. Do not accept an implementation that reads any
   Scope-time signal as a substitute or shortcut for this check.
4. **Signal-disagreement regression (AC 3 — behavior_changed true but no src/ file)** — construct a second
   synthetic case: `files_changed: ['config/simulation_quality/profiles/foo.yaml']` (no `src/` path) but
   `behavior_changed: true`. Confirm the skip condition evaluates false (the `&&` requires both), so Parity
   still runs in full. This is the config/data-file-with-real-effect scenario the AC calls out explicitly.
5. **P0 safeguard presence and placement (AC 4)** — grep-verify the new safeguard check exists, runs only
   inside the skip-eligible branch (lazy — not on every Parity invocation; see investigation.md's mechanism
   recommendation), and scans exactly the 8 canonical parity-ledger files the existing Parity prompt already
   lists (`implement-ticket.js:556`) — not a naive `docs/parity_ledger/*.yaml` glob that would also sweep in
   `faction.yaml`/`schema.json`. Confirm the safeguard, if it ever found an intersection, would force the
   full agent call rather than silently proceeding with the skip (i.e. it must be able to override the skip,
   not just log a warning).
6. **`pushEvent(..., 'skipped', ...)` shape (AC "zero change for non-skip tickets" + Hard Rule)** — diff
   the skip branch's `pushEvent` call against the hotfix-tier precedent
   (`pushEvent('Investigate', 'investigator', 'skipped', 'Hotfix tier — investigation skipped')`,
   `implement-ticket.js:423`): confirm the new call uses `pushEvent('Parity', 'parity-updater', 'skipped',
   '<reason>')` — same 4-arg shape, no `ts` argument (defaults to `null`, back-filled by `writeMonitoring`).
7. **Zero-cost/no-regression path (AC 5 — a ticket that DOES need Parity)** — grep-verify the `else` branch
   (or equivalent) that reaches the existing unmodified `agent(...)` call at lines 542-567 is byte-identical
   to the pre-change code; confirm via `git diff` that the only changes inside the Parity phase section are
   (a) the new condition check, (b) the new synthetic-result + `pushEvent('skipped', ...)` branch, and (c)
   the new lazy P0-safeguard scan — no changes to the existing agent prompt text or schema.
8. **Doc updates** — after editing `docs/ai/workflows.md`, `docs/ai/system_overview.md`,
   `docs/ai/ticket-lifecycle.md` to describe the new conditional skip (matching how Security-Review's
   conditional trigger is already documented in all three), run `make knowledge-index-update` per CLAUDE.md
   ("If any files under `docs/` were created or modified"). Required, easy to forget.
9. **Event-count byte comparison (analogous to the security-gate ticket's AC 3 check)** — for a
   non-skip-eligible ticket (touches `src/`), confirm `agent-monitoring/events.jsonl`'s Parity-phase event
   count and shape are unchanged from a pre-change run — the optimization must be strictly additive
   (new branch only), never altering the existing non-skip code path's observable output.

## Scoped Pytest Commands

No Python source is expected to change for the core skip logic (it lives entirely in
`.claude/workflows/implement-ticket.js` plus 3 docs files). Run these as regression guards only:

```
python3 -m pytest tests/tools/test_validate_frontmatter.py -v
```

If Plan decides to implement the P0-safeguard scan as a standalone, testable Python helper (e.g.
`tools/parity_ledger_scan.py`, mirroring `tools/registry_query.py`'s pattern, invoked by the orchestrating
agent via a single Bash call rather than inline shell) rather than as an ad-hoc inline shell one-liner, add
`tests/tools/test_parity_ledger_scan.py` with:
- a positive-control case using a synthetic small YAML fixture where a P0 entry's `v2_evidence` does contain
  a path matching a given `files_changed` entry (must detect it, since none of the real ledger's current
  content can exercise this branch — see investigation.md's empirical finding),
- a negative-control case using the real 8-file scan returning no intersection for a representative
  docs-only `files_changed` list (e.g. `['docs/ai/workflows.md']`),
- an explicit check that the function only scans the 8 canonical files (`substrate.yaml`,
  `combat_movement.yaml`, `strategic_cognition.yaml`, `town_resource.yaml`, `progression.yaml`,
  `social_narrative.yaml`, `world_dynamics.yaml`, `infrastructure.yaml`) and not `faction.yaml`.

```
python3 -m pytest tests/tools/test_parity_ledger_scan.py -v   # only if this module is created
```

## Anti-Drift Test Guards

- **Do not build a Test-phase skip alongside this one.** The tag-tuning investigation's Candidate 4
  explicitly rejected the analogous "skip Test for docs-only tickets" idea, falsified by
  `TCK-20260705-AI-AGENT-OVERVIEW-DOC`'s legitimate passing `test_validate_frontmatter.py` run on a
  docs-only change. Any test plan or implementation that starts touching `phase('Test')`
  (`implement-ticket.js:479` onward) is out of scope and a drift signal.
- **Do not let the P0 safeguard degrade into a warning-only check.** If a future edit makes the safeguard
  merely `log()` a warning instead of forcing the full Parity agent call on intersection, that silently
  reintroduces the exact risk (P0 entry going stale) the ticket's Scope explicitly guards against. Any test
  or review of this ticket must confirm the safeguard can actually block the skip, not just annotate it.
- **Do not let the skip's synthetic "not applicable" result get treated as equivalent to a real
  `parity-updater` return for downstream phases.** Verify (Verify phase, `implement-ticket.js:658-688`)
  reads `implementation.behavior_changed` directly (line 672) and does not read the `parity`/`parityText`
  variable at all today — confirm this remains true after the change so the synthetic result never needs to
  imitate the real agent's return shape beyond what `pushEvent` needs.
