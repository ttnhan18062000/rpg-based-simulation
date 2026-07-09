export const meta = {
  name: 'create-tickets',
  description: 'Parse a natural-language proposal into investigation-backed TCK-*.md ticket files ready for /implement-epic',
  phases: [
    { title: 'Comprehend', detail: 'Read proposal as-is, extract discrete concerns in natural language — no structure enforcement' },
    { title: 'Investigate', detail: 'Per-concern: grep codebase, check Mechanics Bible, scan existing tickets, derive file paths and AC signals (parallel)' },
    { title: 'Structure', detail: 'Synthesize all investigation findings into properly-formed ticket fields with real file paths and concrete ACs' },
    { title: 'Write', detail: 'Create one TCK-*.md per ticket using ticket-scoper (parallel)' },
    { title: 'Link', detail: 'Update epic Related Tickets section if epic_id provided' },
  ],
}

// Args:
//   source    — path to the source markdown document (required)
//   structure — path to a ticket plan structure / template doc (optional)
//               Guides concern granularity and scope conventions.
//   output    — output folder override (optional, e.g. "tickets/todos/phase29-repair/")
//               Inferred from proposal content if omitted.
//   epic_id   — existing epic ticket ID to link created tickets to (optional)

const source = (args && args.source) || ''
const structureDoc = (args && args.structure) || ''
const outputOverride = (args && args.output) || ''
const epicId = (args && args.epic_id) || ''

if (!source) {
  return {
    status: 'INVALID_ARGS',
    message: 'Provide source=<path to markdown document>. Example: /create-tickets source=docs/plans/proposal.md',
  }
}

// ─── Phase 1: Comprehend ──────────────────────────────────────────────────────
//
// Read the proposal as natural language. Extract discrete concerns without
// enforcing ticket schema. The author may be a dev, BA, or tester writing
// in domain language, not code language. No codebase investigation yet.

phase('Comprehend')

const CONCERN_SCHEMA = {
  type: 'object',
  required: ['id', 'title', 'description', 'domain_area', 'type_hint', 'priority_hint', 'raw_excerpts'],
  properties: {
    id: {
      type: 'string',
      description: 'Local reference ID: C1, C2, C3 ... Used to correlate with investigation results.',
    },
    title: {
      type: 'string',
      description: 'Short natural-language title capturing the concern — in the author\'s terms, not code terms',
    },
    description: {
      type: 'string',
      description: 'What the author wants — in their words and intent. Include why if stated. Do not rewrite into ticket language.',
    },
    domain_area: {
      type: 'string',
      description: 'Rough system area: combat, economy, world, cognition, simulation, infrastructure, testing, etc.',
    },
    type_hint: {
      type: 'string',
      enum: ['bug', 'feature', 'refactor', 'chore', 'repair'],
      description: 'Best guess from the author\'s framing — investigation may revise',
    },
    priority_hint: {
      type: 'string',
      enum: ['P0', 'P1', 'P2'],
      description: 'Inferred from urgency language in the proposal. Default P1 if unclear.',
    },
    raw_excerpts: {
      type: 'array',
      items: { type: 'string' },
      description: '1-3 direct quotes or close paraphrases from the proposal that support this concern',
    },
  },
}

