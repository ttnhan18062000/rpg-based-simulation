---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260705-TAG-REGISTRY-QUERY
artifact_type: investigation
tags: [tagging, taxonomy, registry, investigator]
---

# Investigation — TCK-20260705-TAG-REGISTRY-QUERY

## Current Behavior

### Two independent, non-identical "prior work" query mechanisms exist today

**1. `.claude/workflows/create-tickets.js` Investigate phase** (`.claude/workflows/create-tickets.js:337-350`):

```python
import yaml
with open('docs/REGISTRY.yaml') as f:
    entries = yaml.safe_load(f)
layers = ${JSON.stringify(registryLayers)}
matches = [e for e in entries if e.get('layer') in layers]
docs    = [e for e in matches if e.get('type') == 'doc']
tickets = [e for e in matches if e.get('type') == 'ticket']
```

`registryLayers` is derived at `create-tickets.js:262-290` via `DOMAIN_TO_LAYERS`, a hardcoded
`concern.domain_area` → `layer[]` lookup table (e.g. `cognition: ['ai', 'strategy']`), with `'core'`
as the fallback when no domain key matches. This is the **only** place in agent-facing code that
filters `REGISTRY.yaml` by `layer`.

**2. `.claude/agents/investigator.md` "Finding Prior Work"** (lines 13-25): filters
`type: ticket` entries where `related_code_areas` **overlaps with the current ticket's Related Code
Areas**. It does **not** filter by `layer` at all today — despite the ticket's own Scope section
phrasing ("alongside `related_code_areas`/`layer`"), `layer` is not currently a dimension
`investigator.md` reads. `docs/ai/agents.md:54` and `docs/ai/README.md:51` both confirm this same
description: "filters `ticket` entries by `related_code_areas` overlap." So the ticket text's
premise that investigator.md already does layer-filtering is not accurate — only `create-tickets.js`
does.

This means "add tags as a second filter dimension" lands differently in the two files:
- `create-tickets.js`: tags become a **second** dimension alongside the existing `layer` dimension.
- `investigator.md`: tags become a **second** dimension alongside the existing `related_code_areas`
  dimension — there is no existing `layer` dimension to sit "alongside" there.

### Critical finding: the existing `layer` filter has never matched a single ticket entry

`tools/generate_registry.py`'s `collect_tickets()` (lines 239-304) builds each ticket entry as:

```python
entry = {
    "type": "ticket", "path": ..., "ticket_id": ..., "title": ..., "tier": ...,
    "ticket_type": ..., "date": ..., "related_code_areas": ..., "artifact_files": ..., "tags": ...,
}
```

There is **no `layer` key at all** on ticket entries — `layer` is only ever set on `doc` entries
(`collect_docs()`, line 223: `"layer": fm.get("layer", "")`). Every ticket's frontmatter *does*
carry a `layer` field (confirmed: every fixture in `tests/tools/test_generate_registry.py`'s ticket
builder sets `layer: engine`), but `collect_tickets()` never reads or emits it.

Verified empirically against the live 1272-entry `docs/REGISTRY.yaml`:
```
ticket entries total: 1019
ticket entries with a layer key at all: 0
```
Running the exact `create-tickets.js:338-350` snippet with `layers = ['ai', 'strategy']` (the
`cognition` mapping) returns `DOCS: 24, TICKETS: 0` — and this is true for **every** possible
`layers` list, because `e.get('layer')` is `None` for all 1019 ticket entries and `None` is never
`in` a list of layer-name strings.

**Consequence for this ticket's scope:** the create-tickets.js `layer`-only ticket search has been
silently dead code since the registry was introduced — it has never surfaced one ticket, regardless
of domain/layer. This directly affects AC4 ("no existing layer-only query behavior regresses") —
that guarantee is trivially satisfiable for tickets (there is no existing ticket-matching behavior to
preserve), but must still hold for **docs**, where `layer` filtering does work today (24 docs
matched for `['ai','strategy']` above). The tag-based union filter this ticket adds will be the
**first mechanism that has ever actually surfaced tickets** through this code path — raising the
stakes on getting the tag-derivation heuristic right, since it is not "one lens among two" for
tickets in practice, it is the only working lens.

