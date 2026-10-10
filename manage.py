#!/usr/bin/env python3
"""Snapshot or restore the explicit configuration manifest."""
import argparse
import json
import shutil
import configparser
import os
import re
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent


def select_firefox(home, explicit=None):
    if explicit:
        candidate = explicit.expanduser().resolve()
        if not candidate.is_dir() or not candidate.is_relative_to(home):
            raise SystemExit('Firefox profile must be an existing directory inside the target home.')
        return str(candidate.relative_to(home))
    for base in [home / '.config/mozilla/firefox', home / '.mozilla/firefox']:
        config = configparser.ConfigParser(interpolation=None)
        config.read(base / 'profiles.ini')
        installs = configparser.ConfigParser(interpolation=None)
        installs.read(base / 'installs.ini')
        candidates = []
        for settings, sections in [(config, [s for s in config.sections() if s.startswith('Install')]),
                                   (installs, installs.sections())]:
            for section in sections:
                value = settings.get(section, 'Default', fallback='')
                if value:
                    candidate = (base / value).resolve()
                    if candidate.is_dir() and candidate.is_relative_to(home) and candidate not in candidates:
                        candidates.append(candidate)
        if len(candidates) > 1:
            raise SystemExit('Multiple Firefox installation defaults; specify --firefox-profile.')
        if candidates:
            return str(candidates[0].relative_to(home))
        profiles = [s for s in config.sections() if s.startswith('Profile')]
        defaults = [s for s in profiles if config.get(s, 'Default', fallback='0') == '1']
        selected = defaults or profiles
        available = []
        for section in selected:
            value = config.get(section, 'Path', fallback='')
            candidate = base / value if config.get(section, 'IsRelative', fallback='1') == '1' else Path(value)
            candidate = candidate.resolve()
            if value and candidate.is_dir() and candidate.is_relative_to(home):
                available.append(candidate)
        if len(available) > 1:
            raise SystemExit('Multiple Firefox profiles without an installation default; specify --firefox-profile.')
        if available:
            return str(available[0].relative_to(home))
    return None


