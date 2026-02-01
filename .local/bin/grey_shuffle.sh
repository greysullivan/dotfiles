#!/bin/bash
#################################
#   grey-manjarov1 Window Shuffle
#   Quarter/quadrant cycling (50% x 50%)
#################################

# Window gap size in pixels
GAP=10

# Get active window ID
get_active_window() {
    xdotool getactivewindow
}

# Get screen dimensions
get_screen_dimensions() {
    xdpyinfo | grep dimensions | awk '{print $2}'
}

# Parse width and height
parse_dimensions() {
    # Get actual workarea (usable screen space after panels)
    local workarea=$(xprop -root _NET_WORKAREA | awk '{print $3, $4, $5, $6}' | tr -d ',')
    local wa_array=($workarea)

    # Workarea format: x_offset, y_offset, width, height
    local x_offset=${wa_array[0]}
    local y_offset=${wa_array[1]}
    SCREEN_WIDTH=${wa_array[2]}
    SCREEN_HEIGHT=${wa_array[3]}

    # Use full workarea height (no manual panel adjustment needed)
    USABLE_HEIGHT=$SCREEN_HEIGHT

    # Calculate quarter dimensions with gaps
    # Each quarter gets: (total - 3*gap) / 2
    # This creates: gap | quarter | gap | quarter | gap
    QUARTER_WIDTH=$(( (SCREEN_WIDTH - GAP * 3) / 2 ))
    QUARTER_HEIGHT=$(( (USABLE_HEIGHT - GAP * 3) / 2 ))
}

# Detect current quadrant based on window position and size
detect_quadrant() {
    local window_id=$1
    local geom=$(xdotool getwindowgeometry $window_id)

    # Extract X and Y position
    local x=$(echo "$geom" | grep "Position" | awk '{print $2}' | cut -d',' -f1)
    local y=$(echo "$geom" | grep "Position" | awk '{print $2}' | cut -d',' -f2)

    # Extract width and height
    local w=$(echo "$geom" | grep "Geometry" | awk '{print $2}' | cut -d'x' -f1)
    local h=$(echo "$geom" | grep "Geometry" | awk '{print $2}' | cut -d'x' -f2)

    # Remove whitespace
    x=$(echo $x | tr -d ' ')
    y=$(echo $y | tr -d ' ')
    w=$(echo $w | tr -d ' ')
    h=$(echo $h | tr -d ' ')

    parse_dimensions

    local mid_x=$((SCREEN_WIDTH / 2))
    local mid_y=$((USABLE_HEIGHT / 2))

    # Check if window is roughly quarter-sized (within 10% tolerance)
    local expected_w=$QUARTER_WIDTH
    local expected_h=$QUARTER_HEIGHT
    local w_diff=$((w - expected_w))
    local h_diff=$((h - expected_h))

    # Use absolute values
    [ $w_diff -lt 0 ] && w_diff=$((-w_diff))
    [ $h_diff -lt 0 ] && h_diff=$((-h_diff))

    local tolerance_w=$((expected_w / 10))
    local tolerance_h=$((expected_h / 10))

    # Determine quadrant based on position
    if [ $x -lt $mid_x ] && [ $y -lt $mid_y ]; then
        echo "top-left"
    elif [ $x -ge $((mid_x - 100)) ] && [ $y -lt $mid_y ]; then
        echo "top-right"
    elif [ $x -ge $((mid_x - 100)) ] && [ $y -ge $((mid_y - 100)) ]; then
        echo "bottom-right"
    elif [ $x -lt $mid_x ] && [ $y -ge $((mid_y - 100)) ]; then
        echo "bottom-left"
    else
        # Default to top-left if uncertain
        echo "top-left"
    fi
}

# Move window to specific quadrant
move_to_quadrant() {
    local window_id=$1
    local quadrant=$2

    parse_dimensions

    case $quadrant in
        "top-left")
            wmctrl -i -r $window_id -e 0,$GAP,$GAP,$QUARTER_WIDTH,$QUARTER_HEIGHT
            ;;
        "top-right")
            wmctrl -i -r $window_id -e 0,$((QUARTER_WIDTH + GAP * 2)),$GAP,$QUARTER_WIDTH,$QUARTER_HEIGHT
            ;;
        "bottom-right")
            wmctrl -i -r $window_id -e 0,$((QUARTER_WIDTH + GAP * 2)),$((QUARTER_HEIGHT + GAP * 2)),$QUARTER_WIDTH,$QUARTER_HEIGHT
            ;;
        "bottom-left")
            wmctrl -i -r $window_id -e 0,$GAP,$((QUARTER_HEIGHT + GAP * 2)),$QUARTER_WIDTH,$QUARTER_HEIGHT
            ;;
    esac
}

