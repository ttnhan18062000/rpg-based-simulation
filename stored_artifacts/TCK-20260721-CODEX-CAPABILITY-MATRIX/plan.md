---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-CODEX-CAPABILITY-MATRIX
artifact_type: plan
tags: [ai, workflows, process-improvement]
---

# Implementation Plan — TCK-20260721-CODEX-CAPABILITY-MATRIX

## Summary

This ticket produces one new durable decision-record doc, `docs/ai/codex_capability_matrix.md`, plus one new isolated diagnostic test, `tests/tools/test_codex_capability_diagnostics.py`. The doc enumerates the six required rows (current Codex capabilities, project trust behavior, all ten lifecycle hook events, role/delegation model, skills/configuration surfaces, payload/fixture gaps), with every entry citing a source and a verification date of today's execution date (2026-07-21) — not carried over unchanged from the plan's stale 2026-07-20 citation (AC1). All ten hook events are individually marked VERIFIED, each backed by an excerpt quoted directly from `/tmp/openai-docs-cache/codex-manual.md` into the durable doc (not just a path reference, since that cache is not guaranteed to persist) (AC2). The `codex features list` output (`hooks stable true`), already gathered as direct-experiment evidence during investigation, is cited as the matrix's fixture-experiment entry and is distinguished explicitly from documentation-citation entries; this same command is codified as a skippable diagnostic test so the evidence is re-runnable rather than a one-off manual finding (AC3). A dedicated "Divergences / Silences" section states plainly that no divergence was found between the manual and the plan's ten-hook claim, and separately flags what the plan was silent on (capabilities/trust/roles/skills detail) plus the residual limitation that live WebFetch re-verification is blocked in this sandbox (AC4). The deeper stdin-payload-capture fixture experiment (writing an isolated `hooks.json` outside the repo and running `codex exec` against it) is explicitly decided **not** to be performed in this ticket — `codex features list` already satisfies AC3's literal wording as a genuine direct-experiment result distinct from documentation citation, and payload-capture is recorded in the matrix as a deferred future enhancement, consistent with test_plan.md's own "optional, explicitly deferred" framing. No production Claude/Codex file, no `src/engine/capability.py`, and no `.codex/` directory inside this repo is touched anywhere in this plan.

## Steps

### Step 1 — Confirm regression baseline before any change
**Files:** none (verification only)
**Change:** Run the three scoped regression commands from `test_plan.md`:
```
.venv/bin/python3 -m pytest tests/unit/engine/test_capability_registry.py tests/architecture/test_capability_references.py -v
.venv/bin/python3 -m pytest tests/unit/lab_agent/ tests/integration/lab_agent/ -v
.venv/bin/python3 -m pytest tests/tools/test_post_tool_hook.py -v
```
Confirm all pass before writing anything, so any later failure can be attributed to this ticket's own changes rather than pre-existing drift.
**Do NOT touch:** Any file. Read-only verification.
**Verify:** All three commands exit 0 with no failures.

### Step 2 — Write the Codex capability matrix doc
**Files:** `docs/ai/codex_capability_matrix.md` (new file)
**Change:** Create the doc with frontmatter matching the sibling precedent (`docs/ai/agents_dir_disposition.md`): `status: active`, `layer: ai`, `authority: P1`, `audience: developer`, `tags: [ai, workflows, process-improvement]` (all three already registered — reuse verbatim, do not invent new tags). Content, at minimum:

1. **Header note** stating this is a standalone artifact per AC1 — distinct from, and re-verified independently of, `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md:108`'s 2026-07-20 citation. Every entry below carries its own verification date of **2026-07-21** (today's execution date), not inherited from the plan doc.

