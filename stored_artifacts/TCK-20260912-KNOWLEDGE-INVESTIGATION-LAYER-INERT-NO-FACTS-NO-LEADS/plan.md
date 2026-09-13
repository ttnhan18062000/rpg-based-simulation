# Plan — TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS

## Steps taken
1. Evaluated Gap 2 vs Gap 4 with real evidence, chose Gap 2 (see investigation.md).
2. Fixed the real blocker (`"iron"` → `"iron_vein"`) in `src/town/guild.py`, cited in a code
   comment; filed `TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE` for the underlying shape
   question rather than designing a content-authoring mechanism now.
3. Found and filed (not fixed inline) the `LeadState.detail` contract mismatch surfaced by step 2
   — `TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH`.
4. Obtained real before/after SimQ evidence (D-10) under an explicit override.
5. Flipped `FeatureFlagManager`'s own default; discovered and confirmed (revert-and-compare) that
   this flip does not propagate to real corpus-profile runs; filed
   `TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS` (P0) with the
   measured blast radius.
6. Corrected D-10's own record to state the override-vs-default distinction plainly rather than
   let the record imply the acceptance signal was met at the new default.
7. Checked 4 apparently-broken `test_corpus_diversity.py` NARRATIVE anchors via revert-and-compare;
   confirmed pre-existing, unrelated; left untouched.
8. Ticket stays `BLOCKED`, not `DONE` — see investigation.md's Disposition.

## Scope guard
No implementation of the propagation fix, the `LeadState.detail` fix, or the resource-ID-hardcode
shape question — all three filed as their own tickets, each carrying a real, unresolved design
question not decided here.

## Acceptance-criteria map
See the ticket body's own Acceptance Criteria section — each item marked `[x]`/`[ ]` directly, with
inline notes on why the unmet ones stay unmet pending the blocking ticket.
