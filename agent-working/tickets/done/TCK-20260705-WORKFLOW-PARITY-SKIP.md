---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260705-WORKFLOW-PARITY-SKIP
phase: done
date: 2026-07-05
tags: [workflows, observability]
---

# TCK-20260705-WORKFLOW-PARITY-SKIP

## Title
Skip the Parity phase's agent call for tickets with no src/ changes and no reported behavior change

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION` (done) found that `implement-ticket.js`'s Parity phase
**always** invokes the `parity-updater` agent (line ~521), even when `implementation.behavior_changed`
is `false` — the existing ternary only softens the agent's prompt (verify `test_path` references rather
than update ledger entries), it never skips the call itself. This session repeatedly observed this
pattern on genuinely docs-only/investigation-only tickets (e.g. `TCK-20260705-WORKING-LOG-BACKFILL`,
`TCK-20260705-SIX-SKILLS-INVESTIGATION`, `TCK-20260705-AI-AGENT-OVERVIEW-DOC`), where the Parity phase's
agent call reliably concluded "N/A, no parity ledger entry applies" — a real, recurring, bounded cost
with no informational value in the common case.

## Scope
- Modify `implement-ticket.js`'s Parity phase to skip the `agent(...)` invocation entirely (replacing it
  with a synthetic "not applicable" result plus a `pushEvent(..., 'skipped', ...)`) **only when both**:
  1. `implementation.files_changed.every(f => !f.startsWith('src/'))` — no `src/` path in the
     post-Implement, authoritative file list (`IMPL_SCHEMA`, already required today).
  2. `!implementation.behavior_changed` — the implementer's own self-reported boolean is also false.
  Both signals must agree before skipping — never trust either alone (this is the investigation's
  explicit, non-negotiable safety condition).
- The trigger **must** read `implementation.files_changed`/`implementation.behavior_changed` (both
  produced by the Implement phase that has already run by the time Parity starts) — **never**
  `Related Code Areas` (a pre-Implement, Scope-time guess). This is the single most important
  constraint in this ticket: a ticket originally scoped as "docs only" that actually touches `src/` once
  Implement runs (scope drift) must still get a full Parity pass.
- Still write a `pushEvent(..., 'skipped', ...)` entry for the skipped case — CLAUDE.md's Hard Rule
  requires at least one event entry per phase-equivalent step; follow the existing hotfix-tier skip
  convention already used for Investigate/Plan/Review (`implement-ticket.js` lines ~401-404) as the
  precedent to copy.
- Add an explicit safeguard: before allowing the skip, confirm none of `implementation.files_changed`
  intersects any P0 parity-ledger entry's `v2_evidence` path — a P0 entry going stale must never be a
  silent side effect of this optimization.

## Out of Scope
- Any change to the Test phase's behavior — this session's investigation explicitly **rejected** a
  parallel "skip Test for docs-only tickets" candidate (directly falsified by
  `TCK-20260705-AI-AGENT-OVERVIEW-DOC`'s own legitimate, passing `test_validate_frontmatter.py` run on a
  docs-only change). Do not fold any Test-phase change into this ticket.
- Any change to `implement-epic.js` — delegates entirely to `implement-ticket.js` per child ticket, so
  this skip applies epic-wide automatically; do not duplicate logic there.
- Any change to how `implementation.behavior_changed` itself is computed or reported by the
  `implementer` agent — this ticket only adds a new consumer of the existing field.
- A Scope-time (pre-Implement) variant of this skip — explicitly rejected by the investigation as unsafe
  (see Scope's safety condition above); do not build it under any framing.

## Acceptance Criteria
- [ ] A genuinely docs-only ticket (`files_changed` = only `docs/`/`tickets/` paths,
      `behavior_changed: false`) → Parity's agent call is skipped entirely; `events.jsonl` shows a
      `skipped` status for the Parity phase seq.
- [ ] A scope-drift ticket — originally scoped as docs-only but whose Implement phase's
      `files_changed` actually includes a `src/` path — → Parity still runs in full. This is the
      single most important regression test for this ticket.
- [ ] A ticket where `files_changed` has no `src/` paths but `behavior_changed` is (surprisingly) `true`
      (e.g. a config/data file with real behavioral effect) → Parity still runs in full — both signals
      must agree before skipping, never either alone.
- [ ] No P0 parity ledger entry's `v2_evidence` path is ever touched by a skipped ticket (explicit check
      before allowing the skip to fire).
- [ ] A ticket that DOES need Parity (behavior changed or `src/` touched) sees zero change from today's
      existing flow.

## Related Tickets
- TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION (recommended this as "build now, narrowly", Candidate 3)
- TCK-20260705-WORKFLOW-SECURITY-GATE (sibling ticket, same investigation, independent — no shared code path)

## Related Docs
- stored_artifacts/TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION/investigation.md (Candidate 3's full
  trigger/change/feasibility/risk assessment, including the exact safety-condition reasoning)
- docs/parity_ledger/*.yaml (P0 entries whose `v2_evidence` paths must never go stale from a skip)

## Related Stored Artifacts
None yet — staging artifacts to be created under
`staging_artifacts/TCK-20260705-WORKFLOW-PARITY-SKIP/` when implementation begins.

## Related Code Areas
- .claude/workflows/implement-ticket.js (Parity phase, ~line 500-535)
- docs/parity_ledger/*.yaml (read-only reference for the P0-safeguard check)

## Assumptions / Open Questions
- Exact mechanism for the "no P0 entry's v2_evidence path intersects files_changed" safeguard (a full
  scan of all 8 parity ledger YAML files per run, vs. a cheaper pre-built index) — left for Plan to
  decide based on measured cost.

## Implementation Notes
Implemented per the approved plan (`staging_artifacts/TCK-20260705-WORKFLOW-PARITY-SKIP/plan.md`),
Steps 2-10 (Step 1 was a documented no-op — `.claude/skills/implement-ticket/SKILL.md` was not touched).

- Created `tools/parity_ledger_scan.py` with `find_p0_intersection(files_changed, ledger_dir=...)`,
  scanning exactly the 8 canonical parity-ledger files for P0 entries whose `v2_evidence` contains any
  changed-file path as a substring. Mirrors `tools/registry_query.py`'s style (pure functions, no CLI).
- Added `tests/tools/test_parity_ledger_scan.py` (3 tests: synthetic P0-intersection positive control,
  real-ledger negative control against `docs/ai/workflows.md`, canonical-8-only scan confirmation
  excluding `faction.yaml`). All 3 pass.
- Updated `meta.phases`'s `'Parity'` detail string in `.claude/workflows/implement-ticket.js` to describe
  the new conditional skip.
- Wrapped the existing Parity `agent(...)` call (`implement-ticket.js`, formerly lines 542-567) in an
  if/else keyed on `parityNoSrcChange = implementation.files_changed.every(f => !f.startsWith('src/'))`
  and `paritySkipEligible = parityNoSrcChange && !implementation.behavior_changed`. Both signals read
  post-Implement `implementation.*` fields only — never Scope-time/`ticketInfo` fields — so mid-run scope
  drift always forces the full agent call. When skip-eligible, a lazy P0 safeguard (only evaluated on
  this rare branch) runs `tools/parity_ledger_scan.py`'s `find_p0_intersection` via a `bash(...)` call
  (pseudocode instructing the orchestrating session to run it directly, not spawn an agent), passing each
  changed-file path as its own independently-quoted trailing `sys.argv` element (never an embedded
  `JSON.stringify(...)` blob inside the double-quoted `python3 -c "..."` string, which would corrupt the
  script via shell quote-stripping). Output uses the non-overlapping token pair `P0_INTERSECTION_FOUND` /
  `P0_NO_INTERSECTION` (confirmed `"P0_NO_INTERSECTION".includes("P0_INTERSECTION_FOUND")` is false). If
  the safeguard finds an intersection, `parityForceFullRun` is set and the full `agent(...)` call runs
  anyway; otherwise a `pushEvent('Parity', 'parity-updater', 'skipped', ...)` is recorded (4-arg shape,
  matching the existing hotfix-tier skip precedent) and the agent call is skipped entirely. The `else`
  branch's `agent(...)` call body is unchanged from the pre-change code (confirmed via `git diff` — only
  indentation changed).
- Updated 3 docs to describe the conditional skip: `docs/ai/workflows.md` (Parity row),
  `docs/ai/system_overview.md` (phase-chain sentence, preserving the "9 standing phases plus one
  conditional gate" framing — only the agent *call* is conditional, not the Parity *phase*),
  `docs/ai/ticket-lifecycle.md` (ASCII diagram annotation + new "Skipped when" prose paragraph).
- Ran `make knowledge-index-update` after the doc edits (exit 0, 4 files re-embedded).

Did NOT move this ticket to `tickets/done/`, did NOT migrate staging artifacts to `stored_artifacts/`,
did NOT touch `tickets/working_log.csv` — those are Finalize-phase actions outside this implementer
session's scope for this ticket.

## Test Summary
- `python3 -m pytest tests/tools/test_parity_ledger_scan.py -v` — 3/3 pass.
- `python3 -m pytest tests/tools/test_validate_frontmatter.py -v` — 64/64 pass (regression guard for the
  doc edits' frontmatter).
- `node -c .claude/workflows/implement-ticket.js` — exit 0.
- Manually executed the actual P0-safeguard Bash command (not just hand-traced) with a realistic
  multi-path `files_changed` list, including a path containing spaces — printed `P0_NO_INTERSECTION`
  cleanly both times, no Python traceback, confirming the shell-quoting fix works for real.
- Confirmed via `git diff`/`git status` that no out-of-scope files were touched: `docs/parity_ledger/`,
  `.claude/skills/implement-ticket/SKILL.md`, `.claude/workflows/implement-epic.js`,
  `tickets/working_log.csv`, and `tools/agent-monitoring/*.py` all show zero changes.

## Files Changed
- `.claude/workflows/implement-ticket.js` (modified — `meta.phases` Parity detail string; Parity phase
  body wrapped in skip/P0-safeguard logic)
- `tools/parity_ledger_scan.py` (new)
- `tests/tools/test_parity_ledger_scan.py` (new)
- `docs/ai/workflows.md` (modified — Parity row)
- `docs/ai/system_overview.md` (modified — phase-chain sentence)
- `docs/ai/ticket-lifecycle.md` (modified — diagram annotation + Parity prose paragraph)

## Completion Summary
Made the Parity phase's `parity-updater` agent call conditional in `implement-ticket.js` — skipped only
when both post-Implement, authoritative signals agree: `implementation.files_changed` has no `src/`
path AND `implementation.behavior_changed` is false. The check deliberately never reads Scope-time
`Related Code Areas` data, so a ticket that starts looking docs-only but ends up touching `src/` once
Implement actually runs (scope drift) always gets the full Parity pass, never the skip. A new
`tools/parity_ledger_scan.py` module provides a lazy, standalone-testable P0-ledger safeguard: before
the skip is allowed to fire, it checks whether any P0 entry across the 8 canonical parity-ledger files
already depends (via its `v2_evidence` text) on one of the changed files — if so, it forces the full
agent call instead of skipping. The safeguard is empirically inert today (no P0 entry currently cites a
non-`src/` path) but is implemented for real, not stubbed, since that invariant is a fact about the
ledger's current contents, not an enforced guarantee.

Architecture review caught one real, confirmed bug before implementation: the original design embedded
a raw JSON array of changed files directly inside a double-quoted `python3 -c "..."` shell string,
which the shell would corrupt by stripping the JSON's own embedded quotes — causing a Python
`NameError`/`SyntaxError` on every real invocation and making the safeguard silently fail open exactly
in the branch it exists to protect. Fixed by passing each changed path as its own independently-quoted
trailing shell argument (`sys.argv[1:]`) instead. The review also caught that the original plan proposed
adding a new `orchestratorBash` primitive to the shared `.claude/skills/implement-ticket/SKILL.md`
translation table — a file governing every future ticket's execution, out of this ticket's declared
scope — fixed by removing that step and using an inline JS comment instead, matching the sibling
Security-Review ticket's own precedent for documenting a call-site nuance without touching the shared
execution contract.

Updated `docs/ai/workflows.md`, `docs/ai/system_overview.md`, and `docs/ai/ticket-lifecycle.md` to
document the new conditional skip, preserving the existing "9 standing phases plus one conditional
gate" framing (Parity itself still always runs and is always logged — only its agent call is
conditional). No `src/` code, `docs/parity_ledger/*.yaml` content, `.claude/skills/implement-ticket/SKILL.md`,
or `implement-epic.js` was touched. This is the second of two tickets from
`TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION`'s "build now" recommendations — the sibling
`TCK-20260705-WORKFLOW-SECURITY-GATE` is already merged.