def portable_data(rel, data, home, firefox, profile):
    """Adapt text only; sound assets and other binaries retain their bytes."""
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        return data
    text = text.replace('/home/grey', str(home))
    if firefox:
        text = text.replace('.config/mozilla/firefox/59y3la6e.default-release', firefox)
    if rel == '.local/bin/audio-live':
        text = text.replace('cd "$HOME/src/arch-audio-live" || exit 1',
                            'project="$HOME/src/arch-audio-live"\n'
                            '[ -f "$project/live.py" ] || project="$HOME/.local/share/grey-audio-live"\n'
                            'cd "$project" || exit 1')
    if profile == 'macbookpro11-4':
        if rel == '.config/fastfetch/config.jsonc':
            config = json.loads(text)
            for module in config['modules']:
                if isinstance(module, dict) and module.get('type') in ('host', 'cpu'):
                    module.pop('format', None)
            text = json.dumps(config, indent=2) + '\n'
        if rel == '.config/i3/config':
            text = text.replace('xinput set-prop "bcm5974" "libinput Tapping Enabled" 1',
                                '~/.local/bin/touchpad-tapping')
        if rel == '.config/xorg/30-touchpad.conf':
            text = text.replace('    MatchProduct "bcm5974"\n', '')
        if rel == '.config/i3status/config':
            batteries = sorted(Path('/sys/class/power_supply').glob('*/type'))
            batteries = [p.parent for p in batteries if p.read_text().strip() == 'Battery']
            if batteries:
                text = text.replace('/sys/class/power_supply/BAT%d/uevent', str(batteries[0] / 'uevent'))
        if rel == '.xinitrc':
            text = text.replace('exec i3', 'if command -v xrdb >/dev/null 2>&1; then\n'
                                '    xrdb -merge "$HOME/.config/xorg/macbookpro-resources"\n'
                                'fi\nexec i3')
    return text.encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['snapshot', 'restore'])
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--apply', action='store_true', help='Actually restore; default is a preview')
    parser.add_argument('--portable', action='store_true', help='Adapt home paths and select an existing Firefox profile')
    parser.add_argument('--profile', choices=['source', 'macbookpro11-4'], default='source')
    parser.add_argument('--firefox-profile', type=Path, help='Explicit existing Firefox profile in the target home')
    args = parser.parse_args()
    if args.profile != 'source' and (args.action != 'restore' or not args.portable):
        parser.error('--profile requires restore --portable')
    home = args.home.expanduser().resolve()
    paths = json.loads((REPO / 'manifest.json').read_text())
    permissions_file = REPO / 'file-modes.json'
    permissions = json.loads(permissions_file.read_text()) if permissions_file.exists() else {}
    firefox = None
    if args.portable:
        if args.action != 'restore':
            parser.error('--portable is only for restore')
        firefox = select_firefox(home, args.firefox_profile)
    backup = home / '.local/state/dotfiles/backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    if any(p.is_symlink() for p in [backup, *backup.parents]):
        raise SystemExit(f'Refusing to write backups through symlink: {backup}')
    operations = []
    for rel in paths:
        path = Path(rel)
        if path.is_absolute() or '..' in path.parts:
            raise SystemExit(f'Invalid manifest path: {rel}')
        live, stored = home / path, REPO / 'home' / path
        if args.portable:
            if rel == '.config/QtProject.conf':
                continue  # File-dialog history is specific to the old machine.
            if rel.startswith('.config/mozilla/firefox/59y3la6e.default-release/'):
                if firefox is None:
                    print('Skip Firefox styling/preferences: start Firefox once, then rerun.')
                    continue
                live = home / firefox / Path(rel).relative_to('.config/mozilla/firefox/59y3la6e.default-release')
        source, target = (live, stored) if args.action == 'snapshot' else (stored, live)
        if not source.is_file() or source.is_symlink():
            raise SystemExit(f'Missing or symlink source: {source}')
        if target.is_symlink() or any(p.is_symlink() for p in target.parents):
            raise SystemExit(f'Refusing to write through symlink: {target}')
        if target.exists() and not target.is_file():
            raise SystemExit(f'Destination is not a regular file: {target}')
        data = source.read_bytes()
        mode = source.stat().st_mode & 0o777
        if args.action == 'restore':
            mode = permissions.get(rel, mode)
        if not isinstance(mode, int) or mode < 0 or mode > 0o777:
            raise SystemExit(f'Invalid file mode: {rel}')
        if args.portable:
            data = portable_data(rel, data, home, firefox, args.profile)
            if rel.endswith('/user.js') and target.is_file():
                mode = target.stat().st_mode & 0o777
                existing = target.read_text()
                preference = 'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);'
                pattern = r'user_pref\([ \t]*"toolkit\.legacyUserProfileCustomizations\.stylesheets"[ \t]*,[ \t]*(?:true|false)[ \t]*\);'
                if re.search(pattern, existing):
                    existing = re.sub(pattern, preference, existing)
                else:
                    existing = existing.rstrip() + '\n' + data.decode('utf-8')
                data = existing.encode('utf-8')
        operations.append((rel, source, target, data, mode))
    if args.action == 'restore':
        for rel, asset in json.loads((REPO / 'asset-manifest.json').read_text()).items():
            for value in (rel, asset):
                if Path(value).is_absolute() or '..' in Path(value).parts:
                    raise SystemExit(f'Invalid asset path: {value}')
            source, target = REPO / asset, home / rel
            if not source.is_file() or source.is_symlink():
                raise SystemExit(f'Missing asset: {source}')
            if target.is_symlink() or any(p.is_symlink() for p in target.parents) or (target.exists() and not target.is_file()):
                raise SystemExit(f'Unsafe asset destination: {target}')
            operations.append((rel, source, target, source.read_bytes(), source.stat().st_mode & 0o777))
    if args.action == 'restore' and args.profile == 'macbookpro11-4':
        target = home / '.config/xorg/macbookpro-resources'
        if target.is_symlink() or any(p.is_symlink() for p in target.parents) or (target.exists() and not target.is_file()):
            raise SystemExit(f'Unsafe resource destination: {target}')
        data = target.read_bytes() if target.is_file() else b'Xft.dpi: 192\nXft.antialias: true\nXft.hintstyle: hintslight\n'
        mode = target.stat().st_mode & 0o777 if target.is_file() else 0o644
        operations.append(('Retina resources', None, target, data, mode))
    count = 0
    unchanged = 0
    for rel, source, target, data, mode in operations:
        if target.is_file() and target.read_bytes() == data and target.stat().st_mode & 0o777 == mode:
            unchanged += 1
            continue
        if args.action == 'restore' and not args.apply:
            print(f'{"Update" if target.exists() else "Add"} {target.relative_to(home)}')
            count += 1
            continue
        if args.action == 'restore' and target.exists():
            saved = backup / target.relative_to(home)
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + '.dotfiles-tmp-' + str(os.getpid()))
        try:
            with temporary.open('xb') as stream:
                stream.write(data)
            temporary.chmod(mode)
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                temporary.unlink()
        count += 1
    print(f'{args.action}: {count} files' + (' (preview; use --apply)' if args.action == 'restore' and not args.apply else ''))
    print(f'Unchanged: {unchanged} files')
    if backup.exists():
        print(f'Backups: {backup}')


if __name__ == '__main__':
    main()
