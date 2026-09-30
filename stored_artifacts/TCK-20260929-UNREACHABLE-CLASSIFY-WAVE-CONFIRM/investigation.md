---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-WAVE-CONFIRM
artifact_type: investigation
tags: [investigation, root-cause, corpus, world, simulation-quality]
---

# Investigation — TCK-20260929-UNREACHABLE-CLASSIFY-WAVE-CONFIRM

Three items: two record-only (verdicts established by PR #258, not re-derived) and one real classification. No `src/`
change. Environment: branch tip `3dbdff48a`; `search_docs`/`graphify` live.

## Record-only
- `CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` -> `DEFECT` (wave `J1`, `investigation.md` line 55): `apply_calamity_consequences`
  has no production caller. Freshness check only: still definition + one unit test + the wave's own architecture pin
  (`tests/architecture/test_calamity_intensity_producer_unwired.py`); `calamity.py` untouched since. Registry-side write
  stays with `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION`.
- `LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` -> `CONDITION`, **world-content** (wave `J2`, line 101): `moon_cave` is spatially isolated
  from every hostile faction; fresh 5,000-tick run showed `trauma_score == 0.0`. More ticks cannot help (AC-6 split recorded).

## Classification — `COMBAT-GATE-DOWNSTREAM-STARVATION` boss-gate half -> `CONDITION` (corpus run length)
A/B on the canonical harness (`frontier_living_world`, seed 42, 3,000 ticks, `PROD_SMALL`), flag `ENABLE_COMBAT_ENGAGEMENT`
`ON` vs `OFF`: first `world_boss` at tick **2101** in both, peak trauma **21.26** (`goblin_camp`) in both. The posture gate does
not touch the chain in this world; the ticket's starvation risk is not observed. Tick arithmetic: maturity +1 / 1000 ticks
(`calamity.py:17,31`), threshold 2.0 (`boss.py:26`) -> earliest spawn tick 2000; trauma threshold 8.0 (`boss.py:27`) met.
Runs under ~2,000 ticks cannot see the boss; the corpus spans 1,000-5,000. Owner proposed: SimQ corpus scope; `T06` decides.
No combat-volume number is cited. Limits: one world, one seed.

## Not done
Faction-chain half (resolved elsewhere); shared classification doc (-> `T06`); any registry write.
