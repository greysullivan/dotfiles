#!/usr/bin/python3
"""Preserve and prepare Grey's identified LaCie drive; encrypted backups."""
import argparse
import datetime as dt
import fcntl
import getpass
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import sys
import tempfile

HOME = Path('/home/grey')
MOUNT = HOME / 'External'
UUID = '00F2-EA07'
SERIAL = 'WCJBN19R'
PART = Path('/dev/disk/by-uuid') / UUID
REPO = MOUNT / 'backups/air/restic'
CONFIG = Path('/etc/grey-drive-backup.json')
STATE = Path('/var/lib/grey-drive-backup')
KEY = HOME / '.config/drive-use/backup-password'
INSTALLED = Path('/usr/local/bin/grey-drive')
account = pwd.getpwnam('grey')


def command(args, capture=False, check=True):
    return subprocess.run([str(a) for a in args], check=check,
                          capture_output=capture, text=True)


def detect():
    data = json.loads(command(['lsblk', '-J', '-o', 'NAME,SERIAL,FSTYPE,UUID,MOUNTPOINTS'], True).stdout)
    disks = [d for d in data['blockdevices'] if d.get('serial') == SERIAL]
    if len(disks) != 1:
        raise RuntimeError('Expected LaCie drive is not connected uniquely. No disk changes made.')
    parts = [p for p in disks[0].get('children', []) if p.get('uuid') == UUID and p.get('fstype') == 'exfat']
    if len(parts) != 1:
        raise RuntimeError('Expected exFAT UUID does not match the identified drive.')
    return '/dev/' + disks[0]['name'], parts[0]


def mounted():
    result = command(['findmnt', '-J', '--mountpoint', MOUNT, '-o', 'SOURCE,FSTYPE,OPTIONS'], True, False)
    if result.returncode == 1:
        return None
    if result.returncode:
        raise RuntimeError('Cannot verify mount state.')
    fs = json.loads(result.stdout)['filesystems'][0]
    if os.path.realpath(fs['source']) != os.path.realpath(PART) or fs['fstype'] != 'exfat':
        raise RuntimeError('The external-drive location contains a different filesystem.')
    return fs


def mount_drive():
    _, part = detect()
    fs = mounted()
    if fs is None:
        if any(part.get('mountpoints') or []):
            raise RuntimeError('Drive is mounted elsewhere; leave that mount untouched and stop.')
        MOUNT.mkdir(mode=0o700, exist_ok=True)
        if any(MOUNT.iterdir()):
            raise RuntimeError('Mount location contains local files; refusing to hide them.')
        command(['mount', '-t', 'exfat', '-o', f'rw,nosuid,nodev,noexec,uid={account.pw_uid},gid={account.pw_gid},umask=0077', PART, MOUNT])
        fs = mounted()
    if not {'rw', 'nosuid', 'nodev', 'noexec'} <= set(fs['options'].split(',')):
        raise RuntimeError('Drive mount does not have the expected options.')


def restic(*args, capture=False):
    if not KEY.is_file() or not CONFIG.is_file():
        raise RuntimeError('Backup setup or password file is missing.')
    return command(['restic', '-r', REPO, '--password-file', KEY, *args], capture)


def backup():
    settings = json.loads(CONFIG.read_text())
    if not PART.exists():
        print('Backup skipped: the LaCie drive is disconnected.', flush=True)
        return
    mount_drive()
    if not (REPO / 'config').is_file():
        raise RuntimeError('Expected encrypted repository is missing; refusing to create a substitute.')
    meta = STATE / 'metadata'
    meta.mkdir(parents=True, exist_ok=True)
    for filename, args in [('packages.txt', ['pacman', '-Q']),
                           ('explicit-packages.txt', ['pacman', '-Qqe']),
                           ('disks.json', ['lsblk', '-J', '-o', 'NAME,TYPE,FSTYPE,SIZE,UUID,MOUNTPOINTS']),
                           ('mounts.json', ['findmnt', '-J'])]:
        (meta / filename).write_text(command(args, True).stdout)
    marker = meta / 'restore-test.txt'
    marker.write_text('Grey external backup restore test\n')
    sources = ['/', '/boot'] if settings['scope'] == 'full-system' else [str(HOME), '/etc', '/boot', '/var/lib/pacman', str(meta)]
    excludes = ['/dev', '/proc', '/sys', '/run', '/tmp', '/mnt', '/media', '/lost+found',
                str(MOUNT), str(HOME / 'Drive'), str(HOME / '.cache'), str(HOME / 'Snapshots'),
                str(KEY), '/root/.cache', '/var/cache', '/var/tmp', str(STATE / 'restic-cache')]
    args = ['backup', '--one-file-system', '--host', 'air', '--tag', 'machine', '--tag', settings['scope']]
    for path in excludes:
        args += ['--exclude', path]
    args += sources
    print('Creating an encrypted machine snapshot...', flush=True)
    restic(*args)
    restic('check')
    snapshots = json.loads(restic('snapshots', '--json', '--host', 'air', '--tag', settings['scope'], capture=True).stdout)
    snapshot = max(snapshots, key=lambda x: x['time'])
    with tempfile.TemporaryDirectory(prefix='grey-restore-check-', dir=STATE) as tmp:
        restic('restore', snapshot['id'], '--target', tmp, '--include', str(marker))
        restored = Path(tmp) / str(marker).lstrip('/')
        if not restored.is_file() or hashlib.sha256(restored.read_bytes()).digest() != hashlib.sha256(marker.read_bytes()).digest():
            raise RuntimeError('Restored test file does not match the source.')
    command(['sync', '-f', REPO])
    state = {'finished': dt.datetime.now().astimezone().isoformat(), 'snapshot': snapshot['id'],
             'scope': settings['scope'], 'repository_check': 'passed', 'sample_restore': 'passed',
             'limits': 'Live file backup, not an atomic snapshot or bootable disk image. Data packs not fully reread by restic check.'}
    (STATE / 'last-backup.json').write_text(json.dumps(state, indent=2) + '\n')
    print('Backup and sample restore verified. Snapshot: ' + snapshot['short_id'], flush=True)


