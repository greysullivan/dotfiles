#!/usr/bin/env python3
import tkinter as tk
import subprocess
import time

# Get active window geometry using xdotool
result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowgeometry', '--shell'],
                       capture_output=True, text=True)

# Parse geometry
geometry = {}
for line in result.stdout.strip().split('\n'):
    if '=' in line:
        key, value = line.split('=')
        geometry[key] = int(value)

x = geometry['X']
y = geometry['Y']
width = geometry['WIDTH']
height = geometry['HEIGHT']
border_width = 4

# Create root window
root = tk.Tk()
root.withdraw()

# Soft warm white color
color = '#e8e4e0'

# Create 4 border windows (top, bottom, left, right)
borders = []

# Top border
top = tk.Toplevel(root)
top.overrideredirect(True)
top.configure(bg=color)
top.geometry(f"{width}x{border_width}+{x}+{y}")
top.attributes('-topmost', True)
top.attributes('-alpha', 1.0)
borders.append(top)

# Bottom border
bottom = tk.Toplevel(root)
bottom.overrideredirect(True)
bottom.configure(bg=color)
bottom.geometry(f"{width}x{border_width}+{x}+{y+height-border_width}")
bottom.attributes('-topmost', True)
bottom.attributes('-alpha', 1.0)
borders.append(bottom)

# Left border
left = tk.Toplevel(root)
left.overrideredirect(True)
left.configure(bg=color)
left.geometry(f"{border_width}x{height}+{x}+{y}")
left.attributes('-topmost', True)
left.attributes('-alpha', 1.0)
borders.append(left)

# Right border
right = tk.Toplevel(root)
right.overrideredirect(True)
right.configure(bg=color)
right.geometry(f"{border_width}x{height}+{x+width-border_width}+{y}")
right.attributes('-topmost', True)
right.attributes('-alpha', 1.0)
borders.append(right)

# Update to show windows
root.update()

# Fade out effect
steps = 20
delay = 0.08
for i in range(steps):
    alpha = 1.0 - (i + 1) / steps
    for border in borders:
        border.attributes('-alpha', alpha)
    root.update()
    time.sleep(delay)

# Close all windows
root.destroy()
