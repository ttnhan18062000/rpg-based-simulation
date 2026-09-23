---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP
artifact_type: plan
---

# Plan — TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP

## Steps

1. Corpus-wide symbol-existence sweep of all 1888 `status: verified` entries across all 9
   `docs/parity_ledger/*.yaml` shards (see `investigation.md` for the full method) to find any
   entry whose named class/function/module is confirmed absent from the codebase.
2. **Hard gate before any write**: produce a per-entry verdict list (entry id, shard, named
   symbol, search evidence + scope, outcome, CERTAIN/JUDGEMENT, re-point target if any) and send it
   via `SendMessage` to both `rpg-feature-planning` and `agent-working-design`. Write nothing until
   `rpg-feature-planning` approves.
3. Apply exactly what is approved, and only through `tools/parity_ledger_writer.py::write_entry()`
   — never a raw `Edit` on the YAML.
4. Run the scoped parity/schema tests (`tests/tools/test_parity_ledger_writer.py`,
   `tests/tools/test_parity_ledger_schema.py`, `tests/tools/test_parity_ledger_scan.py`).
5. Standard-tier close: staging artifacts → `stored_artifacts/`, ticket → `tickets/done/`,
   `record_hand_orchestrated_closure.py`, `docs/REGISTRY.yaml` regenerated and staged,
   `done_checker_static.py`, mechanism-registry changed-code advisory.

## Acceptance criteria map

| Ticket AC | How this plan satisfies it |
|---|---|
| A ledger-wide count of `status: verified` entries whose named symbol is confirmed absent from `src/`, distinct from the bare-missing-`test_path` corpus | Step 1 — 1888 entries swept, method and false-positive accounting fully in `investigation.md` |
| Each hit independently re-verified via git history, not present-day grep alone | Step 1's git-history classification pass (§ Method, step 4) — applied to every candidate that survived the full-repo escalation |
| Every confirmed dangling entry corrected via `parity_ledger_writer.py`, recording the dangling reference as evidence, never repointed at a plausible substitute | Steps 2-3 — `INFRA-228` downgraded (not repointed, since the one relevant investigation into a successor explicitly declines to confirm one); `WORLD-CULT-002`'s consumption citation repointed only after direct code-level confirmation (CERTAIN, not inferred) |
| Cross-referenced explicitly against `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS` | `investigation.md` Related section, and the ticket body's own Related Tickets |

## Deviations from the ticket's original scope note

None on scope. Two live corrections layered on top mid-batch, both requested by
`rpg-feature-planning` during gate review, applied within Step 3 before close:
- `INFRA-228`: `agent-working-design`'s independent check found one sub-claim (the
  `runtime_content_source` default change) survives with a live test; named in `divergence_note`
  rather than left implicit, per instruction.
- `WORLD-CULT-002`: gate required reading the two candidate call sites directly before writing,
  rather than accepting my own JUDGEMENT-level draft — done, upgraded to CERTAIN before the write.
