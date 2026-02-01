#!/usr/bin/env bash

# --- THEO LAYOUT WITH PROPER GAPS ---
GAP=10

# Get screen dimensions from workarea
read SCREEN_X SCREEN_Y SCREEN_W SCREEN_H < <(xprop -root _NET_WORKAREA | awk '{print $3, $4, $5, $6}' | sed 's/,//g')

# Calculate quarter dimensions with gaps
QUARTER_W=$(( (SCREEN_W - GAP * 3) / 2 ))
QUARTER_H=$(( (SCREEN_H - GAP * 3) / 2 ))

# Calculate positions for 2x2 grid
TL_X=$GAP
TL_Y=$GAP
TR_X=$((QUARTER_W + GAP * 2))
TR_Y=$GAP
BL_X=$GAP
BL_Y=$((QUARTER_H + GAP * 2))
BR_X=$((QUARTER_W + GAP * 2))
BR_Y=$((QUARTER_H + GAP * 2))

# Helper function to get the most recent window ID
get_latest_window() {
    sleep 0.5
    xdotool search --class xfce4-terminal | tail -1
}

# --- LAUNCH APPS AND POSITION THEM ---

# Top-left: Terminal with fastfetch (runs from .zshrc)
xfce4-terminal &
WIN_TL=$(get_latest_window)
wmctrl -i -r $WIN_TL -e 0,$TL_X,$TL_Y,$QUARTER_W,$QUARTER_H

# Top-right: Terminal with cava
xfce4-terminal -e cava &
WIN_TR=$(get_latest_window)
wmctrl -i -r $WIN_TR -e 0,$TR_X,$TR_Y,$QUARTER_W,$QUARTER_H

# Bottom-left: Terminal with tty-clock
xfce4-terminal -e "tty-clock -c" &
WIN_BL=$(get_latest_window)
wmctrl -i -r $WIN_BL -e 0,$BL_X,$BL_Y,$QUARTER_W,$QUARTER_H

# Bottom-right: Terminal without fastfetch (like Super+Space)
xfce4-terminal -e 'zsh -c "SKIP_FASTFETCH=1 exec zsh"' &
WIN_BR=$(get_latest_window)
wmctrl -i -r $WIN_BR -e 0,$BR_X,$BR_Y,$QUARTER_W,$QUARTER_H
