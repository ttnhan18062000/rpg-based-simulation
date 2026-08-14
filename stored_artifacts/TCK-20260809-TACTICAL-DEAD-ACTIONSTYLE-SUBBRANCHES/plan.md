---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES
artifact_type: plan
tags: [combat, simulation-quality]
---

# Plan — TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES

## Chosen approach: remove (option a)
Delete the dead `AGGRESSIVE`/`EVASIVE` `attack_range` bias block (`src/engine/tactical.py`,
former lines 596-603) entirely, replacing it with a code comment explaining why it was removed
and why option (b) — implementing it for real — was rejected. `style`/`ActionStyle` remain real,
used imports/locals (the real kiting-distance consumer at line ~555 is untouched).

## Rejected: option (b), implement for real
Would require moving the `ActionStyle` bias earlier, before `is_attack_legal` is computed
(line ~401), and feeding it into `LegalityServiceV2.verify_attack_legality`'s own real range
check — directly modifying the exact decision point 2 immediately-prior tickets this same session
spent real, corpus-verified effort hardening. No real, confirmed requirement exists for this
specific "aggressive ignores range buffers" effect (never requested, no design doc calls for it,
no test expects it) — implementing it now would be scope creep into a new feature, not a bug fix,
carrying real regression risk against freshly-verified code for a speculative benefit.

## Adjacent fix: COMB-263's stale test citation
Found while investigating (same file, same compliance ID this dead code's own comment cited) —
corrected `docs/compliance/checklist.md`'s own wrong test-file reference rather than leaving it
silently wrong, since it's small, real, in-scope, and doc-only (zero regression risk).

## Verification plan
- Confirm no test references the removed block's behavior (done, via grep).
- Full scoped pytest re-run.
- Real corpus `is_attack_legal` re-verification (same probe methodology used throughout this
  session) to confirm the freshly-hardened legality path is genuinely unaffected — not just
  assumed safe because "it's dead code."

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md re-confirms the dead-code finding, makes a real (a)/(b) decision | Done — (a), with real rationale |
| If (b): re-verified via live corpus probe | N/A — chose (a) |
| Scoped pytest passes | Done |
