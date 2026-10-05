# SLUNTSHACK SYSTEM COLOUR GRAMMAR — 2026-10-05

Source: ~/Drive/Downloads/SluntShack/color-rules.txt
This supersedes the previous bone/mauve appearance.
Black #000000: space/background. White #FFFFFF: primary information.
Greys #A3A3A3/#D0D0D0/#B8B8B8/#C0C0C0: secondary information and syntax.
Surface #191919; divider #343434. Orange #FF3D00: focus/selection/attention.
Red #D88C8C: faults/destructive actions. No green/yellow/blue/purple/cyan
semantic roles. Legacy palette token names remain for generator compatibility,
but their values are neutral. Yazi icons remain disabled, as before.

Canonical settings: ~/.config/air-theme/palette.json
Generator/application: air-theme charcoal
Status: air-theme status
Original oldest desktop baseline remains intact. This update has its own
current-state backup, including independent i3 edits and the Codex config.

## Refresh

XFCE Terminal colours, i3 and Dunst are refreshed in place.
Yazi: quit normally with q and run y. ncspot: enter :reload.
Kitty: reopen normally. Neovim: :colorscheme charcoal (or reopen).
tmux: tmux source-file ~/.tmux.conf when a server exists.
Codex CLI: restart the session to load tui.theme = "sluntshack".
GTK apps: reopen normally. Firefox chrome CSS remains staged; it takes effect
only if toolkit.legacyUserProfileCustomizations.stylesheets is already enabled,
then restart Firefox normally. Website content and image assets are unaffected.
No original TUI sessions are killed or playback interrupted.

## Codex

A supported custom ~/.codex/themes/sluntshack.tmTheme neutralises fenced-code
syntax and diff content. Existing hooks, notifications and other config values
are preserved. Other Codex TUI styles are not exposed through this syntax-theme
setting; literal truecolour styles may remain outside its control. ANSI-based
colours follow the new terminal palette. No upstream binary patching is used.
Official OpenAI Docs: https://learn.chatgpt.com/docs/cli-customization

## Presentation

Filetypes, executables, media and archives use white/greys, not error/attention
colours. Broken links and destructive cut/deletion states retain red.
Selection/mode badges use black on orange; inactive/copied states use greys.
Resource graphs and diff data are neutral, including high numerical values.
Threshold warnings that request attention use orange, actual errors use red.
The command-entry prompt is orange because it is the active interaction.
Neovim's plain Linux-console fallback cannot reproduce exact orange and uses
neutral bold/inverse contrast; graphical truecolour terminals use exact orange.

## Verification and limits

Native JSON/TOML/XML parsing, i3 config validation and native Neovim theme load
are checked before application. Whole-system appearance is generated from the
preserved baseline and merged with independent edits before writes.
Reload results, native render evidence and rollback tests are recorded below.
Not every app state can be exercised without changing the user's work. Ordinary
application content can emit literal RGB escape sequences independently of a
terminal palette; unsupported cases are documented rather than patched blindly.
The Codex gong, per-stream ducking, settings, startup, compositor, navigation,
Yazi layout and all keybindings remain unchanged by this presentation update.

## Rollback

Restore just this update (before rolling back older updates):

```text
/home/grey/.local/state/air-theme/sluntshack-20261005-074940/restore
```

Preflight:

```text
/home/grey/.local/state/air-theme/sluntshack-20261005-074940/restore --check
```

Run from the ordinary user terminal. Codex files are protected inside the Codex
sandbox, so an agent invoking this restore requires filesystem escalation.
The restore validates snapshots, preflights all files, preserves independent
edits through three-way merging and aborts on conflicts before live file writes.
It reloads i3/Dunst and restores captured live XFCE terminal colour settings.
Reopen TUIs and Kitty after restoration.

## Shell

Shell completion selection is black on orange, replacing white on the former
blue ANSI background. No-match completion messages are grey, not faults.
The sourced shell-colours.zsh exports neutral LS_COLORS and EZA_COLORS; eza
extension defaults are reset. Broken-link and Git-conflict states remain red.
Existing aliases, command behaviour, matching and bindings are preserved.
Open a new shell or source ~/.config/air-theme/shell-colours.zsh to load the
listing colours; restarting the shell also refreshes completion styling.

