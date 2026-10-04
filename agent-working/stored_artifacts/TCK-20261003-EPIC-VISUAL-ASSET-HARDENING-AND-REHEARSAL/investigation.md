---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261003-EPIC-VISUAL-ASSET-HARDENING-AND-REHEARSAL
artifact_type: investigation
tags: [architecture, testing, mcp, security]
---

# Investigation (as built) — TCK-20261003-EPIC-VISUAL-ASSET-HARDENING-AND-REHEARSAL

**Decisions (user, 2026-10-03, each by a blocking question):** D8 deployment Profile A (the registry, runtime manifest, artifacts and client are one immutable Vite release; no asset-only pointer), D9 no signing (integrity is the `pixels-v1` hash plus the hash-linked provenance chain, checked by `verify`), D10 real Aseprite only on the licence holder's machine (never installed, built, cached or uploaded in CI). Recorded in `docs/architecture/visual_asset_foundation_adr.md` and `docs/assets/aseprite_licence_review.md`. Budgets: the implementer measures, the planner proposes, the owner approves in PR review. An isolated `AM-M5` rehearsal on synthetic fixtures was authorized; `AM-M6` (activation) and `AM-M7` (migration) stay dormant (no adopted art, no human-selected role).

**Review findings that changed scope**
- **F1/F5, record size bounds (ticket 2 review).** Every writer and reader capped every record at `MAX_RECORD_BYTES`, so a legal registry (about 207 keys), release manifest (about 400 entries) or `IntakeResult` with 4-byte text (68483 B) could not be read or written. Fix: per-type bounds with one lookup, `MAX_RECORD_BYTES` 131072, `MAX_VISUAL_KEYS` 1024 by the 2 s / 256 MiB rule; a guard test builds the maximum legal instance of every record type.
- **F4.** `MAX_DECODED_BYTES` had two jobs; `MAX_PNG_FILE_BYTES` (4259840, the worst legal 1024 px noise PNG rounded to 64 KiB) now bounds file reads.
- **F2/F3/F6 kept:** `MAX_SOURCE_BYTES` stays 102400 (R1 waived, the 16-frame dense case is a known limit, D2's trigger working as designed); the pure-Python decoder limits the dimension bounds; scale 16 at 128 px is refused upstream.
- **Sandbox leak (found in the ticket 2 review).** A timed-out job could leave the inner bwrap (the PID-namespace init, immune to SIGTERM) alive holding a job directory, and the timeout test failed machine-wide. Reproduced and the survivor identified; round 2 of its review found a SIGSTOP race and, under artificial CPU load, an interrupt (the repo's per-test alarm) between SIGSTOP and SIGKILL that left a stopped tree and hung `Popen.__exit__` for 13 minutes: SIGKILL now sits in a `finally`.
- **`MAX_MANIFEST_BYTES` 393216 (ticket 3).** The guard showed the widest runtime manifest (359764 B) exceeds the candidate manifest (292081 B) it was first sized for; raised and accepted by the planner.
- **Rehearsal capture (ticket 4).** A real Chromium capture showed the hollow-frame fallback's letter invisible; fixed with a contrast-tested light letter.

**Still open, nothing filed:** owner approval of the budget numbers (rows are `PROPOSED`); `AM-M6`/`M7`; a predeclared client matrix; an M4 rehearsal and client/rollback roots for `AM5-W09` and `AM-C09`; rollback/recall authority for `AM-C06`; U-02 and the licence of real assets; signing is decided against.
