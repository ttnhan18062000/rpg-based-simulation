---
status: active
layer: engine
authority: P1
audience: developer
---

# Simulation Kernel Contract

## 1. Purpose
This contract defines the authoritative laws and deterministic semantics of the Resource-Safe Simulation Engine. It serves as the single source of truth for kernel behavior, state classification, and time progression.

## 2. Tick Semantics
- **Definition**: A "Tick" is the smallest indivisible unit of authoritative simulation time.
- **Tick Progression**: Advancement is explicit and occurs exactly once per world-loop iteration.
- **Independence**: Tick advancement is independent of non-authoritative systems (Replay, Observability, Metrics). A failure in a non-authoritative system must not block tick progression.

## 3. Authoritative State
- **Definition**: Minimum state required to determine **future simulation outcomes**.
- **Classification**:
    - **Authoritative**: Entities, Positions, Resources, Time/Tick, RNG State.
    - **Non-Authoritative**: Replay logs, UI/API event streams, telemetry, diagnostic traces.
- **Rule**: Non-authoritative data must never be read by authoritative logic.

## 4. Tick Phase Ordering (The Law)
Every tick must execute the following phases in this exact order:
1. `INIT`: Setup tick context and handle incoming system requests.
2. `SCHEDULING`: Identify entities ready to act based on eligibility timers.
3. `COLLECTION`: Gather action proposals from ready entities.
4. `RESOLUTION`: Validate proposals and apply state changes in deterministic order.
5. `CLEANUP`: Finalize state, remove expired entities, and perform lifecycle maintenance.
6. `ADVANCEMENT`: Increment the world tick count.
7. `PERSISTENCE`: (Non-Authoritative) Stream logs and record snapshots.

## 5. Action Readiness Semantics
- Entities are eligible to act only when their readiness threshold is met.
- Readiness is a property of continuous simulation time, but eligibility is checked only at phase boundaries.
- Empty ticks (where no entity is ready) are valid and must progress time deterministically.

## 6. Deterministic Apply Order
- Updates to authoritative state must be applied in a stable, deterministic order.
- **Tie-Breaking**: If multiple updates occur at the same tick, an explicit tie-break rule (e.g., Entity ID or deterministic priority) must be used.

## 7. Deterministic RNG Contract
- All simulation randomness must flow through a singular `DeterministicRNG` interface.
- No authoritative logic may use:
    - `time.time()`
    - `random.random()`
    - Ambient thread/process state.
    - Unordered collection iteration.

### 7.1 RNG Consumption in Practice

Verified 2026-08-21 (TCK-20260817-DOC-COLLECTION-RNG-CONSUMPTION), resolving the open question
left in `docs/plans/kernel_concurrency_design_review_proposal.md` C7 with a direct trace rather
than an absence-of-grep-match inference.

**The Collection-phase worker path consumes no RNG.** A grep of `src/engine/worker_logic.py`,
`src/engine/domain_logic.py`, `src/engine/combat.py`, and `src/engine/movement.py` for
`rng`/`RNG`/`random.` finds zero matches — no import, no call, in any of the four files. This is
consistent with mechanics-bible design, not merely un-instrumented: `docs/mechanics/
02_combat_laws.md:11` states "The simulation follows a deterministic, non-random resolution for
all primary attacks."

The only RNG draw physically inside Collection-phase packet construction is
`src/engine/executor.py:301` (`packet_seed = rng.get_int(Domain.DEFAULT, state.tick,
item.owner_id, 0, 1000000)`), assigned to `WorkerPacket.seed` (`src/core/worker_protocol.py:29`)
at `executor.py:307`. This value is **dead**: `packet.seed` is never read by `worker_logic.py`,
`domain_logic.py`, `combat.py`, `movement.py`, or anywhere else under `src/` — it is only ever
*written*, and only otherwise referenced where test fixtures construct a `WorkerPacket` directly
(e.g. `tests/unit/kernel/test_worker_integrity.py`, `tests/integration/kernel/
test_worker_determinism.py`).

