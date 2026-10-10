#!/usr/bin/env python3
"""Validate our declarative live subset and emit native DSP."""
import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
LIMITS = {'frequency': (40, 2000), 'mod_rate': (.1, 20), 'mod_depth': (0, 500),
          'delay_ms': (10, 1000), 'dry': (0, 1), 'echo': (0, 1), 'level': (0, .3)}
SHAPE_LIMITS = {'drive': (0, 16), 'mix': (0, 1)}
PHASE_LIMITS = {'phase_frequency_1': (0, 10000), 'phase_frequency_2': (0, 10000),
                'phase_depth': (0, 16), 'phase_offset': (-math.pi, math.pi)}
PHASE_KEYS = {'phase_frequency_1': 'frequency_1_hz', 'phase_frequency_2': 'frequency_2_hz',
              'phase_depth': 'drive_depth', 'phase_offset': 'offset_radians'}
SAMPLE_RATES = (24000, 44100, 48000, 96000)


def number(value, lo, hi, name):
    if type(value) not in (int, float) or not math.isfinite(value) or not lo <= value <= hi:
        raise ValueError('Control out of range: ' + name)
    return value


def load(declaration=None):
    if isinstance(declaration, dict):
        return declaration
    return json.loads(Path(declaration or ROOT / 'declaration.json').read_text())


def settings(spec):
    result = dict(spec['controls'])
    if 'waveshaping' in spec:
        result.update({k: spec['waveshaping'][k] for k in SHAPE_LIMITS})
    if 'relative_phase' in spec:
        result.update({key: spec['relative_phase'][declared] for key, declared in PHASE_KEYS.items()})
    return result


def generate(spec):
    required = {'sample_rate', 'channels', 'source', 'modulation', 'output',
                'max_delay_seconds', 'controls'}
    if not required <= set(spec) or set(spec) - required - {'waveshaping', 'relative_phase'}:
        raise ValueError('Unsupported declaration fields')
    rate = spec['sample_rate']
    if type(rate) is not int or rate not in SAMPLE_RATES or type(spec['channels']) is not int or spec['channels'] != 1:
        raise ValueError('This live subset requires mono at 24000, 44100, 48000 or 96000 samples/second')
    if (spec['source'], spec['modulation'], spec['output']) != ('sine', 'frequency', 'dry_plus_echo'):
        raise ValueError('Unsupported signal relationships')
    maximum = number(spec['max_delay_seconds'], .01, 1, 'maximum delay seconds')
    samples = maximum * rate
    if not float(samples).is_integer():
        raise ValueError('Maximum delay must resolve to whole samples')
    if not isinstance(spec['controls'], dict) or set(spec['controls']) != set(LIMITS):
        raise ValueError('Incorrect controls')
    values = dict(spec['controls'])
    for key, (lo, hi) in LIMITS.items():
        number(values[key], lo, hi, key)
    if values['delay_ms'] > maximum * 1000:
        raise ValueError('Default delay exceeds maximum')
    shaping = spec.get('waveshaping')
    if shaping is not None:
        if not isinstance(shaping, dict) or set(shaping) != {'kind', 'drive', 'mix'} or shaping['kind'] not in ('tanh', 'hard_clip'):
            raise ValueError('Waveshaping requires kind (tanh/hard_clip), drive and mix')
        for key, (lo, hi) in SHAPE_LIMITS.items():
            values[key] = number(shaping[key], lo, hi, key)
    elif 'waveshaping' in spec:
        raise ValueError('Waveshaping must be a relationship object')
    else:
        values.update(drive=1, mix=0)
    relative = spec.get('relative_phase')
    if 'relative_phase' in spec:
        if shaping is None:
            raise ValueError('Relative phase controls require a waveshaping relationship')
        if not isinstance(relative, dict) or set(relative) != {'mode', *PHASE_KEYS.values()}:
            raise ValueError('Relative phase requires mode, two frequencies, drive depth and offset')
        if relative['mode'] not in ('free_running', 'shared_clock'):
            raise ValueError('Phase mode must be free_running or shared_clock')
        for key, (lo, hi) in PHASE_LIMITS.items():
            values[key] = number(relative[PHASE_KEYS[key]], lo, hi, key)
        if relative['mode'] == 'shared_clock' and values['phase_frequency_1'] != values['phase_frequency_2']:
            raise ValueError('Shared-clock phases must declare equal frequencies')
        if values['phase_depth'] > min(values['drive'], 16-values['drive']):
            raise ValueError('Phase drive depth exceeds the valid drive domain')
    else:
        values.update(phase_frequency_1=0, phase_frequency_2=0, phase_depth=0, phase_offset=0)
    text = (ROOT / 'dsp-template.hpp').read_text()
    for key, value in values.items():
        literal = f'{value:.17e}' if key == 'phase_offset' else f'{value:.9e}f'
        text = text.replace('@' + key.upper() + '@', literal)
    constants = {'SR': rate, 'CAPACITY': 1 << (int(samples) - 1).bit_length(),
                 'MAX_DELAY_MS': f'{maximum*1000:.9e}f',
                 'SMOOTH': f'{1-math.exp(-1/(rate*.01)):.9e}f',
                 'SHAPING_ENABLED': 'true' if shaping is not None else 'false',
                 'SHAPE_KIND': 1 if shaping and shaping['kind'] == 'hard_clip' else 0,
                 'PHASE_ENABLED': 'true' if relative is not None else 'false',
                 'SHARED_CLOCK': 'true' if relative and relative['mode'] == 'shared_clock' else 'false'}
    for key, value in constants.items():
        text = text.replace('@' + key + '@', str(value))
    if '@' in text:
        raise ValueError('Unresolved template field')
    return text


def build(declaration=None, destination=None):
    spec = load(declaration)
    generated = generate(spec)
    if destination is not None:
        dest = Path(destination)
    elif declaration is None:
        dest = ROOT / 'build'
    else:
        digest = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:12]
        dest = ROOT / 'build' / digest
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'generated.hpp').write_text(generated)
    subprocess.run(['c++', '-std=c++17', '-O3', '-ffp-contract=off',
                    '-I', str(dest), '-I', str(ROOT), str(ROOT / 'engine.cpp'),
                    '-o', str(dest / 'engine')], check=True, capture_output=True)
    return dest / 'engine'


if __name__ == '__main__':
    print(build())
