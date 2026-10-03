---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-BASH-SECRET-SCAN-HOOK
artifact_type: investigation
tags: [governance, ai, hooks, security]
---

# Investigation — TCK-20260904-BASH-SECRET-SCAN-HOOK

## Current Behavior

**`.claude/settings.json` (`hooks.PreToolUse`, currently 4 entries):**
- `[0]` matcher `"*"` → `python3 tools/agent-monitoring/pre_tool_hook.py 2>/dev/null || true`
- `[1]` matcher `"Bash"` (**closest existing analog for this ticket**) → a `CMD=$(python3 -c
  "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',d).get('command',''))"
  2>/dev/null || true)` subshell, followed by a `case "$CMD" in *grep*|*rg\ *|...)` shell
  glob-match that emits a graphify-nudge `additionalContext` JSON string when the command looks
  like a raw search tool. This is the single closest prior-art shape: same event (`PreToolUse`),
  same matcher (`Bash`), same "extract `tool_input.command` from stdin JSON via a `python3 -c`
  one-liner, then decide whether to emit `hookSpecificOutput.additionalContext`" structure this
  ticket's own Scope explicitly names.
- `[2]` matcher `"Agent"` → context-search nudge, same shape, extracts `description`/`prompt`.
- `[3]` matcher `"Edit|Write"` → the sidecar reminder hook (`TCK-20260807-...`, later migrated to
  session-scoped sidecar reads by `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE`).

All four entries are wrapped in `2>/dev/null || true` — advisory/fail-open by convention. This is
also the required shape for the new hook: it must never abort or block the Bash call.

**`tools/write_path_guard.py::scan_for_secrets()` (line 149-166, confirmed by direct read):**
```python
def scan_for_secrets(text: str) -> str | None:
```
Confirmed exact signature matches the ticket's stated `scan_for_secrets(text: str) -> str | None`.
Iterates the 10-entry `_SECRET_SCAN_PATTERNS` dict (module lines 128-146: AWS key, generic
api-key assignment, PEM header, bearer token, GitHub token, Slack token, OpenAI key, Anthropic
key, generic password/secret assignment, basic-auth-in-URL) and returns the first matching
pattern's key, else `None`. Pure regex `.search()` calls only — no I/O, no mutation of any
argument or module state, no exceptions raised for ordinary text input. Confirmed safe to call
from a hook subprocess with zero side effects: it neither writes nor reads any file, network
resource, or environment variable.

Confirmed live and directly callable from a bare `python3 -c` one-liner with cwd = repo root and
**no `sys.path` bootstrapping needed** — `tools/` has no `tools/__init__.py` but Python 3's
implicit namespace-package resolution plus `python -c`'s own `sys.path[0] = ''` (→ cwd) makes
`from tools.write_path_guard import scan_for_secrets` resolve directly. Verified live in this
session:
```
$ echo '{"tool_input":{"command":"export API_KEY=\"abcdefghijklmnop1234\""}}' \
  | python3 -c "import json,sys
try:
    from tools.write_path_guard import scan_for_secrets
    d=json.load(sys.stdin)
    m=scan_for_secrets(d.get('tool_input',d).get('command',''))
    if m: print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','additionalContext':'secret-scan: possible '+m+' pattern detected in this Bash command. Advisory only, not blocked.'}}))
except Exception:
    pass" 2>/dev/null || true
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "secret-scan: possible generic_api_key_assignment pattern detected in this Bash command. Advisory only, not blocked."}}
```
and, for an ordinary command (`pytest tests/tools -q`), the same snippet produces **no stdout at
all** — matching the "never emits anything on a non-match" requirement. This is a validated,
working reference snippet, not a hypothesis — the implementer can adapt it directly into the
`.claude/settings.json` command string (adding the outer `2>/dev/null || true` and wiring it under
a new `PreToolUse` array entry, matcher `"Bash"`).

**`tools/write_path_guard.py`'s own module docstring (lines 1-35) already anticipates this exact
consumer**: "these functions have real, live consumers outside the gateway package
(`tools/retrieval_cache.py`'s own connection-opening helpers; **the planned
`governance_capability_policy_epic.md` M4 secret-exposure hook**)". This confirms the extraction
ticket (`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`) was already done with this hook in mind —
no further extraction/refactor is needed on the module side.

## Mechanics / Engine Constraints

