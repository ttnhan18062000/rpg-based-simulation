"""Tests for tools/gate_checks/architecture_reviewer_static.py
(TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER).

Coverage-honesty requirement (per test_plan.md): every check function below has at least one
fixture proving it catches a real violation it claims to catch, and at least one negative control
proving it does not false-positive on the codebase's own known-legitimate patterns. Several tests
exist specifically to keep an in-docstring precision/recall caveat honest, not merely to prove the
function runs.

No pytest marker — must not be discovered by `pytest tests/ -m "architecture"` / `make
lane-architecture` (that lane guards `src/` architecture, a different domain from this
agent-workflow-hygiene module).
"""

import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks import architecture_reviewer_static as module  # noqa: E402
from gate_checks.architecture_reviewer_static import (  # noqa: E402
    check_api_boundary_exposure,
    check_durable_state_mutation,
    check_reason_metadata_smuggling,
    run_architecture_checks,
)

_MODULE_PATH = Path(module.__file__)


# ---------------------------------------------------------------------------
# 1. Durable-state-mutation check
# ---------------------------------------------------------------------------


def test_flags_setattr_bypass_outside_allowlist_on_non_cache_field():
    source = (
        "def mutate(entity, new_combat):\n"
        '    object.__setattr__(entity, "combat", new_combat)\n'
    )
    status, evidence = check_durable_state_mutation("src/systems/cheater.py", source)
    assert status == "FAIL"
    assert "combat" in evidence


def test_does_not_flag_cache_suffix_setattr():
    # Mirrors the real src/engine/apply.py replace() idiom — the dominant real-world pattern
    # investigation.md found; the single most important false-positive regression guard here.
    source = (
        "def replace(obj):\n"
        "    res = object.__new__(obj.__class__)\n"
        '    object.__setattr__(res, "_spatial_grid_cache", None)\n'
        "    return res\n"
    )
    status, evidence = check_durable_state_mutation("src/engine/apply.py", source)
    assert status == "PASS"


def test_does_not_flag_allowlisted_call_site_outside_src_engine():
    # Mirrors the real src/world/environment.py:87 pattern: a _cache-suffixed object.__setattr__
    # on AuthoritativeState from a file entirely outside src/engine/. Proves the check uses only
    # field-name/allowlist logic, never a directory-prefix test (src/engine/authoritative_pipeline*
    # does not exist as a real path).
    source = (
        "def populate_cache(state, strongholds):\n"
        "    try:\n"
        '        object.__setattr__(state, "_strongholds_cache", strongholds)\n'
        "    except AttributeError:\n"
        "        pass\n"
    )
    status, evidence = check_durable_state_mutation("src/world/environment.py", source)
    assert status == "PASS"


def test_flags_mutable_container_mutation_by_known_field_name():
    # The highest-value, hardest-to-catch real violation surface: frozen dataclasses block
    # rebinding their own fields but not mutation of a mutable object a field already points to.
    # This is a name-heuristic match, not a type-resolved one — the evidence text must say so.
    source = (
        "def leak(entity, x):\n"
        "    entity.inventory.items.append(x)\n"
        "\n"
        "def leak_dict(state):\n"
        '    state.global_resources["gold"] = 5\n'
    )
    status, evidence = check_durable_state_mutation("src/systems/leaky.py", source)
    assert status == "FAIL"
    assert "name-heuristic" in evidence
    assert "items" in evidence
    assert "global_resources" in evidence


def test_does_not_crash_on_unrelated_attribute_with_same_name():
    # Documents a known, accepted false-positive limitation: name-only matching cannot distinguish
    # entity.inventory.items from an unrelated object's .items attribute. This test exists so a
    # future "fix" to the heuristic cannot silently pass without this test (and the docstring
    # caveat it protects) being revisited too.
    source = (
        "def touch(some_other_object, x):\n"
        "    some_other_object.items.append(x)\n"
    )
    status, evidence = check_durable_state_mutation("src/somewhere/unrelated.py", source)
    assert status == "FAIL"


def test_direct_attribute_assignment_on_frozen_field_is_flagged():
    # entity.combat.hp = 5 (no object.__setattr__) would already raise FrozenInstanceError at
    # runtime on a real frozen dataclass — this check's value is catching it before a test run.
    source = (
        "def cheat(entity):\n"
        "    entity.combat.hp = 5\n"
    )
    status, evidence = check_durable_state_mutation("src/somewhere/cheat.py", source)
    assert status == "FAIL"
    assert "FrozenInstanceError" in evidence


def test_does_not_flag_mock_return_value_configuration():
    # Confirmed real production pattern (src/lab/workflows.py: MagicMock configuration via
    # `mock_world_repo.list_worlds.return_value = [...]`) matches the same depth>=2 attribute-chain
    # shape as `entity.combat.hp = 5` — must not be flagged, per the narrow
    # _MOCK_CONFIGURATION_ATTRS exception discovered at implementation time.
    source = (
        "def _validate_scenario(self, spec):\n"
        "    mock_world_repo = MagicMock()\n"
        "    mock_world_repo.list_worlds.return_value = [spec.world_id]\n"
        "    mock_world_repo.load_world.return_value = spec\n"
    )
    status, evidence = check_durable_state_mutation("src/lab/workflows.py", source)
    assert status == "PASS"


def test_tolerates_unparseable_python_fixture():
    status, evidence = check_durable_state_mutation("src/broken.py", "def broken(:\n    pass")
    assert status == "SKIP"
    assert "unparseable" in evidence.lower()


