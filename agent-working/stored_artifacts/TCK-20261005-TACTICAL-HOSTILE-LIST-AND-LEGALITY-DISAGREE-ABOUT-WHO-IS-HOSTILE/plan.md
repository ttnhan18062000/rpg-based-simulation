---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-TACTICAL-HOSTILE-LIST-AND-LEGALITY-DISAGREE-ABOUT-WHO-IS-HOSTILE
artifact_type: plan
tags: [engine, combat]
---

# Plan (investigation only)

1. Compare the three hostility call sites on the corpus: `probes/hostility_probe.py` recomputes tactics' and legality's predicates from the
   same context at every `verify_attack_legality` call (4 worlds x 2 runs, values).
2. Test the planner's spawned-monster and objective-target hypotheses, then trace who asks for each friendly-fire verdict
   (`probes/ff_origin.py`).
3. No unification before ratification, and none was proposed: 0 disagreeing pairs. Close as a measured non-defect; the latent dead
   fallback is filed separately (`TCK-20261005-LEGALITY-RAW-FACTION-EQUALITY-FALLBACK-IS-DEAD-BUT-LATENT`, P3).
