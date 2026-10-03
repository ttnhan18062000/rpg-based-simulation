---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION
artifact_type: plan
tags: [world, determinism, observability, architecture]
---

# Plan — sovereignty ownership-writer consolidation

**Decision: outcome 3 of the ticket's three — two writers stay; the precedence between them is
documented; consolidation is deferred. No `src/` behaviour change.**

Owner-approved 2026-10-03 after the measurements in `investigation.md` §5/§5a. This is the ticket's own
third legitimate outcome ("Conclude two writers are correct and document why"), with one amendment:
they are not *correct*, they are **inert and undocumented**, which is why the deliverable is a
documented precedence rather than a defence.

## Why not consolidate

The consolidation was ranked as hard-bug work on the reading that ownership is "one durable fact held
with two conflicting live values". **Measurement retracts that** (`investigation.md` §5): 0 same-tick
overlaps in ≈48,000 region-ticks, 0 ownership writes from writer 2 in any natural run, both figures
positive-controlled. The structure is last-writer-wins on one field, not two live values.

With the premise gone, consolidation is a refactor on a near-inert path. `owner_decision_memo.md`
row 7 — the only copy of the hard-bug definition, not restated here — parks non-hard-bug work until its
(a) and (b) hold. The contract review found nothing blocking a phase move
(`investigation.md` §3), so this is deferred on **yield**, not on permission: it is available whenever
the foundation gate opens.

Recorded explicitly so the option is not re-litigated from scratch: if consolidation is ever taken up,
**option 2 (move settlement after `lifecycle`) is the one with no contract obstruction**, and §3 holds
the evidence.

## Steps

1. **`docs/world/regional_sovereignty_runtime_contract.md`** — amend the existing two-writer section
   (`:36-55`, which already records the two writers as a scoped decision) to add what it currently
   omits:
   - The precedence is **writer 2 overrides writer 1**, via `WorldUpdate.merge`'s other-wins rule at
     `core/updates.py:882`, with writer 2 merged into writer 1's entry at `lifecycle.py:303-307`. State
     it as a documented consequence, not an accident.
   - Writer 1 evaluates **last tick's** influence: `influence_delta`'s only producer
     (`influence.py:62`) runs 13 phases after its only consumer (`world_dynamics.py:89`); measured 0
     nonzero in 24,000 executions.
   - Writer 2 **emits no `SOVEREIGNTY_SHIFT`**, so any flip it performs is unobservable to
     `WorldEmergencePhase` — latent while writer 2 never writes, and the reason `WORLD-107` is not
     currently false.
   - Writer 2 is **measured inert for ownership** in the shipped corpus, with the measurement's scope
     and its explicit non-generalisation ("true zero for this corpus, not proof of impossibility").
   - Correct the stale call-site anchor to `lifecycle.py:298` / gate `294`.
2. **`docs/parity_ledger/world_dynamics.yaml`, `WORLD-107`** — append to `v2_evidence` only: that
   ownership has a second, non-emitting writer, measured to produce no ownership writes in ≈48,000
   region-ticks, which is why the entry's observability claim holds today. `status` stays `verified`
   — the entry's text makes no phase-position claim and its P1 `test_path` passes. Do **not** restate
   the measurement; cite this ticket. Use `tools/parity_ledger_writer.py`; check `git diff --stat`
   afterwards, since a full-file YAML rewrite is the known failure mode here.
3. **Add the AC-4 regression test** — the one piece of code this ticket does land. See `test_plan.md`.
4. **No `intentional_divergences.md` entry.** AC-5 requires one only for a timing change; there is no
   behaviour change, so an entry would record a change that did not happen. Stated here so the absence
   is a decision, not an omission. §2.58's deferral note (lines 1943-1947) is left standing — it
   correctly describes a still-deferred consolidation.
5. **No `authoritative_pipeline.md` phase-table edit.** Needed only if a phase moves. The doc's
   independent "39 phases vs 44 `run_phase` sites" drift is recorded in `investigation.md` §7 and is
   **out of scope here** — it is a pre-existing defect with its own test pinning the literal string.

## Scope guards

- **No file under `src/` is modified.** If a step seems to require one, stop: the decision was
  explicitly decision-only.
- Do not touch the `-1` sentinel defect (`investigation.md`, filed separately). It is a real, verified
  crash but dormant by row 7's test; fixing it here would be exactly the dormant-path work row 7 parks.
- Do not touch `registries/` or catalog files — `world-rule-catalog-design` owns that content, and the
  question of whether a Rule governs owner encoding is with them.
- Do not widen into `TERR-01`/`TERR-03`, the semantic overload, or `RegionalSovereigntyService`'s
  orphan status (`TCK-20260917-...-ORPHAN-TAXATION-DEBUFFS` owns that).

## Acceptance-criteria map

| AC | Discharged by |
|---|---|
| 1 — decision recorded with the phase-ordering consequence stated | This file: outcome 3, plus `investigation.md` §3's NOT-ADDRESSED verdict and the one-tick consequence |
| 2 — no ownership-transfer capability lost | Trivially: no behaviour change. Writer 1's non-death `HERO_GUILD` conquest path is untouched |
| 3 — `test_regional_ownership_flip` still passes | Unchanged and passing (baseline: 10 tests green) |
| 4 — a test asserts ownership is re-evaluated with no death that tick | New dedicated test, step 3 / `test_plan.md` |
| 5 — any timing change recorded | None exists; step 4 records why, deliberately |
| 6 — `WORLD-107` `status` + `v2_evidence` updated | Step 2 (`v2_evidence` only; `status` justified as unchanged) |

## What this ticket deliberately leaves on the table

Named so none of it is mistaken for an oversight:

1. The **`-1` sentinel crash** — verified end-to-end, filed separately, parked as dormant.
2. **Ownership dynamics are near-inert** — most regions at influence exactly `0.0` for 2000 ticks.
   Possibly the most consequential observation in this investigation, and squarely balance/tuning work,
   which row 7 parks. Not filed as a defect.
3. **`authoritative_pipeline.md`'s 39-vs-44 phase drift** and two stale `combat-mechanics` SKILL.md
   phase numbers (`investigation.md` §7).
4. A possible **determinism divergence** (same world, same seed, differing per-tick death
   distribution). Under a bounded confirm-or-refute probe; **not filed on one unreplicated
   observation**.
