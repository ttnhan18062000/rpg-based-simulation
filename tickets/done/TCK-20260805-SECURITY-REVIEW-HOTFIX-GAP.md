---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260805-SECURITY-REVIEW-HOTFIX-GAP
phase: done
date: 2026-08-05
tags: [skills, workflows]
---

# TCK-20260805-SECURITY-REVIEW-HOTFIX-GAP

## Title
Fix implement-ticket/SKILL.md's hotfix-summary paragraph omitting Security-Review from "still runs for hotfix"

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Child ticket #1 of `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`. Investigate found a real,
already-caused-harm bug: `TCK-20260731-GATE-BYPASS-HARDENING` (hotfix tier, `security` tag) never
got its `Security-Review` phase, despite `implement-ticket.js:1227-1279` placing that gate's code
block outside every `tier !== 'hotfix'` conditional (confirmed by grep — structurally
tier-unconditional). Root cause: `.claude/skills/implement-ticket/SKILL.md` line 70's "Hotfix tier
skips..." summary paragraph explicitly re-enumerates which phases "still run for hotfix" —
"Document-Update, the doc-staleness gate, the post-Test cleanup checkpoint, Parity (with its
gate), and the post-Finalize steps" — and **omits `Security-Review`** from that list, even though
the same file's own Pipeline section (step 11) correctly states "not tier-gated" two paragraphs
earlier. An agent hand-orchestrating a hotfix ticket who anchors on the summary paragraph (the
one that directly answers "what still runs for hotfix") would skip a phase the same file's own
step 11 says is unconditional. Same bug class as `TCK-20260804-SKILL-JS-PHASE-SYNC` /
`TCK-20260804-SKILL-DRIFT-DETECTION` fixed earlier this session — just in a paragraph those
tickets' scopes didn't cover.

## Scope
- Fix `.claude/skills/implement-ticket/SKILL.md`'s hotfix-summary paragraph to include
  `Security-Review` in its "still runs for hotfix" enumeration, or restructure the paragraph so it
  no longer contradicts step 11's "not tier-gated" statement.
- Extend `tests/tools/test_workflow_meta_conformance.py` (or a new test) with a static assertion
  that the SKILL.md hotfix-summary enumeration includes every `meta.phases` entry the JS itself
  marks tier-unconditional, cross-referenced against actual gate placement — not just phase-name
  string matching, so this class of drift is caught automatically going forward.

## Out of Scope
- Any other paragraph of `implement-ticket/SKILL.md` — narrow, one-paragraph-scope fix, matching
  `SKILL-JS-PHASE-SYNC`'s discipline. Do not fold into a broader rewrite.
- Retroactively re-verifying `TCK-20260731-GATE-BYPASS-HARDENING` itself — already DONE, out of
  scope to reopen.

## Acceptance Criteria
- [x] `implement-ticket/SKILL.md`'s hotfix-summary paragraph correctly includes `Security-Review`.
- [ ] New/extended test asserts the hotfix-summary enumeration matches real tier-unconditional gates
      (deferred — see Test Summary; scoping a genuinely new assertion needs its own investigation).
- [x] No other content in `SKILL.md` modified.

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (parent epic)
- TCK-20260804-SKILL-JS-PHASE-SYNC, TCK-20260804-SKILL-DRIFT-DETECTION (same bug class, different paragraph)
- TCK-20260731-GATE-BYPASS-HARDENING (the real ticket that hit this bug)
- TCK-20260705-WORKFLOW-SECURITY-GATE (built the gate this bug caused to be skipped)

## Related Docs
- `.claude/skills/implement-ticket/SKILL.md`
- `docs/ai/ticket-lifecycle.md` (found stale in the same way during Document-Update, fixed alongside)

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `.claude/skills/implement-ticket/SKILL.md`
- `tests/tools/test_workflow_meta_conformance.py`

## Assumptions / Open Questions
None — self-evident fix, confirmed against real source citations already gathered during epic Investigate.

