# LaCie daily storage and machine backups

Prepared for disk serial `WCJBN19R`, exFAT data UUID `00F2-EA07`.
This setup preserves the existing partitions, labels, and files. It does not format the disk or move the existing archive.

## Proposed layout

The drive mounts at `/home/grey/External`:

```text
External/
  personal/                 existing files, retained
  public/                   existing folder, retained
  samples/                  existing files, retained
  daily/
    inbox/
    documents/
    projects/
    media/
  backups/air/restic/        encrypted machine snapshots
```

exFAT retains compatibility with other systems. Its file storage does not provide Linux ownership, permissions, or symlink semantics, so keep executable development environments and application configuration on the internal Linux filesystem. The `daily/projects` folder is for portable project files.

## Installation

Run in a visible terminal:

```sh
sudo python3 /home/grey/setup/drive-use/grey-drive.py setup
```

The default backup covers `/home/grey`, `/etc`, `/boot`, the package database, and generated package/disk/mount inventories. To select a full live-filesystem backup instead, use `setup --scope full-system` on the initial installation.

The setup verifies the drive identity and checks exFAT without repairing it. If the same single damaged zero-length WAV entry remains, it saves the affected directory internally, then asks you to type `REPAIR` before starting interactive filesystem repair. It stops if the findings differ or the subsequent filesystem check is not clean. The saved directory is not an independent backup of all 213 GiB of existing external files.

The script installs Restic if needed and asks for an encryption password. It stores the password internally at `~/.config/drive-use/backup-password` with mode 0600; it never prints the password. Keep the password separately so you can restore after losing the laptop. Do not store your only recovery password on this drive.

It installs a UUID-based, optional manual mount entry in `/etc/fstab`, a root-owned `grey-drive` helper, the `drive` command, and a daily systemd timer. Existing files are kept. Backups do not start until the drive has passed the filesystem check.

## Verification and daily use

The first backup must succeed, pass a repository check, restore a test file with a matching SHA-256 hash, and pass a complete backup-data read before scheduling is enabled. Daily runs perform a repository check and sample restore. This verifies backup storage and a sample restoration; it is not a full system recovery drill.

```sh
drive mount       # mount at ~/External
drive status      # show the last verified snapshot and timer
drive backup      # take and verify a snapshot now
drive eject       # flush writes and unmount before unplugging
```

The timer runs at 19:00 local time, with up to ten minutes of jitter. A missed scheduled run is considered after the machine starts; a disconnected drive is skipped without writing a substitute backup to the laptop. Reconnecting after a skipped run does not itself trigger another backup: use `drive backup` or leave the drive connected for the next scheduled run.

Cloud mounts, external mounts, caches, temporary files, the backup password, and the internal `Snapshots` directory are excluded. No existing snapshots are automatically deleted or pruned. Backups are live file copies, not atomic snapshots, disk images, or bootable clones. Application files can change during a backup; Restic errors must be resolved before a snapshot is treated as verified.

The backup repository protects the laptop's files on another disk. Existing archives and new files stored only in `External/daily` still have no independent second copy; this setup does not silently upload them to cloud storage.

## Recovery

Use Restic with the repository at `External/backups/air/restic` and the separately retained password. Restore into an empty destination first. Inspect snapshots with:

```sh
restic -r ~/External/backups/air/restic --password-file ~/.config/drive-use/backup-password snapshots
```

The system configuration and package inventory help rebuild Arch. A full recovery still requires separately recreating partitions, encryption, boot configuration, and reinstalling a bootloader as needed; this setup does not change those components.

Setup evidence is saved under `~/setup/drive-use/evidence/`; backup status is `/var/lib/grey-drive-backup/last-backup.json`. Timer logs are available using `journalctl -u grey-drive-backup.service`.

Official references: [Restic repository and password setup](https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html), [backup options](https://restic.readthedocs.io/en/stable/040_backup.html), and [restoring backups](https://restic.readthedocs.io/en/stable/050_restore.html).
