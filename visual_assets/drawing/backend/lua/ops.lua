-- Fixed, hash-pinned Aseprite script. Runs inside the bwrap sandbox as /lua/ops.lua.
-- Reads /job/req.json (already validated by adapter.py), writes /job/res.json and,
-- for mutating requests, /job/out.aseprite. No caller-supplied text is ever evaluated.
--
-- Request: { mode = "new"|"edit"|"inspect", width, height, bg, ops = {...},
--            refs = <count of /job/ref<N>.aseprite stamp sources>, frame, region }
-- Every op may carry `layer` (name, default: bottom layer) and `frame` (1-based, default 1).

local MAX_LAYERS, MAX_FRAMES = 16, 16

local function read_all(path)
  local f = assert(io.open(path, "rb"))
  local s = f:read("a")
  f:close()
  return s
end

local req = json.decode(read_all("/job/req.json"))
local res = { ok = false }

local function finish()
  local f = assert(io.open("/job/res.json", "wb"))
  f:write(json.encode(res))
  f:close()
end

local rgba = app.pixelColor.rgba
local function pv(c) return rgba(c[1], c[2], c[3], c[4]) end
local function hex(v)
  return string.format("#%02x%02x%02x%02x",
    app.pixelColor.rgbaR(v), app.pixelColor.rgbaG(v),
    app.pixelColor.rgbaB(v), app.pixelColor.rgbaA(v))
end

local spr, refs = nil, {}

local function find_layer(name)
  if name == nil then return spr.layers[1] end
  for _, l in ipairs(spr.layers) do
    if l.name == name then return l end
  end
  error("no such layer: " .. name)
end

local function check_frame(f)
  f = f or 1
  if f < 1 or f > #spr.frames then error("no such frame: " .. f) end
  return f
end

-- Returns the cel image for (layer, frame), guaranteeing a full-canvas cel at the origin.
local function cel_img(layer, f)
  local cel = layer:cel(f)
  if not cel then
    local img = Image(spr.width, spr.height, ColorMode.RGB)
    return spr:newCel(layer, f, img, Point(0, 0)).image
  end
  local img = cel.image
  if cel.position.x == 0 and cel.position.y == 0
      and img.width == spr.width and img.height == spr.height then
    return img
  end
  local full = Image(spr.width, spr.height, ColorMode.RGB)
  full:drawImage(img, cel.position)
  return spr:newCel(layer, f, full, Point(0, 0)).image
end

local function target(op)
  local layer = find_layer(op.layer)
  local f = check_frame(op.frame)
  return cel_img(layer, f), layer, f
end

local function in_bounds(x, y) return x >= 0 and y >= 0 and x < spr.width and y < spr.height end

local function put(img, x, y, v)
  if not in_bounds(x, y) then error("pixel out of bounds: " .. x .. "," .. y) end
  img:putPixel(x, y, v)
end

local function flatten(f)
  local flat = Image(spr.spec)
  flat:drawSprite(spr, f)
  return flat
end

local function ellipse_hit(px, py, cx, cy, rx, ry)
  local dx, dy = (px + 0.5 - cx) / rx, (py + 0.5 - cy) / ry
  return dx * dx + dy * dy <= 1.0
end

local handlers = {}

function handlers.pixels(op)
  local img = target(op)
  for _, p in ipairs(op.pixels) do put(img, p.x, p.y, pv(p.c)) end
end

function handlers.line(op)
  local img = target(op)
  local v = pv(op.c)
  local x0, y0, x1, y1 = op.x0, op.y0, op.x1, op.y1
  local dx, dy = math.abs(x1 - x0), -math.abs(y1 - y0)
  local sx = x0 < x1 and 1 or -1
  local sy = y0 < y1 and 1 or -1
  local err = dx + dy
  while true do
    put(img, x0, y0, v)
    if x0 == x1 and y0 == y1 then break end
    local e2 = 2 * err
    if e2 >= dy then err = err + dy; x0 = x0 + sx end
    if e2 <= dx then err = err + dx; y0 = y0 + sy end
  end
end

function handlers.rect(op)
  local img = target(op)
  local v = pv(op.c)
  for y = op.y, op.y + op.h - 1 do
    for x = op.x, op.x + op.w - 1 do
      if op.fill or y == op.y or y == op.y + op.h - 1 or x == op.x or x == op.x + op.w - 1 then
        put(img, x, y, v)
      end
    end
  end
end

function handlers.ellipse(op)
  local img = target(op)
  local v = pv(op.c)
  local rx, ry = op.w / 2, op.h / 2
  local cx, cy = op.x + rx, op.y + ry
  for y = op.y, op.y + op.h - 1 do
    for x = op.x, op.x + op.w - 1 do
      local hit = ellipse_hit(x, y, cx, cy, rx, ry)
      if hit and not op.fill then
        hit = not (rx > 1 and ry > 1 and ellipse_hit(x, y, cx, cy, rx - 1, ry - 1))
      end
      if hit then put(img, x, y, v) end
    end
  end
