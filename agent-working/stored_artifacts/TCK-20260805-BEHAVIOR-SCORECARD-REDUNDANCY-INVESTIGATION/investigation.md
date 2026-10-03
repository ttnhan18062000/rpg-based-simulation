---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-BEHAVIOR-SCORECARD-REDUNDANCY-INVESTIGATION
artifact_type: investigation
tags: [cognition, observability, simulation-quality]
---

# investigation.md — TCK-20260805-BEHAVIOR-SCORECARD-REDUNDANCY-INVESTIGATION

## Current Behavior (file:line refs)

`EntityBehaviorScorecard` (`src/observability/behavior/behavior_scorecard.py:11-51`) is a frozen
dataclass with 12 substantive fields. Grepped every construction site across `src/` and `tests/`:
**`EntityBehaviorScorecard(` is never constructed in production code anywhere** — only in
`tests/unit/observability/behavior/test_phase26_entity_behavior_scorecard.py` and
`test_phase26_cohort_analyzer.py`, both of which hand-construct it with literal hardcoded values
(e.g. `stagnation_score=0.1, progression_score=0.8, ...`) purely to test dataclass frozen-ness and
`to_dict`/`from_dict` round-tripping — not to test any real computation. **There is no production
function anywhere that computes these scores from real data.** This is a stronger finding than
"unwired" — the score-computation logic itself doesn't exist yet, independent of substrate.

## Field-by-Field Verdict (AC1)

| Field | Derivable from `decision_trace.jsonl`? | Derivable from `cognition_graph_diffs.jsonl`? | Real production computation exists anywhere? |
|---|---|---|---|
| `route_families_used` | **Yes** — count `route_kind` of the `selected: true` entry per entity per tick | Partially (project kind, not route family specifically) | No, but trivial: `decision_trace.jsonl` alone is sufficient and richer (full score breakdown, not just counts) |
| `behavior_categories_used` | **No** | **No** | Yes — `BehaviorEventNormalizer` (`normalizer.py`) maps raw `simulation_events.jsonl` event types (`combat_damage`, `combat_kill`, `quest_accepted`/`quest_completed`, etc.) to `behavior_category`/`behavior_family` pairs. Neither `decision_trace` (route-decision scores only) nor `cognition_graph` (project/objective graph state only) captures raw gameplay *outcomes* like "quest completed" or "combat kill" — this requires the raw event stream directly. |
| `episodes_started/completed/failed` | **No** | **No** | Yes — `EpisodeDetector` (`episode_detector.py`) groups categorized `BehaviorEvent`s into multi-step episodes (combat engage→kill, quest accept→complete, info query→learned, blocked→resolved). Built directly on `behavior_category`, so inherits the same "No" from the row above. |
| `repeated_failure_count` | **No** | **No** | Yes — `RepeatedFailureLoopDetector` (`pattern_detectors.py:13-38`) counts episodes with `outcome == "failure"`; depends on episodes above. |
| `adaptation_proof_count` | **No** | **No** | Yes — `BehaviorChangeProofDetector` (`pattern_detectors.py:41-65`) counts episodes with `outcome == "resolved"`; depends on episodes above. |
| `stagnation_score`, `progression_score`, `cooperation_score`, `information_usage_score`, `behavior_diversity_score`, `verdict` | N/A — no computation exists | N/A — no computation exists | **No, anywhere.** Confirmed via the construction-site grep above: these 6 fields are populated only with hand-picked literals in test fixtures. Whatever substrate is eventually chosen, this scoring logic must be written from scratch — it is not a matter of "reviving" existing code. |

## Recommendation (AC2 — option chosen)

**Neither pure option (1) nor pure option (3) fits; the honest answer is nuanced, matching option
(2) but for a different reason than field-count:**

- `route_families_used` is genuinely, fully redundant with `decision_trace.jsonl` — reviving
  `BehaviorWorker` for this field alone would be strictly worse (decision_trace is richer: full
  per-route score breakdown, not just a selection count). **Do not use the scorecard for this.**
- `behavior_categories_used`/episodes/failure-adaptation counts require raw gameplay-*outcome*
  event categorization (quest completion, combat kills) that neither `decision_trace` (strategic
  route-*decision* scores) nor `cognition_graph` (project/objective *structural* state) can see —
  these are genuinely different information, not a redundant re-encoding. `BehaviorEventNormalizer`
  + `EpisodeDetector` are real, tested, working code for this specific job. **If a future ticket
  wants per-entity episode/category tracking, reviving `BehaviorWorker`'s wiring (`simulation_events.jsonl`
  → normalizer → episode detector — components that already exist and work, confirmed by direct
  read) is cheaper than reimplementing equivalent logic on top of `decision_trace`/`cognition_graph`,
  which structurally cannot see the events this needs.**
- The 6 numeric score fields (`stagnation_score` etc.) are unimplemented regardless of substrate —
  **do not assume reviving `BehaviorWorker` gets these "for free."** A future ticket choosing to
  build them must design and write the scoring formulas from scratch, the same amount of new work
  whether built on decision_trace, cognition_graph, or revived BehaviorEvents.

**Bottom line for AC3 (narrow future scoping):** if per-entity behavioral diversity work is ever
picked up, it should NOT try to derive categories/episodes from `decision_trace`/`cognition_graph`
(structurally impossible — wrong information) — it should wire `BehaviorWorker` (real, unwired,
narrow: `src/observability/behavior/worker.py` needs a single instantiation call site, confirmed
absent from `src/engine/` by the original grep this ticket's parent audit ran) for
categories/episodes specifically, and write new scoring logic for the 6 numeric fields as a
separate, explicit design task — not bundled as if it already exists.

## Docs Requiring Update
- `docs/simulation_quality/extension_points.md`: axis 3's addendum (references this ticket) needs
  its "under investigation" framing replaced with this finding.

## Parity Ledger Overlap
None — observability tooling, not a Mechanics-Bible-tracked gameplay subsystem.

## Prior Work
- `TCK-20260529-OBS-PHASE26-BEHAVIOR-SCORECARDS` — original scorecard dataclass implementation,
  done, but (confirmed here) never wired to real computation.
- `TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP` — sibling ticket, fixed cognition-graph capture
  gating; this investigation's cognition_graph_diffs analysis used its fix.

## Risks and Open Questions
None outstanding — the field-by-field evidence is conclusive.
