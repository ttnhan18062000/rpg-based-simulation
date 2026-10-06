"""Read-only render-match check of a draft set: the same function `adopt-set` calls (rendering.compare_preview, with the store's own sandboxed Aseprite renderer), run on every entry.
Adopts nothing and writes nothing. An entry passes when the verdict is MATCH and rendered_pixel_hash equals the entry's pixel_hash (adopt-set's own condition). Usage: python render_match_check.py [set_id]"""
import sys
from visual_assets.store import drafts
from visual_assets.store.build import exporter
from visual_assets.store.contracts.review import RenderVerdict
from visual_assets.store import rendering

set_id = sys.argv[1] if len(sys.argv) > 1 else "terrain-v1"
renderer = exporter.default_renderer()
assert renderer is not None, "no Aseprite renderer on this machine"
record, _ = drafts.load_set(set_id)
bad = 0
print(f"set {set_id}: {len(record.entries)} entries, renderer {renderer.tool_name} {renderer.tool_version}")
for entry in record.entries:
    files = drafts.read_entry(set_id, entry)
    cmp = rendering.compare_preview(intake_id=entry.draft_id, source=files.source, preview=files.preview, tool=renderer, created_at="2026-10-06T00:00:00Z")
    ok = cmp.check.verdict is RenderVerdict.MATCH and cmp.check.rendered_pixel_hash == entry.pixel_hash
    bad += not ok
    slot = entry.visual_key + (f"[{entry.detail}]" if entry.detail else "")
    print(f"{'OK  ' if ok else 'FAIL'} {slot:34s} {entry.draft_id} verdict={cmp.check.verdict.value} scale={cmp.check.scale} rendered={cmp.check.rendered_pixel_hash} entry={entry.pixel_hash}")
print("ALL MATCH" if not bad else f"{bad} MISMATCH")
sys.exit(1 if bad else 0)
