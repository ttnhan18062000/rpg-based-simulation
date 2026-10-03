---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260514-DOCS-REORG
artifact_type: investigation
tags: [docs, reorg]
---

# Investigation - Documentation Audit

## Objective
Identify structural inconsistencies and broken links in the legacy RPG documentation suite.

## Findings
- **Fragmentation**: Core laws were scattered across 138+ files with no central index.
- **Link Rot**: Over 40% of internal links used absolute paths that were environment-dependent or broken by file renames.
- **Semantic Drift**: Documentation for `AuthoritativeApplyPipeline` was outdated, missing recent phase additions (e.g., `ReputationPhase`, `RewardPhase`).
- **Logic Gaps**:
    - `ActorValidityPhase`: Lacks explicit checks for `status_sleeping` actors.
    - `StrategicIntelligence`: Uses hardcoded "Magic Numbers" (e.g., `30` for retention) instead of Law-defined constants.

## Recommendations
- Flatten the directory structure into domain-specific subdirectories (`core/`, `engine/`, `systems/`).
- Establish a "Single Source of Truth" for the Authoritative Pipeline refinement phases.
- Automate link fixing to ensure portability.
