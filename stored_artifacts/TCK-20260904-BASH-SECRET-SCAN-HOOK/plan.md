---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-BASH-SECRET-SCAN-HOOK
artifact_type: plan
tags: [governance, ai, hooks, security]
---

# Implementation Plan — TCK-20260904-BASH-SECRET-SCAN-HOOK

## Summary

Wire `scan_for_secrets()` (unmodified, from `tools/write_path_guard.py:149-166`) as a new,
additive `hooks.PreToolUse` array entry in `.claude/settings.json` (matcher `"Bash"`), using the
exact `python3 -c` one-liner already live-verified in `investigation.md`'s Current Behavior
section (confirmed there to fire on a synthetic secret-shaped command and stay silent on an
ordinary command). The new entry is advisory-only (`additionalContext`, never
`permissionDecision`/`deny`) and sits alongside — never replaces or edits — the four existing
`PreToolUse` entries. Add a new behaviorally-executed test file
(`tests/tools/test_bash_secret_scan_hook.py`) modeled on
`tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py`'s subprocess-execution pattern.
Update the three docs the investigation names as stale once this ships, and add a new
`INFRA-413` parity-ledger entry via the sanctioned `tools/parity_ledger_writer.py` writer. Do not
touch `tools/write_path_guard.py`, `redaction_retention_policy.md`, or `standalone_items.md` — all
three are explicit Scope Guards, restated below with the investigation's own reasoning.

## Steps

### Step 1 — Add the new `PreToolUse` hook entry to `.claude/settings.json`

**Files:** `.claude/settings.json`

**Change:** Confirmed live today (`python3 -c "import json; d=json.load(open('.claude/settings.json')); print([e.get('matcher') for e in d['hooks']['PreToolUse']])"` → `['*', 'Bash', 'Agent', 'Edit|Write']`, 4 entries, indices 0-3) that no `BASH-SECRET-SCAN-HOOK` entry exists yet and the array shape for each entry is `{"matcher": <str>, "hooks": [{"type": "command", "command": <str>}]}` — confirmed by reading the live `PreToolUse[1]` and `PreToolUse[3]` entries directly. Append a **5th** entry (`PreToolUse[4]`) with `matcher: "Bash"` and this command (reusing, verbatim, the exact snippet already live-verified in `investigation.md` lines 51-61 — do not re-derive a new one):

```
python3 -c "import json,sys
try:
    from tools.write_path_guard import scan_for_secrets
    d=json.load(sys.stdin)
    m=scan_for_secrets(d.get('tool_input',d).get('command',''))
    if m: print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','additionalContext':'secret-scan: possible '+m+' pattern detected in this Bash command. Advisory only, not blocked.'}}))
except Exception:
    pass" 2>/dev/null || true
```

Build this programmatically — `json.load()` the file, append the new dict to `data["hooks"]["PreToolUse"]`, `json.dump(data, f, indent=2)` and re-add the trailing newline the file currently ends with (confirmed live: `.claude/settings.json` is 143 lines, 2-space indent, ends `}\n`) — do **not** hand-type the escaped-quote JSON string directly into the file with Edit; the embedded `"` and newlines inside the python source make manual escaping error-prone and this file's existing entries (e.g. `PreToolUse[3]`) show the escaping is already non-trivial (`\'`, `\"` mixed). After writing, verify with `python3 -m json.tool .claude/settings.json` (must succeed) and re-confirm indices 0-3 are byte-identical to their pre-edit values.

**Other writer to this same shared resource (enumerated per Fact-Verification requirement):** `.claude/settings.json`'s `hooks` block was touched by two other same-batch tickets, both already merged and confirmed live in the current file: `TCK-20260904-TEST-SCOPER-HANG-GUARD` (added the `SubagentStop` key — untouched by this step, confirmed present in the live read above) and `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE` (edited `PreToolUse[3]`'s `RUN_ID` subshell body — untouched by this step). Both edits already landed before this ticket's Plan phase (confirmed by investigation's own live re-check), so there is no live race — this step is purely additive (append index 4) and does not collide with either.

**Do NOT touch:** `PreToolUse[0]`, `[1]`, `[2]`, `[3]`; `PostToolUse`; `SubagentStop`; `permissions.allow`.

