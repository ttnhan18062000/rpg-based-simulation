---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION
artifact_type: test_plan
tags: [architecture, mcp, testing]
---

# Test Plan — TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION

- [x] keep refusals and defaults; drafts invisible to gc, build, release, verify; fresh copy verifies.
- [x] One test per chain link (source, intake result, pixel hash) for `draft verify` and `adopt-set`.
- [x] adopt-set all-or-nothing: not confirmed, render mismatch, one bad entry; one confirmation listing every entry and the set hash.
- [x] Mutant: skipping the render comparison fails a test.
- [x] Widest records at 256 entries within `MAX_RECORD_BYTES`; budgets parity.

## Proof Plan
- level: unit and contract (pure Python with a deterministic renderer stand-in)
- proof kind: positive and negative cases, tamper per link, snapshot equality for all-or-nothing, a mutant
- oracle source: the ticket, the planner's decisions D1-D10 and `docs/assets/store_contract.md`
- expected effect: drafts are durable and inert; a reviewed set is adopted only after every entry is re-proved, in one confirmed decision
- selected commands: `pytest tests/visual_assets`, `python -m visual_assets.store verify`, `python -m visual_assets.store draft verify`
