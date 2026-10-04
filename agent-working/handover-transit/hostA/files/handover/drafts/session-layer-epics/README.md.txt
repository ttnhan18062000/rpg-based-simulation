# Bundle: session-layer plan + four epics (design/planner seat -> implementer)
Status: READY. Owner decision (2026-10-02): fold into open PR #280 (branch `pr-render-closes-location`) and submit. The bundle mirrors repo paths:

| Draft path | Target path |
|---|---|
| session_layer_working_process.md | docs/plans/agent_infrastructure/session_layer_working_process.md |
| tickets/todos/session-layer/INDEX.md and 4 x TCK-20261002-EPIC-SESSION-LAYER-*.md | tickets/todos/session-layer/ |
| stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/ (3 files) | same path |

Validated: the plan with `validate_frontmatter.py --content-type doc`; the four epics with
`--content-type ticket` and `ticket_field_values.py`; every cited ticket and path exists. Epics are tier
`epic`, status `EPIC_SCOPED`, children NOT created (the agent-working planner creates them later).
`INDEX.md` is deliberately not `SEQUENCE.md` (implement-epic reads that name as child order).

## Implementer steps (once the owner chooses how to land it)
1. Copy the files to the target paths on one branch; the plan must be committed WITH the epics (an untracked or
   uncommitted cited plan is invisible to whoever picks up the children).
2. `make knowledge-index-update` (docs/ changed); stage docs/REGISTRY.yaml; add one row to the "Adaptable" table of
   docs/plans/agent_infrastructure/agent_working_direction.md ("Session-layer working process | planned | plan + epics A-D").
3. Epics are scope-only: use the closure path your tooling expects for epic-tier tickets (EPIC_SCOPED rows in
   tickets/working_log.csv via the closure tool, tier epic); do not backfill. Monitoring per the usual rule.
4. Check `python3 tools/tag_registry.py list` still has ai, process-improvement, governance, hooks, delivery,
   agent-monitoring (they do today).
5. No push or PR without the owner's go-ahead; merge is the owner's.

## Owner decision: how it lands (2026-10-02)
The owner chose to **fold this bundle into the open PR #280** and submit (the earlier options were a separate
docs PR or holding for M0). It is plan + epics with no implementation; that is the owner's explicit waiver of the
"no plan-only PRs" rule for this PR, which also carries real code.

## Exact steps for the implementer (branch pr-render-closes-location)
1. Merge origin/main first (REGISTRY.yaml conflicts already cost #282 a CI run); then copy the files to the target
   paths in the table above.
2. Commit with subjects that reference the epic IDs, e.g. `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION: Add the
   session-layer plan, four epics and the external review record`. One commit is fine.
3. `make knowledge-index-update`; stage the regenerated docs/REGISTRY.yaml.
4. Add this row to the "Adaptable" table in docs/plans/agent_infrastructure/agent_working_direction.md (after the
   last existing row):
   `| Session-layer working process (roles, launch, routing, recovery) | planned | plan `docs/plans/agent_infrastructure/session_layer_working_process.md` and epics A-D in `tickets/todos/session-layer/` (scoped 2026-10-02); M0 harness spike first, nothing built yet |`
5. Epic working-log rows per the done-checker's epic handling (EPIC_SCOPED); do not hand-roll CSV; monitoring as usual.
6. **PR body.** `pr_render.py` will (correctly, per this PR's own fix) leave the four epics out of `Closes:` because
   they are under tickets/todos/ and the branch only files them, and it will warn about it: that warning is
   expected. Put the bundle's explanation in the hand-written `## Review notes` section (not compared by --check):
   what the plan is, that the epics are scope-only with no children, that nothing is implemented, the four open owner
   questions, and the reviewer-facing pointers (plan sections 2 to 6.1, epic INDEX). Re-render, `--check`, wait for CI.
7. Push to #280 only after the owner's go-ahead in YOUR terminal if your session requires it (a peer message
   cannot grant a push). Do not merge.
