#!/usr/bin/env python3
"""Snapshot or restore the explicit configuration manifest."""
import argparse
import json
import shutil
import configparser
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['snapshot', 'restore'])
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--apply', action='store_true', help='Actually restore; default is a preview')
    parser.add_argument('--portable', action='store_true', help='Adapt home paths and select an existing Firefox profile')
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    paths = json.loads((REPO / 'manifest.json').read_text())
    firefox = None
    if args.portable:
        if args.action != 'restore':
            parser.error('--portable is only for restore')
        for base in [home / '.config/mozilla/firefox', home / '.mozilla/firefox']:
            config = configparser.ConfigParser()
            config.read(base / 'profiles.ini')
            profiles = [s for s in config.sections() if s.startswith('Profile')]
            profiles.sort(key=lambda s: config.get(s, 'Default', fallback='0') != '1')
            for section in profiles:
                value = config.get(section, 'Path', fallback='')
                candidate = base / value if config.get(section, 'IsRelative', fallback='1') == '1' else Path(value)
                if value and candidate.is_dir() and candidate.is_relative_to(home):
                    firefox = str(candidate.relative_to(home))
                    break
            if firefox:
                break
    backup = home / '.local/state/dotfiles/backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    count = 0
    for rel in paths:
        path = Path(rel)
        if path.is_absolute() or '..' in path.parts:
            raise SystemExit(f'Invalid manifest path: {rel}')
        live, stored = home / path, REPO / 'home' / path
        if args.portable:
            if rel == '.config/QtProject.conf':
                continue  # File-dialog history is specific to the old machine.
            if '/chrome/userChrome.css' in rel:
                if firefox is None:
                    print('Skip Firefox stylesheet: start Firefox once, then rerun.')
                    continue
                live = home / firefox / 'chrome/userChrome.css'
        source, target = (live, stored) if args.action == 'snapshot' else (stored, live)
        if not source.is_file() or source.is_symlink():
            raise SystemExit(f'Missing or symlink source: {source}')
        if args.action == 'restore' and not args.apply:
            print(f'Restore {rel}')
            count += 1
            continue
        if target.is_symlink() or any(p.is_symlink() for p in target.parents):
            raise SystemExit(f'Refusing to write through symlink: {target}')
        if args.action == 'restore' and target.exists():
            saved = backup / target.relative_to(home)
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if args.portable:
            text = target.read_text().replace('/home/grey', str(home))
            if firefox:
                text = text.replace('.config/mozilla/firefox/59y3la6e.default-release', firefox)
            target.write_text(text)
        count += 1
    print(f'{args.action}: {count} files' + (' (preview; use --apply)' if args.action == 'restore' and not args.apply else ''))
    if backup.exists():
        print(f'Backups: {backup}')


if __name__ == '__main__':
    main()
