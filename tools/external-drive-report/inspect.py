#!/usr/bin/python3
"""Read-only inspection of Grey's identified LaCie drive; artifacts stay internal."""
import collections
import datetime as dt
import heapq
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import time

HOME = Path('/home/grey')
REPORT = HOME / 'external-drive-report-2026-10-06.md'
DATA = HOME / 'setup/external-drive-report/data'
SERIAL = 'WCJBN19R'
UUID = '00F2-EA07'
errors = []
records = {}


def run(name, args, timeout=30):
    try:
        r = subprocess.run(args, capture_output=True, text=True,
                           errors='replace', timeout=timeout)
        item = {'args': args, 'code': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}
    except (OSError, subprocess.TimeoutExpired) as e:
        item = {'args': args, 'code': None, 'stdout': '', 'stderr': str(e)}
    records[name] = item
    (DATA / (name + '.json')).write_text(json.dumps(item, indent=2) + '\n')
    return item


def props(text):
    return dict(line.split('=', 1) for line in text.splitlines() if '=' in line)


def size(n):
    return f'{n / 1024**3:,.2f} GiB ({n:,} bytes)'


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')


def table(headers, rows):
    lines = ['| ' + ' | '.join(headers) + ' |',
             '| ' + ' | '.join('---' for _ in headers) + ' |']
    lines += ['| ' + ' | '.join(cell(v) for v in row) + ' |' for row in rows]
    return '\n'.join(lines)


def inventory(root):
    """Single postorder walk; never follows links or opens file contents."""
    largest_files, largest_dirs = [], []
    extensions = collections.defaultdict(lambda: [0, 0])
    top = []
    counts = {'files': 0, 'directories': 0, 'symlinks': 0, 'other': 0}
    failures = []
    oldest = newest = None
    v = os.statvfs(root)
    rootdev = os.stat(root).st_dev
    progress_at = time.monotonic()
    # Each frame has its own open scandir iterator and accumulated totals.
    stack = [{'path': root, 'it': os.scandir(root), 'logical': 0, 'allocated': 0, 'files': 0}]
    try:
        while stack:
            frame = stack[-1]
            try:
                entry = next(frame['it'])
            except (StopIteration, OSError) as e:
                if isinstance(e, OSError):
                    failures.append({'path': str(frame['path'].relative_to(root)), 'error': str(e)})
                frame['it'].close()
                stack.pop()
                if stack:
                    rel = str(frame['path'].relative_to(root))
                    heapq.heappush(largest_dirs, (frame['logical'], frame['files'], rel))
                    if len(largest_dirs) > 30:
                        heapq.heappop(largest_dirs)
                    parent = stack[-1]
                    for key in ('logical', 'allocated', 'files'):
                        parent[key] += frame[key]
                    if len(stack) == 1:
                        top.append({'path': rel, 'bytes': frame['logical'], 'files': frame['files'], 'type': 'directory'})
                else:
                    totals = frame
                continue
            try:
                s = entry.stat(follow_symlinks=False)
                rel = str(Path(entry.path).relative_to(root))
                if s.st_dev != rootdev:
                    failures.append({'path': rel, 'error': 'Skipped another filesystem'})
                    continue
                if stat.S_ISDIR(s.st_mode):
                    counts['directories'] += 1
                    stack.append({'path': Path(entry.path), 'it': os.scandir(entry.path), 'logical': 0, 'allocated': 0, 'files': 0})
                elif stat.S_ISREG(s.st_mode):
                    counts['files'] += 1
                    frame['files'] += 1
                    frame['logical'] += s.st_size
                    frame['allocated'] += s.st_blocks * 512
                    ext = Path(entry.name).suffix.lower() or '(no extension)'
                    extensions[ext][0] += 1
                    extensions[ext][1] += s.st_size
                    heapq.heappush(largest_files, (s.st_size, rel))
                    if len(largest_files) > 20:
                        heapq.heappop(largest_files)
                    oldest = s.st_mtime if oldest is None else min(oldest, s.st_mtime)
                    newest = s.st_mtime if newest is None else max(newest, s.st_mtime)
                    if len(stack) == 1:
                        top.append({'path': rel, 'bytes': s.st_size, 'files': 1, 'type': 'file'})
                elif stat.S_ISLNK(s.st_mode):
                    counts['symlinks'] += 1
                else:
                    counts['other'] += 1
            except OSError as e:
                failures.append({'path': entry.path, 'error': str(e)})
            if time.monotonic() - progress_at >= 15:
                message = f"Scanned {counts['files']:,} files and {counts['directories']:,} folders"
                print(message, flush=True)
                (DATA / 'progress.txt').write_text(message + '\n')
                progress_at = time.monotonic()
    finally:
        for frame in stack:
            frame['it'].close()
    return {'counts': counts, 'logical_bytes': totals['logical'], 'allocated_file_bytes': totals['allocated'],
            'filesystem_bytes': v.f_blocks * v.f_frsize,
            'used_bytes': (v.f_blocks - v.f_bfree) * v.f_frsize,
            'free_bytes': v.f_bfree * v.f_frsize, 'available_bytes': v.f_bavail * v.f_frsize,
            'top_level': sorted(top, key=lambda x: x['bytes'], reverse=True),
            'largest_files': sorted(largest_files, reverse=True),
            'largest_directories': sorted(largest_dirs, reverse=True),
            'extensions': dict(extensions), 'errors': failures,
            'oldest_mtime': oldest, 'newest_mtime': newest}


