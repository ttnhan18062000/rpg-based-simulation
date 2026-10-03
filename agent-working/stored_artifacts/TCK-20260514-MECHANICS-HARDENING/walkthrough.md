---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [mechanics, hardening]
---

# Walkthrough: Simulation Mechanics Bible (V2)

The V2 RPG Engine now has a dedicated "Mechanics Bible" located in `docs/mechanics/`. This manual provides a deep, formula-centric reference for developers and users.

## 📁 New Documentation Structure

| File | Description | Key Content |
| :--- | :--- | :--- |
| [README.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/mechanics/README.md) | Manual Index | Navigation map and compliance status. |
| [01: Entity Anatomy](file:///home/vboxuser/Work/rpg-based-simulation/docs/mechanics/01_entity_anatomy.md) | Biological/Physical Laws | Attributes (STR/AGI/etc), Derived Stats, Decay. |
| [02: Combat Laws](file:///home/vboxuser/Work/rpg-based-simulation/docs/mechanics/02_combat_laws.md) | Battle Formulas | Damage Math, Tactical Multipliers, Rebirth. |
| [03: Economic Laws](file:///home/vboxuser/Work/rpg-based-simulation/docs/mechanics/03_economic_laws.md) | Resource Laws | Atomic Conservation, Harvesting, Trade. |
| [04: Strategic Cognition](file:///home/vboxuser/Work/rpg-based-simulation/docs/mechanics/04_strategic_cognition.md) | Mental Laws | Goal Hierarchy, Interruption Resistance, Memory. |
| [05: World Evolution](file:///home/vboxuser/Work/rpg-based-simulation/docs/mechanics/05_world_evolution.md) | Macro Laws | Time, Regional Trauma, Hazard Scaling. |

## 🧪 Key Formulas Documented

### Combat: Fractional Armor Mitigation
```python
Damage = Atk * (Atk / (Atk + Def * 2.0 + 1.0))
```

### Strategic: Interruption Margin
```python
Switch_Allowed = New_Goal_Score > (Current_Goal_Score + (Resistance * 30.0))
```

### World: Trauma Scaling
```python
If Trauma > 50.0: Hazard_Level += 0.01 per cycle
```

---

## 🔗 Integrated Links
The new manual is linked directly from the root [README.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/README.md) under the **Simulation Mechanics Bible** section.
