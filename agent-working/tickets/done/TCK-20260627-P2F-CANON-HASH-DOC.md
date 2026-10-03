---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260627-P2F-CANON-HASH-DOC
phase: done
date: 2026-06-27
tags: [canonical-hash, determinism, documentation, known-limitations]
---

# TCK-20260627-P2F-CANON-HASH-DOC

## Title
Document canonical state hash scope and "SKIPPED" behavior in known limitations

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`CanonicalStateHasher.get_hash()` is only called when `replay_richness == "FULL"` or `audit_mode=True`. Standard runs record `"SKIPPED"`. Full hash traceability is absent in normal runs; only the lighter `fingerprint()` runs. This is not documented. Source: D09 Finding 6, Risk 8/15.

## Scope
- Add an entry to `docs/engine/known_limitations.md` explaining:
  - Which run configurations produce `"SKIPPED"` in canonical hash records.
  - That `fingerprint()` (lighter SHA-256 of partial state) IS active on all ticks in standard runs.
  - Whether `fingerprint()` is sufficient for standard determinism verification.
- If the fingerprint is sufficient: update `docs/engine/kernel.md` §Phase Persistence to explicitly state this.
- Run `make knowledge-index-update` after doc changes.

## Out of Scope
- Enabling full hashing in standard runs (performance cost, not justified by current use case).
- Changes to `kernel.py` hashing behavior.

## Acceptance Criteria
- [ ] `docs/engine/known_limitations.md` documents: canonical hash produces `"SKIPPED"` in non-FULL, non-audit runs.
- [ ] Document clarifies whether `fingerprint()` is the authoritative determinism check in standard runs.
- [ ] `docs/engine/kernel.md` updated if fingerprint sufficiency determination is made.
- [ ] `make knowledge-index-update` run.

## Related Tickets
- TCK-20260627-P1G-STABILITY-GUARD (related — both are kernel observability documentation items)

## Related Docs
- `docs/audits/D09_system_wiring.md` Finding 6
- `docs/engine/kernel.md`
- `docs/engine/known_limitations.md`

## Related Stored Artifacts
- N/A

## Related Code Areas
- `src/engine/kernel.py` (`_phase_persistence()`)

## Assumptions / Open Questions
- The `fingerprint()` function produces a lightweight determinism signal. If it hashes enough state to catch non-determinism, it is sufficient for standard runs.

## Implementation Notes
- Documentation-only change. No source code modified.
- Key correction from investigation: the ticket framing ("Standard runs record SKIPPED") is inaccurate. NORMAL and CONSTRAINED modes use `replay_richness="FULL"` and compute the full canonical SHA-256 per-tick. "SKIPPED" only occurs in DEGRADED mode.
- `_phase_persistence()` condition: `replay_allowed AND (audit_mode OR replay_richness=="FULL")`.
- `StateFingerprinter` uses MD5 (not SHA-256). Emitted in REFINED_UPDATE events via `replay_allowed` path (separate from TICK_END hash gate).
- Fingerprint excludes: buildings, corpses, ground_items, chests, home_storage, camps, blocked_tiles, town_tiles, building_tiles, periodic_due_ticks, work_debt, rng_checkpoint.
- Shutdown always emits canonical SHA-256 regardless of mode.
- Updated: `docs/engine/known_limitations.md` (§2.4 added) and `docs/engine/kernel.md` (Phase 7 hashing section added).

## Test Summary
- No code change. Verify doc content manually.

## Files Changed
- `docs/engine/known_limitations.md` — added §2.4 "Canonical State Hash Availability by Runtime Mode"
- `docs/engine/kernel.md` — added "State Hashing in Phase 7 (Persistence)" section
- `docs/parity_ledger/infrastructure.yaml` — added INFRA-223

## Completion Summary
Documentation-only ticket. Added §2.4 to `known_limitations.md` with a mode-by-mode table
(NORMAL/CONSTRAINED → SHA-256 per tick; DEGRADED → "SKIPPED"; SURVIVAL → no TICK_END)
and fingerprint domain gap list. Added Phase 7 hashing section to `kernel.md`. Added INFRA-223
to infrastructure parity ledger. Key finding: ticket framing was inaccurate — NORMAL and
CONSTRAINED modes compute the full canonical hash per-tick; "SKIPPED" only applies to DEGRADED
mode. Fingerprint (MD5, StateFingerprinter) is the lighter signal active in all replay-enabled
modes but is not a complete determinism proof. Shutdown always emits the final canonical SHA-256.
