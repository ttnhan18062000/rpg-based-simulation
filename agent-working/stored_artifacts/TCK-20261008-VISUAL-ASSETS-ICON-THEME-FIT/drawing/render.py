from PIL import Image
def render(items, path, scale=6, cols=6, gap=6):
    """items: list of (name, Canvas). Each drawn on a dark and a light panel side by side."""
    cell = max(c.w for _, c in items) * scale + gap
    rows = (len(items) + cols - 1) // cols
    img = Image.new("RGB", (cols * 2 * cell, rows * cell), (60, 60, 60))
    for i, (name, c) in enumerate(items):
        ox, oy = (i % cols) * 2 * cell, (i // cols) * cell
        for bg, off in (((17, 24, 39), 0), ((229, 231, 235), cell)):
            for y in range(cell):
                for x in range(cell): img.putpixel((ox + off + x, oy + y), bg)
            for (x, y), col in c.px.items():
                rgb = tuple(int(col[k:k + 2], 16) for k in (1, 3, 5))
                for dy in range(scale):
                    for dx in range(scale): img.putpixel((ox + off + gap // 2 + x * scale + dx, oy + gap // 2 + y * scale + dy), rgb)
    img.save(path)