**Verify:** `python3 -m json.tool .claude/settings.json`; new test `test_new_bash_secret_scan_hook_entry_registered` (Step 2); existing `tests/tools/test_settings_json_hooks_wiring.py::test_edit_write_hook_reads_scoped_sidecar_via_env_var` and `::test_edit_write_hook_still_fail_open_and_advisory` and `::test_edit_write_hook_json_still_valid_after_edit` must all stay green unmodified (proves `[3]` untouched).

---

### Step 2 — Update the stale `PreToolUse` length assertion this step's own addition breaks

**Files:** `tests/tools/test_settings_json_hooks_wiring.py`

**Change:** Read `tests/tools/test_settings_json_hooks_wiring.py:71-78` directly (`test_existing_hook_writers_untouched`): it asserts `assert len(settings["hooks"]["PreToolUse"]) == 4`. Step 1 appends a 5th entry, so this assertion will fail the instant Step 1 lands unless updated. This is a genuine other-writer collision on the same shared resource (the `PreToolUse` array's length), not something `test_plan.md` explicitly called out by exact line — `test_plan.md`'s Regression Surface section says only "must not change any index this file currently asserts on," which this fixed-length assertion is a stricter instance of. Change the literal to `assert len(settings["hooks"]["PreToolUse"]) == 5`, and add a one-line comment above it noting the count includes the new `TCK-20260904-BASH-SECRET-SCAN-HOOK` entry, so a future reader does not mistake the bump for scope creep. Leave `assert len(settings["hooks"]["PostToolUse"]) == 4` untouched — this ticket does not touch `PostToolUse`.

**Do NOT touch:** any other assertion in this file (all reference fixed indices `[3]` or fixed keys, none of which move when appending at index 4).

**Verify:** `pytest tests/tools/test_settings_json_hooks_wiring.py -v` — all tests pass, including the updated length assertion.

---

### Step 3 — New behavioral test file `tests/tools/test_bash_secret_scan_hook.py`

**Files:** `tests/tools/test_bash_secret_scan_hook.py` (new)

**Change:** Model directly on `tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py` (read in full: `_load_settings()` helper reads `.claude/settings.json` from `Path(__file__).parent.parent.parent`; tests either extract and run the bare inner `python3 -c` snippet via `subprocess.run(["python3", "-c", snippet], input=..., capture_output=True, text=True)`, or run the **full** command string via `subprocess.run(["bash", "-c", full_command], input=..., ...)` when the outer `2>/dev/null || true` wrapper's fail-open behavior is itself under test). Implement all 7 tests from `test_plan.md`'s "New Tests Required" section:

1. `test_new_bash_secret_scan_hook_entry_registered` — load settings.json, assert a `PreToolUse` entry with `matcher == "Bash"` and `"scan_for_secrets"` (or `"write_path_guard"`) in its command exists, distinct from `PreToolUse[1]`'s grep-nudge entry (both present).
2. `test_positive_fire_on_synthetic_secret_shaped_command` — parametrize over ≥3 of the 10 `_SECRET_SCAN_PATTERNS` keys (read `tools/write_path_guard.py:128-146` for the real pattern list/keys before picking synthetic examples — do not guess pattern names). Run the full command via `bash -c` with stdin `{"tool_input": {"command": "<secret-shaped literal>"}}`; assert stdout parses as JSON matching `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "<non-empty, names the pattern>"}}`.
3. `test_negative_no_fire_on_ordinary_commands` — parametrize over 2-3 ordinary commands (`"pytest tests/tools -q"`, `"git status"`, a plain `python3` script invocation); assert **empty** stdout.
4. `test_hook_never_emits_permission_decision_or_deny` — on a positive-fire case, assert no `"permissionDecision"` key anywhere in the parsed JSON and the wrapping process exits 0.
5. `test_hook_fails_open_on_malformed_or_missing_stdin` — malformed non-JSON stdin and stdin missing `tool_input.command`; assert exit code 0, empty stderr, no traceback (mirror `test_settings_json_edit_write_hook_sidecar_scope.py::test_malformed_or_missing_sidecar_json_degrades_to_empty_not_traceback`'s exact assertions).
6. `test_scan_for_secrets_module_unchanged_by_this_ticket` — per `test_plan.md`'s guidance, implement the "simpler and more robust" form: assert that running `tests/tools/test_write_path_guard.py`'s existing full suite still passes unmodified (call it via `subprocess.run([sys.executable, "-m", "pytest", "tests/tools/test_write_path_guard.py", "-q"])`, assert returncode 0) as the load-bearing proof that `scan_for_secrets()`/`_SECRET_SCAN_PATTERNS` behavior is unchanged — do not add a git-diff-against-HEAD check (test_plan.md itself flags that form as fragile across rebases).
7. `test_existing_bash_and_sidecar_hooks_untouched` — assert `PreToolUse[1]` and `PreToolUse[3]` command strings are byte-identical to the values already asserted/read in `test_settings_json_hooks_wiring.py` (hardcode the known-good strings or diff against a captured pre-Step-1 snapshot fixture — implementer's choice, document which was used in a file-level docstring comment).

**Do NOT touch:** `tests/tools/test_write_path_guard.py` itself (only invoked as a subprocess, never edited) — this ticket's `scan_for_secrets()` coverage guard depends on that file staying exactly as-is.

**Verify:** `pytest tests/tools/test_bash_secret_scan_hook.py -v` (all 7+ parametrized cases pass); this closes AC #4.

---

### Step 4 — Update `governance_capability_policy_epic.md` M4 section to SHIPPED

**Files:** `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`

**Change:** Read the live M4 section (lines 149-180) and the "Acceptance signal" M4 bullet (lines 228-230). Mirror the exact pattern already used for the sibling `guardrail_enforcement_epic.md`'s M3 (confirmed live, lines 105-107): change the M4 heading from `### M4 — Bash secret-exposure advisory hook (gated on the cross-epic extraction step — see roadmap.md)` to `### M4 — Bash secret-exposure advisory hook (gated on nothing — SHIPPED)`, and prepend a **SHIPPED** paragraph directly under the heading naming `TCK-20260904-BASH-SECRET-SCAN-HOOK`, the new `PreToolUse[4]` entry, and `tests/tools/test_bash_secret_scan_hook.py` (mirroring the guardrail M3 paragraph's structure: what shipped, which hook key, which test file verifies it). Leave the rest of the M4 body (scope boundary, named limitation, "ships advisory-only" paragraph) as-is — it remains accurate. Update the M4 Acceptance-signal bullet (line 228-230) to note it is now confirmed true (matching the "M3: ... All three waves complete..." bullet's past-tense-confirmed phrasing style used for shipped milestones in the same list) rather than leaving it phrased as a future check.

**Do NOT touch:** M1, M2, M3, M5, "Follow-on (Bucket B)" section (the blocking-escalation decision is explicitly still open, out of scope, unaffected by this ticket), "Out of scope" section, "References" section.

**Verify:** Manual doc read-through; no automated test covers doc prose, but `make knowledge-index-update` (Finalize-phase step, not this step) must be run after this and Step 5/6 land since `docs/` files changed.

---

### Step 5 — Update `roadmap.md` item 2's row and the stale "unaffected and still open" prose

**Files:** `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md`

**Change:** Three distinct edits, confirmed live by direct read:
1. **Table row (line 29)**: `| 2 | Bash secret-exposure advisory hook | A — Committed | H0, start now | governance_capability_policy_epic.md (M4) |` → strike the item name and append **SHIPPED** with the ticket ID, mirroring the exact markup already used for items 5/7/10 in the same table (e.g. item 5's row: `~~Convert 2 proven-failing prose rules to hooks~~ **SHIPPED** — M2 (...) and M3 (...) both landed`).
2. **Prose (lines 100-101, confirmed live)**: `"The Bash secret-exposure advisory hook (item 2, M4) and the capability-envelope baseline (item 3, M2) are unaffected and still open."` — split this sentence: item 2 is no longer "still open" (it shipped), item 3 remains open and unaffected. Reword to keep item 3's claim intact while marking item 2 shipped with a forward reference to the new M4 SHIPPED paragraph (Step 4).
3. **Running count (line 90, confirmed live)**: `"...leaving 2 still Horizon-2-only — items 11–12 and 7 remaining to implement overall (1, 2, 3, 7, 9, plus item 1's remaining waves)."` — append a new dated status paragraph directly after this line, mirroring the exact "Item 10 — shipped (2026-09-06)" paragraph's structure and phrasing convention (bold `**Item 2 — shipped (2026-09-08)**:` lead-in), stating item 2 shipped via this ticket and recomputing the count to `6 remaining to implement overall (1, 3, 7, 9, plus item 1's remaining waves)`. Do not edit the line-90 sentence in place — the doc's own established convention (used for items 5 and 10) is to append a new dated paragraph superseding the count, not silently rewrite the original snapshot sentence.

**Do NOT touch:** line 281 (the Bucket-B follow-on reference to "item 2" in the M5/exit-gate section) — read it first; it already correctly frames item 2's *escalation decision* as a distinct future Bucket-B item, not a claim that item 2 itself is unshipped, so it needs no edit. Confirm this reading holds before leaving it untouched; if it turns out to read as contradicting the SHIPPED status, flag it rather than silently leaving it.

**Verify:** Manual doc read-through for internal consistency (table row, prose, and count all agree that item 2 is shipped).

---

### Step 6 — Update `subsystem_ownership_lifecycle.md`

**Files:** `docs/guidelines/subsystem_ownership_lifecycle.md`

**Change:** Read the live file: the "Excluded Subsystems" section (lines 40-52) lists "Bash secret-exposure advisory hook" (lines 45-47) with reasoning "excluded — subsystem is BLOCKED ... add a row when it ships and is unblocked." Remove that bullet entirely (leave the "AST import-boundary enforcement" bullet untouched — unrelated). Add a new row to the "Ownership & Lifecycle Table" (lines 30-38), modeled directly on the live `Test-scoper hang guard` row (line 36) as the closest same-batch, same-mechanism (new `.claude/settings.json` hook key) precedent — same 5-column shape (Subsystem | Accountable role | Update trigger | Staleness signal | Removal condition):
- **Subsystem**: `Bash secret-exposure advisory hook (PreToolUse hook, .claude/settings.json — governance_capability_policy_epic.md M4; shipped by TCK-20260904-BASH-SECRET-SCAN-HOOK)`
- **Accountable role**: `Workflow Runtime Maintainer` (matches the Test-scoper hang guard row's role — both are `.claude/settings.json` hook-key subsystems)
- **Update trigger**: `tools/write_path_guard.py::scan_for_secrets()`'s signature or `_SECRET_SCAN_PATTERNS` set changes, or the harness's `PreToolUse` payload shape changes
- **Staleness signal**: `A synthetic secret-shaped command stops producing additionalContext in test_bash_secret_scan_hook.py despite the hook still being wired, or a real false-positive/false-negative pattern is observed in normal operation`
- **Removal condition**: `The Bucket-B blocking-escalation decision (roadmap.md item 17) supersedes this advisory-only hook with a blocking one, or the hook is folded into a broader command-risk policy; migration ticket recorded here`

**Do NOT touch:** the "Accountable Role Vocabulary" section, any other row in the Ownership & Lifecycle Table, the "AST import-boundary enforcement" Excluded Subsystems bullet, the "Related Docs" section.

**Verify:** Manual doc read-through; table row count increases by 1 (from 6 to 7), Excluded Subsystems section shrinks to 1 bullet.

---

### Step 7 — Add `INFRA-413` parity ledger entry

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Confirmed live (`grep -oE 'INFRA-[0-9]+' docs/parity_ledger/infrastructure.yaml | sort -t- -k2 -n | tail -5` → highest existing is `INFRA-412`), so `INFRA-413` is the next available ID as of this Plan phase — **re-verify this is still true immediately before running Step 7 at Implement time** (another ticket could land an `INFRA-413` first; re-run the same grep and increment if so, per this ticket's own instruction not to hardcode the investigation's placeholder without re-checking). Confirmed live (`tools/parity_ledger_writer.py:90-119`, `write_entry(shard_filename, entry, ledger_dir=None, db_path=None)`) that this module exposes a Python function, not a CLI with flags (`python3 tools/parity_ledger_writer.py --help` produces no output/no argparse) — invoke it via a short inline `python3 -c` call (or a throwaway one-off script) that imports `write_entry` from `tools.parity_ledger_writer` and calls it directly, e.g.:

```python
from tools.parity_ledger_writer import write_entry
write_entry("infrastructure.yaml", {
    "id": "INFRA-413",
    "text": "Bash secret-exposure advisory PreToolUse hook (TCK-20260904-BASH-SECRET-SCAN-HOOK): new .claude/settings.json PreToolUse[4] entry, matcher Bash, reuses tools/write_path_guard.py::scan_for_secrets() unmodified, advisory-only via hookSpecificOutput.additionalContext, never permissionDecision/deny.",
    "status": "verified",
    "priority": "P0",
    "v2_evidence": "tests/tools/test_bash_secret_scan_hook.py positive/negative-fire behavioral tests, executed via subprocess against the live .claude/settings.json command string",
    "test_path": "tests/tools/test_bash_secret_scan_hook.py",
})
```

Confirmed via `validate_entry()` (`tools/parity_ledger_writer.py:66-87`): `status: verified` requires non-empty `v2_evidence` and `test_path` (both provided above); `priority: P0` also requires non-empty `test_path` (provided); `status: verified` does **not** require `divergence_note` (only `status: divergent` does), so omit it. This mirrors the immediate `INFRA-405` precedent (same batch, same P0 priority, same "new `.claude/settings.json` hook key" category — confirmed live at `docs/parity_ledger/infrastructure.yaml:12083-12098`).

**Do NOT touch:** any other existing `INFRA-*` entry, `docs/parity_ledger/schema.json`, or edit the YAML file by hand — use the writer only (per the Anti-Drift Hazards' explicit instruction against raw/ad-hoc YAML edits on this 12,000+-line file).

**Verify:** `write_entry()`'s own return value (`{"status": "ok", ...}`); `tools/parity_index.py`'s in-process rebuild inside `write_entry()` completes without error; re-read the shard file afterward to confirm the new entry is present and every other entry is byte-identical to its pre-edit form (spot-check `INFRA-405` and `INFRA-412`).

## Scope Guards

Restated from the ticket's Out of Scope and the investigation's Anti-Drift Hazards — the implementer must not:

- Extract, refactor, or otherwise touch `scan_for_secrets()` or `_SECRET_SCAN_PATTERNS` in `tools/write_path_guard.py` in any way — including the module's own docstring, which currently says "*planned*" for this hook (now stale to "*live*"). **This staleness is a known, accepted gap and must NOT be fixed as part of this ticket** — AC #3 requires a diff proving the module is byte-identical before/after this ticket; fixing the docstring wording would violate that AC even though it is a one-line, low-risk change. Flag it in Completion Summary instead, or route it through a separate follow-up hotfix ticket if judged worth doing.
- Add any dangerous-command, command-injection, or network-exfiltration detection — out of scope per both the ticket and `governance_capability_policy_epic.md`'s M4 scope-boundary paragraph and top-level "Out of scope" list.
- Escalate to `permissionDecision`/`deny` under any circumstance — advisory-only is a hard requirement; the blocking-escalation decision is a separate, not-yet-scoped Bucket-B experiment (`roadmap.md` item 17).
- Edit the existing `PreToolUse[1]` (`Bash` grep-nudge) entry's command string when adding the new entry — add a new, separate array entry with the same `"Bash"` matcher; do not merge logic into the existing entry.
- Attempt to catch commands that merely *read* a secret (`cat ~/.aws/credentials`, `export $(cat .env)`) — named, accepted limitation in both the ticket and the epic doc, not a gap to close via broader heuristics.
- Edit `docs/parity_ledger/infrastructure.yaml` by hand/raw YAML edit — use `tools/parity_ledger_writer.py::write_entry()` only (12,000+-line file, high corruption risk from ad-hoc edits per project memory).
- **Touch `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`.** Investigation confirmed (its Docs Requiring Update section) this document's §1 Purpose is explicitly scoped to "the Knowledge Gateway MCP's future cached *payload* rows," and its §4 disclosure about `scan_for_secrets()`'s own baseline/non-production-complete caveat is unchanged by this ticket (the function is reused byte-for-byte, per AC #3). The one sentence that reads as potentially stale ("No secret-detection or credential-scanning module exists anywhere in this repository today") is historical framing for *why* §4 had to define a brand-new ruleset at authoring time (2026-08-14) and has been deliberately left untouched through multiple later addenda, including the 2026-09-07 extraction-archive pass that touched this document extensively elsewhere. This ticket adds a new *caller* to an already-extracted, gateway-independent module — that is out of this document's own stated scope; folding Bash-hook content into a Knowledge-Gateway-scoped contract doc would be scope creep. If a future doc audit wants that one sentence tightened, that is a separate, small, doc-only fix independent of this ticket.
- **Touch `docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md`.** Investigation confirmed its references to this ticket (lines 44, 58) are about the *knowledge-gateway removal item* (roadmap item 6), a separately-tracked item whose blocking chain was already resolved by `TCK-20260907-KGMCP-DEPRECATION-EPIC`/`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`, not by this ticket. This ticket's own Related Tickets section already correctly attributes that resolution elsewhere.
- Add or update anything under `docs/mechanics/` or `docs/guidelines/intentional_divergences.md` — investigation confirmed this ticket is agent-infrastructure/governance tooling, not simulation logic; the Mechanics Bible/Engine Contracts/Intentional Divergences framework does not apply here (no divergence from any Mechanics Bible chapter is introduced).

## Dependency Map

- Step 1 has no dependencies — it is the foundational change.
- Step 2 depends on Step 1 (the length assertion only needs updating once the 5th entry actually exists, but can technically be written first as a pre-registered expectation — implementer's choice on ordering, must land together).
- Step 3 depends on Step 1 (tests exercise the live command string Step 1 adds — cannot pass until Step 1 lands).
- Steps 4, 5, 6 (docs) depend on Steps 1-3 all passing — do not mark anything SHIPPED in docs before the hook is real and tested.
- Step 7 (parity ledger) depends on Step 3 (its `test_path` must point at a real, passing test file) — run Step 3's tests green before writing the ledger entry.
- Steps 4, 5, 6 are independent of each other and of Step 7 — any order among them is fine once Steps 1-3 are done.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — new `hooks.PreToolUse` entry, matcher `Bash`, emits valid `additionalContext` JSON on match, never `permissionDecision`/deny | Step 1 | `test_new_bash_secret_scan_hook_entry_registered`, `test_hook_never_emits_permission_decision_or_deny`, `python3 -m json.tool .claude/settings.json` |
| AC #2 — synthetic secret-shaped command produces non-empty `additionalContext` naming the pattern; ordinary command produces no output | Step 1 (implementation), Step 3 (tests) | `test_positive_fire_on_synthetic_secret_shaped_command`, `test_negative_no_fire_on_ordinary_commands` |
| AC #3 — hook calls `scan_for_secrets()` unmodified, verified by diff showing the module is unchanged | Step 1 (do-not-touch discipline), Scope Guards | `test_scan_for_secrets_module_unchanged_by_this_ticket`, full `tests/tools/test_write_path_guard.py` suite green |
| AC #4 — new test file asserts positive-fire and negative-no-fire via subprocess/thin wrapper | Step 3 | The new file itself: `pytest tests/tools/test_bash_secret_scan_hook.py -v` |

## Anti-Drift Notes

- The most likely accidental regression, per `test_plan.md`'s own Anti-Drift Test Guards section, is a future edit escalating this hook from advisory to blocking without the Bucket-B evidence-gated decision first — Test #4 (`test_hook_never_emits_permission_decision_or_deny`) exists specifically to catch this and must not be weakened or removed.
- Three same-batch tickets all touch `.claude/settings.json` (`TCK-20260904-TEST-SCOPER-HANG-GUARD`, `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE`, this one) — confirmed live that both siblings already landed cleanly before this ticket's Plan phase, so Step 1 is purely additive with no live merge conflict expected; Test #7 (`test_existing_bash_and_sidecar_hooks_untouched`) is the regression guard if that assumption ever breaks.
- `scan_for_secrets()`'s own docstring states its original caller "must REJECT the write outright — never redact-and-store." This ticket's caller is advisory-only, a deliberately weaker consequence policy for the same detection function — sanctioned explicitly by the epic doc's M4 section and this ticket's own Scope/Out-of-Scope, not a contradiction to resolve in code.
- Every hook in `.claude/settings.json` is wrapped `2>/dev/null || true` (fail-open by convention) — the new entry must follow this exactly; Test #5 (`test_hook_fails_open_on_malformed_or_missing_stdin`) is the regression guard.
- Do not run `pytest tests/` broadly — scope stays to `tests/tools/test_write_path_guard.py`, `tests/tools/test_bash_secret_scan_hook.py`, `tests/tools/test_settings_json_hooks_wiring.py`, `tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py`, plus `PYTHONPATH=tools:. pytest tests/agent_orchestration/test_contract_structure.py` per `test_plan.md`'s Scoped Pytest Commands section.
