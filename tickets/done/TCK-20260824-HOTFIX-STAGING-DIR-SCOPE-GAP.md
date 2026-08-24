---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260824-HOTFIX-STAGING-DIR-SCOPE-GAP
phase: done
date: 2026-08-24
tags: [ai, workflows, process-improvement, agent-monitoring]
---

# TCK-20260824-HOTFIX-STAGING-DIR-SCOPE-GAP

## Title
Make Scope phase's staging-directory creation tier-conditional (skip for hotfix)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`.claude/workflows/implement-ticket.js`'s Scope phase, in the "Create a new ticket" branch of the
ticket-scoper prompt (currently line 162), unconditionally instructs the agent to "Create the
staging directory: staging_artifacts/{ticket_id}/" — with no tier check. This runs for hotfix
tickets too, even though hotfix tickets never populate that directory: Investigate/Plan/Review
(the phases that write investigation.md/plan.md/test_plan.md into it) are all skipped for hotfix
tier per the pipeline's own tier-routing table. The directory is therefore created empty and stays
empty for the life of the hotfix ticket.

`done-checker`'s own DoD condition 9 ("Repo state is consistent" — `.claude/agents/done-checker.md`
line 123-124, "No leftover staging or temp files") then correctly flags that now-empty leftover
directory as a hygiene violation and BLOCKs the Verify phase. Finalize's own prompt text (line
~1453) already has a defensive cleanup instruction for exactly this case ("Hotfix: no staging
artifacts to move. Delete staging_artifacts/${tid}/ if it was accidentally created") — but Finalize
runs *after* Verify in the pipeline's phase order, so that cleanup instruction can never actually
run before done-checker already sees and blocks on the leftover directory. This is a 100%
reproducible self-inflicted Scope-vs-Verify contradiction, not incidental: confirmed 2/2
occurrences this week per `agent-monitoring/retro/RETRO-2026-W34.md` ("## Notes" → "1. What failed
most?"), both from hotfix tickets in the same session (`TCK-20260823-LIVE-TEST-API-KEY-AUTH`,
`TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-SHALLOW-CLONE-FALSE-POSITIVE`), each costing a full extra
BLOCKED → manual `rmdir` → re-verify round-trip to close.

Fix: make the Scope-phase instruction tier-conditional, using the exact same
`${tier !== 'hotfix' ? '...' : '...'}` ternary pattern already used elsewhere in this same file
(e.g. the Implement-phase prompt around line 750/766/818/1024, and the Finalize-phase prompt around
line 1452-1453) — only instruct creating `staging_artifacts/{ticket_id}/` when tier is not hotfix;
for hotfix tier, explicitly instruct the agent to skip that step.

## Scope
- Edit `.claude/workflows/implement-ticket.js`'s Scope-phase ticket-scoper prompt, "Create a new
  ticket for this request" branch (the template-string body currently spanning roughly lines
  128-172 — re-read the file directly at implementation time to confirm exact current line numbers,
  since concurrent work on this branch may have shifted them since this ticket was scoped).
- Replace the unconditional step 7 ("7. Create the staging directory:
  staging_artifacts/{ticket_id}/") with a tier-conditional instruction: create the directory only
  when tier is standard/epic; for hotfix tier, explicitly instruct the agent to skip creating it.
- Match the file's own existing hotfix-carve-out ternary idiom (`${tier !== 'hotfix' ? X : Y}`) for
  consistency with the rest of the file rather than inventing a new phrasing style.
- Verify the fix closes the loop: a fresh hotfix-tier Scope run should no longer create
  `staging_artifacts/{ticket_id}/` at all, so done-checker's condition 9 has nothing to flag.

## Out of Scope
- The "Load existing ticket" (resume) branch of the same prompt — it has no staging-dir-creation
  instruction today and must stay that way; do not add one.
- `TICKET_SCHEMA` or tier-inference logic itself — unrelated to this gap.
- Finalize's existing defensive cleanup instruction (~line 1453, "Hotfix: no staging artifacts to
  move. Delete staging_artifacts/${tid}/ if it was accidentally created") — leave it in place
  unchanged as a harmless backstop; do not remove it.
- The second, separate finding surfaced in the same retro note ("`CONFLICTS_DETECTED` treated as an
  unconditional hard stop even for non-blocking disclosure") — a distinct gate-design issue, not
  this ticket's scope; file separately if pursued.
- `done-checker`'s condition 9 logic itself (`.claude/agents/done-checker.md` / any script it
  might later gain) — the fix is at the source (Scope phase stops creating the directory), not at
  the consumer (Verify phase learning to tolerate an empty directory).
- `tools/gate_checks/done_checker_static.py`'s `check_staging_artifacts_complete` script check —
  confirmed during scoping that this script-checked condition already returns `NA` unconditionally
  for hotfix tier regardless of directory existence, so it was never the actual blocking condition;
  the real blocker is done-checker's separate agent-judgment condition 9 ("Repo state is
  consistent"), which is not script-checked. No change needed to this file.

## Acceptance Criteria
- Running the Scope phase for a request with `tier: hotfix` no longer creates
  `staging_artifacts/{ticket_id}/` on disk.
- Running the Scope phase for a request with `tier: standard` or `tier: epic` still creates
  `staging_artifacts/{ticket_id}/` exactly as before (no behavior change for non-hotfix tiers).
- The "Load existing ticket" (resume) branch's prompt text is unchanged (byte-for-byte, apart from
  incidental line-number shifts from the edit above).
