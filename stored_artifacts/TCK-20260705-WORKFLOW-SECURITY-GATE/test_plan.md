---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKFLOW-SECURITY-GATE
artifact_type: test_plan
tags: [tagging, security, workflows]
---

# Test Plan — TCK-20260705-WORKFLOW-SECURITY-GATE

## Regression Surface

- **No existing automated test exercises `.claude/workflows/*.js` semantics.** Confirmed by a repo-wide
  search of `tests/` and `tools/` for references to `implement-ticket` or `workflows/*.js` — zero hits.
  These files are interpreted by the Claude Code harness's own DSL runtime (`agent()`, `phase()`, `log()`,
  `workflow()` are harness-injected primitives, not real Node.js globals or Python functions); there is no
  pytest or Node test runner wired to them. `tickets/done/TCK-20260607-MON-CAPTURE.md`'s own Test Summary
  states the established precedent verbatim: *"No automated tests added (workflow script testing is
  manual)."* This ticket should not invent a new testing pattern that other workflow-file tickets don't
  follow.
- **`tools/agent-monitoring/{record_run,record_events,validate,query,generate_retro}.py`** — must continue
  accepting the new phase's event records and the new `final_status` value with zero code changes. Confirmed
  none of these five scripts validate phase names or `final_status` against an enum/allowlist (`record_run.py`
  only checks 5 required *keys* are present; `validate.py`'s `LEGACY_TERMINAL_STATUS_VALUES` is a legacy
  backward-compat fallback for old records missing `end_ts`, not an enforced schema). No test regression
  risk here as long as the new phase's `pushEvent`/`writeMonitoring` calls follow the exact same call shape
  as every existing phase's calls.
- **`tests/tools/test_validate_frontmatter.py`** — validates ticket/doc YAML frontmatter schema. Unaffected
  unless `docs/ai/workflows.md`, `docs/ai/system_overview.md`, or `docs/ai/ticket-lifecycle.md` frontmatter
  is touched carelessly while updating body content — run as a regression guard since this ticket does
  modify those 3 doc files.
- **`tests/tools/test_registry_query.py`** — covers `tools/registry_query.py`'s `SEED_TAGS`/
  `candidate_tags_from_text`/`filter_registry`. Not touched by this ticket (the mis-tag heuristic is
  recommended as a standalone list, not a `registry_query.py` addition — see investigation.md) — run only
  as a negative-control check that this ticket did not accidentally modify that module.
- If a new `.claude/agents/security-reviewer.md` is added: no existing test validates `.claude/agents/*.md`
  structure (confirmed none exists), so nothing regresses, and this ticket gains no automated coverage from
  adding it — acceptable, matching every other agent `.md` file in the repo (none have dedicated tests).

## New Tests Required

Since `.claude/workflows/implement-ticket.js` has no executable Python/pytest surface, "tests" for this
ticket are necessarily structural/manual verification steps — the same category MON-CAPTURE used. Per AC:

1. **Syntax validity** — `node -c .claude/workflows/implement-ticket.js` must exit 0 after the edit (the
   one fully automatable check available; confirms no stray brace/paren broke the file).
2. **Trigger correctness (AC 1 & 2, security-tagged ticket)** — grep-verify the new gate's `agent(...)`,
   `phase(...)`, and both `pushEvent(...)` calls (success and failure paths) are the *only* code reachable
   inside `if (ticketInfo.suggested_skills && ticketInfo.suggested_skills.includes('/security-review')) { ... }`,
   and that this `if` sits between Parity's `pushEvent` (currently line 550) and `phase('Verify')` (currently
   line 554).
3. **Zero-cost inert path (AC 3)** — grep-verify there is no `else` branch on the new `if` that calls
   `pushEvent`, `agent`, or any monitoring write; the mis-tag `WARNING` (if implemented as a separate `log()`
   check) must not itself be gated behind the trigger `if` and must never call `pushEvent`. Confirm by
   diffing `agent-monitoring/events.jsonl` line count for two runs of an identical non-`security`-tagged
   ticket — one against the pre-change file (e.g. via `git stash`), one post-change — must be identical
   counts (byte-identical per AC 3's literal wording).
4. **Distinct status/phase naming (AC 4)** — `grep -n "status: '" .claude/workflows/implement-ticket.js`
   and `grep -n "pushEvent('" .claude/workflows/implement-ticket.js` before implementation, to enumerate
   every existing `status` and phase-label string; confirm the new gate's chosen values (e.g.
   `SECURITY_BLOCKED`, `'Security-Review'`) do not appear anywhere in that enumeration.
