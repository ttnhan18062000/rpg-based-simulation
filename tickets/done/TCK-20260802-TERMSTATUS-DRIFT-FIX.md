---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260802-TERMSTATUS-DRIFT-FIX
phase: done
date: 2026-08-02
tags: [workflows, documentation]
---

# TCK-20260802-TERMSTATUS-DRIFT-FIX

## Title
Fix stale line-number provenance and incorrect DOC_STALENESS_BLOCKED phase attribution in terminal-statuses.yaml

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found while auditing agent-monitoring/dashboard fallout from `TCK-20260802-DOC-UPDATE-DISCIPLINE`:

1. **Caused by that ticket's own edit**: `agent-orchestration/terminal-statuses.yaml`'s header
   comment cites exact `.claude/workflows/implement-ticket.js` source line numbers (`:1234`,
   `:1246`) as provenance for `FINALIZE_INCOMPLETE`'s call sites. Adding lines earlier in that file
   (for the doc-update-discipline work) shifted those to `1377`/`1389` — the same two line numbers
   already corrected in `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py`
   and `test_terminal_status_conformance.py`, but never in this YAML's own prose.
2. **Pre-existing, unrelated to that ticket**: the same YAML's `DOC_STALENESS_BLOCKED` entry claims
   `phases: [Architecture-Verify]`. Tracing the actual code: `writeMonitoring('DOC_STALENESS_BLOCKED')`
   /`return { status: 'DOC_STALENESS_BLOCKED' }` always execute inside the `Implement` phase block —
   `phase('Architecture-Verify')` is only called afterward, and never runs at all when this status
   fires. `docs/agent-monitoring/schema.md` already documents this correctly ("caught right after
   Implement, before Architecture-Verify..."); this YAML doesn't. No test catches it because
   `tools/agent_orchestration/terminal_statuses.py::validate_terminal_statuses` only checks
   structural shape (non-empty list of strings), never cross-references real `phase()` call sites.

`agent-orchestration/rendered/claude-adapter.yaml` is a generated mirror of this same data
(`tools/agent_orchestration_claude_adapter/generator.py::render_claude_adapter`) — it inherits both
issues and must be regenerated, not hand-edited, once the source YAML is fixed.

## Scope
- `agent-orchestration/terminal-statuses.yaml`: update header comment's line-number citations
  (`:1234`→`:1377`, `:1246`→`:1389`); correct `DOC_STALENESS_BLOCKED`'s `phases` from
  `[Architecture-Verify]` to `[Implement]`.
- Regenerate `agent-orchestration/rendered/claude-adapter.yaml` via
  `render_claude_adapter(repo_root, repo_root / "agent-orchestration" / "rendered")` — never
  hand-edit the generated file.

## Out of Scope
- Adding a validator that cross-references `phases` against real `phase()` call sites — a genuine
  improvement (would have caught issue 2 automatically) but a separate, larger change; not needed
  to fix the two concrete drift instances found here.
- Any change to `.claude/workflows/implement-ticket.js` itself — the line numbers there are correct;
  only the YAML's citation of them was stale.

## Acceptance Criteria
- [x] `terminal-statuses.yaml`'s header comment cites `:1377`/`:1389`, not `:1234`/`:1246`.
- [x] `terminal-statuses.yaml`'s `DOC_STALENESS_BLOCKED` entry has `phases: [Implement]`.
- [x] `agent-orchestration/rendered/claude-adapter.yaml` regenerated (not hand-edited) and reflects
      both fixes.
- [x] `tools/agent_orchestration/terminal_statuses.py::validate_terminal_statuses` still passes
      against the edited YAML (structural validation unaffected).
- [x] All existing tests referencing this YAML/rendered file still pass.

## Related Tickets
- TCK-20260802-DOC-UPDATE-DISCIPLINE (caused issue 1; surfaced issue 2 during a related audit)
- TCK-20260720-GATE-CHECK-WIRING-DECISIONS (introduced DOC_STALENESS_BLOCKED)
- TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER (introduced terminal-statuses.yaml itself)

## Related Docs
- docs/agent-monitoring/schema.md (already correct; used as the cross-check reference)

## Related Stored Artifacts
None (hotfix — no staging artifacts).

## Related Code Areas
- agent-orchestration/terminal-statuses.yaml
- agent-orchestration/rendered/claude-adapter.yaml

## Assumptions / Open Questions
None.

## Implementation Notes
Updated `terminal-statuses.yaml`'s header comment — all four line-number citations were actually
stale, not just the two directly caused by `TCK-20260802-DOC-UPDATE-DISCIPLINE`
(`:1234`→`:1377`, `:1246`→`:1389` for `FINALIZE_INCOMPLETE`); re-verifying the other two against
current source found `:582`→`:708` (`writeMonitoring(review.verdict)`) and `:760`→`:903`
(`writeMonitoring(archVerify.verdict)`) had already drifted independently since the YAML's
2026-07-22 source date, and the SCOPE_AGENT_FAILED bypass citation `:178-183`→`:190-193` had too —
ten days of intervening ticket work on `implement-ticket.js` had already made most of this
comment's provenance stale before this ticket's own edit added one more instance of the same
problem. Added a one-line note to the comment itself flagging that these citations drift and the
`statuses:` data below is authoritative, the header is best-effort only — cheaper than committing
to re-verifying this comment every time the workflow file grows.

Corrected `DOC_STALENESS_BLOCKED`'s `phases` field from `[Architecture-Verify]` to `[Implement]`,
matching the actual `writeMonitoring('DOC_STALENESS_BLOCKED')` call site (which always executes
before `phase('Architecture-Verify')` is ever reached — confirmed via `grep -n` ordering of
`phase('Implement')` at :728, the `DOC_STALENESS_BLOCKED` return at :827-829, and
`phase('Architecture-Verify')` only at :845).

Regenerated `agent-orchestration/rendered/claude-adapter.yaml` via `render_claude_adapter()` rather
than hand-editing it, per that module's own generated-artifact contract — a 2-line diff (only the
`DOC_STALENESS_BLOCKED` phases value; the header-comment fix lives only in the source YAML, not the
rendered mirror, which doesn't carry that comment).

## Test Summary
`pytest tests/agent_orchestration_claude_adapter/ tests/agent_orchestration/ -q` — 97 passed
(confirms `validate_terminal_statuses`, the generator's containment/round-trip tests, and phase/
terminal-status conformance tests are unaffected by the corrections).

## Files Changed
- agent-orchestration/terminal-statuses.yaml
- agent-orchestration/rendered/claude-adapter.yaml

## Completion Summary
Fixed one self-caused doc-drift (stale line-number comment) and one pre-existing bug (incorrect
DOC_STALENESS_BLOCKED phase attribution) in the terminal-status contract YAML, and regenerated its
derived rendered mirror. No source-code behavior changed — this is a documentation/contract-data
correction only.
