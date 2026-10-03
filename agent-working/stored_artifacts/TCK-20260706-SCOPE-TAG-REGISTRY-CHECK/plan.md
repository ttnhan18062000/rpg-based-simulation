---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260706-SCOPE-TAG-REGISTRY-CHECK
artifact_type: plan
tags: [tagging, workflows, agent-monitoring]
---

# Plan — TCK-20260706-SCOPE-TAG-REGISTRY-CHECK

## Steps

1. **`tools/tag_registry.py`**: add `check_tags_registered(tags, root=None) -> list[str]` near
   `is_tag_registered`. Returns `[t for t in tags if not is_tag_registered(t, registry)]` after one
   `load_registry(root)` call.

2. **`.claude/agents/ticket-scoper.md`**: extend the existing `tags:` line's guidance (currently
   "see docs/guidelines/tag_taxonomy.md — prefer its categories and canonical spellings...") with a
   clause pointing at `python3 tools/tag_registry.py list` to check what's already registered before
   picking a tag. Soft guidance only — the actual gate lives in the orchestrator, per the
   investigation's design correction.

3. **`.claude/workflows/implement-ticket.js`**: immediately after the `ticketInfo` agent call
   returns (before the existing `pushEvent('Scope', ...)` line), add:
   ```js
   const tagsArgs = (ticketInfo.tags || []).map(t => `"${t}"`).join(' ')
   const tagCheckOutput = tagsArgs ? await bash(
     `python3 -c "
   import sys, json
   sys.path.insert(0, 'tools')
   from tag_registry import check_tags_registered
   print('TAG_CHECK_JSON:' + json.dumps(check_tags_registered(sys.argv[1:])))
   " ${tagsArgs}`
   ) : 'TAG_CHECK_JSON:[]'
   let unregisteredTags = []
   const tagCheckMarkerIndex = tagCheckOutput.indexOf('TAG_CHECK_JSON:')
   if (tagCheckMarkerIndex !== -1) {
     try { unregisteredTags = JSON.parse(tagCheckOutput.slice(tagCheckMarkerIndex + 'TAG_CHECK_JSON:'.length).trim()) }
     catch (e) { unregisteredTags = [] }
   }
   ```
   (The `tagsArgs ? ... : 'TAG_CHECK_JSON:[]'` guard avoids an empty/malformed `python3 -c` call
   when a ticket somehow has zero tags — same defensive style as other conditional bash calls in
   this file.)

   Update the existing `pushEvent('Scope', ...)` call (currently line ~242) to compute a
   `reason_code`:
   ```js
   const scopeReasonCode = (ticketInfo.conflicts && ticketInfo.conflicts.length > 0)
     ? 'conflicts_detected'
     : (unregisteredTags.length > 0) ? 'tag_registry_rejection' : null
   pushEvent('Scope', 'ticket-scoper',
     (ticketInfo.conflicts && ticketInfo.conflicts.length > 0) || unregisteredTags.length > 0 ? 'failed' : 'ok',
     ticketInfo.summary || 'Scoped ticket ' + tid, ticketInfo.ts, null, scopeReasonCode)
   ```

   Add the new gate immediately after the existing `CONFLICTS_DETECTED` block:
   ```js
   if (unregisteredTags.length > 0) {
     log(`Unregistered tag(s): ${unregisteredTags.join(', ')}`)
     log('Register each via `python3 tools/tag_registry.py add <tag> --category <cat> --note "..."`, or edit the ticket to use an existing registered tag, then re-run with ticket_id="' + tid + '".')
     await writeMonitoring('TAGS_NOT_REGISTERED')
     return {
       status: 'TAGS_NOT_REGISTERED',
       ticket_id: tid,
       tier,
       unregistered_tags: unregisteredTags,
       message: 'Register each tag via `python3 tools/tag_registry.py add <tag> --category <cat> --note "..."`, or edit the ticket\'s tags to use an existing registered tag, then re-run with ticket_id="' + tid + '".',
     }
   }
   ```

4. **`docs/agent-monitoring/schema.md`**: add `TAGS_NOT_REGISTERED` to `final_status` values;
   update the `reason_code` section — now populated for `Scope`/`failed` (both
   `conflicts_detected` and `tag_registry_rejection`) in addition to `Verify`/`failed`.

5. **`docs/ai/workflows.md`**: `implement-ticket`'s phase table — Scope's Gate condition column
   gains ", or if any tag isn't in the registry"; Return Values table gains a `TAGS_NOT_REGISTERED`
   row.

6. **`docs/ai/ticket-lifecycle.md`**:
   - Mermaid diagram: `Scope` node gains a second gate edge, e.g.
     `Scope -- TAGS_NOT_REGISTERED --> ScopeTagFix[/"Register tag(s) or edit ticket, re-run"/]`.
   - Failure Recovery Reference table: +1 row for `TAGS_NOT_REGISTERED`.
   - Step-by-Step Detail's Scope section: one sentence noting the new check, alongside the existing
     conflicts-gate description.

7. **Tests**: `tests/tools/test_tag_registry.py` — `check_tags_registered`: all-registered → `[]`;
   mixed → returns only the unregistered subset; phase-N tags never flagged; empty input → `[]`.

## Verification

- `pytest tests/tools/test_tag_registry.py -v`
- `node --check .claude/workflows/implement-ticket.js`
- Manual bracket/content-parity check on the updated Mermaid diagram (same method as
  `TCK-20260706-DIAGRAM-COVERAGE`).
- Full `tests/tools/` regression.

## Out of scope reaffirmed

`create-tickets.js`, auto-registration, retrofitting `reason_code` elsewhere.
