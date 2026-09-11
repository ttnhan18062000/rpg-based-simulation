---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260804-SKILL-JS-PHASE-SYNC
phase: done
date: 2026-08-04
tags: [skills, workflows]
---

# TCK-20260804-SKILL-JS-PHASE-SYNC

## Title
Sync .claude/skills/implement-ticket/SKILL.md's phase-translation table with the real implement-ticket.js (missing Document-Update phase, missing doc-staleness gate, missing shadow-packet probe)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
While investigating why `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`'s shadow-packet evidence count had stalled at 12 events/11 run_ids despite two full standard-tier tickets running today, direct comparison of `.claude/skills/implement-ticket/SKILL.md` (what a hand-orchestrating agent actually follows, since the real `Workflow` tool is unavailable in this harness) against `.claude/workflows/implement-ticket.js` (the authoritative source) found SKILL.md is stale in three concrete ways:

1. **Shadow-packet probe missing.** `implement-ticket.js:560-588`'s advisory, fail-open bash block (gated `SHADOW_CONTEXT_PACKET_ENABLED=1`, calls `wrap_context_packet_assembly()` with an empty candidate set, negative-seq collision-safe) runs at the end of the real Investigate phase. SKILL.md's phase-translation table has no row for it, so every hand-orchestrated Investigate phase silently skips it — confirmed directly: this session ran 2 full standard-tier tickets today with real Investigate phases and the shadow-packet event count did not move.
2. **Document-Update phase missing from the pipeline entirely.** `implement-ticket.js:774-838` runs Document-Update unconditionally, every tier (including hotfix), positioned between Implement and Architecture-Verify — its own comment states this ordering is load-bearing ("merging this phase's own reported docs into that gate's input is the entire point"). SKILL.md's `## Pipeline (standard tier)` list has no Document-Update row at all.
3. **`doc_staleness_check.py` gate missing.** `implement-ticket.js:839-905` runs this deterministic, potentially-blocking gate (`DOC_STALENESS_BLOCKED`) immediately after Document-Update, folding its result into the Implement phase's `pushEvent`. It is a real, hard-blocking gate per its own docstring (`tools/gate_checks/doc_staleness_check.py`) — not advisory. SKILL.md has no step for it.

A fuller read-through of the rest of the JS (Test through Finalize) found two more gaps of the same class:

