-- Prevent cava terminal from staying on top
if (get_window_role() == "cava-terminal") then
    set_window_above(false)
end

-- Remove border from cava-float
if (get_window_class() == "cava-float") or (get_window_name():find("cava-float")) then
    undecorate_window()
end
