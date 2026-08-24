from pathlib import Path

# Static guard for TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD: the tickets/artifacts/
# agent-monitoring plugin-content-docs instances were removed entirely (not just metadata-disabled)
# to shrink the public Docusaurus build, and the docs preset's exclude list was expanded to drop
# archive/plans/audits. Follows the tests/static/test_deploy_docs_heap_limit.py precedent: parse
# the raw source as text, never require()/node -e it -- @easyops-cn/docusaurus-search-local isn't
# installed in this worktree (no website/node_modules/), so the config can't be evaluated here.

_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_PATH = _ROOT / "website" / "docusaurus.config.js"
_INDEX_PAGE_PATH = _ROOT / "website" / "src" / "pages" / "index.js"

_REMOVED_SIDEBAR_FILES = [
    _ROOT / "website" / "sidebars-tickets.js",
    _ROOT / "website" / "sidebars-artifacts.js",
    _ROOT / "website" / "sidebars-agent-monitoring.js",
]

_APPROVED_KEEP_FOLDERS = [
    "agent-monitoring",
    "ai",
    "architecture",
    "cognition",
    "combat",
    "compliance",
    "content",
    "core",
    "engine",
    "event_ledger",
    "guidelines",
    "guides",
    "mechanics",
    "observability",
    "performance",
    "simulation",
    "simulation_quality",
    "strategy",
    "systems",
    "testing",
    "visual_quality",
    "world",
]


def _config_text():
    return _CONFIG_PATH.read_text()


def test_tickets_artifacts_agent_monitoring_plugins_removed():
    text = _config_text()
    assert "id: 'tickets'" not in text
    assert "id: 'artifacts'" not in text
    assert "id: 'agent-monitoring'" not in text


def test_docs_preset_unchanged_and_present():
    text = _config_text()
    assert "path: '../docs'" in text
    assert "routeBasePath: 'docs'" in text
    assert "showLastUpdateTime: true" in text
    assert "showLastUpdateAuthor: true" in text


def test_docs_exclude_list_covers_approved_exclusions_only():
    text = _config_text()
    start = text.index("exclude: [")
    end = text.index("]", start)
    exclude_block = text[start:end]

    for expected in [
        "superpowers/**",
        "specs/**",
        "parity_ledger/**",
        "scenarios/**",
        "entity/**",
        "archive/**",
        "plans/**",
        "audits/**",
        "optimization_audit_ledger.md",
    ]:
        assert expected in exclude_block, f"{expected!r} missing from docs preset exclude list"

    for approved in _APPROVED_KEEP_FOLDERS:
        assert f"'{approved}/**'" not in exclude_block, (
            f"approved-subset folder {approved!r} must not be excluded from the docs preset"
        )


def test_navbar_and_search_theme_no_longer_reference_removed_routes():
    text = _config_text()
    assert "/tickets/" not in text
    assert "/artifacts/" not in text
    assert "/agent-monitoring/" not in text

    start = text.index("docsRouteBasePath: [")
    end = text.index("]", start)
    route_base_path_block = text[start:end]
    assert "'docs'" in route_base_path_block
    assert "tickets" not in route_base_path_block
    assert "artifacts" not in route_base_path_block
    assert "agent-monitoring" not in route_base_path_block


def test_removed_sidebar_files_deleted():
    for path in _REMOVED_SIDEBAR_FILES:
        assert not path.exists(), f"{path} should have been deleted"


def test_homepage_no_longer_references_ticket_artifact_counts():
    text = _INDEX_PAGE_PATH.read_text()
    assert "closed tickets" not in text
    assert "artifact sets" not in text
