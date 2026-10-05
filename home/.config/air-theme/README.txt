CHARCOAL — ARCH AIR OPTIONAL THEME
Installed and selected for review: 2026-10-05.

COMMANDS
  air-theme charcoal   Generate, validate and select charcoal; safe to repeat.
  air-theme original   Restore captured appearance, preserving unrelated edits.
  air-theme status     Show selection, refresh failures and file drift.
  start03              Select charcoal, then run the existing startx route.

Existing startup stays available: startx -> ~/.xinitrc -> i3.
Neither shell login nor .xinitrc was given an automatic theme-selection hook.
Appearance config changes persist after logout. Starting with startx alone
will not restore the old theme. Run air-theme original explicitly to restore.
From a TTY, graphical reloads are skipped; app files are still selected.
start03 rejects an existing graphical session and a non-console terminal.

PALETTE AND IMPLEMENTATION
  ~/.config/air-theme/palette.json       One named source palette.
  ~/.config/air-theme/generated/         Generated native appearance configs.
  ~/.local/bin/air-theme                 Python generator and safe switcher.
  ~/.local/bin/start03                   Small guarded startup entry point.
  ~/.local/state/air-theme/              Private baseline, state and merge data.
Existing zsh PATH already includes ~/.local/bin, so shell configs needed no edit.
Python, diff3 and existing app tools are used. No packages were installed.

Palette: desktop #000000, background #0e0e0e, surface #191919,
foreground #f5f3ed, muted #a3a19b, divider #343434, accent #FF3D00.
Error #d88c8c, success #a9c99f, warning #d8c5a0, info #9faec7,
violet #b2a4c7 and cyan #9fc7c7 preserve ANSI meanings, diagnostics,
diff distinctions and CPU/memory/network graph readability. Their roles are
separate from the orange focus/selection/activity accent. Bright ANSI entries
retain their semantic colors; applications may additionally use bold/labels.

Measured contrast: warm content/background 17.40:1, muted/background 7.47:1,
black/orange selection 5.92:1. Dividers are deliberately fine (1.55:1 against
the background) and were visible in the Air preview at 1440x900.

WHAT CHANGED
19 native files, listed below. Existing configs were transformed only for
appearance; native fragments were added where appropriate. Original bindings,
accounts, openers, icons, information arrangement, plugins and startup daemons
remain shared. Neovim had no user configuration and received only a small
colorscheme plus its loader. Installed tmux had no user config and received
appearance settings. GTK settings/CSS were absent and were added.
xfce4-terminal retains JetBrains Mono 11 and is now opaque. Picom's existing
shadows, opacity rules and other compositor settings are unchanged; the
compositor can still dim inactive windows. i3 remains borderless with its
existing gaps. xsetroot and i3lock use true black. Existing glimmer behavior
was preserved. This task did not change the screen mode or icon policy.

NATIVE FILES (paths relative to home)
  .config/i3/config
  .config/i3status/config
  .config/xfce4/xfconf/xfce-perchannel-xml/xfce4-terminal.xml
  .config/fastfetch/config.jsonc
  .config/btop/btop.conf
  .config/btop/themes/charcoal.theme
  .config/aerc/aerc.conf
  .config/aerc/stylesets/charcoal
  .config/yazi/theme.toml
  .config/ncspot/config.toml
  .config/dunst/dunstrc
  .config/kitty/theme.conf
  .config/starship.toml
  .config/nvim/init.lua
  .config/nvim/colors/charcoal.lua
  .config/gtk-3.0/settings.ini
  .config/gtk-3.0/gtk.css
  .config/mozilla/firefox/59y3la6e.default-release/chrome/userChrome.css
  .tmux.conf

ORIGINAL AND SAFE RESTORATION
Original appearance backup:
  /home/grey/.local/state/air-theme/original-20261005-055649
The backup contains the original file bytes, a manifest of absence, permissions,
symlink targets and SHA-256 hashes. baseline.json references this stable first
backup; repeated selection never replaces it. Backups/state directories are
private (0700) and backup files are 0600. Do not publish these files.
Pre-existing implementation scripts/palette were also captured before editing:
  ~/.local/state/air-theme/implementation-before-20261005-055436/

Use air-theme original. Three-way merges reverse our appearance changes while
retaining independent later edits. If a file conflicts, application stops before
any live file writes. Its current, requested and merge copies are saved under
~/.local/state/air-theme/conflicts/<relative-path>{,.requested,.merge}.
Read the exact conflict path printed by the command, resolve the overlapping
change deliberately, then rerun the selection. No conflicting file is silently
replaced. Files originally absent are removed if no independent content remains.
Current permissions are preserved; changed symlink targets are refused.
A malformed edited palette cannot prevent original restoration.
The 'last' directory tracks intended appearance deltas, not unrelated edits;
state.json records actual final file hashes and refresh errors. Interrupted
writes leave status 'partial'; retry the desired selection after resolving errors.

