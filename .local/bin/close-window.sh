#!/bin/bash
WID=$(xdotool getactivewindow)
wmctrl -ic "$WID"
