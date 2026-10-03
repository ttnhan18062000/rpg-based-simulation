---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260904-TOWN-RESOURCE-PARITY-CITATION-HARDENING
artifact_type: plan
tags: [economy]
---

# Plan — TCK-20260904-TOWN-RESOURCE-PARITY-CITATION-HARDENING

1. For each of the 13 entries, search the real test tree by the behavior described in `text`, not by
   guessing near the old stale path.
2. Run each candidate test directly before citing it — never cite an unverified guess.
3. Write each corrected entry via `tools/parity_ledger_writer.py` (never a raw YAML edit), preserving
   every other field (`text`, `v2_evidence`, `status`, `priority`) unchanged.
4. Rebuild the parity index, confirm health.
5. Update the roadmap's Economic axis check section to record full resolution.
