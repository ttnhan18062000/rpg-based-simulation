# Investigation: Phase 1 Behavioral Realism

## Existing State Scan
- `src/core/aspects/mind.py`: 
    - Already has `DecisionState.motives` placeholder.
    - `MemoryRecord` exists but is truth-based (direct faction/position).
    - `NarrativeMemory` exists but is just a log of events.
- `src/ai/brain.py`:
    - `_memory_appraisal_phase` handles some memory aging but it's hardcoded logic.
    - `_deliberation_tactical_phase` uses `GoalEvaluator`.
- `src/ai/states/`: Handlers for IDLE, HUNT, etc. currently read target info directly from `actor.mind.memory`.

## Duplication/Conflict Scan
- Conflicting Ticket: `TCK-20260407-PHASE1-PERSONALITY.md` was seen in `tickets/done`. Wait, let me double check that.
- Actually, `TCK-20260407-PHASE1-PERSONALITY.md` IS in `tickets/done`. 
- `TCK-20260407-PHASE1-DS.md` is in `tickets/inprogress`.
- `TCK-20260407-PHASE0-CONTINUE.md` is in `tickets/done`.
- `TCK-20260407-PH0-FIX.md` is in `tickets/done`.

Let's check `tickets/done/TCK-20260407-PHASE1-PERSONALITY.md` to see if someone already did the personality part.

## Reused Patterns
- Pillar 1: Domain-Driven Separation (Separating Decision, Perception, Emotion).
- Pillar 2: Phased Appraisal (Sensing -> Appraisal -> Deliberation).
- SimulationModel/BaseModel: Use Pydantic for all state.

## Risks
- Forward reference issues in Pydantic models when nesting Mind objects.
- Performance hit of updating beliefs for every visible entity every tick. (Throttling appraisal is already suggested).
