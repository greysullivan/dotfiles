# Grey's dotfiles

Current Arch Linux/X11/i3 configuration, shell startup files, theme, custom
commands, and systemd user units. `home/` mirrors paths under `/home/grey`.
`manifest.json` explicitly lists every managed file.

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

The repository does not install packages or enable services. Package inventory
is in `packages/`; inspect those lists before installing on another machine.
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

This is a local repository. No remote is configured and nothing has been pushed.
