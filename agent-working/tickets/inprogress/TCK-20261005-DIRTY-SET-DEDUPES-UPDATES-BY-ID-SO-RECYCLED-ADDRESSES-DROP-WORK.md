---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK
phase: implement
date: 2026-10-05
tags: [engine, determinism]
---

# TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK

## Title
`DirtySetBuilder.mark_from_update` de-duplicates entity updates by `id()`, so an update allocated at a
recycled address is silently skipped — the leading candidate cause of a confirmed, `audit_mode`-proof
determinism break

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
**The measurement in this ticket is `rpg-implementer`'s**, produced while closing
`TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` and reported to `rpg-planner`
on 2026-10-05. **Split out on the planner's ruling**: that ticket's acceptance criteria asked only
that the divergence be reproduced and characterised, which it was, and the fix needs two contested
files, a proof step and a bare-`main` comparison — more than belonged in a four-ticket batch.

**The confirmed finding** (that ticket, closed, with a positive control): `frontier_living_world`,
2000 ticks, `audit_mode=True`, `max_tick_budget_ms=1e9`, `LocalSequentialExecutor`,
`CanonicalStateHasher` every tick, `dropped_work_total` 0 and governor mode 0 on every tick. Four
identical seed-42 runs in fresh processes: three end `cc17cd69…`, one ends `a76fb7bf…`; one of the
three also diverged at tick 512 and **re-converged**. Seed-43 control differs at tick 1 in every
entity, so the instrument detects a difference when one exists. Distinct from `INFRA-273`.

**The proximate mechanism, measured.** First divergence at tick 5 (index 4), entities 16 and 36:
`navigation.target`, `current_project_id`, `current_objective_id` and a whole `projects` entry differ.
At tick 4 the `StrategicWorkQueue` candidate list differs between traces at identical budget (10) and
sweep interval (5). The **only** differing per-entity scheduling input is entity 16's membership in
`dirty.strategic_entities` — `True` in one trace, `False` in the other — which moves it from tier 6 to
the tier-7 background sweep, whose rotation then selects different entities under the budget.

**The upstream cause — a strong lead, explicitly NOT proven.**
`DirtySetBuilder.mark_from_update` (`src/core/dirty.py:141-146`):

```python
for e_id, e_upd in update.entity_updates.items():
    upd_id = id(e_upd)
    if upd_id in self._processed_upd_ids:
        continue
    self._processed_upd_ids.add(upd_id)
```

`id()` is unique only among **live** objects. Once an update object is garbage-collected, a later
update can be allocated at the same address, collide with the retained `upd_id`, and be **silently
skipped** — so its entity is never marked dirty. A shadow check found **~56 such skipped updates per
8-tick trial in every trial from tick 0** (range 53-60). That variance is itself the signature of an
allocation-dependent mechanism.

**What is NOT shown, and must not be assumed:** that entity 16's update was among the skipped ones in
a diverging run. The diverging trace did not reproduce in the last two probe runs.

**A second, untested hazard of the same shape:** `get_frozen` in `src/engine/executor.py:256-262`
caches frozen world views keyed on `id(obj)` (`CORE-PERF-020`). Same reuse risk, never probed.

**A documentation contradiction this creates.** `docs/engine/deterministic_execution.md:69` states
`audit_mode` "is the current way to get a deterministic run". The confirmed divergence happened **with
`audit_mode` on**, and the mechanism above reads no clock, so that sentence is now false.

## Scope
1. **Prove or refute the entity-16 link before fixing anything.** Hold a strong reference to every
   update object for the life of a trial (a shadow list) so addresses cannot be reused, and show the
   divergence disappears. That is the discriminator: if divergence survives with reuse impossible, the
   `id()` de-dup is not the cause and this ticket's premise is wrong.
2. **Run on bare `origin/main`.** The confirmed measurement ran on `main` plus three of the reporting
   session's tickets (none touching the dirty set). Whether `main` alone diverges, or is merely masked,
   is open and cheap to settle.
3. Only then fix: give the de-dup a stable identity that does not depend on allocation — the
   `(entity_id, …)` key the loop already has, or an explicit counter — rather than retaining strong
   references in production to keep `id()` unique. **Retaining references as the fix would trade a
   determinism bug for a memory leak; do not.**
