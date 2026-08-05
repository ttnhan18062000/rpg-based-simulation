---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, agent-monitoring]
---

# Agent/Skill Definition Gap Audit — 2026-08-04

Evidence base for `TCK-20260804-SKILL-JS-PHASE-SYNC`, `TCK-20260804-CREATE-TICKETS-SKILL-SYNC`,
and a planner fact-verification ticket. Triggered by finding a real bug: `.claude/skills/
implement-ticket/SKILL.md` had drifted from `.claude/workflows/implement-ticket.js` in 7 ways,
none of which showed up in any failure metric (the gaps caused silent under-execution, not
errors). That precedent motivated two passes: (1) mine `agent-monitoring/*.jsonl` for real,
recurring failure signals that existing metrics *can* see, and (2) a targeted drift-comparison
pass on the other `.claude/skills/*`/`.claude/agents/*.md` files for the same silent-gap class
metrics *can't* see. Both passes found real, current gaps.

Every number below was independently re-queried directly against
`agent-monitoring-index/monitoring.db` (rebuilt first — it was 1.3% stale) for this document,
not copied from the investigating agent's report without verification.

## Part 1 — Data-evidenced findings

### Review-phase (architecture-reviewer, pre-Implement gate) failure rate is high and rising

Query: `events` table, `phase='Review'`, grouped by `strftime` month of `ts`, `status='failed'`
over `status IN ('ok','failed','skipped','blocked')` denominator.

| Month | Failed / Total | Rate |
|---|---|---|
| 2026-06 | 3 / 110 | 2.7% |
| 2026-07 | 50 / 257 | 19.5% |
| 2026-08 | 8 / 35 | 22.9% |
| **All** | **61 / 402** | **15.2%** |

The rate is rising month over month, not settling — this is not historical noise from an early
rollout period.

**Sample of 8 real Review failures** (read directly from `events.jsonl` evidence text, not
paraphrased from a summary): recurring theme is the planner asserting factual claims about
*existing* system behavior in `plan.md` that turn out to be wrong when checked against real
source — e.g. a claimed "repeat-fire-every-tick" behavior that doesn't match the actual code, a
claimed canonical-hash exclusion rule that's false, a missed `RolloutProfile` flag combination
the plan didn't account for, a payload field name (`rejection_count` vs. the real field `count`)
asserted incorrectly in an acceptance-criteria description.

**Root cause, confirmed by reading `.claude/agents/planner.md` (88 lines) directly**: zero
instruction anywhere in the file requiring the planner to verify a factual claim about current
code behavior against real source before writing it into `plan.md`. The one substring match for
"Verify:" is an unrelated per-step field label, not a directive about claim verification.

### Verify-phase (done-checker, DoD gate) failure rate is comparably high

| Month | Failed / Total | Rate |
|---|---|---|
| 2026-06 | 0 / 117 | 0.0% |
| 2026-07 | 61 / 278 | 21.9% |
| 2026-08 | 7 / 43 | 16.3% |
| **All** | **68 / 438** | **15.5%** |

**Sample of 8 real Verify failures**: dominated by implementer/Finalize hygiene misses, not
architecture problems — an unfilled `## Completion Summary` placeholder left as
`(filled during Finalize)`, missing entries in `## Files Changed`, uncleaned `data/runs/`
artifacts, unchecked acceptance-criteria checkboxes, stale ticket text left inconsistent with
what was actually implemented.

**Root cause, confirmed by reading `.claude/agents/implementer.md` directly**: zero mention of
`## Completion Summary` or `data/runs/` cleanup anywhere in the file. This guidance currently
lives only in `implement-ticket.js`'s per-call prompt text (a one-time reminder at Implement),
not in the implementer agent's own persistent definition — and the recurrence rate across many
independent runs suggests the prompt-only reminder isn't sufficient on its own.

Both phases dwarf every other phase's failure rate in the same query (Implement 2.1%, Investigate
1.8%, Test 0.8%, Scope ~1% — computed the same way, not shown in full table here).

## Part 2 — Drift-found (same class as the implement-ticket/SKILL.md bug, no failure signal)

### `create-tickets/SKILL.md` is missing a real orchestrator-run gate

`create-tickets.js:576-614` runs a tag-registry check (`tag_registry.check_tags_registered()`)
between Structure and Write that silently filters out (does not write) any task carrying an
unregistered tag, pushing a `blocked`-status event and logging remediation instructions.
`create-tickets.js:559-574` also silently drops duplicate-`short_scope` tasks via plain JS Set
logic. Neither behavior — nor any orchestrator-run-bash row in the phase-translation table at
all — appears anywhere in `.claude/skills/create-tickets/SKILL.md`.

Independently re-queried run counts by `workflow` value in `runs` table: `create-tickets` = 26
runs — the 3rd-most-used workflow after `implement-ticket` (697) and `implement-epic` (101),
confirming this isn't a rarely-exercised path.