def make_report(disk, p, inv, mounted, unmounted):
    now = dt.datetime.now().astimezone().isoformat(timespec='seconds')
    complete = inv is not None and not inv['errors'] and unmounted
    lines = ['# External drive report', '', f'Inspection time: {now}', '',
             f"**{'Contents scan completed' if complete else 'Inspection incomplete'}**. Drive identity: LaCie Rugged USB-C, disk serial `{SERIAL}`, data UUID `{UUID}`.", '',
             '## Hardware and connection', '', table(['Property', 'Observed value'], [
                 ('Internal disk model', disk['model']), ('Disk serial', SERIAL),
                 ('Enclosure model', p.get('ID_USB_MODEL', 'Unavailable')),
                 ('Enclosure serial', p.get('ID_USB_SERIAL_SHORT', 'Unavailable')),
                 ('Disk firmware', p.get('ID_REVISION', 'Unavailable')),
                 ('Enclosure revision', p.get('ID_USB_REVISION', 'Unavailable')),
                 ('Capacity', size(disk['size'])), ('Partition table', disk.get('pttype')),
                 ('Rotation speed', p.get('ID_ATA_ROTATION_RATE_RPM', 'Unavailable') + ' RPM'),
                 ('Logical / physical sector', f"{disk['log-sec']} / {disk['phy-sec']} bytes"),
                 ('USB driver', p.get('ID_USB_DRIVER', 'Unavailable')),
                 ('Negotiated USB speed', records.get('usb_speed', {}).get('stdout', '').strip() + ' Mbps'),
                 ('SMART capability / enabled', f"{p.get('ID_ATA_FEATURE_SET_SMART', '?')} / {p.get('ID_ATA_FEATURE_SET_SMART_ENABLED', '?')}"),
                 ('Read / write cache enabled', f"{p.get('ID_ATA_READ_LOOKAHEAD_ENABLED', '?')} / {p.get('ID_ATA_WRITE_CACHE_ENABLED', '?')}"),
             ]), '',
             'The observed 480 Mbps connection is USB 2.0 speed. Its signalling rate is equivalent to 60 MB/s before protocol overhead; actual file throughput was not measured. The cause of the negotiated speed has not been established.', '',
             '## Partitions', '', table(['Device', 'Capacity', 'Filesystem', 'Label', 'UUID', 'GPT type'], [
                 (x['name'], size(x['size']), x.get('fstype'), x.get('label'), x.get('uuid'), x.get('parttype'))
                 for x in disk.get('children', [])]), '',
             '## Hardware health', '']
    smart = records.get('smart_sat', records.get('smart', {}))
    try:
        data = json.loads(smart.get('stdout', '{}'))
    except ValueError:
        data = {}
    status = data.get('smart_status', {}).get('passed')
    lines += [f"SMART overall result: **{('PASSED' if status else 'FAILED') if status is not None else 'Unavailable'}**.", '',
              table(['Metric', 'Value'], [
                  ('Temperature', str(data.get('temperature', {}).get('current', 'Unavailable')) + ' °C'),
                  ('Power-on hours', data.get('power_on_time', {}).get('hours', 'Unavailable')),
                  ('Power cycles', data.get('power_cycle_count', 'Unavailable')),
                  ('SMART command exit code', smart.get('code', 'Not run')),
              ]), '']
    attrs = data.get('ata_smart_attributes', {}).get('table', [])
    if attrs:
        lines += [table(['ID', 'Attribute', 'Normalized', 'Worst', 'Threshold', 'Raw', 'Failure'], [
            (a['id'], a.get('name'), a.get('value'), a.get('worst'), a.get('thresh'),
             a.get('raw', {}).get('string', a.get('raw', {}).get('value')), a.get('when_failed', ''))
            for a in attrs]), '']
    lines += [('Collected SMART JSON, including any available error and self-test logs, is retained in the evidence folder.' if smart else 'SMART data has not been collected.'), '',
              'No new self-test was started. A passing overall result alone does not establish that every sector is readable.', '',
              '## Filesystem check', '']
    fsck = records.get('fsck', {})
    lines += [f"Read-only exFAT check exit code: `{fsck.get('code', 'Not run')}`.", '',
              '```text', (fsck.get('stdout', '') + fsck.get('stderr', '')).strip() or 'Unavailable.', '```', '',
              'The check uses `fsck.exfat -n`, with repairs disabled. A timeout or nonzero result is not reported as a clean filesystem.', '',
              '## Storage and contents', '']
    if inv is None:
        lines += ['Used/free space and file inventory are unavailable: the data partition has not been inspected.', '']
    else:
        lines += [table(['Metric', 'Value'], [
            ('Filesystem capacity', size(inv['filesystem_bytes'])), ('Used', size(inv['used_bytes'])),
            ('Free', size(inv['free_bytes'])), ('Available', size(inv['available_bytes'])),
            ('Regular files', f"{inv['counts']['files']:,}"), ('Folders excluding root', f"{inv['counts']['directories']:,}"),
            ('Symlinks / other entries', f"{inv['counts']['symlinks']} / {inv['counts']['other']}"),
            ('Logical file sizes', size(inv['logical_bytes'])), ('Allocated file sizes', size(inv['allocated_file_bytes'])),
            ('Used minus allocated file sizes', size(inv['used_bytes'] - inv['allocated_file_bytes'])),
            ('Unreadable / skipped paths', len(inv['errors']))]), '',
            'Filesystem usage includes directory allocations, filesystem metadata, and any allocations not represented by readable regular files. Logical sizes exclude allocation padding. Nested directory totals overlap and must not be added together.', '',
            '### Top-level entries by size', '', table(['Path', 'Type', 'Files', 'Logical size'], [
                (x['path'], x['type'], x['files'], size(x['bytes'])) for x in inv['top_level']]), '',
            '### Largest 30 directories', '', table(['Path', 'Files', 'Logical size'], [
                (path, count, size(n)) for n, count, path in inv['largest_directories']]), '',
            '### Largest 20 files', '', table(['Path', 'Logical size'], [
                (path, size(n)) for n, path in inv['largest_files']]), '',
            '### File types by size', '', table(['Extension', 'Count', 'Logical size'], [
                (ext, count, size(n)) for ext, (count, n) in sorted(inv['extensions'].items(), key=lambda x: x[1][1], reverse=True)]), '',
            'Types are inferred from filename extensions, not file contents.', '',
            '### Modification dates', '']
        for label, key in [('Oldest file modification', 'oldest_mtime'), ('Newest file modification', 'newest_mtime')]:
            value = inv[key]
            try:
                date = dt.datetime.fromtimestamp(value).astimezone().isoformat() if value is not None else 'No regular files'
            except (ValueError, OverflowError, OSError):
                date = f'Unrepresentable timestamp: {value}'
            lines += [f'- {label}: {date}']
        lines += ['', 'These are filesystem modification timestamps, not verified creation dates.', '']
        if inv['errors']:
            lines += ['### Unreadable or skipped paths', '', table(['Path', 'Reason'], [
                (x['path'], x['error']) for x in inv['errors']]), '']
    lines += ['## Kernel evidence', '', '```text',
              records.get('kernel', {}).get('stdout', '').strip() or 'Unavailable.', '```', '',
              '## Findings and limits', '',
              '- The drive was detected with two GPT partitions; the main partition is labelled `grey home` and uses exFAT.',
              '- USB connection speed is 480 Mbps; no performance benchmark was run.',
              '- The kernel reports minimum/optimal I/O sizes that do not match the 4 KiB physical block size. These messages alone do not establish media damage.',
              '- No repairs, write benchmarks, full sector scans, or personal-file content reads were performed.',
              f'- Temporary read-only mount created: {mounted}. Temporary mount successfully removed: {unmounted}.', '']
    if status is False:
        lines += ['- **SMART reports a failed overall health result.**', '']
    if errors:
        lines += ['### Unavailable checks and collection errors', ''] + ['- ' + cell(e) for e in errors] + ['']
    lines += ['## Evidence', '', f'Command outputs and the inventory JSON are saved under `{DATA}`. The evidence folder can contain personal filenames.', '']
    REPORT.write_text('\n'.join(lines))


