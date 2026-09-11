"""Tests for the Knowledge Gateway MCP evidence & cache identity contract freeze
(TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY).

Phase 0 is contract-only: no gateway, routing, cache-invalidation, or migration code exists yet.
These tests structurally validate the frozen contract artifacts under
`docs/engine/contracts/knowledge_gateway_mcp/` (`evidence_cache_identity_contract.md`,
`evidence_identity_kinds.schema.json`, `cache_migration_plan.md`), using the same raw-`json.loads()`
/`Path.read_text()`/`ast.parse()` pattern `tests/tools/test_retrieval_cache.py::TestStaticGuards`
uses — no `jsonschema` dependency, no import of live cache-invalidation code (none exists to import
at Phase 0). (The former sibling cross-check against `test_knowledge_gateway_contract_schemas.py`
was removed when that file was hard-deleted by TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY.)

Test #2 and Test #9 read the real, untouched `tools/retrieval_cache.py` via `ast.parse()` /
`Path.read_text()` only — they are regression guards against that module, not tests of new code
this ticket writes (this ticket writes no `tools/`/`src/` code at all).
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_CONTRACTS_DIR = _REPO_ROOT / "docs" / "engine" / "contracts" / "knowledge_gateway_mcp"

_IDENTITY_CONTRACT_MD = _CONTRACTS_DIR / "evidence_cache_identity_contract.md"
_EVIDENCE_KINDS_SCHEMA = _CONTRACTS_DIR / "evidence_identity_kinds.schema.json"
_MIGRATION_PLAN_MD = _CONTRACTS_DIR / "cache_migration_plan.md"
_SHARED_ENUMS = _CONTRACTS_DIR / "shared_enums.schema.json"
_REQUEST_SCHEMA = _CONTRACTS_DIR / "knowledge_context_request.schema.json"

_RETRIEVAL_CACHE_PY = _REPO_ROOT / "tools" / "retrieval_cache.py"

_EIGHT_KINDS = {
    "DOCUMENT",
    "DOCUMENT_SECTION",
    "FILE",
    "SYMBOL",
    "TICKET",
    "PARITY_ENTRY",
    "REGISTRY_ENTRY",
    "PROVIDER_GENERATION",
}

_EXPECTED_MAY_LIST_COLUMNS = {
    "content_hash",
    "embedding_version",
    "chunking_version",
    "source_id",
    "query_hash",
    "filters_hash",
    "corpus_generation",
    "retrieval_version",
    "score",
    "latency_ms",
    "packet_key_hash",
    "cited_hashes_json",
    "policy_version",
    "cache_status",
    "reason_code",
    "created_at",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _section(text: str, start_marker: str, end_marker: str | None) -> str:
    start = text.index(start_marker)
    if end_marker is None:
        return text[start:]
    end = text.index(end_marker, start)
    return text[start:end]


def _field_names_in_table(section_text: str) -> set[str]:
    return set(re.findall(r"^\| `([a-zA-Z_]+)` \|", section_text, flags=re.MULTILINE))


# ---------------------------------------------------------------------------
# Test 1 — lookup identity and evidence-validity identity are disjoint field sets
# ---------------------------------------------------------------------------

def test_lookup_and_validity_identity_are_structurally_distinct():
    text = _IDENTITY_CONTRACT_MD.read_text()

    lookup_section = _section(text, "## 1. Lookup identity", "## 2. Evidence-validity identity")
    validity_section = _section(text, "## 2. Evidence-validity identity", "## 3. Non-collapse rule")

    lookup_fields = _field_names_in_table(lookup_section)
    validity_fields = _field_names_in_table(validity_section)

    assert lookup_fields, "lookup-identity field table not found or empty"
    assert validity_fields, "evidence-validity-identity field table not found or empty"
    assert lookup_fields.isdisjoint(validity_fields), (
        f"lookup identity and evidence-validity identity share field name(s): "
        f"{lookup_fields & validity_fields}"
    )

    non_collapse_section = _section(text, "## 3. Non-collapse rule", "## 4.")
    assert "same primary identity" in non_collapse_section
    assert "lookup hit" in non_collapse_section.lower()


# ---------------------------------------------------------------------------
# Test 2 — real retrieval_cache.py lookup functions carry no validity/freshness verdict
# ---------------------------------------------------------------------------

def test_no_shared_code_or_table_conflates_lookup_hit_with_validity_proof():
    source = _RETRIEVAL_CACHE_PY.read_text()
    tree = ast.parse(source)

    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    for lookup_fn in (
        "check_index_cache", "check_query_cache", "check_packet_cache",
    ):
        assert lookup_fn in function_names, f"expected lookup function {lookup_fn} not found"

    result_dataclass_fields = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name in (
            "IndexCacheResult",
            "QueryCacheResult",
            "PacketCacheResult",
        ):
            fields = {
                stmt.target.id
                for stmt in node.body
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
            }
            result_dataclass_fields[node.name] = fields

    assert set(result_dataclass_fields) == {
        "IndexCacheResult",
        "QueryCacheResult",
        "PacketCacheResult",
    }
    for class_name, fields in result_dataclass_fields.items():
        assert fields == {"status", "reason_code"}, (
            f"{class_name} carries unexpected field(s) beyond status/reason_code: {fields} — "
            f"today's lookup-check return shape must smuggle no validity/freshness verdict"
        )

    # TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS (Architecture-Review-ratified DD4,
    # docs/guidelines/intentional_divergences.md §2.44): the new Level 2
    # retrieval_context_packet_cache_rows table legitimately carries freshness/verification
    # columns (LEVEL2_CACHE_COLUMNS, migration_002_add_level2_tables) -- a schema-only, bounded
    # divergence from this file's own Non-collapse rule Bullet 1, ratified because no
    # check_*/write_* lookup function exists yet for that table (separately guarded by
    # tests/tools/test_retrieval_cache.py::TestLevel2Migrations::
    # test_check_and_write_functions_no_longer_exist_for_the_removed_level2_table). The real rule
    # this test protects -- Bullet 2, no lookup FUNCTION return shape ever carries a freshness/
    # verification verdict -- stays enforced by the three check_*_cache Result dataclass
    # field-set assertions above; narrowed here to every current lookup function's own source.
    # check_provider_result_cache (Level 1's own real lookup function) was briefly in this loop
    # between TCK-20260816 and TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL, which
    # deleted it along with its only production caller -- the loop is back to just the three live,
    # unrelated index/query/packet lookup functions.
    for lookup_fn in (
        "check_index_cache", "check_query_cache", "check_packet_cache",
    ):
        fn_node = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == lookup_fn
        )
        fn_source = (ast.get_source_segment(source, fn_node) or "").lower()
        assert "freshness" not in fn_source
        assert "verification" not in fn_source


# ---------------------------------------------------------------------------
# Test 3 — all 8 evidence identity kinds defined, closed set, identity + fingerprint present
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kind", sorted(_EIGHT_KINDS))
def test_all_eight_evidence_kinds_defined_with_identity_and_fingerprint(kind):
    schema = _load_json(_EVIDENCE_KINDS_SCHEMA)

    enum_values = set(schema["definitions"]["evidence_identity_kind"]["enum"])
    kind_keys = set(schema["kinds"].keys())
    assert enum_values == _EIGHT_KINDS, f"evidence_identity_kind enum is not the closed 8-kind set: {enum_values}"
    assert kind_keys == _EIGHT_KINDS, f"kinds table is not the closed 8-kind set: {kind_keys}"

    entry = schema["kinds"][kind]
    assert isinstance(entry["stable_identity_form"], str) and entry["stable_identity_form"].strip()
    assert isinstance(entry["preferred_fingerprint"], str) and entry["preferred_fingerprint"].strip()


# ---------------------------------------------------------------------------
# Test 4 — normalization rules cover rename/delete/duplicate-name/schema-version-change per kind
# ---------------------------------------------------------------------------

def test_normalization_rules_cover_rename_delete_duplicate_schema_version_change():
    schema = _load_json(_EVIDENCE_KINDS_SCHEMA)
    required_cases = {"rename", "delete", "duplicate_name", "schema_version_change"}

    for kind_name, entry in schema["kinds"].items():
        rules = entry.get("normalization_rules")
        assert rules is not None, f"{kind_name}: missing normalization_rules"
        assert set(rules.keys()) == required_cases, (
            f"{kind_name}: normalization_rules keys {set(rules.keys())} != {required_cases}"
        )
        for case, resolution in rules.items():
            assert isinstance(resolution, str) and len(resolution.strip()) > 10, (
                f"{kind_name}.{case}: resolution is missing or a bare mention: {resolution!r}"
            )


# ---------------------------------------------------------------------------
# Test 5 — PROVIDER_GENERATION is fallback-only (direct AC3 acceptance test)
# ---------------------------------------------------------------------------

def _has_finer_fingerprint(kind: str, kinds_table: dict) -> bool:
    return not kinds_table[kind]["preferred_fingerprint"].startswith("None.")


def _survives_generation_bump(kind: str, kinds_table: dict, old_fingerprint, new_fingerprint, old_generation, new_generation) -> bool:
    """Test-only fixture helper modeling evidence_cache_identity_contract.md §4's documented rule:
    a record with a finer fingerprint is judged solely on that fingerprint; only a record with no
    finer fingerprint (PROVIDER_GENERATION itself) falls back to the generation value.
    """
    if _has_finer_fingerprint(kind, kinds_table):
        return old_fingerprint == new_fingerprint
    return old_generation == new_generation


def test_provider_generation_is_fallback_only_symbol_result_survives_unrelated_generation_bump():
    kinds_table = _load_json(_EVIDENCE_KINDS_SCHEMA)["kinds"]

    contract_text = _IDENTITY_CONTRACT_MD.read_text()
    fallback_section = _section(contract_text, "## 4. Provider-generation fallback rule", "## 5.")
    assert "SYMBOL" in fallback_section and "FILE" in fallback_section
    assert "must never be invalidated" in fallback_section

    # SYMBOL/FILE-backed record: unchanged kind-specific fingerprint, unrelated generation bump.
    for finer_kind in ("SYMBOL", "FILE"):
        assert _has_finer_fingerprint(finer_kind, kinds_table)
        survives = _survives_generation_bump(
            finer_kind,
            kinds_table,
            old_fingerprint="content-hash-abc",
            new_fingerprint="content-hash-abc",
            old_generation="gen-1",
            new_generation="gen-2",
        )
        assert survives is True, f"{finer_kind}-backed record must survive an unrelated generation bump"

    # PROVIDER_GENERATION-only-backed record: no finer fingerprint, IS invalidated by the bump.
    assert not _has_finer_fingerprint("PROVIDER_GENERATION", kinds_table)
    invalidated = _survives_generation_bump(
        "PROVIDER_GENERATION",
        kinds_table,
        old_fingerprint=None,
        new_fingerprint=None,
        old_generation="gen-1",
        new_generation="gen-2",
    )
    assert invalidated is False, "PROVIDER_GENERATION-only-backed record must be invalidated by a generation bump"


# ---------------------------------------------------------------------------
# Test 6 — repository/branch/working-tree cache scope: new commit alone is not a miss,
#          cross-branch reuse is rejected
# ---------------------------------------------------------------------------

def _cache_scope_compatible(cached_scope: dict, current_scope: dict) -> bool:
    """Test-only helper modeling evidence_cache_identity_contract.md §5's documented rules."""
    if cached_scope["repo"] != current_scope["repo"]:
        return False
    if cached_scope["branch"] != current_scope["branch"]:
        return False
    return True


