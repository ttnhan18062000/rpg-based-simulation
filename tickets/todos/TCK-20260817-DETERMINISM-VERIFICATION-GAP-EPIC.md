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
OPEN

## Tier
standard

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
Full findings are in `docs/plans/determinism_verification_gap_epic.md`. Per the source audit's
own framing, this is the lowest-urgency item in the whole roadmap — only worth picking up if
off-path mutation bugs have actually occurred or are a live concern. Concrete scope when picked up:
- Consider a cheap, always-on partial/sampled fingerprint as an alternative to the current
  all-or-nothing `audit_mode` gating in `src/engine/kernel.py`.
- At minimum, if a cheaper always-on check isn't pursued: flag `DEGRADED`/`SURVIVAL` run outputs
  as "reduced verification" so a consumer of that run's results knows the strongest proof wasn't
  applied.

## Out of Scope
- Making the full Tier-2 fingerprint or canonical hash always-on unconditionally — a genuine
  cost/coverage tradeoff per the source audit, not a bug to eliminate outright.

## Acceptance Criteria
- [ ] Either a cheap always-on partial fingerprint exists and narrows the current
      audit-mode-only gap, or `DEGRADED`/`SURVIVAL` run outputs are explicitly labeled as
      reduced-verification.
- [ ] The full Tier-2 fingerprint / canonical hash remains conditional (not made unconditionally
      always-on) — this is a deliberate cost/coverage tradeoff, not a bug to eliminate.

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
  ticket — that's the deciding factor for whether this ticket should be picked up at all.
- **Downgraded from epic to standard tier (2026-08-18):** one of 10 sub-epics under
  `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`; a single contained fix to one file
  (`src/engine/kernel.py`) with two concrete alternative resolutions — one standard ticket, not a
  multi-ticket initiative. `staging_artifacts/TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC/`
  not yet created. Still gated on the "is this a live concern" question above before pickup.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
