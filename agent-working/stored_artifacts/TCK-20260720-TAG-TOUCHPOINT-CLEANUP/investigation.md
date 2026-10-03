---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260720-TAG-TOUCHPOINT-CLEANUP
artifact_type: investigation
tags: [tagging, workflows]
---

# Investigation — TCK-20260720-TAG-TOUCHPOINT-CLEANUP

## Current Behavior

### 1. `done_checker_static.py`'s substring-matched tag rejection

`tools/gate_checks/done_checker_static.py::classify_checklist_failure()` (lines 310-339) scans
a `checklist: list[dict]` (each item `{"condition": str, "status": "PASS"|"FAIL"|"NA", "evidence":
str}`) for the first `FAIL` entry, then does:

```python
_TAG_REGISTRY_REJECTION_MARKER = "is not in the tag registry"   # line 307
if _TAG_REGISTRY_REJECTION_MARKER in item.get("evidence", ""):
    return "tag_registry_rejection"
return "dod_condition_failed"
```

The marker string is a substring of the exact message `validate_frontmatter.py::_check_tags()`
(lines 152-181) constructs at line 176-180:

```python
errors.append(
    f"{filepath}: tags: {tag!r} is not in the tag registry — register it first via "
    f"`python3 tools/tag_registry.py add {tag} --category <category> --note \"...\"`"
)
```

This message is produced deep inside `_check_tags()`, folded into `_validate_ticket()`/
`_validate_artifact()`'s `list[str]` return (lines 210, 224), further folded into
`validate_file()`'s `list[str]` return (line 281), further folded into
`done_checker_static.py::check_frontmatter_valid()`'s (lines 237-264) `"; ".join(all_errors)`
evidence string (line 263), which becomes the `evidence` field of the `frontmatter_valid`
checklist item `run_static_precheck()` (lines 284-300) emits. **Four layers of string-joining**
separate the actual violation (an unregistered tag) from the point where `classify_checklist_failure`
re-derives it — purely by re-matching a substring against the final flattened text.

**Important pre-existing gap, confirmed by direct read**: `check_frontmatter_valid()` (lines
237-264) calls `validate_file(ticket_path)` (line 248) and `validate_directory(staging_dir,
content_type_override="artifact")` (line 258) — **neither call passes a `registry` argument.**
`_check_tags()`'s registry-membership branch (line 175: `if registry is not None and not
is_tag_registered(tag, registry)`) is therefore **never exercised from this call site** — only
canonical-form violations (`canonical_form_violation`) are ever caught by the Verify-phase gate's
static `frontmatter_valid` condition today. Registry membership (the actual "hard allowlist" the
tag registry exists to enforce, per `tag_taxonomy.md`'s Enforcement section) is only checked when
`validate_frontmatter.py` is run directly as a CLI (`main()`, line 320, which does call
`load_registry()`) — confirmed via grep that `.claude/workflows/implement-ticket.js` never invokes
`validate_frontmatter.py` as a subprocess, and no CI workflow (`.github/workflows/*.yml`) invokes
it either. **In practice, an unregistered tag on a ticket/artifact is not currently rejected by the
automated Verify-phase gate at all** — only a human/agent manually running the CLI would catch it.
This means `_TAG_REGISTRY_REJECTION_MARKER`'s substring match in `classify_checklist_failure` is
almost certainly dead-in-practice on the static-precheck path (it can only ever fire if the
`done-checker` agent's own manual file-read judgment — not the static script — independently
decides a tag is unregistered and writes matching evidence text, since the prompt says "For all
others, read the actual files to verify" for the non-script-covered conditions, and separately
tells the agent to cite the static script's JSON "verbatim" for `frontmatter_valid` specifically —
which, per this gap, never contains the marker). This makes the recommended fix below not just a
refactor but a **real enforcement-gap fix**: the new design's `check_tags_registered()` call is the
first time the Verify-phase gate would actually enforce tag-registry membership.

**Real call site** (the only place `classify_checklist_failure`'s output is used at runtime):
`.claude/workflows/implement-ticket.js:1206`, `const reasonCode =
classifyChecklistFailure(doneCheck.checklist)` — but `doneCheck.checklist` is **not**
`run_static_precheck()`'s raw output. It is the `done-checker` agent's own structured JSON
return, constrained by `DONE_SCHEMA` (lines 1156-1167: each checklist item may carry only
`condition`, `status`, `evidence` — all strings). The prompt (lines 1190-1192) tells the agent to
"cite [the static pre-check script's] JSON output verbatim" for the 5 static-checkable conditions
(including `frontmatter_valid`), but this is agent-prose compliance, not a guaranteed pass-through
— the LLM re-serializes its own JSON conforming to the schema. **Any field not in `condition`/
`status`/`evidence` is not reliably preserved end-to-end.** This is the structural reason
`evidence` text is the only channel `classify_checklist_failure` can currently depend on for the
real runtime path.

### 2. `implement-ticket.js`'s hand-synced JS mirror

`.claude/workflows/implement-ticket.js:276-294`:

```js
// Mirrors tools/gate_checks/done_checker_static.py's classify_checklist_failure() exactly — kept
// in sync by hand ... Not invoked via bash()/subprocess: doneCheck.checklist can contain arbitrary
// evidence text (quoted tag names, backtick-wrapped shell commands from validate_frontmatter.py's
// own error messages) that this file's own established convention warns against embedding into a
// shell command string ... A local JS re-implementation of this ~5-line check avoids that risk
// entirely.
const _TAG_REGISTRY_REJECTION_MARKER = 'is not in the tag registry'
const classifyChecklistFailure = (checklist) => {
  for (const item of checklist || []) {
    if (item.status === 'FAIL') {
      return (item.evidence || '').includes(_TAG_REGISTRY_REJECTION_MARKER)
        ? 'tag_registry_rejection'
        : 'dod_condition_failed'
    }
  }
  return null
}
```

Called synchronously (line 1206) on `doneCheck.checklist`, an in-memory JS array already parsed
from the agent's structured JSON response — never round-tripped through a shell. The
quote-corruption risk the comment describes is specifically about the *alternative design* the JS
mirror was chosen over: invoking Python's `classify_checklist_failure` via `bash(python3 -c
"...")` with `doneCheck.checklist`'s arbitrary evidence text embedded in the command string
(mirrors the file's own `p0ScanOutput`-comment precedent for why embedding JSON blobs in `python3
-c "..."` strings is unsafe — line 237's cross-reference). Confirmed real: `_check_tags`'s own
evidence message (line 176-180 above) contains **both** backticks and a nested double-quoted
`--note "..."` fragment — exactly the shell-hostile content the comment warns about.

### 3. `registry_query.py`'s hardcoded `SEED_TAGS`

`tools/registry_query.py` (58 lines, read in full), lines 13-24:

```python
SEED_TAGS = (
    "combat", "economy", "cognition", "faction", "resource",
    "social", "content", "world", "engine", "strategy",
)
```

`candidate_tags_from_text(*texts)` (lines 27-34) does a plain case-insensitive substring test of
each `SEED_TAGS` word against the concatenation of `texts`. The module docstring (lines 1-11)
explicitly says this tuple and `docs/guidelines/tag_taxonomy.md`'s prose list are "two independent
copies of the same 10 words and must be kept in sync by hand." Consumers: `.claude/agents/
concern-investigator.md` (line 64-69, `candidate_tags = candidate_tags_from_text(<title>,
<description>, <domain_area>)`), and `filter_registry()` (lines 37-52, unaffected by this change —
it only consumes the resulting `candidate_tags` set, agnostic to how it was built).

**Verified against the live registry** (`registries/tag_registry.jsonl`, 53 rows, 19
`subsystem-topic` tags today) which of the 10 `SEED_TAGS` words are actually registered:

| Word | Registered as `subsystem-topic`? |
|---|---|
| `cognition` | yes (2026-07-06) |
| `faction` | yes (2026-07-06) |
| `social` | yes (2026-07-10) |
| `world` | yes (2026-07-06) |
| `combat` | **no** |
| `economy` | **no** |
| `resource` | **no** (a different tag, `resource-registry`, is registered) |
| `content` | **no** |
| `engine` | **no** |
| `strategy` | **no** |

Only 4 of the 10 seed words are actually registered tags today. See Risks below — this is a real
coverage gap a naive swap would introduce.

### 4. Doc references (tag_taxonomy.md, ticket_tagging.md, ticket_reporting.md, CLAUDE.md,
tag_report.py, generate_retro.py)

Checked all six for (a) stale `docs/guidelines/{tag,layer}_registry.jsonl` paths and (b)
hardcoded-category-list prose that doesn't describe the registry-backed model:

- **No stale `docs/guidelines/tag_registry.jsonl` / `docs/guidelines/layer_registry.jsonl`
  references found** in any of the six files. `TCK-20260720-TAG-REGISTRY-RELOCATE` (done ticket,
  `Files Changed`) already updated all of `tag_taxonomy.md`, `ticket_tagging.md`,
  `ticket_reporting.md`, `CLAUDE.md`, `tools/tag_report.py`, and `tools/validate_frontmatter.py` to
  the new `registries/` paths in the same pass.
- **`tag_taxonomy.md`'s category description already accurately reflects the registry-backed
  model**: line 158 (`<category>` must be one of the 4 named values) is immediately followed
  (lines 180-185) by "the registry is currently seeded with exactly the 4 addable categories named
  above" — phrased as a description of current registry *contents*, not a hardcoded code
  enumeration. `TCK-20260720-TAG-CATEGORY-REGISTRY` (done ticket, `Files Changed`) already updated
  this file when it converted `ALL_CATEGORIES`/`ADDABLE_CATEGORIES` to `category_values()`.
- **`tools/tag_report.py`** (docstring lines 12-17) already describes categorization as "a direct
  lookup against `registries/tag_registry.jsonl`" — no stale hardcoded-list prose.
- **`tools/agent-monitoring/generate_retro.py`** has no doc-path or category-list references at
  all (it imports `load_registry`/`categorize_tag` and consumes them functionally — no prose to
  go stale).
- **Residual gap found, not previously covered**: `tests/tools/test_registry_query.py` and
  `.claude/agents/concern-investigator.md` both directly reference `candidate_tags_from_text`/
  `SEED_TAGS`-adjacent behavior and are **not** in the ticket's named doc list, but are real
  touchpoints of Scope bullet 2 (see Anti-Drift Hazards).

**Conclusion: AC #3 (doc references) appears to already be satisfied by the two prerequisite
tickets** (`TCK-20260720-TAG-REGISTRY-RELOCATE`, `TCK-20260720-TAG-CATEGORY-REGISTRY`, both
`DONE`, both explicitly listing these six files in their own `Files Changed`). No further doc edits
were found necessary during this investigation; the planner should re-verify with a final grep
sweep at Verify time rather than assume new prose changes are required, since the ticket's own
scope bullet 3 wording predates confirmation that the two dependency tickets already closed this
gap.

## Mechanics / Engine Constraints

None. This ticket touches only agent-workflow tooling (`tools/gate_checks/`, `tools/
registry_query.py`, `.claude/workflows/implement-ticket.js`) and process documentation — no
`docs/mechanics/` or `docs/engine/` chapter governs gate-check/tag-registry internals. No
Mechanics Bible citation applies.

## Parity Ledger Overlap

Searched `docs/parity_ledger/infrastructure.yaml` (the subsystem covering "Replay, telemetry,
observability, workers" / tooling) for entries whose `text`/`v2_evidence` touch the files in
scope:

- **`INFRA-180`** (`verified`, P2) — "Frontmatter validator ... correctly enforces the doc schema
  ... tags additionally carry controlled-vocabulary enforcement." `v2_evidence` cites
  `tools/validate_frontmatter.py` + `tests/tools/test_validate_frontmatter.py`. **Not affected**
  by the recommended design below (validate_frontmatter.py's `validate_file`/`_check_tags` public
  contract is left unchanged) — no update needed unless implementation deviates from that
  recommendation.
- **`INFRA-263`** (`verified`, P2) — "Ticket-close finalize gate enforces that docs/REGISTRY.yaml
  has been regenerated..." `v2_evidence` cites `check_registry_entry_regenerated()` (a *different*
  function in the same file as `classify_checklist_failure`). **Not affected** — this ticket does
  not touch `check_registry_entry_regenerated`.
- No parity ledger entry exists for `classify_checklist_failure`, `SEED_TAGS`/
  `candidate_tags_from_text`, or the JS mirror specifically — expected, since these are
  agent-orchestration internals, not simulation laws, and the Parity Ledger's stated scope
  (`docs/parity_ledger/schema.json`, CLAUDE.md's Authoritative Mechanics Rule) is simulation
  behavior parity between legacy and V2, not tooling implementation details.
- **No P0 entries touched.** Both entries found are P2. No `test_path` gap: both cited test files
  (`tests/tools/test_validate_frontmatter.py`, `tests/tools/test_done_checker_static.py`) exist.

**Conclusion: no parity ledger entry requires updating for this ticket**, provided the
implementation follows the recommendation below (validate_frontmatter.py's public surface
unchanged). If the implementer instead changes `validate_file`/`_check_tags`'s return contract
(the AC #1 alternative), `INFRA-180`'s `v2_evidence` should be re-verified for accuracy (not
necessarily rewritten — the entry describes *behavior*, which would be unchanged either way, only
internal return-shape would differ).

## Prior Work

- **`TCK-20260705-GATE-DET-DONE-CHECKER`** (stored artifacts read in full) — built
  `done_checker_static.py` itself, Part A/B checks, `run_static_precheck`/
  `run_finalize_selfcheck`. Established the "plain tuple returns, no argparse" module convention
  this ticket must preserve.
- **`TCK-20260706-MONITORING-REASON-CODE`** — built `classify_checklist_failure` and the
  `reason_code` concept for `DOD_BLOCKED` disambiguation. Its docstring (still in the current
  source, lines 313-333) is the origin of both the substring-marker approach and the documented
  JS-mirror rationale. No `plan.md`/`investigation.md` text specifically named the "shell
  quote-corruption" phrase (that language lives entirely in the current source comments, not a
  separate stored artifact) — the current code *is* the authoritative record of that decision.
- **`TCK-20260705-TAG-REGISTRY-QUERY`** — built `registry_query.py`'s `SEED_TAGS`/
  `candidate_tags_from_text`/`filter_registry`, explicitly as a "cheap seed-vocabulary" mechanism,
  documented in its own module docstring as a deliberate stopgap ("no runtime parsing of the doc
  into this module — that would be over-engineering for a 10-word list"). This ticket's Scope
  bullet 2 directly reverses that stopgap decision now that a live registry exists.
- **`TCK-20260706-TAG-REGISTRY-DATA`** — built the original `registries/tag_registry.jsonl` +
  `is_tag_registered`/`check_tags_registered` (`tools/tag_registry.py`) that both this ticket's
  Scope bullets 1 and 2 are meant to consume directly instead of duplicating.
- **`TCK-20260720-TAG-CATEGORY-REGISTRY`** and **`TCK-20260720-TAG-REGISTRY-RELOCATE`** (both
  `DONE`, both stored artifacts read) — the two direct prerequisites this ticket's own
  `Assumptions/Open Questions` names. Confirmed landed: `registries/tag_registry.jsonl`,
  `registries/tag_category_registry.jsonl`, `category_values()` all exist and are live. This
  ticket's Scope bullet 3 (doc updates) is, per Current Behavior #4 above, already substantially
  satisfied by these two tickets' own `Files Changed`.
- **Epic context**: `tickets/todos/tag-registry-redesign/SEQUENCE.md` lists this ticket as item 6
  of 7 in a batch, depending on both `TAG-REGISTRY-RELOCATE` and `TAG-CATEGORY-REGISTRY` (both
  satisfied). The SEQUENCE.md's own "Known Open Decisions" section names this ticket's JS-mirror
  question verbatim but deliberately leaves it unresolved for this ticket's own Investigate/Plan
  phase — consistent with what this investigation resolves below.
- **`TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX`** (done, hotfix) — confirmed genuinely
  out-of-scope/non-overlapping: it fixed a *different* file (`create-tickets.js`'s Structure-phase
  tag-category-restriction prompt text), not touched by this ticket's Scope bullets.

## Risks and Open Questions

### Resolved: JS mirror decision (ticket AC #4)

**Recommendation: update `implement-ticket.js`'s `classifyChecklistFailure` in lockstep with the
Python side — do not keep it as a hand-synced string match.**

The quote-corruption rationale (comment at `implement-ticket.js:276-283`) is specifically about
**not piping `doneCheck.checklist`'s arbitrary `evidence` text through a `bash(python3 -c "...")`
call** — `_check_tags`'s own evidence message literally contains backticks and a nested
double-quoted fragment (confirmed above), which would corrupt a naively-embedded shell string.
That risk is real today because the *only* signal available to classify a tag rejection is that
evidence text.

The recommended `classify_checklist_failure` redesign below (see "Resolved: structured
reason_code mechanism") changes what signal is used: instead of scanning `evidence` text, it (a)
matches on the `condition` field (a small closed vocabulary — `"frontmatter_valid"` — not
free text), and (b) independently re-verifies tag-registry membership by re-reading the *live*
ticket/staging files' `tags:` frontmatter (using `ticket_id`/`tier`, both plain identifiers already
interpolated safely into other `bash()` calls in this exact file — e.g. `writeSidecar`,
`resolveScopeTicketLocation` at lines 240-274 already do `"${tid}"`/`"${id}"` interpolation without
incident). **No `evidence` text — the actual quote-corruption-risk content — ever needs to cross
the shell boundary under this design.** The original rationale therefore does not survive the
AC #1 redesign; it applied to the old (evidence-text-substring) mechanism specifically, not to
tag-rejection classification in general.

Concrete lockstep change: replace `classifyChecklistFailure`'s body with a call to
`bash(python3 -c "...")` invoking a new Python helper (see below) with `tid`/`tier` as argv, for
the `frontmatter_valid`-condition case only; keep the plain `dod_condition_failed` fallback local
(no shell call needed — it needs no data beyond `status === 'FAIL'`). This becomes `async`
(the call site at line 1206 must `await` it — currently synchronous).

### Resolved: structured reason_code mechanism (ticket AC #1 / Assumptions bullet 2)

**Recommendation: Option B — `done_checker_static.py` independently re-derives the reason via
`tag_registry.py`'s `check_tags_registered()`, decoupled from `validate_frontmatter.py`'s error
text. Do NOT change `validate_frontmatter.py::_check_tags`'s return type.**

This has a second, independent justification beyond decoupling from text-matching: per the
pre-existing gap documented in Current Behavior #1 above, `check_frontmatter_valid()` today calls
`validate_file`/`validate_directory` with no `registry` argument, so registry-membership is
**never actually checked** by the static precheck — only canonical form is. `_check_tags`'s
`is_tag_registered` branch is effectively dead code on this path. Fixing this (passing a real
`registry` through, or — equivalently and more directly — having a dedicated helper call
`check_tags_registered()` itself) is required regardless of which reason-code mechanism is chosen;
Option B's design folds that fix in naturally, since it calls `check_tags_registered()` directly.

Why not the `_check_tags` structured-tuple option: `validate_file()`/`validate_directory()`
(the functions `_check_tags`'s errors ultimately flow through) are consumed by **50+ existing
assertions** in `tests/tools/test_validate_frontmatter.py` (every one of the form `errors =
validate_file(f)` / `assert validate_file(f) == []`, confirmed by direct grep — lines 147-733),
plus `done_checker_static.py::check_frontmatter_valid` itself. Changing `_check_tags`'s return
shape from `list[str]` to `list[tuple[str, str]]` (message, reason_code) cascades into
`_validate_ticket`/`_validate_artifact`'s `errors += _check_tags(...)` accumulation (lines 210,
224) and therefore `validate_file`'s overall return type — a blast-radius change to a
widely-tested, non-ticket-owned public contract, for a benefit (`classify_checklist_failure`'s
internal classification) that does not actually need it end-to-end: even if `_check_tags` returned
structured data, `check_frontmatter_valid` still flattens into a single joined evidence string for
the checklist item (line 263), and `DONE_SCHEMA` still only allows `condition`/`status`/`evidence`
on the agent-round-tripped path — so a reason_code embedded at the `_check_tags` level would not
reliably survive to the real call site (`doneCheck.checklist` at line 1206) any more reliably than
today's text marker does, for the added cost of a breaking API change.

**Concrete implementation (confined to `tools/gate_checks/done_checker_static.py` +
`tests/tools/test_done_checker_static.py` only — zero change to `validate_frontmatter.py`'s
public surface, zero risk to its 50+ existing tests):**

```python
from tag_registry import check_tags_registered  # new import, alongside existing tag_registry usage

def _frontmatter_has_unregistered_tags(
    ticket_id: str, tier: str, ticket_path: Path = None, staging_dir: Path = None
) -> bool:
    """Independently determine whether ticket_path/staging_dir's declared `tags:` frontmatter
    includes anything not in the live tag registry — calls tag_registry.check_tags_registered()
    directly, zero dependency on validate_frontmatter.py's error TEXT. Mirrors
    check_frontmatter_valid's own path-resolution/hotfix-branching so the two functions agree on
    which files' tags to check, without sharing implementation or return shape."""
    if ticket_path is None:
        ticket_path = Path(f"tickets/inprogress/{ticket_id}.md")
    if staging_dir is None:
        staging_dir = Path(f"staging_artifacts/{ticket_id}")

    files = [ticket_path] if ticket_path.exists() else []
    if not (tier == "hotfix" and not staging_dir.exists()):
        files += sorted(staging_dir.rglob("*.md")) if staging_dir.exists() else []

    all_tags: list[str] = []
    for f in files:
        try:
            fm = extract_frontmatter(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if fm and isinstance(fm.get("tags"), list):
            all_tags.extend(fm["tags"])

    return bool(check_tags_registered(all_tags))


def classify_checklist_failure(
    checklist: list[dict], ticket_id: str | None = None, tier: str | None = None
) -> str | None:
    for item in checklist:
        if item.get("status") == "FAIL":
            if (
                item.get("condition") == "frontmatter_valid"
                and ticket_id is not None
                and tier is not None
                and _frontmatter_has_unregistered_tags(ticket_id, tier)
            ):
                return "tag_registry_rejection"
            return "dod_condition_failed"
    return None
```

`extract_frontmatter` needs importing from `validate_frontmatter` (already a one-directional,
existing-pattern import — `done_checker_static.py` already imports `validate_file`/
`validate_directory` from the same module at line 39).

**This changes `classify_checklist_failure`'s signature** (adds two optional kwargs, backward
compatible — existing 2-arg calls still work but degrade to the old-style FAIL→
`dod_condition_failed` fallback since the tag re-check is now gated on `ticket_id`/`tier` being
supplied). The real call site (`implement-ticket.js:1206`) must be updated to pass `tid`/`tier`
(both already in scope as closure variables at that point in the function) for the classification
to work end-to-end — **this is a required, not optional, companion change**, or `DOD_BLOCKED`
reason codes silently regress to `dod_condition_failed` for every tag rejection after this ticket
lands.

**Impact on the 5 existing `classify_checklist_failure` tests**
(`tests/tools/test_done_checker_static.py:553-604`): they currently construct synthetic
`checklist` dicts with marker text and call `classify_checklist_failure(checklist)` with no
ticket_id/tier. Under the new signature, `test_classify_checklist_failure_tag_registry_rejection`
and `test_classify_checklist_failure_scans_past_leading_pass_entries` (the two that assert
`"tag_registry_rejection"`) would need to be rewritten to (a) pass `ticket_id`/`tier`, and (b) set
up a real `tmp_path` fixture ticket file with an actual unregistered tag (this suite already uses
`monkeypatch.chdir(tmp_path)` fixture patterns elsewhere — e.g. around line 540-545 — so this is a
precedented pattern, not a new one). This satisfies AC #1's explicit allowance: "the existing 5
done_checker_static tests still pass unmodified **or with equivalently-asserted behavior**" — the
3 non-tag-rejection tests (`all_pass_returns_none`, `generic_dod_failure`,
`returns_first_fail_when_multiple`) need no fixture changes since they never hit the tag-check
branch (no `frontmatter_valid`-condition FAIL present).

### Blocking-if-unaddressed: `check_frontmatter_valid` must also start passing a real `registry`

The dead-code gap above has a sharper implication than "the reason code is sometimes
misclassified": **`check_frontmatter_valid()`'s own `status` (PASS/FAIL) for the
`frontmatter_valid` condition never turns `FAIL` for an unregistered tag today**, because
`_check_tags` needs `registry is not None` to run that branch at all. If this ticket only fixes
`classify_checklist_failure` (adds the independent re-check) but leaves `check_frontmatter_valid`
itself calling `validate_file(ticket_path)` / `validate_directory(staging_dir, ...)` with no
`registry`, then: (a) an unregistered tag still produces a `PASS` static-precheck result, (b)
`doneCheck.verdict` can still reach `READY_TO_CLOSE` with an unregistered tag present, and (c)
`classify_checklist_failure`'s new tag-recheck branch is unreachable in practice (it only runs
when `item.get("condition") == "frontmatter_valid"` AND `status == "FAIL"` — which never happens
for this cause under the current wiring). **The planner must include, as part of AC #1's fix,
passing `load_registry()`'s output through to `validate_file`/`validate_directory` inside
`check_frontmatter_valid` itself** (one-line change: `validate_file(ticket_path, registry=...)` /
`validate_directory(staging_dir, content_type_override="artifact", registry=...)`, using
`tag_registry.load_registry()`, mirroring `validate_frontmatter.py::main()`'s own line 320 usage).
Without this, the ticket's stated goal ("no longer relies on substring-matching... it derives
reason_code by calling tag_registry.py's ... directly") is satisfied on paper but the gate itself
still never blocks on an unregistered tag — a much worse outcome than today's fragile-but-at-least-
sometimes-working text match. This is not itself a scope-creep risk (Scope bullet 1 already covers
`check_frontmatter_valid`'s "tag_registry_rejection classification" as a whole, not just
`classify_checklist_failure` in isolation) but is easy to miss since the two functions are
textually adjacent and easy to conflate.

### Open risk (not blocking, flagged for planner): SEED_TAGS coverage gap

Swapping `registry_query.py::SEED_TAGS` for a live read of `registries/tag_registry.jsonl`'s
`subsystem-topic` tags (AC #2) is a **real behavior change**, not a pure refactor: only 4 of the
10 current `SEED_TAGS` words (`cognition`, `faction`, `social`, `world`) are actually registered
tags today. `combat`, `economy`, `resource`, `content`, `engine`, `strategy` are **not**
registered — prior-work search coverage for these 6 core-subsystem words would silently narrow
the moment the swap lands, unless they are also registered as `subsystem-topic` tags in the same
ticket. This is exactly the trade AC #2's own wording anticipates ("adding a new subsystem-topic
tag via the CLI makes it queryable with zero code change") — but the swap alone, without also
registering the 6 missing words, produces a net *regression* in seed coverage versus today's
hardcoded list. **Recommendation for the planner**: register the 6 missing words via `python3
tools/tag_registry.py add <word> --category subsystem-topic --note "..."` as part of this
ticket's implementation (they are uncontroversial, already-named-in-tag_taxonomy.md core
subsystem words, canonical form already satisfied), preserving today's coverage before the swap
takes effect — or, if the planner decides not to backfill, explicitly document the coverage
narrowing as an accepted, intentional trade in the ticket's Completion Summary rather than leaving
it a silent side effect.

### Minor gap: two Scope-bullet-2 touchpoints not in the ticket's own "Related Code Areas"

`tests/tools/test_registry_query.py` and `.claude/agents/concern-investigator.md` both directly
exercise `candidate_tags_from_text`/`SEED_TAGS`-adjacent behavior but are not named in this
ticket's Related Code Areas or Related Docs. `test_registry_query.py` must be touched regardless
(it is the regression surface for AC #2 — see test_plan.md). `concern-investigator.md` calls
`candidate_tags_from_text(<title>, <description>, <domain_area>)` positionally — unaffected by an
internal implementation swap as long as the function signature (`*texts: str) -> set[str]`) is
preserved, which the recommended design does not change.

## Anti-Drift Hazards

- **Do not widen `validate_frontmatter.py::validate_file`/`_check_tags`'s return contract.** 50+
  existing tests in `tests/tools/test_validate_frontmatter.py` assert `list[str]` shape directly;
  this is the single highest-blast-radius mistake available in this ticket's scope. The
  recommended design above deliberately avoids it.
- **Do not let `classify_checklist_failure`'s new tag-recheck become a second source of truth for
  "is this tag registered."** It must call `tag_registry.check_tags_registered()` — never
  re-implement the canonical-form/registry-membership logic locally.
- **The JS-side lockstep update must remain `async`-safe.** `classifyChecklistFailure` becomes a
  function that shells out (`bash(...)`) for the `frontmatter_valid` case; its one call site
  (line 1206) is currently a synchronous assignment inside an already-`async` workflow function —
  must add `await`, and must not silently swallow a bash failure into a wrong classification
  (default to `dod_condition_failed` on any subprocess error, never crash the workflow — matches
  this file's own "monitoring write must never fail the workflow" convention elsewhere).
- **Do not silently drop the `SEED_TAGS`-word coverage** when removing the tuple (see Risks
  above) — verify via a real diff of old-vs-new `candidate_tags_from_text` output over a sample of
  known ticket titles, not just "the tests still pass."
- **`registries/tag_category_registry.jsonl` and `registries/tag_registry.jsonl` are append-only.**
  Registering the 6 missing `SEED_TAGS` words (if the planner adopts that recommendation) is a
  one-way action — get the category (`subsystem-topic`) and canonical form right the first time.
- **Do not conflate this ticket's `classify_checklist_failure` reason-code work with
  `TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX`'s unrelated Structure-phase prompt-text fix** — both
  are filed the same day, touch adjacent files, but are explicitly independent per this ticket's
  own Out of Scope section and the epic SEQUENCE.md's "Related, Not Duplicated" note.
