---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260529-OBS-PHASE23-BEHAVIOR-TIMELINE-EPISODES
artifact_type: plan
tags: [obs, phase23, behavior, timeline, episodes]
---

# Proposed Plan

Introduce EntityBehaviorTimeline, BehaviorEpisode, BehaviorTimelineStore, and EpisodeDetector to reconstruct structured behavior episodes chronologically.

## Design Decisions
1. Aggregations run post-run or async to keep hot path completely cheap.
2. Gracefully handle ongoing/unresolved episodes.