# Cycle through quadrants (forward: TL → TR → BR → BL)
cycle_forward() {
    local window_id=$(get_active_window)
    local current_quad=$(detect_quadrant $window_id)

    case $current_quad in
        "top-left")
            move_to_quadrant $window_id "top-right"
            ;;
        "top-right")
            move_to_quadrant $window_id "bottom-right"
            ;;
        "bottom-right")
            move_to_quadrant $window_id "bottom-left"
            ;;
        "bottom-left")
            move_to_quadrant $window_id "top-left"
            ;;
    esac
}

# Cycle through quadrants (reverse: BL → BR → TR → TL)
cycle_reverse() {
    local window_id=$(get_active_window)
    local current_quad=$(detect_quadrant $window_id)

    case $current_quad in
        "top-left")
            move_to_quadrant $window_id "bottom-left"
            ;;
        "bottom-left")
            move_to_quadrant $window_id "bottom-right"
            ;;
        "bottom-right")
            move_to_quadrant $window_id "top-right"
            ;;
        "top-right")
            move_to_quadrant $window_id "top-left"
            ;;
    esac
}

# Slide window horizontally left (keep size)
slide_left() {
    local window_id=$(get_active_window)
    local geom=$(xdotool getwindowgeometry $window_id)

    # Get current position and size
    local pos=$(echo "$geom" | grep "Position" | awk '{print $2}')
    local size=$(echo "$geom" | grep "Geometry" | awk '{print $2}')

    local x=$(echo $pos | cut -d',' -f1 | tr -d ' ')
    local y=$(echo $pos | cut -d',' -f2 | tr -d ' ')
    local w=$(echo $size | cut -d'x' -f1 | tr -d ' ')
    local h=$(echo $size | cut -d'x' -f2 | tr -d ' ')

    parse_dimensions

    # Move one quarter width left
    local new_x=$((x - QUARTER_WIDTH))

    # Clamp to screen bounds
    if [ $new_x -lt 0 ]; then
        new_x=0
    fi

    wmctrl -i -r $window_id -e 0,$new_x,$y,$w,$h
}

# Slide window horizontally right (keep size)
slide_right() {
    local window_id=$(get_active_window)
    local geom=$(xdotool getwindowgeometry $window_id)

    # Get current position and size
    local pos=$(echo "$geom" | grep "Position" | awk '{print $2}')
    local size=$(echo "$geom" | grep "Geometry" | awk '{print $2}')

    local x=$(echo $pos | cut -d',' -f1 | tr -d ' ')
    local y=$(echo $pos | cut -d',' -f2 | tr -d ' ')
    local w=$(echo $size | cut -d'x' -f1 | tr -d ' ')
    local h=$(echo $size | cut -d'x' -f2 | tr -d ' ')

    parse_dimensions

    # Move one quarter width right
    local new_x=$((x + QUARTER_WIDTH))

    # Clamp to screen bounds
    local max_x=$((SCREEN_WIDTH - w))
    if [ $new_x -gt $max_x ]; then
        new_x=$max_x
    fi

    wmctrl -i -r $window_id -e 0,$new_x,$y,$w,$h
}

# Main
case "$1" in
    "forward")
        cycle_forward
        ;;
    "reverse")
        cycle_reverse
        ;;
    "slide-left")
        slide_left
        ;;
    "slide-right")
        slide_right
        ;;
    *)
        echo "Usage: $0 {forward|reverse|slide-left|slide-right}"
        echo ""
        echo "Quadrant layout (quarters - 50% x 50%):"
        echo "┌───────┬───────┐"
        echo "│  TL   │  TR   │  TL = Top-Left"
        echo "│   1   │   2   │  TR = Top-Right"
        echo "├───────┼───────┤  BR = Bottom-Right"
        echo "│  BL   │  BR   │  BL = Bottom-Left"
        echo "│   4   │   3   │"
        echo "└───────┴───────┘"
        echo ""
        echo "forward: TL → TR → BR → BL → TL"
        echo "reverse: BL → BR → TR → TL → BL"
        exit 1
        ;;
esac
