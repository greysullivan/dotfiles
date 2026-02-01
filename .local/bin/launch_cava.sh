#!/bin/bash

# Launch cava in xfce4-terminal with specific dimensions and positioning

TITLE="cava-panel"

# Launch terminal with cava (hide all UI elements, disable server for independent window)
xfce4-terminal --disable-server --title="$TITLE" --geometry=37x11 --hide-menubar --hide-scrollbar --hide-borders -e "cava" &

# Wait for window to appear (match more flexibly on "cava")
sleep 0.5
for i in {1..20}; do
    if wmctrl -l | grep -qi "cava"; then
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

# cava: middle-right strip (17% of screen height, starting after pclock)
PCLOCK_HEIGHT=$((SCREEN_HEIGHT * 17 / 100))
Y=$PCLOCK_HEIGHT
HEIGHT=$((SCREEN_HEIGHT * 17 / 100))

# Position window using wmctrl (match by cava in title)
wmctrl -r "cava" -e "0,$X,$Y,$WIDTH,$HEIGHT"

# Wait a moment for window to be fully positioned
sleep 0.2

# Remove window decorations (title bar, borders) to make it look like an app
wmctrl -r "cava" -b add,above
wmctrl -r "cava" -b remove,decorations
