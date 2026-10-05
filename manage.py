#!/usr/bin/env python3
"""Snapshot or restore the explicit configuration manifest."""
import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['snapshot', 'restore'])
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--apply', action='store_true', help='Actually restore; default is a preview')
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    paths = json.loads((REPO / 'manifest.json').read_text())
    backup = home / '.local/state/dotfiles/backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    count = 0
    for rel in paths:
        path = Path(rel)
        if path.is_absolute() or '..' in path.parts:
            raise SystemExit(f'Invalid manifest path: {rel}')
        live, stored = home / path, REPO / 'home' / path
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
            saved = backup / path
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        count += 1
    print(f'{args.action}: {count} files' + (' (preview; use --apply)' if args.action == 'restore' and not args.apply else ''))
    if backup.exists():
        print(f'Backups: {backup}')


if __name__ == '__main__':
    main()