4. Probe `executor.py`'s `get_frozen` for the same defect and report it either way. If it is live, say
   whether it belongs here or in its own ticket.
5. Correct `docs/engine/deterministic_execution.md:69` once the outcome is known, and record the
   change in `docs/guidelines/intentional_divergences.md` if the determinism claim changes class.
6. Add a regression test that fails on the `id()`-keyed de-dup. A test that merely runs twice and
   compares is not enough — the divergence is probabilistic and appeared after trial 7 in three of five
   instrumented experiments and never in the other two.

## Out of Scope
- `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE`'s own ACs. Met and closed.
- `INFRA-273`'s throttle, and the governor's `tick_compute_ms` path. Ruled out on this evidence
  (`dropped_work_total` 0, mode 0 every tick).
- `src/engine/tactical.py`. Explicitly **not** the source — the divergence is in strategic scheduling,
  before any tactical decision differs.
- The **parked** slow-regression determinism root cause. Owner-parked; do not re-raise or merge into it.
- Adding the dirty set to the canonical hash. Tempting, because the dirty set is not hashed and that is
  why hashes match until tick 5 — but it is derived per-tick state, not durable state, and hashing it
  would change what the canonical contract means. If it looks necessary, bring it to the planner.

## Acceptance Criteria
- [ ] Scope 1's strong-reference discriminator is run and its result stated. **"Divergence survived, so
      the `id()` de-dup is not the cause" is a valid and valuable outcome** — report it rather than
      hunting for a way to confirm the hypothesis.
- [ ] Scope 2's bare-`main` comparison is reported, with the commit named.
- [ ] If fixed: the de-dup key no longer depends on object identity, and no production code retains
      references to keep `id()` unique.
- [ ] `get_frozen` is probed and the result recorded either way.
- [ ] A regression test exists that fails deterministically on the old keying — not a flaky
      run-twice-and-compare.
- [ ] `deterministic_execution.md:69` is corrected, or the investigation records why it still stands.
- [ ] `docs/parity_ledger/infrastructure.yaml` updated (determinism/replay is its subsystem).
- [ ] The ~56-skipped-updates-per-8-tick figure is re-measured after the fix and reported.

## Related Tickets
- `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` (closed 2026-10-05) — the
  confirmed characterisation this ticket fixes. **Read it first**; its notes carry the trace detail.
- `TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN` (closed) — its AC-1/AC-4 corpus counts
  were **downgraded, not taken**, precisely because this divergence makes the protocol untrustworthy.
  Those counts become takeable when this lands.
- `TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES` (closed) — its
  A/B compared two arms of a single run each; same caveat.
- `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2` — adjacent, different mechanism.

## Related Docs
- `docs/engine/deterministic_execution.md` — `:62-69`, the claim this contradicts
- `docs/engine/kernel.md` — the 7-phase loop and the dirty-set stage
- `docs/parity_ledger/infrastructure.yaml`

## Related Stored Artifacts
- `agent-working/tickets/inprogress/TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE.md`
  at close carries the full trace notes; the probe itself was not committed — **ask for it rather than
  rewriting one.**

## Related Code Areas
- `src/core/dirty.py:141-146` — the `id()`-keyed de-dup. **CONTESTED SURFACE** (`src/core/**`): claim a
  hold from the planner before editing.
- `src/engine/executor.py:256-262` — `get_frozen`'s `id()`-keyed cache. **CONTESTED SURFACE.**
- `src/engine/checkpoint.py::CanonicalStateHasher` — the correct comparison instrument. **CONTESTED.**
- `src/systems/strategic_systems/` — `StrategicWorkQueue` tiering, the proximate symptom site

## Assumptions / Open Questions
- **The upstream cause is a lead, not a finding.** The reporting session said so plainly and this
  ticket keeps that framing. The ~56 skipped updates are real and measured; their connection to the
  observed divergence is not.
- Unexplained and recorded as such: the second trace appeared after trial 7 in three of five
  instrumented experiments and never in the other two. Nobody knows why trial 7.
- **A confirmed determinism break means every single-run measurement taken on this engine is a
  sample, not a value.** That includes measurements taken this week on the trauma, influence and
  attack-count paths. Order-of-magnitude conclusions survive; precise tick numbers and exact counts
  do not. Say so when citing any of them, and prefer a repeated or paired-arm measurement.
- Line numbers are at `da064fe78`.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
