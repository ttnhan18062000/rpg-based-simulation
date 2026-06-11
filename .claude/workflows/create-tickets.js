export const meta = {
  name: 'create-tickets',
  description: 'Parse a detailed markdown document into TCK-*.md ticket files ready for implement-epic',
  phases: [
    { title: 'Parse', detail: 'Read source doc, extract tasks and all ticket fields, detect duplicates' },
    { title: 'Write', detail: 'Create one TCK-*.md per task using ticket-scoper (parallel)' },
    { title: 'Link', detail: 'Update epic Related Tickets section if epic_id provided' },
  ],
}

// Args:
//   source    — path to the source markdown document (required)
//   structure — path to a ticket plan structure / template doc (optional)
//               Guides task granularity and scope conventions.
//   output    — output folder override (optional, e.g. "tickets/todos/phase29-repair/")
//               Inferred from source doc content if omitted.
//   epic_id   — existing epic ticket ID to link created tickets to (optional)

const source = (args && args.source) || ''
const structure = (args && args.structure) || ''
const outputOverride = (args && args.output) || ''
const epicId = (args && args.epic_id) || ''

if (!source) {
  return {
    status: 'INVALID_ARGS',
    message: 'Provide source=<path to markdown document>. Example: /create-tickets source=docs/plans/phase29.md',
  }
}

// ─── Phase 1: Parse ───────────────────────────────────────────────────────────
//
// One agent reads the source doc, scans ALL existing tickets for duplicates,
// and extracts a structured task list. No implementation — read only.

phase('Parse')

const TASK_SCHEMA = {
  type: 'object',
  required: ['short_scope', 'title', 'tier', 'type', 'priority', 'request_summary', 'scope', 'out_of_scope', 'acceptance_criteria', 'related_code_areas'],
  properties: {
    short_scope: {
      type: 'string',
      description: 'UPPER-KEBAB-CASE, max 4 words, unique in this batch. Used as TCK-YYYYMMDD-<short_scope>. Descriptive, not generic.',
    },
    title: { type: 'string' },
    tier: { type: 'string', enum: ['hotfix', 'standard', 'epic'] },
    type: { type: 'string', enum: ['bug', 'feature', 'refactor', 'chore', 'repair'] },
    priority: { type: 'string', enum: ['P0', 'P1', 'P2'] },
    request_summary: { type: 'string', description: 'One paragraph: what is being done and why' },
    scope: { type: 'array', items: { type: 'string' } },
    out_of_scope: { type: 'array', items: { type: 'string' } },
    acceptance_criteria: {
      type: 'array',
      items: { type: 'string' },
      description: 'Concrete and testable — no vague "works correctly" items',
    },
    related_code_areas: {
      type: 'array',
      items: { type: 'string' },
      description: 'Specific file paths (src/foo/bar.py) — not directories',
    },
    related_docs: { type: 'array', items: { type: 'string' } },
    related_tickets: { type: 'array', items: { type: 'string' } },
    assumptions: { type: 'array', items: { type: 'string' } },
  },
}

const PARSE_SCHEMA = {
  type: 'object',
  required: ['date', 'folder_name', 'tasks', 'skipped', 'summary'],
  properties: {
    date: { type: 'string', description: 'Today in YYYYMMDD format from `date +%Y%m%d`' },
    folder_name: {
      type: 'string',
      description: 'Short kebab-case name for the output folder under tickets/todos/, inferred from source doc topic',
    },
    tasks: { type: 'array', items: TASK_SCHEMA },
    skipped: {
      type: 'array',
      items: { type: 'string' },
      description: 'Items from source NOT converted to tickets. Format: "<description>: <reason>" (duplicate: <id>, too vague, already done)',
    },
    summary: { type: 'string', description: 'One sentence: N tasks extracted, M skipped (≤200 chars)' },
  },
}