REFRESH AND LIMITATIONS
Within X, i3 reload, xsetroot, xfconf terminal palette updates and dunstctl reload
were performed successfully. Existing terminals, editors, music and mail were
kept running. Other app sessions may retain old explicit colors until reopened.
  ncspot: :reload is supported; no playback/auth changes were made.
  Neovim: :colorscheme charcoal in an existing session (TTY: disable
           termguicolors if it was previously enabled).
  btop/Yazi/aerc/Kitty/fastfetch: reopen or run the next invocation.
  GTK: reopen applications. Existing icons and installed GTK theme are retained.
  tmux: new servers load ~/.tmux.conf. With an existing server, explicitly
        source ~/.tmux.conf if you want all its appearance options now. Merely
        restoring the file does not reset options already loaded into a server.

Firefox chrome CSS is staged in the existing default-release profile. Its
user.js and prefs.js were not changed: the legacy chrome-stylesheet preference
was disabled/absent, and enabling it can persist beyond deleting user.js.
If you want this optional browser chrome, enable
  toolkit.legacyUserProfileCustomizations.stylesheets
in about:config and restart Firefox. This changes browser chrome only. If you
enable it yourself, remember that air-theme original restores the CSS file,
but does not undo your manual preference choice. No website CSS was added.

Real Linux console output is limited by the console's 16-color palette and
font. Exact #FF3D00 is retained in truecolor terminals. Neovim disables
termguicolors on TERM=linux and supplies nearest ANSI colors, with brighter
colors preferred for equal-distance ties (orange becomes bright red, index 9,
under the standard console palette). btop's --tty option provides its own
16-color/ANSI graph mode. Other TUIs choose their terminal-capability fallback;
identical TTY rendering is not promised. No console palette was globally changed.

VERIFICATION
Passed Python and shell syntax; TOML, JSON and XML parsing; i3 -C validation;
actual fastfetch config parsing; actual Neovim colorscheme loading and highlight
checks; Neovim TERM=linux fallback; isolated tmux native config loading; live
xfconf selection foreground/background; successful i3 and Dunst reloads;
command discovery from a zsh login shell; repeated live theme application;
status without drift; start03's already-in-X guard.
Isolated copies of tracked files passed original byte/absence restoration,
unrelated-edit preservation across repeated apply, conflicting-edit refusal,
and restoration even when the palette is invalid. Live original restoration
was not exercised, to avoid repeatedly changing the working desktop.

Disposable native previews were inspected on the actual X display: terminal
palette/selection samples, btop graphs/values, Yazi selection/borders, Neovim
syntax/search, and aerc read/unread/selection using locally generated messages.
The aerc pager filter parsed the styleset on synthetic text. Private mail,
accounts and auth settings were not opened or used in these checks.
Screenshots and harmless sample files are under ~/.config/air-theme/review/.
Ncspot, Kitty, Firefox chrome, GTK dialogs and live notifications were not
visually inspected. Dunst config reload succeeded; placement/timeouts remain
unchanged, with critical notifications explicitly labelled CRITICAL.

MANUAL TTY CHECK
At a convenient time, exit i3 normally, returning to the original local TTY.
Run start03. Check that the usual i3 desktop and daemons start as before.
Use air-theme original to restore, then startx to use the captured appearance.
Actual X startup was not tested because a desktop session was already running.

VERSION CHECKS
All requested apps were installed; none were missing.
i3 4.25.1, xfce4-terminal 1.2.0, fastfetch 2.69.0, btop 1.4.7,
aerc 0.22.0, Yazi 26.9.1, ncspot 1.4.0, Neovim 0.12.5,
Dunst 1.13.2, tmux 3.7_c, Firefox 157.0, Kitty 0.49.2, Picom 13.
Local help/man pages, built-in Yazi defaults and versioned upstream docs were
checked. Older Yazi hovered/help keys were replaced with this version's
indicator/chord/action keys. Ncspot supports the existing theme entries.
Upstream references:
  https://raw.githubusercontent.com/sxyazi/yazi/v26.9.1/yazi-config/preset/theme-dark.toml
  https://raw.githubusercontent.com/hrkfdn/ncspot/v1.4.0/doc/users.md

STATUS
Charcoal selected for optional review. No refresh failures are recorded.
Firefox chrome is staged pending the explicit manual opt-in described above.

YAZI STATUS COLOR UPDATE — 2026-10-05
See YAZI-COLOURS.txt for bone/mauve colors, scoped application and a
backup-specific rollback command. Only Yazi appearance changed in this update.