Not applicable in the Mechanics-Bible/engine-contract sense — this is agent-infrastructure/
governance tooling (`.claude/settings.json` hooks, `tools/`), not simulation logic. The relevant
constraining documents are instead:
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §4 — the disclosure
  that `scan_for_secrets()`'s 10-pattern baseline is "a documented starting point, not a
  production-complete secret scanner," and that any match "must cause the write to be rejected
  outright... never silently redacted and stored" for its *original* (cache-write) caller. This
  ticket's caller is different (advisory-only, never a write/deny decision) — see Risks below for
  why that is a deliberate, ticket-scoped divergence in *consequence*, not in the scan itself.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`
  M4 (lines 149-180) — the authoritative spec for this exact hook: reuse `scan_for_secrets()`
  as-is, new `PreToolUse` hook matching `Bash`, same shell-wrapper pattern, advisory-only
  (`additionalContext`, never `deny`), explicit scope boundary (secret-shaped values only, not a
  dangerous-command or command-injection policy), and the named limitation (catches embedded
  literals, not commands that merely *read* a secret file). The ticket's own Scope/Out-of-Scope
  sections are a verbatim match to this spec — confirmed, no drift between ticket and epic doc.
- CLAUDE.md Hard Rules — "Never edit an artifact to make an automated gate/check pass instead of
  fixing the underlying substance" and the general hook-advisory-only convention already
  established by every existing `PreToolUse` entry in this repo.

## Docs Requiring Update

- `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`: M4's
  own section (currently headed "gated on the cross-epic extraction step") must be updated to
  reflect that both named prerequisites are resolved and M4 has shipped, mirroring how M3's section
  and the "Acceptance signal" bullet were marked SHIPPED by the sibling ticket
  `TCK-20260904-TEST-SCOPER-HANG-GUARD`.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md`: the inventory table's item 2
  row (line 29, "Bash secret-exposure advisory hook | A — Committed | H0, start now") and the prose
  at lines 100-101 ("The Bash secret-exposure advisory hook (item 2, M4)... are unaffected and
  still open") are both stale the moment this ticket ships and must be updated to SHIPPED, matching
  the pattern already used for items 5/7/10 elsewhere in this same file.
- `docs/guidelines/subsystem_ownership_lifecycle.md`: this subsystem is currently listed under
  "## Excluded Subsystems" (line 45-47) with the reasoning "excluded — subsystem is BLOCKED
  (`TCK-20260904-BASH-SECRET-SCAN-HOOK`), no code exists yet; **add a row when it ships and is
  unblocked**." That condition is now met — a real ownership/lifecycle table row (accountable role,
  update trigger, staleness signal, removal condition) must be added, and the "Excluded Subsystems"
  bullet removed, following the exact row shape already used for the sibling `TCK-20260904-TEST-SCOPER-HANG-GUARD`
  row (line 36) as the closest same-batch, same-mechanism (new `.claude/settings.json` hook key)
  precedent.
