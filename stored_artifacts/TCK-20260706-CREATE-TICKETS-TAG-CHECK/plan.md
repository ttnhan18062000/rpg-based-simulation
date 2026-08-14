---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260706-CREATE-TICKETS-TAG-CHECK
artifact_type: plan
tags: [tagging, workflows, agent-monitoring]
---

# Plan — TCK-20260706-CREATE-TICKETS-TAG-CHECK

## Steps

1. Register `api-design`, `debugging`, `performance` via `tools/tag_registry.py add` (done — see
   investigation.md).

2. **`create-tickets.js`**: `pushEvent` signature gains a 6th `reasonCode` param (mirrors
   `implement-ticket.js`'s addition), included as `reason_code: reasonCode || null`.

3. Immediately after the `droppedScopes` block, before the `tasksWithSkills` log line, insert:
   ```js
   const allBatchTags = [...new Set(dedupedTasks.flatMap(t => t.tags || []))]
   const tagsArgs = allBatchTags.map(t => `"${t}"`).join(' ')
   const tagCheckOutput = tagsArgs ? await bash(
     `python3 -c "
   import sys, json
   sys.path.insert(0, 'tools')
   from tag_registry import check_tags_registered
   print('TAG_CHECK_JSON:' + json.dumps(check_tags_registered(sys.argv[1:])))
   " ${tagsArgs}`
   ) : 'TAG_CHECK_JSON:[]'
   let unregisteredBatchTags = []
   const tagCheckMarkerIndex = tagCheckOutput.indexOf('TAG_CHECK_JSON:')
   if (tagCheckMarkerIndex !== -1) {
     try { unregisteredBatchTags = JSON.parse(tagCheckOutput.slice(tagCheckMarkerIndex + 'TAG_CHECK_JSON:'.length).trim()) }
     catch (e) { unregisteredBatchTags = [] }
   }

   let tasksReadyToWrite = dedupedTasks
   const tasksWithUnregisteredTags = []
   if (unregisteredBatchTags.length > 0) {
     const unregisteredSet = new Set(unregisteredBatchTags)
     tasksReadyToWrite = []
     for (const task of dedupedTasks) {
       const badTags = (task.tags || []).filter(t => unregisteredSet.has(t))
       if (badTags.length > 0) {
         tasksWithUnregisteredTags.push({ short_scope: task.short_scope, tags: badTags })
       } else {
         tasksReadyToWrite.push(task)
       }
     }
     log(`WARNING: unregistered tag(s) — skipping write for: ${tasksWithUnregisteredTags.map(t => `${t.short_scope} (${t.tags.join(', ')})`).join(' | ')}`)
     log('Register each via `python3 tools/tag_registry.py add <tag> --category <cat> --note "..."`, then re-run to pick up the skipped concern(s).')
     pushEvent('Structure', 'create-tickets', 'blocked', `${tasksWithUnregisteredTags.length} task(s) skipped — unregistered tag(s)`, null, 'tag_registry_rejection')
   }
   ```

4. Replace every subsequent use of `dedupedTasks` for **writing/graphing** (not the earlier
   `tasksWithSkills` log, which can stay informational either way) with `tasksReadyToWrite`:
   `outputFolder`/`dateStr` computation stays as-is (batch-level, not per-task); `pipeline(dedupedTasks,
   ...)` at Write phase → `pipeline(tasksReadyToWrite, ...)`; the SEQUENCE.md `batchIdSet`/`depMap`
   construction's `dedupedTasks.map(...)`/`for (const task of dedupedTasks)` → `tasksReadyToWrite`.

5. Final return object: add `tags_not_registered: tasksWithUnregisteredTags` alongside the existing
   `scope_dupes_dropped` field.

6. **`tools/agent-monitoring/generate_retro.py`**: rename `"## DOD_BLOCKED Reason Codes"` →
   `"## Reason Codes"` and adjust the one-line guard comment above it accordingly. No aggregation
   logic changes (confirmed workflow-agnostic already).

7. **Docs**: `docs/ai/workflows.md`'s `create-tickets` Structure phase row/description;
   `docs/agent-monitoring/schema.md`'s `reason_code` section — generalize "two phases" framing and
   add `create-tickets`/`Structure` to the table's `Phase(s)` column for `tag_registry_rejection`.

## Verification

- `node --check .claude/workflows/create-tickets.js`
- `pytest tests/tools/ -q --ignore=tests/tools/test_knowledge_search.py` (no create-tickets.js-specific
  Python tests exist or are needed — this is JS orchestration, same disclosed limitation as the
  sibling ticket)
- Manual read-through confirming `tasksReadyToWrite` is used everywhere `dedupedTasks` previously
  was, for both Write and SEQUENCE.md generation — a missed replacement would silently reintroduce
  the bug this ticket fixes.
