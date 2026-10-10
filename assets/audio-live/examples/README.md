# Opt-in signal relationships

Plain `audio-live` displays the new distortion and phase controls with wet mix
and phase depth initially zero, preserving the original sound. Raise wet mix
to hear distortion and phase depth to vary its drive. The original
`declaration.json` is unchanged; `audio-live --declaration declaration.json`
shows only its original controls. Launch enabled examples with the same command:

```sh
audio-live --declaration examples/tanh.json
audio-live --declaration examples/hard-clip.json
audio-live --declaration examples/phase-drive.json
audio-live --declaration examples/shared-phase.json
```

Paths in these examples are relative to the project directory used by the
installed launcher. For another declaration, use its absolute path.

Both start muted. Space unmutes; arrows select/change parameters, +/- make fine
changes, `r` restores this declaration's defaults, and `q` quits. Distortion
controls are appended. Setting wet mix or base drive to zero bypasses after
the live fade completes. The default declaration has no shaping relationship.

The supported mono sample rates are 24000 (default), 44100, 48000 and 96000 Hz.
Shaping is 1× in live playback; filtered 4×/16× oversampling is an offline
experiment, not a live feature or an alias-free guarantee.

`phase-drive.json` declares two free-running control oscillators, at 2 and
2.25 Hz, producing a .25-Hz relative-phase drive modulation. These are separate
from the audible oscillator. `shared-phase.json` declares one clock shared by
the two phases with a π/2 offset; both phase-rate controls are tied together.
Shared clock is an explicit relationship, not observed or achieved locking.

Phase drive is `g = base_drive + depth*cos(phi1-phi2-offset)`. Depth is bounded
by `min(base_drive, 16-base_drive)`; reducing base drive also reduces allowable
depth. Offset is in radians and smooths along the shortest circular arc.
If phase modulation momentarily makes `g=0` with positive base drive, the wet
branch evaluates tanh(0) or clip(0), yielding zero. Setting **base drive** to
zero instead requests the deliberate bypass fade.