### `implement-epic/SKILL.md` — checked, clean

Delegates to `implement-ticket/SKILL.md`'s translation table by reference rather than duplicating
it, so the sibling ticket's fix propagates automatically. No action needed.

No other `.claude/workflows/*.js` file has a corresponding hand-orchestration skill with
meaningful run volume in the data (the rest — `simq-audit`, etc. — have ≤1 run each) —
deprioritized, not checked in depth.

## Resulting tickets

- `TCK-20260804-SKILL-JS-PHASE-SYNC` (DONE, landed before this doc was written) — fixed the
  original 7-gap `implement-ticket/SKILL.md` drift that motivated this audit.
- `TCK-20260804-CREATE-TICKETS-SKILL-SYNC` — fixes the `create-tickets/SKILL.md` drift found in
  Part 2.
- A planner fact-verification ticket (standard tier, scoped separately — the fix needs to define
  *what* "verify before asserting" concretely means for the planner agent, not just state the
  requirement) — addresses Part 1's Review-failure finding.
- The implementer Completion-Summary/data-runs checklist gap (Part 1's Verify-failure finding) is
  folded into a hotfix alongside the planner ticket's scoping, since it's the same class of fix
  (add missing guidance to an agent's own persistent definition file) applied to a different
  agent.

**How to tell if these fixes worked**: re-run this same query (Review/Verify failure rate by
month) after each fix lands and has accumulated a few weeks of real runs. A real fix should show
the rate trending back down toward the 2026-06 baseline (Review 2.7%, Verify 0.0%), not just a
one-time drop. This reuses existing instrumentation (`generate_retro.py`'s gate-outcome
computation, and this doc's own query) — no new metric needed to verify these particular fixes.

## Update — TCK-20260804-AGENT-DEF-GAP-FIXES landed (2026-08-05)

Landed: `planner.md` fact-verification sub-instructions, `implementer.md` before-returning
checklist, and a root-cause parser fix (`done_checker_static.py`'s new `_is_none_section()` helper
now tolerates trailing rationale prose after "None."/"N/A" — e.g. "None. See note below" — while
still correctly detecting a real `docs/` bullet if one follows, avoiding the false-PASS risk a
looser prefix check alone would carry) — see
`stored_artifacts/TCK-20260804-AGENT-DEF-GAP-FIXES/plan.md` for exact text and reasoning.

**How to check if THIS fix worked**, using the same method as this ticket's own investigation
(`stored_artifacts/TCK-20260804-AGENT-DEF-GAP-FIXES/investigation.md`), not the original audit's
one-time monthly percentages:

1. **Immediate, non-deferred check (parser fix only):** re-run the Verify-failure count for the
   "Docs Requiring Update" none-phrase/trailing-prose failure mode specifically — query
   `agent-monitoring-index/monitoring.db` for `phase='Verify'`, `status='failed'` events since
   2026-08-05 whose evidence text mentions "Docs Requiring Update" or "none-phrase". Expected: 0
   going forward, immediately — this is a deterministic parser fix, not a behavior-change-dependent
   one, so it does not need weeks of accumulation to validate. (A separate, still-open `:line`-
   suffix bullet-format bug was found during this ticket's Plan phase — confirmed real via
   `TCK-20260804-EXPANSION-RATE-WIRING`'s own event log — but is out of this ticket's 3-occurrence-
   evidenced scope; flagged as a future-ticket candidate, not fixed here.)
2. **Deferred check (planner.md / implementer.md fixes — needs real accumulated runs):** re-run
   this investigation's exact query — `events` table, `phase IN ('Review','Verify')`,
   `status='failed'`, grouped by month — after several weeks of real runs post-2026-08-05. Compare
   against the fresh pre-fix baseline this ticket established (not the original audit's monthly
   percentages): 15 Review failures and 25 Verify failures in the 2026-07-20 to 2026-08-05 window.
   A working fix should show:
   - Review failures per equivalent-length window trending below 15, with the specific
     "wrong factual claim about existing code" / "schema-referencing-a-nonexistent-field" /
     "AC-vs-plan self-contradiction" sub-patterns specifically declining (classify manually by
     reading `summary` text, same method investigation.md used — do not swap to a coarser
     "any failure" metric).
   - Verify failures' AC-checkbox-miss (was 6), stale-Status-field (was 5), and
     Completion-Summary-gap (was 4) sub-patterns specifically declining.
   - **Not expected to move** (out of this ticket's scope, do not count as evidence against the
     fix if these don't improve): "Scope item silently not implemented" (1), "Undisclosed scope
     creep" (1), "Real substantive contradiction" (1) — these are different failure classes this
     ticket did not address.
3. **A same-day or single-week re-check is not a valid deferred-check result** for item 2 above —
   report "not enough data yet," not a false negative or false positive.
