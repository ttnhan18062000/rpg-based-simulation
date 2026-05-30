# Phase 3 Implementation Plan

## Core Technical Solutions

### 1. Module and Schema Architecture
We will create `src/domains/adventure/` containing:
- `src/domains/adventure/schema.py`: Defines `AdventureRouteOption`, `RejectedRoute`, `AdventureDecisionResult`.
- `src/domains/adventure/generator.py`: Suggests options.
- `src/domains/adventure/scoring.py`: Subjective scoring with personality bias.
- `src/domains/adventure/service.py`: High-level evaluation.
- `src/domains/adventure/mapper.py`: Bridge from decision result to strategic `ProjectState` / `ObjectiveState`.
- `src/domains/adventure/resolver.py`: Objective-to-ActionIntent resolver.
- `src/domains/adventure/phase.py`: System Phase runner.

### 2. Imperfect Decision Scoring Logic
Formula:
$$\text{Score} = \text{urgency} + \text{benefit} + \text{personality\_bias} + \text{knowledge\_confidence} - \text{risk\_penalty} - \text{blocker\_penalty}$$
Personality mapping:
- Brave: reduces risk penalty.
- Cautious: increases recover score, increases risk penalty.
- Greedy: increases expected benefit for gold/loot routes.
- Curious: increases score for information/scout routes.
- Industrious: increases score for gather/craft routes.
- Sociable: increases score for party/social routes.

### 3. Execution Cadence & Bounding
We will ensure that the decision phase skips:
- Dead, inactive, or impaired entities.
- Entities that already have an active, unblocked strategic project.
- Entities whose need levels and opportunity sets haven't changed.
- Bounded to run only when cadence allows or direct triggers (e.g. current project block, new quest, or need change) are present.