end

function handlers.flood_fill(op)
  local img = target(op)
  if not in_bounds(op.x, op.y) then error("seed out of bounds") end
  local from, to = img:getPixel(op.x, op.y), pv(op.c)
  if from == to then return end
  local stack = { { op.x, op.y } }
  while #stack > 0 do
    local p = table.remove(stack)
    local x, y = p[1], p[2]
    if in_bounds(x, y) and img:getPixel(x, y) == from then
      img:putPixel(x, y, to)
      stack[#stack + 1] = { x + 1, y }
      stack[#stack + 1] = { x - 1, y }
      stack[#stack + 1] = { x, y + 1 }
      stack[#stack + 1] = { x, y - 1 }
    end
  end
end

function handlers.replace_color(op)
  local img = target(op)
  local from, to = pv(op.from), pv(op.to)
  for y = 0, spr.height - 1 do
    for x = 0, spr.width - 1 do
      if img:getPixel(x, y) == from then img:putPixel(x, y, to) end
    end
  end
end

function handlers.outline(op)
  local img = target(op)
  local v = pv(op.c)
  local add = {}
  for y = 0, spr.height - 1 do
    for x = 0, spr.width - 1 do
      if app.pixelColor.rgbaA(img:getPixel(x, y)) == 0 then
        local near = false
        for _, d in ipairs({ { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } }) do
          local nx, ny = x + d[1], y + d[2]
          if in_bounds(nx, ny) and app.pixelColor.rgbaA(img:getPixel(nx, ny)) > 0 then near = true end
        end
        if near then add[#add + 1] = { x, y } end
      end
    end
  end
  for _, p in ipairs(add) do img:putPixel(p[1], p[2], v) end
end

function handlers.silhouette(op)
  local img = target(op)
  for y = 0, spr.height - 1 do
    for x = 0, spr.width - 1 do
      local a = app.pixelColor.rgbaA(img:getPixel(x, y))
      if a > 0 then img:putPixel(x, y, rgba(op.c[1], op.c[2], op.c[3], a)) end
    end
  end
end

function handlers.flip(op)
  local img = target(op)
  local copy = img:clone()
  for y = 0, spr.height - 1 do
    for x = 0, spr.width - 1 do
      local sx, sy = x, y
      if op.axis == "h" then sx = spr.width - 1 - x else sy = spr.height - 1 - y end
      img:putPixel(x, y, copy:getPixel(sx, sy))
    end
  end
end

function handlers.clear(op)
  local img = target(op)
  img:clear()
end

function handlers.grayscale(op)
  local img = target(op)
  for y = 0, spr.height - 1 do
    for x = 0, spr.width - 1 do
      local v = img:getPixel(x, y)
      local r, g, b, a = app.pixelColor.rgbaR(v), app.pixelColor.rgbaG(v),
        app.pixelColor.rgbaB(v), app.pixelColor.rgbaA(v)
      local l = (299 * r + 587 * g + 114 * b + 500) // 1000
      img:putPixel(x, y, rgba(l, l, l, a))
    end
  end
end

function handlers.stamp(op)
  local ref = refs[op.ref]
  if not ref then error("bad stamp source") end
  local img = target(op)
  local rf = op.src_frame or 1
  if rf < 1 or rf > #ref.frames then error("no such source frame: " .. rf) end
  if op.x + ref.width > spr.width or op.y + ref.height > spr.height then
    error("stamp does not fit on the canvas")
  end
  local flat = Image(ref.spec)
  flat:drawSprite(ref, rf)
  img:drawImage(flat, Point(op.x, op.y))
end

function handlers.add_layer(op)
  if #spr.layers >= MAX_LAYERS then error("layer limit reached") end
  for _, l in ipairs(spr.layers) do
    if l.name == op.name then error("layer exists: " .. op.name) end
  end
  local l = spr:newLayer()
  l.name = op.name
end

function handlers.rename_layer(op)
  local l = find_layer(op.layer)
  for _, other in ipairs(spr.layers) do
    if other ~= l and other.name == op.name then error("layer exists: " .. op.name) end
  end
  l.name = op.name
end

function handlers.set_visible(op)
  find_layer(op.layer).isVisible = op.visible
end

function handlers.add_frame(op)
  if #spr.frames >= MAX_FRAMES then error("frame limit reached") end
  if op.copy_from then
    spr:newFrame(check_frame(op.copy_from)) -- copy is inserted right after its source
  else
    spr:newEmptyFrame(#spr.frames + 1)
  end
end

function handlers.set_duration(op)
  spr.frames[check_frame(op.frame)].duration = op.ms / 1000
end

function handlers.add_tag(op)
  if op.from < 1 or op.to < op.from or op.to > #spr.frames then error("bad tag range") end
  local t = spr:newTag(op.from, op.to)
  t.name = op.name
end

function handlers.set_palette(op)
  local pal = spr.palettes[1]
  pal:resize(#op.colors)
  for i, c in ipairs(op.colors) do
    pal:setColor(i - 1, Color { r = c[1], g = c[2], b = c[3], a = c[4] })
  end
end

function handlers.delete_layer(op)
  -- Aseprite itself happily deletes the only layer, leaving a sprite with none.
  if #spr.layers <= 1 then error("cannot delete the last layer") end
  spr:deleteLayer(find_layer(op.layer))
end

function handlers.delete_frame(op)
  -- Likewise for the only frame. Tags spanning the frame shrink natively; a tag fully inside it goes.
  if #spr.frames <= 1 then error("cannot delete the last frame") end
  spr:deleteFrame(check_frame(op.frame))
end

function handlers.resize_canvas(op)
  -- crop() both shrinks and grows the canvas, top-left anchored, but leaves every cel image
  -- as it was, so re-normalise each existing cel to a full-canvas image at the origin.
  spr:crop(Rectangle(0, 0, op.width, op.height))
  for _, l in ipairs(spr.layers) do
    for f = 1, #spr.frames do
      if l:cel(f) then cel_img(l, f) end
    end
  end
end

local function summary()
  local seen, colors, n_colors = {}, {}, 0
  local frames, layers = {}, {}
  for f = 1, #spr.frames do
    local flat = flatten(f)
    local nonempty, h = 0, 2166136261
    for y = 0, spr.height - 1 do
      for x = 0, spr.width - 1 do
        local v = flat:getPixel(x, y)
        h = ((h ~ v) * 16777619) & 0xffffffff
        if app.pixelColor.rgbaA(v) > 0 then
          nonempty = nonempty + 1
          local s = hex(v)
          if not seen[s] then
            seen[s] = true
            n_colors = n_colors + 1
            if #colors < 64 then colors[#colors + 1] = s end
          end
        end
      end
    end
    frames[#frames + 1] = {
      index = f, duration_ms = math.floor(spr.frames[f].duration * 1000 + 0.5),
      nonempty = nonempty, checksum = string.format("%08x", h),
    }
  end
  for _, l in ipairs(spr.layers) do
    local per = {}
    for f = 1, #spr.frames do
      local cel = l:cel(f)
      local n = 0
      if cel then
        for it in cel.image:pixels() do
          if app.pixelColor.rgbaA(it()) > 0 then n = n + 1 end
        end
      end
      per[#per + 1] = n
    end
    layers[#layers + 1] = { name = l.name, visible = l.isVisible, nonempty_by_frame = per }
  end
  local tags = {}
  for _, t in ipairs(spr.tags) do
    tags[#tags + 1] = { name = t.name, from = t.fromFrame.frameNumber, to = t.toFrame.frameNumber }
  end
  local pal = {}
  local p = spr.palettes[1]
  for i = 0, math.min(#p, 64) - 1 do pal[#pal + 1] = hex(p:getColor(i).rgbaPixel) end
  res.width, res.height = spr.width, spr.height
  res.frames, res.layers, res.tags = frames, layers, tags
  res.palette, res.palette_size = pal, #p
  res.colors, res.n_colors = colors, n_colors
  res.nonempty_pixels = frames[1].nonempty
end

local ok, err = pcall(function()
  if req.mode == "new" then
    spr = Sprite(req.width, req.height)
    spr.layers[1].name = "base"
    if req.bg then spr.cels[1].image:clear(pv(req.bg)) end
  else
    spr = Sprite { fromFile = "/job/in.aseprite" }
  end
  if spr.colorMode ~= ColorMode.RGB then error("only RGB sprites are supported") end
  for _, l in ipairs(spr.layers) do
    if l.isGroup then error("layer groups are not supported") end
  end
  for i = 1, (req.refs or 0) do
    local r = Sprite { fromFile = "/job/ref" .. i .. ".aseprite" }
    if r.colorMode ~= ColorMode.RGB then error("only RGB sprites are supported") end
    refs[i] = r
  end

  for i, op in ipairs(req.ops or {}) do
    local h = handlers[op.op]
    if not h then error("unknown op: " .. tostring(op.op)) end
    local ok2, e2 = pcall(h, op)
    if not ok2 then error("op " .. i .. " (" .. op.op .. "): " .. tostring(e2)) end
  end

  summary()

  if req.mode == "inspect" and req.region then
    local r = req.region
    local f = check_frame(req.frame)
    local flat = flatten(f)
    local rows = {}
    for y = r.y, r.y + r.h - 1 do
      local row = {}
      for x = r.x, r.x + r.w - 1 do
        row[#row + 1] = in_bounds(x, y) and hex(flat:getPixel(x, y)) or "oob"
      end
      rows[#rows + 1] = row
    end
    res.region = rows
  end

  if req.mode ~= "inspect" then spr:saveAs("/job/out.aseprite") end
end)

res.ok = ok
if not ok then res.error = tostring(err) end
finish()