2. **Lifecycle Hook Events table** — one row per event, columns: Event | Status (VERIFIED for all ten) | Scope (turn vs thread/subagent-start, per manual lines 9163-9166) | Matcher support (per manual lines 9443-9454) | Common input fields (per manual lines 9494-9510) | Output fields honored (per manual lines 9517-9549) | Source. Quote the load-bearing text directly from `/tmp/openai-docs-cache/codex-manual.md` (re-read lines 9144-9567 fresh at implementation time) into the doc body — do not cite only the `/tmp` path, since investigation.md flags that cache as non-durable. If the cache file is no longer present at implementation time, fall back to the WebSearch corroboration already gathered in investigation.md (`developers.openai.com/codex/hooks`, `deepwiki.com/openai/codex/3.11-hooks-system` snippets naming the same 10 events) and mark those rows' Source column accordingly with reduced confidence — do not silently reuse the plan's original citation without a fresh execution-date note.
   - The ten events, unchanged from the plan and corroborated by the cache: `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `SubagentStop`, `Stop`, `SessionStart`, `SubagentStart`.
   - Note the two known field-coverage asymmetries the manual documents (not divergences from the plan, since the plan never claimed field-level detail): `permission_mode` is listed for 8 of 10 events but not `PreCompact`/`PostCompact` (manual line ~9494-9510); `PreToolUse`/`PermissionRequest` reject `continue`/`stopReason`/`suppressOutput` in their output (manual line ~9517-9549).

3. **Current Codex Capabilities** section — summarize from the cached manual's relevant sections (capabilities overview, `codex features list` output), cite line numbers, verification date 2026-07-21.

4. **Project Trust Behavior** section — quote/paraphrase manual line 3170 and line 9196-9198 (untrusted projects ignore `.codex/` layers including hooks/config/rules; user/system layers still load). Cite both line locations.

5. **Role/Delegation Model** section — summarize manual's `[agents]` in `config.toml` heading (line 3219) and "Roles and workspace permissions" (line 12976).

6. **Skills/Configuration Surfaces** section — summarize manual's "Build skills" (line 8395), "Skill controls" (line 13051), "Skills & Plugins" (line 15450).

7. **Payload/Fixture Gaps** section (AC3) — two clearly distinguished sub-entries:
   - "Documented in official docs": the field tables above (common input/output fields, matcher support) — sourced from documentation review only, not independently confirmed against a live payload.
   - "Fixture-confirmed by direct experiment": cite the investigation's `codex features list` output verbatim (`hooks   stable   true`), run against this environment's installed `codex-cli 0.144.6` (`~/.codex/` present, authenticated). State explicitly this confirms the hooks *capability* is live and enabled on the installed build — it does not itself confirm exact per-event stdin payload shape. Record the deeper stdin-payload-capture experiment (isolated `hooks.json` outside the repo, `codex exec` against a throwaway fixture, capture real JSON for one event) as an explicitly deferred future enhancement — not performed in this ticket, and not required to satisfy AC3's literal wording, which asks only that at least one entry cite a fixture-experiment result distinct from documentation citation.

8. **Divergences / Silences vs. the plan's existing claims** section (AC4):
   - State plainly: no divergence was found — all ten hook names, scopes, and existence are corroborated exactly as the plan (2026-07-20) claimed.
   - Silences: the plan's citation covered only the ten hook names; it said nothing about capabilities/trust/roles/skills detail (rows 3-6 above) or field-level payload tables — this matrix is the first artifact to cover those, sourced fresh from the manual.
   - Residual limitation: `WebFetch` is blocked in this sandbox (self-signed-certificate error on all three URLs tried, including a control URL) — live re-fetch of `https://learn.chatgpt.com/docs/hooks.md` to confirm it has not changed since the 2026-07-20 snapshot is not currently possible from this environment. `WebSearch` works and returned corroborating third-party summaries; this is noted as a residual limitation, not a blocker, since the cache + CLI evidence together are sufficient for VERIFIED status per the investigation's own conclusion.

**Do NOT touch:** `src/engine/capability.py`, `docs/engine/capability_registry.yaml`, any file under `.agents/`, `.claude/`, or `tools/agent-monitoring/`. This step only creates the new doc.
**Verify:** Manual review — all six required rows present, all ten hooks individually marked VERIFIED, at least one entry distinguishes fixture-confirmed from documentation-cited evidence, a Divergences/Silences section exists, every entry's verification date reads 2026-07-21. No executable test covers doc content (per test_plan.md's Anti-Drift Test Guards: "No test in this plan should assert on the content of the matrix doc itself").

