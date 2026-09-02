---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-SOCIAL-CANONICAL-HASH-GAP
artifact_type: investigation
tags: [social, determinism]
---

# Investigation — TCK-20260902-SOCIAL-CANONICAL-HASH-GAP

Full investigation lives in `docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md`
§3.1 ("Determinism: canonical-hash coverage gap") — not duplicated here. Summary of the finding this
ticket acts on:

- `EntityState.to_canonical_dict()` (`src/core/state.py`) includes a `"social"` sub-dict covering 10 of
  `SocialComponent`/`SocialBond`'s 15 real fields.
- The 5 uncovered fields are enumerated in the source doc's §3.1 table (field name, type, current
  coverage status).
- This gap is distinct from `StateFingerprinter`'s (`src/replay/fingerprint.py`) already-known,
  explicitly-non-canonical near-zero coverage — the canonical hash is the authoritative one
  (`world_compile_report.json`'s `state_hash`).
- Required direction named in the source doc: either add the 5 fields to `to_canonical_dict()`, or
  explicitly document per-field why each is legitimately excluded (e.g. derived/non-authoritative).

## Next step for implementation
1. Re-read the source doc's §3.1 table directly against current `src/core/state.py` (confirm no drift
   since 2026-09-02) before writing code.
2. For each of the 5 fields, make and record the coverage decision.
3. Confirm with the concurrent M3 implementation session before editing `src/core/state.py` — shared,
   central file.
