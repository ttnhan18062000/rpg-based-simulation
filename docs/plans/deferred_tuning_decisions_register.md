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

**Corrected (2026-09-11) — the original entry here favored the authored `spawn_region` option as
"defensible and deterministic" before this was checked. It is wrong: `spawn_region` does not
survive past `WorldEntitySpawner.spawn_from_context()`.** That method hardcodes
`EntitySpawnContext(spawn_region=None, ...)`, so no campaign-spawned entity's `spawn_region` ever
reaches `EntityCarryForward`, `StrategicComponent.home_region_id`, or anywhere else on the live
entity — reusing `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`'s
`_resolve_spawn_position()` directly is not available; it requires a `spawn_region` string no
survivor has. Recovering it would need new wiring across `entity_spawner.py` +
`archetype_factory.py` + a new `EntityCarryForward` field (see the newly-filed threading-gap
ticket below) — a materially bigger change than this entry originally implied.

The wiring fix instead carries each survivor's own `entity.navigation.position` (their real last
position when the episode ended, already computed live by the simulation) into a new
`EntityCarryForward.last_position` field, reused at reconstruction with a light deconfliction pass
(`_DECONFLICT_PROBE_OFFSETS`, no region-bounds machinery needed). This is both the cheaper fix and
the one the data actually supports.

