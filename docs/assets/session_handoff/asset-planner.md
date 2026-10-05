---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-05
tags: [architecture, documentation]
---

# Handover — asset-planner

> Snapshot of the gitignored `.claude/handover/asset-planner.md` on 2026-10-04 at 95b74a25f; on a new machine copy it to `.claude/handover/asset-planner.md`.

Updated: 2026-10-04 (PR #334 merged; asset work paused)

## Open
- Branch: none in flight · PR: none open (last: #334 merged as 95b74a25f, AM-M1 unblock batch; #330 as f6783200f).
  asset-implementer idle; worktree rpg-aseprite-mcp detached at origin/main 95b74a25f.
- Result after #334: AM-M0 INCONCLUSIVE (user kept it: hosting/clients/staleness open for AM-M6), AM-M1 BLOCKED on "M0 did not
  pass" (owner decisions D13-D18 recorded; register 55 MET / 7 GAP / 6 N/A). Even with M0 PASS it would be INCONCLUSIVE until code
  lands for W02.7, W06.3, W03.1 (parked, no tickets). AM-M2 BLOCKED, AM-M6 NO-GO, charter unsigned.
- Owner decisions taken 2026-10-04 (all Recommended options; full table in the epic): nhan holds every role; frontend derives
  keys; never retire; ranges N/A under A; variant_axes frozen empty; single-operator retention, review at 50 MB; W13.3/4/6
  carried to AM-M6; write a retrospective AM-M0 result; M0 kept INCONCLUSIVE (hosting/clients/staleness open for AM-M6). Still parked: terrain-v1 adopt-set, charter signing, AM-M6.
- ASSET WORK PAUSED (user 2026-10-04) at map basics until the RPG core features land. Resume only when the user says so.
  Parked, no tickets: icons and other kinds (entities, buildings, items, UI; reuse draft sets + adopt-set),
  todos/TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN.md (root of todos/).
- Ignore (user, 2026-10-04): the agent-monitoring retro hook and the TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN staleness nag.
- FYI codebase-planner: from merges on/after 2026-10-18, src/ PRs fail CI on new/worse ruff, complexipy, line-count, mypy,
  ast-grep N3/N4/E3. Asset batches touch visual_assets/ + frontend/ + docs/ only; if one ever edits src/, run
  `make code-health` + `make typecheck-py` first.

## State worth knowing
- Merged epics: foundation (#286, #299), hardening + isolated M5 rehearsal (#309), pilot readiness (#317), detail variants +
  draft sets (#327), AM-M1 docs batch (#330), AM-M1 unblock (#334).
- AM-M1 (#330, re-derived by #334): `docs/assets/m1_contract_register.md`, 68 clauses, 55 MET / 7 GAP / 6 N/A. Result **BLOCKED**
  only because AM-M0 (`docs/assets/m0_discovery_result.md`) is INCONCLUSIVE. Owner decisions are ADR D13-D18. Remaining GAPs:
  W02.7, W03.1, W06.3 (code, parked), W07.4 (with the first capability), W13.3/4/6 (carried to AM-M6). AM-C01 judged met (a
  judgment, not an owner-signed gate record).
- Owner APPROVED 2026-10-04: `docs/assets/fallback_safety.md` (W06, three classes decorative/identifying/critical) and
  `docs/assets/m2_evidence_charter.md` (W11; rerun rule: pre-approval results count only when rerun unchanged on a named commit
  after approval). AM-M2 still BLOCKED (M1 not PASS, no authorization).
- Catalog: real key `terrain.forest` with detail values plain/bush/tree (all owner-adopted); release `pilot/rc-0003` current
  (rc-0001/rc-0002 history). Draft set terrain-v1: 22 unadopted drafts; colour-vision finding open (cvd_pairs.txt).
- Decided: Profile A (D8), no signing (D9), Aseprite local only, Aseprite package U-02 + U-14 closed (D10; the other machine needs its own licensed Aseprite, see the last section), detail axis (D11), draft sets (D12);
  every budget APPROVED incl. retention 30 days; gc never deletes tracked state; rollback/recall owner "nhan (owner)".
- M5 (rerun on 401921bdd): overall INCONCLUSIVE; no M1/M2/M4 PASS record. Gates are never reworded to pass.

## Pointers
- Register + M1 result: `docs/assets/m1_contract_register.md`; plan package status: `docs/plans/visual-asset-management-runtime-integration/README.md`
- Contract (as built): `docs/assets/store_contract.md`; ADR: `docs/architecture/visual_asset_foundation_adr.md`
- Charter draft: `docs/assets/pilot_charter_am6.md`; M5: `docs/assets/surface_rehearsal_result.md`
- Done batches: `agent-working/tickets/done/visual-asset-m1-contracts/`, `agent-working/tickets/done/visual-asset-m1-unblock/`
- Delivery rules: `docs/guides/delivery_process.md`

## For a new machine (flagged, not deleted)

- **Paths marked "(this machine)"** (`/home/vboxuser/Work/rpg-aseprite-mcp`, `/home/vboxuser/Work/rpg-based-simulation/.venv*`, the knowledge venv) are this machine's; use your own worktree and interpreter, by absolute path.
- **`systemd-run ... MemoryMax`** is this machine's cap; keep the idea (heavy commands foreground, one at a time, capped), re-size the number.
- **Aseprite is local-only (`ADR D10`, `docs/architecture/visual_asset_foundation_adr.md`):** real Aseprite runs only on the licence holder's own machine, never on a shared or hosted one. The other machine needs **its own licensed Aseprite** before any drawing, `adopt` or `adopt-set` (adoption re-renders each source with the store's own Aseprite and refuses without it). Without it, docs and read-only store work are still possible.
- **Local-only state that does not travel:** the gitignored quarantine under `visual_assets/catalog/.quarantine/` and `.review/` (including the two unadopted first-draft forest intakes `in-1f3ef37e2cc9156b`, `in-990026dd005070e8`), `.claude/handover/` itself, and the agent-monitoring retro/staleness nags the user said to ignore.
