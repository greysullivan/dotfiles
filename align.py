#!/usr/bin/env python3
"""Audit dependencies and explicitly apply existing-machine startup settings."""
import argparse
import os
from pathlib import Path
import pwd
import shutil
import subprocess
from datetime import datetime

REPO = Path(__file__).resolve().parent


def package_names(full=False, profile='source'):
    files = ['full.txt'] if full else ['desktop.txt', 'extras.txt', 'behaviour.txt']
    names = set()
    for filename in files:
        names.update(line.strip() for line in (REPO / 'packages' / filename).read_text().splitlines()
                     if line.strip() and not line.startswith('#'))
    if profile == 'macbookpro11-4':
        names.add('xorg-xrdb')
    return sorted(names)


def missing_packages(full=False, profile='source'):
    present = set(subprocess.check_output(['pacman', '-Qq'], text=True).splitlines())
    return sorted(set(package_names(full, profile)) - present)


def check_profile(profile):
    if profile == 'macbookpro11-4':
        actual = Path('/sys/class/dmi/id/product_name').read_text().strip()
        if actual != 'MacBookPro11,4':
            raise SystemExit(f'Pro profile requires MacBookPro11,4; found {actual}.')


def service_plan(home):
    requirements = {
        'wireplumber.service': ['/usr/bin/wireplumber'],
        'pipewire.socket': ['/usr/bin/pipewire'],
        'pipewire-pulse.socket': ['/usr/bin/pipewire-pulse'],
        'put-on-sync.path': ['.local/bin/put-on'],
        'put-on-sync.timer': ['.local/bin/put-on'],
        'rclone-gdrive.service': ['.config/rclone/rclone.conf'],
        'flameshot-drive-upload.timer': ['.config/rclone/rclone.conf'],
        'aerc-gmail-initialize.service': ['.config/aerc/accounts.conf', '.config/isyncrc'],
    }
    if not (home / '.local/state/aerc-setup/maildir-ready').is_file():
        requirements['aerc-gmail-initialize.service'] += [
            '.local/state/aerc-setup/check-local-aerc.py',
            '.local/state/aerc-setup/gmail-initial.isyncrc',
        ]
    return [(unit, [rel for rel in needs if not (home / rel).is_file()])
            for unit, needs in requirements.items()]


def activate(home, apply):
    if apply and (os.geteuid() == 0 or home != Path.home().resolve()):
        raise SystemExit('Enable user services as the target user in their own home.')
    plan = service_plan(home)
    for unit, missing in plan:
        if missing:
            print(f'Skip {unit}: requires ' + ', '.join(missing))
        else:
            print(f'Enable {unit}' + ('' if apply else ' (preview)'))
    if not apply:
        return
    (home / 'Music/playlists').mkdir(parents=True, exist_ok=True)
    (home / 'Drive').mkdir(exist_ok=True)
    subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
    for unit, missing in plan:
        if not missing:
            subprocess.run(['systemctl', '--user', 'enable', '--now', unit], check=True)


def system_plan(home):
    account = pwd.getpwnam(home.owner())
    if Path(account.pw_dir).resolve() != home:
        raise SystemExit('Home must be the target account home directory.')
    files = {
        '/etc/systemd/logind.conf.d/20-grey-lid.conf': (REPO / 'assets/system/20-grey-lid.conf').read_bytes(),
        '/etc/systemd/logind.conf.d/30-power-button-hold.conf': (REPO / 'assets/system/30-power-button-hold.conf').read_bytes(),
        '/etc/X11/xorg.conf.d/30-grey-touchpad.conf': (home / '.config/xorg/30-touchpad.conf').read_bytes(),
    }
    return files


def apply_system(home, profile, apply, backup_root=Path('/var/backups/grey-alignment')):
    if apply:
        check_profile(profile)
        if os.geteuid() != 0:
            raise SystemExit('System apply needs sudo; specify --home for the target user.')
    files = system_plan(home)
    for filename in files:
        dest = Path(filename)
        if dest.is_symlink() or any(p.is_symlink() for p in dest.parents) or (dest.exists() and not dest.is_file()):
            raise SystemExit(f'Unsafe system destination: {dest}')
    backup = backup_root / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    if any(p.is_symlink() for p in [backup, *backup.parents]):
        raise SystemExit(f'Unsafe system backup destination: {backup}')
    for filename, data in files.items():
        target = Path(filename)
        if target.is_file() and target.read_bytes() == data:
            print(f'Unchanged {filename}')
            continue
        print(f'Update {filename}' + ('' if apply else ' (preview)'))
        if not apply:
            continue
        if target.exists():
            saved = backup / filename.lstrip('/')
            saved.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            shutil.copy2(target, saved)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + '.alignment-' + str(os.getpid()))
        try:
            with temporary.open('xb') as stream:
                stream.write(data)
            temporary.chmod(0o644)
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                temporary.unlink()
    for unit in ('NetworkManager.service', 'systemd-timesyncd.service', 'touchegg.service'):
        print(f'Enable {unit}' + ('' if apply else ' (preview)'))
        if apply:
            subprocess.run(['systemctl', 'enable', unit], check=True)
    if apply:
        subprocess.run(['systemctl', 'start', 'touchegg.service'], check=True)
        print('Logind changes take effect after reboot. Existing system files backed up under ' + str(backup))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['audit', 'missing', 'services', 'system', 'check-profile'])
    parser.add_argument('--full', action='store_true', help='Compare the entire compatible source package inventory')
    parser.add_argument('--profile', choices=['source', 'macbookpro11-4'], default='source')
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    if args.action == 'check-profile':
        check_profile(args.profile)
    elif args.action == 'missing':
        print('\n'.join(missing_packages(args.full, args.profile)))
    elif args.action == 'audit':
        missing = missing_packages(args.full, args.profile)
        print('Missing packages: ' + (' '.join(missing) if missing else 'none'))
        for name in ('codex', 'ncspot'):
            local = home / '.local/bin' / name
            print(f'Local {name}: ' + ('present' if local.is_file() else 'not present; see ALIGNMENT.md'))
        model = home / '.config/nerd-dictation/model/am/final.mdl'
        print('Dictation model: ' + ('present' if model.is_file() else 'requires a private transfer/download'))
        activate(home, False)
    elif args.action == 'services':
        if args.apply:
            check_profile(args.profile)
        activate(home, args.apply)
    else:
        apply_system(home, args.profile, args.apply)


if __name__ == '__main__':
    main()