### REGISTRY.yaml tag field coverage

Confirmed via live registry (1272 entries):
- `tags` key is present on **100%** of entries (`missing_key: 0`) — but **181/1272 (14.2%)** have an
  **empty list** (`tags: []`), all from pre-taxonomy content.
- 1091 entries have ≥1 tag; 1367 distinct tag strings total (consistent with
  `docs/guidelines/tag_taxonomy.md`'s cited "1273 distinct tags" corpus-review figure — the count
  has grown slightly since that doc was written).
- Tag-taxonomy Subsystem/Topic named examples (`combat, economy, cognition, faction, resource,
  social, content, world, engine, strategy`) all appear with real, non-trivial frequency in the live
  corpus: `combat=20, economy=20, cognition=28, faction=27, resource=33, social=23, content=24,
  world=41, engine=21, strategy=5`. `strategy` is the thinnest at 5 occurrences but is present.
- Worked example verification (ticket AC3, taxonomy doc's own `faction` example): 27 entries tagged
  `faction`, spanning ticket types `TCK-20260619-E53*` (faction/diplomacy epic family),
  `TCK-2026070[12]-SIMQ-*` (SimQ faction scorers), and one `architecture` doc. Since ticket entries
  carry no `layer` key (see above), the observable "layer" spread for these entries is effectively
  unknowable from the registry today — the taxonomy doc's claim that `faction` "spans the `ai`,
  `systems`, and `social` layers" is asserted from ticket *content*, not verifiable via
  `REGISTRY.yaml`'s own `layer` field for tickets. Tag-based lookup is the only registry-native way
  to actually gather this set in one query.

## Mechanics / Engine Constraints

None. This ticket touches agent-tooling meta-files (`.claude/workflows/create-tickets.js`,
`.claude/agents/investigator.md`) and documentation only — no `src/` simulation code, no Mechanics
Bible chapter, no Engine Contract governs this behavior. `graphify query` (run per the mandatory
context-scan rule) returned only unrelated `src/` community-0/1/8 nodes (entity/world-assembly
graph) — confirming this ticket has no code-graph footprint, consistent with it being pure
agent-tooling/process work.

## Parity Ledger Overlap

None. Checked all 8 `docs/parity_ledger/*.yaml` files by content grep for `tag`/`registry`/
`investigat` — zero hits. This is process/tooling work, not simulation-law behavior; no parity
ledger entry applies and none should be added.

## Prior Work

- **TCK-20260704-TAG-TAXONOMY** (done): defined the 4-category taxonomy in
  `docs/guidelines/tag_taxonomy.md` and confirmed (per its own investigation, cited in this ticket's
  Request Summary) that "tags never queried" was the baseline gap — this ticket is its direct
  follow-on for the Subsystem/Topic category specifically.
- **TCK-20260705-TAG-SKILL-SUGGEST** (done, `stored_artifacts/TCK-20260705-TAG-SKILL-SUGGEST/`):
  sibling ticket, consumed the *Process/Skill-signal* category instead. It touched
  `create-tickets.js`'s **Structure phase** (`TASK_SCHEMA` at lines 441-460, the `tags`/
  `suggested_skills` prompt rules at ~583-597, and the frontmatter-template line at ~712) — a
  disjoint region of the same file from this ticket's target (**Investigate phase**, lines
  262-350). Confirmed via `git show 16dd0241 -- .claude/workflows/create-tickets.js`: zero line
  overlap between the two tickets' diffs. That commit's message explicitly calls out the scope
  boundary: "broader Subsystem/Topic tagging is deferred to the sibling ticket
  TCK-20260705-TAG-REGISTRY-QUERY (a scope boundary architecture review required tightening in the
  plan before approval)" — i.e., the architecture-reviewer already enforced this exact split once;
  this ticket should not re-open the Structure-phase `TASK_SCHEMA.tags` field, which already exists
  and is populated (with Process/Skill-signal tags only) by that prior ticket.
