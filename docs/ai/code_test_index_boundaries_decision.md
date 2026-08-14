---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, investigation]
---

# Code/Test Index Boundaries Decision — TCK-20260728-CODE-TEST-INDEX-BOUNDARIES

Resolves **Open Decision 2** from
`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
(tracked by epic `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`):

> Which code/test relationships can be built deterministically from existing AST, import, test
> naming, and Graphify data before adding any semantic code model?

This document **decides and evidences**. It implements nothing — no extractor, script, or index
is created or modified as part of landing it. All claims below were verified directly against the
installed `graphify` package source and this repo's test-scoping docs, not assumed from the prior
investigation pass that motivated this ticket.

---

## 1. Verified Facts

### 1.1 `graphify` is an external pip package, not repo-owned code

```
$ python3 -c "import graphify; print(graphify.__file__)"
/home/vboxuser/.local/lib/python3.13/site-packages/graphify/__init__.py

$ pip show graphifyy
Name: graphifyy
Version: 0.6.7
Location: /home/vboxuser/.local/lib/python3.13/site-packages
```

The **import name** (`graphify`) and the **distribution/pip name** (`graphifyy`, note the extra
`y`) differ. Nothing under this repo's `tools/` implements extraction — `tools/graphify_to_html.py`
and `tools/knowledge_search.py` only consume `graphify-out/graph.json`, they do not produce it.

**Reproducibility/versioning implication:** the relation vocabulary and extraction behavior this
decision relies on live in a third-party package installed to the user's local site-packages, not
pinned in this repo's `requirements*.txt`/lockfile at the time of this investigation. A future
`pip install -U graphifyy` (or a different machine/agent without it installed at all) can silently
change or remove relation types this decision treats as stable, with no repo-level signal. Any
future ticket that builds retrieval logic on top of these relation strings should pin
`graphifyy==0.6.7` (or whatever version is adopted) in a tracked dependency file and re-verify this
document's relation-type table against the pinned version, rather than assuming ambient stability.

### 1.2 Graphify's extraction has two structurally distinct parts

**Part A — deterministic, tree-sitter/AST-based, no LLM.** Implemented in
`graphify/extract.py` (module docstring, line 1: *"Deterministic structural extraction from source
code using tree-sitter. Outputs nodes+edges dicts."*). The bulk of relation types come from a
shared, language-parameterized engine: `LanguageConfig` (lines 66–106) + `_extract_generic()`
(lines 852–1541), which `extract_python()` (line 1645) and the other per-language `extract_*`
functions call with a language-specific config. A separate deterministic post-pass,
`_extract_python_rationale()` (lines 1542–1599), walks Python docstrings via the same tree-sitter
parser to emit `rationale_for` edges — this is **not** an LLM call, it is a regex/AST pass over
docstring text.

Every edge produced by Part A carries `"confidence": "EXTRACTED"`. Where `confidence_score` is not
set explicitly at the call site, `graphify/export.py`'s `_CONFIDENCE_SCORE_DEFAULTS` (line 329)
maps `EXTRACTED → 1.0` (vs. `INFERRED → 0.5`, `AMBIGUOUS → 0.2`) when the graph is serialized. So
every Part A edge is `confidence_score = 1.0` by construction, not by convention.

**Part B — semantic/LLM extraction, non-deterministic.** Implemented in `graphify/llm.py`, which
calls out to an actual model API (`_call_claude()` line 152, using `anthropic.Anthropic(...)`, or
an OpenAI-compatible backend via `_call_openai_compat()` line 110; `env_key: ANTHROPIC_API_KEY` at
line 50). The prompt schema embedded at `llm.py:76` fixes the LLM's own output relation vocabulary
to: `calls | implements | references | cites | conceptually_related_to | shares_data_with |
semantically_similar_to`, with confidence one of `EXTRACTED | INFERRED | AMBIGUOUS` (i.e. the LLM
is allowed to self-report `EXTRACTED`, which is a materially different guarantee from Part A's
structurally-forced `EXTRACTED`). This path requires a live API call, an API key, and a chosen
model — it is not reproducible byte-for-byte across runs or model versions and does not satisfy
"no new semantic code model."

**Correction to the ticket's stated premise:** the ticket description (and the prior investigation
pass that seeded it) placed `rationale_for` in Part B alongside `conceptually_related_to`,
`semantically_similar_to`, and `shares_data_with`. Direct inspection of `llm.py:76`'s prompt schema
shows `rationale_for` is **not** in the LLM's output vocabulary at all — it is emitted only by Part
A's deterministic docstring pass (`extract.py:1542-1599`, confidence `EXTRACTED`). This document
corrects that: `rationale_for` belongs in the Part A / deterministic-today column below, not Part B.

### 1.3 Test-naming mapping is a deterministic *procedure*, not checked-in code

`.claude/agents/test-scoper.md` describes a step-by-step mapping (`src/content/` →
`tests/unit/content/`, etc., §"Test Directory Map" and §"What to Do") that an agent follows by
reading the file map and using `grep`/naming heuristics at request time. `docs/testing/
how_to_add_requirement_tests.md` §3 "Naming Convention" defines the `test_<law_noun>_<condition>`
pattern (line 85) as something a human/agent author follows when *writing* a test, and
`docs/testing/test_taxonomy.md` defines the adjacent marker/proof-standard rules the same tests
must also satisfy — but neither doc, nor any file under `tools/`, encodes this mapping as an
executable, checked-in artifact. A repo-wide search (`grep -rl "tests/unit" tools/`, search for
`*test_map*`/`*test_index*`/`*code_test*` under `tools/`) found nothing.

**Gap, stated explicitly:** this is deterministic *in the sense that the same inputs would always
produce the same mapping if executed*, but it is not deterministic *in the sense of graphify's Part
A*, where the mapping is already produced, checked, and stored as data (`graphify-out/graph.json`)
independent of any agent's interpretation. Treating "agent follows a written procedure correctly
every time" as equivalent to "checked-in code enforces the mapping" would be the exact overstatement
this ticket exists to prevent. Formalizing test-scoper's procedure into a checked-in script/index is
explicitly out of scope for this ticket (see the ticket's Out of Scope) and is left as a candidate
for a future ticket if Phase 2+ retrieval work needs it as data rather than prose.

---

## 2. Relationship Type Table

| Relationship type | Source | Deterministic today? | Evidence citation |
|---|---|---|---|
| `imports` | Graphify Part A (`_extract_generic`, per-language `_import_*` helpers) | Yes | `extract.py:152,253,370,390,410,430,446,466,486,769,804,1792,3222` — all `confidence: EXTRACTED` |
| `imports_from` | Graphify Part A (`_import_js`, `_import_java`, `_import_scala`) | Yes | `extract.py:177,225,331` — `confidence: EXTRACTED` |
| `calls` | Graphify Part A (`_extract_generic` call-site walk) | Yes | `extract.py:1357,2450,2635,3842` — `confidence: EXTRACTED` |
| `contains` | Graphify Part A (`_extract_generic` / SQL extractor) | Yes | `extract.py:1945` — `confidence: EXTRACTED` |
| `defines` | Graphify Part A (`_extract_generic`, Dart extractor) | Yes | `extract.py:1765,1779` — `confidence: EXTRACTED` |
| `uses` | Graphify Part A (`_extract_generic`) | Yes | `extract.py:3138` — `confidence: EXTRACTED` |
| `uses_static_prop` | Graphify Part A (`_extract_generic`) | Yes | `extract.py:1469` — `confidence: EXTRACTED` |
| `references_constant` | Graphify Part A (`_extract_generic`) | Yes | `extract.py:1490` — `confidence: EXTRACTED` |
| `bound_to` | Graphify Part A (`_extract_generic`, container binding) | Yes | `extract.py:1442` — `confidence: EXTRACTED` |
| `listened_by` | Graphify Part A (`_extract_generic`, event listener props) | Yes | `extract.py:1518` — `confidence: EXTRACTED` |
| `includes` | Graphify Part A (Blade template extractor) | Yes | `extract.py:1719` — `confidence: EXTRACTED` |
| `uses_component` | Graphify Part A (Blade template extractor) | Yes | `extract.py:1729` — `confidence: EXTRACTED` |
| `binds_method` | Graphify Part A (Blade template extractor) | Yes | `extract.py:1739` — `confidence: EXTRACTED` |
| `rationale_for` | Graphify Part A (`_extract_python_rationale`, docstring pass) | Yes (corrected — not LLM; see §1.2) | `extract.py:1542-1599`, edge at line 1593 — `confidence: EXTRACTED` |
| `conceptually_related_to` | Graphify Part B (LLM extraction) | No — requires live model call | `llm.py:76` prompt schema; `llm.py:152` `_call_claude` |
| `semantically_similar_to` | Graphify Part B (LLM extraction) | No — requires live model call | `llm.py:76` prompt schema |
| `shares_data_with` | Graphify Part B (LLM extraction) | No — requires live model call | `llm.py:76` prompt schema |
| `implements` / `references` / `cites` | Graphify Part B (LLM extraction; overlaps some Part A names but self-reported confidence) | No — requires live model call | `llm.py:76` prompt schema |
| Test-naming mapping (`src/X/` → `tests/unit/X/`; `test_<law_noun>_<condition>`) | Repo convention, agent-followed procedure | Deterministic-in-principle, **not checked-in code today** — gap | `.claude/agents/test-scoper.md` §Test Directory Map/§What to Do; `docs/testing/how_to_add_requirement_tests.md:85-90,280`; `docs/testing/test_taxonomy.md` (adjacent marker rules) |

---

## 3. Resolution

**Open Decision 2 is resolved.** The code/test relationships that can be built deterministically
today, without adding any new semantic code model, are exactly **Graphify's Part A relation set**
(`imports`, `imports_from`, `calls`, `contains`, `defines`, `uses`, `uses_static_prop`,
`references_constant`, `bound_to`, `listened_by`, `includes`, `uses_component`, `binds_method`,
`rationale_for`) as already produced by the installed `graphify` (pip: `graphifyy==0.6.7`) package's
tree-sitter/AST extractor and stored with `confidence_score = 1.0` in `graphify-out/graph.json`.
Graphify's Part B relations (`conceptually_related_to`, `semantically_similar_to`,
`shares_data_with`, and LLM-self-reported `calls`/`implements`/`references`/`cites`) require a live
LLM call and are excluded — building on them would itself be "adding a semantic code model."

Test-to-code linkage (the "test naming" leg of the decision) is deterministic **as a procedure**
today (test-scoper's directory-mapping heuristic, the `test_<law_noun>_<condition>` naming
convention) but has **no checked-in code or index backing it** — this is a real gap, not
equivalent-in-kind to graphify's stored, versioned artifact. Any Phase 2+ retrieval work that wants
test-linkage as reliable as the graphify relations must first close this gap with a checked-in
script/index (out of scope here), rather than relying on an agent re-deriving the mapping from prose
each time.

Any future retrieval/indexing ticket building on this decision should (a) pin the `graphifyy`
package version per §1.1, (b) restrict itself to the Part A relation set in §2, and (c) treat
test-naming linkage as an open gap requiring its own ticket rather than assuming it is already data.
