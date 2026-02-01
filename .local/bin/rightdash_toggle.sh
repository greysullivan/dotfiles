#!/bin/bash

# Master toggle script for right-side dashboard (pclock, cava, btop)

# Check if any of the dashboard windows exist
if wmctrl -l | grep -q "pclock-panel\|cava-panel\|btop-panel"; then
    # Windows exist - kill all three
    pkill -f "pclock-panel"
    pkill -f "cava-panel"
    pkill -f "btop-panel"
else
    # No windows exist - launch all three
    ~/.local/bin/launch_pclock.sh &
    sleep 0.2
    ~/.local/bin/launch_cava.sh &
    sleep 0.2
    ~/.local/bin/launch_btop.sh &
fi
