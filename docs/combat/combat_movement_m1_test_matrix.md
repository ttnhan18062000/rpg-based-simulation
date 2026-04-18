# Combat-Movement Milestone 1 — Test Matrix

## 1. Spatial Contract Tests

| Test Case | Input | Expected Rule |
| :--- | :--- | :--- |
| **Manhattan Distance** | (0,0) to (1,1) | Distance = 2 |
| **Orthogonal Adjacency** | (0,0) to (1,0) | Adjacent = True |
| **Diagonal Adjacency** | (0,0) to (1,1) | Adjacent = False |
| **Hard Occupancy** | Move to entity pos | Blocked = True |
| **AoE Range** | Impact at range+1 | Legal = False |
| **AoE LOS** | Wall between center | Legal = False |
| **AoE Splash** | Target at radius+1 | Hit = False |

## 2. Timing Contract Tests

| Test Case | Input | Expected Rule |
| :--- | :--- | :--- |
| **Readiness** | tick < next_act_at | Can Act = False |
| **Quiet Tick** | No actor ready | tick increments = True |
| **Passive Decay** | Status dur=1 at tick 10 | Status expired at tick 11 |
| **Need Progression** | Hunger at tick 10 | Hunger > prev_hunger at tick 11 |

## 3. Enforcement Tests

| Test Case | Input | Expected Rule |
| :--- | :--- | :--- |
| **Validation Reject** | Proposal for dist > range | Success = False |
| **Authority Reject** | Illegal proposal bypasses validation | ActionSystem rejects = True |
