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
Interruption_Margin = Profile_Resistance * 30.0
```
*   **Profile Resistance**: A value (0.0 to 1.0) defined by the entity's personality or class.
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