5. **Mis-tag WARNING correctness (AC 5)** — construct two synthetic checks against the recommended keyword
   list (`credential`, `secret`, `password`, `api_key`, `private_key`, `.env`, `oauth`, `jwt`; explicitly
   excluding `auth`, `cert`, `key`, `token`, `session`):
   - Positive control: a `Related Code Areas` line like `src/api/auth/credentials.py` or
     `config/secrets.env` should trigger the WARNING when no `security` tag is present.
   - Negative control (collision guard): `src/engine/authoritative_pipeline.md` and
     `src/certification/harness.py` must **not** trigger the WARNING — these are the two confirmed
     real-codebase collision hazards (`authoritative`/`authoring` vs. bare `auth`; `certification` vs. bare
     `cert`) documented in investigation.md. This negative control is the single most important new check
     in this plan — a naive keyword list would silently spam false-positive warnings on nearly every
     engine-touching ticket.
6. **Doc updates (AC 6)** — after editing `docs/ai/workflows.md`, `docs/ai/system_overview.md`, and
   `docs/ai/ticket-lifecycle.md`, run `make knowledge-index-update` per CLAUDE.md's rule ("If any files
   under `docs/` were created or modified"). This is a required step, not optional, and is easy to forget
   since it's a Makefile target rather than a pytest command.

## Scoped Pytest Commands

No Python source is expected to change for the core gate (it lives entirely in `.claude/workflows/*.js`,
`.claude/agents/*.md`, and `docs/ai/*.md`). Run these as regression guards only:

```
python3 -m pytest tests/tools/test_validate_frontmatter.py -v
python3 -m pytest tests/tools/test_registry_query.py -v
```

If Plan decides to implement the mis-tag keyword check as a testable Python helper (e.g.
`tools/security_tag_heuristic.py`, mirroring `tools/registry_query.py`'s pattern) rather than as inline
prompt instructions, add a new `tests/tools/test_security_tag_heuristic.py` following
`tests/tools/test_registry_query.py`'s exact structure (a positive-match test and a
`assert candidate_tags_from_text(...) == set()`-style negative/empty-set test), and include the two
collision negative-controls from item 5 above as explicit test cases:

```
python3 -m pytest tests/tools/test_security_tag_heuristic.py -v   # only if this module is created
```

Do not run the full suite (`pytest tests/`) — out of scope per CLAUDE.md's Testing Rule, and this ticket's
change surface does not touch simulation/`src/` code that the broader suite covers.

## Anti-Drift Test Guards

- **Never let the mis-tag heuristic collide with `authoritative`/`certification` vocabulary.** Any future
  extension of the keyword list must re-run the same `grep -rli <new-term> src/` collision spot-check
  documented in investigation.md before merging — this codebase's own naming conventions (`AuthoritativeState`,
  `authoritative_pipeline.md`, `CertificationHarness`) make naive security-keyword substrings unusually
  collision-prone compared to a typical repo.
- **Never let the new gate silently gain a `pushEvent` in its non-triggering path.** The AC's
  "byte-identical events.jsonl" requirement is stronger than "roughly the same" — any stray `log()`-to-
  `pushEvent()` upgrade later (e.g. someone "improving" the WARNING into a tracked event) would silently
  break AC 3 for every non-security ticket ever run afterward; flag this explicitly in code comments near
  the new `if` block.
- **Never reuse `SECURITY_BLOCKED` (or whatever name is chosen) for a different meaning later.** Because
  `final_status` has no enum anywhere in the monitoring tooling, nothing will structurally stop a future
  ticket from repurposing the string — the only guard is human/agent discipline plus the retro report
  (`make agent-monitoring-retro`) actually separating the two `Review`/`Security-Review` phases in its
  tier/gate-failure breakdowns, per this ticket's own AC 4. Spot-check this after the first real run by
  querying `agent-monitoring/events.jsonl` for `"phase":"Security-Review"` and confirming it never merges
  with `"phase":"Review"` counts in `tools/agent-monitoring/generate_retro.py`'s output.
