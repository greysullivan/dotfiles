"""Bounded live-audio side channel and local float WAV snapshot dataset."""
import copy
from collections import deque
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import struct
import threading
import time
import uuid

from compiler import LIMITS, SHAPE_LIMITS, PHASE_LIMITS, PHASE_KEYS

DEFAULT_DATASET = Path.home() / 'Music' / 'audio-live-samples'
KEYS = list(LIMITS) + list(SHAPE_LIMITS) + list(PHASE_LIMITS)
PACKET = struct.Struct('=QI30d1024s')


def recipe(spec, controls):
    result = copy.deepcopy(spec)
    result['controls'] = {key: controls[key] for key in LIMITS}
    if 'waveshaping' in result:
        result['waveshaping'].update({key: controls[key] for key in SHAPE_LIMITS})
    if 'relative_phase' in result:
        result['relative_phase'].update({field: controls[key] for key, field in PHASE_KEYS.items()})
    return result


def positions(spec, controls):
    result = {}
    for key, value in controls.items():
        lo, hi = (LIMITS | SHAPE_LIMITS | PHASE_LIMITS)[key]
        if key == 'delay_ms':
            hi = min(hi, spec['max_delay_seconds'] * 1000)
        if key == 'phase_depth':
            hi = min(controls['drive'], 16-controls['drive'])
        result[key] = {'value': value, 'minimum': lo, 'maximum': hi,
                       'position': (value-lo)/(hi-lo) if hi > lo else 0}
    return result


def float_wav(rate, audio):
    """IEEE float32 mono WAV: preserve exactly the samples sent to aplay."""
    return (struct.pack('<4sI4s4sIHHIIHH4sI', b'RIFF', 36+len(audio), b'WAVE',
                        b'fmt ', 16, 3, 1, rate, rate*4, 4, 32, b'data', len(audio)) + audio)


class Snapshots:
    def __init__(self, fd, rate, dataset=DEFAULT_DATASET):
        self.dataset = Path(dataset).expanduser().resolve()
        self.dataset.mkdir(parents=True, exist_ok=True)
        self.rate = rate
        self.blocks = deque(maxlen=(5*rate+255)//256)
        self.lock = threading.Lock()
        self.status = 's saves last 5 seconds'
        self.last_received = time.monotonic()
        self.writer = None
        self.reader = threading.Thread(target=self._read, args=(fd,), daemon=True)
        self.reader.start()

    def _read(self, fd):
        pending = b''
        try:
            while chunk := os.read(fd, PACKET.size*8):
                pending += chunk
                while len(pending) >= PACKET.size:
                    block = PACKET.unpack(pending[:PACKET.size])
                    pending = pending[PACKET.size:]
                    with self.lock:
                        self.blocks.append(block)
                        self.last_received = time.monotonic()
        finally:
            os.close(fd)

    def save(self, spec, controls, muted, selected):
        if self.writer and self.writer.is_alive():
            return
        with self.lock:
            blocks = list(self.blocks)
            age = time.monotonic()-self.last_received
        if not blocks:
            self.status = 'No audio captured yet; try s again'
            return
        if age > .5:
            self.status = 'Capture stalled; no sample saved'
            return
        spec, controls = copy.deepcopy(spec), dict(controls)
        self.status = 'Saving sample...'
        self.writer = threading.Thread(target=self._save,
                                       args=(blocks, spec, controls, muted, selected), daemon=True)
        self.writer.start()

    def _save(self, blocks, spec, controls, muted, selected):
        folder = None
        try:
            start = blocks[0][0]
            expected = start
            audio = []
            events = []
            previous = None
            for block in blocks:
                sample, count = block[:2]
                if sample != expected:
                    raise ValueError('Capture gap detected; retry after 5 seconds')
                expected += count
                target = dict(zip(KEYS, block[2:15]))
                if target != previous:
                    events.append({'sample': sample-start, 'target': target})
                    previous = target
                audio.append(block[-1][:count*4])
            audio = b''.join(audio)
            trim = max(0, len(audio)//4-5*self.rate)
            audio = audio[trim*4:]
            # Keep the target active at the beginning plus later exact-sample events.
            initial = [event for event in events if event['sample'] <= trim][-1]
            events = [dict(initial, sample=0)] + [dict(event, sample=event['sample']-trim)
                                                   for event in events if event['sample'] > trim]
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
            name = stamp + '-' + uuid.uuid4().hex[:8]
            folder = self.dataset / ('.pending-' + name)
            folder.mkdir()
            metadata = {
                'schema_version': 1, 'created_utc': stamp, 'sample_rate_hz': self.rate,
                'channels': 1, 'encoding': 'IEEE_FLOAT_32_LE', 'frames': len(audio)//4,
                'duration_seconds': len(audio)/4/self.rate, 'engine_start_sample': start+trim,
                'control_units': {key: ('Hz' if key in ('frequency','mod_rate','mod_depth','phase_frequency_1','phase_frequency_2') else 'ms' if key == 'delay_ms' else 'rad' if key == 'phase_offset' else 'dimensionless') for key in controls},
                'controls_at_save': controls, 'control_positions': positions(spec, controls),
                'muted_at_save': muted, 'selected_control': selected, 'parameter_events': events,
                'block_start_state': {'engine_sample': start, 'current': dict(zip(KEYS, blocks[0][15:28])),
                                      'phases_radians': dict(zip(('source', 'modulation', 'first', 'second'), blocks[0][28:32]))},
                'state_trim_samples': trim,
                'capture': 'Actual generated stream before device gain; retrospective up to 5 seconds.',
                'replay': 'declaration.json restores controls at save; restarting resets phases and delay history. WAV is the exact captured signal.',
            }
            (folder/'audio.wav').write_bytes(float_wav(self.rate, audio))
            (folder/'metadata.json').write_text(json.dumps(metadata, indent=2)+'\n')
            (folder/'declaration.json').write_text(json.dumps(recipe(spec, controls), indent=2)+'\n')
            folder.rename(self.dataset/name)
            self.status = 'Saved ' + name
        except (OSError, ValueError) as error:
            self.status = 'Save failed: ' + str(error)
            # A pending bundle is intentionally retained if a write fails.

    def finish(self):
        self.reader.join(timeout=2)
        if self.writer:
            self.writer.join(timeout=5)
