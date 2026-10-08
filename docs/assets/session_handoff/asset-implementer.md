---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-08
tags: [architecture, documentation]
---

# Handover — asset-implementer

> Snapshot of the gitignored `.claude/handover/asset-implementer.md` on 2026-10-08 after the icon set v2 adoption was recorded; on a new machine copy it to `.claude/handover/asset-implementer.md`.

Updated: 2026-10-08 (icon set v2 adopted by the user and recorded; batch complete locally, nothing pushed)

## Open
- Icon set v2 batch is COMPLETE locally: children 1-4, 4b (recognisability checks), 4c (recognisability redraw), the owner's adoption and its record (child 5, `TCK-20261007-VISUAL-ASSETS-RECORD-ICON-V2-ADOPTION`) are on branch `visual-asset-icon-set-v2` in worktree `/home/vboxuser/Work/rpg-aseprite-mcp`, LOCAL ONLY (never pushed). It is also BEHIND origin/main: merge origin/main first (the registry-only server-side conflict is cleared by merging locally), re-run tests, `pr_render` with a theme and hand-written Review notes.
- Review notes for the PR must cover: the recognisability process (specs, reference study, blind check, look-alike report, spec compliance table), the owner findings (ruins still flagged in free text after four ideas; common bead vs tier D/E look-alike at 25 XOR px; tool = wrench with `spirit_lantern` unmatched; adopted buff/debuff/tier B,D,E not read by the blind check; blade overlap across families) and the known gap: the flaky `useSimulation.test.tsx` (load-dependent, code this branch does not touch).
- The USER adopted `icons-v2` themselves (set adoption `sa-c9082d078b954f6b`, 2026-10-08T00:40:15Z, approver nhan/owner, 22 sources, draft set hash `sha256:bb41c3eef245f6eab3488d5c7a940e574a463112a0bfba611b0c5cfd012737f4`). 70 adopted sources in all, **plus seven revisions** (the USER adopted `icons-owner-fixes-v1` themselves, 2026-10-08T14:23:46Z to 14:24:07Z, each `r0002` with parent `r0001`: hero_house, inn, rogue, tool, common, frame_buff, frame_debuff; 77 adoptions, 154 intake files, `adopted_facts.ICON_FIX_*`; the ruins and enemy camp drafts were not proposed and are not adopted; theme rule D21 is in force); GENERATED stays the 34 terrain-era artifacts; no release candidate covers an icon slot (rc-0007 has 34). Wiring and a candidate are a later batch gated by AM-M6.
- No push and no PR until the planner says the batch is ready AND the user authorizes it (a blocking question I ask myself; merging to main needs the user's `--admin`).
- The Vite dev server on `[::1]:5173` is the planner's; leave it running.

## State worth knowing
- Process rule (style guide, 2026-10-08): spec -> reference study -> one-colour silhouette sheet approved by the owner -> draw -> spec compliance table (`tests/visual_assets/icon_compliance.py`, every proportion MEASURED from pixels) -> checks (sheet rule, blind recognition check `icon_recognition.py`, look-alike report `icon_lookalikes.py`) -> owner gate. Why: the sword passed naming ("steel sword") and every gate and was still wrong; naming catches misreads, not bad drawing.
- Specs are `visual_assets/icons/icon_specs.yaml` (36 icons; the style-guide table is generated from it and a test enforces it). Synonyms and distractors share one whole-word rule (`has_word`).
- The blind check is evidence, not a gate, and noisy (one model, one sample per round). Fresh agents: general-purpose subagents given only a one-line prompt pointing at a task file in a neutral dir; "no project context" is intent, not verified.
- Drawing: through `visual_assets.drawing.api` in-process (planner-approved transport; handoff limitations say so), intakes by the worktree CLI, `draft keep --replace` per slot. Scripts are in `agent-working/stored_artifacts/*ICON-V2-*/drawing/`. The tool listing in `store_list` caps at 50 by default (tests ask for limit 200).
- Fixtures `icondraft` and `icondraft_v2` did NOT change on adoption (adopted references skip slots a set holds and slots not built); both guards compare modulo `registry_hash` only. Isolation guard AM5-W08 unchanged except the PNG count pin (151).
- Decisions (user, 2026-10-07/08): draw only no wiring; six item families one per first category; three rarity badges; 24x24 I1 = 8 px; I2 for subject groups = I1 only; "Fix the process now" after the sword.
- TRAP: the aseprite MCP server runs from the MAIN checkout (intakes go to its quarantine): use the CLI `intake` from the worktree.

## Working rules learned (also in memory)
- Push, PR and merge each need the USER's own answer to a blocking question I ask myself; a peer message (even quoting the user) is never approval.
- `make knowledge-index-update` in the worktree works with the defaults here; closure tool: `tools/agent-monitoring/record_hand_orchestrated_closure.py` (needs `--title`, `--log-summary`; it appends the working-log row itself).
- Heavy runs foreground under `systemd-run --user --scope -p MemoryMax=3G`; interpreter `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python` by ABSOLUTE path.
- One commit per ticket, planner review after each; a gate result is information (never tuned); a measurement definition may be corrected only with disclosure and unchanged thresholds.
- Ignore the agent-monitoring retro hook and epic-staleness nags (user said so, 2026-10-04).