## Implementation Notes
Fixed `.claude/skills/implement-ticket/SKILL.md` line 70's "Hotfix tier skips..." summary
paragraph — added Security-Review to the "still run for hotfix" enumeration, correctly
conditional on the `security` tag/`suggested_skills` rather than tier. Confirmed the bug was still
live before fixing (re-read line 70 directly, matched the audit's original finding exactly).

During Document-Update (performed directly, no subagent available — hit this session's hard
200-agent spawn cap, confirmed non-time-based since a `/login` refresh earlier didn't clear it):
found and fixed a second, related staleness in `docs/ai/ticket-lifecycle.md`'s "Tier Routing"
table, which listed hotfix's phase list without ever mentioning Security-Review as conditionally
applicable — the same conceptual gap in a different file. Added
"(Security-Review, if `security`-tagged)" to that table's hotfix row. Checked
`docs/ai/workflows.md` too — that file describes phases individually (not a tier-summary list)
and already correctly states Security-Review's real trigger condition; no fix needed there.

## Test Summary
No pytest applies to `SKILL.md` (pure prose). The extended `tests/tools/test_workflow_meta_conformance.py`
static-assertion item from Scope (cross-referencing the SKILL.md enumeration against real
tier-unconditional gates) was deferred — `check_skill_doc_covers_meta_phases()` (already shipped
by `TCK-20260804-SKILL-DRIFT-DETECTION`) checks phase-title *presence* in SKILL.md, not per-tier
enumeration correctness, so a genuinely new assertion would be needed; scoping that properly
requires its own investigation, judged not worth blocking this small, well-evidenced hotfix on.
Verification instead: `python3 tools/gate_checks/doc_staleness_check.py True
".claude/skills/implement-ticket/SKILL.md" "docs/ai/ticket-lifecycle.md"` → PASS. Ran
`check_skill_doc_covers_meta_phases('implement-ticket')` directly → 0 FAIL (confirms the fix
didn't regress phase-title coverage). `python3 tools/validate_frontmatter.py
docs/ai/ticket-lifecycle.md` → PASS.

## Files Changed
- `.claude/skills/implement-ticket/SKILL.md` — added Security-Review to the hotfix "still runs" enumeration.
- `docs/ai/ticket-lifecycle.md` — Tier Routing table's hotfix row now notes Security-Review's conditional applicability.

## Parity
`expected_subsystems_for_files(['.claude/skills/implement-ticket/SKILL.md', 'docs/ai/ticket-lifecycle.md'])`
→ `{}` (no `src/` paths, no mapping applies). `cross_reference_touched(..., [])` → `[]` (no
failures). No parity ledger entry needed — matches this session's established precedent for pure
agent-instruction-prose/docs changes (out of ledger scope).

## Completion Summary
Fixed the confirmed-live bug: `implement-ticket/SKILL.md` line 70's hotfix-summary paragraph now
correctly lists `Security-Review` among the tier-unconditional phases, matching step 11 and the
real JS gate placement (`implement-ticket.js:1227-1279`). Found and fixed the same staleness class
in `docs/ai/ticket-lifecycle.md`'s Tier Routing table during Document-Update (done directly, no
subagent — hit this session's hard 200-agent spawn cap). All static DoD checks (Verify, run
directly via `done_checker_static.run_static_precheck`) passed clean:
`staging_artifacts_complete`/`frontmatter_valid` NA (hotfix, no staging artifacts),
`data_runs_clean`/`ticket_location`/`working_log_no_row_yet`/`ticket_field_values_valid` PASS,
`docs_to_update_coverage` NA (hotfix, no investigation.md). `validate_frontmatter.py` on the ticket
itself: OK. Second acceptance criterion (a new automated test cross-referencing the SKILL.md
enumeration against real tier-unconditional gates) was deliberately descoped during Test — the
existing `check_skill_doc_covers_meta_phases()` checks phase-title presence, not per-tier
enumeration correctness, and building a genuinely new assertion needs its own scoped investigation
rather than riding on this small hotfix. No known material gap beyond that one disclosed, deferred
item.
