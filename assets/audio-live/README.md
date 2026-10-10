# Audio processor — live compiler demo

This project explores building our own declarative audio compiler: describe
the signal relationships in a small JSON declaration, generate native C++ DSP,
and hear the result continuously while changing parameters in a terminal.
The aim of this alpha is to make that compiler experiment playable on an Arch
machine and establish a working foundation for further audio experiments.

This description draws from the included [project handoff](live-addendum.md).

## What the demo does

Python validates `declaration.json` and generates C++ from `dsp-template.hpp`.
The system C++ compiler builds the engine once on launch. The terminal interface
sends parameter changes to the running engine, which streams audio to ALSA
through `aplay`.

The current declaration combines a sine oscillator, sine frequency modulation,
and one delayed read of the oscillator's history. Output is the direct signal
plus the delayed signal, scaled by the master level. Oscillator phases and
history persist between blocks.

The engine runs at 24 kHz in mono. A one-second delay allowance uses a rounded
32,768-sample history buffer (128 KiB). Controls use approximately 10-ms
exponential smoothing, and fractional delay positions use linear interpolation.

## Run on Arch Linux

Install missing dependencies:

```sh
sudo pacman -S --needed python gcc alsa-utils
```

From the checkout, in an interactive terminal:

```sh
python live.py
```

On Grey's current machine, the checkout is `~/src/arch-audio-live` and the
installed shortcut is `audio-live`. The default ALSA device connects to
PipeWire. `~/audio-live/arch-audio-live` remains a compatibility symlink.

The interface starts muted. Press **Space** to hear the default 220-Hz tone.
Select modulation depth and raise it from zero to hear pitch movement.

| Key | Action |
| --- | --- |
| Space | Mute or unmute |
| Up / Down | Select a parameter |
| Left / Right | Decrease or increase it |
| + / - | Adjust in smaller steps |
| r | Reset to declared defaults |
| s | Save the last five seconds of audio and parameters locally |
| q | Stop playback and quit |

Available controls are tone frequency, modulation rate and depth, echo delay,
direct level, echo level, and master level. A continuous tone's delayed signal
mainly changes phase and interference. Changing delay can bend pitch.

## Optional distortion and phase relationships

The same installed command launches the new opt-in declarations:

```sh
audio-live --declaration examples/tanh.json
audio-live --declaration examples/hard-clip.json
audio-live --declaration examples/phase-drive.json
audio-live --declaration examples/shared-phase.json
```

Plain `audio-live` now displays distortion and phase controls too, with wet mix
and phase depth initially zero. Raise **Distortion wet mix** to hear shaping;
then raise **Phase-driven drive depth** to hear phase-controlled changes.
The header reads `DISTORTION + PHASE`. To show only the original controls, use
`audio-live --declaration declaration.json`.

Press Space to unmute. Extra controls appear after the original controls;
arrow keys scroll the list on shorter terminals. `r` restores the selected
declaration's defaults. Wet mix zero or base drive zero bypasses after a short
fade. The original declaration and default audio output remain unchanged.

The phase example compares two independent control phases to vary distortion
drive; the shared-clock example declares a common clock with a fixed offset.
These relationships do not pull oscillator frequencies into lock.

See [the example guide](examples/README.md) and [technical evidence](technical-report.md)
for equations, limits, measurements, captures and remaining limitations.
Live processing has no new Python package dependencies; numerical and plotting
packages are confined to the optional development environment.

## Local sound snapshots

Press **s** while playing to save the most recent five seconds (or the shorter
available window after startup). The interface shows save progress and the
saved bundle name. Your local dataset is `~/Music/audio-live-samples/`.
Choose another location with `audio-live --dataset-dir /path/to/dataset`.

Each timestamped folder contains:

- `audio.wav`: the actual generated mono float32 samples, without normalization.
- `metadata.json`: parameter values and normalized positions at save, mute state,
  selected control, sample rate, exact sample offsets of parameter changes,
  and the smoothed controls and oscillator phases at the first retained block.
- `declaration.json`: a runnable declaration restoring the controls at save.

For example: `audio-live --declaration ~/Music/audio-live-samples/BUNDLE/declaration.json`.
A restarted declaration begins with new phases and empty delay history; use the
WAV to hear the exact saved signal. Device volume, room sound and microphone
input are outside the capture. Muting can therefore produce silent snapshots.
A save includes parameter changes within its retrospective window.

Disk writes run separately from playback. A bounded nonblocking side channel
feeds the capture ring; if packets are missing, saving reports a capture gap
instead of writing discontinuous audio. Retry after five seconds. Successful
bundles appear atomically with unique names; failed disk writes may leave a
hidden `.pending-*` folder. Nothing is uploaded or overwritten.

## Verify and troubleshoot

```sh
python live.py --build-only
python test_live.py
PYTHONPATH=.:tests .venv/bin/python -m unittest discover -s tests -v
```

Set up the development environment using [tests/README.md](tests/README.md).
The legacy test writes its offline WAV under `build/`, keeping the checked-in
example untouched. Generate matched captures and plots with:

```sh
.venv/bin/python tools/collect_evidence.py
```

Tests cover numerical sine and modulation references, delay and ring-buffer
wraparound, mute and gain smoothing, output bounds, declaration validation,
and terminal startup, adjustment, and shutdown using a substitute audio sink.
These checks passed on this machine on 2026-10-09. Separately, the real demo's
24-kHz playback stream was confirmed connected to PipeWire's analog output,
with an empty `audio-error.log`. This confirms routing; listening quality and
measured latency remain to be assessed.

If playback stops, inspect `audio-error.log` and list the available devices:

```sh
aplay -L
python live.py --device DEVICE_NAME
```

Use a device name from that list. Builds and logs stay in the project folder.

## Current scope

This is a limited live compiler alpha. It has no recursive echo feedback or
microphone input. It does not promise alias-free synthesis, hard real-time
execution, or a measured control latency. Feedback and broader compiler
optimisation are future work identified in the handoff.

See [README.txt](README.txt) for detailed parameter limits, buffering behavior,
and playback notes. `live-example.wav` is an offline example generated by the
engine, rather than a recording of the machine's speakers.
