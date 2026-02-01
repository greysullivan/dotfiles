#!/bin/bash
# Auto-chmod if needed
[[ ! -x "$0" ]] && chmod +x "$0" && exec "$0" "$@"

# Launch kitty with no decorations running cacademo
kitty --class=cacad \
      --title " " \
      -o remember_window_size=no \
      -o window_padding_width=0 \
      -o window_margin_width=0 \
      -o tab_bar_style=hidden \
      -o macos_titlebar_color=none \
      -o hide_window_decorations=yes \
      -e cacademo