### Step 3 — Add the diagnostic test codifying the fixture-experiment evidence
**Files:** `tests/tools/test_codex_capability_diagnostics.py` (new file)
**Change:** Add `test_codex_hooks_feature_reported_enabled` (or equivalent name), sibling in style to `tests/tools/test_post_tool_hook.py`. Behavior:
- Guard with `shutil.which("codex")`; if `None`, `pytest.skip("codex CLI not installed in this environment")` — CLI presence is an environment fact, not a repo invariant.
- If present, run `codex features list` via `subprocess.run(..., capture_output=True, text=True)` and assert the captured stdout contains a `hooks` row reporting a truthy/`stable` state (parse loosely — a substring/regex check on the `hooks` line, not an exact full-output match, since output formatting is provider-controlled and not this repo's contract to pin exactly).
- Do not assert on any other `codex features list` row — only the `hooks` line is this ticket's concern.
- Mark the test with a short docstring citing this ticket ID and explaining it codifies the investigation's manually-gathered direct-experiment evidence into a re-runnable diagnostic.
**Do NOT touch:** `tests/tools/test_post_tool_hook.py` itself, or any file under `tools/agent-monitoring/`. Do not add the second, optional payload-capture test (`test_codex_pretooluse_payload_matches_documented_schema`) described in test_plan.md — that is explicitly deferred, not part of this ticket's scope (see Step 2's Payload/Fixture Gaps decision).
**Verify:** `.venv/bin/python3 -m pytest tests/tools/test_codex_capability_diagnostics.py -v` → 1 passed (in this environment, where `codex` is installed and authenticated) or 1 skipped (in an environment without `codex` on `PATH`) — either outcome is a valid pass state for this test.

### Step 4 — Full scoped regression pass
**Files:** none (verification only)
**Change:** Re-run all commands from Step 1 plus the new test:
```
.venv/bin/python3 -m pytest tests/unit/engine/test_capability_registry.py tests/architecture/test_capability_references.py -v
.venv/bin/python3 -m pytest tests/unit/lab_agent/ tests/integration/lab_agent/ -v
.venv/bin/python3 -m pytest tests/tools/test_post_tool_hook.py -v
.venv/bin/python3 -m pytest tests/tools/test_codex_capability_diagnostics.py -v
```
**Do NOT touch:** Nothing new here — pure verification. If anything outside the new files changes behavior, that is scope creep — stop and investigate rather than editing further files to "fix" it.
**Verify:** All four commands exit 0. `git status` afterward shows changes confined to: `docs/ai/codex_capability_matrix.md` (new), `tests/tools/test_codex_capability_diagnostics.py` (new), plus this ticket's own artifacts (`tickets/inprogress/TCK-20260721-CODEX-CAPABILITY-MATRIX.md`, `staging_artifacts/TCK-20260721-CODEX-CAPABILITY-MATRIX/*`, `agent-monitoring/`). Nothing under `src/engine/`, `.agents/`, `.claude/`, `.codex/`, or `tools/agent-monitoring/*.py` should appear.

