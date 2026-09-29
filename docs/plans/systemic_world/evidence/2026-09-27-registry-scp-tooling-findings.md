---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated evidence snapshot supporting `docs/plans/systemic_world/roadmap.md`, copied from the local working file `registry-scp-tooling-findings.md` on 2026-09-27. Where the roadmap has since corrected a claim, the roadmap is authoritative.

# Registry/SCP tooling query recipes — findings

Directive: investigate the existing Semantic Control Plane (SCP) and mechanism-registry tooling
and answer instruction §1's four practical questions with real, tested commands (not invented
ones).

## Q1 — Given a Rule/domain capability, which formal mapping, mechanism, classification, and evidence currently exist?

No general-purpose query tool exists. `tools/semantic_control_plane/generate_territory_control_view.py`'s
`main()` is hardcoded to exactly two domains (`_TERR_RULE_IDS`, `_COMBAT_RULE_IDS` — confirmed by
reading the source; no `--rule` argument for an arbitrary Rule ID). For any other Rule, the only
recipe is a manual filter. Run against current repo state:

```python
import yaml
edges = yaml.safe_load(open('registries/rule_mechanism_edges.yaml'))['edges']
print(len(edges))                              # -> 18
print(sorted(set(e['rule_id'] for e in edges)))
# -> ['AGENCY-01','AGENCY-02','AGENCY-04','BODY-07','CAP-01','KNOW-01','LIFE-01','LIFE-02',
#     'OWN-02','PERC-01','TERR-01','TERR-02','TERR-03','TERR-05']
```

Real result: 18 total mapping edges, covering only 14 of 172 Rule IDs — everything else is
genuinely `UNKNOWN` (matches the roadmap's own §6 claim, now independently confirmed).

**Named gap**: no CLI/function does this lookup — it's a hand-rolled YAML filter every time, and
the one generator that exists can't be pointed at a Rule outside its two hardcoded domains.

## Q2 — Given a mechanism or changed production path, which mapped Rules, downstream causal relationships, and scenario checks may need revalidation?

`tools/semantic_control_plane/registry.py` has real, working `consumers_of(mechanism_id, edges)`
and `producers_for(mechanism_id, edges)` — but only over `mechanism_causal_edges.yaml`
(mechanism→mechanism chains). There is **no equivalent reverse lookup from mechanism_id →
citing rule_id** in `rule_mechanism_edges.yaml`. Verified directly against the lineage
mechanisms:

```python
[e for e in edges if e['mechanism_id']=='succession']    # -> []
[e for e in edges if e['mechanism_id']=='aging_death']   # -> []
```

Both return empty — confirms lineage's `succession`/`aging_death` mechanisms have zero SCP
edges, consistent with "not SCP-mapped," but confirming it took a manual scan since no reverse
index exists.

Separately, `tools/mechanism_registry/mechanism_registry_changed_code_check.py` and
`mechanism_prose_field_drift_check.py` are real, working changed-code advisories, but neither
crosses into the Rule-mapping layer — they check mechanism-registry-internal drift only, not
which Rules a changed mechanism implicates.

## Q3 — What is formally mapped, what is supported only by Catalog prose/investigation notes, and what has no evidence yet?

Already answered structurally by Q1's 18-edge/14-Rule-ID count (the formally-mapped set).
`registries/rule_classifications.yaml`'s own header states explicitly that `UNKNOWN` ("not yet
looked at") must never be conflated with `MISSING` ("investigated, confirmed absent") — this is
real, working, already-documented discipline, not a gap. Its `evidence:` fields cite Catalog
Repository-Findings prose (e.g. `TERR-01`'s `CONFLICTING` entry) directly, distinctly from the
edge-level machine mapping.

## Q4 — Which paths or evidence references have drifted since their last verification?

Real, working tool, actually run against current HEAD:

```
$ python3 tools/semantic_control_plane/mapping_drift_check.py
Mapping drift check (report-only, never fails): 0 cited-code drift finding(s), 0 verdict drift finding(s)
```

No gap here — it checks both cited-code drift and classification-verdict drift, anchored to
each row's own `review_date` against real git history.

**Validator** (structural only, not a query tool, also run for real):
`python3 tools/semantic_control_plane/registry.py` →
`OK: rule_mechanism_edges.yaml, mechanism_causal_edges.yaml, rule_classifications.yaml valid`.

## Recommendation — smallest incremental improvement

Explicitly not a second registry, a universal ontology, or an early Stage-F Context Compiler,
per the review's own prohibition. Add one pure function to
`tools/semantic_control_plane/registry.py`:

```python
def rules_for(mechanism_id: str, edges: List[dict]) -> List[str]:
    """Every rule_id that cites this mechanism_id -- reverse of the forward Rule->edges lookup."""
    return [e["rule_id"] for e in edges if e.get("mechanism_id") == mechanism_id]
```

This mirrors the existing `consumers_of`/`producers_for` shape exactly — a ~10-line
reverse-index reusing an already-proven pattern in the same file — and closes the one concrete,
evidenced gap (Q2) without touching schema, validation, or the two-domain view generator.
Everything else asked for in §1 already has a real, working answer today.

Q1's broader general-purpose multi-Rule query CLI (extending
`generate_territory_control_view.py` past its two hardcoded domains, or building a separate
thin CLI) is a larger design decision than "smallest increment" and is left out of scope here,
for whoever next scopes that work.