const parsed = await agent(
  `Extract implementation tickets from a source document.

Step 1 — get today's date:
  Run: date +%Y%m%d
  This is the \`date\` field.

Step 2 — read the source document:
  Read: ${source}

${structure
  ? `Step 3 — read the structure/template guide for task granularity and scope conventions:
  Read: ${structure}`
  : `Step 3 — use CLAUDE.md's ticket format and standard project conventions as your guide.`}

Step 4 — find all existing tickets (complete duplicate detection):
  Run: find tickets/ -name "TCK-*.md" 2>/dev/null
  For any task from the source that is already covered by an existing ticket, add it to \`skipped\`
  with reason "duplicate: <ticket_id>".

Step 5 — extract tasks:

  Each task must be:
  - Self-contained: completable by one implementer without waiting on another task in this batch
  - Narrow: specific files/modules, not "the whole subsystem"
  - Testable: acceptance criteria are concrete and verifiable — no vague items
  - Correctly sized: standard for substantive work, hotfix only for trivially small fixes

  Split aggressively — one concern per ticket, no lumping.
  Map content faithfully from the source document — do not invent scope not in the doc.

  short_scope rules:
  - UPPER-KEBAB-CASE, max 4 words
  - MUST be unique across all tasks in this batch — verify before returning
  - Descriptive: "RESOLVER-UNION-TYPE" not "REPAIR-3"

  related_code_areas: specific file paths only (src/...), not directories
  related_docs: docs/mechanics/ chapters or docs/engine/ contracts relevant to this task

Step 6 — infer folder_name:
  Short kebab-case derived from the source document's topic.
  Examples: "phase29-repair", "content-resolver-fixes", "world-assembly-cleanup"
  ${outputOverride ? `User-specified path: "${outputOverride}" — extract the last path segment as folder_name.` : ''}

Return: date, folder_name, tasks[], skipped[], summary.`,
  { label: 'parse', schema: PARSE_SCHEMA }
)

log(`Parse: ${parsed.summary}`)
if (parsed.skipped.length > 0) {
  log(`Skipped ${parsed.skipped.length}: ${parsed.skipped.join(' | ')}`)
}

if (parsed.tasks.length === 0) {
  return {
    status: 'NOTHING_TO_CREATE',
    source,
    skipped: parsed.skipped,
    message: 'No actionable tasks found in the source document.',
  }
}

// Enforce short_scope uniqueness in code — parse agent may still produce dupes
// despite instructions. Drop silently with a warning rather than writing
// a second ticket that overwrites the first.
const seenScopes = new Set()
const dedupedTasks = []
const droppedScopes = []
for (const task of parsed.tasks) {
  if (seenScopes.has(task.short_scope)) {
    droppedScopes.push(task.short_scope)
  } else {
    seenScopes.add(task.short_scope)
    dedupedTasks.push(task)
  }
}
if (droppedScopes.length > 0) {
  log(`WARNING: duplicate short_scope from parse — dropped: ${droppedScopes.join(', ')}`)
}

const outputFolder = outputOverride
  ? (outputOverride.endsWith('/') ? outputOverride : outputOverride + '/')
  : `tickets/todos/${parsed.folder_name}/`

const dateStr = parsed.date

log(`Writing ${dedupedTasks.length} ticket(s) to ${outputFolder}`)

// ─── Phase 2: Write (ticket-scoper, parallel pipeline) ────────────────────────
//
// Uses the same agentType as implement-ticket's scope phase so both paths share
// the ticket-scoper's canonical format knowledge. The only difference from
// single-ticket creation: no investigation scan (parse phase did it), and the
// output path is tickets/todos/ instead of tickets/inprogress/.

phase('Write')