def setup(scope):
    disk, part = detect()
    if any(part.get('mountpoints') or []):
        raise RuntimeError('Setup requires the drive unmounted; existing mounts are left untouched.')
    stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S')
    saved = HOME / 'setup/drive-use/evidence' / stamp
    saved.mkdir(parents=True, mode=0o700)
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not shutil.which('restic'):
        command(['pacman', '-S', '--needed', '--noconfirm', 'restic'])
    (saved / 'partitions.txt').write_text(command(['sfdisk', '--dump', disk], True).stdout)
    check = command(['fsck.exfat', '-n', PART], True, False)
    (saved / 'filesystem-before.txt').write_text(check.stdout + check.stderr)
    if check.returncode:
        expected = '022_c__Beat_128bpm_-_EDMDV2_Zenhiser.wav'
        if check.returncode != 4 or expected not in check.stdout or 'files corrupted 1, files fixed 0' not in check.stdout:
            raise RuntimeError('Filesystem findings differ from the reviewed single damaged entry. Setup stopped; see saved check output.')
        # Capture the affected directory read-only before offering repair.
        repair_mount = Path(tempfile.mkdtemp(prefix='grey-drive-pre-repair-', dir='/mnt'))
        command(['mount', '-t', 'exfat', '-o', 'ro,nosuid,nodev,noexec', PART, repair_mount])
        try:
            relative = Path('personal/geekshit/archives/playbook_backups/documentsM1/Image-Line/FL Studio/Projects/packs/EDM Drums Vol. 2/EDM_Drums_V2_-_Zenhiser/EDMDV2_-_Drum_Beats')
            affected = repair_mount / relative / expected
            if affected.stat().st_size != 0:
                raise RuntimeError('Damaged file is not zero length as expected; no repair performed.')
            command(['tar', '-cf', saved / 'affected-directory.tar', '-C', repair_mount, relative])
        finally:
            command(['umount', repair_mount])
            repair_mount.rmdir()
        print('The check found the previously reported zero-length WAV entry with a missing FAT chain.', flush=True)
        print('Its parent directory and partition layout have been saved internally. This is not a backup of the entire external drive.', flush=True)
        answer = input('Repair this filesystem entry interactively, keeping all existing files? Type REPAIR to continue: ')
        if answer != 'REPAIR':
            raise RuntimeError('No repair authorized. Drive remains unmounted; setup stopped.')
        command(['fsck.exfat', '-r', PART], check=False)
        check = command(['fsck.exfat', '-n', PART], True, False)
        (saved / 'filesystem-after.txt').write_text(check.stdout + check.stderr)
        if check.returncode:
            raise RuntimeError('Filesystem check still reports an issue; writable setup stopped.')
    if not sys.stdin.isatty():
        raise RuntimeError('Run setup in a visible terminal for password entry.')
    KEY.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chown(KEY.parent, account.pw_uid, account.pw_gid)
    if not KEY.exists():
        print('Choose a backup password you can keep separately from this laptop and drive.', flush=True)
        password = getpass.getpass('New encrypted-backup password: ')
        confirm = getpass.getpass('Confirm backup password: ')
        if not password or password != confirm:
            raise RuntimeError('Passwords are empty or do not match; repository not initialized.')
        with KEY.open('x') as stream:
            stream.write(password + '\n')
        os.chmod(KEY, 0o600)
        os.chown(KEY, account.pw_uid, account.pw_gid)
    if CONFIG.exists():
        if json.loads(CONFIG.read_text())['scope'] != scope:
            raise RuntimeError('Existing backup scope differs; refusing to silently change it.')
    else:
        CONFIG.write_text(json.dumps({'scope': scope, 'uuid': UUID, 'serial': SERIAL}, indent=2) + '\n')
        os.chmod(CONFIG, 0o600)
    fstab = Path('/etc/fstab')
    contents = fstab.read_text()
    marker = '# Grey LaCie daily storage (grey-drive managed)'
    if marker not in contents:
        if UUID in contents:
            raise RuntimeError('UUID already appears in fstab; manual review required.')
        (saved / 'fstab-before').write_text(contents)
        fstab.write_text(contents.rstrip() + f'\n\n{marker}\nUUID={UUID} {MOUNT} exfat noauto,nofail,user,uid={account.pw_uid},gid={account.pw_gid},umask=0077,nosuid,nodev,noexec 0 0\n')
    INSTALLED.parent.mkdir(parents=True, exist_ok=True)
    if Path(__file__).resolve() != INSTALLED:
        shutil.copyfile(__file__, INSTALLED)
    os.chown(INSTALLED, 0, 0)
    os.chmod(INSTALLED, 0o755)
    wrapper = HOME / '.local/bin/drive'
    if wrapper.exists() and 'grey-drive' not in wrapper.read_text():
        raise RuntimeError('An unrelated drive command already exists; refusing to overwrite it.')
    wrapper.write_text('#!/bin/sh\nexec sudo /usr/local/bin/grey-drive "$@"\n')
    wrapper.chmod(0o755)
    os.chown(wrapper, account.pw_uid, account.pw_gid)
    mount_drive()
    for folder in ['daily/inbox', 'daily/documents', 'daily/projects', 'daily/media', 'backups/air']:
        (MOUNT / folder).mkdir(parents=True, exist_ok=True)
    if not (REPO / 'config').exists():
        REPO.mkdir(parents=True, exist_ok=True)
        if any(REPO.iterdir()):
            raise RuntimeError('Backup repository directory is nonempty but uninitialized; stopped.')
        restic('init')
    # Complete the first backup and restore test before enabling automation.
    backup()
    print('Reading all backup data to verify the initial repository...', flush=True)
    restic('check', '--read-data')
    system = Path('/etc/systemd/system')
    (system / 'grey-drive-backup.service').write_text('[Unit]\nDescription=Encrypted backup to Grey LaCie drive\nConditionPathExists=/dev/disk/by-uuid/00F2-EA07\n\n[Service]\nType=oneshot\nExecStart=/usr/local/bin/grey-drive backup\nUMask=0077\nNice=10\nIOSchedulingClass=best-effort\nIOSchedulingPriority=7\n')
    (system / 'grey-drive-backup.timer').write_text('[Unit]\nDescription=Daily encrypted machine backup\n\n[Timer]\nOnCalendar=*-*-* 19:00:00\nPersistent=true\nRandomizedDelaySec=10m\n\n[Install]\nWantedBy=timers.target\n')
    command(['systemctl', 'daemon-reload'])
    command(['systemctl', 'enable', '--now', 'grey-drive-backup.timer'])
    for path in [saved, *saved.iterdir()]:
        os.chown(path, account.pw_uid, account.pw_gid)
    print(f'Drive ready at {MOUNT}. Existing files retained. Daily backups scheduled for 19:00 local time.', flush=True)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['setup', 'mount', 'backup', 'status', 'eject'], nargs='?', default='status')
    parser.add_argument('--scope', choices=['home-config', 'full-system'], default='home-config')
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error('Run setup with sudo in your terminal; after setup use the drive command.')
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (STATE / 'operation.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another drive operation is running. Try again after it finishes.')
        if args.action == 'setup':
            setup(args.scope)
        elif args.action == 'mount':
            if not CONFIG.exists():
                raise RuntimeError('Complete setup before mounting for daily use.')
            mount_drive()
            print(MOUNT)
        elif args.action == 'backup':
            backup()
        elif args.action == 'eject':
            detect()
            if mounted():
                command(['sync', '-f', MOUNT])
                command(['umount', MOUNT])
            print('Drive unmounted; safe to unplug.')
        else:
            detect()
            print('Mount:', mounted() or 'unmounted')
            state = STATE / 'last-backup.json'
            print(state.read_text() if state.exists() else 'No verified backup created yet.')
            command(['systemctl', 'list-timers', 'grey-drive-backup.timer', '--no-pager'], check=False)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, OSError, ValueError, KeyboardInterrupt, EOFError) as error:
        print('Stopped: ' + str(error), file=sys.stderr)
        sys.exit(1)
