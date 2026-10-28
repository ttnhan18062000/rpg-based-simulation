---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, performance]
---

# Run ledger: a started row and an end row per paired or gate invocation

`TCK-20261023-MEASURED-STEP-RUN-AND-RERUN-LEDGER` (T1 of `docs/plans/architecture/faster_feature_testing_draft_tickets.md`). The authoritative description is the docstring of
`tools/test_architecture/run_ledger.py`; this page is the orientation.

**What it is evidence for.** How many paired or gate runs a measured step took, how many were reruns, how long they took per arm and what the peak memory was,
and why an invocation ended (PASS, STOP, REFUSED, KILLED, ERROR). It is what lets a plan name the dominant term of the step cycle instead of quoting a handover.

**What it is not.** It is never a gate. Nothing reads it to pass or fail a run, no CI job gates on it and nothing uploads it (T2 decides what its workflow keeps).
A write failure prints a warning on stderr and never changes an invocation's exit code.

## File and rows

Append-only JSONL, default `data/ledgers/run_ledger.jsonl` (git-ignored), override with `RUN_LEDGER_PATH`. One line per row, one `O_APPEND` write each.
Schema `run-ledger/v1`; every field is required, the nullable ones are marked. This page and the module docstring are the one written source of the v1 schema. `mode` and `workers` were
added to the ticket's Scope 2 on 2026-10-26 at rpg-planner's request (so paired rows can be read correctly) and accepted by testing-planner the same day:

| field | meaning |
|---|---|
| `schema` | `run-ledger/v1` |
| `invocation_id` | uuid4, shared by the started row and the end row |
| `tool`, `mode` | `paired` with `step` / `neutral` / `report_only`, or `gate` with `gate`. `mode` says what a PASS means: a `report_only` PASS suppresses STOP and is not a real pass; `neutral` IDENTICAL is PASS and DIFFERENT is STOP |
| `step` | paired `--step`, or the gate's milestone / dispatch label (`--step`, default `gate`) |
| `workers` | strict integer >= 1 (no boolean): the parallelism (`--jobs` / `--workers`) the per-arm wall time depends on |
| `base_sha` (nullable), `new_sha` | `base_sha` is null for gate |
| `worlds`, `seeds`, `ticks` | what was run |
| `started_at`, `ended_at` (nullable) | ISO, timezone-aware |
| `outcome` (nullable), `outcome_detail` (nullable) | `PASS` / `STOP` / `REFUSED` / `KILLED` / `ERROR`, with the typed reason (e.g. a `NonAuditRunError` message) |
| `rerun_of` (nullable) | the earlier `invocation_id`, given by the caller (`--rerun-of`), never guessed |
| `runs` | per arm run: `arm` (`base`/`new`/`self`/`gate`), `world`, `seed`, `wall_seconds`, `peak_rss_mb` (nullable), `cached` (true = served from the cache, not executed) |
| `host` | `name`, `nproc`, `mem_total_mb`, `python`, `platform` |

A killed invocation cannot write its own end row, so every invocation first writes a *started* row (`outcome` and `ended_at` null) and an end row with the same
`invocation_id` when it finishes. The summary reads a started row with no end row as `KILLED`. `RunLedgerRow.from_json` rejects an unknown or missing field and a wrong type,
naming the field; a writer builds rows through the dataclass, never by hand.

## Rules the paired hook (AC4) is reviewed against

`from_json` accepts only these `tool`/`mode` pairs and names `mode` for any other: `gate` with `gate`; `paired` with `step`, `neutral` or `report_only`.

- Mapping confirmed by rpg-planner on 2026-10-26:
  - a neutral run's IDENTICAL is `PASS` and DIFFERENT is `STOP`, with the differing keys in `outcome_detail`;
  - a `NonAuditRunError` is `REFUSED`, its message in `outcome_detail`;
  - arm `self` is paired's base-vs-base repeat arm and is **never cached** (`cached: false`).
- A `report_only` invocation suppresses STOP, so its `PASS` is not a real pass: the summary counts it under `modes`, never as a step PASS.
- A caller that cannot finish (a host kill) still leaves its started row; it must not invent an end row.

## Summary

`python -m tools.test_architecture.run_ledger summary [--step S] [--since YYYY-MM-DD] [--json] [--path FILE]` prints, per step: invocations, reruns, runs executed and cached, total and
per-arm wall time of the executed runs, the max peak RSS, and the outcomes and modes by kind. `--json` prints the same as `run-ledger-summary/v1` plus `invalid_lines` (lines of the
file that were not valid rows; they are not counted).

## Writers

- Gate: `rpg_gate_harness.run_matrix` writes a started row and an end row per invocation (a no-data run makes the outcome `ERROR` and names it; an exception is `ERROR`; an interrupt is `KILLED`).
- Paired: `tools/rpg_measure/paired.py` writes a started row and an end row per invocation to this schema (rpg's hook ticket; testing reviews it). Arm `self` is paired's base-vs-base repeat arm and is never cached.