## Results

- All generated native JSON/TOML/XML files and i3 config passed validation.
- Neovim loaded natively; every resolved foreground/background/special colour
  was neutral, orange attention or red fault. Built-in default leakage corrected.
- Native fastfetch and aerc colour-filter rendering passed.
- Native btop rendered 44 RGB colours; all neutral or semantic attention/fault.
- Real XFCE Terminal palette and Yazi screenshots were inspected: neutral
  data/filetypes, black background, readable text and orange selection.
- Live XFCE colour values matched; i3/Dunst reloads reported no failures.
- Idle native Codex theme picker displayed sluntshack (custom) (current).
  Its diff/syntax preview loaded; no model turn was submitted.
- Repeated generation produces identical intended themes; independent existing
  i3 changes were preserved. Dunst non-colour settings and all bindings match.
- Rollback was tested in an isolated copy, including prior Codex files, later
  independent config/palette edits, and overlapping-edit refusal.
Evidence: ~/.config/air-theme/review/sluntshack/
GTK/Firefox chrome, ncspot, aerc's full mailbox view, tmux and every warning/error
state were not separately visually exercised. Existing app sessions need the
refreshes listed above. Codex non-syntax TUI controls and literal RGB output in
other tools can remain outside supported theme/ANSI controls.

## Exact modified/added files (relative to home)

```text
.config/i3/config
.config/i3status/config
.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-terminal.xml
.config/fastfetch/config.jsonc
.config/btop/themes/charcoal.theme
.config/aerc/stylesets/charcoal
.config/yazi/theme.toml
.config/ncspot/config.toml
.config/dunst/dunstrc
.config/kitty/theme.conf
.config/starship.toml
.config/nvim/colors/charcoal.lua
.config/gtk-3.0/gtk.css
.config/mozilla/firefox/59y3la6e.default-release/chrome/userChrome.css
.tmux.conf
.local/bin/air-theme
.config/air-theme/palette.json
.config/air-theme/SLUNTSHACK.txt
.codex/config.toml
.codex/themes/sluntshack.tmTheme
.local/state/air-theme/state.json
.config/air-theme/generated/.config/i3/config
.config/air-theme/generated/.config/i3status/config
.config/air-theme/generated/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-terminal.xml
.config/air-theme/generated/.config/fastfetch/config.jsonc
.config/air-theme/generated/.config/btop/themes/charcoal.theme
.config/air-theme/generated/.config/aerc/stylesets/charcoal
.config/air-theme/generated/.config/yazi/theme.toml
.config/air-theme/generated/.config/ncspot/config.toml
.config/air-theme/generated/.config/dunst/dunstrc
.config/air-theme/generated/.config/kitty/theme.conf
.config/air-theme/generated/.config/starship.toml
.config/air-theme/generated/.config/nvim/colors/charcoal.lua
.config/air-theme/generated/.config/gtk-3.0/gtk.css
.config/air-theme/generated/.config/mozilla/firefox/59y3la6e.default-release/chrome/userChrome.css
.config/air-theme/generated/.tmux.conf
.local/state/air-theme/last/.config/i3/config
.local/state/air-theme/last/.config/i3status/config
.local/state/air-theme/last/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-terminal.xml
.local/state/air-theme/last/.config/fastfetch/config.jsonc
.local/state/air-theme/last/.config/btop/themes/charcoal.theme
.local/state/air-theme/last/.config/aerc/stylesets/charcoal
.local/state/air-theme/last/.config/yazi/theme.toml
.local/state/air-theme/last/.config/ncspot/config.toml
.local/state/air-theme/last/.config/dunst/dunstrc
.local/state/air-theme/last/.config/kitty/theme.conf
.local/state/air-theme/last/.config/starship.toml
.local/state/air-theme/last/.config/nvim/colors/charcoal.lua
.local/state/air-theme/last/.config/gtk-3.0/gtk.css
.local/state/air-theme/last/.config/mozilla/firefox/59y3la6e.default-release/chrome/userChrome.css
.local/state/air-theme/last/.tmux.conf
.zshrc
.config/air-theme/shell-colours.zsh
```
