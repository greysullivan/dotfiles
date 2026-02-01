#!/bin/bash
# Toggle artha window visibility

# Check if artha is running
if ! pgrep -x artha > /dev/null; then
    # Start artha if not running
    artha &
    sleep 0.5
fi

# Get artha window IDs
windows=$(xdotool search --class artha 2>/dev/null)

if [ -z "$windows" ]; then
    # No window found, try to show it
    pkill -USR1 artha
else
    # Toggle window visibility
    for win in $windows; do
        xdotool windowactivate "$win" 2>/dev/null && break
    done
fi