def test_new_commit_alone_is_not_a_cache_miss_but_cross_branch_reuse_is_rejected():
    text = _IDENTITY_CONTRACT_MD.read_text()
    scope_section = _section(text, "## 5. Repository/branch/working-tree cache scope", "## 6.")
    assert "is not automatically a cache miss" in scope_section
    assert "hard partition" in scope_section
    assert "never reused" in scope_section

    same_branch_new_commit = _cache_scope_compatible(
        {"repo": "rpg-based-simulation", "branch": "main", "commit": "aaa111"},
        {"repo": "rpg-based-simulation", "branch": "main", "commit": "bbb222"},
    )
    assert same_branch_new_commit is True

    cross_branch = _cache_scope_compatible(
        {"repo": "rpg-based-simulation", "branch": "feature/x", "commit": "ccc333"},
        {"repo": "rpg-based-simulation", "branch": "main", "commit": "ccc333"},
    )
    assert cross_branch is False


# ---------------------------------------------------------------------------
# Test 7 — changed-paths-intersection working-tree fingerprint approach is documented
# ---------------------------------------------------------------------------

def test_changed_paths_intersected_with_cached_evidence_paths_approach_is_documented():
    text = _IDENTITY_CONTRACT_MD.read_text()
    scope_section = _section(text, "## 5. Repository/branch/working-tree cache scope", "## 6.")

    assert "changed_paths" in scope_section
    assert "intersect" in scope_section.lower()
    assert "hashing the entire working tree" in scope_section
    assert "knowledge_context_request.schema.json" in scope_section

    request_schema = _load_json(_REQUEST_SCHEMA)
    assert request_schema["properties"]["changed_paths"]["type"] == "array"
    assert request_schema["properties"]["changed_paths"]["items"]["type"] == "string"


