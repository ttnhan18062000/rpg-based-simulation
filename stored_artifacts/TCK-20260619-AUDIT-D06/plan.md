# Plan — D06 Long-Run Simulation Health

## Method
run-sim: 1,000-tick runs on sandbox_world, seeds 42 and 137.

## Questions to Answer
1. Does tick compute stay bounded across 1,000 ticks (no memory/CPU creep)?
2. Do entity counts stabilise, collapse, or recover (attrition vs replenishment)?
3. Do resource nodes deplete and recover (ecology working)?
4. Is behavioral activity sustained past tick 200 now that RC1/RC2/RC3 are fixed?
5. Does rejection count grow monotonically or plateau?
6. Does the governor stay NORMAL or escalate to throttle?

## Scoring Method
Same Emergence Gap rubric as D03: Variety Gap × Lifespan Gap × System Silence (max 15/15 worst).
Additionally: performance degradation rated separately (ms/tick trend across quartile windows).

## Run Commands
```
python3 -m src cli --ticks 1000 --seed 42
python3 -m src cli --ticks 1000 --seed 137
```
