#!/bin/bash

# Launch btop in xfce4-terminal with specific dimensions and positioning

TITLE="btop-panel"

# Launch terminal with btop
xfce4-terminal --title="$TITLE" --geometry=78x30 -e "btop" &

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

# btop: bottom-right region (remaining space after pclock and cava)
PCLOCK_HEIGHT=$((SCREEN_HEIGHT * 17 / 100))
CAVA_HEIGHT=$((SCREEN_HEIGHT * 17 / 100))
Y=$((PCLOCK_HEIGHT + CAVA_HEIGHT))
HEIGHT=$((SCREEN_HEIGHT - Y))

# Position window using wmctrl
wmctrl -r "$TITLE" -e "0,$X,$Y,$WIDTH,$HEIGHT"
