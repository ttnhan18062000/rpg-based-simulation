# Test Plan — TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP

- Hazard collision: records `HAZARD` the kill tick, stays recorded, attribution loss pinned, trauma parity.
- Negative control (immune hazard kind): still records `COMBAT`.
- Corpus (slow): hazard-only deaths 20/21/55/63 recorded; DEFEAT/REBIRTH leftovers remain unrecorded.
- Starvation test in `test_natural_aging_old_age_dispatch.py` unchanged: passive bio deaths stay silent.
- Run: mechanic_scenarios, parity, docs, architecture, simulation_quality, integration, unit/engine.
