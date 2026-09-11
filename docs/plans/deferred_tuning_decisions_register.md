---
status: active
layer: simulation
authority: P1
audience: agent
tags: [calibration, audit]
---

# Deferred Tuning Decisions Register

**Document type:** REGISTER — a durable index of balance/number decisions deliberately deferred, so
they are not lost when the work that surfaced them closes.

**Why this exists.** Standing user direction (2026-09-11): *defer balancing and number-adjustment;
focus on wiring and ensuring core RPG logic actually delivers the feature, even if the stats look
wrong.* That is the right call — a mechanism that runs with bad numbers beats one that does not run.
But it produces a specific risk: each deferral is recorded inside whichever ticket happened to
surface it, those tickets close, and the deferred question becomes unfindable. This register is the
single place to look when balance work is picked up.

**What belongs here:** a number, threshold, rate, or formula whose *value* was deliberately not
decided during wiring work.

**What does NOT belong here:** anything where the mechanism itself is wrong, unwired, or
unreachable. Those are defects and get their own tickets. See the Reachability caveat below — the
distinction is easy to get wrong in the direction that hides real bugs.

**Feeds into:** `docs/audits/D04_balance_tuning.md` and `docs/plans/long_term_development_roadmap.md`
Epic 1.2 (Balance & Tuning Baseline). This register is the inbox; those are where the work is
planned.

---

## ⚠️ Reachability is not tuning

The most important entry in this document is not a number.

A mechanism gated behind a threshold that no real run ever reaches **does not deliver its feature**.
That looks like a tuning problem and is not one — the threshold's *value* is a number and defers,
but whether the mechanism is ever *reachable* is wiring and is in scope now.

Two live examples are recorded below (D-05, D-06). Both were originally treated as accepted
long-horizon divergences. Under the wiring-first rule that disposition is questionable: we may have
formally documented "this feature never runs" as though it were a design choice.

**Test to apply:** before filing something here, ask *"if this number stays exactly as it is, does
the mechanism still execute in a real run?"* If no, it is not a deferred tuning decision — it is a
reachability defect and needs a ticket.

---

## Register

### D-01 · Camp raid size formula
**Deferred from:** `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX` (done) →
`TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH` (open)

`docs/world/raid_boss_camp_contract.md:138` specifies `raid_size = 3 + camp.maturity`. The code
(`src/world/raid.py:34`) computes `RAID_BASE_SIZE + state.maturity`.

- Doc formula: camps trigger at `camp.maturity >= 80`, so it yields **~83 raiders** — from a camp
  whose own `monster_cap` is `max(2, int(camp.maturity / 10))` = **8**. Internally inconsistent.
- Code formula: `state.maturity` stays near 0 for ~50,000 ticks, so every raid is **~3 raiders**
  regardless of camp maturity. The scaling mechanic is effectively inert.

**Neither reads as designed.** Mechanism is wired and works; only the number is open.
**Needs:** a real intended raid size, and whether it should scale off camp or world maturity.

### D-02 · Cooperation trust deltas
**Deferred from:** `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION` (open)

`src/domains/cooperation/services.py:350-372` computes real deltas: `+0.08`, `+0.22`, `-0.25`,
`-0.75` by interaction outcome. These are deliberately left untouched while the wiring bug (trust
never accumulating at all) is fixed.

**Do not tune until trust demonstrably accumulates.** Once it does, these values and D-03's
threshold should be evaluated together against real run data, not in isolation.

### D-03 · Grief ally-trust threshold
**Deferred from:** `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION` (done, partial)

`ALLY_TRUST_THRESHOLD = 0.30` gates whether an entity grieves a death. Currently unreachable in
practice because `trust_history` is empty (see D-02) — but that is a wiring bug, not this number's
fault.

**Sequencing matters:** fix D-02's wiring first, keep `0.30` fixed, and re-observe. If grief still
never fires with trust accumulating, *then* this is a real tuning question. Changing it now would
mask the wiring bug.

Note also that cooperation consumers read trust as `.get(id, 0.5)` — defaulting to neutral — while
grief requires a genuine entry. Whether that asymmetry is intended is a **design** question, not a
tuning one.

### D-04 · Population count expansion — density consequences
**Deferred from:** `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE` (open)

