---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260705-SIX-SKILLS-INVESTIGATION
artifact_type: plan
tags: [skills, process-improvement, investigation]
---

# Implementation Plan — TCK-20260705-SIX-SKILLS-INVESTIGATION

## Summary

This is an investigation-only ticket with no code change. `investigation.md` already produced a
per-skill verdict for all 6 skills (`test-driven-development`, `python-testing-patterns`,
`backend-testing`, `architecture`, `brainstorming`, `doc-coauthoring`), each backed by reproducible
counts — independently re-verified in this session by re-running every script in `test_plan.md`
verbatim: 41 total Skill invocations (6 target skills at exactly 0), 281 `tests/` edits, 9
`docs/architecture/` edits, 669 `docs/` edits overall, 5 `conftest.py` files, 303 files with existing
fixture/mock/parametrize precedent, 36 `AskUserQuestion` calls — every number matched exactly.

**Verdict summary**: all 6 skills scored **correctly redundant** — none is a clean "genuine gap."
`doc-coauthoring` is flagged as the closest thing to a soft gap (its ~13% free-form `docs/plans/` +
`docs/architecture/` slice is topically close to its target, but produced via single-pass
agent-autonomous authorship, not the skill's assumed human-interactive co-writing mode) but is not
scored as a gap requiring wiring.

Because zero of the 6 are confirmed genuine gaps, this ticket's Acceptance Criteria are satisfied by
recording the verdicts themselves — there is no wiring to hand off to `TCK-20260705-TAG-SKILL-SUGGEST`
or a follow-on ticket. The `doc-coauthoring` soft-gap is recorded as a **named-only watch item** (not a
ticket) for whoever eventually extends the tag-based mechanism, consistent with how
`TCK-20260705-WORKING-LOG-BACKFILL` recorded (not created) its own follow-up recommendations.

## Steps

### Step 1 — Correct/finalize the ticket's own text
- **Files:** `tickets/inprogress/TCK-20260705-SIX-SKILLS-INVESTIGATION.md`.
- **Do:**
  - Fill `Implementation Notes` with the per-skill verdict table (copied/summarized from
    `investigation.md`), citing the reproducible counts.
  - Amend all four Acceptance Criteria with their actual disposition (verdict-per-skill delivered;
    Testing/Architecture Rule overlap resolved per-skill, not as one blanket answer; docs/ composition
    resolved at 86%/13%; zero wiring performed, zero genuine gaps found so nothing to hand off).
  - Fill `Test Summary` with the independent re-verification results (all counts matched exactly on
    re-run).
  - Fill `Files Changed`: this ticket file only, plus `stored_artifacts/TCK-20260705-SIX-SKILLS-INVESTIGATION/*`.
  - Fill `Completion Summary`: state plainly that all 6 skills are correctly redundant, none requires
    wiring, `doc-coauthoring` is the closest soft gap and is recorded as a watch item only.
- **Do NOT touch:** `CLAUDE.md`, any `.claude/skills/*/SKILL.md` file, any other ticket file.
- **Verify:** manual diff read; confirm no wiring language leaks into Completion Summary implying a
  change was made to CLAUDE.md or a skill file.

### Step 2 — Record (not create) the doc-coauthoring watch item
- **Files:** `tickets/inprogress/TCK-20260705-SIX-SKILLS-INVESTIGATION.md` (`Related Tickets` section
  only).
- **Do:** Name the watch item explicitly enough to scope later, without creating a ticket file for it:
  "`doc-coauthoring` soft-gap: ~13% of `docs/` edits (`docs/plans/`, `docs/architecture/`) are
  free-form/proposal-shaped but agent-authored rather than human-co-written; revisit only if
  `docs/plans/` reader-quality issues surface, and only via the tag-based mechanism once
  `TCK-20260705-TAG-SKILL-SUGGEST` lands — not as a standalone `CLAUDE.md` row."
- **Do NOT:** create a new ticket file, do NOT wire anything into `CLAUDE.md`.
- **Verify:** `Related Tickets` section names the watch item; no ticket file created for it.

### Step 3 — Cleanup pass (Definition of Done housekeeping)
- **Files:** `data/runs/*`, `reports/release_proof/*` if present.
- **Do:** `rm -rf data/runs/* reports/release_proof/*` (expected no-op — this ticket generates no
  simulation run data).
- **Verify:** `git status` shows no stray untracked run artifacts.

### Step 4 — Append working_log.csv row + move to done + migrate staging artifacts
- Standard Finalize steps: append one row to `tickets/working_log.csv`, move ticket to
  `tickets/done/`, migrate `staging_artifacts/TCK-20260705-SIX-SKILLS-INVESTIGATION/` to
  `stored_artifacts/`.
- **Verify:** `git diff --stat tickets/working_log.csv` shows exactly `1 insertion(+), 0 deletions(-)`.

## Scope Guards

- No edit to `CLAUDE.md`, any `.claude/skills/*/SKILL.md` file, or any other ticket.
- No new ticket file created for the `doc-coauthoring` watch item — name only.
- No re-litigation of the 3 already-wired skills from `TCK-20260704-SKILL-TRIGGER-COVERAGE`.

## Acceptance Criteria Map

| AC | Original wording | Disposition | Verified by |
|---|---|---|---|
| AC1 | Each of the 6 skills has a documented verdict with cited evidence | Satisfied — `investigation.md`'s Per-Skill Verdict Table, all counts independently re-verified this session | Direct re-run of every script in `test_plan.md`; all numbers matched exactly |
| AC2 | Testing Rule / Architecture Rule overlap explicitly resolved | Satisfied — resolved per-skill (not blanket): TDD is divergent (pipeline runs Implement before Test), python-testing-patterns/backend-testing redundant via in-repo precedent not rule-text, Architecture Rule covers different subject matter than ADR-authoring (redundancy is precedent-driven, not rule-driven) | `investigation.md` Per-Skill Verdict Table, CLAUDE.md overlap column |
| AC3 | 659-docs-edits composition question resolved | Satisfied — 86% mandated/ticket-workflow-internal vs. 13% free-form, with named subdirectory breakdown and 3 sampled files read directly | `investigation.md`'s docs/ subdirectory categorization table |
| AC4 | No skill wiring implemented; confirmed gaps handed off | Satisfied — zero genuine gaps found, so nothing to hand off for wiring; `doc-coauthoring`'s soft-gap recorded as a named watch item only (Step 2) | Step 2's `Related Tickets` entry; no CLAUDE.md/SKILL.md diff |

## Anti-Drift Notes

- Do not let "all correctly redundant" read as "nothing worth recording" — the reasoning per skill
  (especially TDD's *active pipeline conflict*, not mere redundancy, and doc-coauthoring's
  authorship-mode mismatch) is exactly the kind of nuance a future reader needs; it must survive in the
  ticket's own Completion Summary, not only in `investigation.md`.
- Do not create a ticket file for the `doc-coauthoring` watch item — that would contradict AC4's "no
  wiring" intent and this ticket's own explicit sequencing deferral to `TAG-SKILL-SUGGEST`.
- If re-verification in Step 1 shows any count has drifted materially from `investigation.md`'s cited
  numbers (beyond a small delta explainable by new sessions since 2026-07-05), stop and re-investigate
  rather than silently citing stale numbers in the ticket text.
