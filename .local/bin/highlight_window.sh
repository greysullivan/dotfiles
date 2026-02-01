#!/bin/bash

# Get current desktop number
CURRENT_DESKTOP=$(wmctrl -d | grep '\*' | awk '{print $1}')

# Get list of windows on current workspace only, excluding panel and desktop
WINDOWS=($(wmctrl -l | awk -v desk="$CURRENT_DESKTOP" '$2 == desk' | grep -v -i "xfce4-panel\|Desktop" | awk '{print $1}'))

# If no windows or just one, highlight and exit
if [ ${#WINDOWS[@]} -le 1 ]; then
    [ ${#WINDOWS[@]} -eq 1 ] && python3 /home/grey/.local/bin/highlight_window.py
    exit 0
fi

# Get current active window in hex format
CURRENT_HEX=$(printf "0x%08x" $(xdotool getactivewindow))

# Find current window index and get next window
TOTAL=${#WINDOWS[@]}
for i in "${!WINDOWS[@]}"; do
    if [ "${WINDOWS[$i]}" == "$CURRENT_HEX" ]; then
        NEXT_INDEX=$(( (i + 1) % TOTAL ))
        wmctrl -i -a "${WINDOWS[$NEXT_INDEX]}"
        sleep 0.05
        python3 /home/grey/.local/bin/highlight_window.py
        exit 0
    fi
done

# If current window not found in list, activate first window
wmctrl -i -a "${WINDOWS[0]}"
sleep 0.05
python3 /home/grey/.local/bin/highlight_window.py
