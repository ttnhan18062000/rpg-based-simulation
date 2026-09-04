---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260904-TOWN-RESOURCE-PARITY-CITATION-HARDENING
phase: done
date: 2026-09-04
tags: [economy]
---

# TCK-20260904-TOWN-RESOURCE-PARITY-CITATION-HARDENING

## Title
docs/parity_ledger/town_resource.yaml: 13 entries cite a tests_v2/ path that doesn't exist anywhere in
this repo

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Found during the 2026-09-02 Economic axis check (`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`,
"Economic axis check" section): `town_resource.yaml` has the same stale-citation class hardening item 2
already found and fixed in `substrate.yaml` (`SUB-327`, a fabricated citation). That earlier pass fixed 2
of the 15 affected entries (`TOWN-005`, `TOWN-006`, both corrected to
`tests/unit/movement/test_occupancy_conflicts.py`) but explicitly left the remaining 13 unfixed, since
"guessing a replacement citation would repeat the exact fabrication pattern this session already found
and corrected once."

Re-confirmed the exact remaining scope directly (2026-09-04): **13 entries**, all citing one of four
`tests_v2/`-prefixed paths, none of which exist anywhere in this repo (confirmed via direct grep, not
assumed):
- `TOWN-001`, `TOWN-004`, `TOWN-007`: `tests_v2/test_deterministic_baseline.py`
- `TOWN-008`: `tests_v2/replay/`
- `TOWN-009`, `TOWN-010`, `TOWN-013`, `TOWN-014`: `tests_v2/parity/test_resource_interaction_parity.py`
- `TOWN-015`, `TOWN-016`, `TOWN-017`, `TOWN-019`, `TOWN-020`: `tests_v2/parity/test_town_resolution_parity.py`

## Scope
- For each of the 13 entries, investigate whether a real, current test file actually covers the same
  behavior the entry's `text` field describes (the same discipline `TOWN-005`/`TOWN-006` used — a
  confirmed real replacement, not a guess).
- Where a real replacement is found: update the entry's `test_path` via
  `tools/parity_ledger_writer.py` (never a raw YAML edit), following the `SUB-327`/`TOWN-005`/`TOWN-006`
  precedent exactly.
- Where no real replacement exists: mark the entry's `status` honestly (`missing`/`unsupported`, per
  `docs/parity_ledger/schema.json`'s enum) rather than leaving a citation to a nonexistent file — do not
  invent a citation to avoid an honest `missing` status.
- Record a summary: how many of the 13 got a real replacement citation vs. how many were honestly marked
  `missing`/`unsupported`.

## Out of Scope
- Any change to the actual economic mechanics `town_resource.yaml` documents — this is a citation-
  accuracy pass only, not a mechanics review.
- Re-auditing `TOWN-005`/`TOWN-006` or any of the other 177 already-correct entries in this shard.
- The `substrate.yaml` shard itself — already fully hardened in the earlier pass this ticket's finding
  parallels.

## Acceptance Criteria
- [x] All 13 entries (`TOWN-001, 004, 007, 008, 009, 010, 013, 014, 015, 016, 017, 019, 020`) have an
      explicit, evidence-backed disposition: either a confirmed real replacement citation, or an honest
      `missing`/`unsupported` status — none left silently citing a nonexistent `tests_v2/` path. All 13
      got confirmed real replacement citations — none needed `missing`/`unsupported`.
- [x] Every citation change goes through `tools/parity_ledger_writer.py`, never a raw YAML edit.
- [x] Parity index confirmed FRESH after the writes. Rebuilt successfully, `status: ok`.
- [x] `rpg_design_roadmap.md`'s "Economic axis check" section updated to record this as resolved.

## Related Tickets
None — this is the direct follow-up to the 2026-09-02 Economic axis check's own flagged gap, which was
not itself ticketed at the time.

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` ("Economic axis check" section)
- `docs/parity_ledger/town_resource.yaml`
- `docs/parity_ledger/substrate.yaml` (the `SUB-327` precedent this ticket mirrors)

## Related Stored Artifacts
(staging artifacts in `staging_artifacts/TCK-20260904-TOWN-RESOURCE-PARITY-CITATION-HARDENING/`)

## Related Code Areas
- `docs/parity_ledger/town_resource.yaml`
- `tools/parity_ledger_writer.py`

## Assumptions / Open Questions
- Whether a real replacement exists for each of the 13 entries is not yet investigated per-entry — that
  is this ticket's own scope, not resolved here.

## Implementation Notes
Confirmed via direct file checks that every entry's `v2_evidence` source path already exists — the gap
is isolated to `test_path` citations only, not a broader ledger-accuracy problem. For each of the 13
entries, searched the real test tree by the behavior described in the entry's own `text` field, then ran
the candidate test directly before citing it (never guessed). Found a real, confirmed replacement for
all 13 — none needed an honest `missing`/`unsupported` status, unlike the ticket's own contingency
scope for that outcome. Every write went through `tools/parity_ledger_writer.py`, preserving `text`,
`v2_evidence`, `status`, and `priority` unchanged — only `test_path` was corrected. `TOWN-016` kept its
already-correct second citation (`test_macro_economy.py::test_reputation_discount_applies`) alongside
the new one.

## Test Summary
Ran every newly-cited test directly to confirm it passes before citing it:
`pytest tests/unit/core/test_authoritative_state_contract.py::test_mutation_tripwire_during_decision
tests/integration/kernel/test_simulation_kernel_contract.py
tests/unit/kernel/test_replay_contract.py::test_replay_is_non_authoritative
tests/unit/resource/test_loot_channeling.py tests/unit/resource/test_harvest_channeling.py
tests/unit/resource/test_inventory_hardening.py tests/unit/resource/test_resource_conservation_regression.py
tests/unit/world/test_town_building_contract.py::test_town_navigation_proximity
tests/unit/world/test_economy_contract.py tests/unit/world/test_building_interaction_contract.py
tests/unit/world/test_recovery_class_hall.py tests/unit/world/test_town_services.py` → 38 passed,
1 skipped (pre-existing, unrelated). Parity index rebuilt: `status: ok`, `entry_count: 2141`.

## Files Changed
- `docs/parity_ledger/town_resource.yaml` — 13 entries' `test_path` corrected.
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — Economic axis check section updated.

## Completion Summary
Closed the Economic axis's flagged `town_resource.yaml` stale-citation gap in full — all 13 remaining
entries (of the original 15 found in the 2026-09-02 pass) now have confirmed, evidence-backed, passing
real replacement citations, matching the discipline the earlier `SUB-327`/`TOWN-005`/`TOWN-006` fixes
established: never guess, always verify by running the actual test. No entry needed a `missing`/
`unsupported` fallback — real coverage existed for all 13, it simply wasn't cited correctly. Parity
index confirmed healthy after the writes.
