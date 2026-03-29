# The 4 Pillars of RPG Refinement

The RPG simulation has evolved from a reactive world into a **proactive, personality-driven engine**. This shift is structured around four architectural pillars that influence every entity from spawn to level 100.

---

## 🏛️ Pillar 1: The Soul (Mind & Emotions)
*Transforming reaction-machines into evolving agents.*

### 1.1 The 7-Phase Cognitive Pipeline
Instead of simple state-logic, entities now process their world through a structured brain:
1.  **Sensory**: Gathers raw data & applies **Selective Attention**.
2.  **Perception**: Identifies nearest threats and ally proximity.
3.  **Memory**: Records narrative logs (Trauma, Glory, Discoveries).
4.  **Appraisal**: Derives `mood` and `bravery` from memory clusters.
5.  **Deliberation**: Utility AI goal scoring with personality modifiers.
6.  **Selection**: Picking a goal using **Temperature (Softmax)**.
7.  **Output**: Generates Action Proposal + **Tactical Intents**.

### 1.2 Selective Attention
Simulates "tunnel vision" in dense scenarios. Entities filter their visible list based on **Saliency** (distance, rarity, faction), ensuring the brain only considers the most relevant entities for decision-making.

### 1.3 Narrative Appraisal
- **Trauma Cluster**: High-damage events reduce `mood` and increase `panic`.
- **Glory Cluster**: Victorious encounters boost `bravery` and combat tenacity.

---

## 🏛️ Pillar 2: The Body (Genetics & Progression)
*Ensuring every entity is a unique biological agent.*

### 2.1 Genetic Evolution (Aptitudes)
Every entity possesses unique genetic **Aptitudes** (multipliers for STR, AGI, INT, etc.).
- **Divergence**: Two level-20 Warriors will have different stats based on their seed-derived aptitudes.
- **Milestone Growth**: Stat growth is accelerated at "Ascension" (50), "Mastery" (75), and "Divinity" (100).

### 2.2 Pillar Traits
High-level entities unlock unique traits at breakthroughs:
- **Colossus (Level 50)**: Massive HP and DEF spikes.
- **Archmage (Level 75)**: Skill power and mana cost optimization.
- **Juggernaut (Level 100)**: Ultimate resilience and CC immunity.

---

## 🏛️ Pillar 3: The Action (Tactical Decoupling)
*Separating 'What to do' from 'How to do it'.*

### 3.1 Tactical Intents (Hints)
The brain no longer just says "Attack". It provides **Tactical Hints** to the state handlers:
- **Skirmish (Kiting)**: "Maintain 3 tiles distance while attacking."
- **Support**: "Target specifically the ally at 10% HP for the next heal."
- **Flank**: "Prioritize targets not facing the actor."

### 3.2 Decision Inertia (Goal Hysteresis)
To prevent "jittering" between goals:
- **Goal Lock**: Entities commit to a state for `GOAL_LOCK_TICKS` (5-10) unless in critical danger.
- **Anticipatory Cooldowns**: Recently abandoned goals are penalized to prevent rapid switching.

---

## 🏛️ Pillar 4: The Social (Relationships)
*Driving emergent behavior through collective history.*

### 4.1 Familiarity & Bonding
Entities develop **Familiarity** with nearby allies (+0.002/tick).
- **Group Cohesion**: High familiarity (allies) provides a subtle `bravery` boost when in proximity.
- **The Nemesis System**: Victims record a "Grudge" against attackers, marking them as Nemeses who override standard priority targeting.

### 4.2 Environmental Dread
Collective regional sentiment (derived from deaths of same-faction entities) creates a "Dread" aura, causing local entities to become more anxious and prone to fleeing.

---

## ⚙️ Technical Optimizations

### Vector Flow Fields (Navigation Amortization)
For mass navigation (e.g., 50 heroes targeting a City), the engine uses **Vector Flow Fields** ($O(1)$ query) instead of individual A* pathing to reduce CPU overhead by 90% in dense zones.

### Hysteresis-Driven Sleep
Entities in a `Goal Lock` skip the expensive `AIBrain.decide()` selection phase for the duration of the lock, further stabilizing the simulation performance.
