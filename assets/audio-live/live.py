#!/usr/bin/env python3
"""Arrow-key controls for our continuously running declarative DSP."""
import argparse
import curses
import fcntl
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from snapshots import DEFAULT_DATASET, Snapshots

from compiler import ROOT, LIMITS, SHAPE_LIMITS, PHASE_LIMITS, build, load, settings as declared_settings

FIELDS = [('frequency', 'Tone frequency', 'Hz', 10),
          ('mod_rate', 'Modulation rate', 'Hz', .1),
          ('mod_depth', 'Frequency modulation depth', 'Hz', 10),
          ('delay_ms', 'Echo delay', 'ms', 10),
          ('dry', 'Direct level', '', .05),
          ('echo', 'Echo level', '', .05),
          ('level', 'Master level', '', .01)]
SHAPE_FIELDS = [('drive', 'Distortion drive', '', .25), ('mix', 'Distortion wet mix', '', .05)]
PHASE_FIELDS = [('phase_frequency_1', 'First control phase rate', 'Hz', .1),
                ('phase_frequency_2', 'Second control phase rate', 'Hz', .1),
                ('phase_depth', 'Phase-driven drive depth', '', .1),
                ('phase_offset', 'Relative phase offset', 'rad', .1)]


def launch_spec(declaration=None):
    spec = load(declaration)
    if declaration is None:
        # Expose the new controls on the usual command, with both optional
        # contributions disabled. Explicit declarations remain authoritative.
        spec.setdefault('waveshaping', {'kind': 'tanh', 'drive': 4, 'mix': 0})
        spec.setdefault('relative_phase', {'mode': 'free_running', 'frequency_1_hz': 2,
                                         'frequency_2_hz': 2.25, 'drive_depth': 0,
                                         'offset_radians': 0})
    return spec


def fields_for(spec):
    return (FIELDS + (SHAPE_FIELDS if 'waveshaping' in spec else [])
            + (PHASE_FIELDS if 'relative_phase' in spec else []))


def adjust(settings, index, direction, fine=False, fields=None, spec=None):
    fields = fields or FIELDS
    spec = spec or load()
    key, _, _, step = fields[index]
    lo, hi = (LIMITS | SHAPE_LIMITS | PHASE_LIMITS)[key]
    if key == 'delay_ms':
        hi = min(hi, spec['max_delay_seconds'] * 1000)
    if key == 'phase_depth':
        hi = min(settings['drive'], 16-settings['drive'])
    settings[key] = max(lo, min(hi, round(settings[key] + direction * step * (.1 if fine else 1), 6)))
    if 'relative_phase' in spec:
        settings['phase_depth'] = min(settings['phase_depth'], settings['drive'], 16-settings['drive'])
        if spec['relative_phase']['mode'] == 'shared_clock' and key in ('phase_frequency_1','phase_frequency_2'):
            settings['phase_frequency_1'] = settings['phase_frequency_2'] = settings[key]


def stop(child):
    if child is not None and child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