- No prior ticket in `docs/REGISTRY.yaml` (checked via the registry's own `related_code_areas` field
  for tickets referencing `create-tickets.js` or `investigator.md`) touches the Investigate-phase
  `layer` query itself — this is a genuinely new code path change.

## Risks and Open Questions

1. **Candidate-tag derivation approach (the ticket's own flagged open question — recommendation
   below).** Two options exist:
   - (a) Curate a small fixed seed list.
   - (b) Derive the vocabulary from `docs/REGISTRY.yaml`'s own historical `tags` field via frequency
     analysis.
   **Recommendation: neither in isolation — use `docs/guidelines/tag_taxonomy.md`'s own named
   Subsystem/Topic examples as the seed vocabulary** (`combat, economy, cognition, faction,
   resource, social, content, world, engine, strategy`), matched via simple case-insensitive
   substring/keyword presence against the concern's `title + description + domain_area` (for
   `create-tickets.js`) or the ticket's own title/description (for `investigator.md`). Reasoning:
   - This is not "inventing a new curated list" — it reuses a list the taxonomy doc *already*
     maintains as its authoritative illustration of the category, so there is exactly one place to
     extend the vocabulary later (the doc itself), not two.
   - Cross-checked against the live corpus: all 10 seed words appear with real, non-trivial
     frequency (5-41 occurrences each) — they are not hypothetical, they are already load-bearing
     tags in the corpus today.
   - Pure frequency-mining of `REGISTRY.yaml`'s 1367 distinct tags (option b) pulls in noise that
     does NOT belong in Subsystem/Topic: `audit`(53), `hardening`(51) are Quality-attribute;
     `phase-5`(32) and 35 other `phase-N` variants are Phase/Milestone; `observability`(58),
     `performance`(25) are Process/Skill-signal-adjacent; `documentation`(40), `epic`(36), `lab`(21),
     `test`(23), `contract`(30) are uncategorized one-offs. A naive top-N-by-frequency scan would
     silently mix categories — exactly the anti-pattern `tag_taxonomy.md`'s Disambiguation Rule
     exists to prevent. Frequency-scanning could still be a *secondary, opt-in* expansion mechanism
     later, but should not be this ticket's primary derivation method.
   - This keeps candidate-tag derivation genuinely cheap (`any(seed in text.lower() for seed in
     SEED_TAGS)`), matching the ticket's explicit "no NLP layer" constraint, and keeps the
     `mcp__knowledge-search__search_docs` / this-cheap-tag-lens division of labor clean (per Out of
     Scope).

2. **The pre-existing `layer`-key-missing-from-tickets bug (see Current Behavior) is adjacent but
   distinct scope.** `tools/generate_registry.py` is listed in this ticket's Related Code Areas as
   **read-only**, so fixing `collect_tickets()` to also emit `layer` is explicitly out of this
   ticket's implementation surface. Flagging for Plan: even after this ticket ships, ticket-side
   `layer` matching in `create-tickets.js` will remain permanently broken (0 matches, always) unless
   a separate follow-on ticket adds `layer` to `collect_tickets()`'s entry dict and regenerates
   `docs/REGISTRY.yaml`. This ticket's tag-based union filter is therefore not a nice-to-have second
   lens for tickets — it is the *only* lens that will ever produce ticket results from this code path
   until that separate gap is fixed. Plan should decide whether to (a) proceed as scoped and note the
   dependency, or (b) flag the `generate_registry.py` gap as a blocking prerequisite tickiet. Given
   `tags` is reliably present (100% key-coverage, only 14.2% empty-list) and the union semantics
   specified in Scope ("union the two result sets rather than requiring both to match") already
   tolerates one side being permanently empty for tickets, (a) is recommended — this is not a
   blocker, just a fact that should be stated plainly in the ticket's Implementation Notes so it
   isn't rediscovered as a "bug" during Test or Review.

