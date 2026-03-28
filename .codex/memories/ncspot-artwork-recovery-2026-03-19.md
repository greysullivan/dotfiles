# ncspot Artwork Recovery Notes

Date: 2026-03-19
Host user: `grey`

## Current state

- `music` launches plain `ncspot` again.
- `ncspot` function keys are configured natively:
  - `F1` -> `focus queue`
  - `F2` -> `focus search`
  - `F3` -> `focus library`
  - `F8` -> `focus cover`
- The native `ncspot` cover pane opens, but images do not render.
- Cover files are definitely downloading into `~/.cache/ncspot/covers/`.
- `ueberzug` is installed at `/usr/bin/ueberzug`.
- Python modules for `ueberzug` and `PIL` are present.

## Important conclusion

The remaining problem is not keybinding or cover download.
It is native `ncspot` cover rendering.

## Files touched during this session

- `/home/grey/.config/ncspot/config.toml`
- `/home/grey/.config/kitty/ncspot-card.conf`
- `/home/grey/.config/kitty/sessions/ncspot`
- `/home/grey/.local/share/ncspot-card/config.sh`
- `/home/grey/.local/share/ncspot-card/fetch_metadata.sh`
- `/home/grey/.local/share/ncspot-card/render_card.sh`
- `/home/grey/.local/share/ncspot-card/toggle_card.sh`

## Desired native config right now

`/home/grey/.config/ncspot/config.toml` should contain:

```toml
[keybindings]
"F1" = "focus queue"
"F2" = "focus search"
"F3" = "focus library"
"F8" = "focus cover"
```

`/home/grey/.config/kitty/ncspot-card.conf` should NOT bind `f8`.

## Evidence already confirmed

- Native cover cache exists:
  - `/home/grey/.cache/ncspot/covers/...`
- Cached images are valid JPEGs:
  - mostly `640x640`
- Example sizes are around `79K` to `226K`
- `ncspot` is therefore fetching cover art successfully

## Likely failure area

Native cover rendering in `ncspot` via `ueberzug`.

## First commands to run after reboot

Open a fresh terminal and run:

```bash
music
```

Inside `ncspot`, press:

```text
F8
```

If the cover pane is still blank, close `ncspot` and run a debug session:

```bash
ncspot --debug /tmp/ncspot-debug.log
```

Then:

1. Start playback
2. Press `F8`
3. Quit `ncspot`
4. Inspect:

```bash
rg -n "Ueberzug|cover|image|Failed" /tmp/ncspot-debug.log
```

## Useful checks

Check runtime pieces:

```bash
command -v ueberzug
python3 - <<'PY'
import importlib.util
print("PIL", bool(importlib.util.find_spec("PIL")))
print("ueberzug", bool(importlib.util.find_spec("ueberzug")))
PY
```

Check that covers still download:

```bash
ls -lh ~/.cache/ncspot/covers | tail
file ~/.cache/ncspot/covers/* | tail
```

## Notes on the helper path

There is an external helper project at:

`/home/grey/.local/share/ncspot-card`

It was explored as a fallback because it can show:

- artwork
- song
- album
- artist

But the user explicitly wanted to work with native `ncspot`, not replace it.
So `F8` was restored to native `focus cover`.

## One known unrelated log

`/home/grey/.cache/ncspot/backtrace.log` currently shows a `cursive` panic about:

`Can not disable mouse capture or show cursor`

That does not prove the cover issue, but it is worth keeping in mind if `ncspot`
acts unstable in this terminal/session.
