-- Select the art scaler before decoding, using this machine's VA-API codecs.
-- Inactive unless the dedicated YouTube art profile enabled it.
local cpu_graph = "fps=24,scale=-2:540"
local gpu_graph = "fps=24,scale_vaapi=w=-2:h=540"
local supported = {h264=true, vp8=true, mpeg2video=true, vc1=true}

local function active_graph()
    if mp.get_opt("youtube-art-enabled") ~= "yes" then return nil end
    local filters = mp.get_property_native("vf", {})
    if not filters[1] or filters[2] or filters[1].name ~= "lavfi" then return nil end
    local graph = (filters[1].params or {}).graph
    if graph == cpu_graph or graph == gpu_graph then return graph end
end

local function set_graph(graph)
    mp.set_property_native("vf", {{name="lavfi", params={graph=graph}}})
end

mp.add_hook("on_preloaded", 50, function()
    if not active_graph() then return end
    local selected
    for _, track in ipairs(mp.get_property_native("track-list", {})) do
        if track.type == "video" and not track.albumart then
            selected = selected or track
            if track.selected then selected = track; break end
        end
    end
    local hardware = mp.get_property("options/hwdec", "no")
    local output = mp.get_property("options/vo", "")
    if selected and supported[selected.codec] and hardware ~= "no" and output ~= "null" then
        mp.set_property("hwdec", "vaapi")
        set_graph(gpu_graph)
    else
        if hardware ~= "no" then mp.set_property("hwdec", "auto-copy") end
        set_graph(cpu_graph)
    end
end)

local function fallback()
    if active_graph() ~= gpu_graph then return end
    local actual = mp.get_property("hwdec-current")
    if actual == "no" or actual == "" then
        mp.set_property("hwdec", "auto-copy")
        set_graph(cpu_graph)
        mp.msg.info("Using CPU art scaling: native VA-API decoding unavailable")
    end
end

mp.register_event("file-loaded", fallback)
mp.register_event("video-reconfig", fallback)
