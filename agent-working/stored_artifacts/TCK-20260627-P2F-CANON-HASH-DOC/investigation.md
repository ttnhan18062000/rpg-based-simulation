# Investigation — TCK-20260627-P2F-CANON-HASH-DOC

## Summary

Traced the canonical hash pipeline end-to-end from `_phase_persistence()` through
`CanonicalStateHasher`, `StateFingerprinter`, and `GovernorPolicy` to determine
exactly when each hash is computed and what it covers.

---

## Findings

### 1. `_phase_persistence()` — the canonical hash gate

`src/engine/kernel.py:870–884`

```python
def _phase_persistence(self) -> None:
    tick_hash = "SKIPPED"
    if self._current_policy.replay_allowed and (
        self._audit_mode or self._current_policy.replay_richness == "FULL"
    ):
        from src.engine.checkpoint import CanonicalStateHasher
        tick_hash = CanonicalStateHasher.get_hash(self._state)

    if self._current_policy.replay_allowed:
        self._replay.emit(TraceEvent(
            tick=self._state.tick,
            system="KERNEL",
            event_type="TICK_END",
            payload={"hash": tick_hash}
        ), self._current_policy)

    self._replay.on_tick_end(self._state.tick)
```

Two separate conditions:
- `tick_hash` (canonical SHA-256) requires `replay_allowed AND (audit_mode OR replay_richness=="FULL")`
- TICK_END event emission requires only `replay_allowed`

---

### 2. `replay_richness` by `RuntimeMode`

`src/engine/policy.py` — `GovernorPolicy.from_mode()`:

| RuntimeMode | `replay_allowed` | `replay_richness` | tick_hash result |
|---|---|---|---|
| NORMAL | True | "FULL" | SHA-256 canonical hash |
| CONSTRAINED | True | "FULL" | SHA-256 canonical hash |
| DEGRADED | True | "MINIMAL" | "SKIPPED" |
| SURVIVAL | False | "OFF" | no TICK_END event at all |

**Key correction from ticket framing:** The ticket states "Standard runs record 'SKIPPED'".
This is inaccurate. NORMAL and CONSTRAINED modes — the most common run configurations —
use `replay_richness="FULL"` and therefore compute the full canonical hash per-tick.
The "SKIPPED" case applies only to DEGRADED mode.

---

### 3. `CanonicalStateHasher.get_hash()` — full canonical SHA-256

`src/engine/checkpoint.py:38–107`

Covers the full `AuthoritativeState`:
- Scalar fields: tick, seed, world_time, movement_count, maturity, last_calamity_tick, town_center
- Entities (sorted by ID, each via `to_canonical_dict()`)
- All world collections: regions, local_scars, resource_nodes, buildings, corpses, ground_items, chests, groups, home_storage, camps
- Derived indices: global_resources, periodic_due_ticks, work_debt, blocked_tiles, town_tiles, building_tiles
- RNG checkpoint

This is a complete cryptographic proof. Bit-identical across runs iff all authoritative state is bit-identical.

Governed by `CanonicalHashScheduler` (INFRA-197): full hash calls outside of tick=0, run-end, or
reasons {"certification","audit","replay"} raise `HashScheduleViolation`.

---

### 4. `StateFingerprinter` — lightweight MD5 fingerprint

`src/replay/fingerprint.py` — `StateFingerprinter.get_fingerprint()`

`AuthoritativeState.fingerprint()` delegates here (`src/core/state.py:1252`).

**Covers:**
- Entity identity, position, HP, gold, current_project/objective, readiness, lifecycle, skills, items, bonds, reputation, full strategic state (projects, blockers, leads, directives, concerns, contracts, boredom)
- Global resources
- Resource nodes (remaining_charges, cooldown_remaining)
- Regions (owner, influence, hazard_level)
- Local scars (severity)
- Groups (leader, members, shared_target, intent, contract)
- Macro world state (maturity, last_calamity_tick, movement_count)

**Excludes** (present in CanonicalStateHasher but NOT in StateFingerprinter):
- buildings, corpses, ground_items, chests, home_storage, camps
- blocked_tiles, town_tiles, building_tiles
- periodic_due_ticks, work_debt
- rng_checkpoint

**Algorithm:** MD5 (not SHA-256). Not cryptographically secure. Not a determinism proof.

**Where emitted:** In `REFINED_UPDATE` events (`src/engine/kernel.py:610`) whenever
`replay_allowed=True` (NORMAL, CONSTRAINED, DEGRADED modes).

Also used by `_guard_stability()` in audit_mode to check for field-level mutations during
read-only phases (Scheduling, Collection).

---

### 5. Is `fingerprint()` sufficient for standard determinism verification?

**No — not as a complete proof.** Missing domains (buildings, items on ground, RNG checkpoint)
mean divergences in those domains would be invisible.

**Yes — as a primary signal in DEGRADED mode.** When `replay_richness="MINIMAL"` (DEGRADED),
the fingerprint is the only per-tick hash signal. It covers the most gameplay-visible state.

**Irrelevant in NORMAL/CONSTRAINED mode.** The canonical SHA-256 runs every tick, so the
fingerprint's partial coverage is not the primary signal.

The authoritative determinism proof is always `CanonicalStateHasher.get_hash()`, used in:
- Per-tick TICK_END events in NORMAL/CONSTRAINED modes
- Shutdown final hash (`src/engine/kernel.py:918–919`)
- Certification harness full-evidence runs (EvidenceLevel.FULL)

---

### 6. Existing documentation gaps

- `docs/engine/deterministic_execution.md` — documents the canonical hash contract but does
  not mention the `replay_richness` condition that gates it, nor the "SKIPPED" behavior.
- `docs/engine/kernel.md` — Phase 7 (Persistence) row says "Calculate state hashes" but
  does not explain the conditional behavior.
- `docs/engine/known_limitations.md` — no section on hash availability by runtime mode.

---

## References

- `src/engine/kernel.py:870–884` (`_phase_persistence`)
- `src/engine/checkpoint.py` (`CanonicalStateHasher`, `CanonicalHashScheduler`, INFRA-196/197)
- `src/replay/fingerprint.py` (`StateFingerprinter`)
- `src/engine/policy.py` (`GovernorPolicy.from_mode()`)
- `src/core/state.py:1252` (`AuthoritativeState.fingerprint()`)
- `docs/engine/deterministic_execution.md`
- `docs/engine/known_limitations.md`
- `docs/engine/kernel.md`
- `docs/parity_ledger/infrastructure.yaml` (INFRA-119–130, INFRA-196, INFRA-197)
