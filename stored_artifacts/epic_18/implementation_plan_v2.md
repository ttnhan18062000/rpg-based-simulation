# Comparative Implementation Guide: Epic 18 & AI Heuristics

This document provides a detailed breakdown of the shift from the current "Reactive" simulation model to a "Living Lifecycle" model. It contrasts existing logic with proposed enhancements, detailing the rationale behind each technical decision.

---

## 1. AI Thinking: From Reactive to Life-Heuristic

### Current Behavior & Logic
Entities use a **Utility AI** model (`src/ai/goals/scorers.py`) where each tick evaluates goals based on immediate stats (HP, Stamina, nearby enemies).
- **Looping Issue**: There is no "memory" of recent goals. A hero might move A -> B -> C -> A if the scores fluctuate slightly, repeating the same 4-tile patrol for 100 ticks.
- **Static Priorities**: A Level 1 hero and a Level 25 hero score `Combat` and `Explore` using the same base curves, with only minor danger penalties.

### New Behavior & Logic: "Boredom & Life-Stages"
1.  **Boredom/Novelty Penalty**: 
    - *Logic*: Every time a goal is selected, its "Boredom Multiplier" (starting at 1.0) is multiplied by 0.9.
    - *Outcome*: After 5 consecutive `Explore` actions, the utility score drops significantly (~0.59x), forcing the AI to consider `Social`, `Trade`, or `Rest` even if immediate stats don't demand it.
2.  **Lifecycle Stages**:
    - *Logic*: Inject a `life_multiplier` into scorers based on level brackets (1-10, 11-20, 21-30).
    - *Outcome*: Young entities prioritize high-volume `Explore/Rest` (learning the world). Veterans prioritize `Social/Craft` (refining their peak) and hunting high-threat targets (Nemesis).

### Rationale
To simulate "thinking," an entity must have a sense of time. Life-stages give them a "long-term goal," and boredom ensures they experience the full breadth of the simulation's features.

---

## 2. Physical Growth: From Stats to Evolution

### Current Behavior & Logic
- **Leveling**: Predictable stat growth (`+2` to all base attributes on level up).
- **Hardness**: Entities don't get "tougher" by surviving fights; they only get XP.
- **Static Identity**: A `wolf` is always a `wolf`, only with higher numbers.

### New Behavior & Logic: "Hardening & KIND Shifts"
1.  **The Toughness Passive**:
    - *Logic*: Every time an entity takes damage, they receive a fractional gain in `VIT` and `END`.
    - *Outcome*: A front-line Warrior will naturally develop higher `VIT` than a back-line Mage, even at the same level, purely through experience.
2.  **Near-Death Hardening**:
    - *Logic*: Surviving a fight with `< 15% HP` triggers a "Hardened" event (permanent `+1 Max HP`).
3.  **Entity Evolution**:
    - *Logic*: At Level 10 + Veteran Rank, an entity can trigger a `KIND` evolution (e.g., `Orc` -> `Orc Chieftain`).
    - *Outcome*: Changes the sprite/model, racial growth profile, and innate talents.

### Rationale
Progression shouldn't just be "numbers go up." It should be visible and earned through specific hardships. Evolution provides the "Aha!" moment for the observer, signaling a major lifecycle shift.

---

## 3. Resilience: From Fragile to Chaotic

### Current Behavior & Logic
- **Worker Reliability**: The engine assumes `AIBrain.decide` always returns a valid proposal. If a distributed worker (RabbitMQ) drops a packet, the engine might stall or skip an entity.
- **Fuzzing**: We test with hand-written scenarios (e.g., `test_combat.py`). We don't know what happens if an entity has `999,999` Luck or `0.0001` Speed.

### New Behavior & Logic: "Fault Injection & Invariants"
1.  **Fault Injection**:
    - *Logic*: In `WorkerPool`, if `chaos_mode` is ON, we purposefully discard 1% of AI results.
    - *Outcome*: Forces the Engine to implement robust "Fallback to Idle" logic without breaking the tick cycle.
2.  **Property-Based Testing (Hypothesis)**:
    - *Logic*: Instead of `Entity(level=1)`, we test `Entity(level=draw(integers(1, 100)))`.
    - *Outcome*: Finds the mathematical edge cases in our balance formulas (like where Speed might cause an infinite tick delay).

### Rationale
As we move to more complex AI heuristics, the chance of "brain farts" or network drops increases. Chaos testing ensures the simulation is "unkillable" even if the AI workers are stuttering.

---

## Summary of Technical Changes

| Feature | File | Shift |
|---------|------|-------|
| **AI Boredom** | `src/ai/brain.py` | Add `goal_history` and decay multipliers. |
| **Life-Stages** | `src/ai/goals/scorers.py` | Add `level_curve` utility modifiers. |
| **Hardening** | `src/actions/combat.py` | Assign `VIT` training on damage taken. |
| **Evolution** | `src/engine/world_loop.py` | Check for KIND swap periodically. |
| **Chaos Mode** | `src/config.py` | Add stress-test toggles. |
