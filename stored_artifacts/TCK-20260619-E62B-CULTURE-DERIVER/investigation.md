---
ticket_id: TCK-20260619-E62B-CULTURE-DERIVER
phase: investigation
date: 2026-06-23
---

# Investigation — TCK-20260619-E62B-CULTURE-DERIVER

## Key Findings

- `ChronicleGrouper.group(entries)` is pure/stateless; safe to call at episode end
- `ChronicleHierarchy.events` is a `tuple[NarrativeLedgerEntry, ...]` of chronicle-worthy events
- EventSignificanceScorer filters entries before they reach hierarchy.events; only significant entries appear
- `CampaignOrchestrator._advance_state()` runs after `narrative_ledger.extend()` so the full ledger (including new entries from this episode) is available when calling `ChronicleGrouper().group()`
- Deferred import inside `_advance_state()` avoids circular import (matching E32D/E61B patterns)
- Region attribution: `entry.payload.get("region_id", "__global__")` — falls back to "__global__" for events without region context
