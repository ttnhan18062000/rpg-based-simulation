---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260706-SCOPE-TAG-REGISTRY-CHECK
phase: done
date: 2026-07-06
tags: [tagging, workflows, agent-monitoring]
---

# TCK-20260706-SCOPE-TAG-REGISTRY-CHECK

## Title
Check the tag registry at Scope time, not just at Verify — new `TAGS_NOT_REGISTERED` gate, traced via `reason_code`

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Follow-up to `TCK-20260706-TAG-REGISTRY-DATA` and `TCK-20260706-MONITORING-REASON-CODE`. Prior
investigation found: `ticket-scoper.md` and `implement-ticket.js`'s Scope phase (both the
Create-new and Load-existing branches) never check whether a ticket's tags are actually registered
— only `done-checker`'s Verify-phase `frontmatter_valid` condition does, 6+ phases later. User
asked to fix this and to make sure the fix "utilizes the new working workflow, and durable
traceable data and logging" — i.e. reuse the `reason_code` tracing infrastructure just built
(`TCK-20260706-MONITORING-REASON-CODE`), not invent a third mechanism.

## Scope
- **`tools/tag_registry.py`**: new `check_tags_registered(tags: list[str], root=None) -> list[str]`
  — returns the subset not registered (phase-N tags always excluded, matching
  `is_tag_registered`'s existing exemption).
- **`.claude/agents/ticket-scoper.md`**: add a soft guidance note (not an enforcement mechanism —
  see below) pointing at `tools/tag_registry.py list` when picking tags, so the agent's own choices
  are more likely to land on an existing tag in the first place.
- **`.claude/workflows/implement-ticket.js`** (orchestrator-run check, corrected during
  investigation from an initially-planned agent-self-report design — see investigation.md):
  - No `TICKET_SCHEMA` change — the orchestrator already has `ticketInfo.tags` after the agent call
    returns, so it runs the check itself via `bash()` (mirrors Architecture-Verify's/Parity's Step
    0 pattern: individually-quoted argv elements, `MARKER:`-prefixed JSON output, try/catch parse)
    rather than depending on the agent to self-report correctly.
  - New gate, immediately after the existing `CONFLICTS_DETECTED` check: if the check finds any
    unregistered tag, log guidance, `writeMonitoring('TAGS_NOT_REGISTERED')`, and return
    `{status: 'TAGS_NOT_REGISTERED', ticket_id, unregistered_tags, message}` — same shape/precedent
    as `CONFLICTS_DETECTED`.
  - The `Scope`/`ticket-scoper` `pushEvent` call now computes a `reason_code`
    (`'conflicts_detected'` or `'tag_registry_rejection'`, `null` if neither) — Scope now has 2
    distinct failure causes, the same "collapsed causes" problem `DOD_BLOCKED` had, so it needs the
    same disambiguation `TCK-20260706-MONITORING-REASON-CODE` introduced. Reuses the existing
    `tag_registry_rejection` code (same root cause as the Verify-phase one, just caught earlier) —
    not a new taxonomy value.
- **`docs/agent-monitoring/schema.md`**: add `TAGS_NOT_REGISTERED` to the `final_status` values
  table; update the `reason_code` section to note it's now also populated for `Scope`/`failed`
  events, and document `conflicts_detected` as the (now also explicit) code for the pre-existing
  conflicts case.
- **`docs/ai/workflows.md`**: update `implement-ticket`'s phase table (Scope gate condition) and
  Return Values table (+1 row).
- **`docs/ai/ticket-lifecycle.md`**: update the Mermaid pipeline diagram (Scope node gains a second
  gate-branch edge) and the Failure Recovery Reference table (+1 row), keeping the diagram accurate
  per `TCK-20260706-DIAGRAM-COVERAGE`'s own stated purpose.
- **Tests**: `tests/tools/test_tag_registry.py` gains coverage for `check_tags_registered`.

## Out of Scope
- `create-tickets.js`'s Structure/Write phases — same underlying gap (computes tags without
  registry awareness), but not named in this request; flagged as a related, deferred item, not
  silently ignored.
- Auto-registering an unregistered tag on the agent's behalf — the whole point of a hard allowlist
  is deliberate registration; this ticket surfaces the problem early, it does not silently fix it.
