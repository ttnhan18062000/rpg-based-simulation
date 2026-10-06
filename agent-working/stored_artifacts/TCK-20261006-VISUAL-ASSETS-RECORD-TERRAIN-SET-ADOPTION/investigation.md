---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION
artifact_type: investigation
tags: [architecture, testing, live-map]
---

# Investigation — TCK-20261006-VISUAL-ASSETS-RECORD-TERRAIN-SET-ADOPTION

- Adoption record: `sa-f4c541f25f112221`, approver nhan / owner, decided_at 2026-10-05T18:17:03Z (UTC), draft_set_hash sha256:287ab36c0299f9180b2ebf47afc84c95babf612818f80af3e0eeb78457023eb2, 31 entries; review evidence "terrain-v1 preview page with borders on/off, border close-ups and before/after sheet, 2026-10-06". The user typed the licence decision and evidence themselves.
- The draft_set.json bytes still hash to that value (asserted by a test), so what was reviewed, what is committed as history and what was adopted are the same bytes.
- Seven guards failed because they asserted the pre-adoption world; no code regressed. Changed assertions: catalog integrity (sources list), registry (catalog contents and the adoptions/intake file counts), detail axis (the per-source detail map), adoption "never touched" (counts, now 34/34/68/1/0 plus the exact source names), terrain draft set ("unadopted" became "history, with an adoption pointing at every entry"), store tools stdio (source count 34), server stdio (sources list). All use equality against `adopted_facts`.
- Not covered: no `build` (generated artifacts are the forest's three), no release candidate (rc-0004 is the forest only), no runtime export of the 31 slots.
