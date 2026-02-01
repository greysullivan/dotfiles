#!/bin/bash
# Launch terminal centered on screen
# Used by Super+space keybinding

# Get screen dimensions
read SCREEN_W SCREEN_H <<< $(xdotool getdisplaygeometry)

# Terminal size (adjust as needed)
TERM_W=900
TERM_H=600

# Calculate center position
POS_X=$(( (SCREEN_W - TERM_W) / 2 ))
POS_Y=$(( (SCREEN_H - TERM_H) / 2 ))

# Launch centered terminal
xfce4-terminal --geometry=110x30+${POS_X}+${POS_Y} -e 'zsh -c "SKIP_FASTFETCH=1 exec zsh"'
