#!/usr/bin/env python3
"""Refresh the reviewed configuration allowlist, package inventory and audio sources."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parent
HOME = Path.home()
ADDITIONS = [
    '.config/air-theme/SLUNTSHACK.txt',
    '.config/systemd/user/aerc-gmail-initialize.service',
    '.config/systemd/user/aerc-gmail-sync.service',
    '.config/systemd/user/aerc-gmail-sync.timer',
    '.config/systemd/user/put-on-sync.service',
    '.config/systemd/user/put-on-sync.path',
    '.config/systemd/user/put-on-sync.timer',
    '.config/mozilla/native-messaging-hosts/ff2mpv.json',
    '.mozilla/native-messaging-hosts/ff2mpv.json',
    '.local/bin/aerc-gmail-initialize', '.local/bin/aerc-gmail-sync',
    '.local/bin/put-on', '.local/bin/audio-live', '.local/bin/drive',
    '.local/bin/firefox-theme-rollback',
    '.local/share/applications/ncspot.desktop',
    '.local/share/codex-alerts/gong.wav', '.local/share/codex-alerts/ding.wav',
    '.local/share/codex-alerts/previous-notify.py',
]
AUDIO_FILES = [
    'live.py', 'compiler.py', 'snapshots.py', 'engine.cpp',
    'dsp-template.hpp', 'relations.hpp', 'declaration.json', 'README.md',
    'examples/tanh.json', 'examples/hard-clip.json',
    'examples/phase-drive.json', 'examples/shared-phase.json', 'examples/README.md',
]


def query(*args):
    result = subprocess.run(['pacman', *args], capture_output=True, text=True)
    if result.returncode and not (result.returncode == 1 and not result.stdout and not result.stderr):
        raise RuntimeError(result.stderr.strip() or 'pacman query failed')
    return result.stdout.splitlines()


def main():
    paths = sorted(set(json.loads((REPO / 'manifest.json').read_text())) | set(ADDITIONS))
    audio = HOME / 'src/arch-audio-live'
    sources = [HOME / path for path in paths] + [audio / path for path in AUDIO_FILES]
    sources.append(Path('/usr/local/bin/grey-drive'))
    for source in sources:
        if source.is_symlink() or not source.is_file():
            raise SystemExit(f'Unavailable reviewed source: {source}')
    (REPO / 'manifest.json').write_text(json.dumps(paths, indent=2) + '\n')
    (REPO / 'file-modes.json').write_text(json.dumps({rel: (HOME / rel).stat().st_mode & 0o777 for rel in paths}, indent=2) + '\n')
    subprocess.run(['python3', str(REPO / 'manage.py'), 'snapshot'], check=True)
    assets = {'.local/bin/touchpad-tapping': 'assets/touchpad-tapping'}
    for relative in AUDIO_FILES:
        target = REPO / 'assets/audio-live' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(audio / relative, target)
        assets['.local/share/grey-audio-live/' + relative] = str(target.relative_to(REPO))
    (REPO / 'asset-manifest.json').write_text(json.dumps(assets, indent=2) + '\n')
    shutil.copy2('/usr/local/bin/grey-drive', REPO / 'tools/drive-use/grey-drive.py')
    explicit = set(query('-Qqe'))
    native = set(query('-Qqn'))
    hardware = {'broadcom-wl-dkms'}
    packages = []
    for line in query('-Q'):
        name, version = line.split(maxsplit=1)
        packages.append({'name': name, 'version': version, 'explicit': name in explicit,
                         'native': name in native, 'source_hardware_only': name in hardware})
    for filename, names in [
        ('official.txt', native), ('explicit.txt', explicit),
        ('foreign.txt', {p['name'] for p in packages} - native),
        ('full.txt', native - hardware), ('source-hardware.txt', hardware & native),
    ]:
        (REPO / 'packages' / filename).write_text('\n'.join(sorted(names)) + '\n')
    software = []
    for name in ('ncspot', 'codex'):
        path = HOME / '.local/bin' / name
        if path.is_file():
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            software.append({'name': name, 'path': str(path.relative_to(HOME)),
                             'resolved_path': str(path.resolve()).replace(str(HOME), '~'),
                             'sha256': digest, 'distribution': 'private backup; not committed'})
    inventory = {'captured_utc': datetime.now(timezone.utc).isoformat(),
                 'source_model': Path('/sys/class/dmi/id/product_name').read_text().strip(),
                 'packages': packages, 'non_pacman_software': software,
                 'audio_source': {'repository': 'https://github.com/greysullivan/yuley',
                                  'commit': subprocess.check_output(['git', '-C', str(audio), 'rev-parse', 'HEAD'], text=True).strip()},
                 'note': 'Versions are an inventory, not pins. Default alignment preserves installed packages.'}
    (REPO / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'Captured {len(paths)} configuration files and {len(packages)} installed packages.')


if __name__ == '__main__':
    main()
