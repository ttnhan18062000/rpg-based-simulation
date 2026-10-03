---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-DOC-COLLECTION-RNG-CONSUMPTION
phase: done
date: 2026-08-17
tags: [documentation, engine, determinism]
---

# TCK-20260817-DOC-COLLECTION-RNG-CONSUMPTION

## Title
Record where (if anywhere) DeterministicRNG is consumed during the tick, and flag executor.py:301's dead packet_seed

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
A grep across domain_logic.py/combat.py/movement.py/worker_logic.py for RNG call patterns found no matches, suggesting combat-roll randomness resolves later in serial Resolution rather than parallel Collection — but this was only confirmed by absence of a grep match. The author wants a definitive investigation of where (if anywhere) DeterministicRNG is consumed during the tick, with the finding recorded in kernel.md or the worker contract either way.

## Scope
- Write a finding (in docs/engine/kernel.md or docs/engine/contracts/simulation_kernel_contract.md) stating the only RNG draw physically inside Collection-phase worker dispatch is executor.py:301's packet_seed, computed but NOT read by worker_logic.py/domain_logic.py/combat.py/movement.py
- State explicitly that combat is deterministic/non-random by mechanics-bible design (docs/mechanics/02_combat_laws.md:11), resolving the open question rather than leaving it an absence-of-grep-match inference
- List the actual downstream RNG consumers found: EntityGenerator (via src/engine/pipeline.py, src/engine/world_dynamics.py), QuestGenerator (via src/engine/pipeline_phases/guild_visit.py, src/engine/quests.py, src/quests/generator.py), GuildSystem (via src/town/guild.py) — confirm these run in serial Resolution/apply, not parallel Collection
- Record the disposition decision for the dead packet_seed at executor.py:301 (remove/defer/wire to something real) explicitly rather than leaving it silently in place
- Add a one-line clarifying note on EntityGenerator constructing a second DeterministicRNG instance (src/systems/world_systems/generator.py) as a minor tension with simulation_kernel_contract.md §7's "singular DeterministicRNG interface" wording

## Out of Scope
- Functionally fixing the dead packet_seed unless the Plan phase explicitly scopes a trivial removal — this is a documentation-recording ticket, not a behavior-change ticket
- Any change to src/platform/rng.py's DeterministicRNG implementation itself

## Acceptance Criteria
- [x] A written finding (in kernel.md or simulation_kernel_contract.md) states the only RNG draw physically inside Collection-phase worker dispatch is executor.py:301's packet_seed, computed but not read by worker_logic.py/domain_logic.py/combat.py/movement.py
- [x] Finding explicitly states combat is deterministic/non-random by mechanics-bible design, resolving the open question rather than leaving it an absence-of-grep-match inference
- [x] Finding lists the actual downstream RNG consumers (EntityGenerator via pipeline.py/world_dynamics.py, QuestGenerator via guild_visit.py/quests.py, GuildSystem via town/guild.py) and confirms they run in serial Resolution/apply, not parallel Collection
- [x] If the team decides the dead packet_seed at executor.py:301 should be removed/deferred/wired to something real, that decision is recorded explicitly, not left silently in place

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC
- TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING

## Related Docs
- docs/engine/deterministic_execution.md
- docs/mechanics/02_combat_laws.md
- docs/engine/contracts/simulation_kernel_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/executor.py
- src/engine/kernel.py
- src/engine/worker_logic.py
- src/engine/domain_logic.py
- src/engine/combat.py
- src/engine/movement.py
- src/core/worker_protocol.py
- src/engine/pipeline.py
- src/engine/world_dynamics.py
- src/engine/pipeline_phases/guild_visit.py
- src/engine/quests.py
- src/systems/world_systems/generator.py
- src/quests/generator.py
- src/town/guild.py
- src/platform/rng.py

## Assumptions / Open Questions
- packet_seed at executor.py:301 is real dead code (computed, never read) — could confuse future readers into thinking it seeds per-worker randomness; documenting it is the requested fix, not silently removing it as unscoped scope creep
- EntityGenerator's second DeterministicRNG instance is a minor tension with the contract's "singular" wording — worth a one-line clarifying note only, not a functional fix