### Step 5 — Update the ticket body with the decision and results
**Files:** `tickets/inprogress/TCK-20260721-CODEX-CAPABILITY-MATRIX.md`
**Change:** Fill in `## Implementation Notes` (summarize the matrix doc's structure and the decision not to perform the deeper payload-capture experiment), `## Test Summary` (paste Step 4's pass/skip counts), `## Files Changed` (the exact list from Step 4's `git status`), and `## Completion Summary`. Check all four `## Acceptance Criteria` boxes. Do not alter `## Scope`, `## Out of Scope`, or `## Related Tickets`.
**Do NOT touch:** Frontmatter fields other than what closure conventions require.
**Verify:** All four AC checkboxes ticked with content matching what Steps 2-4 actually produced.

## Scope Guards

- Do not modify `src/engine/capability.py`, `docs/engine/capability_registry.yaml`, `tests/unit/engine/test_capability_registry.py`, or `tests/architecture/test_capability_references.py` — coincidentally-named, unrelated simulation-engine system.
- Do not create, modify, or trust any `.codex/` directory inside this repository (confirmed none currently exists).
- Do not touch `.claude/settings.json`, any `.claude/workflows/*.js`, `.claude/agents/*.md`, or `tools/agent-monitoring/*` (owned by sibling ticket `TCK-20260721-MONITORING-WRITER-DECISION`).
- Do not touch `.agents/` (owned by sibling ticket `TCK-20260721-AGENTS-DIR-DISPOSITION`, already closed).
- Do not perform the isolated `hooks.json` / `codex exec` stdin-payload-capture fixture experiment — explicitly decided as deferred future work in Step 2, not required by AC3's literal wording.
- Do not add the optional `test_codex_pretooluse_payload_matches_documented_schema` test or its fixture — deferred alongside the payload-capture experiment above.
- Do not open or scope any Codex provider-runtime implementation ticket — blocked until all five discovery outputs across `TCK-20260721-PROVIDER-AGNOSTIC-EPIC` are complete and approved.
- Do not run `pytest tests/` broadly — use only the scoped commands in Steps 1 and 4.
- Do not edit `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md` — the matrix is a standalone artifact per AC1, not a merge into the existing plan citation.

## Dependency Map

- Step 1 has no dependencies; run first to establish a clean baseline.
- Step 2 (matrix doc) has no code dependency on Step 1 but should follow it for narrative safety.
- Step 3 (diagnostic test) is independent of Step 2's file but references the same evidence Step 2 documents — write after Step 2 for narrative consistency, though no file-level dependency exists.
- Step 4 depends on Steps 2 and 3 both being complete (regression pass needs the final state, including the new test file).
- Step 5 depends on Step 4 (ticket closure documents actual verified results, not planned ones).
- All steps are otherwise sequential and independently verifiable.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — standalone matrix artifact enumerating capabilities/trust/hooks/roles/skills/gaps, each cited with a fresh (2026-07-21) verification date, not carried over unchanged from the plan's 2026-07-20 citation | Step 2 | Manual doc review (no executable test; documentation deliverable, per test_plan.md's Anti-Drift Test Guards) |
| AC2 — all ten hook events individually marked VERIFIED or UNVERIFIED/DIVERGENT | Step 2 | Manual doc review |
| AC3 — at least one entry cites a provider fixture-experiment result, distinguished from documentation-citation entries | Step 2 (writes the distinguishing entry), Step 3 (codifies it as a re-runnable test) | `.venv/bin/python3 -m pytest tests/tools/test_codex_capability_diagnostics.py -v` → 1 passed or 1 skipped |
| AC4 — matrix explicitly calls out divergence/silence/irreconcilable gaps vs. the plan's existing claims | Step 2 | Manual doc review |

## Anti-Drift Notes

- **The `/tmp/openai-docs-cache/codex-manual.md` cache is not durable.** Step 2 must excerpt the load-bearing text directly into `docs/ai/codex_capability_matrix.md`, not merely cite the `/tmp` path — if the cache is gone by implementation time, fall back to the WebSearch corroboration already recorded in investigation.md and mark those rows with reduced-confidence sourcing rather than silently reusing the plan's original citation.
- **`codex features list` is capability-presence evidence, not payload-shape evidence.** Do not let Step 2's Payload/Fixture Gaps section imply that `hooks: stable, true` confirms exact per-event JSON schema — it confirms only that the hooks feature is live and enabled on this installed build. The distinction must be explicit in the doc, per AC3's own wording.
- **`src/engine/capability.py` and its tests are a false lead.** The "Related Code Areas" field on the ticket names them only due to a coincidental "capability matrix" name collision with an unrelated simulation-engine system (see investigation.md's Parity Ledger Overlap section) — Step 1/4's regression commands exist specifically to prove this ticket did not touch them.
- **Do not let "no dependency on sibling children" become "ignore sibling closure state."** `tests/unit/lab_agent/` and `tests/integration/lab_agent/` are included in the regression surface specifically to confirm this ticket does not silently perturb the just-closed `TCK-20260721-AGENTS-DIR-DISPOSITION` work, even though there is no functional dependency between the two tickets.
- **The deeper stdin-payload-capture experiment is a deliberate scope decision, not an oversight.** If a future ticket (e.g. `TCK-20260721-ORCHESTRATION-CONTRACT-ADR` or a dedicated `CODEX-REPLAY-PROOF` per `SEQUENCE.md`) needs byte-exact payload verification, that is new scope for that ticket, not a gap to be silently filled here.
