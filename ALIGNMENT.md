# Align the existing Pro with the Air

This kit updates the Pro's existing Arch/i3 setup. The running Air is the visual
and behavioral reference: black backgrounds, white text, grey structure, muted
pink focus/selection, JetBrains Mono, the same shortcuts and terminal workflows.
Your existing packages, accounts, projects and private files stay in place.

## Obtain the kit

```sh
git clone --branch migration-macbookpro11-4 https://github.com/greysullivan/dotfiles.git ~/src/air-alignment
cd ~/src/air-alignment
```

If GitHub cloning still fails, use the controller's exported archive instead.
Copy `air-alignment.tar.gz` over SSH or a USB stick, extract it into an empty
folder, and run the same commands there. The archive contains the reviewed repo
files; it includes neither Git history nor private machine data. Check the
adjacent SHA-256 file after transferring it.

## Preview, then align

```sh
./install.sh --align --profile macbookpro11-4
./install.sh --align --profile macbookpro11-4 --apply
```

The preview reports missing dependencies and lists only changed/new files.
Apply restores configs and custom commands without a package transaction. Add
`--install-missing` to install the missing dependencies with
`pacman -Syu --needed`; Arch's normal full upgrade also updates existing packages.
No package is removed. Add `--zsh` only if the login shell needs changing.

`--full` compares the entire compatible Air package inventory rather than just
desktop/custom-command dependencies. The source's `broadcom-wl-dkms` driver is
excluded from that list. Preserve the Pro's working Wi-Fi and GPU drivers.
`inventory.json` records all 661 source packages, versions, installation reasons,
custom executable hashes and the bundled audio project's source commit.
`services-reference.json` records the source's enabled user and system units.

The Pro profile requires `MacBookPro11,4` when applied through the installer.
It uses the actual host/CPU, battery path and libinput touchpads. Its Retina
resource file starts at `Xft.dpi: 192`; adjust
`~/.config/xorg/macbookpro-resources` if needed. Subsequent alignment preserves
your DPI adjustment.

Firefox's installation-default profile takes priority over a legacy profile's
`Default=1`. If there are several installation defaults, select one explicitly:

```sh
python3 manage.py restore --portable --profile macbookpro11-4 \
  --firefox-profile "$HOME/.config/mozilla/firefox/your-profile" --apply
```

Firefox styling is skipped if no profile exists. Start Firefox once and rerun.
Other `user.js` preferences are retained while enabling custom chrome styles.
The profile's bookmarks, passwords, extensions and other browser data are untouched.

Log out of i3 and run `startx` again to pick up the full session configuration.
Restart Firefox and terminals. Existing configs are backed up under
`~/.local/state/dotfiles/backups/<timestamp>/`, preserving permissions.
Recorded configuration modes survive Git clones; existing Firefox preference
file permissions are retained.
Identical files are left untouched. All managed destinations are checked before
writing; symlink destinations are refused.

## Startup and administrator settings

Preview user services, then activate only those whose prerequisites exist:

```sh
python3 align.py services --profile macbookpro11-4
python3 align.py services --profile macbookpro11-4 --apply
```

This covers PipeWire/WirePlumber, `put-on`, Drive mounting/uploads, and mail
initialization. Mail requires your existing private account/isync config and
either a completed Maildir marker or the private initialization helpers.
Missing private prerequisites are reported and skipped. Services are enabled
only when explicitly requested; alignment itself does not activate cloud/mail
connections. Account readiness and expired tokens still require verification.

Review system changes separately, after applying home configs:

```sh
python3 align.py system --profile macbookpro11-4 --home "$HOME"
sudo python3 align.py system --profile macbookpro11-4 --home "$HOME" --apply
```

This installs tap-to-click and the Air's lid/power-button settings, enables
NetworkManager, time synchronization and touchegg, and starts touchegg. System
files are backed up under `/var/backups/grey-alignment/`. Logind changes take
effect after reboot; existing logind sessions are not restarted. Check for
other locally configured logind overrides if behavior differs. This command
does not replace networking profiles, drivers, partitions, encryption or boot
entries. Existing locale, timezone and keyboard settings are retained.

The `drive` command and identified external-drive helper are included as
references. The alignment does not run its `setup` command, disk repair,
formatting, or backup timer installation. Keep the existing external-drive
setup, and use its documented identity checks before configuring it on the Pro.

## Features requiring additional state

The repo supplies current themes, config, command scripts, notification sounds,
Neovim/notes, capture/YouTube helpers, native Firefox messaging manifests, and
the audio compiler runtime. `audio-live` uses your existing
`~/src/arch-audio-live` when present, otherwise the bundled runtime under
`~/.local/share/grey-audio-live`. It does not overwrite an existing project.

The Air's custom `~/.local/bin/ncspot`, separately installed Codex, Vosk speech
model, mail/Drive/Spotify credentials, theme rollback history, and personal data
are not in the public repo. `python3 align.py audit` reports these prerequisites.
Use the packaged ncspot if its behavior is sufficient; matching the Air's custom
binary requires a private transfer and checking its shared-library dependencies.
Theme rollback requires that machine's own local theme history; source-machine
rollback paths should not be transplanted into an established target setup.

A full private transfer remains a separate operation. Use a dedicated encrypted
Restic repository over SSH, back up application state with writers stopped (or
SQLite's backup API), restore to staging, verify, then select the needed files.
Do not overlay the entire home directory on this already configured Pro. Preserve
its SSH access, machine identity, project changes, and account state. Exclude
Drive/external mounts, caches, sockets and backup destinations; retain the
encryption password separately. See the official
[SFTP setup](https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html#sftp)
and [restore verification](https://restic.readthedocs.io/en/stable/050_restore.html).

## Verify on the Pro

- Compare terminal, i3, launcher, notifications, Firefox, Neovim and Yazi colors.
- Check Super+Enter, Super+d, workspace moves, capture, lock and dictation keys.
- Exercise `notes`, `work`, `put-on`, `yt`, `ty` and `audio-live`; test media playback.
- Check audio, screen/keyboard brightness, gestures, battery status and Wi-Fi.
- Inspect `systemctl --user --failed` and enabled timers; verify configured accounts.
- Reboot, log in, run `startx`, and check the one-second power-button hold and lid behavior.

The controller's automated tests cover restoration safety and repeatability.
Visual and hardware verification must still happen on the Pro.

## Refresh the reference later

On the Air, run `python3 capture.py`, inspect the diff, run
`python3 -m unittest discover -s tests -v`, and review staged content before
committing. Capture uses an explicit allowlist; new files must be deliberately
added. Live configuration remains independent of this repo.
