---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [epic_18]
---

# Newcomer's Guide: Understanding "Progression Depth"

Welcome to the RPG Simulation! As a new developer, it's easy to see the system as just numbers on a grid. This guide explains **Progression Depth**—the feature that turns "units" into "individuals" with life stories.

---

## 1. The Problem: The "Robotic Loop"

In many simulations, an entity (like a Wolf or a Hero) follows a simple, unchanging loop:
1.  **A**: Wander around.
2.  **B**: Find something to fight.
3.  **C**: Rest when HP is low.
4.  **Repeat**.

Without Progression Depth, an entity will perform **A -> B -> C -> A** for 5,000 ticks. They are robotic. They don't learn, they don't get "bored," and they never fundamentally change their priorities.

---

## 2. Our Solution: Progression Depth

We are introducing a "Lifecycle Heuristic." This means the entity’s brain doesn't just look at *now*, it looks at its *whole life*.

### A. The "Boredom" Mechanic (Variety)
Imagine eating your favorite pizza every single day. Eventually, you’d want a salad.
- **Old Way**: The AI always picks the highest-scoring activity.
- **New Way**: Every time an entity picks a goal (like `Combat`), that goal's priority slightly "decays." 
- **The Result**: After a few fights, the entity thinks, *"I've had enough blood for today; I'll go explore that forest or visit the town guild instead."* This forces variety.

### B. Life-Stage Priorities
Our entities now acknowledge their "age" (Level).
- **Youth (Level 1-10)**: Fast learners, high curiosity. They prioritize `Explore` and `Rest`. They are just trying to survive and see the world.
- **Growth (Level 11-20)**: Peak ambition. They prioritize `Combat` and `Loot`. They are focused on gaining power and wealth.
- **Veteran (Level 21-30)**: Master status. They prioritize `Social` training and hunting "Nemeses" (enemies that almost killed them before). They seek specialized growth.

---

## 3. Physical Evolution

In standard RPGs, a Wolf at Level 10 is just a Level 1 Wolf with more health. Here, they actually **harden** and **evolve**:

1.  **Hardening**: Every time an entity takes damage, they train their Vitality (`VIT`) and Endurance (`END`). They literally "toughen up" through pain.
2.  **Evolution**: When a Wolf reaches a certain level of power and experience, they don't just stay a Wolf. They might evolve into a **Dire Wolf**, changing their appearance, their speed, and how they grow in the future.

---

## 4. Why are we doing this? (The Goal)

We want to reach a point where you can look at a specific entity—let's say **Hero #42**—and see a unique history:
> *"This hero survived a brutal ambush in the mountains (Hardened), got bored of fighting goblins (Variety), decided to visit the Alchemy Lab to learn about poisons (Lifecycle shift), and eventually evolved into a Paladin after reaching Level 20."*

**That is Progression Depth.**

---

## 5. Summary for Developers

| Feature | Metaphor | Code Location |
|---------|----------|---------------|
| **Boredom** | "I need a change of pace." | `src/ai/brain.py` |
| **Life-Stages** | "I'm not a kid anymore." | `src/ai/goals/scorers.py` |
| **Toughness** | "What doesn't kill me makes me stronger." | `src/actions/combat.py` |
| **Evolution** | "I've become something more." | `src/engine/world_loop.py` |