**Second correction, also found before implementation started**: region *bounds* are authored and
stable across episodes (`RegionSpec.bounds`, read verbatim by `WorldCompiler.compile()`), but
per-tile terrain (`compiler.py`'s `rng.weighted_choice` over `terrain_variants`) and building
placement (`rng.get_int(..., seed=episode_seed)` into `blocked_tiles`) are both drawn from the
per-episode seeded RNG (`episode_seed = base_seed + episode_index`, different every episode). A
carried `last_position` is therefore only guaranteed to be within its region's bounds next
episode, not guaranteed walkable or building-free — `blocked_tiles` is a real legality gate
(`src/engine/legality.py:70-76`), not cosmetic. The fix needs a validity check with a fallback for
when the carried position lands on now-blocked terrain, not a bare carry-through.

**Open, non-blocking:** where survivors *should* narratively reappear between episodes — their last
known position, a settlement, their home region, or their original authored `spawn_region`. These
imply different campaign fictions; last-known-position is the wiring fix's pragmatic default given
what's actually recoverable, not a narrative conclusion. Revisit when campaign narrative structure
is designed — including whether `spawn_region` threading (see below) later makes the "authored
region" option viable again.

**Third correction (2026-09-13) — the threading gap named above is now closed, but only partway.**
`TCK-20260911-ENTITYSPAWNCONTEXT-SPAWN-REGION-THREADING-GAP` wired `spawn_region` from
`PopulationSpec` through `ResolvedEntityProfile` (a new field, previously absent — the gap was one
level upstream of what this entry originally guessed) and into `EntitySpawnContext`, so
`identity.properties["spawn_region"]` is now genuinely populated on freshly-spawned
archetype-native entities, matching what the classic `WorldCompiler.compile()` pipeline already did.

**Precisely what changed and what didn't**: the value now reaches the live entity's
`identity.properties` dict. It does **not** reach `EntityCarryForward` (which has no region field
of any kind — confirmed via inspection, nothing to carry it into) or
`StrategicComponent.home_region_id` (a separate, real mechanism for a different purpose — idea 59
displacement/reproduction homes, set by `src/world/displacement.py`/`src/world/boss.py`, never
from spawn-time `properties["spawn_region"]`). So the authored-region option is **not yet viable**
for survivor reconstruction specifically — that would need a further hop (reading
`properties["spawn_region"]` at episode-end and carrying it forward the same way `last_position`
is carried today), which is new campaign-side wiring, not a byproduct of the threading fix. The
correct summary for whoever revisits the narrative question: *profile and spawn context now carry
the region name; campaign carry-forward still does not.*

The `last_position` fix stands regardless of this correction — it remains the better default, and
this entry's second correction (per-episode terrain/`blocked_tiles` reseeding invalidating any
carried position's walkability) applies identically to an authored-region carry-forward if one is
ever built.

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

### D-09 · Recruitment-offer acceptance criteria
**Deferred from:** `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION`

Wiring `CooperationPosture.JOIN_PARTY` (the designed-but-never-connected accept half of
recruitment-offer party formation — see that ticket's own investigation.md for the full trace) is
**wiring** and is in scope. What conditions should govern *whether* an entity accepts a given
pending offer — trust level toward the offerer, whether the entity's own current need matches what
the offer provides, faction alignment, existing commitments/cooldowns, personality — is **tuning**
and is explicitly deferred, per the user's own standing rule that acceptance-criteria design is a
separate decision from making the mechanism reachable at all.

**Shipped minimal condition** (`CooperationDecisionService.find_pending_incoming_offer()`,
`src/domains/cooperation/services.py`): a pending, unexpired `OFFERED` `RECRUITMENT` contract
exists targeting this entity, the offering entity is alive and active, and this entity is not
already in a group. First qualifying offer wins, deterministically ordered. No trust check, no
need matching, no faction check, no rejection path at all — every qualifying offer is accepted.

**Accepted outcome:** an entity will accept a recruitment offer from anyone, regardless of
trust/history/faction, as long as it isn't already grouped. This may look "too agreeable" once
groups form frequently in real runs. That is a tuning question for a future pass, not a defect in
the wiring — see `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION`'s own Completion
Summary for the real before/after evidence this minimal condition already produced.

---

### D-10 · Observed behavioral shift from actually enabling `ENABLE_GUILD_QUEST_GENERATION`
**Deferred from:** `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`

Recorded as an **observed consequence**, not a tuning question needing a number decided — nothing
here is being deferred for later calibration; it's the evidence that a previously-inert mechanism
does what it was designed to do, once actually reached.

**Correction, made the same day this was first recorded**: the measurement below was obtained by
setting `ENABLE_GUILD_QUEST_GENERATION` via an explicit env-var override, **not** by running an
unmodified corpus world at the flag's new `FeatureFlagManager` default. That default does not
currently propagate to any real run at all — confirmed via `TCK-20260913-FEATURE-FLAG-DEFAULT-
DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS`. State it bluntly: this measurement shows the mechanism
genuinely works when actually enabled; it does **not** show the default flip delivering that
behavior in a real run, and `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`
stays `BLOCKED`, not `DONE`, specifically because of that gap.

**Measured** (`frontier_living_world`, seed 42, 500 ticks, `tools/calibrate_simq.py`, before/after
identical except the one flag, set via explicit override):

| Pillar | OFF (before) | ON (after, explicit override) |
|---|---|---|
| COGNITION | B, norm +0.024, 2 events | **S, norm +3.446, 346 events** |
| INFORMATION | B, norm +0.080, 1 event | **S, norm +30.344, 519 events** |
| COMBAT | A, norm +1.774, 313 events | A, norm +1.272, 230 events |
| PROGRESSION | C, norm -0.016, 58 events | B, norm +0.1844, 59 events |
| SOCIAL | S, norm +74.792, 10021 events | S, norm +58.394, 7800 events |
| Overall | S, score 7.9386 | S, score 9.6644 |

COGNITION and INFORMATION both moved a full letter grade (B→S) with event counts jumping by two
orders of magnitude — this is the mechanism actually running for the first time, not noise.
`decision_diverged_by_belief` appeared 506 times in the ON run (real route-scoring decisions
influenced by belief/lead state) — real evidence beliefs are changing decisions, which is the thing
the whole initiative was for, obtained under an explicit override rather than the flag's own
default. COMBAT and SOCIAL both moved down while staying in their existing letter grade — plausible
knock-on effects of entities spending ticks on guild visits instead of other activity, not
investigated further. PROGRESSION improved. None of these numbers need a decision; they stand as
the record of what happens once the propagation gap above is actually resolved and this reaches
real runs by default.

**Accepted outcome:** these shifts stand as measured, unTuned. If any pillar's new grade is judged
unacceptable on gameplay-feel grounds in a future pass, that is a tuning decision to make then,
against real data, not a reason to have withheld the wiring fix now.

**Second correction, 2026-09-13, after `TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-
STATE-FEATURE-FLAGS` and `TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` landed**:
re-ran the same measurement against the same unmodified `frontier_living_world` profile with **no
env var** — the real acceptance signal. Direct instrumentation confirmed `GuildAction.visit()`
fires identically (same 4 calls, same ticks, same entities) whether the flag reaches `ON` via
explicit env-var override or via the propagation fix's own default-seeding. At the event level
(`decision_divergence_detected`, the real COGNITION-scorer event type — not the similarly-named
`decision_diverged_by_belief`, which is an INFORMATION-scorer event, see below): **4 of 5 no-env-
var/explicit-ON samples produced 344 real events and COGNITION graded S; every explicit-OFF sample
produced 0 events and graded B** — a clean, reproducible, binary signal that COGNITION genuinely
depends on this flag reaching real runs, now confirmed working by default.

**One anomalous sample** (the very first no-env-var run attempted) produced 0 `decision_divergence_
detected` events despite `GuildAction.visit()` having fired identically to every other sample —
consistent with this project's own already-documented wall-clock-timing-driven kernel-throttle
non-determinism (the same class of confound behind the NARRATIVE-pillar flakiness noted earlier
this batch, and `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2`), not a defect in the
propagation fix — 4 repeated, consistent samples since outweigh the 1 outlier.

**INFORMATION's own movement in the table above does not actually track this flag — correcting
that attribution rather than let it stand implied.** `decision_diverged_by_belief` (INFORMATION's
own scorer event, confirmed by reading `InformationScorer.EVENT_TYPES`) fired **506 times in a
fresh explicit-OFF run today** — identical to a same-day ON run — and a fresh OFF baseline graded
INFORMATION **S**, not the **B, 1 event** the original table above reports. INFORMATION's real
driver is `ENABLE_BELIEF_ASSIMILATION` (already `ON` via this profile's own YAML, independent of
`ENABLE_GUILD_QUEST_GENERATION`); the original OFF-baseline INFORMATION reading was either stale
(commits since then, including this batch's own `LeadState.detail` fix, changed how many leads the
belief-confirmation loop successfully processes) or itself an artifact of the same run-to-run
timing noise. Either way, INFORMATION moving is real and current, but not caused by this flag —
the original framing ("COGNITION and INFORMATION both moved... the mechanism actually running")
overstated INFORMATION's own connection to this specific fix. COGNITION's own connection is the
one confirmed clean and specific to this flag.

`TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` closes `DONE` on this
evidence — see that ticket's own updated Completion Summary for the full picture.

---

## Related

- `docs/audits/D04_balance_tuning.md` — existing balance audit; this register feeds it.
- `docs/plans/long_term_development_roadmap.md` Epic 1.2 — where balance work is planned.
- `docs/plans/agent_infrastructure/reachability_verification_findings.md` — why "documented as
  deferred" is not the same as "will be found later"; the motivation for keeping this register in
  one place rather than distributed across closed tickets.
