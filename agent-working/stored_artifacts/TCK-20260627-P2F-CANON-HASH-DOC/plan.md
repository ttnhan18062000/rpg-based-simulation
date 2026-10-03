# Plan — TCK-20260627-P2F-CANON-HASH-DOC

## Objective

Document the canonical state hash conditionality in `known_limitations.md` and `kernel.md`
so that developers understand when full SHA-256 hashing runs, when `"SKIPPED"` appears in
TICK_END payloads, and what the lightweight `fingerprint()` covers in the interim.

## Key facts (from investigation)

1. `_phase_persistence()` sets `tick_hash = "SKIPPED"` unless:
   `replay_allowed AND (audit_mode OR replay_richness == "FULL")`

2. `replay_richness` by mode:
   - NORMAL → "FULL" → canonical hash IS computed per-tick
   - CONSTRAINED → "FULL" → canonical hash IS computed per-tick
   - DEGRADED → "MINIMAL" → tick_hash = "SKIPPED"
   - SURVIVAL → replay_allowed=False → no TICK_END event at all

3. The fingerprint (StateFingerprinter, MD5) is emitted in REFINED_UPDATE events for
   NORMAL/CONSTRAINED/DEGRADED modes. It covers most entity domains but excludes:
   buildings, corpses, ground_items, chests, home_storage, camps, blocked_tiles,
   town_tiles, building_tiles, periodic_due_ticks, work_debt, rng_checkpoint.

4. The fingerprint is NOT a complete determinism proof. The canonical SHA-256 is the
   authoritative proof; it always runs at shutdown (final hash) regardless of mode.

## Correction to ticket framing

The ticket states "Standard runs record 'SKIPPED'." This is inaccurate:
NORMAL and CONSTRAINED modes (the typical operation modes) use `replay_richness="FULL"`
and compute the full canonical hash per-tick. "SKIPPED" occurs only in DEGRADED mode.
The documentation will reflect the accurate, mode-specific behavior.

## Changes

### 1. `docs/engine/known_limitations.md`

Add new subsection **§2.4 Canonical State Hash Availability by Runtime Mode** between
§2.3 (Phase Isolation Detection) and §3 (Tooling/Observability).

Content:
- Table: RuntimeMode → replay_richness → tick_hash value in TICK_END
- Explain what "SKIPPED" means in TICK_END events (DEGRADED mode)
- Explain SURVIVAL mode (no TICK_END at all)
- Explain StateFingerprinter (MD5, broad domain coverage, NOT a proof)
  and where it appears (REFINED_UPDATE events)
- Clarify fingerprint field gaps vs canonical hash
- Note that shutdown always emits the final canonical hash regardless of mode

### 2. `docs/engine/kernel.md`

Add a new subsection after the Phase Domain Permissions table:
**"State hashing in Phase 7 (Persistence)"**

Content:
- Two-tier hash model: canonical SHA-256 (NORMAL/CONSTRAINED) vs fingerprint MD5 (all replay-enabled modes)
- When TICK_END.hash is "SKIPPED" (DEGRADED) vs a real hash value
- When no TICK_END event is emitted at all (SURVIVAL)
- Cross-reference to `known_limitations.md §2.4` and `deterministic_execution.md`

### 3. Parity ledger

No new parity entry needed — behavior is unchanged. The existing INFRA-119 through INFRA-130
entries cover "Replay hash includes X" and are verified. A note will be added to the
investigation confirming these entries remain accurate.

## Out of scope

- No code changes to `kernel.py` or `checkpoint.py`
- No change to `replay_richness` defaults
- No new tests (pure documentation)

## Review gate

APPROVED — no unresolved questions. All facts confirmed from source. Scope is narrow and
self-contained to two existing docs.
