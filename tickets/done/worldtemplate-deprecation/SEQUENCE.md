# Implementation Sequence — TCK-20260701-WORLDTEMPLATE-DEPRECATION-EPIC

Parent epic: `tickets/todos/worldtemplate-deprecation/TCK-20260701-WORLDTEMPLATE-DEPRECATION-EPIC.md`
Consumer (existing, external to this folder): `tickets/inprogress/TCK-20260701-SANDBOX-MONSTER-BALANCE.md` (`BLOCKED`)

---

## Stage 1 — No blockers (run in any order / parallel)

```
TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE
TCK-20260701-HAZARD-NATIVE-IMMUNITY
```

- `SANDBOX-WORLDCOMP-MIGRATE` touches `data/worlds/sandbox_world/` content only, reusing
  existing `worldcomposition.v1` modules and resolution machinery. No dependency on the
  hazard fix.
- `HAZARD-NATIVE-IMMUNITY` touches `src/world/environment.py` only. No dependency on the
  schema migration — it's a general engine fix applicable to every world's hazard mechanic.

## Stage 2 — Requires SANDBOX-WORLDCOMP-MIGRATE to be resolved first

```
TCK-20260701-WORLDTEMPLATE-REMOVE
```

**Why the gate:** `WORLDTEMPLATE-REMOVE` deletes the `worldtemplate.v1` CLI branches and
expansion code. `sandbox_world` is currently the only world still authored as
`worldtemplate.v1` — removing the schema before migrating it would break the only remaining
consumer. `SANDBOX-WORLDCOMP-MIGRATE` must land first so zero worlds depend on the schema
being removed.

`HAZARD-NATIVE-IMMUNITY` does NOT gate `WORLDTEMPLATE-REMOVE` — they're unrelated subsystems
(hazard mechanics vs. schema/CLI), safe to land in any order relative to each other.

## Stage 3 — External consumer, not implemented in this batch

```
TCK-20260701-SANDBOX-MONSTER-BALANCE   (tickets/inprogress/, not in this folder)
```

This ticket is `BLOCKED` after two failed attempts (stat differentiation, spawn placement)
and is expected to resolve once both `SANDBOX-WORLDCOMP-MIGRATE` (real monster stats) and
`HAZARD-NATIVE-IMMUNITY` (monsters survive their own habitat's hazard) have landed. It should
be re-verified — not blindly closed — via an empirical 200-tick re-run once both land, since
either fix alone may not fully resolve the tick-8 extinction (verify, don't assume).

---

## Status at creation

| Ticket | Status | Gate |
|---|---|---|
| TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE | OPEN | None |
| TCK-20260701-HAZARD-NATIVE-IMMUNITY | OPEN | None |
| TCK-20260701-WORLDTEMPLATE-REMOVE | OPEN | SANDBOX-WORLDCOMP-MIGRATE |
| TCK-20260701-SANDBOX-MONSTER-BALANCE (external) | BLOCKED | SANDBOX-WORLDCOMP-MIGRATE + HAZARD-NATIVE-IMMUNITY |
