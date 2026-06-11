---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [epic, multi, hero]
---

# Design: Dedicated `HeroLifecycleSystem` Architecture

## Why the Dedicated System?
To inject multi-hero stakes (names, escalating mortality, interpersonal bonds) without destroying the existing generic `WorldLoop` math logic, we are creating the `HeroLifecycleSystem` (Approach C).

## 1. Data Contract Modifications
Currently, `models.Entity` fields are flat. We will add optionally nullable fields explicitly assigned during the `EntityBuilder` step:
```python
display_name: str = ""
death_count: int = 0
generation: int = 1
hero_familiarity: dict[int, float] = field(default_factory=dict)
```

## 2. Generator Logic Loop
In `engine_manager.py`, the `_build()` function will loop from `1` to `config.hero_count` (Defaulting to 4).
Through a round-robin rotation, it will cycle through `HeroClass.WARRIOR`, `MAGE`, `RANGER`, `ROGUE`.

## 3. Name Generation Tables
`src/core/hero_names.py` will hold static constant lists:
`FIRST_NAMES` = ["Kael", "Lyra", "Thorne", "Sera", ...]
`TRAITS` = ["Brave", "Cautious", "Greedy", ...]

Whenever a hero spawns, the `HeroLifecycleSystem` queries the RNG stream to deterministically select a first name and a title if `display_name` is blank.

## 4. Escallating Death Stakes
Inside the `HeroLifecycleSystem.on_tick()` routine, the system will look for essentially exactly what `world_loop._process_death` used to do, but intercept Heroes:
- **Death 1:** Bag drops.
- **Death 2:** Bag + Accessories drop.
- **Death 3:** Bag + Accessories + Armor drops.
- **Death 4:** Permadeath. Entity is pruned from the Dict, and a `PendingReplacement` queue inside the System requests the `generator.py` to spit out a new level 1 Hero in town at `Generation N+1`.

## 5. Familiarity Matrix
Also ticking inside `HeroLifecycleSystem`, any two active Heroes inside the same visibility radius will increment their bond map. When bonding exceeds `0.5`, existing combat APIs will dynamically check adjacent bond status and grant a flat +10% conditional ATK multiplier.