- Retrofitting `reason_code` onto any phase besides Scope and Verify — no evidenced catch-all
  problem elsewhere yet.

## Acceptance Criteria
- [ ] `check_tags_registered` exists, pure, tested.
- [ ] A ticket whose tags include an unregistered one is caught at Scope (`TAGS_NOT_REGISTERED`),
      not only at Verify — for both the Create-new and Load-existing (resume by `ticket_id`)
      branches.
- [ ] The Scope-phase `events.jsonl` record for a `TAGS_NOT_REGISTERED` run carries
      `reason_code: "tag_registry_rejection"`; a `CONFLICTS_DETECTED` run carries
      `reason_code: "conflicts_detected"`.
- [ ] `docs/agent-monitoring/schema.md`, `docs/ai/workflows.md`, `docs/ai/ticket-lifecycle.md`
      (including its Mermaid diagram) all reflect the new gate accurately.
- [ ] All new/updated tests pass; no regressions in the broader `tests/tools/` suite.

## Related Tickets
- TCK-20260706-TAG-REGISTRY-DATA (the hard allowlist this check runs proactively against)
- TCK-20260706-MONITORING-REASON-CODE (the tracing mechanism this ticket reuses, not duplicates)
- TCK-20260706-CLAUDE-MD-TAG-REGISTRY-DOC (the sibling documentation fix from the same request)
- TCK-20260706-DIAGRAM-COVERAGE (owns the Mermaid diagram this ticket keeps accurate)

## Related Docs
- docs/agent-monitoring/schema.md
- docs/ai/workflows.md
- docs/ai/ticket-lifecycle.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/tag_registry.py
- .claude/agents/ticket-scoper.md
- .claude/workflows/implement-ticket.js (Scope phase, `TICKET_SCHEMA`, `pushEvent` call)

## Assumptions / Open Questions
- Assumed each tag can be safely passed as its own shell argv element without JSON-embedding
  risk, since a canonical-form tag (lowercase, hyphenated) never contains quotes/backticks/spaces
  — the same class of characters that caused `TCK-20260706-MONITORING-REASON-CODE`'s subprocess
  approach to be rejected. If an agent proposes a genuinely non-canonical draft tag, canonical-form
  validation already happens downstream at Verify regardless; this check only needs to handle
  already-canonical-looking tags safely, not arbitrary text.
- `create-tickets.js` is explicitly deferred (Out of Scope) — flagged for the user's awareness, not
  a silent gap.

## Implementation Notes
Implemented per plan.md, with one design correction made during investigation (not assumed
upfront — see investigation.md's "Design correction" section):

1. **`tools/tag_registry.py`**: added `check_tags_registered(tags, root=None) -> list[str]` —
   one `load_registry()` call, returns the unregistered subset via `is_tag_registered`.
2. **Design correction:** originally planned to have the *agent* self-report `unregistered_tags`
   in its own returned JSON (mirroring `conflicts`). Corrected during investigation: the
   orchestrator already receives `ticketInfo.tags` after the agent call returns, so it runs the
   check itself via `bash()` — mirroring the *stronger* existing precedent (Architecture-Verify's
   and Parity's orchestrator-run Step 0 checks) rather than the weaker one (`done-checker`'s
   agent-run precheck, only accepted there because no better option exists at that point in the
   pipeline). This removes any dependency on the agent correctly following a self-report
   instruction, and needed **no** `TICKET_SCHEMA` change at all.
3. **`.claude/workflows/implement-ticket.js`**: added the orchestrator-run check (individually
   quoted argv elements per tag, `TAG_CHECK_JSON:`-prefixed marker output, try/catch parse —
   identical shape to the existing `archCheckOutput`/`p0ScanOutput` calls in this same file) right
   after `ticketInfo` returns. Updated the `Scope`/`ticket-scoper` `pushEvent` call to compute a
   `reason_code` (`'conflicts_detected'` or `'tag_registry_rejection'`) — Scope now has 2 distinct
   failure causes, reopening the same "collapsed causes" problem `DOD_BLOCKED` had, so it needs
   the same disambiguation. Added the new `TAGS_NOT_REGISTERED` gate immediately after the existing
   `CONFLICTS_DETECTED` block, identical shape (log guidance, `writeMonitoring`, structured return).
4. **`.claude/agents/ticket-scoper.md`**: added a soft guidance clause to the `tags:` line pointing
   at `python3 tools/tag_registry.py list` — helps the agent land on an existing tag in the first
   place, but is not load-bearing for the actual gate (which is orchestrator-run and would still
   fire even if the agent ignores this guidance).
5. **Docs**: `docs/agent-monitoring/schema.md` (`TAGS_NOT_REGISTERED` added to `final_status`
   values; `reason_code` section rewritten to explain *why* Scope now also gets a code, with a
   3-column table including the `Phase(s)` each value applies to — `tag_registry_rejection` now
   explicitly spans both Scope and Verify, same root cause); `docs/ai/workflows.md` (Scope's Gate
   condition column and Return Values table updated); `docs/ai/ticket-lifecycle.md` (Mermaid
   diagram gains a second Scope gate-branch edge, the Scope Step-by-Step Detail section documents
   the new gate for both the Create-new and Load-existing branches, Failure Recovery Reference
   table gains a row) — content-parity verified: all 8 distinct gate-status labels in the diagram
   now match `workflows.md`'s Return Values table exactly (grepped and diffed, same method as
   `TCK-20260706-DIAGRAM-COVERAGE`).