## Implementation Notes

Real code investigation (no assumptions taken from the ticket premise or the origin proposal
doc without independent verification):

1. **Collection-phase RNG absence** — `grep -n "rng\|RNG\|random\." src/engine/worker_logic.py
   src/engine/domain_logic.py src/engine/combat.py src/engine/movement.py` returned zero matches
   in all four files. Confirms the ticket's premise exactly as stated.
2. **Dead `packet_seed`** — `src/engine/executor.py:301` computes `packet_seed =
   rng.get_int(Domain.DEFAULT, state.tick, item.owner_id, 0, 1000000)` and assigns it to
   `WorkerPacket.seed` (`src/core/worker_protocol.py:29`) at `executor.py:307`. Repo-wide grep for
   `packet_seed` and for `.seed` attribute access inside `worker_logic.py`/`domain_logic.py`/
   `combat.py`/`movement.py` found no reads anywhere in `src/` — confirmed genuinely dead. It is
   only ever set as a constructor arg in ~11 test files
   (`tests/unit/kernel/test_worker_integrity.py`, `test_worker_bounds.py`,
   `test_worker_fallback.py`, `test_worker_adaptation.py`,
   `tests/unit/core/test_no_worker_direct_mutation.py`, `test_signal_hardening.py`,
   `test_fallback_hardening.py`, `tests/integration/kernel/test_authoritative_outcome_truth.py`,
   `test_milestone_b_closure.py`, `test_worker_determinism.py`, `test_milestone_d_closure.py`).
3. **Combat determinism claim** — read `docs/mechanics/02_combat_laws.md:11` directly: "The
   simulation follows a deterministic, non-random resolution for all primary attacks." Confirmed
   verbatim.
4. **Downstream RNG consumers** — traced by grep + read, not assumed from the proposal doc:
   - `EntityGenerator.__init__` constructs `DeterministicRNG(seed)` at
     `src/systems/world_systems/generator.py:27`. Instantiated at `src/engine/pipeline.py:281`
     and consumed by `WorldDynamicsSystem.resolve_dynamics` (`src/engine/world_dynamics.py:23`),
     both inside `AuthoritativeApplyPipeline.refine()`.
   - `QuestGenerator.generate()` constructs `DeterministicRNG(seed)` at
     `src/quests/generator.py:135`. Called from `GuildAction.visit()`
     (`src/town/guild.py:43,78`), which is invoked by `GuildVisitPhase.resolve()`
     (`src/engine/pipeline_phases/guild_visit.py`), wired into the pipeline at
     `src/engine/pipeline.py:303-304`.
   - The ticket/proposal called the third consumer "GuildSystem" — the actual class name in
     `src/town/guild.py` is `GuildAction` (no `GuildSystem` class exists in that file). Corrected
     in the doc finding rather than silently perpetuating the wrong name.
   - Confirmed phase placement: `AuthoritativeApplyPipeline.refine()` is called only from
     `Kernel._phase_resolution()` (`src/engine/kernel.py:648`), never from
     `Kernel._phase_collection()` (`src/engine/kernel.py:563`), which only dispatches worker
     packets via `executor.py`. Matches `docs/engine/kernel.md`'s Phase Domain Permissions table
     (COLLECTION write domain = `proposals` only; RESOLUTION is the sole `entity`/`world` writer).
5. **Second `DeterministicRNG` instance tension** — confirmed `EntityGenerator.__init__`
   (`src/systems/world_systems/generator.py:27`) builds its own `DeterministicRNG(seed)`,
   separate from the Kernel's own instance passed into `executor.py`. Read
   `simulation_kernel_contract.md` §7's exact wording ("All simulation randomness must flow
   through a singular `DeterministicRNG` interface") before writing the clarifying note: the
   interface is singular at the *type* level, not the *instance* level — not a determinism
   violation since `DeterministicRNG` is stateless per call (fresh `random.Random` per call,
   seeded by a pure hash of inputs), but worth flagging so it isn't misread as instance-level
   singularity.

No contradiction of the ticket's premise was found anywhere — all five claims verified true
against real code.