4. **Post-Test `data/runs`/`reports/release_proof` cleanup checkpoint missing** (`implement-ticket.js:1047-1090`) — an orchestrator-run bash call immediately after Test, before Parity. Low practical impact (both dirs were independently confirmed clean during today's manual checks) but the explicit step is absent from SKILL.md.
5. **Post-Finalize knowledge-index refresh missing** (`implement-ticket.js:1471-1490`) — runs `make knowledge-index-update` automatically whenever `git status --porcelain -- docs/` is non-empty, per CLAUDE.md's own "After Work" rule. This one **was** a real, live gap: today's two tickets modified real `docs/` files and the index was never refreshed during either Finalize. Already fixed retroactively (ran `make knowledge-index-update` directly — "Incremental update complete: 6635 chunks total (8 files re-embedded...)" — before scoping this ticket) — no further action needed on the already-closed tickets, but the step must be added to SKILL.md so it isn't missed again.
6. **Parity's post-agent cross-reference gate** (`implement-ticket.js:1184-1219`, can hard-block with `PARITY_INCOMPLETE`) and its pre-agent `expected_subsystems_for_files` hint injection (`:1147-1154`) are also absent from SKILL.md. Retroactively confirmed no-op for today's two tickets (`expected_subsystems_for_files` returns `{}` for `tools/`-only changes — the mapping only covers `src/` paths — so `cross_reference_touched` returns `[]`, no failures).
7. Two Finalize-tail advisory-only checks (`check_monitoring_write_recorded`, `check_tag_drift`, both non-blocking, `implement-ticket.js:1502-1548`) are also undocumented in SKILL.md — lowest priority of the findings here since they can never block and are pure "loud warning" value-adds.

**Retroactive impact check (already performed, no further action needed on today's 2 closed tickets):** re-ran `check_doc_staleness()` and `cross_reference_touched()` directly against both of today's completed tickets' real `files_changed` lists — both gates PASS/no-op trivially (neither ticket touched `src/`, `config/`, or `.claude/workflows/*.js`, only `tools/`/`tests/`/`docs/`). `make knowledge-index-update` has been run retroactively to close the one gap that was real (stale search index). Document-Update made zero edits on both of today's tickets ("no additional staleness found"), so running it after Architecture-Verify instead of before had no material effect this session — but the ordering was wrong relative to the authoritative JS and must not be relied on to stay harmless in future tickets where Document-Update does make edits.

## Scope
- Add a Document-Update row to SKILL.md's `## Pipeline (standard tier)` list, positioned between Implement and Architecture-Verify (matching `implement-ticket.js:774` vs `:915`), explicitly noting it runs unconditionally for every tier including hotfix (per the JS's own comment at line 775).
- Add a step describing the `doc_staleness_check.py` gate, positioned immediately after Document-Update and before Architecture-Verify, as a `Gate condition` per the existing phase-translation table row — including that a FAIL returns `DOC_STALENESS_BLOCKED` and stops the workflow.
- Add a step to the Investigate phase description (or a note near it) describing the shadow-packet call site: run the exact bash block from `implement-ticket.js:560-588` (gated `SHADOW_CONTEXT_PACKET_ENABLED=1`, fail-open, using the real `tid` as `run_id`) after producing `investigation.md`/`test_plan.md`.
- Add a post-Test cleanup step (data/runs, reports/release_proof) between Test and Parity.
- Add the Parity cross-reference gate (`PARITY_INCOMPLETE`, hard-blocking) and its static hint-injection step.
- Add the post-Finalize knowledge-index refresh step (`make knowledge-index-update`, run whenever `docs/` changed), citing CLAUDE.md's existing "After Work" rule as the source of truth this step implements.
- Add the two Finalize-tail advisory checks (monitoring-write verification, tag-drift) as optional/non-blocking notes.
- Re-number the pipeline list to reflect the corrected phase count and ordering.
- Full read-through of `implement-ticket.js` already completed during Investigate (this ticket) — confirmed the 7 gaps above are the complete set; no further drift found in Scope/Review/Security-Review sections.

## Out of Scope
- Changing `implement-ticket.js` itself — it is already correct; this ticket only fixes the hand-orchestration translation doc that describes it.
- Re-opening or re-verifying either of today's two already-closed tickets — the retroactive impact check above already confirms no substantive gap.
- Building a mechanism to auto-detect SKILL.md/JS drift in the future (e.g. a test asserting phase-name parity) — worth considering as a follow-up, but a new detection mechanism is a larger scope than this hotfix's "fix the known drift" intent.

## Acceptance Criteria
- [ ] SKILL.md's pipeline list includes Document-Update, correctly positioned (before Architecture-Verify, present for hotfix too).
- [ ] SKILL.md describes the `doc_staleness_check.py` gate and its `DOC_STALENESS_BLOCKED` failure mode.
- [ ] SKILL.md describes the shadow-packet call-site step as part of Investigate, with the exact env-var gate and fail-open behavior preserved (never presented as a hard requirement — must stay advisory/optional exactly as the JS implements it).
- [ ] SKILL.md describes the post-Test cleanup step, the Parity cross-reference gate (+ hint injection), the post-Finalize knowledge-index refresh, and the two Finalize-tail advisory checks.
- [ ] A full read-through comparison confirms no other phase-list drift between SKILL.md and the current `implement-ticket.js`.
- [ ] No change to `implement-ticket.js` itself.
- [ ] `make knowledge-index-update` retroactively run for today's two already-closed tickets (already done during Investigate; Test phase re-confirms no new docs/ drift since).

## Related Tickets
- TCK-20260729-SHADOW-PACKET-CALL-SITE (built the shadow-packet call site being newly documented here)
- TCK-20260803-DOC-UPDATER-EPIC (added the Document-Update phase to the real JS)
- TCK-20260711-DOC-STALENESS-GATE-CHECK / TCK-20260720-GATE-CHECK-WIRING-DECISIONS (built and wired the doc-staleness gate)
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC (backlogged epic whose stalled evidence count surfaced this gap)

## Related Docs
- `.claude/skills/implement-ticket/SKILL.md`
- `docs/architecture/doc_updater_agent.md`

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `.claude/skills/implement-ticket/SKILL.md`
- `.claude/workflows/implement-ticket.js` (read-only reference, not modified)

## Assumptions / Open Questions
None — the fix is a direct transcription of already-shipped, already-reviewed JS behavior into the translation doc; no new design decision is required.

## Implementation Notes
Rewrote `.claude/skills/implement-ticket/SKILL.md`'s `## Action` and `## Pipeline (standard tier)`
sections to reflect all 7 gaps found during the full read-through of `implement-ticket.js`:

1. Added a new phase-translation-table row for orchestrator-run `await bash(...)` calls (no
   `agent()` wrapper) — explicit instruction to run these directly, never delegate to a sub-agent
   prompt, citing the JS's own repeated warnings that bash instructions embedded only in agent
   prose have been observed to silently not execute.
2. Investigate (step 2): added the shadow context-packet call-site description, citing the exact
   line range, preserving its advisory/opt-in/fail-open nature verbatim (never presented as
   required).
3. New step 6, Document-Update: added as its own numbered pipeline step, correctly positioned
   between Implement and Architecture-Verify (not after, as this session's own hand-orchestration
   had been doing), with the ordering rationale stated explicitly (doc-updater's reported paths
   feed the very next gate).
4. New step 7, doc-staleness gate: added with its exact CLI invocation shape, FAIL/ADVISORY
   semantics, and `DOC_STALENESS_BLOCKED` hard-block behavior.
5. Step 9 (Test): added the post-Test `data/runs`/`reports/release_proof` cleanup checkpoint.
6. Step 10 (Parity): added both the pre-agent `expected_subsystems_for_files` hint injection and
   the post-agent cross-reference gate (`PARITY_INCOMPLETE` hard block).
7. Step 13 (Finalize): added the post-Finalize `make knowledge-index-update` step (fail-open,
   gated on `docs/` having changed) and the two Finalize-tail advisory-only checks.

Renumbered the full pipeline list 0-13 (was 0-11) to keep it sequential. Added a top-of-Action
note stating the JS is authoritative and this file can drift from it — pointing future readers
at this exact ticket as the precedent for what to do when that happens (fix SKILL.md to match,
never the reverse).

**Retroactive fixes applied directly (not part of the SKILL.md diff, but real corrective actions
for today's two already-closed tickets), performed before Implement began:**
- Ran `check_doc_staleness()` and `cross_reference_touched()` directly against both
  TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC's and TCK-20260804-EXPANSION-RATE-WIRING's real
  `files_changed` lists — both gates PASS/no-op (neither ticket touched `src/`/`config/`/
  `.claude/workflows/*.js`; the parity subsystem mapping only covers `src/` paths). No corrective
  action needed on those tickets themselves.
- Ran `make knowledge-index-update` directly (was genuinely stale — "Incremental update complete:
  6635 chunks total, 8 files re-embedded, 2376 from cache").

No change was made to `implement-ticket.js` itself, per Out of Scope.

## Test Summary
No pytest suite covers `.claude/skills/*.md` content (pure prose instructions, not executable
code) — per the JS's own hotfix instruction, "confirm the targeted behavior is tested" was
satisfied via direct verification instead:
- Re-read the final `SKILL.md` in full; confirmed the pipeline table renders as a coherent,
  sequentially-numbered 0-13 list (`awk`-verified 4-column table structure holds for all 10 rows;
  `grep`-verified numbered-list sequencing has no gaps/dupes).
- Cross-checked every new `implement-ticket.js:<line-range>` citation in the new prose against a
  fresh direct read of those exact ranges in the real file — all accurate (Document-Update
  774-838, doc-staleness gate 839-905, post-Test cleanup 1047-1090, Parity hint injection
  1147-1154, Parity cross-reference gate 1184-1219, post-Finalize index refresh 1471-1490,
  Finalize-tail advisories 1502-1548, shadow-packet call site 560-588 — all previously verified
  during this ticket's own investigation before writing).
- Dogfooded 2 of the newly-documented steps for real, against this very ticket's own
  `files_changed`: `python3 tools/gate_checks/doc_staleness_check.py True
  ".claude/skills/implement-ticket/SKILL.md"` → PASS (0 flagged paths, `.claude/skills/` is not
  `.claude/workflows/*.js`). `cross_reference_touched(['.claude/skills/implement-ticket/SKILL.md'],
  [])` → `[]` (no failures) — both steps behave exactly as newly documented.

## Files Changed
- `.claude/skills/implement-ticket/SKILL.md` — added phase-translation-table row for
  orchestrator-run bash calls; added Document-Update, doc-staleness gate, post-Test cleanup,
  Parity hint-injection/cross-reference-gate, and post-Finalize index-refresh/advisory-check
  steps to the pipeline list; renumbered 0-13; added shadow-packet call-site description to
  Investigate.

## Completion Summary
Found while diagnosing why `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`'s shadow-packet
evidence had stalled: `.claude/skills/implement-ticket/SKILL.md` — the doc a hand-orchestrating
agent actually follows, since the real `Workflow` tool is unavailable in this harness — had
drifted from the authoritative `.claude/workflows/implement-ticket.js` in 7 concrete ways: a
missing shadow-packet call-site step (the original finding), a missing Document-Update phase
row (and this session had genuinely been running it in the wrong position, after
Architecture-Verify instead of before), a missing doc-staleness gate, a missing post-Test
cleanup checkpoint, a missing Parity cross-reference gate, and a missing post-Finalize
knowledge-index-refresh step. Rewrote SKILL.md's pipeline section to describe all 7, citing
exact JS line ranges for each, independently re-verified by Architecture review-equivalent
re-reads and by Verify's own independent citation check. Retroactively confirmed no actual harm
to this session's own two already-closed tickets (doc-staleness and parity cross-reference gates
both pass/no-op trivially for their real files_changed), and retroactively ran
`make knowledge-index-update` (was genuinely stale — 8 files re-embedded). Parity phase made an
explicit, reasoned judgment call that this class of change — agent-instruction prose, not
executable source — falls outside the parity ledger's scope; no entry added. Dogfooded 2 of the
newly-documented steps directly against this ticket's own real files_changed as its "test."
Hotfix pipeline: Scope → Implement → Document-Update (no updates needed) → doc-staleness gate
(PASS) → Test (dogfooded, no pytest applicable) → Parity (no entry needed, reasoned) → Parity
cross-reference gate (no failures) → Verify (READY TO CLOSE, 11 PASS / 2 N/A / 0 FAIL) →
Finalize. No change made to `implement-ticket.js` itself.
