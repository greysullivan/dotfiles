#!/bin/bash

# Launch pclock in xfce4-terminal with specific dimensions and positioning

TITLE="pclock-panel"

# Launch terminal with pclock
xfce4-terminal --title="$TITLE" --geometry=39x11 -e "pclock" &

# Wait for window to appear
sleep 0.5
for i in {1..20}; do
    if wmctrl -l | grep -q "$TITLE"; then
        break
    fi
    sleep 0.1
done

# Get screen dimensions
SCREEN_WIDTH=$(xdpyinfo | grep dimensions | awk '{print $2}' | cut -d'x' -f1)
SCREEN_HEIGHT=$(xdpyinfo | grep dimensions | awk '{print $2}' | cut -d'x' -f2)

# Calculate right half dimensions
X=$((SCREEN_WIDTH / 2))
WIDTH=$((SCREEN_WIDTH / 2))

# pclock: top-right strip (17% of screen height)
Y=0
HEIGHT=$((SCREEN_HEIGHT * 17 / 100))

# Position window using wmctrl
wmctrl -r "$TITLE" -e "0,$X,$Y,$WIDTH,$HEIGHT"