**Doc chosen**: `docs/engine/contracts/simulation_kernel_contract.md`, as a new `### 7.1 RNG
Consumption in Practice` subsection directly under §7 "Deterministic RNG Contract" — that section
already carries the "singular `DeterministicRNG` interface" wording the EntityGenerator note
needs to attach to, making it the better fit over `kernel.md` for this specific finding (per the
ticket's own guidance to check §7 first).

**`packet_seed` disposition — deferred, not removed.** `WorkerPacket` is a typed, frozen protocol
dataclass (`src/core/worker_protocol.py`); removing the `seed` field would require touching the
protocol definition plus ~11 test call sites that construct it directly. That is a real (if
small) contract change, not the "trivial removal" this hotfix's Out of Scope section permits —
so it stays in place, its dead status now documented explicitly rather than left silent, tracked
for a future dedicated ticket to actually remove.

## Test Summary
Ran `pytest tests/architecture/test_phase_domain_permissions.py
tests/integration/kernel/test_worker_determinism.py
tests/integration/kernel/test_executor_determinism.py -q` — 11 passed, 0 failed. This is a
docs-only change (no source files touched), so this run confirms no regression rather than
testing new behavior.

## Files Changed
- `docs/engine/contracts/simulation_kernel_contract.md` — added `### 7.1 RNG Consumption in
  Practice` under §7, recording the Collection-phase RNG-absence finding, the dead `packet_seed`
  citation and disposition decision, the combat-determinism citation, the three real downstream
  RNG consumers with file:line evidence and phase placement, and the EntityGenerator
  second-instance clarifying note.
- `docs/plans/kernel_concurrency_design_review_proposal.md` — added a completion cross-link after
  the C7 section and updated Appendix A's duplicate "Open question" line to "now resolved", both
  citing §7.1.
- `docs/engine/kernel.md` — added a one-sentence cross-link under the Phase Domain Permissions
  table's "Key invariant" line, confirming §7.1's traced RNG consumers all run in RESOLUTION.
- `docs/parity_ledger/substrate.yaml` — strengthened `SUB-272` ("Deterministic RNG repeats exactly
  for same seed/domain/entity/tick", P0) with this finding as `v2_evidence`, and filled its
  pre-existing missing `test_path` (a gap not caused by this ticket, but required to be filled
  before the entry could be validly updated at all, per the writer's P0-needs-test_path rule) with
  `tests/unit/core/test_rng_contract.py::test_rng_reproducibility` (3/3 passing, confirmed a real
  match for the entry's claim). Only this one entry changed semantically — the rest of the file's
  large diff is the validating writer's cosmetic re-serialization of all 396 entries, confirmed via
  a parsed-YAML structural diff.
- `tickets/inprogress/TCK-20260817-DOC-COLLECTION-RNG-CONSUMPTION.md` — this file: Status → DONE,
  all 4 Acceptance Criteria checked, Implementation Notes/Test Summary/Files
  Changed/Completion Summary filled in.

## Completion Summary
Verified all five claims in the ticket's scope against real source code (not inferred from the
originating proposal doc) and recorded the finding in
`docs/engine/contracts/simulation_kernel_contract.md` §7.1: the Collection-phase worker path
(`worker_logic.py`/`domain_logic.py`/`combat.py`/`movement.py`) consumes zero RNG; the only RNG
draw in Collection-phase packet construction is `executor.py:301`'s `packet_seed`, confirmed
genuinely dead and explicitly deferred (not removed) rather than silently left undocumented;
combat's deterministic-by-design status is confirmed against `02_combat_laws.md:11` verbatim; the
three real downstream RNG consumers (`EntityGenerator`, `QuestGenerator`, `GuildAction` — corrected
from the ticket's "GuildSystem") are traced with file:line citations and confirmed to run only
inside `Kernel._phase_resolution()`, never `_phase_collection()`; and `EntityGenerator`'s second,
separate `DeterministicRNG` instance is flagged as a type-level-vs-instance-level nuance against
§7's "singular interface" wording. No claim in the ticket was contradicted by the code. Regression
tests for the touched-adjacent determinism/phase-permission suite pass (11/11).
