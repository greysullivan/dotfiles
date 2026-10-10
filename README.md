# Grey's dotfiles

Current Arch Linux/X11/i3 configuration, shell startup files, theme, custom
commands, and systemd user units. `home/` mirrors paths under `/home/grey`.
`manifest.json` explicitly lists every managed file.

## Align an existing MacBook Pro

For the Pro that already runs Arch and the original desktop setup, follow
[ALIGNMENT.md](ALIGNMENT.md). The current live Air configuration is the reference.

```sh
./install.sh --align --profile macbookpro11-4          # preview changes and dependencies
./install.sh --align --profile macbookpro11-4 --apply  # update configs; keep installed packages
```

Missing packages, private prerequisites, services and administrator settings are
handled explicitly. The Pro's existing private data, projects and working boot
setup remain in place. A reviewed archive also works when GitHub cloning fails.

## Fresh Arch install

Finish your base Arch install (for example with `archinstall`), boot it, and
log in as your regular user with working networking and sudo. Copy or clone
this repository, then run:

```sh
cd ~/src/dotfiles
./install.sh                         # preview
./install.sh --apply --zsh           # desktop, configs, zsh login shell
./install.sh --apply --extras --zsh  # also mail, music, Drive and dictation dependencies
```

The installer uses official Arch packages with `pacman -Syu --needed` and normal
package-manager prompts. It keeps the black/charcoal theme and your existing
keyboard layout. After installation, run `startx` from a local TTY.
Super+Enter opens a terminal and Super+d opens the launcher.

It adapts `/home/grey` references to your home directory, preserves file modes,
and backs up overwritten configs. Initialize Firefox once before installing
to apply the stylesheet to an existing profile; otherwise it is skipped.
Enable `toolkit.legacyUserProfileCustomizations.stylesheets` in Firefox's
`about:config`. Run `./install.sh --apply --configs-only` to restore again
without a package transaction. Initialize Firefox and rerun this command before
using `air-theme` on a fresh installation.

Account credentials, Codex installation, the Vosk speech model, and service
enablement are separate setup steps. The optional gestures client requires
the touchegg system service. Hardware-specific Wi-Fi/GPU drivers, boot setup,
and the system-wide power-button/touchpad snippets remain manual choices.
`packages/desktop.txt` and `packages/extras.txt` are the installer lists;
`packages/official.txt` is the original machine inventory, not an install list.

## Update from the live setup

```sh
cd ~/src/dotfiles
python3 manage.py snapshot
git diff
git add .
git commit -m "Update dotfiles"
```

Add new configuration paths to `manifest.json` before taking a snapshot.
Snapshots copy files; live configuration continues to work independently.

The console workspace is available through `work`; its independent tmux
configuration is included. Fastfetch uses a white upper Arch logo and orange
lower section. The Firefox theme template and its enabling preference are
included alongside the generated stylesheet.

## Neovim and notes

Neovim shows only text and the cursor. Code keeps ordinary Vim editing and
manual saves; `notes` opens a fresh Markdown draft ready to type. Notes live
in `~/Notes` and autosave after 750 ms of inactivity, on leaving a buffer,
and on quitting. Untouched drafts create no files. Filename collisions get
unique suffixes; write failures and external changes retain unsaved text.
Persistent undo is enabled. Notes are private user data and are not included
in this repository.

In a note, Ctrl+N starts another draft, Ctrl+O opens the searchable pool,
Ctrl+F searches its content, and Ctrl+S saves. Ctrl+Z/Ctrl+Y undo/redo;
Escape enters Vim normal mode. Tab/Shift+Tab nest/unnest lists, including
their children; Enter continues lists and checkboxes, or ends an empty item.
Project Markdown keeps ordinary editing. `:NotesAdd` copies the current
Markdown buffer into the pool without moving or writing its source file.

In normal mode, Space then `ff` finds project files, `fg` searches content,
`gr` opens working-tree Git changes, and `gs` opens staged changes. Review
is read-only: Enter on a hunk opens the file at that line; `q` returns to
the editor. Space then `nn`/`np`/`ns`/`na` invokes new note/pool/search/add.
Pickers close with Escape. There are no persistent menus or shortcut hints.

The editing modules load independently of the generated theme. Existing
Neovim processes need reopening to load this configuration. Git, ripgrep,
and fzf are already in the desktop package list; no editor plugins are needed.

## External drive tools

`tools/external-drive-report/inspect.py` reads the identified LaCie drive and
generates a local hardware, health, and metadata inventory report.
`tools/drive-use/grey-drive.py` prepares daily storage and encrypted machine
backups while retaining the existing files. See
[drive setup instructions](tools/drive-use/README.md). These tools are specific
to this machine and the reviewed drive identity; the desktop installer does
not run them or change disk partitions. They require administrator access
in a visible terminal. Reports, drive contents, repair evidence, and backup
passwords are not tracked in this repository.

## Restore

```sh
python3 manage.py restore             # preview
python3 manage.py restore --apply     # copy into your home directory
```

Existing destination files are backed up under
`~/.local/state/dotfiles/backups/<timestamp>/`. Review machine-specific paths
before restoring on another computer. The Firefox stylesheet targets this
machine's profile; change its manifest path and repository path for another
profile. Restart affected apps or reload i3 after applying changes.

`manage.py` restores files only; `install.sh` also installs the chosen packages.
Neither enables the Drive services automatically.
Enable the capture upload timer and Drive mount only after configuring rclone
credentials privately. The systemd logind and Xorg snippets are reference copies
under `home/.config`; their system-wide installation requires administrator access.

## Coverage and private data

Includes shell, tmux, i3/i3status, Kitty/XFCE Terminal, GTK, Dunst, Picom,
Neovim, Yazi, ncspot, Cava, btop, fastfetch/neofetch, mpv/YouTube artwork,
Flameshot/capture, Drive service units, dictation helper, mail helpers,
Codex notifications, theme tooling, and the ty/yt commands and interests.

Excludes passwords, OAuth tokens/rclone config, mail account configuration,
browser profile data except the custom stylesheet, histories, caches, screenshots,
recordings, generated theme copies, speech models, downloaded application
binaries, and historical setup backups. Configure mail accounts and credentials
separately; helper scripts reference the private files without storing their contents.
The Codex executable is installed separately. Service enablement symlinks are
also omitted; enable the relevant units explicitly when restoring.

Remote: `https://github.com/greysullivan/dotfiles`, alignment branch
`migration-macbookpro11-4` (based on `arch-install-20261005`).
The existing `master` branch contains the original reference setup.