`PopulationSpec.count` declares N; `WorldEntitySpawner` spawns exactly 1 per population group.
`compiler.py:268-276` meanwhile sums `count` into `region_declared_population`, so declared and
actual already diverge.

Expanding count to spawn N is **wiring** and is in scope now. The consequence — world population
multiplying by whatever the corpus declares, affecting combat volume, economy throughput, and tick
cost — is **tuning** and is deferred.

**Accepted outcome:** runs may become heavy or unbalanced after the fix. That is explicitly not a
reason to leave the mechanism broken.

### D-05 · World-maturity gate for lairs and world bosses ⚠️ reachability
**Deferred from:** `TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN` (done — disposition may need
revisiting)

`state.maturity >= 50` gates both Lair-occupant and `check_for_boss_spawn` (world_boss /
ancient_sentinel). Maturity increments +1 per 1000 ticks (`calamity.py`, `MATURITY_INTERVAL`), so
the gate needs **~50,000 ticks** — against a corpus whose runs are 200-5,000 ticks.

That ticket closed by accepting this as a disclosed long-horizon divergence. **Under the
wiring-first rule that is worth revisiting:** the honest finding may be "lairs and world bosses
never spawn in any real run," which is a feature not delivering rather than a number being large.

- If ancient-world-only lairs are the actual design intent → the value stays, and the divergence
  record is correct.
- If `50` was never tuned → the feature is effectively absent and this is a defect.

**Needs a design-intent answer**, not a balance pass.

### D-06 · Faction war declaration frequency ⚠️ reachability
**Deferred from:** `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT` (done) and
`TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION` (done)

Sieges require a formal `DiplomaticState.WAR` between factions
(`src/engine/military_conflict.py:201`). No WAR was declared in any observed run, including a real
200-tick `campaign_life_arc` episode. Consequently siege progression, territory transfer, and
`EXPAND_TERRITORY` never fire, despite all being live, wired code.

Siege completion itself is fast once war exists (`_SIEGE_PROGRESS_DELTA = 0.05`/tick, offset
`-0.02` with ≥3 defenders → ~20-34 ticks). **The bottleneck is war never starting, not siege being
slow.**

Same caveat as D-05: how *often* factions should go to war is tuning; whether they *ever* do in a
real run is reachability.

### D-07 · Survivor placement — narrative intent
**Deferred from:** `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION` (open)

Multi-episode campaigns currently reconstruct every survivor at `(0.0, 0.0)`, colliding immediately.
The wiring fix (deterministic placement from each survivor's own `spawn_region`, reusing
`TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`'s de-confliction) proceeds now without
waiting on this.

**Open, non-blocking:** where survivors *should* narratively reappear between episodes — their last
known position, a settlement, their home region, or their original authored `spawn_region`. These
imply different campaign fictions. The wiring fix picks the last option as the one that is
defensible and deterministic; revisit when campaign narrative structure is designed.

### D-08 · Divergent thresholds lost to superseded-code deletion
**Deferred from:** `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (done),
`TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`,
`TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION` (open)

The audit found superseded implementations carrying *different* numbers from their live
replacements. Those numbers are being deleted with the dead code. Recorded here because someone
once chose them deliberately, and they may be better:

| Mechanism | Live (kept) | Superseded (deleted) |
|---|---|---|
| Biological decay rate | `hunger +0.1`, `sleep_debt +0.05`, cadence-scaled (`apply.py:89-90`) | `0.5%` / `0.3%` flat (`BiologicalSystem.update()`) |
| Passive-damage thresholds | hunger `≥95`, sleep_debt `≥98` (`apply.py:99-100`) | `90` / `95` |
| Degradation levels | `1.5x` / `1.0x` / `0.7x` (`engine/governor.py`) | `1.0` / `0.95` / `0.8` (`optimization/degradation.py`) |

**No action implied** — the live values stand. This is a record that an alternative calibration
existed, in case current values prove wrong.

---

## Related

- `docs/audits/D04_balance_tuning.md` — existing balance audit; this register feeds it.
- `docs/plans/long_term_development_roadmap.md` Epic 1.2 — where balance work is planned.
- `docs/plans/agent_infrastructure/reachability_verification_findings.md` — why "documented as
  deferred" is not the same as "will be found later"; the motivation for keeping this register in
  one place rather than distributed across closed tickets.
