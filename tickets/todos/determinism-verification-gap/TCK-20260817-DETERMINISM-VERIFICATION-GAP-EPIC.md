---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC
phase: open
date: 2026-08-17
tags: [engine, determinism]
---

# TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC

## Title
Close (or explicitly label) the audit-mode-only determinism/mutation-guard verification gap

## Status
EPIC_SCOPED

## Tier
epic

## Type
repair

## Priority
P3

## Request Summary
The kernel's strongest correctness proofs are mode-dependent: the Tier-2 SHA-256 fingerprint
check that would catch a subtle off-path field mutation during a read-only phase is gated behind
`audit_mode=True`, invisible in default production runs; the canonical hash comparison is skipped
in DEGRADED mode and absent in SURVIVAL mode — unavailable exactly when the system is under the
load most likely to produce a subtle bug. The source audit explicitly frames this as the
lowest-urgency item in the whole roadmap: only worth pursuing if off-path mutation bugs have
actually occurred or are a live concern.

## Scope
- Scope-only epic: full findings and proposed remediation steps are in
  `docs/plans/determinism_verification_gap_epic.md`. Detailed, investigated child tickets are not
  created yet, and per the source audit's own framing this epic should not be picked up without
  a specific reason.
- When work begins (if ever): run `create-tickets` against a proposal document scoped to this
  epic's items (cheap always-on partial fingerprint, or explicit reduced-verification labeling),
  producing investigated child tickets in `tickets/todos/determinism-verification-gap/`.

## Out of Scope
- Making the full Tier-2 fingerprint or canonical hash always-on unconditionally — a genuine
  cost/coverage tradeoff per the source audit, not a bug to eliminate outright.

## Acceptance Criteria
- [ ] `docs/plans/determinism_verification_gap_epic.md` is reviewed and its scope confirmed accurate.
- [ ] A decision is recorded on whether this epic is worth pursuing at all, given its explicitly
      conditional priority.
- [ ] Child tickets are created via `create-tickets` only if this epic is chosen for action.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)

## Related Docs
- docs/plans/determinism_verification_gap_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D23_architecture_resilience.md
- docs/engine/kernel.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/engine/kernel.py (audit_mode-gated fingerprint/hash checks)

## Assumptions / Open Questions
- Whether off-path mutation bugs have actually occurred or are a live concern is unknown to this
  ticket — that's the deciding factor for whether this epic should be pursued at all.

## Implementation Notes
(pending — scope-only epic)

## Test Summary
(pending — no direct tests; each future child ticket will carry its own)

## Files Changed
(pending)

## Completion Summary
(pending)
