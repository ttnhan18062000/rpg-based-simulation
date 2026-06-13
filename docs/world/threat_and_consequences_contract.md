---
status: active
layer: engine
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Threat and Consequences Contract

**Source:** `src/world/threat.py`, `src/world/region_threat_classifier.py`, `src/world/consequences.py`, `src/world/transformation.py`, `src/world/influence.py`
**Related docs:** [ecology_and_calamity_contract.md](ecology_and_calamity_contract.md), [regional_sovereignty_runtime_contract.md](regional_sovereignty_runtime_contract.md), [docs/mechanics/05_world_evolution.md](../mechanics/05_world_evolution.md)

---

## Purpose

Threat tracks how dangerous a region has become over time and in the short term. Consequences are the world-state changes that happen when threat escalates or is resolved. Transformation describes how regions degrade or recover along defined paths. Influence tracks faction control and triggers structural changes at thresholds.

---

## Threat — `threat.py`

Two independent threat axes are tracked per region:

| Axis | What it tracks | Decay |
|---|---|---|
| `trauma_score` | Long-term accumulated danger (deaths, combat events, calamities) | −0.01 per tick during peaceful state |
| `retaliation_pressure` | Short-term aggression (recent kills) | −0.1 per tick always |

### Accumulation rules

- Hero death in region: `trauma_score += 0.5`; `retaliation_pressure += 1.0`
- Calamity event: `trauma_score += fixed increment` (see [ecology_and_calamity_contract.md](ecology_and_calamity_contract.md))
- Camp raid successful: `retaliation_pressure += 1.0`
- Peaceful ticks (no hostile events): `trauma_score -= 0.01` per tick (floors at 0.0)
- `retaliation_pressure`: always cools −0.1 per tick (floors at 0.0)

### RegionThreatClassifier — read-only, perspective-based

`region_threat_classifier.py` produces routing labels for entities. It is **read-only** — it reads `trauma_score`, `retaliation_pressure`, and entity-specific faction context, then returns a threat classification label. It does not write world state.

Labels influence adventure domain route scoring (blocked routes receive −2.0 penalty). The classifier is perspective-based: the same region may classify as LOW threat for a high-level warrior but HIGH for a low-level mage.

---

## Consequences — `consequences.py`

Consequences are the durable world-state mutations applied when threat thresholds are crossed or when resolution events occur.

| Trigger | Consequence |
|---|---|
| `trauma_score >= 80` | Spawns hostile patrol entity in region |
| Camp cleared (all monsters killed) | `trauma_score -= 10`; region broadcasts CAMP_CLEARED event |
| World boss defeated | `trauma_score -= 30`; `retaliation_pressure = 0`; calamity_intensity reduced |
| Hero escort completed | Broadcasts ESCORT_COMPLETE; route reputation update via commitment domain |

All consequences are applied through the authoritative apply pipeline (StateUpdate + entity spawn where needed).

---

## Transformation — `transformation.py`

Regions change their type along defined paths as trauma accumulates or is resolved. Threshold table:

**Degradation paths** (trauma rising):

| From | To | Trauma threshold |
|---|---|---|
| PEACEFUL | TROUBLED | 20 |
| TROUBLED | DANGEROUS | 40 |
| DANGEROUS | BLIGHTED | 60 |
| BLIGHTED | FORSAKEN | 80 |
| PEACEFUL | CONTESTED | (faction influence < −20) |
| TROUBLED | WARZONE | (trauma > 35 AND retaliation > 5) |

**Recovery paths** (trauma falling):

| From | To | Condition |
|---|---|---|
| TROUBLED | PEACEFUL | trauma < 10 for 500 consecutive ticks |
| DANGEROUS | TROUBLED | trauma < 25 for 300 consecutive ticks |
| BLIGHTED | DANGEROUS | world boss cleared + trauma < 50 |

Transformation fires a `REGION_TYPE_CHANGED` event consumed by the world_emergence domain.

---

## Influence — `influence.py`

Faction influence tracks political control of each region, independent of threat.

| Event | Influence change |
|---|---|
| Hero/ally death | `influence -= 5.0` |
| Enemy killed | `influence += 5.0` |

**Threshold triggers:**

- `influence <= −50`: conquest event — spawns a stronghold structure at region centre, locks town access to conquering faction
- `influence >= +50`: liberation event — removes stronghold if present, restores town access

Influence is a durable world field. All changes go through StateUpdate → authoritative apply path.

---

## Regression tests

- `tests/integration/world/test_long_run_stability.py` — trauma accumulation, decay rates, retaliation cooling
- `tests/unit/world/test_region_threat_classifier.py` — perspective-based classification, label correctness
- `tests/certification/test_cert_long_run_stability.py` — camp clear, boss defeat consequence triggers
- `tests/integration/world/test_long_run_stability.py` — region type transition at thresholds

---

## Extension rules

1. To add a new consequence trigger: add a threshold check in `consequences.py`, produce a StateUpdate, add an integration test. Do not add direct world mutations outside the authoritative path.
2. To add a new transformation path: add an entry to the threshold table in `transformation.py`. Recovery paths require sustained duration checks — use the existing tick counter pattern.
3. To add a new influence threshold event: extend `influence.py` with the threshold value and resulting StateUpdate. Keep influence changes symmetric (gain/loss for same event type).
4. `RegionThreatClassifier` is read-only — do not add mutations to it.
