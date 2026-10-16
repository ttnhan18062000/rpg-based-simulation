---
status: historical
layer: observability
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261016-EVENT-CATALOG-INVENTORY-EVERY-EVENT-TYPE-ITS-PRODUCER-READER-AND-COUNT
date: 2026-10-16
tags: []
---

# Investigation: TCK-20261016-EVENT-CATALOG-INVENTORY-EVERY-EVENT-TYPE-ITS-PRODUCER-READER-AND-COUNT

- The knowledge index and graph were absent in the worktree; context came from direct reads.
- Event channels: (R) EventRecorder.record, which counts every call before the mode filter; (L) kernel listeners, which also get the alert events (GOLD_HOARDING and the other economy alerts never reach the recorder); (F) simulation_events.jsonl, which also gets three shutdown tally events written outside record().
- The event file is not lossless: record() keeps a 5000-event in-memory buffer and, when it is full of CRITICAL events, drops every incoming non-critical event before the queue push. biological_state_changed is CRITICAL (14,083 in urban_political seed 42), so from about tick 3300 the file (and the SimQ feed) keeps only CRITICAL events; the gate's tally events are lost with them. Evidence per run in the artifact (F / R, the tick where the file stops keeping events, CRITICAL count).
- The SimQ hub is built only when build_feed_from_env() returns a feed, so the runs had no hub: the SimQ column is static.
- SimQ-motivated seeds are compile-time seeds and feature flags (Pattern 6 in design_patterns.md), not events; the table lists them with what they feed and a D33 view.
- Machine load was high (load average 20-47): the runs took 30-85 minutes each; parallelism was cut to 2 on request.
