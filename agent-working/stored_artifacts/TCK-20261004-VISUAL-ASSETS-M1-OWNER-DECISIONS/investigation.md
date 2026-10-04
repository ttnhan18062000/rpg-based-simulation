---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M1-OWNER-DECISIONS
artifact_type: investigation
tags: [architecture, documentation]
---

# Investigation — TCK-20261004-VISUAL-ASSETS-M1-OWNER-DECISIONS

- `gc --delete` prints each removed item: `visual_assets/store/cli.py`, the `gc` branch (`deleted <kind> <name> (<reason>)`).
- `VisualKeyDefinition` (`visual_assets/store/contracts/definitions.py`) accepts a non-empty `variant_axes`; only duplicate axis names are checked, nothing resolves them. So the D17 freeze is a rule, not a mechanism: `W03.1` stays `GAP` until the parked `verify` rule exists.
- The register's own unblock criterion for `W05.4` allowed "record that one person holds every role", so D13 meets it; separation is stated as not achieved.
- `W10.6`: a printed line is not an audit record; judged MET by the decision, said so in the row.
- Epic table rows not given an ADR row: the `AM-M0` authorization (recorded in `docs/assets/m0_discovery_result.md`) and `W13.3/4/6` (register notes, carried to `AM-M6`).
