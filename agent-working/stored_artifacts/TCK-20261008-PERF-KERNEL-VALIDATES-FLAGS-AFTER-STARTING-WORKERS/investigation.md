---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261008-PERF-KERNEL-VALIDATES-FLAGS-AFTER-STARTING-WORKERS
tags: []
---

# investigation - TCK-20261008-PERF-KERNEL-VALIDATES-FLAGS-AFTER-STARTING-WORKERS

validate(flags) uses only self._profile and flags (ProfileValidator.validate_profile / validate_flags, both pure). The EventRecorder and DecisionTraceWriter drain workers and the quality feed started before it, and create_run_directory had already written the run folder. Moving the call to the top of __init__ needs no other change; startup order is the only difference, so authoritative state is untouched.