3. **181 entries (14.2%) have `tags: []`.** These will never match tag-based candidates and can only
   surface via `layer` (docs) or `related_code_areas` (investigator.md's existing ticket path) or the
   AC4-preserved layer-only path for docs. This is expected and consistent with Out-of-Scope's
   explicit rejection of historical re-tagging — not a gap to fix here, just worth stating in
   Implementation Notes so it isn't mistaken for incomplete tag coverage later.

4. **`related_code_areas` overlap semantics in `investigator.md` are themselves loosely specified**
   ("Filter entries where ... `related_code_areas` overlaps ...") — exact-string match vs. path-
   prefix/substring match is not defined anywhere in the current file. Out of scope to fix here (not
   named in this ticket's Scope), but Plan should not conflate tightening that ambiguity with this
   ticket's tag-filter addition — keep the two changes textually separate in the edited section so a
   future ticket touching `related_code_areas` matching semantics has a clean diff.

5. **`docs/guides/README.md` addition (per ticket's Related Docs "consider whether" language):**
   confirmed no existing guide documents "how ticket investigation finds prior work" in detail today
   — `docs/guides/ticket_tagging.md` (added by the sibling ticket) documents tag *categories* and the
   skill-suggestion consumption, not the registry-query consumption this ticket adds. A one- or
   two-line addition to `ticket_tagging.md` itself (not a new guide, not `README.md`) describing "tags
   are also used as a registry search filter, see `investigator.md`/`create-tickets.js`" would be the
   lowest-friction fit, since that file already owns "what tags are used for" — but this is a Plan-
   phase call, not decided here.

## Anti-Drift Hazards

- **Do not touch `create-tickets.js`'s Structure-phase `TASK_SCHEMA` or its `tags`/`suggested_skills`
  prompt block (lines ~441-460, ~583-597, ~712)** — that is TCK-20260705-TAG-SKILL-SUGGEST's
  delivered surface, already reviewed and merged. This ticket's edit surface is the Investigate phase
  only (~lines 262-350: `DOMAIN_TO_LAYERS` and the embedded Python query string).
- **Do not "fix" the missing `layer` key in `tools/generate_registry.py`** as a drive-by — it's
  listed read-only in this ticket's Related Code Areas, the fix has its own blast radius (touches doc
  AND ticket entry shape, `tests/tools/test_generate_registry.py`, requires a full `make
  docs-registry` regen), and conflating it here would blow past this ticket's Out-of-Scope boundary
  ("no full faceted search tool").
- **Do not derive candidate tags via the `mcp__knowledge-search__search_docs` semantic tool** or any
  embedding-based similarity — Out of Scope explicitly reserves that tool for fuzzy search; this
  ticket's tag lens must be a cheap, deterministic, exact/substring keyword match only.
- **Do not expand the Process/Skill-signal or Phase/Milestone or Quality-attribute categories into
  this ticket's candidate-tag seed list** — scope is Subsystem/Topic only (per Scope and AC3's
  `faction` example). Mixing categories here would reproduce the exact "1273 distinct, uncategorized
  tags" problem `TCK-20260704-TAG-TAXONOMY` was created to fix.
- **`related_code_areas` in `docs/REGISTRY.yaml` ticket entries is a list of raw strings extracted
  from backtick-quoted tokens in the ticket body** (`parse_related_code_areas`,
  `tools/generate_registry.py:62-72) — not always real file paths (e.g. one live entry has
  `related_code_areas: ['tid', 'batchRunId']`, clearly non-path tokens from a differently-styled
  ticket body). Any new logic that assumes `related_code_areas` entries are always valid paths will
  break silently on entries like this — not this ticket's bug to fix, but worth knowing if the
  tag-filter implementation cross-references `related_code_areas` for anything.