# ---------------------------------------------------------------------------
# Test 8 — migration design doc declares the scoped schema-version constant, ordered
#          migrations, and a rebuild command (direct AC5 acceptance test)
# ---------------------------------------------------------------------------

def test_migration_design_doc_declares_schema_version_ordered_migrations_and_rebuild_command():
    text = _MIGRATION_PLAN_MD.read_text()

    assert text.count("retrieval_cache_schema_version") >= 5

    sql_fences = re.findall(r"```sql\n(.*?)\n```", text, flags=re.DOTALL)
    own_table_fences = [f for f in sql_fences if "retrieval_cache_generation" in f]
    assert own_table_fences, "no CREATE TABLE fence found for the new schema-version metadata table"
    for fence in own_table_fences:
        assert "retrieval_cache_schema_version" in fence
        bare_hits = re.findall(r"(?<!retrieval_cache_)(?<!retrieval_event_)\bschema_version\b", fence)
        assert not bare_hits, f"bare, ambiguous 'schema_version' used in own table definition: {fence}"

    assert "migration_001_add_level1_tables" in text
    assert "migration_002_add_level2_tables" in text
    assert "rebuild" in text.lower()
    assert "RETRIEVAL_VERSION" in text
    assert "retrieval_event_schema_version" in text


# ---------------------------------------------------------------------------
# Test 9 — migration plan preserves existing marker-only tables; retrieval_cache.py untouched
# ---------------------------------------------------------------------------

