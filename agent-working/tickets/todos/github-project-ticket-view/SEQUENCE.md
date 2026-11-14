# Implementation Sequence: github-project-ticket-view

Epic `TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW`, filed by agent-working-planner-u24 on 2026-11-12. Source: owner #715
6813165811. Designed by agent-working-designer-u24, and lead-planner-u24 OK'd the design. Design: main-checkout
`.claude/handover/drafts/github-project-ticket-view-2026-11-12.md`.

## Order

1. **DONE** TCK-20261112-PROJECT-SYNC-DRY-RUN (P0, standard): `project_sync.py --dry-run` on u24, rpg lanes. Merged in #889
   (c73d76bad). The owner's go was 6813165811.
2. **DONE** TCK-20261112-PROJECT-SYNC-GUARD-SEAT-AND-STALE (P1a, standard): merged in #893 (f62d240d0). Scope: the guard fix first, then seat mapping (investigated first), `Stale`, the
   entry point and the host name. Dry-run only, covered by go 6813165811 (split by the lead on #715).
3. **DONE** TCK-20261114-PROJECT-SYNC-INIT-AND-APPLY (P1b, standard; merged in #909, 6b8b56eda): `--init`/`--apply` on u24, rpg lanes, run by hand. The owner's
   fresh go is #715 6873359996 (P1b only). It needs the owner's empty org Project under rpg-sim-lab (its number goes into
   session_project.yaml). The first `--init` is the fine-grained token's write proof; if it is refused, stop, because the classic
   `project` fallback is the owner's decision.

4. **DONE** TCK-20261114-PROJECT-SYNC-LAYER-EPIC-PRIORITY-TAGS (P1c, standard; merged in #910, fc62c8557): Layer, Epic, Priority and
   Tags fields, rpg lane. The owner's go was #715 6874493351.
5. TCK-20261114-PROJECT-SYNC-SECOND-HOST (P2, standard): ubuntu writes Project 1 as a second host, rpg lane, run by ubuntu's
   agent-working-implementer. It settles the two-writer question with host-scoped ownership (a `Host facts` field; Status, Seat
   and Domain come from the union of all hosts, and nothing is archived while another host has facts for the item). The owner's
   go is #715 6875225978 item 2. The ubuntu token is in place (lead-planner-u24, 2026-11-14). No u24 `--apply` from ubuntu's
   first `--init` until P2 merges.

P3 prerequisite, not cut: TCK-20261114-PROJECT-CLIENT-WRITE-PACING (write pacing and retry-after). It is filed in this folder and is not
implemented until P3 is dispatched.

## Not cut yet

- **P3:** all lanes and a per-host timer. Needs the owner's timer decision.
- **P4:** the claim-rule change. Needs the owner's decision after P3.

## Rules

- Every child closes its own ticket, and none of them is a ride-along, because each one is code.
- The ticket files stay the only source. Nothing reads the Project back into tickets.