const COMPREHEND_SCHEMA = {
  type: 'object',
  required: ['concerns', 'summary'],
  properties: {
    concerns: { type: 'array', items: CONCERN_SCHEMA },
    summary: {
      type: 'string',
      description: 'One sentence: N concerns extracted from the proposal (≤200 chars)',
    },
    ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ`, captured first' },
  },
}

// ─── Agent Monitoring Setup ────────────────────────────────────────────────────
// Hard rule: mandatory for every run (including hotfix). Failure is non-fatal.
// No single ticket_id exists yet (this workflow creates N tickets), so run_id
// is derived from the source doc path — mirrors implement-epic's FOLDER-{path}.

const sourceSlug = source.replace(/\.[^/.]+$/, '').replace(/[^A-Za-z0-9]+/g, '-').toUpperCase().replace(/^-+|-+$/g, '')
const runId = `CREATE-TICKETS-${sourceSlug}`

const events = []
// reasonCode (TCK-20260706-CREATE-TICKETS-TAG-CHECK, reusing the reason_code field from
// TCK-20260706-MONITORING-REASON-CODE): optional, null by default. Populated on the Structure
// phase's 'blocked' event when tasks are skipped for having an unregistered tag.
const pushEvent = (phaseLabel, agentName, status, summary, ts, reasonCode) => {
  events.push({
    seq: events.length + 1,
    phase: phaseLabel,
    agent: agentName,
    status,
    summary: (summary || '').toString().slice(0, 200),
    ts: ts || null,
    reason_code: reasonCode || null,
  })
}

let startTs = null

const writeMonitoring = async (finalStatus) => {
  const eventsJson = JSON.stringify(events)
  const eventsCount = events.length
  const startTsLiteral = startTs ? startTs : '<END_TS>'
  const result = await agent(
    `Write agent monitoring records for run "${runId}". This is bookkeeping — do NOT fail if writes error.

Step 1 — get current timestamp (run end time):
  Run via Bash: date -u +%Y-%m-%dT%H:%M:%SZ
  Save result as END_TS. Replace every literal <END_TS> in the commands below with this value.

Step 2 — build and write events:
  Input events: ${eventsJson}
  For each event: add "run_id": "${runId}". If "ts" is null or missing, set "ts" to END_TS.
  Run: python3 tools/agent-monitoring/record_events.py --data '<final JSON array>'

Step 3 — write run record (replace <END_TS> with the value from Step 1):
  Run: python3 tools/agent-monitoring/record_run.py --data '{"run_id":"${runId}","start_ts":"${startTsLiteral}","end_ts":"<END_TS>","workflow":"create-tickets","tier":"n/a","final_status":"${finalStatus}","agent_count":${eventsCount}}'

If any command fails, print "WARNING: monitoring write failed: <error>" and continue — do NOT raise.
Return "monitoring written" or "monitoring write failed: <reason>".`,
    { label: 'monitoring-write' }
  )
  if (!result) {
    log('WARNING: agent-monitoring write agent returned null (non-fatal)')
  }
}

const comprehension = await agent(
  `Read a proposal document and extract the discrete concerns the author is describing.

The proposal is written in natural language by a developer, BA, or tester. It may be:
- Flowing prose mixing multiple concerns in one section
- A list of observations without ticket-style structure
- Background, motivation, and requests mixed together
- Written in domain/business language, not code terms

Your job: understand what the author wants, NOT how to implement it. Leave investigation for the next phase.

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` and return it as "ts" — captured before any other work.

Step 1 — read the proposal:
  Read: ${source}

${structureDoc
  ? `Step 2 — read the structure guide for concern granularity conventions:
  Read: ${structureDoc}`
  : `Step 2 — apply this granularity rule: one concern = one coherent problem or goal that can be independently addressed without waiting on the others.`}

Step 3 — extract discrete concerns:

  Splitting rules:
  - Split on: different system areas, different change types (bug vs feature), different affected components
  - Do NOT split: the same goal described from multiple angles, background/motivation from the actual request
  - Do NOT invent concerns not in the document — map faithfully

  For each concern:
  - id: C1, C2, C3 ... (sequential, no gaps)
  - title: short natural-language title (the author's terms, not code variable names)
  - description: what the author wants in their terms, including why if they stated it
  - domain_area: rough system area (combat, economy, world, cognition, simulation, infrastructure, testing)
  - type_hint: bug/feature/refactor/chore/repair — best guess from the author's framing
  - priority_hint: P0/P1/P2 — infer from urgency language, default P1 if not stated
  - raw_excerpts: 1-3 quotes or paraphrases from the proposal supporting this concern

Return: concerns[], summary (one sentence: N concerns extracted), ts.`,
  { label: 'comprehend', schema: COMPREHEND_SCHEMA }
)

startTs = comprehension.ts || null

log(`Comprehend: ${comprehension.summary}`)
pushEvent('Comprehend', 'create-tickets', 'ok', comprehension.summary, startTs)

if (comprehension.concerns.length === 0) {
  pushEvent('Comprehend', 'create-tickets', 'skipped', 'No actionable concerns found in the proposal', startTs)
  await writeMonitoring('NOTHING_TO_CREATE')
  return {
    status: 'NOTHING_TO_CREATE',
    source,
    message: 'No actionable concerns found in the proposal.',
  }
}

// ─── Phase 2: Investigate ─────────────────────────────────────────────────────
//
// Per concern: grep the actual codebase, check Mechanics Bible / engine
// contracts, scan existing tickets, find real file paths and derive AC signals.
// Runs in parallel — one agent per concern.

phase('Investigate')

const INVESTIGATION_SCHEMA = {
  type: 'object',
  required: ['concern_id', 'files_found', 'constraints', 'existing_tests', 'related_tickets', 'ac_signals', 'risks', 'is_duplicate', 'tier_recommendation', 'summary'],
  properties: {
    concern_id: { type: 'string' },
    files_found: {
      type: 'array',
      items: { type: 'string' },
      description: 'Specific file paths (src/...) found by grep/find that are relevant to this concern. No directories, no guesses.',
    },
    constraints: {
      type: 'array',
      items: { type: 'string' },
      description: 'Mechanics Bible laws or Engine contract rules that apply. Format: "docs/mechanics/03_economic_laws.md: <rule summary>"',
    },
    existing_tests: {
      type: 'array',
      items: { type: 'string' },
      description: 'Existing test file paths + test function names that already cover or relate to this concern',
    },
    related_tickets: {
      type: 'array',
      items: { type: 'string' },
      description: 'Existing ticket IDs (TCK-...) that overlap with or relate to this concern',
    },
    ac_signals: {
      type: 'array',
      items: { type: 'string' },
      description: 'Concrete, testable acceptance criteria derived from the concern description + current code behavior + existing test patterns. Each must be independently verifiable.',
    },
    risks: {
      type: 'array',
      items: { type: 'string' },
      description: 'Constraints, risks, or open questions discovered during investigation',
    },
    is_duplicate: {
      type: 'boolean',
      description: 'True only if this concern is already FULLY covered by an existing ticket',
    },
    duplicate_of: {
      type: 'string',
      description: 'Ticket ID if is_duplicate is true, empty string otherwise',
    },
    tier_recommendation: {
      type: 'string',
      enum: ['hotfix', 'standard'],
      description: 'hotfix if the fix is in ≤1 file/function with no architecture change; standard otherwise',
    },
    summary: {
      type: 'string',
      description: 'One sentence: key finding from this investigation (≤200 chars)',
    },
  },
}

// domain_area → REGISTRY.yaml layer(s) mapping — used in Investigate prompt
const DOMAIN_TO_LAYERS = {
  combat:         ['combat', 'mechanics'],
  economy:        ['systems', 'mechanics'],
  resource:       ['systems', 'mechanics'],
  crafting:       ['systems', 'mechanics'],
  trade:          ['systems', 'mechanics'],
  cognition:      ['ai', 'strategy'],
  ai:             ['ai', 'strategy'],
  strategy:       ['ai', 'strategy'],
  world:          ['systems', 'engine'],
  ecology:        ['systems', 'engine'],
  region:         ['systems', 'engine'],
  simulation:     ['engine'],
  pipeline:       ['engine'],
  infrastructure: ['observability', 'performance'],
  observability:  ['observability'],
  performance:    ['performance'],
  testing:        ['testing'],
  entity:         ['core'],
  attributes:     ['core'],
  core:           ['core'],
  architecture:   ['architecture'],
}

const investigations = await pipeline(
  comprehension.concerns,
  (concern) => {
    const domainKey = Object.keys(DOMAIN_TO_LAYERS).find(k => concern.domain_area.toLowerCase().includes(k)) || 'core'
    const registryLayers = DOMAIN_TO_LAYERS[domainKey] || ['core']

    return agent(
      `Investigate concern "${concern.id}: ${concern.title}".

Concern (from proposal):
  Title: ${concern.title}
  Description: ${concern.description}
  Domain area: ${concern.domain_area}
  Type hint: ${concern.type_hint}
  Priority hint: ${concern.priority_hint}

Raw excerpts from proposal:
${concern.raw_excerpts.map(e => `  - ${e}`).join('\n')}

Registry layers to search: ${registryLayers.join(', ')}

Return: concern_id="${concern.id}", plus all other INVESTIGATION_SCHEMA fields per your system prompt's methodology.`,
      { agentType: 'concern-investigator', label: `investigate:${concern.id}`, schema: INVESTIGATION_SCHEMA }
    )
  }
)

const validInvestigations = investigations.filter(Boolean)
log(`Investigate: ${validInvestigations.length}/${comprehension.concerns.length} concerns investigated`)

for (const inv of validInvestigations) {
  pushEvent('Investigate', `investigate:${inv.concern_id}`, inv.is_duplicate ? 'skipped' : 'ok', inv.summary, null)
}
if (validInvestigations.length < comprehension.concerns.length) {
  pushEvent('Investigate', 'create-tickets', 'failed', `${comprehension.concerns.length - validInvestigations.length} investigation agent(s) returned null`, null)
}

const duplicates = validInvestigations.filter(i => i.is_duplicate)
if (duplicates.length > 0) {
  log(`Duplicates skipped: ${duplicates.map(d => `${d.concern_id} → ${d.duplicate_of}`).join(' | ')}`)
}

const activeInvestigations = validInvestigations.filter(i => !i.is_duplicate)

if (activeInvestigations.length === 0) {
  await writeMonitoring('NOTHING_TO_CREATE')
  return {
    status: 'NOTHING_TO_CREATE',
    source,
    duplicates_skipped: duplicates.map(d => `${d.concern_id}: ${d.duplicate_of}`),
    message: 'All concerns are already covered by existing tickets.',
  }
}

// ─── Phase 3: Structure ───────────────────────────────────────────────────────
//
// One synthesis agent takes all investigation results and produces properly-
// formed ticket fields. File paths and ACs come from investigation evidence —
// not from the source doc text. Also handles cross-concern merging/splitting
// and final deduplication across the full batch.

phase('Structure')

const TASK_SCHEMA = {
  type: 'object',
  required: ['short_scope', 'title', 'tier', 'type', 'priority', 'request_summary', 'scope', 'out_of_scope', 'acceptance_criteria', 'related_code_areas', 'tags', 'suggested_skills'],
  properties: {
    short_scope: {
      type: 'string',
      description: 'UPPER-KEBAB-CASE, max 4 words, unique across all tasks in this batch. Descriptive, not generic.',
    },
    title: { type: 'string' },
    tags: {
      type: 'array',
      items: { type: 'string' },
      description: 'Canonical-form tags (lowercase, hyphen-separated, never p0/p1/p2) limited to Process/Skill-signal detection for this ticket — see prompt rule below. Broader Subsystem/Topic/Phase/Quality-attribute tagging is deferred to TCK-20260705-TAG-REGISTRY-QUERY, not assigned here.',
    },
    suggested_skills: {
      type: 'array',
      items: { type: 'string' },
      description: 'Mapped skill(s) from the tag->skill table below; empty array if no tag matches.',
    },
    tier: { type: 'string', enum: ['hotfix', 'standard', 'epic'] },
    type: { type: 'string', enum: ['bug', 'feature', 'refactor', 'chore', 'repair'] },
    priority: { type: 'string', enum: ['P0', 'P1', 'P2'] },
    request_summary: {
      type: 'string',
      description: 'One paragraph: what is being done and why — preserve the proposal author\'s intent and language',
    },
    scope: { type: 'array', items: { type: 'string' } },
    out_of_scope: { type: 'array', items: { type: 'string' } },
    acceptance_criteria: {
      type: 'array',
      items: { type: 'string' },
      description: 'Concrete and testable — derived from investigation ac_signals. No vague or untestable items.',
    },
    related_code_areas: {
      type: 'array',
      items: { type: 'string' },
      description: 'Specific file paths from investigation files_found ONLY — no directories, no invented paths. Use "expected: src/..." prefix if files_found was empty.',
    },
    related_docs: { type: 'array', items: { type: 'string' } },
    related_tickets: { type: 'array', items: { type: 'string' } },
    assumptions: { type: 'array', items: { type: 'string' } },
    source_concern_ids: {
      type: 'array',
      items: { type: 'string' },
      description: 'Which concern IDs (C1, C2 ...) this ticket covers — for traceability',
    },
  },
}

const STRUCTURE_SCHEMA = {
  type: 'object',
  required: ['date', 'folder_name', 'tasks', 'skipped', 'summary'],
  properties: {
    date: { type: 'string', description: 'Today in YYYYMMDD format from `date +%Y%m%d`' },
    folder_name: {
      type: 'string',
      description: 'Short kebab-case name for the output folder under tickets/todos/, inferred from proposal topic',
    },
    tasks: { type: 'array', items: TASK_SCHEMA },
    skipped: {
      type: 'array',
      items: { type: 'string' },
      description: 'Concerns NOT converted. Format: "<concern_id> <title>: <reason>"',
    },
    summary: { type: 'string', description: 'One sentence: N tasks structured, M skipped (≤200 chars)' },
  },
}

const investigationBundle = activeInvestigations.map(inv => {
  const concern = comprehension.concerns.find(c => c.id === inv.concern_id)
  return { concern, investigation: inv }
})

const structured = await agent(
  `Synthesize investigation findings into properly-formed ticket fields.

You have ${activeInvestigations.length} investigated concern(s). Your job: produce implementation-ready ticket data
using ONLY evidence from the investigations. Do NOT re-investigate — all codebase reading is done.

Step 1 — get today's date:
  Run: date +%Y%m%d

Step 2 — review all concern + investigation pairs:
${investigationBundle.map(({ concern, investigation: inv }) => `
=== ${concern.id}: ${concern.title} ===
Author's description: ${concern.description}
Domain: ${concern.domain_area} | Type hint: ${concern.type_hint} | Priority hint: ${concern.priority_hint}

Investigation findings:
  Files found:      ${inv.files_found.join(', ') || '(none found by grep)'}
  Constraints:      ${inv.constraints.join(' | ') || 'none'}
  Existing tests:   ${inv.existing_tests.join(', ') || 'none'}
  Related tickets:  ${inv.related_tickets.join(', ') || 'none'}
  AC signals:       ${inv.ac_signals.join(' | ')}
  Risks:            ${inv.risks.join(' | ') || 'none'}
  Tier rec:         ${inv.tier_recommendation}
  Summary:          ${inv.summary}
`).join('\n')}

Step 3 — decide on merge/split:

  Merge rule: if two concerns share the same files_found AND address the same narrow code change → merge into one ticket.
  Split rule: if investigation reveals a concern actually spans unrelated subsystems (different files, no shared call path) → split into separate tickets.
  Default: one concern → one ticket.

Step 4 — produce ticket tasks using these strict rules:

  short_scope:
  - UPPER-KEBAB-CASE, max 4 words
  - MUST be unique across ALL tasks in this batch — verify before returning
  - Descriptive: "HARVEST-DELTA-CLAMP" not "REPAIR-1"

  related_code_areas:
  - Use ONLY file paths from investigation's files_found
  - If files_found is empty, prefix with "expected: " (e.g., "expected: src/economy/harvesting.py")
  - NEVER invent file paths without the "expected: " prefix

  acceptance_criteria:
  - Directly derived from investigation's ac_signals
  - Each item must be concrete and independently testable
  - Acceptable: "harvesting a non-empty node returns quantity > 0 and decrements node.quantity by that amount"
  - Not acceptable: "the system works correctly" / "handles edge cases"

  request_summary:
  - One paragraph preserving the ORIGINAL AUTHOR'S INTENT from concern.description
  - Do not rewrite into technical jargon — keep the author's framing
  - Add why it matters if stated (from constraints or risks)

  scope:
  - Specific and bounded — grounded in investigation findings
  - Each bullet names what concretely changes

  out_of_scope:
  - Guard against scope creep during implementation
  - List related things NOT addressed by this ticket

  related_docs:
  - Extract doc paths from investigation constraints (e.g., "docs/mechanics/03_economic_laws.md")

  assumptions:
  - From investigation risks that remain as open questions

  tags:
  - Canonical form only: lowercase, hyphen-separated. Never emit p0/p1/p2 as tags.
  - Include a Process/Skill-signal tag from this closed list ONLY when it applies: api-design, debugging, performance, security
  - Do NOT assign Subsystem/Topic, Phase/Milestone, or Quality-attribute tags (per docs/guidelines/tag_taxonomy.md's other 3 categories) — that broader tagging is explicitly out of scope for this workflow today (deferred to a separate ticket, TCK-20260705-TAG-REGISTRY-QUERY). If none of the 4 Process/Skill-signal tags apply, tags may be an empty array.

  suggested_skills:
  - Map each assigned tag against this table; empty array if nothing matches:
      api-design  -> /api-design-principles
      debugging   -> /debugging-strategies (or Agent(subagent_type: "world-debugger") if
                     related_code_areas includes a path under src/worldassembly/,
                     src/worldbuilding/, src/worldmodules/, src/content/, or
                     src/core/registries.py)
      performance -> /python-performance-optimization
      security    -> /security-review
  - Do not invent mappings for tags outside this 4-entry table

  tier:
  - Use investigation's tier_recommendation
  - Override to 'standard' if scope, out_of_scope, or AC count suggests more than a one-liner

  source_concern_ids:
  - Which concern IDs (C1, C2 ...) this ticket covers

Step 5 — infer folder_name:
  Short kebab-case from the proposal's topic.
  ${outputOverride ? `User override: "${outputOverride}" — extract the last path segment as folder_name.` : 'Infer from the concerns and domain areas.'}

Return: date (YYYYMMDD), folder_name, tasks[], skipped[], summary.`,
  { label: 'structure', schema: STRUCTURE_SCHEMA }
)

log(`Structure: ${structured.summary}`)
pushEvent('Structure', 'structure', structured.tasks.length > 0 ? 'ok' : 'skipped', structured.summary, null)
if (structured.skipped.length > 0) {
  log(`Skipped: ${structured.skipped.join(' | ')}`)
}

if (structured.tasks.length === 0) {
  await writeMonitoring('NOTHING_TO_CREATE')
  return {
    status: 'NOTHING_TO_CREATE',
    source,
    skipped: structured.skipped,
    message: 'No actionable tasks after investigation and structuring.',
  }
}

// Enforce short_scope uniqueness in code — structure agent may still produce
// duplicates despite instructions. Drop silently with a warning.
const seenScopes = new Set()
const dedupedTasks = []
const droppedScopes = []
for (const task of structured.tasks) {
  if (seenScopes.has(task.short_scope)) {
    droppedScopes.push(task.short_scope)
  } else {
    seenScopes.add(task.short_scope)
    dedupedTasks.push(task)
  }
}
if (droppedScopes.length > 0) {
  log(`WARNING: duplicate short_scope from structure — dropped: ${droppedScopes.join(', ')}`)
}

// Tag-registry check (TCK-20260706-CREATE-TICKETS-TAG-CHECK): orchestrator-run, same pattern as
// implement-ticket.js's Scope-phase check. Mirrors droppedScopes' defensive-skip precedent
// directly above — the structure agent may still produce an unregistered tag despite
// instructions restricting it to a closed 4-tag list; skip writing that task and continue the
// batch, rather than aborting all N tickets over one task's tag.
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

const tasksWithSkills = tasksReadyToWrite.filter(t => t.suggested_skills && t.suggested_skills.length > 0)
if (tasksWithSkills.length > 0) {
  log(`Suggested skills: ${tasksWithSkills.map(t => `${t.short_scope}: ${t.suggested_skills.join(', ')}`).join(' | ')}`)
}

const outputFolder = outputOverride
  ? (outputOverride.endsWith('/') ? outputOverride : outputOverride + '/')
  : `tickets/todos/${structured.folder_name}/`

const dateStr = structured.date

log(`Writing ${tasksReadyToWrite.length} ticket(s) to ${outputFolder}`)

// ─── Phase 4: Write (parallel) ────────────────────────────────────────────────
//
// Uses ticket-scoper agentType for canonical format knowledge.
// Investigation and structuring are done — write agents do formatting only.

phase('Write')

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
  tasksReadyToWrite,
  (task) => {
    const ticketId = `TCK-${dateStr}-${task.short_scope}`
    const ticketPath = `${outputFolder}${ticketId}.md`

    return agent(
      `Create a ticket file from pre-investigated task data.

IMPORTANT: Investigation and structuring are complete — do NOT scan tickets/, docs/, stored_artifacts/,
or source code. Your role is ticket formatting and file creation only.

Ticket ID: ${ticketId}
Output path: ${ticketPath}

Task data (use this to fill in every section):
${JSON.stringify(task, null, 2)}

Steps:
1. Run: mkdir -p ${outputFolder}
2. Run: date -u +%Y-%m-%dT%H:%M:%SZ — save as TS.
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
   tags: <substitute task.tags as a YAML flow-sequence, e.g. [tagging, skills]; use [] only if task.tags is empty>
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

log(`Written: ${succeeded.length}/${tasksReadyToWrite.length} tickets`)
for (const w of succeeded) {
  pushEvent('Write', 'ticket-scoper', 'ok', w.summary || `Wrote ${w.ticket_id}`, w.ts)
}
if (succeeded.length < tasksReadyToWrite.length) {
  log(`WARNING: ${tasksReadyToWrite.length - succeeded.length} write agent(s) returned null`)
  pushEvent('Write', 'ticket-scoper', 'failed', `${tasksReadyToWrite.length - succeeded.length} write agent(s) returned null`, null)
}

// ─── Auto-generate SEQUENCE.md when intra-batch dependencies exist ────────────
//
// Detect which tickets depend on other tickets in this same batch,
// topological-sort them, and write SEQUENCE.md if any deps were found.
// Uses tasksReadyToWrite, not dedupedTasks — a task skipped for an unregistered tag was never
// written, so it must not appear in the dependency graph either (TCK-20260706-CREATE-TICKETS-TAG-CHECK).

const batchIdSet = new Set(tasksReadyToWrite.map(t => `TCK-${dateStr}-${t.short_scope}`))

const depMap = new Map()
for (const task of tasksReadyToWrite) {
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
  for (const id of [...batchIdSet].sort()) {
    if (!sortedIds.includes(id)) sortedIds.push(id)
  }

  const seqLines = sortedIds.map((id, i) => {
    const prereqs = [...(depMap.get(id) || [])].join(', ')
    const note = prereqs ? `depends on: ${prereqs}` : 'no deps in this batch'
    return `${i + 1}. ${id}  (${note})`
  })

  const seqPath = `${outputFolder}SEQUENCE.md`
  const seqContent = [
    `# Implementation Sequence — ${structured.folder_name}`,
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

// ─── Phase 5: Link ────────────────────────────────────────────────────────────

if (epicId && ticketIds.length > 0) {
  phase('Link')

  const linkResult = await agent(
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

  const linkText = (linkResult || '').toString()
  pushEvent('Link', 'link-epic', linkText.includes('SKIPPED') ? 'skipped' : 'ok', linkText.slice(0, 200) || `Linked to ${epicId}`, null)
  log(`Linked ${ticketIds.length} ticket(s) to epic ${epicId}`)
}

await writeMonitoring('DONE')

return {
  status: 'DONE',
  output_folder: outputFolder,
  ticket_count: succeeded.length,
  ticket_ids: ticketIds,
  duplicates_skipped: duplicates.map(d => `${d.concern_id} → ${d.duplicate_of}`),
  skipped: structured.skipped,
  scope_dupes_dropped: droppedScopes,
  tags_not_registered: tasksWithUnregisteredTags,
  epic_linked: !!epicId,
  message: succeeded.length > 0
    ? `Created ${succeeded.length} ticket(s) in ${outputFolder}.${epicId ? ` Linked to ${epicId}.` : ` Run /implement-epic folder=${outputFolder} to implement.`}`
    : 'No tickets written — check comprehend, investigate, and structure output.',
}
