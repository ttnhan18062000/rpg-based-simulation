---
status: active
layer: architecture
authority: P1
audience: developer
---

# Macro-Interest Redesign: Foundational Constraints

This document defines the architectural boundaries, canonical ownership, and update pathways for the "Macro-Interest" systems. Every new feature in this area must adhere to these rules to prevent state duplication and hidden coupling.

## 1. Canonical Vocabulary

| Term | Definition | Time Scale |
| :--- | :--- | :--- |
| **Archetype** | Static behavioral template (e.g., *Cautious Opportunist*, *Glory Seeker*). Assigned at birth/initialization. | Permanent (Static) |
| **Motive** | Internal drive influencing behavior (e.g., *Revenge*, *Greed*, *Survival*). | Medium-term (Evolving) |
| **Goal** | Specific tactical objective selected by the AI (e.g., *Kill Goblin*, *Rest at Home*). | Short-term (Immediate) |
| **Belief** | Local mental data about facts (e.g., "The Forest is Dangerous"). May be partial or biased. | Dynamic (Mutable) |
| **Relationship** | Directed social bond (e.g., *Trust*, *Fear*, *Rivalry*) stored as public standing. | Long-term (Accumulating) |
| **Turning Point** | High-salience memory that causes a shift in Motives or Archetype weights. | Permanent (Historic) |
| **Interpreted Event** | Atomic action + semantic narrative tag (e.g., `ACTION_KILL` + `TRAUMA`). | Momentary (Event) |

## 2. State Ownership Grid

| State Family | Canonical Owner | Responsibility |
| :--- | :--- | :--- |
| **Personality / Soul** | `IdentityComponent` | Archetype, OCEAN traits, and `life_directive`. |
| **Cognition / Mind** | `StrategicComponent` | Active Motives, Perceptual Beliefs, and Current Goal selection. |
| **Social / Standing** | `SocialRegistry` | Authoritative directed bonds and public reputation. |
| **Physical / World** | `WorldState` | Environmental consequences (Scars) and legacy persistence. |

## 3. The Interpretation Pipeline

All behavioral updates must follow this authoritative flow:

1. **Raw Event**: An action is taken (e.g., `AttackHero`).
2. **Interpretation Layer**: The event is tagged based on context (e.g., `Aggressive`, `Traumatic`).
3. **State Update**:
    - **Private**: Entity's `StrategicComponent` records a `TurningPoint` if salience is high.
    - **Public**: `SocialRegistry` updates directed bonds between participants.
4. **Appraisal**: On subsequent ticks, the AI uses current `Mind` state + `Identity` traits to select the next `Goal`.

## 4. Retention & Salience Rules

To prevent unbounded state growth, every system MUST implement:

- **Memory Cap**: `CognitionModel.memory.experience` (owned by the `cognition` component, `src/core/cognition.py`) is capped at **50 entries**, authoritatively pruned by **weighted salience** (`abs(impact) * (1 - recency_decay)`).
- **Relationship Cap**: `SocialRegistry` limits directed bonds to **20 records** per entity, pruned by last interaction tick.
- **Salience Requirement**: Events are only preserved if their weighted impact remains above a minimum threshold (pruning occurs in the `ActionSystem` update path).

## 5. Truth, Belief, and Public Separation

- **Objective Truth**: Used by the core application engine for resolution (e.g., current HP).
- **Private Belief**: Used by the AI for decision-making (e.g., "I am safe").
- **Public Reputation**: Used for social consequences and world reactions.

## 6. Inspection Boundaries (Curated Spectator Lens)

To maintain behavioral realism and prevent data overload, all entity inspection must be **curated** and **story-driven**:

- **Who Is This?**: Personality traits are presented as labels (e.g., "Creative", "Disciplined") derived from OCEAN traits with a 0.3/0.7 threshold.
- **Likely Next Choices**: Displays the **top 3 goals** from the AI's current utility scoring (`mind.decision.goal_scores`), with utility values and descriptive labels explaining the underlying motive bias.
- **Ongoing Arc**: A hybrid view showing the **top 5 high-salience events** (> 0.4 weighted impact) chronologically, grouped by recent thematic focus (e.g., "Combat Focus").
- **Bonds**: Only bonds with **intensity > 0.3** should be listed in the primary social summary, with dynamic labels (e.g., "Ally", "Nemesis").

---
*Approved by User on 2026-04-06.*