// Mirrors the shape of TICKET_SCHEMA in implement-ticket.
// Omits `status` (always CREATED here) and `conflicts` (handled at parse level).
const WRITE_SCHEMA = {
  type: 'object',
  required: ['ticket_id', 'ticket_path', 'tier', 'summary'],
  properties: {
    ticket_id: { type: 'string' },
    ticket_path: { type: 'string' },
    tier: { type: 'string', enum: ['hotfix', 'standard', 'epic'] },
    summary: { type: 'string', description: 'One sentence confirming what was written (≤200 chars)' },
    ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ`' },
  },
}

const written = await pipeline(
  dedupedTasks,
  (task) => {
    const ticketId = `TCK-${dateStr}-${task.short_scope}`
    const ticketPath = `${outputFolder}${ticketId}.md`

    return agent(
      `Create a ticket file from pre-analyzed task data.

IMPORTANT: This is a batch creation from a planning document — the parse phase has already
performed conflict checking and investigation. Do NOT scan tickets/, docs/, stored_artifacts/,
or source code. Your role here is ticket formatting and file creation only.

Ticket ID: ${ticketId}
Output path: ${ticketPath}

Task data (use this to fill in every section):
${JSON.stringify(task, null, 2)}

Steps:
1. Run: mkdir -p ${outputFolder}
2. Run: date -u +%Y-%m-%dT%H:%M:%SZ — save as TS (use as the \`ts\` field).
3. Write the ticket to ${ticketPath}. The file MUST begin with a YAML frontmatter block
   (before the # heading), then the markdown body with all sections in order.

   Frontmatter block (substitute actual values):
   ---
   status: active
   layer: <infer from task.related_code_areas and task.title — use LAYER_VALUES in tools/validate_frontmatter.py>
   authority: P1
   audience: agent
   ticket_id: ${ticketId}
   phase: open
   date: <YYYY-MM-DD from TS>
   tags: []
   ---

   Map task data to markdown sections:
   - Title           → task.title
   - Status          → OPEN
   - Tier            → task.tier
   - Type            → task.type
   - Priority        → task.priority
   - Request Summary → task.request_summary
   - Scope           → task.scope (one bullet per item)
   - Out of Scope    → task.out_of_scope (one bullet per item, or "None.")
   - Acceptance Criteria → task.acceptance_criteria (one "- [ ] item" per entry)
   - Related Tickets → task.related_tickets (one "- item" per line, or "None.")
   - Related Docs    → task.related_docs (one "- item" per line, or "None.")
   - Related Stored Artifacts → None.
   - Related Code Areas → task.related_code_areas (one "- item" per line)
   - Assumptions / Open Questions → task.assumptions (one "- item" per line, or "None.")
   - Implementation Notes, Test Summary, Files Changed, Completion Summary → (leave blank)

Return: ticket_id="${ticketId}", ticket_path="${ticketPath}", tier="${task.tier}",
summary (one sentence confirming the file was written, ≤200 chars), ts=TS.`,
      { label: `write:${task.short_scope}`, schema: WRITE_SCHEMA, agentType: 'ticket-scoper', phase: 'Write' }
    )
  }
)

const succeeded = written.filter(Boolean)
const ticketIds = succeeded.map(w => w.ticket_id)

log(`Written: ${succeeded.length}/${dedupedTasks.length} tickets`)
if (succeeded.length < dedupedTasks.length) {
  log(`WARNING: ${dedupedTasks.length - succeeded.length} write agent(s) returned null`)
}

// ─── Auto-generate SEQUENCE.md when intra-batch dependencies exist ────────────
//
// Pure JS: detect which tickets depend on other tickets in this same batch,
// topological-sort them, and write a SEQUENCE.md if any deps were found.
// No agent needed for the detection — only for the actual file write.

const batchIdSet = new Set(dedupedTasks.map(t => `TCK-${dateStr}-${t.short_scope}`))

// depMap[id] = Set of ids within this batch that id depends on
const depMap = new Map()
for (const task of dedupedTasks) {
  const ticketId = `TCK-${dateStr}-${task.short_scope}`
  const prereqs = new Set()
  for (const rt of (task.related_tickets || [])) {
    const m = rt.match(/TCK-\d{8}-[A-Z][A-Z0-9-]+/)
    if (m && batchIdSet.has(m[0]) && m[0] !== ticketId) {
      prereqs.add(m[0])
    }
  }
  depMap.set(ticketId, prereqs)
}

