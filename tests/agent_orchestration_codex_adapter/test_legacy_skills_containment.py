from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
ARCHIVE = ROOT / "docs" / "archive" / "legacy_agents_skills_20260722"
EXPECTED = {'api-design-principles': '6976b00b76f20eb60c71a4f18cc5b5c0f58820ce53755b34cc84dc1cbc57591e', 'architecture': '4fd06e457ca7460ef7378a475466008777d608583d38f385c25840f165c47780', 'backend-testing': '91eb6da411be4897aafa9c97f7ec5ce98a1d753b8ca9ed2f0dda4997be9c0113', 'brainstorming': '58353e42ac33396a4b3cc62e69df35f3d3f1d18e60877bf39d492c77dc6a928d', 'clean-code': '1fb4423ab58110e5623d4e84d61e38f66a00fdfab313c13969067c67f952f0aa', 'code-review': '95b1d9c73416f671f2b98f21533ed0541ef58794276990d65f0824bccce683e9', 'codebase-search': '70c1ee665783cb84b761b7bfc4ba1354b11e0bae8ba68416401d362ffabe8b57', 'create-skill': 'a88f91120ab81eb6b63ee384d94ecf62bd5eefafeb32ed14b4c301d74ef25e40', 'debugging-strategies': 'f7361b6e479a148fa609aa2b0c377fd09ed254985aa5763f509be38f7e7e9c0d', 'doc-coauthoring': '2e47d78846faeea4a56e9809c52700087a15a2155a3f293a3efbaded81398ef4', 'frontend-design': 'b81e2ff87ed8fa4d6c377ccb127a7254c9e6a77e3ae94f21e6b514f7bb2945a0', 'graphify': 'a1b301b87129c4e9956de8971d229344afc6400c92fca5f2508a40479e475f59', 'prompt-builder': 'cebe1f7e1670ccf815073e66dcba417cd182154f2acf052788d6b67d6c773956', 'python-performance-optimization': '59efa705313676ffe0f4411a14a41133185bb2cd027cb73a8c866020aaa58b16', 'python-testing-patterns': '615b0a57fbac0f1f32eb0fca118a28229d7a4e35e23184b8d25346f3586aeeec', 'receiving-code-review': 'c9382e92b8f32363566068ecfed19d3b2651eaf40d3942b24840f839dedfc406', 'requesting-code-review': 'a5ff68586ccf62d1803cedeb71d60fd96ec05591d29c8d123196117eefd34cd0', 'test-driven-development': '7dee67b4af6bdccc7a914ca34533184d64592d0f5b23aeae631538168db14994'}

def _digest(path): return sha256(path.read_bytes()).hexdigest()

def test_live_catalog_contains_no_archived_legacy_skill_content():
    live = {_digest(p) for p in (ROOT / ".agents" / "skills").glob("*/SKILL.md")}
    assert not live.intersection(EXPECTED.values())

def test_archived_copy_is_byte_identical():
    assert {name: _digest(ARCHIVE / name / "SKILL.md") for name in EXPECTED} == EXPECTED

def test_archive_is_outside_agents_skills_discovery_path():
    assert not any(parent.name == "skills" and parent.parent.name == ".agents" for parent in [ARCHIVE, *ARCHIVE.parents])