- Finalize's existing cleanup instruction text (~line 1453) is unchanged.
- A subsequent hotfix-tier run through Verify no longer BLOCKs on done-checker condition 9 due to a
  leftover empty `staging_artifacts/{ticket_id}/` directory (verified by re-running or by tracing
  the new prompt text through the same code path that previously produced the 2 BLOCKED
  round-trips this week).

## Related Tickets
- TCK-20260823-LIVE-TEST-API-KEY-AUTH (done) — first occurrence this week; required manual `rmdir`
  + re-verify round-trip.
- TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-SHALLOW-CLONE-FALSE-POSITIVE (done) — second occurrence
  this week, same root cause.
- TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP (done) — same shape of fix (a retro-discovered,
  100%-reproducible workflow-prompt gap in `implement-ticket.js`, hotfix-tiered, `layer: ai`).
- TCK-20260805-SECURITY-REVIEW-HOTFIX-GAP (done) — another prior hotfix-tier gap in the same
  pipeline's tier-conditional prompt logic; useful precedent for the ternary-idiom fix shape.

## Related Docs
- `agent-monitoring/retro/RETRO-2026-W34.md` — "## Notes" → "1. What failed most?" — source of this
  finding (2/2 reproducible occurrences this week).
- `.claude/agents/done-checker.md` — DoD condition 9 ("Repo state is consistent" / "No leftover
  staging or temp files"), lines ~123-124, the consumer-side check that blocks on the leftover
  directory.
- `CLAUDE.md` (project instructions) — "Tier Routing" table and "Workflow Rule" → "Before Work"
  section (staging artifacts required standard/epic only, not hotfix).

## Related Stored Artifacts
None found covering this exact gap. Scanned `stored_artifacts/` for prior investigations touching
`implement-ticket.js`'s Scope phase or the `staging_artifacts/` lifecycle — no direct hit; closest
adjacent work is `stored_artifacts/TCK-20260705-GATE-DET-DONE-CHECKER/` (done-checker gate
determinism, different concern) and `stored_artifacts/TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH/`
(orchestrator bash-step conventions in the same file family).

## Related Code Areas
- `.claude/workflows/implement-ticket.js` (Scope phase ticket-scoper prompt, currently line 162;
  also the existing hotfix ternary precedents around lines 750, 766, 818, 1024, and 1452-1453)
- `.claude/agents/ticket-scoper.md` (confirmed during scoping: carries no independent
  staging-directory-creation instruction of its own — the instruction lives solely in
  `implement-ticket.js`'s inline prompt text; no edit expected here, listed for completeness)
- `.claude/agents/done-checker.md` (condition 9 definition — read-only reference, not edited by
  this ticket)
- `tools/gate_checks/done_checker_static.py` (`check_staging_artifacts_complete`, confirmed
  read-only — already correctly returns `NA` for hotfix tier)

## Assumptions / Open Questions
- Assumes `layer: ai` is correct for this ticket (Claude agent/orchestration tooling, per
  `registries/layer_registry.jsonl`'s own note distinguishing it from gameplay cognition) — matches
  the layer used by every other `implement-ticket.js`/workflow-prompt-gap ticket found during
  scoping (TCK-20260805-SECURITY-REVIEW-HOTFIX-GAP, TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP,
  TCK-20260712-WORKFLOW-FRICTION-FIXES, TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT). If wrong,
  the whole scope stays valid — only the frontmatter `layer:` value would need correcting.
- Assumes Priority P2 is correct (real, reproducible process friction with a known, cheap manual
  workaround already in use — not a production/user-facing defect, not blocking any in-flight
  ticket). If this is judged more urgent (e.g. because it's costing a full BLOCKED round-trip on
  every single hotfix ticket going forward, not just the 2 already hit), P1 would also be
  defensible; P2 was chosen per the request's explicit framing.
- Assumes the exact line numbers cited here (162, 750/766/818/1024, 1452-1453) may drift before
  implementation begins, since this is a shared, actively-edited file — implementer must re-read
  the file directly rather than trust these line numbers as literal patch targets.
- Assumes no change is needed to `done_checker_static.py` — confirmed during scoping that its
  `check_staging_artifacts_complete` already returns `NA` unconditionally for hotfix tier
  regardless of directory existence, so the actual blocking condition is done-checker's separate,
  non-script-checked agent-judgment condition 9 ("Repo state is consistent"). If a future change
  ever makes that agent-judgment condition script-checkable, this ticket's fix (stopping the
  directory from being created at all) still fully resolves the gap at the source, independent of
  how condition 9 itself is implemented.
- This ticket's own Scope phase ran under the pre-fix, unconditional-creation prompt (the fix
  wasn't live yet), so it created `staging_artifacts/TCK-20260824-HOTFIX-STAGING-DIR-SCOPE-GAP/`
  itself — the exact empty leftover this ticket's own fix now prevents for every hotfix ticket
  going forward. Expected and harmless, not a defect in the fix; removed via `rmdir` before this
  ticket closes, same one-time manual cleanup this fix eliminates for all future hotfix tickets.

## Implementation Notes
Edited `.claude/workflows/implement-ticket.js`, "Create a new ticket for this request" branch of
the Scope-phase ticket-scoper prompt (was line 162, the lone `7. Create the staging directory:
staging_artifacts/{ticket_id}/` line). Replaced it with a conditional instruction that branches on
the Tier the agent itself infers in step 6 of the same prompt.

Tier-availability resolution: read the surrounding ~230 lines before editing. The JS `const tier =
tierOverride || ticketInfo.tier || 'standard'` (line 219) is assigned only *after* this `agent()`
call (lines 97-174) resolves — `ticketInfo.tier` is literally the value the ticket-scoper agent
returns from having inferred it in step 6 of this same prompt. So a JS `${tier !== 'hotfix' ? ... :
...}` template-literal ternary (the pattern used later in the file, e.g. lines 750, 1024, 1452,
where `tier` is already assigned) is not available in this branch — referencing it here would hit
the JS temporal-dead-zone (ReferenceError) since `const tier` isn't declared yet at that point in
the file's top-level execution order. The only tier signal that exists at this point in the prompt
is the inference the agent is instructed to make in step 6 ("Tier (infer from request:
hotfix/standard/epic)"). Rewrote step 7 as plain conditional prose telling the agent: if the Tier
it just inferred in step 6 is hotfix, skip creating the directory entirely; otherwise (standard or
epic) create it as before. This is prose-level conditionality inside the template string (not a JS
ternary), which correctly reflects that the branch decision happens inside the agent's own
reasoning, not in the orchestrator's JS.

Left the "Load existing ticket" (resume) branch (lines 99-127) untouched — confirmed it still has
no staging-dir-creation instruction. Left Finalize's defensive cleanup instruction (line
1452-1453, "Hotfix: no staging artifacts to move. Delete staging_artifacts/${tid}/ if it was
accidentally created") untouched as a harmless backstop. Left TICKET_SCHEMA and tier-inference
logic (line 219 and surrounding) untouched. Ran `node --check .claude/workflows/implement-ticket.js`
to confirm the file still parses after the edit.

## Test Summary
No automated test exists for this workflow-prompt-text file (it is JS template-string prose
interpreted by the agent runtime, not directly unit-testable code). Verification performed:
`node --check .claude/workflows/implement-ticket.js` confirms valid JS syntax post-edit. Manually
traced that the "Create a new ticket" branch's step 7 now instructs skipping directory creation
when the agent's own step-6 tier inference is hotfix, and creating it otherwise — matching the
acceptance criteria. Confirmed via grep that the resume branch and the Finalize cleanup line are
byte-identical to their pre-edit state (only line numbers shifted due to the step-7 line growing).

## Files Changed
- `.claude/workflows/implement-ticket.js` (Scope-phase ticket-scoper prompt, "Create a new ticket"
  branch, step 7 — now tier-conditional)
- `tickets/inprogress/TCK-20260824-HOTFIX-STAGING-DIR-SCOPE-GAP.md` (this file — Implementation
  Notes, Test Summary, Files Changed, Completion Summary, Status)

## Completion Summary
Made the Scope phase's "Create a new ticket" prompt skip `staging_artifacts/{ticket_id}/` creation
entirely for hotfix-tier tickets, since it's the agent's own step-6 tier inference (not a JS
variable, which isn't assigned until after this agent call returns) that determines the branch.
Standard/epic tickets are unaffected — the directory is still created exactly as before. This
closes the Scope-vs-Verify contradiction where done-checker's condition 9 correctly flagged the
resulting empty leftover directory as a hygiene violation on every hotfix ticket.