**Disposition — deferred, not removed.** `WorkerPacket` is a typed, frozen protocol dataclass
with `seed` threaded through roughly a dozen test call sites across
`tests/unit/kernel/test_worker_*.py`, `tests/unit/core/test_no_worker_direct_mutation.py`,
`tests/unit/core/test_signal_hardening.py`, `tests/unit/core/test_fallback_hardening.py`, and
`tests/integration/kernel/test_worker_determinism.py`, `test_authoritative_outcome_truth.py`,
`test_milestone_b_closure.py`, `test_milestone_d_closure.py`. Removing the field is a real (if
small) protocol-contract change, not the "trivial removal" this documentation-recording hotfix's
scope allows (see ticket Out of Scope) — left in place, tracked here rather than silently
ignored, for its own ticket to remove.

**The real RNG consumers all run in serial RESOLUTION, not parallel COLLECTION:**

| Consumer | Constructs `DeterministicRNG` at | Invoked from | Runs during |
|---|---|---|---|
| `EntityGenerator` | `src/systems/world_systems/generator.py:27` (`self.rng = DeterministicRNG(seed)`) | `src/engine/pipeline.py:281` (`world_dynamics` phase) / `src/engine/world_dynamics.py:23` | `AuthoritativeApplyPipeline.refine()`, called from `Kernel._phase_resolution()` (`src/engine/kernel.py:648`) |
| `QuestGenerator` | `src/quests/generator.py:135` (`rng = DeterministicRNG(seed)`, inside `generate()`) | `GuildAction.visit()` (`src/town/guild.py:43,78`) | `GuildVisitPhase.resolve()` (`src/engine/pipeline_phases/guild_visit.py`), wired in at `src/engine/pipeline.py:303-304` — same serial `refine()` call |
| `GuildAction` (the ticket's "GuildSystem" — the actual class is `GuildAction`) | `src/town/guild.py:43` (`rng = DeterministicRNG(state.seed)`) | `GuildVisitPhase.resolve()` | same as above |

All three are reached exclusively through `AuthoritativeApplyPipeline.refine()`, invoked from
`Kernel._phase_resolution()` — never from `Kernel._phase_collection()`
(`src/engine/kernel.py:563`), which only dispatches worker packets via `executor.py`. This matches
`docs/engine/kernel.md`'s "Phase Domain Permissions" table: COLLECTION's declared write domain is
`proposals` only; RESOLUTION is the sole phase with `entity`/`world` write access, and it is where
all of these generators actually run.

**Tension with "singular `DeterministicRNG` interface" above:** `EntityGenerator.__init__`
(`src/systems/world_systems/generator.py:27`) constructs its own `DeterministicRNG(seed)`
instance, separate from the instance the `Kernel` holds and passes into `executor.py`'s packet
construction. This is not a determinism violation — `DeterministicRNG` is stateless per call
(`src/platform/rng.py`: each `get_*` builds a fresh `random.Random` seeded by a pure hash of
`(base_seed, domain, tick, entity_id, sub_id)`), so a second instance seeded from the same
`state.seed` lineage produces identical results regardless of which object issues the call. But it
means the "singular interface" guarantee holds at the *type* level (one `DeterministicRNG` class,
one call contract) and not at the *instance* level (more than one live `DeterministicRNG` object
exists per tick) — worth knowing so a future reader doesn't assume instance-level singularity the
code doesn't actually provide.

## 8. Determinism Guarantees
**Same Seed + Same Runtime Profile + Same Inputs => Bit-Identical Authoritative State Checkpoints.**

## 9. Kernel Boundaries
- No scheduler optimization.
- No concurrency outside the bounded COLLECTION-phase worker pool: `WorkerManager`
  (`src/engine/worker_manager.py`) dispatches proposal generation across a profile-controlled
  `ThreadPoolExecutor`/`ProcessPoolExecutor`, per `bounded_concurrency_contract.md`. Every other
  phase — INIT, SCHEDULING, RESOLUTION, CLEANUP, ADVANCEMENT, PERSISTENCE — executes
  synchronously, and RESOLUTION collapses all COLLECTION-phase proposals through a single
  deterministic serial apply order (`ConcurrencyLaw`, `src/core/concurrency_law.py`; Deterministic
  Commit Law, `bounded_concurrency_contract.md` §3), so concurrent Collection execution never
  affects tick outcome.
- No adaptive degradation.
- No external event brokers.
