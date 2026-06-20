---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-06-06
---

# Chapter 4: Strategic Cognition

This chapter explains the "Mental Laws" of the simulation. Entities are not simple automatons; they possess a strategic layer that manages goals, remembers locations, and resists unnecessary interruptions.

---

## 1. Goal Hierarchy & Prioritization
Entities evaluate multiple "Concerns" and select the one with the highest calculated score as their active **Project**.

| Priority Tier | Concern Type | Drive |
| :--- | :--- | :--- |
| **Tier 1: Survival** | `danger`, `fleeing` | Avoidance of death or incapacitation. |
| **Tier 2: Biological** | `hunger`, `sleep`, `exhaustion` | Maintaining operational biological stats. |
| **Tier 3: Social** | `social`, `grudge`, `bond` | Protecting allies or seeking revenge. |
| **Tier 4: Economic** | `harvest`, `trade`, `craft` | Accumulating wealth and equipment. |

---

## 2. Interruption Resistance
To prevent "Goal Flickering" (rapidly switching between two similar goals), entities apply an **Interruption Margin**.

```python
# Switching Law
Switch_Allowed = New_Goal_Score > (Current_Goal_Score + Interruption_Margin)

# Where:
Interruption_Margin = Profile_Resistance * resistance_multiplier
```
*   **Profile Resistance**: A value (0.0 to 1.0) defined by the entity's personality or class.
*   **resistance_multiplier**: A profile-defined constant (not a hard-coded 30.0); value varies by entity profile.
*   **Emergency Bypass**: High-urgency "Danger" concerns (score > 80) ignore the interruption margin.

---

## 3. Strategic Memory: Leads & Blockers
Entities maintain a mental map of the world through two primary data structures.

### Leads (Knowledge)
A `Lead` is a stored piece of information about a resource or location.
*   **Subject**: What the lead is about (e.g., "Iron Ore").
*   **Detail**: Where it is located (e.g., `(45, 12)`).
*   **Certainty**: High, Medium, or Low. Certainty decays over time if the information is not refreshed.

### Blockers (Problems)
A `Blocker` is a reason why a goal cannot be achieved.
*   **Access**: A path is blocked or a location is unreachable.
*   **Material**: Missing items or gold for a recipe.
*   **Inventory**: No more physical space to carry items.
*   **Congestion**: Too many entities in a small area.

---

## 4. The Project Lifecycle
Strategic goals are broken down into a multi-step hierarchy.

1.  **Directive**: High-level intent (e.g., "Improve Defense").
2.  **Project**: A specific actionable goal (e.g., "Craft Iron Breastplate").
3.  **Objective**: A granular, atomic step (e.g., "Travel to Forge", "Interact with Anvil").
4.  **Action**: The raw engine command sent to the simulation.

---

## 5. Perception & Salience
Entities do not see the entire world.
*   **Perception Radius**: Usually 10.0 to 15.0 units.
*   **Salience Filter**: Only entities or events within the perception radius are considered "Salient." Information outside this radius is either ignored or retrieved from Memory (Leads).
*   **Info Decay**: Strategic leads lose certainty every 100 ticks. High-certainty leads become Medium, and so on, until the information is forgotten.

---

## 6. Adventure Route Scoring Constants

**Source:** `src/domains/adventure/scoring.py` — `AdventureRouteScorer.score()`

The adventure decision pipeline (enabled via `ENABLE_ADVENTURE_ROUTING`) scores every candidate route and selects the highest. The formula and all constants are documented here.

### 6.1 Scoring Formula

```
score = urgency + benefit + personality_bias + confidence_bonus − risk_penalty − blocker_penalty
score = max(0.0, score)   # clamped to non-negative; rounded to 4 decimal places
```

### 6.2 Formula Term Constants

| Term | Formula | Constants | Max value |
|---|---|---|---|
| `urgency` | `max(need.urgency for matched needs)` | Depends on active need pressures | ~2.0 |
| `benefit` | `route.expected_benefit` | World-defined per opportunity | — |
| `personality_bias` | `trait × 0.25` (family-matched) | **Weight: 0.25** per trait | 0.25 |
| `confidence_bonus` | `route.confidence × 0.15` | **Weight: 0.15** | 0.15 |
| `risk_penalty` | `route.expected_risk × risk_multiplier × 0.5` | **Risk weight: 0.5**; multiplier below | — |
| `blocker_penalty` | `2.0 if route.blockers else 0.0` | **Fixed: 2.0** (see §6.3) | 2.0 |

### 6.3 Risk Multiplier

```python
risk_multiplier = max(0.1, (1.0 + caution × 0.8) − bravery × 0.6)
```

| Parameter | Coefficient | Effect |
|---|---|---|
| `caution` (= 1.0 − bravery) | 0.8 | Higher caution → higher risk multiplier → more conservative |
| `bravery` | 0.6 | Higher bravery → lower risk multiplier → more risk-tolerant |
| Floor | 0.1 | Prevents multiplier going negative (very high bravery edge case) |

Range: 0.1 (pure bravery) to 1.8 (pure caution). Default personality (bravery=0, caution=1.0) → multiplier = 1.8.

### 6.4 Personality Bias by Route Family

| RouteFamily | Trait | Weight |
|---|---|---|
| `RECOVER` | `caution` | 0.25 |
| `GATHER_RESOURCE`, `SELL_LOOT_FOR_GOLD`, `TAKE_EASY_QUEST` | `greed` | 0.25 |
| `ASK_INFORMATION`, `SCOUT_LOCATION` | `curiosity` | 0.25 |
| `CRAFT_UPGRADE`, `GATHER_RESOURCE` | `industry` | 0.25 |
| `FORM_PARTY` | `sociability` | 0.25 |
| `BUY_UPGRADE`, `COMBAT_ENGAGE`, `DEFER_WITH_REASON` | (none) | 0.0 |

Only one family match applies per route. Maximum personality_bias = 0.25.

### 6.5 blocker_penalty = 2.0 — Justification

`blocker_penalty` is a **fixed constant**, not graduated by severity.

**Rationale (E12A, 2026-06-20):** In 100-tick measurements with `ENABLE_ADVENTURE_ROUTING=ON` (urban_political, seed=42), `blocker_frequency = 0.0` — no blocked routes were scored because resource nodes are absent in the test world. The constant cannot be empirically refined until world content provides non-DEFER route candidates.

**Design intent:** A route with _any_ blocker (missing item, inaccessible location) should be strongly deprioritized. The 2.0 magnitude exceeds the maximum personality_bias+confidence_bonus contribution (0.40), ensuring blocked routes are overridden by the highest-urgency unblocked routes.

**Revisit trigger:** If `blocker_frequency > 0.05` is observed in E12C regression tests, reconsider whether 2.0 is too blunt for minor blockers (e.g., gold deficit < 5).

### 6.6 Score Range Summary (Estimated, No Blockers)

| Component | Min | Max |
|---|---|---|
| urgency | 0.0 | ~2.0 |
| benefit | 0.0 | ~0.5 (typical opportunity) |
| personality_bias | 0.0 | 0.25 |
| confidence_bonus | 0.0 | 0.15 |
| risk_penalty | 0.0 | ~0.9 (max_risk=1.0 × 1.8 × 0.5) |
| **Total non-blocked** | 0.0 | ~2.9 |
| blocker_penalty | 0.0 | 2.0 (fixed) |
| **Total blocked** | clamped to 0 | ~0.9 |
