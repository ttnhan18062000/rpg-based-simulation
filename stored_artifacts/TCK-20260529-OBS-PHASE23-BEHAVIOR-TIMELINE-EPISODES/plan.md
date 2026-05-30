# Proposed Plan

Introduce EntityBehaviorTimeline, BehaviorEpisode, BehaviorTimelineStore, and EpisodeDetector to reconstruct structured behavior episodes chronologically.

## Design Decisions
1. Aggregations run post-run or async to keep hot path completely cheap.
2. Gracefully handle ongoing/unresolved episodes.
