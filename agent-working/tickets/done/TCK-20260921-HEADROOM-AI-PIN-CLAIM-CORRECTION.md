---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260921-HEADROOM-AI-PIN-CLAIM-CORRECTION
phase: done
date: 2026-09-21
tags: [ai, documentation, process-improvement]
---

# TCK-20260921-HEADROOM-AI-PIN-CLAIM-CORRECTION

## Title
Correct a false claim, introduced by this session's own earlier work, that `headroom-ai` is
unpinned in any requirements file — it has been pinned in `requirements-knowledge.txt` since PR #228

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Flagged by peer review while scoping a follow-up batch. `docs/guidelines/agent_working_environment.md`
(line 35, added by `TCK-20260914-VENV-NAMING-CI-PARITY-SWAP`'s own 2nd-pass correction) and that same
ticket's own Completion Summary both claim `headroom-ai==0.37.0` is "installed ad hoc (not pinned in
any requirements file)". That claim is false and was false at the moment it was written — verified
directly: `requirements-knowledge.txt:27` has pinned `headroom-ai==0.37.0` since commit `b71b0a734`
(PR #228, "Agent infra: manifest CI flake fix, selective-retrieval guidance, Headroom safety
envelope"), well before the venv-naming ticket's own later passes made the false claim.

Root cause of the error: whoever wrote the false claim (this same session, in an earlier turn) did
not re-grep `requirements-knowledge.txt` at the moment of writing it, and instead carried forward a
stale assumption from an earlier point in the same session when the pin genuinely hadn't landed yet
(the pin went through its own revert/re-add cycle earlier in this session's Headroom work, alongside
the `.mcp.json` registration itself).

## Scope
- Correct `docs/guidelines/agent_working_environment.md` line 35: `headroom-ai==0.37.0` is pinned in
  `requirements-knowledge.txt`, not installed ad hoc.
- Correct `tickets/done/TCK-20260914-VENV-NAMING-CI-PARITY-SWAP.md`'s Completion Summary (the
  "unpinned `headroom-ai==0.37.0`" phrase), for the same reason — a closed ticket's own summary
  should not permanently assert something false about the repo's current state.
- Repo-wide sweep (`grep -rln "unpinned"` and variants) confirmed these are the only two places the
  false claim appears; no other doc/ticket/stored-artifact repeats it.
- Run `make knowledge-index-update` since `docs/` changed.

## Out of Scope
- Any change to `requirements-knowledge.txt` itself, `.mcp.json`, or the Headroom MCP registration —
  none of those are wrong; only the prose describing them was wrong.
- Re-litigating whether `headroom-ai` *should* be pinned there — it already is, correctly, and has
  been since PR #228.

## Acceptance Criteria
- [x] `docs/guidelines/agent_working_environment.md` line 35 no longer claims `headroom-ai` is
      unpinned; states it is pinned in `requirements-knowledge.txt`.
- [x] `tickets/done/TCK-20260914-VENV-NAMING-CI-PARITY-SWAP.md`'s Completion Summary corrected the
      same way.
- [x] Repo-wide grep for `unpinned`/`not pinned in any requirements` confirms no other file repeats
      the false claim.
- [x] `make knowledge-index-update` run clean.

## Related Tickets
- `TCK-20260914-VENV-NAMING-CI-PARITY-SWAP` (done) — introduced the false claim in its own 2nd pass.
- `TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT` (done) — the ticket that originally added the
  pin to `requirements-knowledge.txt` in PR #228, correctly, at the time.

## Related Docs
- `docs/guidelines/agent_working_environment.md`
- `requirements-knowledge.txt`

## Related Stored Artifacts
- None — hotfix tier, self-evident intent captured here.

## Related Code Areas
- `docs/guidelines/agent_working_environment.md`
- `tickets/done/TCK-20260914-VENV-NAMING-CI-PARITY-SWAP.md`

## Assumptions / Open Questions
- None.

## Implementation Notes
Pure prose correction, no code or config changed. Verified the pin's real origin via
`git log --oneline --follow -S "headroom-ai==0.37.0" -- requirements-knowledge.txt` before writing
anything, rather than assuming the peer's report was correct at face value — it matched exactly.

## Test Summary
No automated test applies — a documentation/prose correction. Verified via direct `grep` sweep
(repo-wide) that no other file repeats the false claim after this fix, and via
`make knowledge-index-update` running clean.

## Files Changed
- `docs/guidelines/agent_working_environment.md` — line 35 corrected.
- `tickets/done/TCK-20260914-VENV-NAMING-CI-PARITY-SWAP.md` — Completion Summary corrected.

## Completion Summary
Corrected a false claim this same session introduced earlier: `headroom-ai==0.37.0` has been pinned
in `requirements-knowledge.txt` since PR #228, not "installed ad hoc." Verified the pin's real origin
via git history before writing the correction, rather than trusting the peer's report or the
original false claim at face value. Repo-wide sweep confirmed exactly two occurrences, both fixed.
No other material gap.
