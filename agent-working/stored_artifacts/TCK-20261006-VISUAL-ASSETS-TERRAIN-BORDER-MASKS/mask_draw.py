"""Draw the nine border masks through the drawing library and package each as a handoff. Prints one JSON line per mask: {"key", "detail", "handoff_dir"}.
Sprites are tmask_<kind>_<variant>. The shape colour is a neutral grey (never shown: the client draws the neighbour's tile pixels where the mask is opaque)."""
import json
import mask_generator as m
from visual_assets.drawing import api, handoff

for (kind, variant), pixels in sorted(m.masks().items()):
    sprite = f"tmask_{kind}_{variant}"
    first = api.new_sprite(sprite, m.SIZE, m.SIZE)  # transparent background
    px = [{"x": x, "y": y, "color": "#c0c0c0"} for x, y in sorted(pixels, key=lambda p: (p[1], p[0]))]
    rev = api.apply_ops(sprite, first["revision"], [{"op": "pixels", "pixels": px}])["revision"]
    out = handoff.build_handoff(
        sprite, rev, licence_state="UNREVIEWED", licence_evidence_ref="UNAVAILABLE", brief_id=f"terrain-v1-border-{kind.replace('_', '-')}-{variant}",
        review_evidence_ref="NOT_APPLICABLE",
        limitations=[f"border mask border.{kind} {variant}: 1-bit alpha shape authored for one orientation, depth within 4 px; the client rotates it and shows the higher neighbour's tile pixels where it is opaque"])
    print(json.dumps({"key": f"border.{kind}", "detail": variant, "handoff_dir": out["directory"]}), flush=True)