const hasIntraDeps = [...depMap.values()].some(s => s.size > 0)

if (hasIntraDeps) {
  // Kahn's topological sort — deterministic (alphabetical tie-breaking)
  const dependents = new Map([...batchIdSet].map(id => [id, new Set()]))
  for (const [id, prereqs] of depMap) {
    for (const prereq of prereqs) {
      if (dependents.has(prereq)) dependents.get(prereq).add(id)
    }
  }
  const inDegree = new Map([...batchIdSet].map(id => [id, depMap.get(id).size]))
  const queue = [...batchIdSet].filter(id => inDegree.get(id) === 0).sort()
  const sortedIds = []
  while (queue.length > 0) {
    const cur = queue.shift()
    sortedIds.push(cur)
    for (const dep of (dependents.get(cur) || [])) {
      const nd = (inDegree.get(dep) || 0) - 1
      inDegree.set(dep, nd)
      if (nd === 0) { queue.push(dep); queue.sort() }
    }
  }
  // Fall back to remaining IDs (cycle guard) in alphabetical order
  for (const id of [...batchIdSet].sort()) {
    if (!sortedIds.includes(id)) sortedIds.push(id)
  }

  const seqLines = sortedIds.map((id, i) => {
    const task = dedupedTasks.find(t => `TCK-${dateStr}-${t.short_scope}` === id)
    const prereqs = [...(depMap.get(id) || [])].join(', ')
    const note = prereqs ? `depends on: ${prereqs}` : 'no deps in this batch'
    return `${i + 1}. ${id}  (${note})`
  })

  const seqPath = `${outputFolder}SEQUENCE.md`
  const seqContent = [
    `# Implementation Sequence — ${parsed.folder_name}`,
    '',
    'Tickets must be implemented in this order. Generated automatically from intra-batch',
    'dependency analysis. `implement-epic` reads this file to override alphabetical order.',
    '',
    '## Order',
    '',
    ...seqLines,
    '',
    '## Why This Order Matters',
    '',
    'Running alphabetically would attempt tickets before their dependencies are in place.',
    'Re-run `/implement-epic` with the same folder after any gate failure — already-done',
    'tickets are skipped automatically.',
  ].join('\n')

  await agent(
    `Write the implementation sequence file for this batch.

Run: mkdir -p ${outputFolder}
Then write the following content to ${seqPath} exactly as shown (no additions):

\`\`\`
${seqContent}
\`\`\`

Confirm: DONE or ERROR.`,
    { label: 'write-sequence', phase: 'Write' }
  )

  log(`SEQUENCE.md written to ${seqPath} (${sortedIds.length} tickets in dependency order)`)
}

// ─── Phase 3: Link ────────────────────────────────────────────────────────────

if (epicId && ticketIds.length > 0) {
  phase('Link')

  await agent(
    `Append new ticket IDs to the ## Related Tickets section of epic ${epicId}.

Step 1 — find the epic ticket:
  Check in order:
    tickets/inprogress/${epicId}.md
    tickets/done/${epicId}.md
    find tickets/todos/ -name "${epicId}.md"

Step 2 — append to ## Related Tickets (do not remove or reorder existing entries):
${ticketIds.map(id => `- ${id}`).join('\n')}

Step 3 — report: DONE (file path updated) or SKIPPED (epic ticket not found).`,
    { label: 'link-epic', phase: 'Link' }
  )

  log(`Linked ${ticketIds.length} ticket(s) to epic ${epicId}`)
}

return {
  status: 'DONE',
  output_folder: outputFolder,
  ticket_count: succeeded.length,
  ticket_ids: ticketIds,
  skipped: parsed.skipped,
  scope_dupes_dropped: droppedScopes,
  epic_linked: !!epicId,
  message: succeeded.length > 0
    ? `Created ${succeeded.length} ticket(s) in ${outputFolder}.${epicId ? ` Linked to ${epicId}.` : ` Run /implement-epic folder=${outputFolder} to implement.`}`
    : 'No tickets written — check parse output and skipped list.',
}