6. **Tests**: `tests/tools/test_tag_registry.py` gains 4 tests for `check_tags_registered`.

## Test Summary
- `pytest tests/tools/test_tag_registry.py -v` → all pass (4 new + 24 pre-existing).
- `node --check .claude/workflows/implement-ticket.js` → syntax OK.
- Manual bracket-balance check on the updated `ticket-lifecycle.md` Mermaid diagram → balanced
  (25 square / 8 paren / 3 brace, open=close on all three).
- Manual content-parity check: all 8 gate-status labels in the diagram match
  `docs/ai/workflows.md`'s Return Values table (previously 7, `TAGS_NOT_REGISTERED` now the 8th).
- Full `pytest tests/tools/ -q --ignore=tests/tools/test_knowledge_search.py` → 491 passed, 2
  failed (the same 2 pre-existing, unrelated `test_search_mcp.py` failures disclosed repeatedly
  this session).
- `make knowledge-index-update` → 7 files re-embedded, completed successfully.
- Could not exercise the new gate via a live `implement-ticket` run on this ticket itself (same
  bootstrapping limitation as `TCK-20260706-MONITORING-REASON-CODE` and
  `TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER`) — verified via unit tests and code read-through.

## Files Changed
- `tools/tag_registry.py` (new `check_tags_registered`)
- `.claude/workflows/implement-ticket.js` (orchestrator-run check, new `TAGS_NOT_REGISTERED` gate,
  `reason_code` added to the Scope `pushEvent` call)
- `.claude/agents/ticket-scoper.md` (soft guidance clause)
- `docs/agent-monitoring/schema.md`, `docs/ai/workflows.md`, `docs/ai/ticket-lifecycle.md` (updated)
- `tests/tools/test_tag_registry.py` (4 new tests)
- `tickets/inprogress/TCK-20260706-SCOPE-TAG-REGISTRY-CHECK.md` → `tickets/done/...`
- `staging_artifacts/TCK-20260706-SCOPE-TAG-REGISTRY-CHECK/` → `stored_artifacts/...`

## Completion Summary
Closed the "distance between cause and detection" gap flagged in the earlier troubleshooting
discussion: an unregistered tag is now caught at Scope — orchestrator-run, not agent-self-reported,
via the same individually-quoted-argv/marker-JSON pattern already established for
Architecture-Verify and Parity — instead of only 6+ phases later at Verify. The fix directly reuses
the `reason_code` tracing infrastructure from `TCK-20260706-MONITORING-REASON-CODE` rather than
inventing a third mechanism, per the user's explicit ask: Scope's `pushEvent` now carries
`reason_code: "tag_registry_rejection"` (reusing the exact value Verify already used for the same
root cause) or `"conflicts_detected"` (newly named for the pre-existing conflicts case, since it's
no longer Scope's only failure mode). One real design correction was made during investigation,
not assumed at planning time: the check is orchestrator-run rather than agent-self-reported,
matching this repo's stronger existing precedent and removing a reliability dependency on the
agent following instructions correctly. `create-tickets.js` has the identical gap but was
explicitly out of scope — flagged, not silently left unaddressed.
