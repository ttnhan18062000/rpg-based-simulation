---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT
artifact_type: investigation
tags: [architecture, testing, live-map]
---

# Investigation — TCK-20261006-VISUAL-ASSETS-TERRAIN-BORDER-CONTRACT

- Draft sets are family-agnostic (`Family` is a free string; `draft keep` checks only the declared key and detail value; the preview manifest parser takes any family). No store check on size, opacity or orientation, so 16x16 1-bit alpha plus client rotation does not clash.
- Probe (guarded scratch copy under the session scratchpad; paths asserted inside it; the real catalog, drafts and quarantine unchanged: `git status` count identical before and after): a 16x16 transparent-background mask drawn with the library passed `intake` (PASSED), `draft keep --as border.edge --detail v1`, `draft verify` and `verify`.
- Not probed: `adopt-set` re-renders each source with Aseprite and requires a pixel match with the draft preview (human only). Pixel hashing normalises transparent pixels, so a match is expected; the first real mask set is the first proof. Flagged to the planner.
- Registering keys moves `registry_hash`: `pilot/rc-0003` can no longer be exported. The user approved `pilot/rc-0004` (2026-10-06); guards re-pointed (`test_pilot_fixture`, `test_catalog_integrity`, `test_store_tools_stdio`, registry test).
- Mutant note: the `crisp` check inside `higher()` is redundant with rank absence (crisp codes have no rank), so removing it alone is an equivalent mutant; the invariant is guarded by the doc-equality and exclusivity tests (a mutant adding wall to the order fails them).
