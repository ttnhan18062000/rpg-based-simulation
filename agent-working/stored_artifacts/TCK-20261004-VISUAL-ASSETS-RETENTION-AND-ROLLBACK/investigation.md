---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK
artifact_type: investigation
tags: [mcp, live-map, testing]
---

# Investigation — TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK

- Re-checked against what landed: gc only touched local and generated junk and never records, so the ticket's release roots had nothing to protect; the planner chose local-only age-based retention (decisions quoted in the ticket).
- `make_intake` stamps intakes 2026-01-01, so existing gc tests pin `now`; an unpinned gc would have listed them as expired.
- Measurements: 4431 bytes tracked per adopt+build+release; local intake 3.3-3.6 KB quarantine plus 2.2-2.7 KB review.
- The mixed-snapshot hazard is a superseded view keeping late images; the loader drops them and the drill proves it.
