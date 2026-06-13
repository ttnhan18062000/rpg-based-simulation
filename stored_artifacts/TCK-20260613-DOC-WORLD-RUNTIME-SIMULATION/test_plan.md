# Test Plan — TCK-20260613-DOC-WORLD-RUNTIME-SIMULATION

Date: 2026-06-13
Status: Active

---

## Ticket Type

Documentation ticket. No new code is written. Verification is structural and semantic — confirming that written docs accurately reflect source behavior and that the knowledge index updates cleanly.

---

## Verification Checklist

### 1. Structural Completeness

For each of the 5 docs, verify:

- [ ] File exists at the correct path in `docs/world/` (no numbered prefix)
- [ ] Frontmatter block is present with: `status: active`, `layer: world`, `authority: P1`, `audience: agent`, `last_verified: 2026-06-13`
- [ ] All template sections are present: Purpose, RPG Meaning, Inputs, Core Rules, Formula/Decision Logic, Lifecycle, Mutation Rules, Edge Cases, Examples, Source Areas, Regression Tests, Extension Rules

### 2. Compliance ID Accuracy

- [ ] `ecology_and_calamity_contract.md` cites: SUB-006, WORLD-023, WORLD-024, WORLD-025, WORLD-026, WORLD-027, WORLD-028, WORLD-029, WORLD-060, WORLD-061, WORLD-063
- [ ] `threat_and_consequences_contract.md` cites: WORLD-006, WORLD-062 (plus WORLD-082–084 from parity ledger for calamity consequences)
- [ ] `raid_boss_camp_contract.md` cites: WORLD-030, WORLD-031, WORLD-032, WORLD-033, WORLD-034, WORLD-035, WORLD-036, WORLD-037, WORLD-048, WORLD-049, WORLD-077–081, WORLD-085–086
- [ ] `opportunity_providers_contract.md`: no source header IDs — confirm no IDs are fabricated
- [ ] `regional_sovereignty_runtime_contract.md` cites: SUB-275, SUB-276, SUB-277, SUB-278, SUB-279, WORLD-038, WORLD-041, WORLD-042, WORLD-043, WORLD-052, WORLD-053, WORLD-054, WORLD-055, WORLD-056, WORLD-057, WORLD-058, WORLD-059

### 3. Behavioral Accuracy Spot Checks

These specific claims must be verifiable against the source files read during investigation:

**Ecology:**
- [ ] Interval is stated as 200 ticks (ECOLOGY_INTERVAL = 200 in ecology.py line 16)
- [ ] Target formula is `int((area / 40_000) * (1 + stability))` with minimum 1
- [ ] Seeding chance is 50% per qualifying tick
- [ ] Node kinds: FOREST→WOOD, MOUNTAIN→IRON, others→STONE

**Calamity:**
- [ ] Maturity advances every 1000 ticks
- [ ] Forced spawn fires at tick % 5000 if last calamity ≥ 2000 ticks ago
- [ ] Spawn requires region with calamity_intensity > 0.3; picks highest
- [ ] Spawned entity is world_boss at difficulty_tier=4
- [ ] Hero death in hazard > 0.5 region raises intensity +0.05 (capped 1.0)
- [ ] CALAMITY_RANDOM_CHANCE is documented as defined-but-inactive

**Threat:**
- [ ] Two axes: trauma_score (long-term) and retaliation_pressure (short-term)
- [ ] Peaceful = no alive world_boss AND retaliation_pressure < 5.0
- [ ] Trauma decays -0.01/tick during peaceful; pressure always cools -0.1/tick
- [ ] Kill adds +1.0 retaliation pressure

**Transformation:**
- [ ] FOREST→BURNT_FOREST threshold: trauma ≥ 50 (not 51, not 49)
- [ ] FOREST→WASTELAND: trauma ≥ 100 AND calamity ≥ 0.5
- [ ] Recovery: BURNT_FOREST→FOREST when trauma < 10

**Influence:**
- [ ] Conquest threshold: influence ≤ -50 (not -49)
- [ ] Liberation threshold: influence ≥ 50
- [ ] Death shift: ±5.0 per kill

**Raid:**
- [ ] Interval: 500 ticks (5 days × 100 ticks/day)
- [ ] Size: RAID_BASE_SIZE(3) + maturity
- [ ] Spawned as goblin_raider at difficulty_tier=4
- [ ] Target forced to (0,0)

**Boss:**
- [ ] Both gates required: maturity ≥ 50 AND trauma ≥ 20
- [ ] Idempotency: one boss per home region, not per current-position region
- [ ] Spawned as ancient_sentinel difficulty_tier=5, retyped to world_boss
- [ ] Carries ancient_core item
- [ ] Boss death: trauma -20 to containing region

**Camp:**
- [ ] Growth: 0.05/tick; ×1.5 if region trauma > 50
- [ ] Monster cap: max(2, maturity/10)
- [ ] Raid trigger: maturity ≥ 80 AND last_raid ≥ 500 ticks ago; costs -20 maturity
- [ ] Clearing: camp.active = False, trauma -10 to region

**Spawn:**
- [ ] Interval: 50 ticks
- [ ] Density formula cited correctly: max(2, int((area/10000) * 2.0 * (1 + hazard_level)))
- [ ] All three SPAWN_POOLS entries correct
- [ ] All four DIFFICULTY_ZONES distance thresholds correct (80, 150, 220, 999+)
- [ ] All four DifficultyMultipliers rows correct

**PerceptionGate:**
- [ ] 7 sense channels listed
- [ ] Score formula: sense × signal × distance_factor × terrain_mod × (0.5 + alertness×0.5)
- [ ] Threshold: 0.2
- [ ] Baseline fallback: vision=medium, hearing=medium, smell=low, magic_sense=none, social_reading=medium

**Sovereignty:**
- [ ] Tax interval: 100 ticks
- [ ] Hero tax: 2.0 gold; building tax: 10.0 gold
- [ ] Debuff: ATK×0.8, DEF×0.8, SPD×0.9 in monster-owned regions
- [ ] Doc accurately states debuff is not yet fully wired at apply-path
- [ ] Doc accurately states no movement-blocking border gate exists

### 4. Process Verification

- [ ] `make knowledge-index-update` exits 0 after docs are written
- [ ] `make docs-registry` exits 0 after docs are written
- [ ] All 5 new files appear in updated `docs/REGISTRY.yaml`
- [ ] Ticket moved to `tickets/done/` with status DONE
- [ ] Working log entry appended (not inserted before existing rows)
- [ ] Staging artifacts moved to `stored_artifacts/`
- [ ] Agent monitoring entries written

---

## Scope of Existing Test Suite

No existing tests need modification. These docs do not change any behavior. The relevant regression tests already exist (verified in parity ledger) and are only being cited, not altered.

If any test is found to contradict a claim written in a doc, the doc must be corrected to match source truth — do not modify tests.
