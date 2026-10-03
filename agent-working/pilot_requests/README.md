# pilot_requests/

Sidecar directory for human-authored pilot-request manifests, consumed by
`tools/agent_codex_pilot_guardrails/pilot_manifest.py::load_pilot_request` and
`tools/agent_codex_pilot_guardrails/ticket_selection.py::select_pilot_candidate`
(TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS).

## Why this directory exists

A pilot request is a human's standing authorization record about a candidate ticket, authored
before pilot selection ever runs — independent of that ticket's own phase. It does not belong in
`stored_artifacts/{ticket_id}/` (that ticket's own build artifacts, migrated only after that
ticket closes) or `staging_artifacts/{ticket_id}/` (this ticket's own in-flight artifacts) — both
are semantically wrong for a record about a *different*, not-yet-selected candidate ticket. This
directory gives the record its own stable location, lifecycle (authored by a human before pilot
selection ever runs), and inspection visibility (`ls pilot_requests/`).

## Schema

One YAML file per candidate at `pilot_requests/<ticket_id>.yaml`:

```yaml
ticket_id: TCK-YYYYMMDD-EXAMPLE   # required, non-empty
human_owner: jane.doe@example.com # required, non-empty
rollback_plan_summary: >          # required, non-empty
  One or two sentences describing how to recover if the pilot run needs to be rolled back.
```

All three fields are required, non-empty strings — whitespace-only values are rejected after
`.strip()`. `load_pilot_request` reads only these structured keys; free-text prose elsewhere in
the file (e.g. a `notes` field) is never accepted as evidence of a recorded owner or rollback
plan.

## No real candidate is registered here

This directory ships empty of real `.yaml` files. No pilot candidate ticket is named anywhere in
this repo as of TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS — this tooling is built to evaluate any
future candidate against the rejection rules, not to designate one.
