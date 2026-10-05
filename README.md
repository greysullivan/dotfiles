# Grey's dotfiles

Current Arch Linux/X11/i3 configuration, shell startup files, theme, custom
commands, and systemd user units. `home/` mirrors paths under `/home/grey`.
`manifest.json` explicitly lists every managed file.

## Fresh Arch install

Finish your base Arch install (for example with `archinstall`), boot it, and
log in as your regular user with working networking and sudo. Copy or clone
this repository, then run:

```sh
cd ~/dotfiles
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
cd ~/dotfiles
python3 manage.py snapshot
git diff
git add .
git commit -m "Update dotfiles"
```

Add new configuration paths to `manifest.json` before taking a snapshot.
Snapshots copy files; live configuration continues to work independently.

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

Remote: `https://github.com/greysullivan/dotfiles`, branch `arch-install-20261005`.
The branch is committed locally; pushing awaits GitHub authentication.
The existing `master` branch contains the original reference setup.