def test_module_has_no_authoritative_pipeline_path_reference():
    # Guards against a future edit reintroducing the ticket's original (confirmed-wrong)
    # src/engine/authoritative_pipeline* path assumption as an actual path check. Disclosure prose
    # in the module's own top docstring is allowed to *name* the nonexistent path to explain why
    # the check is field-name-based instead — what must never appear is that path used as a real
    # startswith/glob test in executable code (or any function docstring below it).
    source = _MODULE_PATH.read_text(encoding="utf-8")
    _, _, body = source.partition('"""')
    _, _, body = body.partition('"""')  # drop the module docstring itself
    assert "authoritative_pipeline" not in body


# ---------------------------------------------------------------------------
# 2. Raw-domain-object API-boundary check
# ---------------------------------------------------------------------------


def test_flags_route_returning_raw_domain_model_directly():
    source = (
        "def get_entity(entity_id: str) -> EntityState:\n"
        "    ...\n"
    )
    status, evidence = check_api_boundary_exposure(
        "src/api/routes/entities.py", source, {"EntityState", "AuthoritativeState", "RegionState"}
    )
    assert status == "FAIL"
    assert "EntityState" in evidence


def test_does_not_flag_presenter_or_response_return_types():
    # Encodes the confirmed real convention: raw type as input, Dict/*Response as output.
    source = (
        "def present_entity(entity: EntityState) -> Dict[str, Any]:\n"
        "    ...\n"
        "\n"
        "def get_history(campaign_id: str) -> CampaignHistoryResponse:\n"
        "    ...\n"
    )
    status, evidence = check_api_boundary_exposure(
        "src/api/presenters/state_presenter.py", source, {"EntityState"}
    )
    assert status == "PASS"


def test_does_not_flag_private_helper_returning_raw_model():
    # Mirrors the real src/api/routes/decisions.py:_get_index(...) -> DecisionTraceIndex shape —
    # a leading-underscore internal helper, never a registered route handler.
    source = (
        "def _get_index(run_id: str) -> DecisionTraceIndex:\n"
        "    ...\n"
    )
    status, evidence = check_api_boundary_exposure(
        "src/api/routes/decisions.py", source, {"DecisionTraceIndex"}
    )
    assert status != "FAIL"


def test_does_not_flag_or_crash_on_unannotated_handler():
    source = (
        "async def get_x(request):\n"
        "    return {}\n"
    )
    status, evidence = check_api_boundary_exposure("src/api/routes/x.py", source, set())
    assert status == "SKIP"
    assert "no return annotation" in evidence


# ---------------------------------------------------------------------------
# 3. Reason/metadata-smuggling regex check
# ---------------------------------------------------------------------------


def test_flags_delimiter_joined_reason_field():
    # Rule-derived, not incident-derived: investigation.md found zero real historical instances of
    # this exact pattern anywhere in this repo's history (git log, tickets/done/, docs/archive/,
    # and all 31 recorded NEEDS_CHANGES/BLOCKED architecture-review verdicts).
    source = (
        "def build(cause, severity, actor_id):\n"
        '    reason = f"{cause}|{severity}|{actor_id}"\n'
        "    return reason\n"
        "\n"
        "def consume(packed):\n"
        '    cause, severity, actor_id = packed.split("|")\n'
        "    return cause, severity, actor_id\n"
    )
    status, evidence = check_reason_metadata_smuggling("src/somewhere/pack.py", source)
    assert status == "FAIL"


def test_does_not_flag_plain_human_readable_reason_string():
    # The real, confirmed-clean pattern at src/lab/workflows.py:1176 — a single interpolated
    # diagnostic value, not durable meaning packed for later parsing.
    source = (
        "def handle(e):\n"
        '    return {"status": "BLOCKED", "reason": f"Malformed or unparseable run manifest: {e}"}\n'
    )
    status, evidence = check_reason_metadata_smuggling("src/lab/workflows.py", source)
    assert status == "PASS"


def test_docstring_discloses_no_incident_corpus():
    # Prevents a future edit from silently strengthening this check's claimed evidence base
    # without also updating this test.
    doc = (check_reason_metadata_smuggling.__doc__ or "").lower()
    assert "zero confirmed historical incidents" in doc


# ---------------------------------------------------------------------------
# 4. Aggregation / schema-shape parity with siblings
# ---------------------------------------------------------------------------


def test_run_all_returns_list_of_condition_status_evidence_dicts(tmp_path):
    (tmp_path / "src" / "core").mkdir(parents=True)
    (tmp_path / "src" / "core" / "foo.py").write_text("def ok():\n    pass\n")
    (tmp_path / "src" / "api").mkdir(parents=True)
    (tmp_path / "src" / "api" / "bar.py").write_text(
        "def get_bar() -> Dict[str, Any]:\n    ...\n"
    )

    results = run_architecture_checks(
        ["src/core/foo.py", "src/api/bar.py", "docs/readme.md", "tests/unit/test_foo.py"],
        base_dir=tmp_path,
    )

    assert isinstance(results, list)
    assert len(results) > 0
    for r in results:
        assert isinstance(r, dict)
        assert set(r.keys()) == {"condition", "status", "evidence"}
        assert r["status"] in {"PASS", "FAIL", "SKIP"}

    conditions = {r["condition"] for r in results}
    assert any(c.startswith("durable_state_mutation:src/core/foo.py") for c in conditions)
    assert any(c.startswith("api_boundary_exposure:src/api/bar.py") for c in conditions)
    # docs/tests paths must never produce a condition entry.
    assert not any("readme.md" in c or "test_foo.py" in c for c in conditions)