def run(screen, engine, player, settings, spec=None, snapshots=None):
    spec = spec or load()
    fields = fields_for(spec)
    defaults = declared_settings(spec)
    curses.curs_set(0)
    screen.keypad(True)
    screen.timeout(50)
    selected = 0
    muted = True

    def send():
        values = [0 if key == 'level' and muted else settings[key] for key, _, _, _ in fields]
        engine.stdin.write((' '.join(map(str, values)) + '\n').encode())
        engine.stdin.flush()

    def line(y, text):
        height, width = screen.getmaxyx()
        if y < height - 1 and width > 2:
            screen.addnstr(y, 1, text, max(1, width - 2))

    send()
    while True:
        if engine.poll() is not None or player.poll() is not None:
            raise RuntimeError('Audio process stopped. Check audio-error.log and try another --device from aplay -L.')
        screen.erase()
        line(0, 'DECLARATIVE AUDIO / LIVE' + (' | DISTORTION + PHASE' if 'relative_phase' in spec else ''))
        line(1, f"Mono {spec['sample_rate']/1000:g} kHz | sine + frequency modulation + delayed history")
        if 'waveshaping' in spec:
            line(2, f"Optional {spec['waveshaping']['kind']} | drive 0 or wet mix 0 bypasses")
        line(3, 'MUTED - press SPACE to hear it' if muted else 'PLAYING - SPACE mutes')
        visible = max(1, screen.getmaxyx()[0] - 11)
        first = max(0, selected - visible + 1)
        for row, i in enumerate(range(first, min(first + visible, len(fields)))):
            key, label, unit, _ = fields[i]
            line(5 + row, ('> ' if i == selected else '  ') + f'{label:28} {settings[key]:8.2f} {unit}')
        bottom = 5 + min(visible, len(fields)) + 1
        line(bottom, 'UP/DOWN select | LEFT/RIGHT change | +/- fine change')
        line(bottom + 1, 'SPACE mute/unmute | r reset | s save sample | q quit')
        if snapshots:
            line(bottom + 2, snapshots.status)
        line(bottom + 3, 'Settings change during playback. Delay changes can bend pitch.')
        screen.refresh()
        key = screen.getch()
        if key in (ord('q'), ord('Q')):
            break
        if key == curses.KEY_UP:
            selected = (selected - 1) % len(fields)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(fields)
        elif key in (curses.KEY_LEFT, curses.KEY_RIGHT, ord('+'), ord('-')):
            adjust(settings, selected, -1 if key in (curses.KEY_LEFT, ord('-')) else 1,
                   key in (ord('+'), ord('-')), fields, spec)
            send()
        elif key == ord(' '):
            muted = not muted
            send()
        elif key in (ord('s'), ord('S')) and snapshots:
            snapshots.save(spec, settings, muted, fields[selected][0])
        elif key == ord('r'):
            settings.update(defaults)
            send()
    muted = True
    send()
    time.sleep(.12)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', default='default')
    parser.add_argument('--dataset-dir', type=Path, default=DEFAULT_DATASET,
                        help='Local WAV and parameter snapshot dataset directory')
    parser.add_argument('--build-only', action='store_true')
    parser.add_argument('--declaration', type=Path, help='Opt-in signal relationship declaration')
    args = parser.parse_args()
    if not shutil.which('c++'):
        parser.exit(1, 'Install gcc: sudo pacman -S --needed gcc\n')
    try:
        spec = launch_spec(args.declaration)
        binary = build(spec)
    except subprocess.CalledProcessError as error:
        parser.exit(1, 'Compilation failed:\n' + error.stderr.decode(errors='replace'))
    except (ValueError, OSError) as error:
        parser.exit(1, f'Invalid declaration: {error}\n')
    if args.build_only:
        print(binary)
        return 0
    if not shutil.which('aplay'):
        parser.exit(1, 'Install alsa-utils: sudo pacman -S --needed alsa-utils\n')
    if not sys.stdin.isatty():
        parser.exit(1, 'Run this interface in an interactive terminal.\n')
    settings = declared_settings(spec)
    engine = player = snapshots = None
    capture_read = capture_write = None
    result = 0
    with (ROOT / 'audio-error.log').open('wb') as errors:
        try:
            capture_read, capture_write = os.pipe()
            snapshots = Snapshots(capture_read, spec['sample_rate'], args.dataset_dir)
            capture_read = None  # reader owns this descriptor
            engine = subprocess.Popen([str(binary), '--realtime', '--capture-fd', str(capture_write)],
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors,
                                      bufsize=0, pass_fds=(capture_write,))
            os.close(capture_write)
            capture_write = None
            try:
                fcntl.fcntl(engine.stdout.fileno(), fcntl.F_SETPIPE_SZ, 4096)
            except OSError:
                pass
            player = subprocess.Popen(['aplay', '-q', '-D', args.device, '-t', 'raw',
                                       '-f', 'FLOAT_LE', '-r', str(spec['sample_rate']), '-c', '1',
                                       '--buffer-time=80000', '--period-time=10000'],
                                      stdin=engine.stdout, stdout=subprocess.DEVNULL, stderr=errors)
            engine.stdout.close()
            curses.wrapper(run, engine, player, settings, spec, snapshots)
        except KeyboardInterrupt:
            pass
        except (OSError, RuntimeError, curses.error) as error:
            print(str(error), file=sys.stderr)
            result = 1
        finally:
            stop(engine)
            for descriptor in (capture_read, capture_write):
                if descriptor is not None:
                    os.close(descriptor)
            if snapshots:
                snapshots.finish()
            # Closing the engine's pipe gives aplay EOF. Let it drain queued
            # muted audio before using a signal, avoiding interrupted writes.
            if player is not None and player.poll() is None:
                try:
                    player.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    stop(player)
            if engine and engine.stdin:
                engine.stdin.close()
    return result


if __name__ == '__main__':
    sys.exit(main())
