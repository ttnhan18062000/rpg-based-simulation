---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261008-PERF-KERNEL-VALIDATES-FLAGS-AFTER-STARTING-WORKERS
tags: []
---

# plan - TCK-20261008-PERF-KERNEL-VALIDATES-FLAGS-AFTER-STARTING-WORKERS

1. kernel.py: call self.validate(flags) right after self._profile is set, before any recorder, feed, run folder or worker exists; delete the later call. validate reads only the profile and the flags and has no side effects.
2. Test beside the flag tests: each forbidden flag through Kernel(...).