- `docs/parity_ledger/infrastructure.yaml`: no existing entry covers this hook (confirmed by grep —
  no `secret`/`Bash.*hook`/`BASH-SECRET-SCAN` hits). The immediate same-batch sibling
  `TCK-20260904-TEST-SCOPER-HANG-GUARD` (also a new `.claude/settings.json` hook key, same
  "agent-orchestration tooling" category) added `INFRA-405` for its own hook, at P0 priority
  matching its own ticket priority. This ticket is also P0-priority and adds a comparably new,
  behaviorally significant hook surface — for consistency with that immediate precedent, a new
  `INFRA-4xx` entry (next available ID at Parity-phase time; `INFRA-413` as of this investigation)
  should be added, `status: verified`, `priority: P0`, with a `test_path` pointing at the new test
  file (P0 entries require a passing `test_path` per CLAUDE.md's Authoritative Mechanics Rule).

The following was considered and is **not** required to change: `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`
(path: `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`). Its §1 Purpose
states explicitly that the document is "scoped specifically to the Knowledge Gateway MCP's future
cached *payload* rows" — its §4 disclosure documents `scan_for_secrets()`'s own baseline and
non-production-complete caveat, which is unchanged by this ticket (the function is reused
byte-for-byte, per AC #3). The sentence flagged as potentially stale ("No secret-detection or
credential-scanning module exists anywhere in this repository today") is, read in its own
paragraph, historical framing for *why* §4 had to define a brand-new ruleset rather than reuse an
existing one — it was already true-at-authoring-time (2026-08-14, before `scan_for_secrets()`
itself existed) and has been left as-is through several later "as of `<ticket>`" addenda to the
same document (including the 2026-09-07 extraction-archive pass, which touched this document
extensively and deliberately left this sentence untouched). This ticket adds a *new caller*
(a Bash `PreToolUse` hook) to an *already-existing* function in an *already-extracted*,
gateway-independent module — it does not touch §2-§11's redaction/retention substance, and the new
caller is already tracked in `tools/write_path_guard.py`'s own module docstring (see Current
Behavior above), which is the more scope-appropriate place for a "new consumer of this pure
function" note now that the module is gateway-independent. Folding Bash-hook-specific content into
a Knowledge-Gateway-scoped contract doc would be scope creep relative to that doc's own stated §1
Purpose. (Flagged for a human/doc-updater judgment call, not silently decided: if a future doc
audit disagrees and wants this document's §4 sentence tightened for literal present-tense accuracy,
that is a separate, small doc-only fix, independent of this ticket's own scope.)

`docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md` (path:
`docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md`) is also not
required to change: its references to this ticket (line 44, 58) are about the *knowledge-gateway
removal item* (item 6), a different, already-separately-tracked item whose own blocking chain was
already resolved and documented by `TCK-20260907-KGMCP-DEPRECATION-EPIC`/`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`
— not by this ticket, and this ticket's own Related Tickets section correctly attributes that
resolution to those two tickets, not itself.

## Parity Ledger Overlap

No existing `docs/parity_ledger/*.yaml` entry currently covers this hook (grep confirmed, see Docs
Requiring Update above). No P0 gameplay/mechanics entry is touched by this ticket — this is
agent-infrastructure tooling, not simulation logic, so the Mechanics-Bible-driven P0 test_path
requirement doesn't apply in the usual sense; the recommended new `INFRA-4xx` entry is added for
consistency with the immediate same-batch `INFRA-405` precedent, not because an existing P0 entry
requires it.

## Prior Work

- `TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP` (done) — the ticket's own cited
  prior-art. Added the `Edit|Write` sidecar-reminder `PreToolUse` hook using the exact same
  "`python3 -c` parses stdin JSON → shell `case`/decision → conditionally emit
  `hookSpecificOutput.additionalContext`" shape this ticket must follow. Confirmed still accurately
  reflected in `.claude/settings.json` today (now at array index 3, later migrated to
  session-scoped sidecar reads by `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE` — that migration
  only changed the `RUN_ID=$(...)` subshell body, not the overall hook shape).
- `TCK-20260904-TEST-SCOPER-HANG-GUARD` (done, same batch) — the closest and most current model for
  (a) how to add a new `.claude/settings.json` hooks-block entry without disturbing existing
  entries, (b) how to structurally test a settings.json-embedded hook
  (`tests/tools/test_settings_json_hooks_wiring.py` — static JSON-shape assertions; run at array
  index, matcher, command-substring checks), (c) how to add a matching `docs/parity_ledger/infrastructure.yaml`
  entry, and (d) how to update `governance_capability_policy_epic.md`/`roadmap.md`/
  `subsystem_ownership_lifecycle.md` for a milestone that ships. Its own Implementation Notes
  explicitly flagged `.claude/settings.json`'s hooks block as "a probable multi-ticket edit
  collision point with this batch's `TCK-20260904-BASH-SECRET-SCAN-HOOK`" and recorded that, at the
  time it edited the file, no collision had landed yet — confirmed still true: today's
  `.claude/settings.json` has `PreToolUse` (4 entries, unchanged), `PostToolUse`, and `SubagentStop`
  (from that ticket) — no `BASH-SECRET-SCAN-HOOK` entry exists yet. Coordination is purely additive
  (new `PreToolUse` array entry), no rebase conflict expected.
- `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE` (done, same batch) — the other recent editor of
  `.claude/settings.json` (the `Edit|Write` entry's `RUN_ID` subshell). Also produced
  `tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py`, the best model for
  **behaviorally executing** a settings.json-embedded command (via `subprocess.run(["bash", "-c",
  full_command], input=<json>, ...)` or a bare extracted `python3 -c` snippet) rather than only
  statically asserting its string shape — directly applicable to this ticket's positive-fire /
  negative-no-fire AC, which needs real execution, not just string presence.
- `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH` / `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`
  (done) — original authorship and later 4→10 pattern expansion of `_SECRET_SCAN_PATTERNS` /
  `scan_for_secrets()`. Confirms the function's patterns and non-production-complete disclosure are
  frozen, tested, and this ticket must not touch them (Out of Scope, confirmed correct).
- `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` (done) — the ticket that unblocked this one by
  extracting `scan_for_secrets()` into gateway-independent `tools/write_path_guard.py` and left an
  explicit forward-reference to this ticket's own hook in the module's docstring.

## Risks and Open Questions

- **Consequence-severity mismatch with the function's own documented contract (flagged, not
  resolved here).** `scan_for_secrets()`'s docstring states "Any non-None result means the caller
  must REJECT the write outright — never redact-and-store." This ticket's caller is not a write
  path at all — it is an advisory Bash-command scan that only ever emits `additionalContext`, never
  blocks. This is explicitly sanctioned by the epic doc (M4 ships advisory-only "until the
  blocking-escalation decision... measures a false-positive rate over real operation" — a separate,
  not-yet-scoped Bucket-B experiment) and by this ticket's own Scope/Out-of-Scope. Not a
  contradiction requiring a code change, but worth stating plainly: this is a second, weaker
  consequence policy for the same detection function, intentionally, not an oversight.
- **`tools/write_path_guard.py`'s own module docstring says "the *planned* `governance_capability_policy_epic.md`
  M4 secret-exposure hook"** — once this ticket ships, that wording becomes stale ("planned" →
  live). AC #3 requires the module to be verified unchanged by this ticket ("except for the
  extraction landing separately"), which forbids editing that docstring as part of this ticket. This
  is a real, small, accepted staleness the implementer should not silently "fix" by touching the
  module (that would violate AC #3) — flag it in Completion Summary rather than editing the file,
  or route a one-line docstring wording fix through a follow-up hotfix if it's judged worth doing.
- **Hook cost**: a second `Bash`-matcher `PreToolUse` entry means *every* Bash tool call now pays
  two Python-process-spawn costs (the existing grep-nudge hook plus this new one) instead of one.
  Acceptable given three of the four existing entries already run on every matching tool call
  (`"*"` fires on literally every tool call), but worth naming as a cumulative-overhead trend if a
  fifth/sixth hook is added later without ever consolidating.
- **False-positive risk on ordinary commands mentioning credential-adjacent words** (e.g. a commit
  message or grep pattern containing the literal word "password" without a `key=value` shape) — the
  epic doc's own "Named limitation, checked against the actual patterns" paragraph already verified
  this is low (all 10 patterns are format/prefix-specific, not bare keyword matches); no new
  evidence gathered here contradicts that.

## Anti-Drift Hazards

- Do not modify `_SECRET_SCAN_PATTERNS`, `scan_for_secrets()`, or any other function in
  `tools/write_path_guard.py` — explicitly Out of Scope (AC #3 requires a diff proving the module
  is unchanged by this ticket).
- Do not add any dangerous-command, command-injection, or network-exfiltration detection — the epic
  doc's own "Out of scope" section is explicit and repeated in two places (M4's own scope-boundary
  paragraph and the epic's top-level Out-of-scope list). Stick to secret-shaped-literal scanning
  only.
- Do not escalate to `permissionDecision`/`deny` under any circumstance — advisory-only is a hard
  requirement from both the ticket and the epic doc, and the blocking-escalation decision is
  explicitly a separate, not-yet-scoped follow-on item (roadmap.md item 17, Bucket B).
- Do not touch the existing `PreToolUse[1]` (`Bash` grep-nudge) entry's command string when adding
  the new entry — add a new, separate array entry with the same `"Bash"` matcher (proven valid by
  the existing repeated-`"*"`-matcher precedent in `PostToolUse`), do not merge logic into the
  existing entry.
- Do not attempt to catch commands that merely *read* a secret (`cat ~/.aws/credentials`,
  `export $(cat .env)`) — this is a named, accepted limitation in both the ticket and the epic doc,
  not a gap to silently try to close via broader heuristics.
- When adding the `docs/parity_ledger/infrastructure.yaml` entry, use the sanctioned
  `tools/parity_ledger_writer.py` writer, not a raw/ad-hoc YAML edit (per project memory on
  full-file YAML rewrite risk) — the file is large (12,000+ lines) and a manual edit risks
  corrupting unrelated entries.
