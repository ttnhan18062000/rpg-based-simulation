---
status: active
layer: engine
authority: P1
audience: developer
---

# The 4 Pillars of RPG Refinement (v2)

The WorldLoop simulation is structured around four architectural pillars that drive emergent, personality-driven gameplay within a strict **Resource-Safe** container.

---

## 🏛️ Pillar 1: The Soul (Cognitive Integrity)
*Transforming reaction-machines into evolving agents.*

### 1.1 The 5-Phase Cognitive Cycle
Entities process their world through a structured brain that isolates strategy from tactical response:
1.  **Strategic Appraisal**: Derives tactical objectives from long-term projects.
2.  **Sensory Filtering**: prioritizes relevant viewport entities (Selective Attention).
3.  **Appraisal**: Calculates emotional spikes (Panic, Grudges, Bravery).
4.  **Deliberation**: Utility AI goal scoring with personality modifiers.
5.  **Selection & Output**: Proposals concrete `ActionResult` with intent.

### 1.2 Selective Attention
Simulates "tunnel vision" and cognitive limits. Entities filter their viewport based on **Saliency**, ensuring that workers Deliberation remains within a fixed resource budget even in dense crowds.

---

## 🏛️ Pillar 2: The Body (Genetic Determinism)
*Ensuring every entity is a unique, persistent agent.*

### 2.1 Genetic Aptitudes
Every entity is seeded with unique **Aptitudes** (e.g., STR, INT, AGI) that act as multiplicative modifiers for growth. 
- **Evolutionary Scaling**: At level milestones (50, 75, 100), entities unlock specialized **Pillar Traits** (Colossus, Archmage, Juggernaut) that fundamentally warp their stats.

### 2.2 Bounded Progression
The engine guarantees that stat growth remains within a certified envelope, preventing "Infinite Stat Drift" that could break simulation math.

---

## 🏛️ Pillar 3: The Action (Authoritative Decoupling)
*Separating 'What to do' from 'How to do it'.*

### 3.1 Worker Packets
The brain no longer "does" things. It proposes them. By offloading AI to the `WorkerPool` using compact state-packets, the engine can parallelize thousands of entities while maintaining a single authoritative state transition point.

### 3.2 Decision Continuity
To prevent "tactical jitter," entities use **Goal Hysteresis**. Once a commitment (Objective) is made, the brain penalizes switching to a new goal unless the utility delta exceeds a "Breakthrough Threshold."

---

## 🏛️ Pillar 4: The Social (Relationship Continuity)
*Driving behavior through collective history.*

### 4.1 Familiarity & Bonding
Entities register presence-based familiarity with allies, providing subtle morale boosts. Conversely, the **Nemesis System** marks high-impact attackers as priority targets that override standard AI scoring.

### 4.2 Environmental Dread
Local casualty rates create a "Regional Dread" aura. High-dread zones bias all local AI toward caution, flight, and defensive behavior.

---

## ⚙️ Technical Constraints
All gameplay pillars are implemented within the **Law of 6 Phases**. This ensures that even the most complex AI interaction remains deterministic, replayable, and resource-bounded.
