ARCH AIR — DUNST AND CODEX ALERTS
Installed 2026-10-05. Enabled for existing Codex completion and approval events.

DUNST APPEARANCE
Background #1C1A1D, text #C9C4BC, border #FF3D00. The existing top-right
placement, dimensions, JetBrains Mono 10 font, square 1px frame, timeouts,
critical prefix, notification limits and dismissal behavior were preserved.
Critical notifications retain their explicit CRITICAL label and urgency.
No i3, compositor, launcher, app layout or ncspot launching changes were made.
Bone/charcoal contrast is 9.96:1. Orange/charcoal contrast is 4.87:1.
Notification palette tokens live in ~/.config/air-theme/palette.json.
Mauve #A38BA8 remains available as notification_muted for secondary styling.
Re-generate only notification appearance:
  air-theme charcoal --only dunst
Check appearance state:
  air-theme status

CODEX HOOKS
Installed CLI and app server: 0.160.0. Existing user-level notify command and
trusted asynchronous PermissionRequest hook in ~/.codex/config.toml were
left unchanged. codex-notify composes with the captured original popup handler,
retaining its Done/Approval titles, urgency and project context, then starts a
short-lived audio worker. No new hook trust state, service or package was added.
Active events:
  agent-turn-complete — existing external notify command.
  PermissionRequest — existing approval hook.
Separate required-input and terminal-error notifications were not added: the
external notify interface documents only completion, and the current approved
hooks provide approval requests. Routine tool failures are not treated as
user-actionable errors. No streamed-message or token notifications are emitted.
The helper does not read transcripts or record prompts, commands, credentials
or message bodies. Metadata files record only event type/time, playback outcome
and observed volume numbers. Popup context remains the old project basename.
Official OpenAI Docs checked:
  https://learn.chatgpt.com/docs/config-file/config-advanced#notifications
  https://learn.chatgpt.com/docs/hooks

SOUND AND SETTINGS
A locally generated original 1.7-second mono gong uses a rounded 120ms attack,
a low 195Hz fundamental, restrained inharmonic partials and a fading tail.
Its WAV peak is limited to 0.30 full scale; initial playback volume is modest.
No downloaded sound or new audio stack is involved.
Edit ~/.config/codex-alerts/settings.json. Changes apply to the next alert:
  sound_enabled: true       Disable the gong and ducking with false.
  gong_volume: 0.60          Playback setting from 0.0 to 1.0.
  duck_factor: 0.80          Multiply music volume by this value (20% dip).
  restore_seconds: 0.75     Smooth return time (0.1–2 seconds).
  coalesce_seconds: 5.0     Suppress overlapping/closely repeated sounds.
  music_apps: ncspot, spotify
  sound_file: ~/.local/share/codex-alerts/gong.wav
The sound stream has a dedicated restore identity, avoiding ordinary event
sound volume preferences. Ordinary notifications receive no new sound.
Inspect sound state without playing anything:
  codex-notify --status
Deliberate labelled popup/gong test (plays once; does not enable music):
  codex-notify --test

DUCKING AND RECOVERY
PipeWire 1.6.9 exposes the installed PulseAudio interface. The worker identifies
an active music stream at runtime, prioritizing ncspot/Spotify and honoring
MPRIS paused/stopped state where available. Muted, corked, zero-volume and
communication/video streams are excluded. Only the chosen sink-input volume
changes; the output sink, mute state and other streams are never modified.
Original per-channel volumes and channel balance are preserved. Every fade
step checks the stream identity and expected volume; a user adjustment stops
further writes. Values never exceed the captured original volume.
An exclusive lock serializes audio. Nearby alerts are coalesced, so repeated
alerts cannot cumulatively duck music. SIGTERM/SIGINT invoke restoration;
a private journal records in-flight writes for recovery on the next alert
following abrupt termination. SIGKILL cannot run immediate cleanup. There is
no background recovery service. Recovery refuses changed/replaced streams or
volumes that no longer match our owned values. Small PulseAudio quantization
(up to 16 raw units when acknowledging a write) is tolerated.
If per-stream audio is unavailable, the original popup still runs; sound is
attempted without ducking and status records the limitation. No global-volume
fallback, playback start, unmute, seek or playback control is used.

VERIFICATION
Passed Python syntax, JSON settings parsing, staged Dunst INI parsing, native
Dunst reload and original-vs-applied comparison of all non-color behavior.
The labelled test popup was visually inspected on the real display and
successfully dismissed. It was redisplayed once without another gong for
capture. Critical popup rendering was not separately captured.
One modest audible gong played successfully. Live ncspot went 100% -> 80% ->
100%, observed in 63 samples; the return used the 0.75-second fade. Five
concurrent worker attempts caused no cumulative dip. The output sink and all
other existing stream volumes remained unchanged; no recovery journal remains.
Native owned-silent-stream checks passed lowering/restoration, preservation of
a simulated user volume adjustment, SIGTERM restoration and muted-stream
exclusion. Original music and unrelated streams stayed unchanged.
No-music/corked/paused paths, asymmetric balance, ceilings, disappearing/reused
streams, mid-write interruption and stale-journal recovery were checked with
controlled stream fixtures. The fully music-free live case was not tested,
because existing playback was preserved. The gong's perceived character is
subjective; gong_volume is adjustable.
Both actual Codex integrations ran successfully: an existing approval hook
and a real ephemeral read-only completion session (no tool/file operations).
The event metadata confirmed PermissionRequest and agent-turn-complete, with
the original popup handler returning success. Source/config checks prove all
other app configs, Yazi, keybindings, startup, compositor and Codex hook
configuration remain unchanged by this notification update.
Isolated rollback checks passed: independent timeout and Yazi palette edits
were preserved, the previous helper was restored, and an overlapping colour
edit aborted all writes. Live rollback preflight also passed.
air-theme status reports pre-existing i3 config drift; it was present in the
notification baseline and remains untouched.
Visual and live-audio evidence: ~/.config/codex-alerts/review/.

BACKUP AND ROLLBACK
Private original-state backup:
  /home/grey/.local/state/codex-alerts/original-20261005-071047
Restore just this notification update:
  /home/grey/.local/state/codex-alerts/original-20261005-071047/restore
Preflight only:
  /home/grey/.local/state/codex-alerts/original-20261005-071047/restore --check
Restoration waits for current gong/fade work to finish, recovers an owned stale
duck when possible, validates hashes/syntax, merges independent later edits,
restores only the listed files and reloads Dunst in X. Conflicts or changed
symlinks stop before file writes, keeping both versions under backup/conflicts.
The existing oldest desktop-theme baseline is untouched.
To undo both recent updates, restore notifications first, then run the Yazi
rollback command documented in ~/.config/air-theme/YAZI-COLOURS.txt.

Exact modified/added config and helper files (relative to home):
  .local/bin/codex-notify
  .local/share/codex-alerts/previous-notify.py
  .local/share/codex-alerts/gong.wav
  .config/codex-alerts/settings.json
  .config/codex-alerts/README.txt
  .config/dunst/dunstrc
  .config/air-theme/palette.json
  .local/bin/air-theme
  .config/air-theme/generated/.config/dunst/dunstrc
  .local/state/air-theme/last/.config/dunst/dunstrc
  .local/state/air-theme/state.json

New private runtime metadata: ~/.local/state/codex-alerts/{sound.lock,
last-event.json,last-sound.json}; duck.json exists only while restoration is
pending. Backup snapshots/manifests and harmless review assets are supporting
artifacts. They are not part of other application configuration.
