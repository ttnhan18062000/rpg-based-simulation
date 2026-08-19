---
status: active
layer: engine
authority: P1
audience: agent
tags: [engine, determinism]
---

# Epic Plan — Determinism Verification Coverage Gap

**Tracking ticket:** `TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC`
**Source:** `docs/audits/D23_architecture_resilience.md` §C, §J (R5)
**Priority:** P3 — only worth doing if off-path mutation bugs are a live concern; both source audits frame this as conditional, not urgent.

## Status
Resolved by `TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC`, via the "at minimum" branch of the
Scope section below — `DEGRADED`/`SURVIVAL` run outputs are now explicitly labeled
reduced-verification rather than left silently indistinguishable from `FULL`-verification runs.

A new cumulative `RuntimeStatus.max_mode_reached` field (`src/engine/runtime_status.py`) tracks
the worst `RuntimeMode` reached at any point during a run, updated unconditionally inside
`reset_dwell()` so it is independent of the replay stream and correctly covers `SURVIVAL` mode
(which emits no `TICK_END` events at all). At shutdown, `Kernel.shutdown()` derives
`verification_level = "REDUCED" if max_mode_reached >= RuntimeMode.DEGRADED else "FULL"` and
surfaces it on `ShutdownResult.verification_level` (`src/core/lifecycle.py`),
`RunManifest.verification_level` (`src/observability/reporting/artifact_repository.py`,
written to `run_manifest.json`), and `run_report.json`/`.md`'s `metadata.verification_level`
(`src/observability/reporting/run_report.py`).

The Out-of-scope item below still holds: the Tier-2 `audit_mode` fingerprint gate and the
DEGRADED/SURVIVAL canonical-hash gate remain deliberately conditional, unchanged by this ticket —
only a truthful reporting label was added, not a widened always-on check. The cheap always-on
partial/sampled fingerprint alternative mentioned in Scope was not pursued; the "at minimum"
labeling branch was judged sufficient. See `docs/engine/known_limitations.md` §2.4 ("Run-level
`verification_level` label") and parity ledger entry `INFRA-363`
(`docs/parity_ledger/infrastructure.yaml`) for full derivation detail.

## Problem

The kernel's mutation-guard and determinism proofs are mode-dependent, not always-on:

- The Tier-2 SHA-256 fingerprint check — the one that would actually catch a subtle off-path
  field mutation of an existing entity during a read-only phase — is gated behind
  `audit_mode=True` (`kernel.md:36-44`). In a default production run, this class of bug is
  invisible; Tier 1 (always-on) only checks entity count and tick number.
- The canonical SHA-256 hash comparison (the strongest determinism proof) is skipped entirely in
  `DEGRADED` mode and absent in `SURVIVAL` mode (`kernel.md:100-109`). The strongest correctness
  proof is unavailable exactly when the system is under the load most likely to produce a subtle
  bug.

## Scope for the eventual `create-tickets` pass

- Consider a cheap, always-on partial/sampled fingerprint as an alternative to the current
  all-or-nothing `audit_mode` gating — narrowing the coverage gap without paying the full Tier-2
  cost on every tick.
- At minimum, if a cheaper always-on check isn't pursued: flag `DEGRADED`/`SURVIVAL` run outputs
  as "reduced verification" so a consumer of that run's results knows the strongest proof wasn't
  applied, rather than silently treating all runs as equally verified.

## Out of scope

- Making the full Tier-2 fingerprint or canonical hash always-on unconditionally — both source
  audits frame this as a genuine cost/coverage tradeoff, not a bug to eliminate outright.
- Pursuing this epic at all, unless off-path mutation bugs have actually occurred or are a
  specifically live concern — per the source audit's own explicit conditional framing, this is
  the lowest-urgency item in the whole roadmap.

## Acceptance signal for this epic (not yet broken into child tickets)

- Either a cheap always-on partial fingerprint exists and narrows the current audit-mode-only
  gap, or `DEGRADED`/`SURVIVAL` run outputs are explicitly labeled as reduced-verification.

## References

- `docs/plans/architecture_resilience_remediation_roadmap.md` (Epic I)
- `docs/audits/D23_architecture_resilience.md` (R5, Stage 5 item 12)