def main():
    DATA.mkdir(parents=True, exist_ok=True, mode=0o700)
    raw = run('devices', ['lsblk', '-b', '-J', '-o', 'NAME,SIZE,MODEL,SERIAL,FSTYPE,LABEL,UUID,MOUNTPOINTS,PTTYPE,PARTTYPE,PARTLABEL,START,LOG-SEC,PHY-SEC,ROTA,RO'])
    disks = [d for d in json.loads(raw['stdout'])['blockdevices'] if d.get('serial') == SERIAL]
    if len(disks) != 1:
        raise SystemExit('Expected LaCie disk serial not found uniquely; stopped without accessing a drive.')
    disk = disks[0]
    partitions = [x for x in disk.get('children', []) if x.get('uuid') == UUID]
    if len(partitions) != 1 or partitions[0].get('fstype') != 'exfat':
        raise SystemExit('Expected exFAT data UUID not found uniquely; stopped.')
    device = '/dev/' + disk['name']
    part = '/dev/' + partitions[0]['name']
    p = props(run('identity', ['udevadm', 'info', '--query=property', '--path=/sys/block/' + disk['name']])['stdout'])
    usb = Path('/sys' + p['DEVPATH'])
    for ancestor in usb.parents:
        if (ancestor / 'speed').is_file():
            run('usb_speed', ['cat', str(ancestor / 'speed')])
            break
    run('kernel', ['journalctl', '-k', '-b', '--no-pager', '-g', rf'\[{disk["name"]}\]|exfat.*{disk["name"]}|I/O error.*{disk["name"]}|Buffer I/O.*{disk["name"]}', '-n', '100'])
    mounted = unmounted = False
    inv = None
    mountpoint = None
    try:
        if os.geteuid() != 0:
            errors.append('Administrator access is required for SMART, filesystem checking, mounting, and contents inspection. Run the prepared script with sudo to complete these checks.')
            return
        missing = [pkg for cmd, pkg in [('smartctl', 'smartmontools'), ('fsck.exfat', 'exfatprogs')] if not shutil.which(cmd)]
        if missing:
            print('Installing inspection tools on the internal system: ' + ', '.join(missing), flush=True)
            install = run('tool_install', ['pacman', '-S', '--needed', '--noconfirm', *missing], timeout=300)
            if install['code'] != 0:
                errors.append('Tool installation failed; unavailable checks are explicitly omitted. See tool_install.json.')
        if shutil.which('smartctl'):
            smart = run('smart', ['smartctl', '-x', '-j', device], timeout=60)
            try:
                readable = json.loads(smart['stdout']).get('smart_status') is not None
            except ValueError:
                readable = False
            if not readable:
                run('smart_sat', ['smartctl', '-x', '-j', '-d', 'sat', device], timeout=60)
        else:
            errors.append('smartctl unavailable; SMART metrics and diagnostic logs were not read.')
        mounts = run('existing_mounts', ['findmnt', '-rn', '-S', part, '-o', 'TARGET,OPTIONS'])
        if mounts['code'] not in (0, 1) or mounts['stdout'].strip():
            errors.append('Data partition is already mounted, or its mount state could not be verified. Stopped before filesystem check and contents scan; existing mount left untouched.')
            return
        if shutil.which('fsck.exfat'):
            print('Checking exFAT without repairs (up to 10 minutes)...', flush=True)
            run('fsck', ['fsck.exfat', '-n', part], timeout=600)
        else:
            errors.append('fsck.exfat unavailable; filesystem consistency has not been checked.')
        # Reconfirm both identifiers immediately before mounting.
        actual_uuid = run('confirm_uuid', ['blkid', '-s', 'UUID', '-o', 'value', part])['stdout'].strip()
        actual_serial = run('confirm_serial', ['lsblk', '-dn', '-o', 'SERIAL', device])['stdout'].strip()
        if actual_uuid != UUID or actual_serial != SERIAL:
            errors.append('Drive identity changed during inspection; contents scan stopped.')
            return
        mountpoint = Path(tempfile.mkdtemp(prefix='external-drive-inspection-', dir='/mnt'))
        result = run('mount', ['mount', '-t', 'exfat', '-o', 'ro,nosuid,nodev,noexec', part, str(mountpoint)])
        if result['code'] != 0:
            errors.append('Read-only mount failed: ' + result['stderr'].strip())
            return
        mounted = True
        check = run('verify_mount', ['findmnt', '-J', '--mountpoint', str(mountpoint), '-o', 'SOURCE,TARGET,FSTYPE,OPTIONS'])
        fs = json.loads(check['stdout'])['filesystems'][0]
        if fs['fstype'] != 'exfat' or not {'ro', 'nosuid', 'nodev', 'noexec'} <= set(fs['options'].split(',')) or os.path.realpath(fs['source']) != os.path.realpath(part):
            errors.append('Read-only mount verification failed; no contents scan performed.')
            return
        print('Read-only mount verified. Scanning names and metadata...', flush=True)
        inv = inventory(mountpoint)
        (DATA / 'inventory.json').write_text(json.dumps(inv, indent=2, ensure_ascii=True) + '\n')
    except Exception as e:
        errors.append(f'{type(e).__name__}: {e}')
    finally:
        if mounted:
            result = run('unmount', ['umount', str(mountpoint)], timeout=60)
            unmounted = result['code'] == 0
            if not unmounted:
                errors.append('Temporary read-only mount could not be removed: ' + result['stderr'].strip())
        if mountpoint is not None and (not mounted or unmounted):
            mountpoint.rmdir()
        make_report(disk, p, inv, mounted, unmounted)
        uid, gid = int(os.environ.get('SUDO_UID', os.getuid())), int(os.environ.get('SUDO_GID', os.getgid()))
        if os.geteuid() == 0:
            for path in [REPORT, DATA, *DATA.iterdir()]:
                os.chown(path, uid, gid)
        print(f'Report saved: {REPORT}', flush=True)
        if errors:
            print('Incomplete checks: ' + '; '.join(errors), flush=True)


if __name__ == '__main__':
    main()