def test_migration_plan_preserves_existing_marker_only_tables_and_does_not_edit_retrieval_cache_py():
    plan_text = _MIGRATION_PLAN_MD.read_text()
    for table_name in (
        "retrieval_index_cache_rows",
        "retrieval_query_cache_rows",
        "retrieval_packet_cache_rows",
    ):
        assert table_name in plan_text, f"migration plan must name existing table {table_name}"

    source = _RETRIEVAL_CACHE_PY.read_text()
    for table_name in (
        "retrieval_index_cache_rows",
        "retrieval_query_cache_rows",
        "retrieval_packet_cache_rows",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in source, (
            f"retrieval_cache.py's existing CREATE TABLE statement for {table_name} changed shape "
            f"or was removed — this ticket must not edit tools/retrieval_cache.py"
        )

    tree = ast.parse(source)
    may_list_columns = None
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None) == "MAY_LIST_COLUMNS":
            call = node.value
            set_node = call.args[0]
            may_list_columns = {elt.value for elt in set_node.elts}

    assert may_list_columns == _EXPECTED_MAY_LIST_COLUMNS, (
        "tools/retrieval_cache.py's MAY_LIST_COLUMNS changed — this ticket must not edit "
        "tools/retrieval_cache.py"
    )


# ---------------------------------------------------------------------------
# Test 10 — no migration-library dependency introduced
# ---------------------------------------------------------------------------

def test_no_migration_library_dependency_introduced():
    forbidden = re.compile(r"alembic|yoyo[-_]?migrations|sqlite-migrate", re.IGNORECASE)

    candidates = [
        _REPO_ROOT / "requirements.txt",
        _REPO_ROOT / "requirements-knowledge.txt",
        _REPO_ROOT / "pyproject.toml",
    ]
    for path in candidates:
        if not path.exists():
            continue
        text = path.read_text()
        assert not forbidden.search(text), f"{path} appears to declare a migration-library dependency"

    # The design doc legitimately *names* alembic/yoyo-migrations/sqlite-migrate to document that
    # none is introduced (the same "cite the anti-pattern to rule it out" precedent the sibling
    # ticket's plan.md uses for jsonschema) -- so the doc is checked for that explicit disclaimer,
    # not scanned for the absence of the library names themselves.
    plan_text = _MIGRATION_PLAN_MD.read_text()
    assert "no migration library" in plan_text.lower() or "no migration-library" in plan_text.lower()


# ---------------------------------------------------------------------------
# Test 11 — new evidence-kinds schema file parses and has its own schema_version
# ---------------------------------------------------------------------------

def test_new_schema_file_parses_and_has_own_schema_version():
    assert _EVIDENCE_KINDS_SCHEMA.exists()
    schema = _load_json(_EVIDENCE_KINDS_SCHEMA)
    assert isinstance(schema["schema_version"], int)
    assert schema["schema_version"] == 1
    assert schema["$schema"]
    assert schema["title"]


# ---------------------------------------------------------------------------
# Test 12 — evidence contract references, never redefines, the frozen freshness/verification enums
# ---------------------------------------------------------------------------

def test_evidence_contract_references_not_redefines_frozen_freshness_and_verification_enums():
    enums = _load_json(_SHARED_ENUMS)["definitions"]
    freshness_values = enums["freshness"]["enum"]
    verification_values = enums["verification"]["enum"]

    contract_text = _IDENTITY_CONTRACT_MD.read_text()

    freshness_quoted = "`/`".join(freshness_values)
    verification_quoted = "`/`".join(verification_values)
    assert f"`{freshness_quoted}`" in contract_text, (
        "contract doc's quoted freshness value list has drifted from shared_enums.schema.json"
    )
    assert f"`{verification_quoted}`" in contract_text, (
        "contract doc's quoted verification value list has drifted from shared_enums.schema.json"
    )

    assert "shared_enums.schema.json" in contract_text
    assert '"definitions"' not in contract_text
    assert "\"enum\": [" not in contract_text
