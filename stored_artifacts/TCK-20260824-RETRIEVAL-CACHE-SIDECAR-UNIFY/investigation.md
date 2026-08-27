# Investigation — TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY

## Ticket text was written before its own dependency (TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION) landed

The ticket's own Scope/AC text says "mirroring post_tool_hook.py's exact preference order" and
describes that order as "scoped-then-unscoped-fallback." By the time this ticket started,
TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION had already landed and changed post_tool_hook.py's
real preference order to: scoped-file-if-exists, else write-a-null-sentinel-and-report-null (NOT
fall back to the unscoped file). The ticket's own Assumptions anticipated exactly this risk
("this ticket's unification target moves").

## Does retrieval_cache.py need the null-sentinel behavior too?

Checked the 7 existing `TestReadCurrentRunSidecar` tests (all write only to the effective
unscoped path, none create a scoped file) — AC #2 explicitly requires these to "continue to pass
... verbatim." Adopting post_tool_hook.py's exact new null-on-absence behavior would break all 7,
since none of them exercise a scoped file at all.

Two real, disclosed reasons NOT to adopt the null-sentinel behavior here, beyond the AC
constraint:
1. This function is called from CLI/library contexts (no hook payload's `session_id`) — adding a
   *write* side effect (the sentinel file) to a function named `read_current_run_sidecar()` would
   be a new responsibility this ticket's own Out of Scope explicitly excludes ("giving
   retrieval_cache.py its own pruning/lifecycle logic").
2. Unlike `tools.jsonl` (which had zero staleness signal until fixed), this function already
   carries `sidecar_stale` — a real, existing safeguard for the single worst failure mode
   (attribution to an already-closed ticket). Blind unscoped-fallback is materially less risky
   here than it was for `post_tool_hook.py`.

**Decision: retrieval_cache.py adopts the scoped-file PREFERENCE (mirrors post_tool_hook.py when
a scoped file exists) but keeps the unscoped-FALLBACK when none exists (does not adopt the
null-sentinel-write behavior).** Documented in `read_current_run_sidecar()`'s own docstring.

## Unexpected regression found

Adding `import os` (needed for `os.environ.get("CLAUDE_CODE_SESSION_ID")`) broke a real,
pre-existing static guard test:
`test_no_pragma_busy_timeout_chmod_or_os_import_introduced_by_level2_migration` — its name and
one clause ban importing `os` anywhere in the file at all, as a proxy for "no `os.chmod`-based
permission hacks introduced by the Level 2 migration work." The same test already has precise,
direct string checks for `"os.chmod"`/`"chmod"`/`"busy_timeout"`/`"PRAGMA ..."` — those remain the
real, substantive invariant and are unaffected by this ticket. The blanket `os`-import-ban clause
is a redundant, overly broad proxy for the same concern the direct checks already cover exactly.
Narrowed (not silently removed) — see plan.md for the exact reasoning recorded in the renamed
test itself, mirroring this repo's own established precedent for narrowing a stale-scope guard
test rather than routing around a real gate.
