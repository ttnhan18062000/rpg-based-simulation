# Implementation Plan - Phase 9 Campaigns

## Proposed Changes

### Campaigns Core Package

#### [NEW] [schema.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/campaigns/schema.py)
Defines CampaignSpec, CampaignResult, expected arc families, and structures for campaign execution.

#### [NEW] [spec.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/campaigns/spec.py)
Loads campaign specs from YAML, parses them, validates arc definitions and constraints.

#### [NEW] [runner.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/campaigns/runner.py)
Wraps the simulation kernel, executes campaigns, manages the tick loop, and accumulates semantic traces.

#### [NEW] [classifier.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/campaigns/classifier.py)
Classifies entity trace logs into life arc types like cautious_growth, craft_growth, etc.

#### [NEW] [behavior_change.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/campaigns/behavior_change.py)
Detects behavioral changes where past events/memories alter subsequent choices.

#### [NEW] [diversity.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/campaigns/diversity.py)
Analyzes diversity of route families across entities and flags stagnation or identical collapse.

#### [NEW] [scorecard.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/campaigns/scorecard.py)
Evaluates overall campaign scores, partial passes, forbidden behaviors, and quality criteria.

#### [NEW] [forbidden.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/campaigns/forbidden.py)
Detects violations of physical laws (e.g. actions post-death, hidden knowledge).

#### [NEW] [reports.py](file:///home/vboxuser/Work/rpg-based-simulation/src/domains/campaigns/reports.py)
Generates readable Markdown and JSON summary reports.

## Verification Plan

### Automated Tests
Run:
`pytest --import-mode=importlib tests/unit/campaigns/`
`pytest --import-mode=importlib tests/integration/campaigns/`
`pytest --import-mode=importlib tests/perf/test_phase9_campaign_semantic_budget.py`
