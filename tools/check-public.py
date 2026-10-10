#!/usr/bin/env python3
"""Check staged filenames and blobs for private data before publishing."""
from pathlib import Path
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
paths = subprocess.check_output(['git', '-C', str(REPO), 'diff', '--cached', '--name-only',
                                 '--diff-filter=ACM', '-z']).decode().split('\0')
forbidden = {'accounts.conf', 'rclone.conf', 'isyncrc', 'hosts.yml', 'auth.json',
             'backup-password', 'cookie', 'userstate.cbor', 'gmail-app-password'}
patterns = [rb'-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----',
            rb'gh[opsur]_[A-Za-z0-9]{20,}', rb'github_pat_[A-Za-z0-9_]{20,}',
            rb'AKIA[A-Z0-9]{16}', rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}']
failed = []
for name in filter(None, paths):
    path = Path(name)
    if path.name in forbidden or any(p in {'.ssh', '.codex', 'Mail', 'Notes', 'restic', 'migration-private'} for p in path.parts):
        failed.append(name + ': forbidden private path')
        continue
    data = subprocess.check_output(['git', '-C', str(REPO), 'show', ':' + name])
    if any(re.search(pattern, data) for pattern in patterns):
        failed.append(name + ': credential/private-key pattern (value withheld)')
if failed:
    print('\n'.join(failed), file=sys.stderr)
    raise SystemExit(1)
print(f'Checked {len(list(filter(None, paths)))} staged files; no forbidden paths or credential patterns.')
print('This automated check supplements manual review; it is not a guarantee that all secrets are detected.')
