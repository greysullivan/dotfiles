# ncspot Final State

Date: 2026-03-19
User: `grey`

## Outcome

Native `ncspot` album art is working.

## What fixed it

The key fix was replacing old `ueberzug` with `ueberzugpp`.

Why this mattered:

- `F8` was already opening native `ncspot` cover view
- cover files were already downloading into `~/.cache/ncspot/covers/`
- the missing piece was native render backend compatibility
- upstream `ncspot` recommends `ueberzugpp` over abandoned `ueberzug`

## Current behavior

### `music`

`music` now behaves simply:

- if run inside kitty, it reuses the current pane and `exec`s into `ncspot`
- if run outside kitty, it opens kitty and runs `ncspot`

File:

- `/home/grey/.local/bin/music`

Current content:

```bash
#!/usr/bin/env bash

set -euo pipefail

if [[ -n "${KITTY_WINDOW_ID:-}" ]]; then
  exec ncspot "$@"
fi

exec kitty sh -lc 'exec ncspot "$@"' sh "$@"
```

### Native ncspot keybindings

File:

- `/home/grey/.config/ncspot/config.toml`

Relevant bindings:

```toml
[keybindings]
"F1" = "focus queue"
"F2" = "focus search"
"F3" = "focus library"
"F8" = "focus cover"
```

### Cover scaling

Native cover scaling cap was increased:

```toml
cover_max_scale = 2.0
```

This allows the cover art to scale much more with pane/window size.

## Kitty-side status

We explicitly stopped fighting native `ncspot` from kitty.

File:

- `/home/grey/.config/kitty/ncspot-card.conf`

Current state:

- no `f8` kitty bind
- native `ncspot` owns `F8`

## Renderer state

Installed package:

```text
ueberzugpp 2.9.8-3
```

`/usr/bin/ueberzug` now resolves to the `ueberzugpp` implementation.

## Files that matter now

- `/home/grey/.local/bin/music`
- `/home/grey/.config/ncspot/config.toml`
- `/home/grey/.config/kitty/ncspot-card.conf`

## If something breaks later

Check:

```bash
command -v ueberzug
pacman -Qi ueberzugpp
music
```

Then inside `ncspot`:

- `F1` queue
- `F2` search
- `F3` library
- `F8` cover

If native cover ever goes blank again, first confirm `ueberzugpp` is still installed before changing config.
